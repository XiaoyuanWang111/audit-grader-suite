"""Adapters that run the two graders under audit exactly as their pipelines do.

Grader A (SkyRL): final_answer_text, then grade_instruction_following (NVIDIA checkers).
Grader B (task curation): grade_judge's _answer_text with reasoning stripping, then each
deterministic verifyit check; a crash counts as a failure (grade_judge._passes).

final_answer_text and _answer_text live in modules that import packages not installed here, so the
two functions are compiled from their exact source text (checked against the case manifest).
"""
from __future__ import annotations

import ast
import hashlib
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

from skyrl_gym.envs.nemotron_ultra.instruction_following import grade_instruction_following  # noqa: E402
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

SEMANTIC = frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                      "language:response_language", "letters:letter_counting"})  # graders.py

ANSWER_EXTRACTION = CASE / "reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py"
GRADE_JUDGE = CASE / "grader/verifyit/modes/grade_judge.py"
PINNED = {
    ANSWER_EXTRACTION: "7e88cf74d5013dd85eab460a6bf92f133ad74f43",
    GRADE_JUDGE: "3cb9b3104c8b5955870ea65d4c653f845e328f12",
}


def _git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _load_function(path: Path, name: str, extra: dict | None = None):
    assert _git_blob(path) == PINNED[path], f"{path} does not match its pinned blob"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Assign)) and (
        (isinstance(n, ast.FunctionDef) and n.name == name)
        or (isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "REASONING_DELIMITERS" for t in n.targets)))]
    module = ast.Module(body=nodes, type_ignores=[])
    namespace = {"re": re, **(extra or {})}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[name]


final_answer_text = _load_function(ANSWER_EXTRACTION, "final_answer_text")
_answer_text = _load_function(GRADE_JUDGE, "_answer_text")


def curation_text(raw: str) -> str:
    """grade_judge_candidate: _answer_text(candidate, strip_candidate_reasoning_blocks=True, strip_outer=False)."""
    return _answer_text(raw, True, strip_outer=False)


# ---------------------------------------------------------------- grader A


def skyrl_constraints(text: str, record: dict) -> tuple[list[bool], list[str | None]]:
    """Per-constraint verdicts and errors of grade_instruction_following on already-extracted text."""
    _, details = grade_instruction_following(text, record)
    return details["follow_instruction_list"], details["instruction_errors"]


def skyrl_constraint(instruction_id: str, kwargs: dict | None, text: str) -> tuple[bool, str | None]:
    verdicts, errors = skyrl_constraints(text, {"instruction_id_list": [instruction_id], "kwargs": [kwargs]})
    return verdicts[0], errors[0]


def skyrl_row(raw: str, record: dict) -> dict:
    """Reward as NemotronTaskSession forms it: any checker error is an INFRA_ERROR with reward 0."""
    text = final_answer_text(raw)
    verdicts, errors = skyrl_constraints(text, record)
    infra = any(errors)
    reward = 0.0 if infra else float(all(verdicts))
    return {"text": text, "verdicts": verdicts, "errors": errors, "infra_error": infra, "reward": reward}


# ---------------------------------------------------------------- grader B


def curation_constraint(instruction_id: str, kwargs: dict | None, text: str) -> tuple[bool | None, str | None]:
    """verifyit check verdict, or None for a semantic constraint (judged by the LLM, no gate check)."""
    if instruction_id in SEMANTIC:
        return None, None
    params = {k: v for k, v in (kwargs or {}).items() if v is not None}
    constraint = Constraint(instruction_id, params)
    [(constraint, check)] = resolve_checks((constraint,))
    try:
        passed, detail = check(text, constraint.params)
    except Exception as error:  # grade_judge._passes counts a crash as a failure
        return False, f"{type(error).__name__}: {error}"
    return bool(passed), None


def curation_row(raw: str, record: dict) -> dict:
    text = curation_text(raw)
    verdicts, errors = [], []
    for iid, kw in zip(record["instruction_id_list"], record["kwargs"]):
        v, e = curation_constraint(iid, kw, text)
        verdicts.append(v)
        errors.append(e)
    gate = [v for v in verdicts if v is not None]
    return {"text": text, "verdicts": verdicts, "errors": errors,
            "gate_passed": all(gate), "has_gate": bool(gate)}
