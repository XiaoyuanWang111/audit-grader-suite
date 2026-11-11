"""Regression tests: every fixture against the grader under audit (Marin's vendored IFBench).

Fixtures the current grader gets wrong carry pytest.mark.xfail(strict=True); a change that
fixes the grader must remove the mark (audit/tests/classification.py).

Run from W:
  PYTHONDONTWRITEBYTECODE=1 NLTK_DATA=$PWD/case/deps/nltk_data .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import graders as G  # noqa: E402
from classification import GRADER_WRONG  # noqa: E402
from fixtures import FIXTURES  # noqa: E402


def _params():
    out = []
    for f in FIXTURES:
        marks = []
        if f["id"] in GRADER_WRONG:
            kind, ref = GRADER_WRONG[f["id"]]
            marks.append(pytest.mark.xfail(strict=True, reason=f"{kind} {ref}"))
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


@pytest.mark.parametrize("f", _params())
def test_grader_matches_contract_label(f):
    got = G.grade_grader(f["check"], f["kwargs"], f["response"])
    assert ("pass" if got else "fail") == f["label"]


def test_classification_ids_exist():
    ids = {f["id"] for f in FIXTURES}
    assert set(GRADER_WRONG) <= ids
