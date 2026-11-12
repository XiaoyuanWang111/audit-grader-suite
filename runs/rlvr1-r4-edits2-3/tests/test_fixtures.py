"""Regression tests: every labeled response in audit/fixtures.jsonl, on all three graders.

- The replacement grader (audit/replacement/contract_grader.py, proposed readings) must
  give every label.
- SkyRL's reward and the task-curation gate are run as their pipelines run them
  (audit/harness.py). A fixture that the current grader gets wrong is marked
  xfail(strict=True) from audit/tests/known_failures.json, so a change that fixes the
  grader must remove the mark. Judged constraints (count_unique, bigram_wrapping,
  response_language, letter_counting) have no task-curation check and are skipped there.

Run: cd audit && ../.venv/Scripts/python.exe -m pytest -q tests -p no:cacheprovider
(NLTK_DATA must point to case/deps/nltk_data; conftest.py sets it if missing).
"""

import json
import os

import pytest

import harness as h

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(AUDIT, "fixtures.jsonl"), encoding="utf-8") as f:
    FIXTURES = [json.loads(line) for line in f if line.strip()]
with open(os.path.join(AUDIT, "tests", "known_failures.json"), encoding="utf-8") as f:
    KNOWN = {k: set(v) for k, v in json.load(f).items()}


def _params(grader):
    out = []
    for fx in FIXTURES:
        marks = []
        if fx["id"] in KNOWN.get(grader, set()):
            marks.append(pytest.mark.xfail(strict=True, reason=f"{grader} contradicts the contract"))
        out.append(pytest.param(fx, id=fx["id"], marks=marks))
    return out


def _replacement(fx):
    if fx.get("raw"):
        out = h.contract_grade(fx["response"], [fx["instruction_id"]], [fx["kwargs"]], fx.get("prompt", ""),
                               bool(fx.get("reasoning_model")))
        return out["results"][0]
    return h.contract_check(fx["response"], fx["instruction_id"], fx["kwargs"], fx.get("prompt", ""))


@pytest.mark.parametrize("fx", [pytest.param(fx, id=fx["id"]) for fx in FIXTURES])
def test_replacement(fx):
    assert _replacement(fx) == (fx["label"] == "pass")


@pytest.mark.parametrize("fx", _params("skyrl"))
def test_skyrl(fx):
    out = h.skyrl_grade(fx["response"], [fx["instruction_id"]], [fx["kwargs"]])
    verdict = bool(out["results"][0]) and not out["infra_error"]
    assert verdict == (fx["label"] == "pass")


@pytest.mark.parametrize("fx", _params("tc"))
def test_task_curation_gate(fx):
    if fx["instruction_id"] in h.SEMANTIC:
        pytest.skip("judged constraint: no deterministic check")
    out = h.tc_gate(fx["response"], [fx["instruction_id"]], [fx["kwargs"]])
    assert out["results"][0] == (fx["label"] == "pass")
