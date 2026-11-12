"""Shared helpers: fixture ids, grading a fixture with the three graders, and classifying wrong verdicts."""
from __future__ import annotations

import hashlib
import itertools
import json

import graders as G
from replacement import contracts_grader as R

COMMON = ["D-outer-whitespace", "D-empty"]
RELEVANT = {
    "change_case:capital_word_frequency": ["D-word", "D-capital-word"],
    "change_case:english_capital": ["D-english"],
    "change_case:english_lowercase": ["D-english"],
    "combination:two_responses": ["D-two-responses-different", "D-separator-edge"],
    "copy:repeat_phrase": ["D-word", "D-repeat-center", "D-repeat-original"],
    "count:count_unique": ["D-word", "D-unique-case"],
    "count:counting_composition": ["D-word", "D-sentence", "D-divider", "D-divider-inline", "D-separator-edge"],
    "count:lowercase_counting": ["D-word", "D-lowercase-counting-scope"],
    "detectable_content:number_placeholders": ["D-placeholder"],
    "detectable_content:postscript": ["D-postscript-marker", "D-postscript-position", "D-postscript-case"],
    "detectable_format:bigram_wrapping": ["D-word", "D-bigram"],
    "detectable_format:constrained_response": ["D-constrained"],
    "detectable_format:json_format": ["D-json"],
    "detectable_format:multiple_sections": ["D-sections-case", "D-sections-numbering", "D-sections-preamble"],
    "detectable_format:number_bullet_lists": ["D-bullets"],
    "detectable_format:number_highlighted_sections": ["D-highlight"],
    "detectable_format:sentence_hyphens": ["D-sentence", "D-hyphens-single"],
    "detectable_format:square_brackets": ["D-word", "D-square-brackets"],
    "detectable_format:title": ["D-title"],
    "first_word:first_word_answer": ["D-word", "D-first-last-case", "D-first-last-markup"],
    "first_word:first_word_sent": ["D-word", "D-sentence", "D-first-last-case", "D-first-last-markup"],
    "keywords:existence": ["D-keyword-match"],
    "keywords:forbidden_words": ["D-keyword-match"],
    "keywords:frequency": ["D-keyword-match"],
    "keywords:keyword_specific_position": ["D-word", "D-sentence"],
    "keywords:letter_frequency": ["D-letter-case"],
    "keywords:no_adjacent_consecutive": ["D-word", "D-consecutive-order"],
    "keywords:palindrome": ["D-word", "D-palindrome"],
    "keywords:start_end": ["D-word", "D-start-end-case", "D-start-end-leading", "D-start-end-single"],
    "keywords:word_count_different_numbers": ["D-keyword-match", "D-count-exact"],
    "keywords:word_once": ["D-keyword-match"],
    "language:response_language": ["D-language"],
    "last_word:last_word_answer": ["D-word", "D-first-last-case", "D-first-last-markup"],
    "last_word:last_word_sent": ["D-word", "D-sentence", "D-first-last-case", "D-first-last-markup"],
    "length_constraints:nth_paragraph_first_word": ["D-word", "D-paragraph-blank", "D-first-last-case", "D-first-last-markup"],
    "length_constraints:number_paragraphs": ["D-divider", "D-divider-inline", "D-separator-edge"],
    "length_constraints:number_sentences": ["D-sentence"],
    "length_constraints:number_words": ["D-word"],
    "letters:letter_counting": ["D-letters-count"],
    "letters:letter_counting2": ["D-letter-case"],
    "paragraphs:paragraphs": ["D-divider", "D-divider-inline", "D-separator-edge"],
    "paragraphs:paragraphs2": ["D-paragraph-blank"],
    "punctuation:no_comma": ["D-comma-chars"],
    "punctuation:punctuation_dot": ["D-dot-chars"],
    "punctuation:punctuation_exclamation": ["D-exclamation-chars"],
    "startend:end_checker": ["D-end-phrase", "D-end-phrase-case"],
    "startend:quotation": ["D-quotation"],
}
UNSWITCHED = {"D-english", "D-language"}  # approximated, no B implementation


def fixture_id(iid: str, kwargs: dict, response: str, thinking: bool | None = None) -> str:
    payload = json.dumps([iid, kwargs, response] + ([thinking] if thinking is not None else []),
                         ensure_ascii=False, sort_keys=True)
    return iid + ":" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def texts(raw: str, thinking: bool | None):
    """Graded text for A, B and the replacement. thinking None means the response is already graded text."""
    if thinking is None:
        return raw, raw, raw
    return G.final_answer_text(raw), G.answer_text_b(raw), R.extract(raw, thinking)


def grade_all(iid, kwargs, raw, thinking=None):
    ta, tb, tr = texts(raw, thinking)
    a, a_err = G.check_a(iid, kwargs, ta)
    b, b_detail = G.check_b(iid, kwargs, tb)
    r = False if tr is None else G.check_r(iid, kwargs, tr)
    return {"A": a, "A_error": a_err, "B": b, "B_detail": b_detail, "R": r}


def classify(iid, kwargs, raw, thinking, grader_verdict: bool):
    """'decision:<entries>' if non-proposed readings of relevant entries give the grader's verdict, else 'finding'."""
    _, _, tr = texts(raw, thinking)
    if tr is None:
        return "finding"
    rel = [d for d in COMMON + RELEVANT[iid] if d not in UNSWITCHED]
    for size in range(1, len(rel) + 1):
        for combo in itertools.combinations(rel, size):
            v = G.check_r(iid, kwargs, tr, {d: "B" for d in combo})
            if v == grader_verdict:
                return "decision:" + "+".join(combo)
    # Reading B of D-english and D-language ("no foreign word at all") is stricter than A, so it
    # can only explain a grader fail that A passes, never a grader pass that A fails.
    if any(d in UNSWITCHED for d in RELEVANT[iid]) and not grader_verdict:
        return "decision-unswitched:" + "+".join(d for d in RELEVANT[iid] if d in UNSWITCHED)
    return "finding"


def label_bool(label: str) -> bool:
    return label == "pass"
