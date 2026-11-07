"""ToyMath grading fixtures, labeled from audit/CONTRACT.md alone.

Each fixture is one response to one problem, with the label that the contract gives it under the
proposed reading (a) of every decision entry. A decision fixture also has `alt`: the label under reading (b)
of the named entry. Labels never come from a grader. The fixture id is the family plus the first 16 hex
digits of sha256(problem_id + NUL + response).

Families:
  line     S1, which line is the answer line
  number   S2, which number the answer line gives
  compare  S3, the 0.01 tolerance
  free     content-free responses (empty, repeated, restated instructions, number lists)
  robust   inputs that must not raise
  decision fixtures whose label depends on a decision entry
Score-level fixtures (S4) are in test_score.py, because they need several responses at once.

This file is ASCII-only: every non-ASCII character is written as an escape.
"""
import hashlib
import json
import os

CASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "case")


def _restated_prompt(problem_id):
    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8", newline="") as f:
        template = f.read()
    with open(os.path.join(CASE, "problems.jsonl"), encoding="utf-8") as f:
        rows = {json.loads(l)["problem_id"]: json.loads(l) for l in f if l.strip()}
    return template.replace("{problem}", rows[problem_id]["problem"])


C, I, N = "correct", "incorrect", "no_answer"

# (family, problem_id, response, label, alt, clause, note)
_RAW = [
    # S1: answer line
    ("line", "p02", "18 x 27 = 486.\nAnswer: 486", C, None, "S1.2", "control: reasoning then answer line"),
    ("line", "p02", "Answer: 486", C, None, "S1.2", "control: answer line only"),
    ("line", "p02", "   Answer: 486", C, None, "S1.2", "leading spaces are allowed"),
    ("line", "p02", "\tAnswer: 486", C, None, "S1.2", "leading tab is allowed"),
    ("line", "p02", "answer: 486", N, None, "S1.4", "lower case is not an answer line"),
    ("line", "p02", "ANSWER: 486", N, None, "S1.4", "upper case is not an answer line"),
    ("line", "p02", "**Answer:** 486", N, None, "S1.4", "bold label does not begin with Answer:"),
    ("line", "p02", "Final Answer: 486", N, None, "S1.4", "line begins with Final"),
    ("line", "p02", "Answer : 486", N, None, "S1.4", "space before the colon"),
    ("line", "p02", "Answers: 486", N, None, "S1.4", "Answers: is not Answer:"),
    ("line", "p02", "The answer is 486.", N, None, "S1.5", "no answer line at all"),
    ("line", "p02", "> Answer: 486", N, None, "S1.4", "blockquote marker before the label"),
    ("line", "p02", "- Answer: 486", N, None, "S1.4", "list marker before the label"),
    ("line", "p02", "Answer\uff1a486", N, None, "S1.4", "fullwidth colon"),
    ("line", "p02", "\u200bAnswer: 486", N, None, "S1.4", "zero-width space is not whitespace"),
    ("line", "p02", "\ufeffAnswer: 486", N, None, "S1.4", "byte-order mark is not whitespace"),
    ("line", "p02", "So the total is computed. Answer: 486", N, None, "S1.2", "label in mid-line"),
    ("line", "p02", "Answer:486", C, None, "S1.2", "no space after the colon"),
    ("line", "p02", "Answer:: 486", C, None, "S2.1", "text after the prefix is ': 486'"),
    ("line", "p02", "Answer: 480\nWait, 18 x 27 is 486.\nAnswer: 486", C, None, "S1.3", "last answer line wins"),
    ("line", "p02", "Answer: 486\nWait, recheck.\nAnswer: 480", I, None, "S1.3", "last answer line wins, wrong"),
    ("line", "p02", "Answer: 486\nI hope this helps; 480 was my first guess.", C, None, "S1.3",
     "lines after the answer line are ignored"),
    ("line", "p02", "Answer: 486\n\n\n", C, None, "S1.1", "trailing blank lines"),
    ("line", "p02", "Work.\r\nAnswer: 486\r\n", C, None, "S1.1", "CRLF line ends"),
    ("line", "p02", "Answer: 480\rAnswer: 486", C, None, "S1.1", "CR alone is a line boundary"),
    ("line", "p02", "Answer: 480\u2028Answer: 486", C, None, "S1.1", "U+2028 is a line boundary"),
    ("line", "p02", "Answer: 480\x85Answer: 486", C, None, "S1.1", "U+0085 NEL is a line boundary"),
    ("line", "p02", "Answer: 480\x0bAnswer: 486", C, None, "S1.1", "vertical tab is a line boundary"),
    ("line", "p02", "Answer: 480\x0cAnswer: 486", C, None, "S1.1", "form feed is a line boundary"),
    ("line", "p02", "Answer: 480\x1cAnswer: 486", C, None, "S1.1", "U+001C is a line boundary"),
    ("line", "p02", "Answer: 486\u2029", C, None, "S1.1", "U+2029 ends the line"),
    ("line", "p02", "Answer: 4\r86", I, None, "S1.1", "CR splits the number's line: 4"),
    ("line", "p02", "Answer:\n486", N, None, "S2.4", "number on the next line does not count"),
    ("line", "p02", "Answer: 486\nAnswer:", N, None, "S2.4", "last answer line has no number"),
    ("line", "p02", "Answer: 486\nAnswer: see above", N, None, "S2.4", "last answer line has no number"),
    ("line", "p02", "Answer: 486\n```", C, None, "S1.3", "code fence after the answer line"),
    # S2: number
    ("number", "p04", "Answer: -7", C, None, "S2.2", "control: negative"),
    ("number", "p04", "Answer: \u22127", I, None, "S2.5", "U+2212 minus sign is not hyphen-minus: 7"),
    ("number", "p04", "Answer: \u20137", I, None, "S2.5", "en dash is not hyphen-minus: 7"),
    ("number", "p04", "Answer: - 7", I, None, "S2.5", "space after the hyphen: 7"),
    ("number", "p04", "Answer: -7\xb0C", C, None, "S2.5", "degree sign after the number"),
    ("number", "p04", "Answer: -7 degrees Celsius", C, None, "S2.5", "unit words after the number"),
    ("number", "p04", "Answer: 7", I, None, "S3.2", "sign dropped"),
    ("number", "p05", "Answer: +72", C, None, "S2.5", "plus sign is not part of the number"),
    ("number", "p05", "Answer: 72.", C, None, "S2.5", "sentence period after the number"),
    ("number", "p05", "Answer: 72 km/h", C, None, "S2.5", "unit after the number"),
    ("number", "p05", "Answer: 72.0", C, None, "S2.2", "decimal zero"),
    ("number", "p05", "Answer: 072", C, None, "S2.2", "leading zero"),
    ("number", "p07", "Answer: 15,000", C, None, "S2.2", "thousands separator"),
    ("number", "p07", "Answer: 15000", C, None, "S2.2", "control: plain digits"),
    ("number", "p07", "Answer: $15,000", C, None, "S2.5", "currency symbol before the number"),
    ("number", "p07", "Answer: 15,000 dollars", C, None, "S2.5", "unit word after the number"),
    ("number", "p07", "Answer: 15,000.00", C, None, "S2.2", "separator and decimal part"),
    ("number", "p07", "Answer: 1.5e4", I, None, "S2.5", "no exponent in the grammar: 1.5"),
    ("number", "p07", "Answer: 1.5E4", I, None, "S2.5", "no exponent in the grammar: 1.5"),
    ("number", "p07", "Answer: 15e3", I, None, "S2.5", "no exponent in the grammar: 15"),
    ("number", "p07", "Answer: 15k", I, None, "S2.5", "suffix k: 15"),
    ("number", "p07", "Answer: 15.000", I, None, "S2.5", "point is a decimal point: 15"),
    ("number", "p07", "Answer: 15 000", I, None, "S2.5", "space is not a separator: 15"),
    ("number", "p01", "Answer: 3,5", I, None, "S2.5", "comma is not a decimal point: 35 (or 3 under D-comma-grouping b)"),
    ("number", "p01", "Answer: 3.50", C, None, "S2.2", "trailing zero"),
    ("number", "p01", "Answer: $3.50", C, None, "S2.5", "currency symbol"),
    ("number", "p01", "Answer: 3.5 dollars", C, None, "S2.5", "unit word"),
    ("number", "p01", "Answer: 3.5.", C, None, "S2.5", "sentence period after a decimal"),
    ("number", "p01", "Answer: .5", I, None, "S2.5", "no digit before the point: 5"),
    ("number", "p09", "Answer: 28.80", C, None, "S2.2", "trailing zero"),
    ("number", "p09", "Answer: 28,8", I, None, "S2.5", "decimal comma: 288 (or 28 under D-comma-grouping b)"),
    ("number", "p06", "Answer: 0", C, None, "S2.2", "control: zero"),
    ("number", "p06", "Answer: -0", C, None, "S2.2", "negative zero equals zero"),
    ("number", "p06", "Answer: 0.00", C, None, "S2.2", "decimal zero"),
    ("number", "p06", "Answer: zero", N, None, "S2.5", "number word"),
    ("number", "p12", "Answer: fifteen", N, None, "S2.5", "number word"),
    ("number", "p12", "Answer: **15**", C, None, "S2.5", "bold number"),
    ("number", "p12", "Answer: $\\boxed{15}$", C, None, "S2.5", "LaTeX box"),
    ("number", "p12", "Answer: 15 eggs", C, None, "S2.5", "unit word"),
    ("number", "p10", "Answer: 13 days", C, None, "S2.5", "unit word"),
    ("number", "p10", "Answer: 13.0", C, None, "S2.2", "decimal zero"),
    ("number", "p08", "Answer: 120 cm\xb2", C, None, "S2.5", "superscript two is not a digit"),
    ("number", "p11", "Answer: 756", C, None, "S2.2", "control"),
    ("number", "p03", "Answer: 2,250", C, None, "S2.2", "thousands separator"),
    ("number", "p03", "Answer: 2250 liters", C, None, "S2.5", "unit word"),
    ("number", "p02", "Answer: 4860", I, None, "S3.2", "wrong magnitude"),
    ("number", "p02", "Answer: 48.6", I, None, "S3.2", "wrong magnitude"),
    # S3: comparison, unambiguous
    ("compare", "p01", "Answer: 3.505", C, None, "S3.2", "inside the tolerance"),
    ("compare", "p01", "Answer: 3.52", I, None, "S3.2", "outside the tolerance"),
    ("compare", "p01", "Answer: 3.48", I, None, "S3.2", "outside the tolerance"),
    ("compare", "p01", "Answer: 3.51000000000000001", I, None, "S3.3", "outside by 1e-17: exact arithmetic"),
    ("compare", "p01", "Answer: 3.4900000000000001", C, None, "S3.3", "inside by 1e-16: exact arithmetic"),
    ("compare", "p06", "Answer: 0.011", I, None, "S3.2", "outside the tolerance"),
    ("compare", "p06", "Answer: 0.009", C, None, "S3.2", "inside the tolerance"),
    ("compare", "p07", "Answer: 15000.005", C, None, "S3.2", "inside the tolerance"),
    ("compare", "p07", "Answer: 15000.02", I, None, "S3.2", "outside the tolerance"),
    ("compare", "p09", "Answer: 28.805", C, None, "S3.2", "inside the tolerance"),
    # decision entries: label under (a), alt under (b)
    ("decision", "p12", "Answer: 15 (3 x 5)", C, {"D-multiple-numbers": I}, "S2.3", "first 15, last 5"),
    ("decision", "p03", "Answer: 2500 - 700 + 450 = 2250", I, {"D-multiple-numbers": C}, "S2.3", "first 2500, last 2250"),
    ("decision", "p11", "Answer: 7 x 12 x 9 = 756", I, {"D-multiple-numbers": C}, "S2.3", "first 7, last 756"),
    ("decision", "p01", "Answer: 3.5 (change from a $20 bill)", C, {"D-multiple-numbers": I}, "S2.3", "first 3.5, last 20"),
    ("decision", "p02", "Answer: 486 Answer: 480", C, {"D-multiple-numbers": I}, "S2.3", "second label in the same line"),
    ("decision", "p12", "Answer: 1,5", C, {"D-comma-grouping": I}, "S2.2", "15, or 1 if only groups of three count"),
    ("decision", "p03", "Answer: 22,50", C, {"D-comma-grouping": I}, "S2.2", "2250, or 22"),
    ("decision", "p02", "Answer: \uff14\uff18\uff16", N, {"D-digits": C}, "S2.2", "fullwidth digits"),
    ("decision", "p02", "Answer: \u0664\u0668\u0666", N, {"D-digits": C}, "S2.2", "Arabic-Indic digits"),
    ("decision", "p02", "\xa0Answer: 486", C, {"D-leading-whitespace": N}, "S1.2", "no-break space before the label"),
    ("decision", "p02", "\u3000Answer: 486", C, {"D-leading-whitespace": N}, "S1.2", "ideographic space before the label"),
    ("decision", "p01", "Answer: 3.51", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p01", "Answer: 3.49", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p06", "Answer: 0.01", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p04", "Answer: -6.99", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p04", "Answer: -7.01", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p09", "Answer: 28.81", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p09", "Answer: 28.79", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    ("decision", "p07", "Answer: 15000.01", C, {"D-tolerance-boundary": I}, "S3.2", "distance exactly 0.01"),
    # content-free responses
    ("free", "p02", "", N, None, "S1.5", "empty response"),
    ("free", "p02", "   \n\n  \t", N, None, "S1.5", "whitespace only"),
    ("free", "p02", _restated_prompt("p02"), N, None, "S2.4", "restated prompt: its answer line has no number"),
    ("free", "p02", "Answer: <number>", N, None, "S2.4", "restated answer template"),
    ("free", "p02", "the " * 200, N, None, "S1.5", "repeated word"),
    ("free", "p05", "Answer: 3.5 486 2250 -7 72 0 15000 120 28.8 13 756 15", I, None, "S2.3",
     "every reference answer on one line: first 3.5, last 15, neither is 72"),
    ("free", "p05", "Answer: 3.5\nAnswer: 72\nAnswer: 486", I, None, "S1.3", "three answer lines, last is 486"),
    ("free", "p05", "The speed is 72 km/h.\nAnswer: 70", I, None, "S1.3", "right number only in the reasoning"),
    ("free", "p05", "The speed is 72 km/h.", N, None, "S1.5", "right number but no answer line"),
    ("free", "p05", "Answer: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 72", I, None, "S2.3",
     "number list: first 0, last 72 (correct only under D-multiple-numbers b)"),
    # robustness: must not raise
    ("robust", "p02", "Answer: " + "9" * 5000, I, None, "S4.4", "5,000-digit number"),
    ("robust", "p02", "Answer: 0." + "0" * 5000 + "1", I, None, "S4.4", "5,000 zeros after the point"),
    ("robust", "p02", "Answer: 486" + "\n" * 20000, C, None, "S4.4", "20,000 trailing newlines"),
    ("robust", "p02", "x" * 200000 + "\nAnswer: 486", C, None, "S4.4", "200,000-character line"),
    ("robust", "p02", "Answer: 486\x00", C, None, "S4.4", "NUL after the number"),
]

# The number-list fixture's label under D-multiple-numbers (b) is correct, so it is a decision fixture too.
_ALT_OVERRIDES = {
    "Answer: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 72": {"D-multiple-numbers": C},
}

# Added after reading the code (contract change 1, 2026-11-06T22:40Z): the label under D-answer-line-form (b),
# for every fixture above whose label changes under that reading. Under (b) the text after "Answer:",
# stripped and without commas, must be exactly one number, so each of these has no number.
_ALF_B = {
    ("p02", "Answer:: 486"): N,
    ("p04", "Answer: " + chr(0x2212) + "7"): N,
    ("p04", "Answer: " + chr(0x2013) + "7"): N,
    ("p04", "Answer: - 7"): N,
    ("p04", "Answer: -7" + chr(0xB0) + "C"): N,
    ("p04", "Answer: -7 degrees Celsius"): N,
    ("p05", "Answer: +72"): N,
    ("p05", "Answer: 72."): N,
    ("p05", "Answer: 72 km/h"): N,
    ("p07", "Answer: $15,000"): N,
    ("p07", "Answer: 15,000 dollars"): N,
    ("p07", "Answer: 1.5e4"): N,
    ("p07", "Answer: 1.5E4"): N,
    ("p07", "Answer: 15e3"): N,
    ("p07", "Answer: 15k"): N,
    ("p07", "Answer: 15 000"): N,
    ("p01", "Answer: $3.50"): N,
    ("p01", "Answer: 3.5 dollars"): N,
    ("p01", "Answer: 3.5."): N,
    ("p01", "Answer: .5"): N,
    ("p12", "Answer: **15**"): N,
    ("p12", "Answer: $\\boxed{15}$"): N,
    ("p12", "Answer: 15 eggs"): N,
    ("p10", "Answer: 13 days"): N,
    ("p08", "Answer: 120 cm" + chr(0xB2)): N,
    ("p03", "Answer: 2250 liters"): N,
    ("p12", "Answer: 15 (3 x 5)"): N,
    ("p03", "Answer: 2500 - 700 + 450 = 2250"): N,
    ("p11", "Answer: 7 x 12 x 9 = 756"): N,
    ("p01", "Answer: 3.5 (change from a $20 bill)"): N,
    ("p02", "Answer: 486 Answer: 480"): N,
    ("p05", "Answer: 3.5 486 2250 -7 72 0 15000 120 28.8 13 756 15"): N,
    ("p05", "Answer: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 72"): N,
    ("p02", "Answer: 486\x00"): N,
}

# Added after reading the code: near misses aimed at what the code does. Labels still come from the contract.
_RAW_AFTER_CODE = [
    # a 1% band around the reference would pass each of these; |x - r| > 0.01 in all of them
    ("compare", "p02", "Answer: 482", I, None, "S3.2", "arithmetic slip of 4"),
    ("compare", "p03", "Answer: 2240", I, None, "S3.2", "slip of 10"),
    ("compare", "p11", "Answer: 754", I, None, "S3.2", "slip of 2"),
    ("compare", "p09", "Answer: 29", I, None, "S3.2", "rounded to whole dollars"),
    ("compare", "p07", "Answer: 14900", I, None, "S3.2", "off by 100"),
    ("compare", "p08", "Answer: 121", I, None, "S3.2", "off by 1"),
    ("compare", "p04", "Answer: -7.05", I, None, "S3.2", "off by 0.05"),
    ("compare", "p05", "Answer: 72.5", I, None, "S3.2", "off by 0.5"),
    ("compare", "p10", "Answer: 13.1", I, None, "S3.2", "off by 0.1"),
    ("compare", "p12", "Answer: 15.1", I, None, "S3.2", "off by 0.1"),
    ("compare", "p01", "Answer: 3.53", I, None, "S3.2", "off by 0.03"),
    # exact arithmetic: the distance has 29 significant digits and exceeds 0.01 by 1e-30
    ("compare", "p06", "Answer: 0.010000000000000000000000000001", I, None, "S3.3", "exceeds 0.01 by 1e-30"),
    ("compare", "p01", "Answer: 3.489999999999999999999999999999", I, None, "S3.3", "exceeds 0.01 by 1e-30"),
    ("compare", "p06", "Answer: 0.0100000000000000000000000001", I, None, "S3.3", "control: exceeds by 1e-28"),
    # commas
    ("number", "p12", "Answer: 15,000", I, None, "S2.2", "15000, not 15"),
    ("number", "p03", "Answer: 2,250.", C, {"D-answer-line-form": N}, "S2.5", "separator and sentence period"),
    # D-answer-line-form, in the panel's own style
    ("decision", "p02", "Answer: 486 students", C, {"D-answer-line-form": N}, "S2.5", "unit word after the number"),
    ("decision", "p09", "Answer: 28.80 dollars", C, {"D-answer-line-form": N}, "S2.5", "unit word after the number"),
    # D-digits with a digit that Python 3.8 does not know (Kawi, Unicode 15.0): 486
    ("decision", "p02", "Answer: " + chr(0x11F54) + chr(0x11F58) + chr(0x11F56), N, {"D-digits": C}, "S2.2",
     "Kawi digits; (b) gives correct on Python 3.12 only"),
]

# Run one at a time: in both graders this response raises decimal.Overflow, which stops the whole run.
ISOLATED = [
    ("robust", "p02", "Answer: " + "9" * 1000000, I, None, "S4.4", "1,000,000-digit number"),
]


def fixture_id(family, problem_id, response):
    h = hashlib.sha256((problem_id + "\x00" + response).encode("utf-8", "surrogatepass")).hexdigest()
    return "%s:%s" % (family, h[:16])


def load(raw):
    out = []
    seen = set()
    for family, pid, resp, label, alt, clause, note in raw:
        alt = dict(alt or {})
        alt.update(_ALT_OVERRIDES.get(resp, {}))
        if (pid, resp) in _ALF_B:
            alt["D-answer-line-form"] = _ALF_B[(pid, resp)]
        fid = fixture_id(family, pid, resp)
        assert fid not in seen, fid
        seen.add(fid)
        out.append({"id": fid, "family": family, "problem_id": pid, "response": resp, "label": label,
                    "alt": alt, "clause": clause, "note": note})
    return out


FIXTURES = load(_RAW + _RAW_AFTER_CODE)
ISOLATED_FIXTURES = load(ISOLATED)
assert len([f for f in FIXTURES if "D-answer-line-form" in f["alt"]]) == len(_ALF_B) + 3, "an _ALF_B key matched no fixture"

if __name__ == "__main__":
    import collections
    print(len(FIXTURES), "fixtures", dict(collections.Counter(f["family"] for f in FIXTURES)),
          "| decision-dependent:", sum(1 for f in FIXTURES if f["alt"]), "| isolated:", len(ISOLATED_FIXTURES))
