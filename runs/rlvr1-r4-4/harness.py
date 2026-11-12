"""Run each grader exactly as its pipeline runs it, on one response or one constraint.

- Grader A (SkyRL reward): `final_answer_text` (exec'd from its source file, because its module
  imports packages that are not installed), then `grade_instruction_following` (imported).
- Grader B (task-curation gate): `_answer_text(..., strip_reasoning=True, strip_outer=False)` and
  `_passes` (both exec'd from verifyit/modes/grade_judge.py, which imports openai), then the
  verifyit checks from `resolve_checks` on every constraint outside SEMANTIC.
- R: the replacement grader in audit/replacement/contract_grader.py.

Set NLTK_DATA and PYTHONDONTWRITEBYTECODE before importing (see case/TASK.md).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(W, "case")
sys.path.insert(0, os.path.join(CASE, "reference"))
sys.path.insert(0, os.path.join(W, "audit", "replacement"))

from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
    build_instruction,
    grade_instruction_following,
    _ensure_nltk_data,
)
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

import contract_grader as R  # noqa: E402

SEMANTIC = frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                      "language:response_language", "letters:letter_counting"})  # graders.py line 217


def _exec_defs(path: str, names: set[str], namespace: dict) -> dict:
    """Execute the named top-level definitions of a source file, byte for byte, in `namespace`."""
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        name = getattr(node, "name", None)
        if name is None and isinstance(node, ast.Assign):
            name = next((t.id for t in node.targets if isinstance(t, ast.Name)), None)
        if name in names:
            code = ast.get_source_segment(src, node)
            exec(compile(code, path, "exec"), namespace)  # noqa: S102
    missing = names - set(namespace)
    if missing:
        raise RuntimeError(f"definitions not found in {path}: {missing}")
    return namespace


class _Logger:
    def warning(self, *args, **kwargs):
        pass


_A_NS = _exec_defs(os.path.join(CASE, "reference", "skyrl_gym", "envs", "nemotron_ultra", "answer_extraction.py"),
                   {"REASONING_DELIMITERS", "final_answer_text"}, {"re": re})
_B_NS = _exec_defs(os.path.join(CASE, "grader", "verifyit", "modes", "grade_judge.py"),
                   {"_answer_text", "_passes"}, {"re": re, "logger": _Logger(), "Check": object})

final_answer_text = _A_NS["final_answer_text"]
_answer_text = _B_NS["_answer_text"]
_passes = _B_NS["_passes"]


def extract_a(raw: str) -> str:
    return final_answer_text(raw)


def extract_b(raw: str) -> str:
    return _answer_text(raw, True, strip_outer=False)


def clean(kwargs):
    return {k: v for k, v in (kwargs or {}).items() if v is not None}


# ---------------------------------------------------------------------------- per constraint

def a_check(iid: str, kwargs, text: str) -> tuple[bool, str | None]:
    """Grader A on one constraint, as grade_instruction_following runs it: (verdict, error)."""
    _ensure_nltk_data()
    try:
        inst = build_instruction(iid, clean(kwargs))
        return bool(inst.check_following(text)), None
    except Exception as error:  # noqa: BLE001
        return False, f"{type(error).__name__}: {error}"


def b_check(iid: str, kwargs, text: str) -> tuple[bool, str | None]:
    """Grader B's deterministic check on one constraint (exceptions count as failed, as _passes does)."""
    c = Constraint(iid, clean(kwargs))
    [(constraint, chk)] = resolve_checks((c,))
    try:
        passed, detail = chk(text, constraint.params)
        err = None
    except Exception as error:  # noqa: BLE001
        passed, err = False, f"{type(error).__name__}: {error}"
    assert _passes(chk, text, constraint.params) == passed
    return passed, err


def r_check(iid: str, kwargs, text: str | None, readings=None) -> bool:
    return R.check(iid, kwargs, text, readings)


# ---------------------------------------------------------------------------- per row

def a_row(raw: str, record: dict) -> tuple[float, dict]:
    """SkyRL reward of one raw response: final_answer_text, then grade_instruction_following."""
    return grade_instruction_following(extract_a(raw), record)


def b_gate(raw: str, record: dict) -> tuple[bool, list[str]]:
    """Task-curation gate: True when every deterministic constraint passes (the judge then decides)."""
    text = extract_b(raw)
    constraints = tuple(Constraint(n, clean(a)) for n, a in zip(record["instruction_id_list"], record["kwargs"]))
    resolve_checks(constraints)
    gate = tuple(c for c in constraints if c.name not in SEMANTIC)
    failed = [c.name for c, chk in (resolve_checks(gate) if gate else []) if not _passes(chk, text, c.params)]
    return not failed, failed


def load_rows() -> dict:
    rows = {}
    with open(os.path.join(CASE, "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            rows[rec["uuid"]] = rec
    return rows
