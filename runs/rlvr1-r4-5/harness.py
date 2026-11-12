"""Run the graders under audit on one constraint or one row, exactly as their pipelines do.

Graders:
- NV   SkyRL reward, default config: `final_answer_text` then `grade_instruction_following`
       (NVIDIA's checkers via `build_instruction`).
- VS   SkyRL reward with `verifyit_enabled`: `final_answer_text` then `grade_nemotron_instructions`
       (run in-process through `_evaluate_with_state`, the function its subprocess runs).
- VG   task-curation deterministic gate: `grade_judge._answer_text(strip_reasoning=True)` then
       verifyit's checks for the non-semantic constraints, an exception counting as a failure.
- R    the replacement grader (audit/replacement.py), proposed readings; RF = fixes only.

`final_answer_text` (answer_extraction.py) and `_answer_text` (grade_judge.py) are loaded from the
pinned files by AST, because their modules import packages that are not installed here.
"""

from __future__ import annotations

import ast
import json
import os
import random
import re
import sys

W = "<W>"
CASE = f"{W}/case"
os.environ.setdefault("NLTK_DATA", f"{CASE}/deps/nltk_data")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True
if f"{CASE}/reference" not in sys.path:
    sys.path.insert(0, f"{CASE}/reference")
if f"{W}/audit" not in sys.path:
    sys.path.insert(0, f"{W}/audit")

from skyrl_gym.envs.nemotron_ultra.instruction_following import grade_instruction_following  # noqa: E402
from skyrl_gym.envs import instruction_verifyit as _iv  # noqa: E402
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

from replacement import Replacement  # noqa: E402

SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)  # graders.py SEMANTIC_INSTRUCTION_CONSTRAINTS


def _load_function(path: str, name: str, extra_names: tuple[str, ...] = ()):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    keep = [
        node
        for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name == name)
        or (isinstance(node, ast.Assign) and any(getattr(t, "id", None) in extra_names for t in node.targets))
    ]
    module = ast.Module(body=keep, type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, path, "exec"), namespace)
    return namespace[name]


final_answer_text = _load_function(
    f"{CASE}/reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py", "final_answer_text", ("REASONING_DELIMITERS",)
)
_answer_text = _load_function(f"{CASE}/grader/verifyit/modes/grade_judge.py", "_answer_text")


def gate_extract(raw: str) -> str:
    """grade_judge_candidate: candidate = _answer_text(candidate, True, strip_outer=False)."""
    return _answer_text(raw, True, strip_outer=False)


# ---- single constraint ------------------------------------------------------------------


def nv_check(iid: str, kwargs: dict | None, text: str) -> tuple[bool, str | None]:
    """NVIDIA checker as grade_instruction_following runs it. Returns (passed, error)."""
    reward, detail = grade_instruction_following(text, {"instruction_id_list": [iid], "kwargs": [kwargs]})
    return detail["follow_instruction_list"][0], detail["instruction_errors"][0]


def vg_check(iid: str, kwargs: dict | None, text: str) -> tuple[bool | None, str | None]:
    """verifyit check as the gate runs it; None for a semantic (judge-only) constraint."""
    if iid in SEMANTIC:
        return None, None
    c = Constraint(iid, {k: v for k, v in (kwargs or {}).items() if v is not None})
    ((constraint, check),) = resolve_checks((c,))
    try:
        passed, detail = check(text, constraint.params)
        return passed, None
    except Exception as error:  # grade_judge._passes: counted as failed
        return False, f"{type(error).__name__}: {error}"


def vs_row(text: str, record: dict) -> dict:
    """grade_nemotron_instructions in-process: the verdict dict of _evaluate_with_state."""
    state = random.getstate()
    verdict = _iv._evaluate_with_state("nemotron", text, record, state)
    if verdict["status"] == "scored":
        random.setstate(_iv._validated_random_state(verdict["detail"]["random_state"]))
    return verdict


def vs_check(iid: str, kwargs: dict | None, text: str) -> tuple[bool | None, str | None]:
    verdict = vs_row(text, {"instruction_id_list": [iid], "kwargs": [kwargs]})
    if verdict["status"] != "scored":
        return False, f"{verdict['status']}: {verdict['detail']}"
    return verdict["detail"]["source_feedback"]["follow_instruction_list"][0], None


R = Replacement()
RF = Replacement.fixes_only()


def r_check(iid: str, kwargs: dict | None, text: str | None, replacement: Replacement = R) -> bool:
    return replacement.check(iid, kwargs, text)


# ---- whole rows (pipelines) -----------------------------------------------------------------


def nv_row(raw: str, record: dict) -> dict:
    action = final_answer_text(raw)
    reward, detail = grade_instruction_following(action, record)
    infra = any(detail["instruction_errors"])
    return {
        "reward": 0.0 if infra else reward,
        "outcome": "infra_error" if infra else "graded",
        "results": detail["follow_instruction_list"],
        "errors": detail["instruction_errors"],
        "action_empty": not action.strip(),
    }


def vg_row(raw: str, record: dict) -> dict:
    candidate = gate_extract(raw)
    constraints = tuple(
        Constraint(n, {k: v for k, v in (a or {}).items() if v is not None})
        for n, a in zip(record["instruction_id_list"], record["kwargs"])
    )
    resolve_checks(constraints)
    results, errors = [], []
    for c in constraints:
        if c.name in SEMANTIC:
            results.append(None)
            errors.append(None)
            continue
        ((constraint, check),) = resolve_checks((c,))
        try:
            passed, _ = check(candidate, constraint.params)
            errors.append(None)
        except Exception as error:
            passed = False
            errors.append(f"{type(error).__name__}: {error}")
        results.append(bool(passed))
    gate = all(r for r in results if r is not None)
    return {"gate_pass": gate, "results": results, "errors": errors, "candidate_empty": not candidate.strip()}


def r_row(raw: str, record: dict, thinking: bool, replacement: Replacement = R) -> dict:
    text = replacement.graded_text(raw, thinking)
    results = [replacement.check(i, k, text) for i, k in zip(record["instruction_id_list"], record["kwargs"])]
    return {"reward": float(all(results)), "results": results, "extraction_failure": text is None}
