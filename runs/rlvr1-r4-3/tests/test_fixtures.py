"""Regression tests: every fixture of audit/fixtures.jsonl against the replacement and both graders.

A fixture's label comes from the contract. The replacement must match every label. Grader A
(SkyRL reward, NVIDIA checkers) and grader B (verifyit gate) carry `xfail(strict=True)` on each
fixture they currently get wrong, with the class from audit/tests/expectations.json (a finding, or
the decision entries whose non-proposed readings give the grader's verdict); a change that fixes the
grader must remove the mark.

Run from W:  .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests
"""
import json
import os
import sys

import pytest

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
import fixture_lib as F  # noqa: E402

with open(os.path.join(AUDIT, "fixtures.jsonl"), encoding="utf-8") as f:
    FIXTURES = [json.loads(line) for line in f]
with open(os.path.join(AUDIT, "tests", "expectations.json"), encoding="utf-8") as f:
    EXPECT = json.load(f)


def _params(grader):
    out = []
    for fx in FIXTURES:
        e = EXPECT[fx["id"]]
        cls = e.get(grader + "_class") if grader != "R" else "ok"
        if cls is None:
            continue  # grader B has no deterministic check for a judged id
        marks = [] if cls == "ok" else [pytest.mark.xfail(strict=True, reason=cls)]
        out.append(pytest.param(fx, id=fx["id"], marks=marks))
    return out


def _verdict(fx, grader):
    res = F.grade_all(fx["instruction_id"], fx["kwargs"], fx["response"], fx.get("thinking"))
    return res[grader]


def test_expectations_cover_fixtures():
    assert {fx["id"] for fx in FIXTURES} == set(EXPECT)
    for fx in FIXTURES:
        assert fx["id"] == F.fixture_id(fx["instruction_id"], fx["kwargs"], fx["response"], fx.get("thinking"))


@pytest.mark.parametrize("fx", _params("R"))
def test_replacement(fx):
    assert _verdict(fx, "R") == F.label_bool(fx["label"])


@pytest.mark.parametrize("fx", _params("A"))
def test_grader_a_skyrl_reward(fx):
    assert _verdict(fx, "A") == F.label_bool(fx["label"])


@pytest.mark.parametrize("fx", _params("B"))
def test_grader_b_verifyit_gate(fx):
    assert _verdict(fx, "B") == F.label_bool(fx["label"])
