"""Every fixture against grader A (SkyRL reward, NVIDIA checkers), grader B (task-curation gate,
verifyit checks) and the replacement grader (audit/lib/contract_grader.py).

A fixture that a grader under audit gets wrong is marked xfail(strict=True) with the finding (F..)
or decision (D-..) that explains it (known_wrong.py); a fix to the grader must remove the mark.
"""
import pytest

import contract_grader as cg
import graders_under_audit as gu
from fixtures import FIXTURES
from known_wrong import KNOWN_WRONG


def _params(grader):
    out = []
    for f in FIXTURES:
        if grader == "B" and f["check"] in gu.SEMANTIC:
            continue
        reason = KNOWN_WRONG.get(f["id"], {}).get(grader)
        marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


@pytest.mark.parametrize("f", _params("A"))
def test_grader_a(f):
    assert gu.check_a(f["check"], f["kwargs"], gu.extract_a(f["response"])) is f["label"]


@pytest.mark.parametrize("f", _params("B"))
def test_grader_b(f):
    assert gu.check_b(f["check"], f["kwargs"], gu.extract_b(f["response"])) is f["label"]


@pytest.mark.parametrize("f", [pytest.param(f, id=f["id"]) for f in FIXTURES])
def test_replacement(f):
    assert cg.check(f["check"], f["kwargs"], f["response"], None, f["ctx"]) is f["label"]
    for decision in f["flip"]:
        assert cg.check(f["check"], f["kwargs"], f["response"], {decision: "B"}, f["ctx"]) is (not f["label"]), decision


def test_every_check_has_pass_and_fail_fixtures():
    ids = {f["check"] for f in FIXTURES}
    assert len(ids) == 47
    for check in ids:
        labels = {f["label"] for f in FIXTURES if f["check"] == check}
        assert labels == {True, False}, check


def test_known_wrong_matches_current_ids():
    assert set(KNOWN_WRONG) <= {f["id"] for f in FIXTURES}
