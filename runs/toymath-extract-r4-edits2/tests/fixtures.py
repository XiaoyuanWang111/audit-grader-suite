"""Labelled fixtures for the ToyMath final-answer check.

Every label comes from audit/CONTRACT.md alone, under the proposed reading (A)
of each decision entry. `alt` maps a replacement-grader switch (or several,
joined by '&') to the label under that other reading. `kind` is control,
finding or decision; `tags` names the finding or decision entries involved.

A fixture's id is `final-answer:` plus the first 16 hex digits of the sha256
of json.dumps([problem_id, response]).
"""
import hashlib
import json
import pathlib

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"

PROBLEMS = {}
for _line in (CASE / "problems.jsonl").read_text(encoding="utf-8").splitlines():
    if _line.strip():
        _p = json.loads(_line)
        PROBLEMS[_p["problem_id"]] = _p
TEMPLATE = (CASE / "prompt_template.txt").read_text(encoding="utf-8")


def rendered_prompt(pid):
    return TEMPLATE.replace("{problem}", PROBLEMS[pid]["problem"])


def fid(pid, response):
    blob = json.dumps([pid, response], ensure_ascii=False)
    return "final-answer:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def F(name, pid, response, label, kind="control", tags=(), alt=None):
    return {"name": name, "id": fid(pid, response), "problem_id": pid, "response": response,
            "label": label, "kind": kind, "tags": list(tags), "alt": dict(alt or {})}


NONUM = {"no_number_label=incorrect": "incorrect"}
STRICT_NONE = {"surrounding=strict": "no_answer"}
EXCL = {"boundary=exclusive": "incorrect"}

FIXTURES = [
    # --- C1 answer line: controls ---
    F("plain-correct", "p02", "18 classes times 27 students is 486.\nAnswer: 486", "correct"),
    F("negative-correct", "p04", "4 - 11 = -7\nAnswer: -7", "correct"),
    F("decimal-trailing-zero", "p01", "6 x 2.75 = 16.50, and 20 - 16.50 = 3.50.\nAnswer: 3.50", "correct"),
    F("plain-incorrect", "p02", "Answer: 500", "incorrect"),
    F("no-answer-line", "p02", "The school has 486 students.", "no_answer"),
    F("lowercase-label", "p02", "answer: 486", "no_answer"),
    F("uppercase-label", "p02", "ANSWER: 486", "no_answer"),
    F("space-before-colon", "p02", "Answer : 486", "no_answer"),
    F("plural-label", "p02", "Answers: 486", "no_answer"),
    F("final-answer-label", "p02", "Final Answer: 486", "no_answer"),
    F("bold-label", "p02", "**Answer:** 486", "no_answer"),
    F("bullet-label", "p02", "- Answer: 486", "no_answer"),
    F("label-mid-line", "p02", "So my Answer: 486", "no_answer"),
    F("last-answer-line-wins", "p02", "Answer: 400\nWait, 18 x 27 is 486.\nAnswer: 486", "correct"),
    F("last-answer-line-wrong", "p02", "Answer: 486\nOn reflection:\nAnswer: 400", "incorrect"),
    F("lines-after-ignored", "p02", "Answer: 486\nThat is 18 times 27, or 500 minus 14.", "correct"),
    F("indent-spaces", "p02", "   Answer: 486", "correct"),
    F("indent-tab", "p02", "\tAnswer: 486", "correct"),
    F("no-space-after-colon", "p02", "Answer:486", "correct"),
    F("no-space-negative", "p04", "Answer:-7", "correct"),
    F("crlf", "p02", "18 x 27\r\nAnswer: 486\r\n", "correct"),
    F("cr-only-split", "p02", "Answer: 400\rAnswer: 486", "correct"),
    F("u2028-split", "p02", "Answer: 400\u2028Answer: 486", "correct"),
    F("nel-split", "p02", "Answer: 400\x85Answer: 486", "correct"),
    F("formfeed-split", "p02", "Answer: 400\x0cAnswer: 486", "correct"),
    F("zero-width-space-prefix", "p02", "\u200bAnswer: 486", "no_answer"),
    F("bom-prefix", "p02", "\ufeffAnswer: 486", "no_answer"),
    F("trailing-newline", "p01", "Answer: 3.5\n", "correct"),
    # --- C1/C3: answer line without a number (D-no-number-label, score-neutral) ---
    F("label-no-number", "p02", "Answer: unknown", "no_answer", "decision", ["D-no-number-label"], NONUM),
    F("number-on-next-line", "p02", "Answer:\n486", "no_answer", "decision", ["D-no-number-label"], NONUM),
    F("template-placeholder", "p02", "Answer: <number>", "no_answer", "decision", ["D-no-number-label"], NONUM),
    # --- C2 number syntax: controls ---
    F("unicode-minus", "p04", "Answer: \u22127", "incorrect"),
    F("spaced-minus", "p04", "Answer: - 7", "incorrect"),
    F("dot-not-thousands", "p03", "Answer: 2.250", "incorrect"),
    F("decimal-comma-is-not-point", "p01", "Answer: 3,5", "incorrect"),
    F("two-decimals", "p09", "Answer: 28.80", "correct"),
    F("zero", "p06", "Answer: 0", "correct"),
    F("negative-zero", "p06", "Answer: -0", "correct"),
    F("zero-off-by-002", "p06", "Answer: 0.02", "incorrect"),
    F("zero-off-by-0011", "p06", "Answer: 0.011", "incorrect"),
    F("leading-zero", "p01", "Answer: 03.5", "correct"),
    F("integer-correct", "p10", "Answer: 13", "correct"),
    F("exponent", "p07", "Answer: 1.5e4", "incorrect", "decision",
      ["D-surrounding-text", "D-multiple-numbers"],
      {"surrounding=strict": "no_answer", "multiple=none": "no_answer"}),
    # --- F1: commas are ignored ---
    F("comma-2250", "p03", "Answer: 2,250", "correct", "finding", ["F1"]),
    F("comma-15000", "p07", "Answer: 15,000", "correct", "finding", ["F1"]),
    F("comma-15000-decimal", "p07", "Answer: 15,000.00", "correct", "finding", ["F1"]),
    F("comma-off-grid", "p02", "Answer: 4,86", "correct", "finding", ["F1"]),
    F("comma-with-reasoning", "p07", "The revenue grows from 12,000 by 3,000.\nAnswer: 15,000", "correct", "finding", ["F1"]),
    # Added after fuzzing (step 4): a comma that is not between two digits is not
    # part of a number, so `4,,86` holds 4 and 86 and never 486.
    F("double-comma", "p02", "Answer: 4,,86", "incorrect", "finding", ["R1"],
      {"multiple=none": "no_answer", "surrounding=strict": "no_answer"}),
    # --- F2: absolute tolerance 0.01 ---
    F("rel-tol-15100", "p07", "Answer: 15100", "incorrect", "finding", ["F2"]),
    F("rel-tol-485", "p02", "Answer: 485", "incorrect", "finding", ["F2"]),
    F("rel-tol-750", "p11", "Answer: 750", "incorrect", "finding", ["F2"]),
    F("rel-tol-3.52", "p01", "Answer: 3.52", "incorrect", "finding", ["F2"]),
    F("rel-tol-2240", "p03", "Answer: 2240", "incorrect", "finding", ["F2"]),
    F("rel-tol-minus-7.05", "p04", "Answer: -7.05", "incorrect", "finding", ["F2"]),
    F("rel-tol-486.02", "p02", "Answer: 486.02", "incorrect", "finding", ["F2"]),
    F("rel-tol-15.1", "p12", "Answer: 15.1", "incorrect", "finding", ["F2"]),
    F("rel-tol-121", "p08", "Answer: 121", "incorrect", "finding", ["F2"]),
    F("rel-tol-72.5", "p05", "Answer: 72.5", "incorrect", "finding", ["F2"]),
    F("rel-tol-13.1", "p10", "Answer: 13.1", "incorrect", "finding", ["F2"]),
    F("rel-tol-29", "p09", "Answer: 29", "incorrect", "finding", ["F2"]),
    # --- D-tolerance-boundary: a difference of exactly 0.01 ---
    F("boundary-zero", "p06", "Answer: 0.01", "correct", "decision", ["D-tolerance-boundary"], EXCL),
    F("boundary-3.51", "p01", "Answer: 3.51", "correct", "decision", ["D-tolerance-boundary"], EXCL),
    F("boundary-3.49", "p01", "Answer: 3.49", "correct", "decision", ["D-tolerance-boundary"], EXCL),
    F("boundary-28.81", "p09", "Answer: 28.81", "correct", "decision", ["D-tolerance-boundary"], EXCL),
    F("boundary-486.01", "p02", "Answer: 486.01", "correct", "decision", ["D-tolerance-boundary"], EXCL),
    # --- F4: exact comparison (decimal precision) ---
    F("precision-zero", "p06", "Answer: 0.010000000000000000000000000001", "incorrect", "finding", ["F4"]),
    F("precision-3.51", "p01", "Answer: 3.510000000000000000000000000001", "incorrect", "finding", ["F4"]),
    # --- D-leading-whitespace ---
    F("ideographic-space-prefix", "p02", "\u3000Answer: 486", "correct", "decision", ["D-leading-whitespace"],
      {"leading_ws=ascii": "no_answer"}),
    F("nbsp-prefix", "p05", "\u00a0Answer: 72", "correct", "decision", ["D-leading-whitespace"],
      {"leading_ws=ascii": "no_answer"}),
    # --- D-digits ---
    F("fullwidth-digits", "p05", "Answer: \uff17\uff12", "no_answer", "decision", ["D-digits"],
      {"digits=unicode": "correct", "no_number_label=incorrect": "incorrect"}),
    F("arabic-indic-digits", "p05", "Answer: \u0667\u0662", "no_answer", "decision", ["D-digits"],
      {"digits=unicode": "correct", "no_number_label=incorrect": "incorrect"}),
    # --- D-surrounding-text ---
    F("currency-sign", "p01", "Answer: $3.50", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    F("unit-after", "p05", "Answer: 72 km/h", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    F("final-period", "p10", "Answer: 13.", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    F("bold-number", "p02", "Answer: **486**", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    F("word-after", "p02", "Answer: 486 students", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    F("curly-quotes-number", "p02", "Answer: \u201c486\u201d", "correct", "decision", ["D-surrounding-text"], STRICT_NONE),
    # --- D-multiple-numbers ---
    F("multi-first-wrong", "p01", "Answer: 6 muffins cost 16.50, so 3.50", "incorrect", "decision",
      ["D-multiple-numbers", "D-surrounding-text"],
      {"multiple=last": "correct", "multiple=none": "no_answer", "surrounding=strict": "no_answer"}),
    F("multi-equation", "p04", "Answer: 4 - 11 = -7", "incorrect", "decision",
      ["D-multiple-numbers", "D-surrounding-text"],
      {"multiple=last": "correct", "multiple=none": "no_answer", "surrounding=strict": "no_answer"}),
    F("multi-first-right", "p07", "Answer: 15000 (up from 12000)", "correct", "decision",
      ["D-multiple-numbers", "D-surrounding-text"],
      {"multiple=last": "incorrect", "multiple=none": "no_answer", "surrounding=strict": "no_answer"}),
    # --- C5 content-free ---
    F("empty", "p02", "", "no_answer"),
    F("whitespace-only", "p02", "   \n\t\n", "no_answer"),
    F("prompt-restated", "p02", rendered_prompt("p02"), "no_answer", "decision", ["D-no-number-label"], NONUM),
    F("problem-restated", "p02", PROBLEMS["p02"]["problem"], "no_answer"),
    F("repeated-number", "p02", "486 " * 50, "no_answer"),
]

_ids = [f["id"] for f in FIXTURES]
_names = [f["name"] for f in FIXTURES]
assert len(set(_ids)) == len(_ids), "duplicate fixture content"
assert len(set(_names)) == len(_names), "duplicate fixture name"
BY_NAME = {f["name"]: f for f in FIXTURES}
