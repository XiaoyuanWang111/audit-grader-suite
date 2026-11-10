"""The replacement grader (audit/replacement/grader.py, default switches = proposed readings) must
match every fixture's contract label, and, with a decision's switch set to "grader", must give the
grader's verdict on that decision's fixtures."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
sys.path.insert(0, os.path.dirname(HERE))
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402
from replacement import grader as X  # noqa: E402

GRADER_READING = {  # decision entry -> switch value that selects the grader's reading
    "D-word": "grader", "D-sentence": "grader", "D-paragraph": "grader", "D-markup": "grader",
    "D-conj-usage": "grader", "D-pronoun-set": "grader", "D-csv-payload": "grader",
    "D-custom-content": "grader", "D-list-extra": "grader", "D-list-labels": "grader",
    "D-reverse-extra": "grader", "D-balance": "grader", "D-overlap-measure": "grader",
    "D-trailing-ws": "grader", "D-change-case": "grader", "D-copy-case": "grader",
    "D-palindrome-distinct": "grader", "D-paren-closed": "grader",
}


def _kw(f):
    if f.get("key") is not None:
        return H.kwargs_for(f["key"], f["check"], int_cast=True), H.row(f["key"])["prompt"]
    return dict(f.get("kwargs") or {}), ""


NOT_FIXED = {"words:odd_even_syllables#f5da1d36": "F38: the replacement counts syllables with syllapy too"}


@pytest.mark.parametrize("fx", [pytest.param(f, id=f["id"], marks=[pytest.mark.xfail(strict=True, reason=NOT_FIXED[f["id"]])]
                                             if f["id"] in NOT_FIXED else []) for f in FIXTURES])
def test_replacement_matches_contract(fx):
    kw, prompt = _kw(fx)
    assert X.grade(fx["check"], fx["response"], kw, prompt) is fx["label"]


DEC = [f for f in FIXTURES if f.get("decision") in GRADER_READING]


@pytest.mark.parametrize("fx", DEC, ids=[f["id"] for f in DEC])
def test_switch_reproduces_grader_reading(fx):
    kw, prompt = _kw(fx)
    expected = H.grade(fx["check"], fx["response"], key=fx.get("key"), kwargs=fx.get("kwargs"), int_cast=True)
    got = X.grade(fx["check"], fx["response"], kw, prompt, switches={fx["decision"]: GRADER_READING[fx["decision"]]})
    assert got is expected
