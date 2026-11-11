"""Regression tests: every fixture against each grader. Run from audit/:

    NLTK_DATA=.../case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 ../.venv/Scripts/python.exe -m pytest tests -q

A grader whose current verdict contradicts the contract label is xfail(strict=True): the change that
fixes the grader must remove the mark.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

GRADERS = {
    "nvidia": lambda fx: P.nvidia_check(fx["check"], fx["kwargs"], fx["response"])[0],
    "verifyit": lambda fx: P.verifyit_check(fx["check"], fx["kwargs"], fx["response"])[0],
    "replacement": lambda fx: C.check(fx["check"], fx["kwargs"], fx["response"]),
}


def _cases():
    for fx in FIXTURES:
        for grader in GRADERS:
            if grader in fx["na"]:
                continue
            marks = []
            if grader in fx["wrong"]:
                marks.append(pytest.mark.xfail(strict=True, reason=f"{fx['kind']} {fx['ref']}: {fx['note']}"))
            yield pytest.param(fx, grader, id=f"{grader}-{fx['id']}", marks=marks)


@pytest.mark.parametrize("fx,grader", list(_cases()))
def test_fixture(fx, grader):
    assert GRADERS[grader](fx) == fx["label"]


def test_replacement_passes_every_fixture():
    wrong = [fx["id"] for fx in FIXTURES if "replacement" in fx["wrong"]]
    assert wrong == []
