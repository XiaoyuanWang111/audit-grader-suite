"""Write audit/tests/xfail_grader.json: fixtures the current grader (strict) gets wrong, with the
finding or decision ids that explain each. Input: audit/work/fixture_results.tsv."""
import csv
import json

W = "<W>/audit"
# finding id per check for fixtures whose label depends on no decision (see AUDIT.md)
FINDING_BY_CHECK = {
    "repeat:repeat_span": "F01", "ratio:sentence_words": "F02", "count:keywords_multiple": "F03",
    "count:conjunctions": "F04", "ratio:sentence_type": "F05", "ratio:sentence_balance": "F05",
    "sentence:alliteration_increment": "F06", "format:newline": "F07", "format:line_indent": "F08",
    "format:quote_unquote": "F09", "format:list": "F10", "format:thesis": "F11", "format:sub-bullets": "F12",
    "format:no_bullets_bullets": "F13", "custom:character_reverse": "F14", "custom:reverse_newline": "F15",
    "custom:european_capitals_sort": "F16", "custom:csv_special_character": "F17", "custom:csv_quotes": "F18",
    "custom:date_format_list": "F19", "format:title_case": "F20", "format:output_template": "F21",
    "repeat:repeat_change": "F22", "format:options": "F23", "format:parentheses": "F24",
    "words:prime_lengths": "F25", "words:last_first": "F26", "words:paragraph_last_first": "F26",
    "format:emoji": "F27", "words:start_verb": "F28", "custom:sentence_alphabet": "F29", "words:words_position": "F30",
}
rows = list(csv.DictReader(open(W + "/work/fixture_results.tsv", encoding="utf-8"), delimiter="\t"))
out = {}
for r in rows:
    if r["grader_strict"] != r["label"]:
        check = r["id"].rsplit(":", 1)[0]
        out[r["id"]] = ("decision " + r["decisions"]) if r["decisions"] else ("finding " + FINDING_BY_CHECK[check])
OVERRIDE = {"custom:european_capitals_sort:c87b724749": "finding F16 (the label also depends on D-europe-set; the grader takes the same reading)"}
out.update({k: v for k, v in OVERRIDE.items() if k in out})
json.dump(out, open(W + "/tests/xfail_grader.json", "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
print(len(out), "xfail entries;",
      sum(v.startswith("finding") for v in out.values()), "findings,",
      sum(v.startswith("decision") for v in out.values()), "decisions")
