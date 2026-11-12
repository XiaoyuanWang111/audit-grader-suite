"""Adapters that run the two graders under audit, and the replacement, on one constraint or one row.

Grader A: Marin's SkyRL reward, `grade_instruction_following`, which builds NVIDIA's checkers
with `build_instruction` and calls `check_following`. Its graded text comes from
`final_answer_text`. Grader B: the task-curation gate, verifyit's `ifeval` checks for every
constraint not in SEMANTIC_INSTRUCTION_CONSTRAINTS. Its graded text comes from verifyit's
`_answer_text(candidate, True, strip_outer=False)`.

`final_answer_text` and `_answer_text` live in modules that import packages not installed here,
so this file compiles exactly those functions from the case's source files with `ast` (no copy).
"""
from __future__ import annotations

import ast
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

from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
    _ensure_nltk_data,
    build_instruction,
    grade_instruction_following,
)
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

from replacement import contracts_grader as R  # noqa: E402

SEMANTIC = frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                      "language:response_language", "letters:letter_counting"})


def _compile_functions(path: str, names: set[str], assigns: set[str]) -> dict:
    source = open(path, encoding="utf-8").read()
    tree = ast.parse(source)
    body = [node for node in tree.body
            if (isinstance(node, ast.FunctionDef) and node.name in names)
            or (isinstance(node, ast.Assign) and any(getattr(t, "id", None) in assigns for t in node.targets))]
    module = ast.Module(body=body, type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, path, "exec"), namespace)
    return namespace


_A_NS = _compile_functions(f"{CASE}/reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py",
                           {"final_answer_text"}, {"REASONING_DELIMITERS"})
_B_NS = _compile_functions(f"{CASE}/grader/verifyit/modes/grade_judge.py", {"_answer_text"}, set())
final_answer_text = _A_NS["final_answer_text"]


def answer_text_b(raw: str) -> str:
    return _B_NS["_answer_text"](raw, True, strip_outer=False)


def clean_kwargs(kwargs):
    return {k: v for k, v in (kwargs or {}).items() if v is not None}


def check_a(iid: str, kwargs: dict, text: str, seed: int | None = 0) -> tuple[bool, str | None]:
    """One NVIDIA checker as grade_instruction_following runs it; returns (verdict, error)."""
    _ensure_nltk_data()
    if seed is not None:
        random.seed(seed)
    try:
        inst = build_instruction(iid, clean_kwargs(kwargs))
        return bool(inst.check_following(text)), None
    except Exception as error:  # the reward counts the constraint as failed
        return False, f"{type(error).__name__}: {error}"


def check_b(iid: str, kwargs: dict, text: str) -> tuple[bool | None, str]:
    """One verifyit gate check as grade_judge_candidate runs it; None for a judged (semantic) id."""
    if iid in SEMANTIC:
        return None, "judged by the LLM, no deterministic check"
    constraint = Constraint(iid, clean_kwargs(kwargs))
    [(constraint, check)] = resolve_checks((constraint,))
    try:
        passed, detail = check(text, constraint.params)
    except Exception as error:
        return False, f"exception {type(error).__name__}: {error}"
    return bool(passed), detail


def check_r(iid: str, kwargs: dict, text: str, readings: dict | None = None) -> bool:
    return R.check(iid, clean_kwargs(kwargs), text, readings)


def row_a(raw: str, record: dict, seed: int | None = 0) -> tuple[float, dict]:
    """Grader A's reward for one model text: final_answer_text, then grade_instruction_following."""
    if seed is not None:
        random.seed(seed)
    return grade_instruction_following(final_answer_text(raw), record)


def row_b_gate(raw: str, record: dict) -> tuple[bool, list]:
    """Grader B's deterministic gate for one model text: True when every gate check passes."""
    text = answer_text_b(raw)
    results = []
    for iid, kw in zip(record["instruction_id_list"], record["kwargs"]):
        v, detail = check_b(iid, kw, text)
        results.append(v)
    return all(v for v in results if v is not None), results
