"""Step 4 property and metamorphic tests: responses whose correct verdict is known by construction.

Each property runs against the replacement, the SkyRL (NVIDIA) checker and the verifyit check
(semantic ids are not gated by verifyit and are skipped there). A grader that fails a property is
marked xfail(strict=True); the reason names the contract it breaks. Hypothesis runs derandomized,
so a failure reproduces.
"""
import pathlib
import sys

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402

SETTINGS = settings(max_examples=150, derandomize=True, deadline=None, database=None,
                    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])

VOCAB = ["apple", "bright", "cloud", "dream", "early", "forest", "green", "house", "island", "jungle", "kettle",
         "lemon", "morning", "night", "ocean", "pencil", "quiet", "river", "stone", "tiger", "under", "violet",
         "winter", "yellow", "zebra"]
words = st.lists(st.sampled_from(VOCAB), min_size=1, max_size=12)


def sentence(ws):
    s = " ".join(ws)
    return s[0].upper() + s[1:] + "."


GRADERS = {
    "replacement": lambda c, kw, t: rp.check_constraint(c, kw, t),
    "skyrl": harness.skyrl_check,
    "verifyit": harness.curation_check,
}


def params(fails):
    out = []
    for g in GRADERS:
        marks = [pytest.mark.xfail(strict=True, reason=fails[g])] if g in fails else []
        out.append(pytest.param(g, marks=marks, id=g))
    return out


@pytest.mark.parametrize("g", params({}))
@SETTINGS
@given(words, st.integers(min_value=0, max_value=200))
def test_no_comma_insert(g, ws, pos):
    t = sentence(ws)
    assert GRADERS[g]("punctuation:no_comma", {}, t) is True
    i = pos % (len(t) + 1)
    assert GRADERS[g]("punctuation:no_comma", {}, t[:i] + "," + t[i:]) is False


@pytest.mark.parametrize("g", params({
    "skyrl": "word_once requires exactly one occurrence; the text says only 'Include keyword'",
    "verifyit": "word_once requires exactly one occurrence; the text says only 'Include keyword'"}))
@SETTINGS
@given(words, st.integers(min_value=1, max_value=4))
def test_word_once_repeats_still_include(g, ws, k):
    t = " ".join([sentence(ws + ["fix"])] * k)
    assert GRADERS[g]("keywords:word_once", {"keyword": "fix"}, t) is True


@pytest.mark.parametrize("g", params({
    "skyrl": "the first whitespace token keeps its trailing punctuation, so 'development,' is not 'development'"}))
@SETTINGS
@given(words, st.sampled_from([",", ":", ";", ".", "!", "?"]))
def test_first_word_with_punctuation(g, ws, p):
    t = "development" + p + " " + " ".join(ws) + "."
    assert GRADERS[g]("first_word:first_word_answer", {"first_word": "development"}, t) is True


@pytest.mark.parametrize("g", params({
    "verifyit": "counts blank-line paragraphs and ignores the instructed *** divider"}))
@SETTINGS
@given(st.lists(words, min_size=1, max_size=5))
def test_number_paragraphs_divider(g, paras):
    t = "\n***\n".join(sentence(p) for p in paras)
    assert GRADERS[g]("length_constraints:number_paragraphs", {"num_paragraphs": len(paras)}, t) is True


@pytest.mark.parametrize("g", params({
    "verifyit": "passes any response with two or more paragraphs; the text says there should be 2"}))
@SETTINGS
@given(st.lists(words, min_size=3, max_size=5))
def test_paragraphs2_more_than_two(g, paras):
    t = "\n\n".join(sentence(p) for p in paras)
    assert GRADERS[g]("paragraphs:paragraphs2", {}, t) is False


@pytest.mark.parametrize("g", params({
    "skyrl": "any whitespace token equal to its reverse counts, so a '-' bullet marker is a palindrome"}))
@SETTINGS
@given(st.lists(words, min_size=1, max_size=4))
def test_palindrome_not_from_bullets(g, items):
    t = "Items:\n" + "\n".join("- " + " ".join(i) for i in items)
    assert GRADERS[g]("keywords:palindrome", {}, t) is False


@pytest.mark.parametrize("g", params({
    "verifyit": "requires at least N lowercase words; the text says at most N times"}))
@SETTINGS
@given(st.lists(st.sampled_from(VOCAB), min_size=1, max_size=10, unique=True))
def test_lowercase_counting_no_lowercase_word(g, ws):
    t = " ".join(w.upper() for w in ws)
    assert GRADERS[g]("count:lowercase_counting", {"N": 2}, t) is True


@pytest.mark.parametrize("g", params({}))
@SETTINGS
@given(words)
def test_end_phrase(g, ws):
    kw = {"end_phrase": "Any other questions?"}
    assert GRADERS[g]("startend:end_checker", kw, sentence(ws) + " Any other questions?") is True
    assert GRADERS[g]("startend:end_checker", kw, sentence(ws) + " Any other questions? " + sentence(ws)) is False


@pytest.mark.parametrize("g", params({
    "verifyit": "accepts single quotation marks; the text asks for double quotation marks"}))
@SETTINGS
@given(words)
def test_quotation_single_quotes_fail(g, ws):
    assert GRADERS[g]("startend:quotation", {}, '"' + sentence(ws) + '"') is True
    assert GRADERS[g]("startend:quotation", {}, "'" + sentence(ws) + "'") is False


@pytest.mark.parametrize("g", params({
    "skyrl": "word_tokenize counts the comma as a word, shifting the position"}))
@SETTINGS
@given(words, words, st.integers(min_value=2, max_value=6))
def test_keyword_position_after_comma(g, first, rest, m):
    body = [w for w in rest][: m - 2] + ["filler"] * max(0, m - 2 - len(rest))
    s2 = "Well, " + " ".join(body + ["village", "here"]) + "."
    t = sentence(first) + " " + s2
    assert GRADERS[g]("keywords:keyword_specific_position", {"keyword": "village", "n": 2, "m": m}, t) is True


SAFE = ["apple", "cloud", "early", "green", "island", "kettle", "morning", "ocean", "quiet", "stone", "under",
        "winter", "yellow"]


@pytest.mark.parametrize("g", params({
    "verifyit": "checks adjacent duplicate words instead of consecutive first letters"}))
@SETTINGS
@given(st.lists(st.sampled_from(SAFE), min_size=2, max_size=12))
def test_no_adjacent_consecutive_detects_ab(g, ws):
    # SAFE first letters a c e g i k m o q s u w y: no two are consecutive
    t = " ".join(ws) + " a big " + " ".join(ws)
    assert GRADERS[g]("keywords:no_adjacent_consecutive", {}, t) is False


@pytest.mark.parametrize("g", params({
    "verifyit": "requires each sentence to contain a hyphen and no spaces, instead of hyphens between sentences"}))
@SETTINGS
@given(st.lists(words, min_size=2, max_size=5))
def test_sentence_hyphens_joined(g, sents):
    t = "-".join(sentence(s) for s in sents)
    assert GRADERS[g]("detectable_format:sentence_hyphens", {}, t) is True


@pytest.mark.parametrize("g", params({
    "skyrl": "the P.S. pattern has no line-start anchor, so a mid-line mention passes"}))
@SETTINGS
@given(words)
def test_postscript_mid_line_mention(g, ws):
    t = sentence(ws) + " See the P.S. section of my letter."
    assert GRADERS[g]("detectable_content:postscript", {"postscript_marker": "P.S."}, t) is False


@pytest.mark.parametrize("g", params({
    "skyrl": "every line starting with '-' counts as a bullet, including a '---' horizontal rule"}))
@SETTINGS
@given(st.lists(words, min_size=1, max_size=5))
def test_bullets_with_horizontal_rule(g, items):
    t = "\n".join("* " + " ".join(i) for i in items) + "\n\n---\n\nThat is all."
    assert GRADERS[g]("detectable_format:number_bullet_lists", {"num_bullets": len(items)}, t) is True
