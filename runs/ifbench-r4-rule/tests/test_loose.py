"""Score-level transform: the grader's loose mode against the contract.

Loose grading passes a check when any of 8 variants passes: the response with its first line,
last line or both removed, each with or without every '*' deleted. The contract grades the whole
graded text, so a loose pass is consistent with it only when the deleted text is markup that G8
ignores. Fixtures whose loose verdict contradicts the contract are xfail(strict=True) (F42).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import harness as H  # noqa: E402

LOOSE = [
    # (check, kwargs, response, contract label, grader-loose-known-wrong)
    ("format:sub-bullets", {}, "* Apples\n* Pears", False, True),
    ("format:no_whitespace", {}, "Sure!\nabc", False, True),
    ("words:start_verb", {}, "Here is my answer:\nImagine a world of peace.", False, True),
    ("count:word_count_range", {"min_words": 3.0, "max_words": 5.0}, "This title line has words\nOne two three.", False, True),
    ("format:title_case", {}, "Sure, here it is:\nThe Lord Of The Rings", False, True),
    ("words:words_position", {"keyword": "vibrant"}, "A vibrant city has vibrant streets.\nThanks for asking", False, True),
    # consistent with the contract: only markup is deleted (G8)
    ("words:start_verb", {}, "**Imagine** a world of peace.", True, False),
]


@pytest.mark.parametrize("check,kw,resp,label,known", [
    pytest.param(*c, id=f"{c[0]}#{i}", marks=[pytest.mark.xfail(strict=True, reason="F42")] if c[4] else [])
    for i, c in enumerate(LOOSE)])
def test_loose_matches_contract(check, kw, resp, label, known):
    assert H.grade(check, resp, kwargs=kw, mode="loose") is label


def test_strict_fails_the_loose_examples():
    for check, kw, resp, label, known in LOOSE:
        if known:
            assert H.grade(check, resp, kwargs=kw, mode="strict") is False, check
