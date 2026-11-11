"""The two graders under audit, run as their pipelines run them.

- SkyRL: `final_answer_text` (answer_extraction.py) then `grade_instruction_following`
  (instruction_following.py), which runs NVIDIA's checkers.
- Task curation: verifyit `_answer_text(..., strip_reasoning=True, strip_outer=False)` (grade_judge.py,
  as `grade_judge_candidate` calls it) then every non-semantic constraint's verifyit check, with an
  exception counted as a failure (`_passes`).

`final_answer_text` and `_answer_text` live in modules that import packages that are not installed, so
their source is taken verbatim from the case files with `ast` and executed alone.
"""
from __future__ import annotations

import ast
import json
import os
import sys

CASE = "<W>/case"
if os.path.join(CASE, "reference") not in sys.path:
    sys.path.insert(0, os.path.join(CASE, "reference"))
os.environ.setdefault("NLTK_DATA", CASE + "/deps/nltk_data")

SEMANTIC = frozenset({"count:count_unique", "detectable_format:bigram_wrapping",
                      "language:response_language", "letters:letter_counting"})  # graders.py


def _load_functions(path: str, names: set[str], extra_globals: dict) -> dict:
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    keep = [n for n in tree.body
            if (isinstance(n, (ast.FunctionDef, ast.Assign)) and
                (getattr(n, "name", None) in names or
                 any(isinstance(t, ast.Name) and t.id in names for t in getattr(n, "targets", []))))]
    module = ast.Module(body=keep, type_ignores=[])
    ns = dict(extra_globals)
    exec(compile(module, path, "exec"), ns)
    return ns


import re as _re  # noqa: E402

_ae = _load_functions(CASE + "/reference/skyrl_gym/envs/nemotron_ultra/answer_extraction.py",
                      {"REASONING_DELIMITERS", "final_answer_text"}, {"re": _re})
final_answer_text = _ae["final_answer_text"]
_gj = _load_functions(CASE + "/grader/verifyit/modes/grade_judge.py", {"_answer_text"}, {"re": _re})
_answer_text = _gj["_answer_text"]


def verifyit_candidate(raw: str) -> str:
    return _answer_text(raw, True, strip_outer=False)


from skyrl_gym.envs.nemotron_ultra.instruction_following import (  # noqa: E402
    _ensure_nltk_data, build_instruction, grade_instruction_following)
from verifyit.modes.grade_ifeval import resolve_checks  # noqa: E402
from verifyit.modes.ifeval import CONSTRAINTS  # noqa: E402
from verifyit.spec import Constraint  # noqa: E402

_ensure_nltk_data()


def clean_kwargs(kw):
    return {k: v for k, v in (kw or {}).items() if v is not None}


def nvidia_check(iid: str, kw: dict, text: str):
    """One NVIDIA checker as grade_instruction_following runs it: (passed, error)."""
    try:
        inst = build_instruction(iid, clean_kwargs(kw))
        return bool(inst.check_following(text)), None
    except Exception as error:  # the reward counts it False; the session reports INFRA_ERROR
        return False, f"{type(error).__name__}: {error}"


def verifyit_check(iid: str, kw: dict, text: str):
    """One verifyit check as grade_judge_candidate runs it: (passed, error)."""
    c = Constraint(iid, clean_kwargs(kw))
    ((constraint, fn),) = resolve_checks((c,))
    try:
        passed, _detail = fn(text, constraint.params)
        return bool(passed), None
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"


def skyrl_grade(raw: str, record: dict):
    """(reward, per-constraint verdicts, errors, graded text) as the session computes them."""
    text = final_answer_text(raw)
    reward, info = grade_instruction_following(text, record)
    return reward, info["follow_instruction_list"], info["instruction_errors"], text


def verifyit_gate(raw: str, record: dict):
    """(gate passed, per-constraint verdicts with None for judged ones, errors, graded text)."""
    text = verifyit_candidate(raw)
    verdicts, errors = [], []
    for iid, kw in zip(record["instruction_id_list"], record["kwargs"]):
        if iid in SEMANTIC:
            verdicts.append(None)
            errors.append(None)
            continue
        ok, err = verifyit_check(iid, kw, text)
        verdicts.append(ok)
        errors.append(err)
    gate = all(v for v in verdicts if v is not None)
    return gate, verdicts, errors, text


def load_rows():
    rows = {}
    with open(CASE + "/data/rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            rec["_index"] = i
            rows[rec["uuid"]] = rec
    return rows
