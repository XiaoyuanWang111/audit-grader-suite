"""Metamorphic tests: a contract-ignored edit of a passing fixture must keep the grader's pass.

Known flips are xfail(strict=True) from audit/tests/property_xfail.json (regenerate with
audit/scripts/step4_properties.py). Grading uses int-cast kwargs so that F01 (TypeError on float
kwargs) does not mask the property under test.
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
from properties import TRANSFORMS  # noqa: E402

XFAIL = json.load(open(os.path.join(HERE, "property_xfail.json"), encoding="utf-8"))
REASON = {
    "trailing_newline": "F28/F29/D-trailing-ws: trailing newline",
    "curly_quotes": "F32: typographic quotes",
    "bold_first_word": "D-markup: bold first word",
    "emdash_between_words": "F36: em dash counted as a word",
}


def _cases():
    for f in FIXTURES:
        if f["label"] is not True:
            continue
        kw = dict(key=f.get("key"), kwargs=f.get("kwargs"))
        if H.grade(f["check"], f["response"], int_cast=True, **kw) is not True:
            continue  # the base fixture already fails; covered by test_fixtures
        for name, (fn, ok) in TRANSFORMS.items():
            t = fn(f["response"])
            if not ok(f["check"]) or t == f["response"]:
                continue
            pid = f"{f['id']}|{name}"
            marks = [pytest.mark.xfail(strict=True, reason=REASON[name])] if pid in XFAIL else []
            yield pytest.param(f, t, kw, id=pid, marks=marks)


@pytest.mark.parametrize("fx,transformed,kw", list(_cases()))
def test_verdict_invariant(fx, transformed, kw):
    assert H.grade(fx["check"], transformed, int_cast=True, **kw) is True
