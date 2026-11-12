"""Shared helpers: fixture ids, grader verdicts on a fixture, and finding-vs-decision classification."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(W / "audit" / "replacement"))

import contract_grader as cg  # noqa: E402
import graders as g  # noqa: E402


def fixture_id(instruction_id, kwargs, response, reasoning_model=False):
    payload = json.dumps([instruction_id, kwargs, response] + ([True] if reasoning_model else []),
                         ensure_ascii=False, sort_keys=True)
    return f"{instruction_id}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def verdict_skyrl(instruction_id, kwargs, response):
    """(verdict, error) through final_answer_text and grade_instruction_following."""
    text = g.final_answer_text(response)
    return g.skyrl_constraint(instruction_id, kwargs, text)


def verdict_curation(instruction_id, kwargs, response):
    text = g.curation_text(response)
    return g.curation_constraint(instruction_id, kwargs, text)


def verdict_replacement(instruction_id, kwargs, response, reasoning_model=False, decisions=None):
    return cg.grade_constraint(instruction_id, kwargs, cg.graded_text(response, reasoning_model), decisions)


def _options(name):
    alt = cg.ALTERNATIVES[name]
    return [cg.PROPOSED[name]] + (alt if isinstance(alt, list) else [alt])


def explain(instruction_id, kwargs, response, observed, reasoning_model=False):
    """Smallest set of non-proposed readings under which the contract gives `observed`, or None."""
    names = cg.DECISIONS_BY_CHECK[instruction_id]
    best = None
    for combo in itertools.product(*[_options(n) for n in names]):
        chosen = {n: v for n, v in zip(names, combo)}
        changed = [n for n in names if chosen[n] != cg.PROPOSED[n]]
        if best is not None and len(changed) >= len(best):
            continue
        try:
            v = verdict_replacement(instruction_id, kwargs, response, reasoning_model, chosen)
        except Exception:
            continue
        if v == observed:
            best = changed
    return best


def classify(instruction_id, kwargs, response, label, observed, error=None, reasoning_model=False):
    """'ok', 'decision', 'finding' or 'grading_failure' (exception), with the decision entries involved."""
    if error:
        return "grading_failure", []
    if observed is None:
        return "not_applicable", []
    if ("pass" if observed else "fail") == label:
        return "ok", []
    readings = explain(instruction_id, kwargs, response, observed, reasoning_model)
    if readings is None or reasoning_model or not readings:
        return "finding", []
    return "decision", readings
