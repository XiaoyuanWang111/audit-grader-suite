"""Audit harness: run the two graders under audit, as the pipelines run them, on one response.

Grader 1, "skyrl": Marin's SkyRL reward. The session passes the model's text through
`final_answer_text` (skyrl_gym/envs/nemotron_ultra/answer_extraction.py), then
`grade_instruction_following` builds each constraint with NVIDIA's registry and calls
`check_following`. answer_extraction.py cannot be imported here (it imports
skyrl_gym.envs.aime.utils, which needs math_verify and sympy), so this module loads the two
definitions it needs, REASONING_DELIMITERS and final_answer_text, from the file's own source
with `ast` and executes them unchanged.

Grader 2, "verifyit": the deterministic gate of Marin's task-curation grader.
`convert_instruction_following` (graders.py) builds one verifyit Constraint per constraint
(kwargs without None values) and drops the four SEMANTIC_INSTRUCTION_CONSTRAINTS from the gate;
`grade_judge_candidate` strips reasoning blocks with `_answer_text` (grade_judge.py, which imports
openai and cannot be imported here; loaded from source the same way) and fails the gate if any
check fails or raises.

Usage: import this module with the case folder as the working directory or call `setup()`.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(W, "case")
NLTK_DATA = os.path.join(CASE, "deps", "nltk_data")
SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)


def _load_defs(path: str, names: set[str], extra_globals: dict) -> dict:
    """Execute the top-level definitions `names` of a source file, unchanged, in a fresh namespace."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    keep = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            keep.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            keep.append(node)
    found = {n.name if hasattr(n, "name") else n.targets[0].id for n in keep}
    if found != names:
        raise RuntimeError(f"{path}: missing definitions {names - found}")
    namespace = dict(extra_globals)
    exec(compile(ast.Module(body=keep, type_ignores=[]), path, "exec"), namespace)
    return namespace


_READY = False


def setup() -> None:
    global _READY, final_answer_text, curation_answer_text, grade_instruction_following, build_instruction
    global resolve_checks, CONSTRAINTS, Constraint
    if _READY:
        return
    os.environ.setdefault("NLTK_DATA", NLTK_DATA)
    import nltk

    # Search only the case's NLTK data, never folders outside the audit directory.
    nltk.data.path[:] = [NLTK_DATA]
    ref = os.path.join(CASE, "reference")
    if ref not in sys.path:
        sys.path.insert(0, ref)
    ns = _load_defs(
        os.path.join(ref, "skyrl_gym", "envs", "nemotron_ultra", "answer_extraction.py"),
        {"REASONING_DELIMITERS", "final_answer_text"},
        {"re": re},
    )
    final_answer_text = ns["final_answer_text"]
    ns2 = _load_defs(
        os.path.join(CASE, "grader", "verifyit", "modes", "grade_judge.py"), {"_answer_text"}, {"re": re}
    )
    _answer_text = ns2["_answer_text"]

    def curation_answer_text(text: str) -> str:
        # grade_judge_candidate: _answer_text(candidate, spec.strip_candidate_reasoning_blocks, strip_outer=False)
        return _answer_text(text, True, strip_outer=False)

    from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
        build_instruction as _bi,
        grade_instruction_following as _gif,
    )
    from verifyit.modes.grade_ifeval import resolve_checks as _rc  # noqa: E402
    from verifyit.modes.ifeval import CONSTRAINTS as _C  # noqa: E402
    from verifyit.spec import Constraint as _Con  # noqa: E402

    grade_instruction_following, build_instruction = _gif, _bi
    resolve_checks, CONSTRAINTS, Constraint = _rc, _C, _Con
    _READY = True


def record_of(row: dict) -> dict:
    return json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])


def clean_kwargs(kwargs) -> dict:
    return {k: v for k, v in (kwargs or {}).items() if v is not None}


def skyrl_constraint(iid: str, kwargs: dict | None, text: str):
    """NVIDIA verdict on already-extracted text, as grade_instruction_following computes it.
    Returns (passed: bool, error: str | None)."""
    setup()
    try:
        instruction = build_instruction(iid, clean_kwargs(kwargs))
        return bool(instruction.check_following(text)), None
    except Exception as error:  # the reward counts it as failed and records the error
        return False, f"{type(error).__name__}: {error}"[:200]


def skyrl_row(raw: str, record: dict) -> dict:
    """The SkyRL reward on a raw model response: final_answer_text, then grade_instruction_following."""
    setup()
    action = final_answer_text(raw)
    reward, details = grade_instruction_following(action, record)
    infra = any(details["instruction_errors"])
    return {"text": action, "reward": reward, "results": details["follow_instruction_list"],
            "errors": details["instruction_errors"], "infra_error": infra}


def verifyit_constraint(iid: str, kwargs: dict | None, text: str):
    """verifyit check verdict on already-extracted text. Returns (passed, detail)."""
    setup()
    constraint = Constraint(iid, clean_kwargs(kwargs))
    (_, check), = resolve_checks((constraint,))
    try:
        passed, detail = check(text, constraint.params)
        return passed, detail
    except Exception as error:  # grade_judge._passes counts a crash as a failed check
        return False, f"EXC {type(error).__name__}: {error}"[:200]


def verifyit_row(raw: str, record: dict) -> dict:
    """The task-curation gate on a raw model response."""
    setup()
    text = curation_answer_text(raw)
    constraints = tuple(Constraint(n, clean_kwargs(a)) for n, a in zip(record["instruction_id_list"], record["kwargs"]))
    resolve_checks(constraints)
    results = []
    for c in constraints:
        if c.name in SEMANTIC:
            results.append(None)  # goes to the LLM judge
            continue
        passed, _ = verifyit_constraint(c.name, c.params, text)
        results.append(bool(passed))
    gated = [r for r in results if r is not None]
    return {"text": text, "gate_pass": all(gated), "results": results}
