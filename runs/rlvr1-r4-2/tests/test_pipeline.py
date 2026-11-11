"""Row-level tests: graded-text extraction (P1), determinism (F29), NLTK data pinning (P2).

Grader A's row reward is `grade_instruction_following(final_answer_text(raw), record)`; grader B's
gate runs every non-semantic check on `_answer_text(raw, True, strip_outer=False)`. The contract
(audit/CONTRACTS.md, section 1) grades a reasoning model's text after its last `</think>`, treats a
reasoning model's response without `</think>` as an extraction failure that fails every check, and
grades a non-reasoning model's whole response.
"""
import random

import pytest

import contract_grader as cg
import graders_under_audit as gu


def row(*constraints):
    return {"instruction_id_list": [c[0] for c in constraints], "kwargs": [c[1] for c in constraints]}


NO_COMMA = row(("punctuation:no_comma", None))
TAG = row(("keywords:existence", {"keywords": ["tag"]}))


def test_closed_reasoning_is_removed_by_all():
    raw = "<think>a, b, c</think>\n\nNo commas here."
    assert gu.reward_a(raw, NO_COMMA)[0] == 1.0
    assert gu.gate_b(raw, NO_COMMA)[0] is True
    assert cg.grade_row(NO_COMMA, raw, "", reasoning_model=True)[0] == 1.0


# The Qwen3 thinking template opens the reasoning block in the prompt, so a response cut inside its
# reasoning has neither marker (139 of the panel's 1,500 thinking responses).
UNCLOSED = "Okay so the user wants an answer without commas so I will plan it step by step and then write"


def test_contract_fails_unclosed_reasoning():
    reward, _, failed = cg.grade_row(NO_COMMA, UNCLOSED, "", reasoning_model=True)
    assert (reward, failed) == (0.0, True)


@pytest.mark.xfail(strict=True, reason="P1: grader A grades the unclosed reasoning as the answer")
def test_grader_a_fails_unclosed_reasoning():
    assert gu.reward_a(UNCLOSED, NO_COMMA)[0] == 0.0


@pytest.mark.xfail(strict=True, reason="P1: grader B grades the unclosed reasoning as the answer")
def test_grader_b_fails_unclosed_reasoning():
    assert gu.gate_b(UNCLOSED, NO_COMMA)[0] is False


# A non-reasoning model that writes a literal "<think>" in its answer (14 panel responses).
LITERAL = "Wrap the plan in a <think> tag before you answer."


def test_contract_grades_literal_marker_text_whole():
    assert cg.grade_row(TAG, LITERAL, "", reasoning_model=False)[0] == 1.0


@pytest.mark.xfail(strict=True, reason="P1: grader A empties a non-reasoning answer that mentions <think>")
def test_grader_a_grades_literal_marker_text():
    assert gu.reward_a(LITERAL, TAG)[0] == 1.0


@pytest.mark.xfail(strict=True, reason="P1: grader B empties a non-reasoning answer that mentions <think>")
def test_grader_b_grades_literal_marker_text():
    assert gu.gate_b(LITERAL, TAG)[0] is True


# The emptied text then passes checks that an empty answer satisfies (content-free passes).
@pytest.mark.xfail(strict=True, reason="P1: an unclosed <think> leaves '' and '' passes no_comma (grader A)")
def test_grader_a_unclosed_open_marker():
    assert gu.reward_a("<think>I will plan, then answer", NO_COMMA)[0] == 0.0


@pytest.mark.xfail(strict=True, reason="P1: an unclosed <think> leaves '' and '' passes no_comma (grader B)")
def test_grader_b_unclosed_open_marker():
    assert gu.gate_b("<think>I will plan, then answer", NO_COMMA)[0] is False


# F29: nth_paragraph > num_paragraphs (77 constraints) makes NVIDIA draw a random paragraph index.
NTH = row(("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "fight"}))
NTH_TEXT = "Fight one.\n\nFight two."


def _a_verdicts_under_seeds(n=20):
    out = set()
    for seed in range(n):
        random.seed(seed)
        out.add(gu.reward_a(NTH_TEXT, NTH)[0])
    return out


@pytest.mark.xfail(strict=True, reason="F29: grader A's verdict depends on the global random state")
def test_grader_a_deterministic_for_out_of_range_nth():
    assert len(_a_verdicts_under_seeds()) == 1


@pytest.mark.xfail(strict=True, reason="F29: grader A can pass a constraint the text makes unsatisfiable")
def test_grader_a_never_passes_unsatisfiable_nth():
    assert _a_verdicts_under_seeds() == {0.0}


def test_grader_b_and_contract_fail_unsatisfiable_nth():
    assert gu.gate_b(NTH_TEXT, NTH)[0] is False
    assert cg.grade_row(NTH, NTH_TEXT, "", reasoning_model=False)[0] == 0.0


# P2: the NLTK data must come from the pinned files; grader A downloads it when missing.
def test_pinned_punkt_tab_is_used():
    import os

    import nltk

    found = nltk.data.find("tokenizers/punkt_tab")
    assert os.path.normcase(str(gu.CASE / "deps" / "nltk_data")) in os.path.normcase(str(found))


@pytest.mark.xfail(strict=True, reason="P2: grader A calls nltk.download('punkt_tab') when the data is missing")
def test_grader_a_does_not_download_nltk_data(monkeypatch):
    import nltk

    from skyrl_gym.envs.nemotron_ultra import instruction_following as m

    calls = []

    def missing(*args, **kwargs):
        raise LookupError("missing")

    monkeypatch.setattr(nltk.data, "find", missing)
    monkeypatch.setattr(nltk, "download", lambda *a, **k: calls.append(a) or True)
    monkeypatch.setattr(m, "_NLTK_READY", False)
    m._ensure_nltk_data()
    assert calls == []
