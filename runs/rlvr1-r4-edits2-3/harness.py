"""Run the two graders under audit, and the replacement, as their pipelines run them.

- SkyRL (`skyrl_grade`): `final_answer_text` from Marin's answer_extraction.py (imported
  with a stub for `skyrl_gym.envs.aime.utils`, whose `math_verify` import is not
  installed; the stub only replaces the two boxed-answer helpers, which
  `final_answer_text` does not use), then `grade_instruction_following(action, record)`.
- Task curation (`tc_gate`): verifyit's `_answer_text(..., strip_reasoning=True)`
  logic (grade_judge.py, which cannot be imported here; its code is identical
  to `final_answer_text`, see audit/ISSUE.md), then every deterministic constraint's
  check from `resolve_checks`, an exception counting as a failure, as
  `grade_judge_candidate` does. Returns per-constraint verdicts for all
  constraints, with None for the four judged ones.
- Replacement (`contract_grade`): audit/replacement/contract_grader.py.

Environment: run with NLTK_DATA set to case/deps/nltk_data and PYTHONDONTWRITEBYTECODE=1.
"""

from __future__ import annotations

import json
import os
import sys
import types

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(W, "case")
os.environ.setdefault("NLTK_DATA", os.path.join(CASE, "deps", "nltk_data"))
sys.dont_write_bytecode = True
if os.path.join(CASE, "reference") not in sys.path:
    sys.path.insert(0, os.path.join(CASE, "reference"))
if os.path.join(W, "audit", "replacement") not in sys.path:
    sys.path.insert(0, os.path.join(W, "audit", "replacement"))

# Stub for skyrl_gym.envs.aime.utils (its math_verify dependency is not installed).
_stub = types.ModuleType("skyrl_gym.envs.aime.utils")
_stub.last_boxed_only_string = lambda text: None
_stub.remove_boxed = lambda text: text
sys.modules.setdefault("skyrl_gym.envs.aime.utils", _stub)

from skyrl_gym.envs.nemotron_ultra.answer_extraction import final_answer_text  # noqa: E402
from skyrl_gym.envs.nemotron_ultra.instruction_following import grade_instruction_following  # noqa: E402
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

import contract_grader  # noqa: E402

SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)
DATA = os.path.join(CASE, "data", "rlvr1_instruction_following.jsonl")


def load_rows() -> list[dict]:
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            nu = row["extra_info"]["nemotron_ultra"]
            rec = json.loads(nu["record_json"])
            rows.append(
                {
                    "index": i,
                    "uuid": nu["uuid"],
                    "prompt": row["prompt"][0]["content"],
                    "record": rec,
                    "ids": rec["instruction_id_list"],
                    "kwargs": rec["kwargs"],
                }
            )
    return rows


def tc_answer_text(text: str) -> str:
    """verifyit grade_judge._answer_text(text, strip_reasoning=True), copied verbatim."""
    import re

    pairs = (("<think>", "</think>"), ("<thinking>", "</thinking>"), ("<|start_think|>", "<|end_think|>"))
    for opening, closing in pairs:
        text = re.sub(re.escape(opening) + ".*?" + re.escape(closing), "", text, flags=re.DOTALL)
    closing = max((text.rfind(end) + len(end) for _, end in pairs if end in text), default=0)
    text = text[closing:]
    if any(opening in text for opening, _ in pairs):
        return ""
    return text.strip().removesuffix("<|eot_id|>").strip()


def skyrl_grade(raw: str, ids: list[str], kwargs: list) -> dict:
    """The SkyRL reward on a raw model text: extraction, then grade_instruction_following."""
    action = final_answer_text(raw)
    reward, info = grade_instruction_following(action, {"instruction_id_list": ids, "kwargs": kwargs})
    infra = any(info["instruction_errors"])
    return {
        "action": action,
        "reward": 0.0 if infra else reward,
        "results": info["follow_instruction_list"],
        "errors": info["instruction_errors"],
        "infra_error": infra,
    }


def skyrl_check(text: str, iid: str, kw) -> tuple[bool, str | None]:
    """One NVIDIA checker on already-extracted text, built as grade_instruction_following builds it."""
    _, info = grade_instruction_following(text, {"instruction_id_list": [iid], "kwargs": [kw]})
    return info["follow_instruction_list"][0], info["instruction_errors"][0]


def tc_constraints(ids, kwargs):
    return tuple(
        Constraint(name, {k: v for k, v in (args or {}).items() if v is not None}) for name, args in zip(ids, kwargs)
    )


def tc_check(text: str, iid: str, kw) -> tuple[bool | None, str]:
    """One verifyit check on already-extracted text; None for a judged constraint."""
    if iid in SEMANTIC:
        return None, "judged"
    (constraint, check), = resolve_checks(tc_constraints([iid], [kw]))
    try:
        passed, detail = check(text, constraint.params)
    except Exception as error:  # grade_judge._passes counts a crash as a failure
        return False, f"exception {type(error).__name__}: {error}"
    return bool(passed), detail


def tc_gate(raw: str, ids, kwargs) -> dict:
    candidate = tc_answer_text(raw)
    constraints = tc_constraints(ids, kwargs)
    resolve_checks(constraints)  # convert_instruction_following rejects the row if this raises
    results = []
    for iid, kw in zip(ids, kwargs):
        results.append(tc_check(candidate, iid, kw)[0])
    gate = all(r for r in results if r is not None)
    return {"candidate": candidate, "results": results, "gate_passed": gate}


def contract_grade(raw: str, ids, kwargs, prompt: str, reasoning_model: bool,
                   readings: contract_grader.Readings = contract_grader.PROPOSED) -> dict:
    text = contract_grader.graded_text(raw, reasoning_model)
    if text is None:
        return {"text": None, "results": [False] * len(ids), "extraction_failure": True, "reward": 0.0}
    results = [contract_grader.check(text, iid, kw, prompt, readings) for iid, kw in zip(ids, kwargs)]
    return {"text": text, "results": results, "extraction_failure": False, "reward": float(all(results))}


def contract_check(text: str, iid: str, kw, prompt: str = "",
                   readings: contract_grader.Readings = contract_grader.PROPOSED) -> bool:
    return contract_grader.check(text, iid, kw, prompt, readings)
