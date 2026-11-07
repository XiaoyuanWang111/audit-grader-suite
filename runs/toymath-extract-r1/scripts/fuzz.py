"""Fuzz grade.py, the reference and the replacement, count exceptions, and explain every disagreement.

Usage: python -I audit/scripts/fuzz.py [N]     (default N = 20000; writes audit/out/fuzz_summary.json)

Inputs come from a seeded random grammar (SEED below) of answer-label variants, numbers (signs, commas, points,
exponents, Unicode digits, values near the reference), unit words and markup, and every str.splitlines line
boundary. Counts depend on this distribution, so they are reported as counts, not rates.

Graders, each called in-process on one response at a time so that every exception is counted:
  grade_py   case/grade.py's grade() on a one-row list
  reference  case/reference/grade_ref.py's final_answer() plus the comparison line from its main()
  rep        the replacement, proposed readings
  rep_g      the replacement with D-digits (b): grade.py's digit reading
  rep_r      the replacement with D-answer-line-form (b) and D-digits (b): the reference's readings
  grade_py with F1 and/or F2 patched, and the reference with F4 patched (exact comparison), to explain each
  disagreement: a patched grader must equal rep_g (grade.py) or rep_r (reference) on every input.
The in-process results are then checked against the two graders' command lines on the same inputs
(without the inputs that raise, which would stop those runs).
"""
import collections
import importlib.util
import json
import os
import random
import re
import sys
from decimal import Decimal

sys.dont_write_bytecode = True  # importing case/grade.py must not write case/__pycache__
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(ROOT, "case")
sys.path.insert(0, os.path.join(ROOT, "audit", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "audit", "tests"))
import grade_contract  # noqa: E402
import graders  # noqa: E402

SEED = 20261106


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G = load("toymath_grade", os.path.join(CASE, "grade.py"))
R = load("toymath_grade_ref", os.path.join(CASE, "reference", "grade_ref.py"))
with open(os.path.join(CASE, "problems.jsonl"), encoding="utf-8") as f:
    PROBLEMS = [json.loads(l) for l in f if l.strip()]
REFS = {p["problem_id"]: p["answer"] for p in PROBLEMS}

LABELS = ["Answer:", "Answer:", "Answer:", " Answer:", "\tAnswer:", "answer:", "**Answer:**", "Answer :",
          "\xa0Answer:", "Answer\uff1a", "Final Answer:", "", "", "> Answer:", "Answers:"]
SEPS = ["\n"] * 12 + ["\r\n", "\r", "\u2028", "\u2029", "\x85", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e"]
WORDS = ["dollars", "km/h", "eggs", "$", "**", "(", ")", "=", "x", "+", "or", "about", "%", "\xb0C", "...",
         "the", "is", ".", ",", ":", "\\boxed{", "}", "e4", "k"]
DIGIT_SETS = ["0123456789"] * 20 + ["\uff10\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19",
                                    "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"]


def number(rng, ref):
    r = Decimal(ref)
    roll = rng.random()
    if roll < 0.35:
        x = r
    elif roll < 0.65:
        x = r + Decimal(rng.choice([-1, 1])) * Decimal(rng.choice(
            ["0.001", "0.005", "0.009", "0.01", "0.0100001", "0.011", "0.02", "0.05", "0.1", "0.5", "1", "3", "10",
             "100", "150", "151"]))
    else:
        x = Decimal(rng.randint(0, 10 ** rng.randint(1, 7))) / Decimal(10 ** rng.choice([0, 0, 0, 1, 2]))
        x = -x if rng.random() < 0.2 else x
    s = format(x, "f")
    if rng.random() < 0.4 and abs(x) >= 1000:
        s = re.sub(r"(?<=\d)(?=(\d{3})+(?!\d)(?:\.|$))", ",", s) if "." not in s else \
            re.sub(r"(?<=\d)(?=(\d{3})+\.)", ",", s)
    if rng.random() < 0.08:
        i = rng.randint(1, max(1, len(s) - 1))
        s = s[:i] + "," + s[i:]
    if rng.random() < 0.05:
        s = s.replace("-", rng.choice(["\u2212", "- ", "+", "\u2013"]))
    if rng.random() < 0.06:
        s = s + rng.choice([".", ".0", "0", "e4", ",", ".."])
    if rng.random() < 0.04:
        ds = rng.choice(DIGIT_SETS[20:])
        s = "".join(ds[int(c)] if c.isdigit() else c for c in s)
    return s


def response(rng, ref):
    lines = []
    for _ in range(rng.randint(1, 6)):
        kind = rng.random()
        if kind < 0.45:
            body = [number(rng, ref)]
            for _ in range(rng.choice([0, 0, 0, 1, 2, 3])):
                tok = number(rng, ref) if rng.random() < 0.4 else rng.choice(WORDS)
                body.insert(rng.randint(0, len(body)), tok)
            line = rng.choice(LABELS) + rng.choice([" ", " ", "", "  "]) + rng.choice([" ", ""]).join(body)
        elif kind < 0.8:
            line = " ".join(rng.choice(WORDS + [number(rng, ref)]) for _ in range(rng.randint(0, 8)))
        else:
            line = rng.choice(LABELS)
        lines.append(line)
    out = ""
    for i, line in enumerate(lines):
        out += line + (rng.choice(SEPS) if i < len(lines) - 1 or rng.random() < 0.3 else "")
    return out


def grade_py(text, pid):
    row = G.grade(PROBLEMS, [{"id": "x", "model": "m", "problem_id": pid, "response": text}])[0]
    return row["verdict"]


def reference(text, pid):
    answer = R.final_answer(text)
    ok = answer is not None and abs(answer - Decimal(REFS[pid])) <= Decimal("0.01")
    return "correct" if ok else ("incorrect" if answer is not None else "no_answer")


COMMA_NUMBER = re.compile(r"-?\d+(?:,\d+)*(?:\.\d+(?:,\d+)*)?")


def grade_py_patched(text, pid, fix_f1, fix_f2):
    """grade.py's line selection, with commas handled (F1) and/or an exact absolute tolerance (F2)."""
    rest = None
    for line in text.splitlines():
        m = G.ANSWER_LINE.match(line)
        if m:
            rest = m.group(1)
    if rest is None:
        return "no_answer"
    m = (COMMA_NUMBER if fix_f1 else G.NUMBER).search(rest)
    if m is None:
        return "no_answer"
    x = m.group(0).replace(",", "")
    if fix_f2:
        return "correct" if grade_contract.within(x, REFS[pid], "inclusive") else "incorrect"
    return "correct" if G.is_correct(Decimal(x), Decimal(REFS[pid])) else "incorrect"


def reference_patched(text, pid):
    """The reference with an exact comparison (F4 fixed)."""
    answer = R.final_answer(text)
    if answer is None:
        return "no_answer"
    return "correct" if grade_contract.within(str(answer), REFS[pid], "inclusive") else "incorrect"


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    rng = random.Random(SEED)
    pids = list(REFS)
    inputs = [(rng.choice(pids), None) for _ in range(n)]
    inputs = [(pid, response(rng, REFS[pid])) for pid, _ in inputs]
    # three huge answers, for the exception count (F5)
    inputs += [("p02", "Answer: " + "9" * 1000000), ("p07", "Answer: 1" + "0" * 1000000),
               ("p06", "Answer: -" + "1" * 1000001)]
    sw_g = grade_contract.switches_for(["D-digits"])
    sw_r = grade_contract.switches_for(["D-answer-line-form", "D-digits"])
    exc = collections.Counter()
    expl_g = collections.Counter()
    expl_r = collections.Counter()
    unexplained = []
    examples = {}
    results = []
    for pid, text in inputs:
        g = safe(grade_py, text, pid)
        r = safe(reference, text, pid)
        rep = grade_contract.grade_response(text, REFS[pid])[1]
        rep_g = grade_contract.grade_response(text, REFS[pid], sw_g)[1]
        rep_r = grade_contract.grade_response(text, REFS[pid], sw_r)[1]
        for name, v in (("grade_py", g), ("reference", r)):
            if v.startswith("EXC:"):
                exc[(name, v)] += 1
        results.append((pid, text, g, r))
        if g != rep:
            if g.startswith("EXC:"):
                cause = "F5 exception"
            elif g == rep_g:
                cause = "D-digits"
            else:
                g1 = grade_py_patched(text, pid, True, False)
                g2 = grade_py_patched(text, pid, False, True)
                g12 = grade_py_patched(text, pid, True, True)
                if g1 == rep_g:
                    cause = "F1"
                elif g2 == rep_g:
                    cause = "F2"
                elif g12 == rep_g:
                    cause = "F1+F2"
                else:
                    cause = "unexplained"
                    unexplained.append(("grade_py", pid, ascii(text)[:200], g, rep, rep_g))
                if cause != "unexplained" and rep_g != rep:
                    cause += "+D-digits"
            expl_g[cause] += 1
            examples.setdefault("grade_py " + cause, (pid, ascii(text)[:160], g, rep))
        if r != rep:
            if r.startswith("EXC:"):
                cause = "F5 exception"
            elif r == rep_r:
                entries = [e for e in ("D-answer-line-form", "D-digits")
                           if grade_contract.grade_response(text, REFS[pid], grade_contract.switches_for([e]))[1] == r]
                cause = "+".join(entries) or "D-answer-line-form+D-digits"
            elif reference_patched(text, pid) == rep_r:
                cause = "F4"
            else:
                cause = "unexplained"
                unexplained.append(("reference", pid, ascii(text)[:200], r, rep, rep_r))
            expl_r[cause] += 1
            examples.setdefault("reference " + cause, (pid, ascii(text)[:160], r, rep))
    # the command lines must agree with the in-process calls (inputs that raise are left out: they stop a run)
    ok_rows = [{"id": "z%05d" % i, "model": "fuzz", "problem_id": pid, "response": text}
               for i, (pid, text, g, r) in enumerate(results) if not g.startswith("EXC:") and not r.startswith("EXC:")]
    by_id = {row["id"]: results[int(row["id"][1:])] for row in ok_rows}
    cli_g, _, rc_g = graders.run_grade_py(ok_rows)
    cli_r, _, rc_r = graders.run_reference(ok_rows)
    cli_mismatch = sum(1 for i, (pid, text, g, r) in by_id.items() if cli_g[i][1] != g or cli_r[i][1] != r)
    summary = {
        "seed": SEED, "inputs": len(inputs), "random_inputs": n, "huge_inputs": 3,
        "exceptions": {"%s %s" % k: v for k, v in exc.items()},
        "grade_py_vs_replacement": dict(expl_g), "reference_vs_replacement": dict(expl_r),
        "unexplained": unexplained[:20], "unexplained_count": len(unexplained),
        "cli_rows": len(ok_rows), "cli_exit": [rc_g, rc_r], "cli_vs_in_process_mismatches": cli_mismatch,
        "examples": examples,
    }
    with open(os.path.join(ROOT, "audit", "out", "fuzz_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "examples"}, indent=1, ensure_ascii=True))
    for k, v in sorted(examples.items()):
        print("example", k, v)


if __name__ == "__main__":
    main()
