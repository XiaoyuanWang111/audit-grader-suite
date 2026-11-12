"""Pipeline-stage fixtures: graded-text extraction, row aggregation, determinism and exceptions.

Each test states the contract (CONTRACTS.md, section 0) it checks. Tests that the current graders
fail are xfail(strict=True) with the finding id.
"""
import random

import pytest

import harness as H
from contract_grader import graded_text, check

KEYWORDS_ROW = {"instruction_id_list": ["keywords:existence"], "kwargs": [{"keywords": ["quote", "teaching"]}]}
# A Qwen3-Thinking response cut by the token limit: the chat template opened <think>, the model never closed it.
UNCLOSED = "Okay, the user wants a quote about teaching. Let me think about which quote fits best and"
CLOSED = "Okay, the user wants a quote about teaching.\n</think>\n\nHere is my answer."
NTH_ROW = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
           "kwargs": [{"num_paragraphs": 3, "nth_paragraph": 4, "first_word": "crash"}]}
EMPTY_ROW = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "limit"}]}


def test_replacement_marks_unclosed_reasoning_as_extraction_failure():
    assert graded_text(UNCLOSED, reasoning_model=True) is None
    assert check("keywords:existence", {"keywords": ["quote", "teaching"]}, None) is False


@pytest.mark.xfail(strict=True, reason="F-G1: final_answer_text grades unclosed reasoning as the answer")
def test_a_unclosed_reasoning_gets_no_reward():
    assert H.a_row(UNCLOSED, KEYWORDS_ROW)[0] == 0.0


@pytest.mark.xfail(strict=True, reason="F-G1: _answer_text grades unclosed reasoning as the answer")
def test_b_unclosed_reasoning_fails_the_gate():
    assert H.b_gate(UNCLOSED, KEYWORDS_ROW)[0] is False


def test_closed_reasoning_is_removed_by_all_three():
    assert H.a_row(CLOSED, KEYWORDS_ROW)[0] == 0.0
    assert H.b_gate(CLOSED, KEYWORDS_ROW)[0] is False
    assert check("keywords:existence", {"keywords": ["quote", "teaching"]}, graded_text(CLOSED, True)) is False
    assert graded_text(CLOSED, True) == "Here is my answer."


@pytest.mark.xfail(strict=True, reason="F-G2: build_instruction redraws nth_paragraph from the global random state")
def test_a_verdict_does_not_depend_on_random_state():
    verdicts = set()
    for seed in range(30):
        random.seed(seed)
        verdicts.add(H.a_row("A.\n\nB.\n\nCrash.", NTH_ROW)[0])
    assert verdicts == {0.0}


@pytest.mark.xfail(strict=True, reason="F-G3: LastWordAnswerChecker raises IndexError on empty text")
def test_a_empty_text_raises_no_checker_error():
    _, detail = H.a_row("", EMPTY_ROW)
    assert detail["instruction_errors"] == [None]


def test_a_reward_is_all_of_its_constraint_verdicts():
    row = {"instruction_id_list": ["punctuation:no_comma", "keywords:existence"],
           "kwargs": [None, {"keywords": ["tea"]}]}
    assert H.a_row("I like tea.", row)[0] == 1.0
    assert H.a_row("I like tea, a lot.", row)[0] == 0.0


def test_b_gate_ignores_the_judged_ids():
    row = {"instruction_id_list": ["language:response_language", "punctuation:no_comma"],
           "kwargs": [{"language": "fr"}, None]}
    assert H.b_gate("I like tea.", row) == (True, [])
