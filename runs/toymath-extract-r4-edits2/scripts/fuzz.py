"""Fuzz the grader and the reference (step 4).

Generates random responses from a grammar of answer-line variants and grades
them in-process with each grader's own functions (extract_answer and
is_correct from case/grade.py; final_answer from the reference plus the
reference's verdict expression), and with the replacement.

Every verdict is compared, at the score level (correct vs not correct), with
the replacement under every combination of decision readings:
  agree     the verdict equals the proposed-reading label;
  decision  it differs from the proposal but some combination of readings gives it;
  finding   no combination gives it. Attributed to F1 (the grader read a
            different number: comma join), F2 (exact difference above 0.01 but
            within 1% of the reference), F4 (exact difference above 0.01 but the
            grader's 28-digit Decimal subtraction rounds it to 0.01 or less), or,
            for the reference, R-comma (it deletes every comma on the line, so
            it reads a number that no reading reads).
Exceptions are counted per grader.

Run from W:  python -B audit/scripts/fuzz.py [N] [SEED]      (defaults 20000, 1)
Counts depend on the generator's distribution: report them as counts.
"""
import importlib.util
import itertools
import pathlib
import random
import sys
from collections import Counter
from decimal import Decimal, localcontext

sys.dont_write_bytecode = True
W = pathlib.Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


grader = load("toymath_grade", W / "case" / "grade.py")
ref = load("toymath_ref", W / "case" / "reference" / "grade_ref.py")
repl = load("grade_contract", W / "audit" / "replacement" / "grade_contract.py")

PROBLEMS = {r["problem_id"]: r for r in grader.load_jsonl(str(W / "case" / "problems.jsonl"))}
SCORE_KEYS = ["leading_ws", "digits", "surrounding", "multiple", "boundary"]  # no_number_label is score-neutral
COMBOS = [dict(zip(SCORE_KEYS, vals)) for vals in itertools.product(*(repl.CHOICES[k] for k in SCORE_KEYS))]

WS = [" ", "  ", "\t", "\u00a0", "\u3000", "", "", ""]
SEPS = ["\n", "\n", "\n", "\r\n", "\r", "\u2028", "\x85", "\x0c", "\x1e"]
DIG_ALT = {"0": "\uff10", "1": "\uff11", "2": "\u0662", "7": "\u0667", "5": "\uff15"}


def exact_diff(a, b):
    with localcontext() as ctx:
        ctx.prec = 200
        return abs(Decimal(a) - Decimal(b))


def rand_number(rng, refv):
    choice = rng.random()
    if choice < 0.35:
        v = refv
    elif choice < 0.6:
        v = refv + Decimal(rng.choice(["0.01", "-0.01", "0.02", "-0.005", "0.1", "1", "-1", "5", "100", "0.0099"]))
    elif choice < 0.75:
        v = refv * Decimal(rng.choice(["1.001", "0.995", "1.01", "0.99", "10", "0.1"]))
    else:
        v = Decimal(rng.randint(-20000, 20000)) / Decimal(rng.choice([1, 1, 10, 100]))
    s = format(v.normalize() if rng.random() < 0.5 else v, "f")
    if rng.random() < 0.3 and abs(v) >= 1000:
        ip, _, fp = s.lstrip("-").partition(".")
        s = ("-" if s.startswith("-") else "") + f"{int(ip):,}" + ("." + fp if fp else "")
    if rng.random() < 0.05:
        s = s.replace("-", "\u2212")
    if rng.random() < 0.05:
        s = "".join(DIG_ALT.get(c, c) for c in s)
    if rng.random() < 0.05:
        s = s + "0" * rng.randint(20, 40) + "1" if "." in s else s + "." + "0" * rng.randint(26, 40) + "1"
    return s


def rand_answer_line(rng, refv):
    num = rand_number(rng, refv)
    pre = rng.choice(WS)
    label = rng.choice(["Answer:"] * 8 + ["answer:", "Answer :", "**Answer:**", "Final Answer:"])
    mid = rng.choice([" ", "", "  ", " $", " **", " \u201c"])
    post = rng.choice(["", "", "", ".", " units", "**", "\u201d", ",", " (approx)", " or " + num])
    return f"{pre}{label}{mid}{num}{post}"


def rand_response(rng, pid):
    refv = Decimal(PROBLEMS[pid]["answer"])
    lines = []
    for _ in range(rng.randint(0, 4)):
        lines.append(rng.choice(["Work it out.", "So 2 + 2 = 4.", "We get 1,000 then 2,500.", "", "Thus:"]))
    for _ in range(rng.choice([0, 1, 1, 1, 2])):
        lines.append(rand_answer_line(rng, refv))
    if rng.random() < 0.2:
        lines.append(rng.choice(["Hope this helps.", "Check: 3 x 4 = 12.", "Answer: see above"]))
    sep = rng.choice(SEPS)
    return sep.join(lines) + (sep if rng.random() < 0.3 else "")


def binary(lab):
    return "correct" if lab == "correct" else "not_correct"


def grader_verdict(text, pid):
    a = grader.extract_answer(text)
    if a is None:
        return "no_answer", None
    return ("correct" if grader.is_correct(a, Decimal(PROBLEMS[pid]["answer"])) else "incorrect"), a


def ref_verdict(text, pid):
    a = ref.final_answer(text)
    ok = a is not None and abs(a - Decimal(PROBLEMS[pid]["answer"])) <= Decimal("0.01")
    return ("correct" if ok else "incorrect"), a


def own_number(text, opts):
    st, num = repl.extract(text, opts)
    return Decimal(num) if st == "number" else None


def attribute_grader(text, pid, g, a):
    """Mechanism of a grader verdict that differs, on the same answer line,
    from the replacement at the grader's own readings (digits=unicode)."""
    refs = PROBLEMS[pid]["answer"]
    if a is not None and a != own_number(text, {"digits": "unicode"}):
        return "F1"  # read a different number from the same line: no comma join
    if a is not None and g == "correct":
        d = exact_diff(a, refs)
        if d > Decimal("0.01"):
            if d <= Decimal("0.01") * max(Decimal(1), abs(Decimal(refs))):
                return "F2"
            return "F4"
    return "other"


def attribute_ref(text, pid, r, a):
    refs = PROBLEMS[pid]["answer"]
    if a is not None and r == "correct" and exact_diff(a, refs) > Decimal("0.01"):
        return "F4"
    rest = repl.answer_rest(text)
    if a is not None and rest is not None and "," in rest and \
            a != own_number(text, {"digits": "unicode", "surrounding": "strict"}):
        return "R-comma"  # deletes every comma on the line, then requires the number alone
    return "other"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    exc = Counter()
    literal = {"grader": Counter(), "reference": Counter()}
    mechanism = {"grader": Counter(), "reference": Counter()}
    own = {"grader": {"digits": "unicode"}, "reference": {"digits": "unicode", "surrounding": "strict"}}
    examples = {}
    pids = sorted(PROBLEMS)
    for _ in range(n):
        pid = rng.choice(pids)
        text = rand_response(rng, pid)
        refs = PROBLEMS[pid]["answer"]
        try:
            prop, _ = repl.verdict(text, refs)
            achievable = {binary(repl.verdict(text, refs, c)[0]) for c in COMBOS}
            own_lab = {who: repl.verdict(text, refs, o)[0] for who, o in own.items()}
        except Exception as e:
            exc["replacement " + type(e).__name__] += 1
            continue
        for who, fn, attr in (("grader", grader_verdict, attribute_grader), ("reference", ref_verdict, attribute_ref)):
            try:
                v, a = fn(text, pid)
            except Exception as e:
                exc[who + " " + type(e).__name__] += 1
                continue
            # Literal step-3 rule.
            if binary(v) == binary(prop):
                key = "agree"
            elif binary(v) in achievable:
                key = "decision"
            else:
                key = "finding " + attr(text, pid, v, a)
            literal[who][key] += 1
            # Mechanism: against the replacement set to this grader's own readings.
            if binary(v) == binary(own_lab[who]):
                mkey = "agree"
            else:
                mkey = attr(text, pid, v, a)
            mechanism[who][mkey] += 1
            if key != "agree":
                examples.setdefault(f"{who} literal {key}", (pid, text, v, prop))
            if mkey != "agree":
                examples.setdefault(f"{who} mechanism {mkey}", (pid, text, v, own_lab[who]))
    print(f"{n} random responses, seed {seed}, {len(COMBOS)} reading combinations")
    print("exceptions:", dict(exc) or "none")
    for who in ("grader", "reference"):
        print(f"{who}, against the replacement at its own readings {own[who]}: {dict(sorted(mechanism[who].items()))}")
        print(f"{who}, literal rule (proposal / any reading combination): {dict(sorted(literal[who].items()))}")
    for k, (pid, text, a, b) in sorted(examples.items()):
        print(f"  example {k}: {pid} {ascii(text[:120])} -> {a} (compared label {b})")


if __name__ == "__main__":
    main()
