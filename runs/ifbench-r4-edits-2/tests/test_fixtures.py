"""Regression tests: every fixture against the grader under audit and the replacement.

Run (Git Bash, from W):
    NLTK_DATA=$PWD/case/deps/nltk_data .venv/Scripts/python.exe -m pytest -q audit/tests

Fixtures that the current grader gets wrong are marked xfail(strict=True) with the finding or
decision id (audit/tests/xfail_grader.json), so a change that fixes the grader must remove
the mark.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import graders  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

XFAIL = json.load(open(os.path.join(HERE, "xfail_grader.json"), encoding="utf-8"))
PROMPT = "fixture prompt"


def _v(x):
    return "pass" if x is True else "fail" if x is False else str(x)


def _params(with_xfail):
    out = []
    for f in FIXTURES:
        marks = []
        if with_xfail and f["id"] in XFAIL:
            marks.append(pytest.mark.xfail(strict=True, reason=XFAIL[f["id"]]))
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


@pytest.mark.parametrize("f", _params(True))
def test_grader_strict(f):
    assert _v(graders.grader_strict(f["check"], f["kwargs"], PROMPT, f["response"])) == f["label"]


@pytest.mark.parametrize("f", _params(False))
def test_replacement(f):
    assert _v(graders.replacement(f["check"], f["kwargs"], PROMPT, f["response"])) == f["label"]


def test_every_check_has_pass_and_fail_fixtures():
    by = {}
    for f in FIXTURES:
        by.setdefault(f["check"], set()).add(f["label"])
    assert len(by) == 58 and all(v == {"pass", "fail"} for v in by.values())
