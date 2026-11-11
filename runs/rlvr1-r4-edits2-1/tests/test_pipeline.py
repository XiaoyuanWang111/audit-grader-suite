"""Pipeline-stage fixtures: graded-text extraction and whole-row rewards.

Contract section 0: a response whose reasoning never closes is an extraction failure and fails every
check. The rows below are real rows of the data (uuids pinned in audit/frozen/row_hashes.tsv).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402

ROWS = P.load_rows()
# A row whose constraints are all negative: "refrain from the use of any commas" and capital words
# "less than 7 times"? Found by scanning; see test_negative_row_exists.
NEG_IDS = {"punctuation:no_comma", "punctuation:punctuation_dot", "punctuation:punctuation_exclamation",
           "keywords:forbidden_words"}


def _negative_row():
    for uuid, rec in ROWS.items():
        if set(rec["instruction_id_list"]) <= NEG_IDS:
            return rec
    raise AssertionError("no all-negative row")


UNCLOSED = "<think>\nThe user wants an answer without commas and dots so I will plan it"
TRUNCATED_THINKING = "The user wants an answer without commas and dots so I will plan it"


@pytest.mark.xfail(strict=True, reason="F37: unclosed reasoning becomes empty text, which passes negative checks")
def test_skyrl_unclosed_reasoning_fails_every_check():
    rec = _negative_row()
    reward, verdicts, errors, text = P.skyrl_grade(UNCLOSED, rec)
    assert reward == 0.0


@pytest.mark.xfail(strict=True, reason="F37: verifyit's gate passes the empty candidate on negative checks")
def test_gate_unclosed_reasoning_fails():
    rec = _negative_row()
    gate, verdicts, errors, text = P.verifyit_gate(UNCLOSED, rec)
    assert gate is False


@pytest.mark.xfail(strict=True, reason="F38: a truncated thinking-model response is graded as its reasoning")
def test_skyrl_truncated_thinking_is_extraction_failure():
    # Qwen3-4B-Thinking-2507's template opens <think> in the prompt, so its text has no opening marker.
    assert P.final_answer_text(TRUNCATED_THINKING) == ""


def test_replacement_extraction_failure_fails_every_check():
    rec = _negative_row()
    g = C.graded_text(TRUNCATED_THINKING, reasoning_model=True)
    assert g is None
    assert C.grade_text(g, rec["instruction_id_list"], rec["kwargs"]) == [False] * len(rec["kwargs"])


def test_negative_row_exists():
    rec = _negative_row()
    assert set(rec["instruction_id_list"]) <= NEG_IDS


@pytest.mark.xfail(strict=True, reason="F44: nth_paragraph > num_paragraphs is re-drawn at random on every call")
def test_nth_paragraph_out_of_range_is_deterministic():
    import random
    rec = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
           "kwargs": [{"first_word": "hole", "nth_paragraph": 4, "num_paragraphs": 3}]}
    text = "Intro here.\n\nHole digging is fun.\n\nThird part."
    rewards = set()
    for seed in range(40):
        random.seed(seed)
        rewards.add(P.grade_instruction_following(text, rec)[0])
    assert rewards == {0.0}


@pytest.mark.xfail(strict=True, reason="F39: empty graded text raises IndexError in last_word_answer (INFRA_ERROR)")
def test_last_word_answer_empty_does_not_raise():
    ok, err = P.nvidia_check("last_word:last_word_answer", {"last_word": "limit"}, "")
    assert err is None
