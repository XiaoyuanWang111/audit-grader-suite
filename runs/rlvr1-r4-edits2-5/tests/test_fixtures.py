"""Regression tests: every fixture of audit/fixtures.jsonl against both graders and the replacement.

A fixture that a grader gets wrong today is marked xfail(strict=True) from known_failures.json, so
the change that fixes the grader must remove it from that list. Run from the audit folder:

    ../.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
sys.path.insert(0, str(AUDIT / "scripts"))

import fixture_lib as fl  # noqa: E402

FIXTURES = [json.loads(line) for line in (AUDIT / "fixtures.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
KNOWN = json.loads((HERE / "known_failures.json").read_text(encoding="utf-8"))


def _cases(grader):
    for fx in FIXTURES:
        marks = []
        if fx["id"] in KNOWN.get(grader, []):
            marks.append(pytest.mark.xfail(strict=True, reason=f"{fx[grader]['class']} {fx[grader]['decisions']}"))
        yield pytest.param(fx, id=fx["id"], marks=marks)


def _expected(fx):
    return fx["label"] == "pass"


@pytest.mark.parametrize("fx", list(_cases("skyrl")))
def test_skyrl_reward_checker(fx):
    kw, iid, resp = fx["kwargs"], fx["instruction_id"], fx["response"]
    if iid == "length_constraints:nth_paragraph_first_word" and kw and kw["nth_paragraph"] > kw["num_paragraphs"]:
        verdicts = {fl.verdict_skyrl(iid, kw, resp)[0] for _ in range(30)}
        assert verdicts == {_expected(fx)}
        return
    verdict, error = fl.verdict_skyrl(iid, kw, resp)
    assert error is None, error
    assert verdict == _expected(fx)


@pytest.mark.parametrize("fx", list(_cases("curation")))
def test_curation_gate_check(fx):
    verdict, error = fl.verdict_curation(fx["instruction_id"], fx["kwargs"], fx["response"])
    if verdict is None:
        pytest.skip("semantic constraint: judged by the LLM, no deterministic check")
    assert error is None, error
    assert verdict == _expected(fx)


@pytest.mark.parametrize("fx", [pytest.param(fx, id=fx["id"]) for fx in FIXTURES])
def test_replacement(fx):
    verdict = fl.verdict_replacement(fx["instruction_id"], fx["kwargs"], fx["response"], fx.get("reasoning_model", False))
    assert verdict == _expected(fx)
