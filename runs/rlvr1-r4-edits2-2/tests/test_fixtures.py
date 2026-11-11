"""Regression tests: every fixture on every grader, plus pipeline-level fixtures.

Run from the case folder:
  cd <W>/case
  NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 \
    ../.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q ../audit/tests
"""

import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures_data import FIXTURES  # noqa: E402
from known_wrong import KNOWN_WRONG  # noqa: E402
from verdicts import GRADERS, harness, nvidia_error, replacement, verdict  # noqa: E402


def _cases():
    for f in FIXTURES:
        for g in GRADERS:
            if g == "verifyit" and f["check"] in harness.SEMANTIC:
                continue
            ref = KNOWN_WRONG.get(f["id"][-12:], {}).get(g)
            marks = [pytest.mark.xfail(strict=True, reason=ref)] if ref else []
            yield pytest.param(f, g, id=f"{g}-{f['id']}", marks=marks)


@pytest.mark.parametrize("fixture,grader", list(_cases()))
def test_fixture(fixture, grader):
    assert verdict(grader, fixture["check"], fixture["kwargs"], fixture["response"]) == fixture["label"]


def test_known_wrong_ids_exist():
    suffixes = {f["id"][-12:] for f in FIXTURES}
    assert set(KNOWN_WRONG) <= suffixes


# ---- pipeline-level fixtures (the reward of a whole row on a raw model response)

NO_COMMA = {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}
TRUNCATED_REASONING = "Okay the user wants an answer without any commas so I should plan the reply first and then"


@pytest.mark.xfail(strict=True, reason="P1: unclosed reasoning (chat-template <think>) is graded as the answer")
def test_skyrl_truncated_reasoning_is_extraction_failure():
    # Qwen3 thinking: the chat template opens <think>, so a response cut off inside its reasoning has no marker.
    result = harness.skyrl_row(TRUNCATED_REASONING, NO_COMMA)
    assert result["reward"] == 0.0


@pytest.mark.xfail(strict=True, reason="P1: unclosed reasoning (chat-template <think>) is graded as the answer")
def test_curation_truncated_reasoning_is_extraction_failure():
    assert harness.verifyit_row(TRUNCATED_REASONING, NO_COMMA)["gate_pass"] is False


@pytest.mark.xfail(strict=True, reason="P2: an explicitly unclosed <think> is graded as empty text, which passes prohibitions")
def test_skyrl_unclosed_think_fails():
    assert harness.skyrl_row("<think>I will avoid commas and", NO_COMMA)["reward"] == 0.0


def test_replacement_unclosed_reasoning_fails():
    assert replacement.check("punctuation:no_comma", None, replacement.graded_text(TRUNCATED_REASONING, True)) is False


@pytest.mark.xfail(strict=True, reason="N16: an exception makes the SkyRL row an infrastructure error")
def test_nvidia_last_word_answer_empty_does_not_raise():
    assert nvidia_error("last_word:last_word_answer", {"last_word": "end"}, "") is None


INFEASIBLE_NTH = {
    "instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
    "kwargs": [{"first_word": "fuel", "nth_paragraph": 3, "num_paragraphs": 2}],
}


@pytest.mark.xfail(strict=True, reason="N17: nth_paragraph > num_paragraphs is re-drawn at random on every call")
def test_nvidia_infeasible_nth_paragraph_always_fails():
    text = "Fuel is costly.\n\nFuel prices rise."
    rewards = set()
    for seed in range(40):
        random.seed(seed)
        rewards.add(harness.skyrl_row(text, INFEASIBLE_NTH)["reward"])
    assert rewards == {0.0}


def test_replacement_infeasible_nth_paragraph_fails():
    kw = INFEASIBLE_NTH["kwargs"][0]
    assert replacement.check("length_constraints:nth_paragraph_first_word", kw, "Fuel is costly.\n\nFuel prices rise.") is False
