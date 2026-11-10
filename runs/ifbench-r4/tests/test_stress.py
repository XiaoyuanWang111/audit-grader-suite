"""Step 4 regression tests: loose transform, metamorphic edits and content-free responses.

Each test states the contract verdict; tests the current grader fails are xfail(strict=True).
"""
import pytest

import ifbaudit as A

LOOSE_CASES = [
    # (id, check, kwargs, text, contract label, tag)
    ("loose-wordcount-lastline", "count:word_count_range", {"min_words": 5.0, "max_words": 5.0},
     "one two three four five\nsix seven eight", False, "F-loose-content"),
    ("loose-nowhitespace-firstline", "format:no_whitespace", {},
     "Two words\nOneword", False, "F-loose-content"),
    ("loose-sentencetype-firstline", "ratio:sentence_type", {},
     "Really? Truly?\nI agree. It works. Is it?", False, "F-loose-content"),
]


def loose_G(check, kw, text):
    """Grader loose verdict for one instruction: any of the eight variants passes."""
    for cand in A.loose_variants(text):
        if cand.strip() and A.check_G(check, kw, cand):
            return True
    return False


@pytest.mark.parametrize("case", [pytest.param(c, id=c[0], marks=pytest.mark.xfail(strict=True, reason=c[5]))
                                  for c in LOOSE_CASES])
def test_loose_matches_contract(case):
    _, check, kw, text, label, _ = case
    assert A.check_G(check, kw, text) is False  # strict already fails
    assert loose_G(check, kw, text) == label


METAMORPHIC = [
    # (id, check, kwargs, passing text, edited text the contract treats the same, tag)
    ("crlf-newline", "format:newline", {}, "Hello\n\nworld.", "Hello\r\n\r\nworld.", "F-crlf"),
    ("curly-apostrophe-options", "format:options", {"options": "I know or I don't know"},
     "I don't know", "I don’t know", "F-curly-apostrophe"),
    ("curly-apostrophe-prime", "words:prime_lengths", {}, "It's", "It’s", "F-curly-apostrophe"),
]


@pytest.mark.parametrize("case", [pytest.param(c, id=c[0], marks=pytest.mark.xfail(strict=True, reason=c[5]))
                                  for c in METAMORPHIC])
def test_metamorphic_invariance(case):
    _, check, kw, text, edited, _ = case
    assert A.check_G(check, kw, text) is True
    assert A.check_G(check, kw, edited) is True


CONTENT_FREE = [
    ("repeated-word-subbullets", "format:sub-bullets", {}, " ".join(["the"] * 200), "F-subbullets-check"),
    ("repeated-word-balance", "ratio:sentence_balance", {}, " ".join(["the"] * 200), "F-balance-zero"),
    ("repeated-word-type", "ratio:sentence_type", {}, " ".join(["the"] * 200), "F-ratio-zero"),
]


@pytest.mark.parametrize("case", [pytest.param(c, id=c[0], marks=pytest.mark.xfail(strict=True, reason=c[4]))
                                  for c in CONTENT_FREE])
def test_content_free_fails(case):
    _, check, kw, text, _ = case
    assert A.check_G(check, kw, text) is False


def test_empty_fails_every_check():
    for row in A.ROWS:
        assert A.grade_G(row, "") == [False] * len(row["instruction_id_list"])
        assert A.grade_G(row, "  \n ") == [False] * len(row["instruction_id_list"])
