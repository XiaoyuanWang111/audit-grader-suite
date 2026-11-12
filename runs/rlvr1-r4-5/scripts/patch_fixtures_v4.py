p = "<W>/audit/tests/fixture_defs.py"
s = open(p, encoding="utf-8").read()
anchor = "# Graded-text extraction:"
new = '''# contract v4 additions (prompted by development panel responses; see ISSUE.md)
FIXTURES += [
    ("detectable_format:sentence_hyphens", None, "Calm minds begin \u2013 our therapists offer care \u2013 empathy drives every session", "fail", [], "spaced en dashes"),
    ("detectable_format:sentence_hyphens", None, "I like cats.\u2014They are cute.", "fail", ["D-hyphen-dash"], "em dash"),
    ("combination:two_responses", None, "A first.\n******\nB second.\n******", "fail", ["D-two-sep-edge"], "trailing separator"),
    ("keywords:no_adjacent_consecutive", None, "\u043f\u043e\u0442\u043e\u043c \u0440\u0430\u0437", "fail", ["D-consecutive-script"], "Cyrillic p r"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main text here - P.P.S This is extra", "fail", ["D-postscript-line"], "marker mid-line"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "[Main] [text]\n[P.P.S] [extra]", "pass", [], "bracketed marker"),
    ("detectable_format:multiple_sections", {"num_sections": 1, "section_spliter": "SECTION"}, '"SECTION 1\nall text here"', "pass", [], "quoted response"),
]

'''
assert s.count(anchor) == 1
s = s.replace(anchor, new + anchor)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
