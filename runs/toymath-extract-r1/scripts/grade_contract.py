"""Replacement ToyMath grader: an implementation of audit/CONTRACT.md, with one switch per decision entry.

Usage (from the run root):
    python -I audit/scripts/grade_contract.py [--problems P] [--responses R] [--out V] [switches]

Switches, default = the proposed reading (a) of each decision entry:
    --multiple-numbers   first | last                 D-multiple-numbers
    --comma-grouping     any | thousands              D-comma-grouping
    --digits             ascii | unicode              D-digits
    --leading-whitespace unicode | ascii              D-leading-whitespace
    --tolerance-boundary inclusive | exclusive        D-tolerance-boundary
    --answer-line-form   search | strict              D-answer-line-form

It prints one row per model: label counts, missing problems, and the score, 100 x correct / 12 (S4). With
--out it writes one JSON line per response: id, model, problem_id, extracted (the number as a string, commas
removed, or null) and verdict (correct, incorrect or no_answer). A file with two responses from one model to
one problem, or a problem_id that is not in the problems file, is rejected with exit code 2 (S4.3).
Comparison is exact: Decimal comparisons against r - 0.01 and r + 0.01, which do not round (S3.3).
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from decimal import Decimal, localcontext

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREFIX = "Answer:"
TOLERANCE = Decimal("0.01")
ASCII_WS = " \t"

DECISIONS = OrderedDict([
    ("multiple_numbers", ("first", "last")),
    ("comma_grouping", ("any", "thousands")),
    ("digits", ("ascii", "unicode")),
    ("leading_whitespace", ("unicode", "ascii")),
    ("tolerance_boundary", ("inclusive", "exclusive")),
    ("answer_line_form", ("search", "strict")),
])
ENTRY = {
    "multiple_numbers": "D-multiple-numbers",
    "comma_grouping": "D-comma-grouping",
    "digits": "D-digits",
    "leading_whitespace": "D-leading-whitespace",
    "tolerance_boundary": "D-tolerance-boundary",
    "answer_line_form": "D-answer-line-form",
}
PROPOSED = {k: v[0] for k, v in DECISIONS.items()}


def switches_for(entry_b=None):
    """The proposed switches, with the named decision entries (a list of D- names) set to reading (b)."""
    sw = dict(PROPOSED)
    for name in entry_b or ():
        key = [k for k, v in ENTRY.items() if v == name][0]
        sw[key] = DECISIONS[key][1]
    return sw


_PATTERNS = {}


def _patterns(digits, comma_grouping):
    key = (digits, comma_grouping)
    if key not in _PATTERNS:
        d = "[0-9]" if digits == "ascii" else r"\d"
        if comma_grouping == "any":
            # S2.2: a comma between two digits is part of the number.
            search = "-?%s+(?:,%s+)*(?:\\.%s+(?:,%s+)*)?" % (d, d, d, d)
            strict = "-?%s+(?:\\.%s+)?" % (d, d)  # matched after all commas are removed
        else:
            # D-comma-grouping (b): only a first group of 1 to 3 digits followed by groups of exactly 3.
            grouped = "%s{1,3}(?:,%s{3})+(?!%s)" % (d, d, d)
            search = "-?(?:%s|%s+)(?:\\.%s+)?" % (grouped, d, d)
            strict = "-?(?:%s{1,3}(?:,%s{3})+|%s+)(?:\\.%s+)?" % (d, d, d, d)
        _PATTERNS[key] = (re.compile(search), re.compile(strict))
    return _PATTERNS[key]


def answer_line_rest(text, leading_whitespace):
    """S1: the text after the prefix on the last answer line, or None if there is no answer line."""
    rest = None
    for line in text.splitlines():
        body = line.lstrip() if leading_whitespace == "unicode" else line.lstrip(ASCII_WS)
        if body.startswith(PREFIX):
            rest = body[len(PREFIX):]
    return rest


def extract(text, sw=PROPOSED):
    """S1 and S2: the answer as a digit string without commas, or None for no answer line or no number."""
    if not isinstance(text, str):
        return None
    rest = answer_line_rest(text, sw["leading_whitespace"])
    if rest is None:
        return None
    search, strict = _patterns(sw["digits"], sw["comma_grouping"])
    if sw["answer_line_form"] == "strict":
        s = rest.strip()
        if sw["comma_grouping"] == "any":
            s = s.replace(",", "")
        return s.replace(",", "") if strict.fullmatch(s) else None
    if sw["multiple_numbers"] == "first":
        m = search.search(rest)
    else:
        m = None
        for m in search.finditer(rest):
            pass
    return None if m is None else m.group(0).replace(",", "")


def within(answer, reference, boundary):
    """S3: exact comparison. Decimal comparisons never round; r +- 0.01 is computed with enough precision."""
    x = Decimal(answer)
    r = Decimal(reference)
    with localcontext() as ctx:
        ctx.prec = max(28, len(reference) + 10)
        lo, hi = r - TOLERANCE, r + TOLERANCE
    if boundary == "inclusive":
        return lo <= x <= hi
    return lo < x < hi


def grade_response(text, reference, sw=PROPOSED):
    """Return (extracted, verdict) for one response and the reference answer string."""
    extracted = extract(text, sw)
    if extracted is None:
        return None, "no_answer"
    return extracted, ("correct" if within(extracted, reference, sw["tolerance_boundary"]) else "incorrect")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def grade(problems, responses, sw=PROPOSED):
    refs = OrderedDict((p["problem_id"], p["answer"]) for p in problems)
    seen = set()
    errors = []
    for r in responses:
        key = (r["model"], r["problem_id"])
        if r["problem_id"] not in refs:
            errors.append("unknown problem_id %r in response %r" % (r["problem_id"], r["id"]))
        elif key in seen:
            errors.append("second response from model %r to problem %r (response %r)" % (key + (r["id"],)))
        seen.add(key)
    if errors:
        raise ValueError("; ".join(errors))
    rows = []
    for r in responses:
        extracted, verdict = grade_response(r["response"], refs[r["problem_id"]], sw)
        rows.append({"id": r["id"], "model": r["model"], "problem_id": r["problem_id"],
                     "extracted": extracted, "verdict": verdict})
    return rows


def summarize(rows, n_problems):
    table = OrderedDict()
    for model in sorted({row["model"] for row in rows}):
        mine = [row for row in rows if row["model"] == model]
        c = {k: sum(1 for row in mine if row["verdict"] == k) for k in ("correct", "incorrect", "no_answer")}
        c["missing"] = n_problems - len(mine)
        c["score"] = 100.0 * c["correct"] / n_problems
        table[model] = c
    return table


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--problems", default=os.path.join(ROOT, "case", "problems.jsonl"))
    ap.add_argument("--responses", default=os.path.join(ROOT, "case", "responses.jsonl"))
    ap.add_argument("--out")
    for key, choices in DECISIONS.items():
        ap.add_argument("--" + key.replace("_", "-"), choices=choices, default=choices[0])
    args = ap.parse_args(argv)
    sw = {key: getattr(args, key) for key in DECISIONS}
    problems = load_jsonl(args.problems)
    try:
        rows = grade(problems, load_jsonl(args.responses), sw)
    except ValueError as e:
        print("rejected: %s" % e, file=sys.stderr)
        return 2
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
    print("%-12s%9s%11s%11s%9s%8s" % ("model", "correct", "incorrect", "no_answer", "missing", "score"))
    for model, c in summarize(rows, len(problems)).items():
        print("%-12s%9d%11d%11d%9d%8.1f" % (model, c["correct"], c["incorrect"], c["no_answer"], c["missing"],
                                             c["score"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
