"""Write audit/tests/known_failures.json: every (grader, fixture) whose verdict differs from the label,
with the finding or decision entries that explain it. Run after scripts/run_fixtures.py.

A fixture with decision tags is explained by those decisions (its label holds under the proposed
reading). A fixture without decision tags is explained by the finding for that grader and check.
"""
import json
import os

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = json.load(open(os.path.join(AUDIT, "work", "fixture_verdicts.json"), encoding="utf-8"))
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language",
            "letters:letter_counting"}

FINDING = {
    ("A", "keywords:word_once"): "F-A1",
    ("A", "keywords:word_count_different_numbers"): "F-A2",
    ("A", "first_word:first_word_answer"): "F-A3",
    ("A", "first_word:first_word_sent"): "F-A3",
    ("A", "length_constraints:nth_paragraph_first_word"): "F-A3",
    ("A", "keywords:keyword_specific_position"): "F-A4",
    ("A", "count:count_unique"): "F-A5",
    ("A", "count:counting_composition"): "F-A6",
    ("A", "detectable_content:number_placeholders"): "F-A7",
    ("A", "detectable_content:postscript"): "F-A8",
    ("A", "detectable_format:bigram_wrapping"): "F-A9",
    ("A", "detectable_format:constrained_response"): "F-A10",
    ("A", "detectable_format:multiple_sections"): "F-A11",
    ("A", "detectable_format:number_bullet_lists"): "F-A12",
    ("A", "detectable_format:number_highlighted_sections"): "F-A13",
    ("A", "detectable_format:sentence_hyphens"): "F-A14",
    ("A", "detectable_format:square_brackets"): "F-A15",
    ("A", "keywords:no_adjacent_consecutive"): "F-A16",
    ("A", "keywords:palindrome"): "F-A17",
    ("A", "keywords:start_end"): "F-A18",
    ("A", "language:response_language"): "F-A19",
    ("A", "length_constraints:number_paragraphs"): "F-A20",
    ("A", "paragraphs:paragraphs"): "F-A20",
    ("A", "length_constraints:number_words"): "F-A21",
    ("A", "combination:two_responses"): "F-A22",
    ("A", "copy:repeat_phrase"): "F-A23",
    ("A", "change_case:english_capital"): "F-A24",
    ("A", "count:lowercase_counting"): "F-A25",
    ("A", "letters:letter_counting"): "F-A26",
    ("B", "keywords:palindrome"): "F-B22",
    ("B", "keywords:no_adjacent_consecutive"): "F-B1",
    ("B", "count:lowercase_counting"): "F-B2",
    ("B", "copy:repeat_phrase"): "F-B3",
    ("B", "detectable_format:square_brackets"): "F-B4",
    ("B", "detectable_format:sentence_hyphens"): "F-B5",
    ("B", "length_constraints:number_paragraphs"): "F-B6",
    ("B", "paragraphs:paragraphs"): "F-B7",
    ("B", "paragraphs:paragraphs2"): "F-B7",
    ("B", "length_constraints:number_words"): "F-B8",
    ("B", "keywords:start_end"): "F-B9",
    ("B", "startend:quotation"): "F-B10",
    ("B", "detectable_content:postscript"): "F-B11",
    ("B", "detectable_format:constrained_response"): "F-B12",
    ("B", "detectable_format:json_format"): "F-B13",
    ("B", "detectable_format:multiple_sections"): "F-B14",
    ("B", "detectable_format:number_bullet_lists"): "F-B15",
    ("B", "detectable_format:number_highlighted_sections"): "F-B16",
    ("B", "detectable_format:title"): "F-B17",
    ("B", "keywords:word_once"): "F-B18",
    ("B", "keywords:word_count_different_numbers"): "F-B19",
    ("B", "count:counting_composition"): "F-B20",
    ("B", "combination:two_responses"): "F-B21",
}

known = {}
missing = []
for v in V:
    for g in ("A", "B"):
        if g == "B" and v["instruction_id"] in SEMANTIC:
            continue
        if v[g] == v["label"]:
            continue
        if v["decisions"]:
            reason = " + ".join(v["decisions"])
        else:
            reason = FINDING.get((g, v["instruction_id"]))
            if reason is None:
                missing.append((g, v["id"]))
                continue
        known[f"{g}|{v['id']}"] = reason
assert not missing, missing
with open(os.path.join(AUDIT, "tests", "known_failures.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(dict(sorted(known.items())), f, indent=1)
print(len(known), "known failures written")
