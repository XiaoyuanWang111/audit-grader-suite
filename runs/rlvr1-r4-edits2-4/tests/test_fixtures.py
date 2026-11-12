"""Regression tests: every labeled fixture against the SkyRL reward, the task-curation gate and
the replacement grader. A verdict that differs from the label today is marked
xfail(strict=True) with its finding or decision id, so a grader fix must remove the mark.

Run from audit/:  ../.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q tests
"""
import json
import random
from pathlib import Path

import pytest

import harness as h
from contract_grader import ContractGrader

AUDIT = Path(__file__).resolve().parents[1]
FIXTURES = [json.loads(line) for line in open(AUDIT / "fixtures.jsonl", encoding="utf-8")]
WRONG = json.loads((AUDIT / "tests" / "expected_wrong.json").read_text(encoding="utf-8"))
CG = ContractGrader()


def verdict(grader, fx):
    iid, kw, response = fx["instruction_id"], fx["kwargs"], fx["response"]
    if grader == "skyrl":
        random.seed(0)
        passed, _ = h.skyrl_check(iid, kw, h.skyrl_text(response))
    elif grader == "gate":
        passed = h.gate_check(iid, kw, h.gate_text(response))
        if passed is None:
            pytest.skip("judged by the LLM judge in task curation; no deterministic check")
    else:
        passed = CG.check(iid, kw, CG.extract(response, fx["thinking"]))
    return "pass" if passed else "fail"


def cases():
    for fx in FIXTURES:
        for grader in ("skyrl", "gate", "replacement"):
            ref = WRONG.get(fx["id"], {}).get(grader)
            marks = [pytest.mark.xfail(strict=True, reason=ref)] if ref else []
            yield pytest.param(grader, fx, id=f"{grader}-{fx['id']}", marks=marks)


@pytest.mark.parametrize("grader,fx", list(cases()))
def test_verdict_matches_label(grader, fx):
    assert verdict(grader, fx) == fx["label"]


def error_cases():
    for fx in FIXTURES:
        ref = WRONG.get(fx["id"], {}).get("skyrl_error")
        marks = [pytest.mark.xfail(strict=True, reason=ref)] if ref else []
        yield pytest.param(fx, id=fx["id"], marks=marks)


@pytest.mark.parametrize("fx", list(error_cases()))
def test_skyrl_raises_no_exception(fx):
    _, error = h.skyrl_check(fx["instruction_id"], fx["kwargs"], h.skyrl_text(fx["response"]))
    assert error is None


@pytest.mark.xfail(strict=True, reason="G3")
def test_skyrl_verdict_does_not_depend_on_random_state():
    kw = {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "rain"}
    verdicts = set()
    for seed in range(40):
        random.seed(seed)
        verdicts.add(h.skyrl_check("length_constraints:nth_paragraph_first_word", kw, "Rain fell.\n\nRain stopped.")[0])
    assert len(verdicts) == 1
