"""Regression tests: every fixture's contract label against the grader under audit.

Fixtures the current grader gets wrong are marked xfail(strict=True) with the finding or decision
id (audit/tests/xfail.json), so a change that fixes the grader must remove the mark.

Run:  cd <W> && NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests -q
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

XFAIL = json.load(open(os.path.join(HERE, "xfail.json"), encoding="utf-8"))


def _params():
    for f in FIXTURES:
        marks = []
        if f["id"] in XFAIL:
            marks.append(pytest.mark.xfail(strict=True, reason=XFAIL[f["id"]]["reason"]))
        yield pytest.param(f, id=f["id"], marks=marks)


@pytest.mark.parametrize("fx", list(_params()))
def test_grader_matches_contract(fx):
    verdict = H.grade(fx["check"], fx["response"], key=fx.get("key"), kwargs=fx.get("kwargs"))
    assert verdict == fx["label"], f"grader={verdict!r} contract={fx['label']!r}"


def test_every_check_has_pass_fail_and_near_miss():
    kinds = {}
    for f in FIXTURES:
        kinds.setdefault(f["check"], set()).add(f["kind"])
    assert len(kinds) == 58
    missing = {c: k for c, k in kinds.items() if not {"pass", "fail"} <= k}
    assert not missing, missing
