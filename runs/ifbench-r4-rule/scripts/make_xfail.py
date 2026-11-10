"""Write audit/tests/xfail.json: fixtures whose current grader verdict differs from the label.

The reason is the decision entry when the fixture names one, else the finding id for its check
(typographic-punctuation fixtures go to F36). Run after audit/scripts/run_fixtures.py.
"""
import csv
import json

W = "<W>"
FINDING_BY_CHECK = {
    "repeat:repeat_span": "F01",  # TypeError on float kwargs; F02 (character indices) shows with int kwargs
    "words:keywords_specific_position": "F01",
    "count:keywords_multiple": "F03",
    "ratio:sentence_words": "F04",
    "words:words_position": "F05",
    "custom:sentence_alphabet": "F06",
    "format:title_case": "F07",
    "format:sub-bullets": "F08",
    "format:list": "F09",
    "format:output_template": "F10",
    "format:thesis": "F11",
    "count:punctuation": "F12",
    "count:conjunctions": "F13",
    "count:pronouns": "F14",
    "count:numbers": "F15",
    "count:unique_word_count": "F16",
    "count:words_japanese": "F17",
    "custom:character_reverse": "F18",
    "custom:word_reverse": "F18",
    "custom:european_capitals_sort": "F19",
    "custom:reverse_newline": "F20",
    "custom:csv_special_character": "F21",
    "custom:csv_quotes": "F22",
    "custom:date_format_list": "F23",
    "custom:mcq_count_length": "F24",
    "format:emoji": "F25",
    "format:line_indent": "F26",
    "format:newline": "F27",
    "format:no_bullets_bullets": "F28",
    "format:options": "F29",
    "format:parentheses": "F30",
    "format:quote_unquote": "F31",
    "format:quotes": "F32",
    "ratio:sentence_balance": "F33",
    "ratio:sentence_type": "F33",
    "repeat:repeat_change": "F34",
    "sentence:alliteration_increment": "F35",
    "words:paragraph_last_first": "F37",
    "words:odd_even_syllables": "F38",
}
TYPO_NOTES = ("em dash", "curly", "don't has 4 letters")

out = {}
with open(f"{W}/audit/out/fixture_results.tsv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["grader"] == r["label"]:
            continue
        if r["decision"]:
            reason = r["decision"]
        elif any(t in r["note"] for t in TYPO_NOTES) and r["check"] not in ("count:unique_word_count",):
            reason = "F36"
        else:
            reason = FINDING_BY_CHECK[r["check"]]
        out[r["id"]] = {"reason": reason, "grader": r["grader"], "label": r["label"]}
json.dump(out, open(f"{W}/audit/tests/xfail.json", "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
from collections import Counter
print(len(out), "xfail fixtures;", Counter(v["reason"] for v in out.values()))
