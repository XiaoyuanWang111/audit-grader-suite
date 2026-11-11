"""Property and metamorphic tests (step 4). Responses are generated so that the contract's verdict is
known by construction. Hypothesis runs derandomized, without its example database.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import contract_grader as cg
import graders_under_audit as gu

SETTINGS = settings(derandomize=True, max_examples=150, database=None, deadline=None)
FILLER = ["river", "stone", "light", "green", "quiet", "table", "music", "north", "plain", "cloud"]


def A(check, kw, text):
    return gu.check_a(check, kw, gu.extract_a(text))


def B(check, kw, text):
    return gu.check_b(check, kw, gu.extract_b(text))


def R(check, kw, text):
    return cg.check(check, kw, text)


GRADERS = {"A": A, "B": B, "R": R}


def graders(xfail):
    """Parametrize over the three graders, marking the known failures xfail(strict=True)."""
    return pytest.mark.parametrize(
        "g", [pytest.param(g, marks=[pytest.mark.xfail(strict=True, reason=xfail[g])] if g in xfail else []) for g in GRADERS]
    )


@st.composite
def keyword_text(draw):
    """(text, k): k whole-word occurrences of 'sale' among filler and words that contain 'sale'."""
    k = draw(st.integers(0, 4))
    decoys = draw(st.integers(1, 3))
    tokens = draw(st.lists(st.sampled_from(FILLER), min_size=3, max_size=12))
    tokens += ["sale"] * k + draw(st.lists(st.sampled_from(["wholesale", "salesman", "resale"]), min_size=decoys, max_size=decoys))
    tokens = draw(st.permutations(tokens))
    return " ".join(tokens) + ".", k


@graders({"A": "F1: substring matches count as the keyword"})
@SETTINGS
@given(keyword_text())
def test_keyword_frequency_counts_whole_words(g, case):
    text, k = case
    kw = {"keyword": "sale", "frequency": 2, "relation": "at least"}
    assert GRADERS[g]("keywords:frequency", kw, text) is (k >= 2)


@graders({"A": "F2: exactly one occurrence required", "B": "F2: exactly one occurrence required"})
@SETTINGS
@given(st.integers(1, 4), st.lists(st.sampled_from(FILLER), min_size=2, max_size=8))
def test_word_once_passes_any_positive_count(g, n, filler):
    text = " ".join(filler + ["beer"] * n) + "."
    assert GRADERS[g]("keywords:word_once", {"keyword": "beer"}, text) is True


@graders({"A": "F9: a horizontal rule counts as a bullet", "B": "F9: a horizontal rule counts as a bullet"})
@SETTINGS
@given(st.integers(1, 5), st.sampled_from(["* * *", "- - -"]))
def test_bullet_count_ignores_horizontal_rules(g, n, rule):
    text = "\n".join(f"* item {i}" for i in range(n)) + "\n\n" + rule + "\n\nThe end."
    assert GRADERS[g]("detectable_format:number_bullet_lists", {"num_bullets": n}, text) is True


@graders({"B": "F14: punctuation after the last word is ignored"})
@SETTINGS
@given(st.lists(st.sampled_from(FILLER), min_size=1, max_size=8), st.sampled_from([".", "!", "?", "..."]))
def test_start_end_fails_after_trailing_punctuation(g, middle, punct):
    text = "Hello " + " ".join(middle) + " hello" + punct
    assert GRADERS[g]("keywords:start_end", None, text) is False


@graders({"B": "F31: the check requires at least N lowercase words"})
@SETTINGS
@given(st.integers(3, 6))
def test_lowercase_counting_fails_when_a_word_repeats_too_often(g, n):
    text = "Look: " + " ".join(["the"] * n) + " END."
    assert GRADERS[g]("count:lowercase_counting", {"N": 2}, text) is False


@graders({"B": "F22: three or more paragraphs pass"})
@SETTINGS
@given(st.integers(3, 6), st.sampled_from(["paragraphs:paragraphs", "paragraphs:paragraphs2"]))
def test_two_paragraph_checks_fail_extra_paragraphs(g, n, check):
    sep = "\n***\n" if check == "paragraphs:paragraphs" else "\n\n"
    text = sep.join(f"Paragraph number {i} is here." for i in range(n))
    assert GRADERS[g](check, {}, text) is False


@graders({"A": "F23: contractions count as two words"})
@SETTINGS
@given(st.integers(2, 12))
def test_word_count_treats_contractions_as_one_word(g, n):
    text = " ".join(["don't"] * n) + "."
    assert GRADERS[g]("length_constraints:number_words", {"num_words": n + 1, "relation": "less than"}, text) is True


@graders({})
@SETTINGS
@given(st.lists(st.sampled_from(FILLER), min_size=1, max_size=10), st.integers(0, 10))
def test_inserting_a_comma_fails_no_comma(g, filler, pos):
    words = list(filler)
    pos = min(pos, len(words))
    words.insert(pos, ",")
    text = " ".join(words)
    assert GRADERS[g]("punctuation:no_comma", None, text) is False


@graders({})
@SETTINGS
@given(st.lists(st.sampled_from(FILLER), min_size=1, max_size=10), st.sampled_from(["art", "Art", "ART"]))
def test_keyword_existence_ignores_case(g, filler, form):
    text = " ".join(filler + [form, "she"]) + "."
    assert GRADERS[g]("keywords:existence", {"keywords": ["art", "she"]}, text) is True


@graders({"B": "F32: one bracketed span is enough"})
@SETTINGS
@given(st.lists(st.sampled_from(FILLER), min_size=2, max_size=10))
def test_square_brackets_fail_when_one_word_is_bare(g, filler):
    text = " ".join(f"[{w}]" for w in filler[:-1]) + " " + filler[-1]
    assert GRADERS[g]("detectable_format:square_brackets", None, text) is False
