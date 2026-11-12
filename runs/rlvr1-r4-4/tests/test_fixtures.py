"""Every hand-written fixture against grader A (NVIDIA checkers as SkyRL runs them), grader B
(verifyit checks of the task-curation gate) and the replacement R.

A fixture that a grader gets wrong today is marked xfail(strict=True) with the finding or decision
entries that explain it (tests/known_failures.json), so a grader change that fixes it must remove
the mark. Grader B is not tested on the four ids that the gate sends to the LLM judge.
"""
import json
import os
import random

import pytest

import harness as H
from fixtures_data import FIXTURES

KNOWN = json.load(open(os.path.join(os.path.dirname(__file__), "known_failures.json"), encoding="utf-8"))


def _params():
    for fx in FIXTURES:
        for g in ("A", "B", "R"):
            if g == "B" and fx["instruction_id"] in H.SEMANTIC:
                continue
            reason = KNOWN.get(f"{g}|{fx['id']}")
            marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
            yield pytest.param(g, fx, id=f"{g}-{fx['id']}", marks=marks)


@pytest.mark.parametrize("grader,fx", list(_params()))
def test_fixture(grader, fx):
    iid, kw, resp = fx["instruction_id"], fx["kwargs"], fx["response"]
    if grader == "A":
        random.seed(0)  # F-G2: grader A reads the global random state on some rows
        verdict, _ = H.a_check(iid, kw, resp)
    elif grader == "B":
        verdict, _ = H.b_check(iid, kw, resp)
    else:
        verdict = H.r_check(iid, kw, resp)
    assert ("pass" if verdict else "fail") == fx["label"]


def test_known_failures_are_current():
    ids = {fx["id"] for fx in FIXTURES}
    assert all(k.split("|", 1)[1] in ids for k in KNOWN)
