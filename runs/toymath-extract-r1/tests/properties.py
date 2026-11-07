"""Property and metamorphic cases for ToyMath, with each case's label known by construction (contract S1-S3).

generate(seed) returns case dicts: id, problem_id, response, prop, label. Each property isolates one stage.
Its wrong answers are far outside a 1% band around the reference, so that only P7 tests the tolerance.

  P1  thousands separators: inserting standard commas into a number of 1,000 or more keeps the verdict (S2.2)
  P2  reasoning lines before the answer line keep the verdict (S1.3)
  P3  lines after the answer line keep the verdict (S1.3)
  P4  spaces and tabs before "Answer:" keep the verdict (S1.2)
  P5  trailing zeros after the decimal point keep the verdict (S2.2)
  P6  CRLF or CR line ends keep the verdict (S1.1)
  P7  an answer more than 0.01 from the reference is incorrect (S3.2)
  P8  a later answer line with a wrong number makes the response incorrect (S1.3)
  P9  a lower-case label leaves no answer line (S1.4)
  P10 the reference number without an answer line is no answer (S1.5)
"""
import json
import os
import random
from decimal import Decimal

SEED = 20261106
CASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "case")

FILLER = [
    "Let me work through this step by step.",
    "The answer is not obvious at first.",
    "**Answer:** see the last line.",
    "answer: we compute it below",
    "Final Answer will follow.",
    "  - Step 2: multiply 12 by 3 to get 36.",
    "> Answer: quoted text is not an answer line",
    "Check: 2,500 - 700 = 1,800 and 1.5 x 2 = 3.",
    "The result could be 99 or 100, so recheck.",
    "Answers: several numbers appear here, 7 and 8.",
    "",
    "   ",
]


def _problems():
    with open(os.path.join(CASE, "problems.jsonl"), encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def with_commas(s):
    """Insert standard thousands separators into a decimal string such as -15000.5."""
    sign = "-" if s.startswith("-") else ""
    s = s.lstrip("-")
    whole, _, frac = s.partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return sign + ",".join(groups) + ("." + frac if frac else "")


def fmt(d):
    """Plain decimal string without exponent."""
    s = format(d, "f")
    return s


def far(rng, r):
    """A wrong answer at least 5% plus 1 away from r."""
    while True:
        mag = abs(r) * Decimal("0.05") + 1
        delta = mag * Decimal(rng.randint(1, 400)) / Decimal(10)
        x = r + (delta if rng.random() < 0.5 else -delta)
        x = x.quantize(Decimal(1)) if rng.random() < 0.6 else x.quantize(Decimal("0.01"))
        if abs(x - r) > mag:
            return x


def generate(seed=SEED, per_problem=6):
    rng = random.Random(seed)
    cases = []

    def add(prop, pid, response, label):
        cases.append({"id": "prop:%s:%05d" % (prop, len(cases)), "problem_id": pid, "response": response,
                      "prop": prop, "label": label})

    for p in _problems():
        pid, r = p["problem_id"], Decimal(p["answer"])
        rs = p["answer"]
        for _ in range(per_problem):
            xw = far(rng, r)
            pairs = [(rs, "correct"), (fmt(xw), "incorrect")]
            # P1: numbers of 1,000 or more, with and without separators
            big = r if abs(r) >= 1000 else None
            cand = [(fmt(big), "correct")] if big is not None else []
            while True:
                x = Decimal(rng.randint(1000, 9999999)) * (1 if rng.random() < 0.8 else Decimal("0.01"))
                if abs(x) >= 1000 and abs(x - r) > abs(r) * Decimal("0.05") + 1:
                    break
            cand.append((fmt(x), "incorrect"))
            # numbers whose first group equals the reference, e.g. 15,321 for 15
            if 0 < r < 1000 and r == r.to_integral_value():
                y = int(r) * 1000 + rng.randint(1, 999)
                cand.append((str(y), "incorrect"))
            for s, lab in cand:
                add("P1", pid, "Work.\nAnswer: " + s, lab)
                add("P1", pid, "Work.\nAnswer: " + with_commas(s), lab)
            for s, lab in pairs:
                pre = "\n".join(rng.choice(FILLER) for _ in range(rng.randint(1, 5)))
                add("P2", pid, pre + "\nAnswer: " + s, lab)
                post = "\n".join(rng.choice([l for l in FILLER]) for _ in range(rng.randint(1, 4)))
                add("P3", pid, "Work.\nAnswer: " + s + "\n" + post, lab)
                ws = "".join(rng.choice(" \t") for _ in range(rng.randint(1, 8)))
                add("P4", pid, "Work.\n" + ws + "Answer: " + s, lab)
                s5 = s + ("" if "." in s else ".") + "0" * rng.randint(1, 4)
                add("P5", pid, "Work.\nAnswer: " + s5, lab)
                end = rng.choice(["\r\n", "\r"])
                add("P6", pid, end.join(["Work.", "More work.", "Answer: " + s, ""]), lab)
            # P7: off by more than 0.01, concentrated inside a 1% band
            while True:
                delta = Decimal(rng.randint(101, 10000)) / Decimal(10000) * max(Decimal(1), abs(r) / 50)
                delta = delta.quantize(Decimal("0.0001"))
                x = r + (delta if rng.random() < 0.5 else -delta)
                if abs(x - r) > Decimal("0.01"):
                    break
            add("P7", pid, "Work.\nAnswer: " + fmt(x), "incorrect")
            add("P8", pid, "Answer: " + rs + "\nWait, let me redo this.\nAnswer: " + fmt(xw), "incorrect")
            add("P9", pid, "Work.\nanswer: " + rs, "no_answer")
            add("P10", pid, "Work.\nThe result is " + rs + ".", "no_answer")
    return cases


PROPS = ["P%d" % i for i in range(1, 11)]

if __name__ == "__main__":
    import collections
    cs = generate()
    print(len(cs), "cases", dict(collections.Counter(c["prop"] for c in cs)))
