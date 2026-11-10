"""Fixtures as regression tests.

test_grader: the grader under audit must give each fixture its contract label.
Fixtures that the current grader gets wrong (tagged F-... findings and D-... decisions)
are marked xfail(strict=True), so a change that fixes the grader must remove the mark.

test_replacement_*: the replacement grader passes every fixture under the proposed
readings, and every non-decision fixture under the as-is switches.

Run: .venv/Scripts/python.exe -I -X utf8 -m pytest -q -p no:cacheprovider audit/tests
"""
import pytest

import ifbaudit as A
import replacement as X
from fixtures import FIXTURES, resolve


def _params(only_untagged_ok=False):
    out = []
    for f in FIXTURES:
        marks = []
        if f["tag"] is not None:
            marks.append(pytest.mark.xfail(strict=True, reason=f["tag"]))
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


@pytest.mark.parametrize("f", _params())
def test_grader(f):
    kw, prompt = resolve(f, A.ROWS)
    assert A.check_G(f["check"], kw, f["text"], prompt) == f["label"]


@pytest.mark.parametrize("f", [pytest.param(f, id=f["id"]) for f in FIXTURES])
def test_replacement_proposed(f):
    kw, prompt = resolve(f, A.ROWS)
    assert X.check(f["check"], kw, f["text"], prompt, X.PROPOSED) == f["label"]


@pytest.mark.parametrize("f", [pytest.param(f, id=f["id"]) for f in FIXTURES
                               if not (f["tag"] or "").startswith("D-")])
def test_replacement_as_is(f):
    kw, prompt = resolve(f, A.ROWS)
    assert X.check(f["check"], kw, f["text"], prompt) == f["label"]


@pytest.mark.xfail(strict=True, reason="F-csv-quotes-exception: the exception leaves grader.py's per-prompt loop")
def test_grader_harness_survives_checker_exception():
    from fixtures import CSV_Q_EMPTY
    row = A.ROWS[275]
    assert row["instruction_id_list"] == ["custom:csv_quotes"]
    assert A.grade_G(row, CSV_Q_EMPTY) == [False]


def test_every_check_has_pass_and_fail_fixtures():
    checks = set(A.G_registry.INSTRUCTION_DICT)
    have = {}
    for f in FIXTURES:
        have.setdefault(f["check"], set()).add(f["label"])
    assert checks == set(have)
    assert all(v == {True, False} for v in have.values())
