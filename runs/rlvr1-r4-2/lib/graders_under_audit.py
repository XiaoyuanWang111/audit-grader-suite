"""Adapters that run the two graders under audit exactly as their pipelines do.

Grader A: the SkyRL reward. `final_answer_text` (answer_extraction.py) then
`grade_instruction_following` (instruction_following.py), which builds NVIDIA's checkers with
`build_instruction`.

Grader B: the task-curation gate. `grade_judge._answer_text(candidate, True, strip_outer=False)`,
then every non-semantic constraint's verifyit check, a raising check counted as failed
(`grade_judge._passes`).

`answer_extraction.py` and `grade_judge.py` import packages that are not installed, so the two
extraction functions are compiled from the case files' own source text with `ast` (no copy).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
CASE = W / "case"
os.environ.setdefault("NLTK_DATA", str(CASE / "deps" / "nltk_data"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True
if str(CASE / "reference") not in sys.path:
    sys.path.insert(0, str(CASE / "reference"))

from skyrl_gym.envs.nemotron_ultra import instruction_following as _if  # noqa: E402
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.modes.ifeval import CONSTRAINTS  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)
DATA = CASE / "data" / "rlvr1_instruction_following.jsonl"


def _load(path: Path, names: set[str]) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            body.append(node)
    found = {n.name if isinstance(n, ast.FunctionDef) else n.targets[0].id for n in body}
    assert found == names, (path, found, names)
    namespace = {"re": re}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return namespace


final_answer_text = _load(
    CASE / "reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py", {"REASONING_DELIMITERS", "final_answer_text"}
)["final_answer_text"]
_answer_text = _load(CASE / "grader/verifyit/modes/grade_judge.py", {"_answer_text"})["_answer_text"]


def extract_a(raw: str) -> str:
    return final_answer_text(raw)


def extract_b(raw: str) -> str:
    return _answer_text(raw, True, strip_outer=False)


def _clean(kwargs) -> dict:
    return {k: v for k, v in (kwargs or {}).items() if v is not None}


def check_a(iid: str, kwargs, text: str):
    """One NVIDIA check on already extracted text. Returns True, False or 'error: ...'."""
    _if._ensure_nltk_data()
    try:
        return bool(_if.build_instruction(iid, _clean(kwargs)).check_following(text))
    except Exception as error:  # noqa: BLE001 - mirrors grade_instruction_following
        return f"error: {type(error).__name__}: {error}"


def check_b(iid: str, kwargs, text: str):
    """One verifyit check on already extracted text. None for a semantic (judge) constraint.

    Returns True or False as the gate counts it, or 'error: ...' when the check raised
    (the gate counts that as False).
    """
    if iid in SEMANTIC:
        return None
    constraint = Constraint(iid, _clean(kwargs))
    (_, check), = resolve_checks((constraint,))
    try:
        passed, _ = check(text, constraint.params)
    except Exception as error:  # noqa: BLE001 - mirrors grade_judge._passes
        return f"error: {type(error).__name__}: {error}"
    return passed


def reward_a(raw: str, record: dict) -> tuple[float, dict]:
    """Grader A's reward for one row, as NemotronTaskSession computes it (before the INFRA_ERROR rule)."""
    return _if.grade_instruction_following(extract_a(raw), record)


def gate_b(raw: str, record: dict) -> tuple[bool, list]:
    """Grader B's gate: (passed, per-constraint list). passed False means reward 0.0."""
    text = extract_b(raw)
    results = []
    for iid, kwargs in zip(record["instruction_id_list"], record["kwargs"]):
        verdict = check_b(iid, kwargs, text)
        if verdict is None:
            continue
        results.append((iid, verdict))
    return all(v is True for _, v in results), results


def load_rows() -> list[dict]:
    rows = []
    with DATA.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            rows.append({"uuid": rec["uuid"], "record": rec, "prompt": row["prompt"][0]["content"]})
    return rows
