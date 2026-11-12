"""Run the two graders under audit exactly as their pipelines do, without editing case/.

SkyRL reward: skyrl_gym.envs.nemotron_ultra.answer_extraction.final_answer_text, then
grade_instruction_following (real modules; answer_extraction's import of envs/aime/utils.py,
which needs packages that are not installed, is satisfied by a stub module whose two
functions final_answer_text never calls).

Task-curation gate: verifyit.modes.grade_judge._answer_text and _passes, compiled from the
pinned grade_judge.py source (the module itself imports openai and cannot be imported here),
then verifyit's resolve_checks over the non-semantic constraints, as case/TASK.md shows.
"""
from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import re
import sys
import types
from pathlib import Path

W = Path("<W>")
CASE = W / "case"
os.environ.setdefault("NLTK_DATA", str(CASE / "deps" / "nltk_data"))
sys.dont_write_bytecode = True
if str(CASE / "reference") not in sys.path:
    sys.path.insert(0, str(CASE / "reference"))

# Stub for skyrl_gym.envs.aime.utils (only last_boxed_answer uses it; final_answer_text does not).
_stub = types.ModuleType("skyrl_gym.envs.aime.utils")
_stub.last_boxed_only_string = lambda text: None
_stub.remove_boxed = lambda text: text
sys.modules.setdefault("skyrl_gym.envs.aime.utils", _stub)

from skyrl_gym.envs.nemotron_ultra.answer_extraction import final_answer_text  # noqa: E402
from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
    build_instruction,
    grade_instruction_following,
)
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.modes.ifeval import CONSTRAINTS  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)  # graders.py SEMANTIC_INSTRUCTION_CONSTRAINTS


def _load_grade_judge_functions():
    path = CASE / "grader" / "verifyit" / "modes" / "grade_judge.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"_answer_text", "_passes"}]
    module = ast.Module(body=wanted, type_ignores=[])
    namespace = {"re": re, "logger": logging.getLogger("grade_judge"), "Check": object}
    exec(compile(module, str(path), "exec"), namespace)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return namespace["_answer_text"], namespace["_passes"], digest


_answer_text, _passes, GRADE_JUDGE_SHA256 = _load_grade_judge_functions()


# ---------------------------------------------------------------- SkyRL reward
def skyrl_text(raw: str) -> str:
    return final_answer_text(raw)


def skyrl_check(iid: str, kwargs: dict | None, text: str) -> tuple[bool, str | None]:
    """One constraint through grade_instruction_following (a one-constraint record)."""
    reward, details = grade_instruction_following(text, {"instruction_id_list": [iid], "kwargs": [kwargs]})
    return details["follow_instruction_list"][0], details["instruction_errors"][0]


def skyrl_row(record: dict, raw: str) -> dict:
    """The SkyRL session's verdict for one row: reward, per-constraint results, infra error."""
    text = skyrl_text(raw)
    reward, details = grade_instruction_following(text, record)
    infra = any(details["instruction_errors"])
    return {
        "reward": 0.0 if infra else reward,
        "results": details["follow_instruction_list"],
        "errors": details["instruction_errors"],
        "infra_error": infra,
    }


# ---------------------------------------------------------------- task-curation gate
def gate_text(raw: str) -> str:
    return _answer_text(raw, True, strip_outer=False)


def gate_constraint(iid: str, kwargs: dict | None) -> Constraint:
    return Constraint(iid, {k: v for k, v in (kwargs or {}).items() if v is not None})


def gate_check(iid: str, kwargs: dict | None, text: str) -> bool | None:
    """verifyit's deterministic check as the gate runs it; None for a judged (semantic) constraint."""
    if iid in SEMANTIC:
        return None
    constraint = gate_constraint(iid, kwargs)
    ((_, check),) = resolve_checks((constraint,))
    return bool(_passes(check, text, constraint.params))


def gate_check_any(iid: str, kwargs: dict | None, text: str) -> bool:
    """verifyit's check even for a semantic id (not run by the gate; used only for comparison)."""
    constraint = gate_constraint(iid, kwargs)
    ((_, check),) = resolve_checks((constraint,))
    return bool(_passes(check, text, constraint.params))


def gate_row(record: dict, raw: str) -> dict:
    text = gate_text(raw)
    results = [gate_check(i, k, text) for i, k in zip(record["instruction_id_list"], record["kwargs"])]
    det = [r for r in results if r is not None]
    return {"gate_pass": all(det), "results": results, "n_deterministic": len(det)}


def load_rows() -> dict[str, dict]:
    rows = {}
    with open(CASE / "data" / "rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
        for index, line in enumerate(f):
            row = json.loads(line)
            nu = row["extra_info"]["nemotron_ultra"]
            record = json.loads(nu["record_json"])
            record["_line"] = index
            rows[nu["uuid"]] = record
    return rows
