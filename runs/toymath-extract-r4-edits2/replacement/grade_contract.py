"""Replacement ToyMath grader, implemented from audit/CONTRACT.md.

One switch per decision entry; the defaults are the proposed readings (A).

    python -B audit/replacement/grade_contract.py [--problems P] [--responses R] [--out V]
        [--leading-ws isspace|ascii]          D-leading-whitespace   (A: isspace)
        [--digits ascii|unicode]              D-digits               (A: ascii)
        [--surrounding allowed|strict]        D-surrounding-text     (A: allowed)
        [--multiple first|last|none]          D-multiple-numbers     (A: first)
        [--boundary inclusive|exclusive]      D-tolerance-boundary   (A: inclusive)
        [--no-number-label no_answer|incorrect]  D-no-number-label   (A: no_answer)

Labels: correct, incorrect, no_answer; grading_error for an exception (counts
as not correct, reported separately). A model's score is 100 * correct / 12
(the number of problems), whatever responses are present.
"""

import argparse
import json
import os
import sys
import unicodedata
from decimal import Decimal, Inexact, localcontext

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")

PREFIX = "Answer:"
TOLERANCE = Decimal("0.01")

DEFAULTS = {
    "leading_ws": "isspace",
    "digits": "ascii",
    "surrounding": "allowed",
    "multiple": "first",
    "boundary": "inclusive",
    "no_number_label": "no_answer",
}

CHOICES = {
    "leading_ws": ("isspace", "ascii"),
    "digits": ("ascii", "unicode"),
    "surrounding": ("allowed", "strict"),
    "multiple": ("first", "last", "none"),
    "boundary": ("inclusive", "exclusive"),
    "no_number_label": ("no_answer", "incorrect"),
}


def _opts(opts):
    o = dict(DEFAULTS)
    if opts:
        for k, v in opts.items():
            if k not in CHOICES or v not in CHOICES[k]:
                raise ValueError(f"bad option {k}={v}")
            o[k] = v
    return o


def _is_ws(ch, o):
    if o["leading_ws"] == "ascii":
        return ch in " \t"
    return ch.isspace()


def _is_digit(ch, o):
    if "0" <= ch <= "9":
        return True
    return o["digits"] == "unicode" and unicodedata.category(ch) == "Nd"


def _ascii_digit(ch):
    return ch if "0" <= ch <= "9" else str(unicodedata.decimal(ch))


def answer_rest(text, opts=None):
    """C1: the text after `Answer:` on the last answer line, or None."""
    o = _opts(opts)
    rest = None
    for line in text.splitlines():
        i = 0
        while i < len(line) and _is_ws(line[i], o):
            i += 1
        if line.startswith(PREFIX, i):
            rest = line[i + len(PREFIX):]
    return rest


def _scan_digits(s, i, o):
    """Digits from s[i], where a comma between two digits joins them.
    Returns (ascii_digits, end_index)."""
    out = []
    n = len(s)
    while i < n:
        if _is_digit(s[i], o):
            out.append(_ascii_digit(s[i]))
            i += 1
        elif s[i] == "," and out and i + 1 < n and _is_digit(s[i + 1], o):
            i += 1
        else:
            break
    return "".join(out), i


def _number_at(s, i, o):
    """C2: a number starting exactly at s[i], or None. Returns (text, end)."""
    n = len(s)
    j = i
    sign = ""
    if j < n and s[j] == "-":
        if j + 1 < n and _is_digit(s[j + 1], o):
            sign = "-"
            j += 1
        else:
            return None
    if not (j < n and _is_digit(s[j], o)):
        return None
    intpart, j = _scan_digits(s, j, o)
    frac = ""
    if j + 1 < n and s[j] == "." and _is_digit(s[j + 1], o):
        frac, j = _scan_digits(s, j + 1, o)
    text = sign + intpart + ("." + frac if frac else "")
    return text, j


def numbers(rest, opts=None):
    """All numbers in the answer-line rest, left to right, as ASCII strings."""
    o = _opts(opts)
    found = []
    i = 0
    n = len(rest)
    while i < n:
        # A number may start at '-' or at a digit that does not continue a
        # previous token (tokens are consumed whole, so this is a plain scan).
        got = _number_at(rest, i, o)
        if got is None:
            i += 1
            continue
        found.append(got[0])
        i = got[1]
    return found


def extract(text, opts=None):
    """Return (status, number_text). status: 'no_line', 'no_number', 'number'."""
    o = _opts(opts)
    rest = answer_rest(text, o)
    if rest is None:
        return "no_line", None
    if o["surrounding"] == "strict":
        # The rest, stripped of whitespace, must be exactly one number.
        lo, hi = 0, len(rest)
        while lo < hi and rest[lo].isspace():
            lo += 1
        while hi > lo and rest[hi - 1].isspace():
            hi -= 1
        core = rest[lo:hi]
        got = _number_at(core, 0, o) if core else None
        if got is None or got[1] != len(core):
            return "no_number", None
        return "number", got[0]
    nums = numbers(rest, o)
    if not nums:
        return "no_number", None
    if o["multiple"] == "first":
        return "number", nums[0]
    if o["multiple"] == "last":
        return "number", nums[-1]
    if len(nums) == 1:
        return "number", nums[0]
    return "no_number", None


def within(answer_text, reference_text, opts=None):
    """C3: exact decimal comparison against the 0.01 tolerance."""
    o = _opts(opts)
    a = Decimal(answer_text)
    r = Decimal(reference_text)
    with localcontext() as ctx:
        ctx.prec = len(answer_text) + len(reference_text) + 10
        ctx.traps[Inexact] = True
        diff = abs(a - r)
    if o["boundary"] == "inclusive":
        return diff <= TOLERANCE
    return diff < TOLERANCE


def verdict(text, reference_text, opts=None):
    """Return (label, number_text)."""
    o = _opts(opts)
    status, num = extract(text, o)
    if status == "no_line":
        return "no_answer", None
    if status == "no_number":
        return o["no_number_label"], None
    return ("correct" if within(num, reference_text, o) else "incorrect"), num


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def grade(problems, responses, opts=None):
    """Grade every response. Returns (rows, notes)."""
    o = _opts(opts)
    refs = {p["problem_id"]: p["answer"] for p in problems}
    rows, notes = [], []
    seen = set()
    for r in responses:
        row = {"id": r.get("id"), "model": r.get("model"), "problem_id": r.get("problem_id"),
               "extracted": None, "verdict": None, "scored": True}
        key = (r.get("model"), r.get("problem_id"))
        if r.get("problem_id") not in refs:
            row["verdict"], row["scored"] = "unknown_problem", False
            notes.append(f"{row['id']}: problem_id {row['problem_id']!r} is not in the problem set; not scored")
        elif key in seen:
            row["verdict"], row["scored"] = "duplicate", False
            notes.append(f"{row['id']}: second response from {key[0]} to {key[1]}; not scored")
        else:
            seen.add(key)
            try:
                text = r["response"]
                if not isinstance(text, str):
                    raise TypeError(f"response is {type(text).__name__}, not str")
                label, num = verdict(text, refs[r["problem_id"]], o)
                row["verdict"], row["extracted"] = label, num
            except Exception as e:  # a grading failure, not a model error
                row["verdict"] = "grading_error"
                notes.append(f"{row['id']}: grading_error {type(e).__name__}: {e}")
        rows.append(row)
    return rows, notes


def summarize(problems, rows):
    n = len(problems)
    table = {}
    for row in rows:
        c = table.setdefault(row["model"], {"correct": 0, "incorrect": 0, "no_answer": 0,
                                            "grading_error": 0, "missing": n})
        if row["scored"]:
            c[row["verdict"]] += 1
            c["missing"] -= 1
    for model, c in table.items():
        c["score"] = round(100.0 * c["correct"] / n, 1) if n else 0.0
    return dict(sorted(table.items()))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Replacement ToyMath grader (audit/CONTRACT.md).")
    ap.add_argument("--problems", default=os.path.join(CASE, "problems.jsonl"))
    ap.add_argument("--responses", default=os.path.join(CASE, "responses.jsonl"))
    ap.add_argument("--out")
    for k, vals in CHOICES.items():
        ap.add_argument("--" + k.replace("_", "-"), choices=vals, default=DEFAULTS[k])
    args = ap.parse_args(argv)
    opts = {k: getattr(args, k) for k in CHOICES}
    problems = load_jsonl(args.problems)
    rows, notes = grade(problems, load_jsonl(args.responses), opts)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    table = summarize(problems, rows)
    print(f"{'model':<12}{'correct':>9}{'incorrect':>11}{'no_answer':>11}{'errors':>8}{'missing':>9}{'score':>8}")
    for model, c in table.items():
        print(f"{str(model):<12}{c['correct']:>9}{c['incorrect']:>11}{c['no_answer']:>11}"
              f"{c['grading_error']:>8}{c['missing']:>9}{c['score']:>8.1f}")
    for note in notes:
        print("note:", note, file=sys.stderr)


if __name__ == "__main__":
    main()
