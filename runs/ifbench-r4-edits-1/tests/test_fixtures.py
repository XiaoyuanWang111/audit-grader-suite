"""Regression tests: every contract fixture against the grader under audit,
the reference implementation, and the replacement grader.

Run from W:
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests -q -p no:cacheprovider

Fixtures the current grader (or reference) gets wrong are xfail(strict=True):
a fix must remove the id from xfail_ids.py, and a regression fails the run.
"""
import os
import pathlib
import sys

import pytest

W = pathlib.Path(__file__).resolve().parents[2]
os.environ.setdefault("NLTK_DATA", str(W / "case" / "deps" / "nltk_data"))
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit"))

import common  # noqa: E402
from tests.fixtures_data import FIX  # noqa: E402
from tests.xfail_ids import XFAIL_GRADER, XFAIL_REFERENCE  # noqa: E402


def _params(xfail):
    out = []
    for f in FIX:
        marks = [pytest.mark.xfail(strict=True, reason="grader contradicts contract")] if f["id"] in xfail else []
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


def _verdict(fn, f):
    kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
    return "pass" if fn(f["check"], kw, prompt, f["response"]) else "fail"


@pytest.mark.parametrize("f", _params(XFAIL_GRADER))
def test_grader(f):
    assert _verdict(common.grade_grader, f) == f["label"]


@pytest.mark.parametrize("f", _params(XFAIL_REFERENCE))
def test_reference(f):
    import ref_runner
    assert _verdict(ref_runner.grade_reference, f) == f["label"]


@pytest.mark.parametrize("f", _params(set()))
def test_replacement(f):
    import replacement
    assert _verdict(replacement.grade, f) == f["label"]
