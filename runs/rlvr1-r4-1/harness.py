"""Run the two graders under audit exactly as their pipelines apply them.

- SkyRL: ``final_answer_text`` (loaded from the pinned ``answer_extraction.py``
  with ``ast``, because the module imports packages that are not installed),
  then ``grade_instruction_following`` from the pinned SkyRL file.
- Task curation: ``_answer_text(text, True, strip_outer=False)`` (loaded from the
  pinned ``grade_judge.py`` with ``ast``), then every deterministic constraint's
  verifyit ``ifeval`` check, an exception counting as a failure (``_passes``).

Run from W with NLTK_DATA set (see case/TASK.md). Nothing here edits case/.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parents[1]
CASE = W / "case"
if str(CASE / "reference") not in sys.path:
    sys.path.insert(0, str(CASE / "reference"))
os.environ.setdefault("NLTK_DATA", str(CASE / "deps" / "nltk_data"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
    build_instruction,
    grade_instruction_following,
)
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

SEMANTIC = frozenset(
    {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
)  # graders.py SEMANTIC_INSTRUCTION_CONSTRAINTS (checked against the file in tests)
DATA = CASE / "data" / "rlvr1_instruction_following.jsonl"


def _load_functions(path: pathlib.Path, names: set[str]) -> dict:
    """Compile only the named top-level assignments and functions of a pinned file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            body.append(node)
    module = ast.Module(body=body, type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, str(path), "exec"), namespace)  # noqa: S102 - pinned source file
    return namespace


_AE = _load_functions(
    CASE / "reference" / "skyrl_gym" / "envs" / "nemotron_ultra" / "answer_extraction.py",
    {"REASONING_DELIMITERS", "final_answer_text"},
)
final_answer_text = _AE["final_answer_text"]
_GJ = _load_functions(CASE / "grader" / "verifyit" / "modes" / "grade_judge.py", {"_answer_text"})
_answer_text = _GJ["_answer_text"]


def load_rows() -> list[dict]:
    return [json.loads(line) for line in DATA.open(encoding="utf-8")]


def record_of(row: dict) -> dict:
    return json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])


def skyrl_grade(raw: str, record: dict, *, extract: bool = True) -> tuple[float, list[bool], list[str | None], str]:
    """SkyRL reward on a raw model text. Returns (reward, per-constraint, errors, graded text)."""
    text = final_answer_text(raw) if extract else raw
    reward, info = grade_instruction_following(text, record)
    return reward, info["follow_instruction_list"], info["instruction_errors"], text


def skyrl_check(instruction_id: str, kwargs: dict, text: str) -> bool:
    """One NVIDIA checker as grade_instruction_following applies it (no extraction)."""
    record = {"instruction_id_list": [instruction_id], "kwargs": [kwargs]}
    _, info = grade_instruction_following(text, record)
    return info["follow_instruction_list"][0]


def curation_constraints(record: dict) -> tuple[Constraint, ...]:
    return tuple(
        Constraint(name, {k: v for k, v in (args or {}).items() if v is not None})
        for name, args in zip(record["instruction_id_list"], record["kwargs"])
    )


def curation_gate(raw: str, record: dict, *, extract: bool = True) -> tuple[bool, list[bool | None], str]:
    """Task-curation deterministic gate. Returns (gate passed, per-constraint (None = judged), graded text).

    A gate pass means the judge decides the reward; a gate failure means reward 0.0.
    """
    text = _answer_text(raw, True, strip_outer=False) if extract else raw
    constraints = curation_constraints(record)
    resolve_checks(constraints)
    results: list[bool | None] = []
    for c in constraints:
        if c.name in SEMANTIC:
            results.append(None)
            continue
        check = resolve_checks((c,))[0][1]
        try:
            passed, _ = check(text, c.params)
        except Exception:  # noqa: BLE001 - _passes counts a crash as a failure
            passed = False
        results.append(bool(passed))
    return all(r is not False for r in results), results, text


def curation_check(instruction_id: str, kwargs: dict, text: str) -> bool:
    """One verifyit check as the gate applies it (no extraction); semantic ids are not gated."""
    c = Constraint(instruction_id, {k: v for k, v in kwargs.items() if v is not None})
    check = resolve_checks((c,))[0][1]
    try:
        passed, _ = check(text, c.params)
    except Exception:  # noqa: BLE001
        passed = False
    return bool(passed)
