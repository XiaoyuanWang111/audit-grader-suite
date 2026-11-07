"""Step 4 fuzzing of the answer-content stage (check_answer.py), seeded.

check_answer.main runs in-process on each generated answer file, and the
replacement grades the same file under every combination of decision
readings. A disagreement with the proposed readings is a decision when some
combination of readings agrees with the grader, and a defect otherwise.
Exceptions are counted separately. Counts depend on the generators' input
distribution; they are counts, not rates. A few examples of each class are
then confirmed through the full verify.sh pipeline.

    python -I audit/scripts/fuzz_verifier.py audit/fuzz/fuzz_results.json
"""

import contextlib
import io
import itertools
import json
import os
import random
import sys
import tempfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "replacement")]

import common  # noqa: E402
import replacement_verifier as rv  # noqa: E402

SEED = 20261107
PER_GENERATOR = 4000
ENTRY_OF = {"leading_zeros": "D-leading-zeros", "plus_sign": "D-plus-sign", "digit_script": "D-digit-script",
            "whitespace_set": "D-whitespace-set", "encoding": "D-encoding"}

POOL = (
    [chr(c) for c in range(32, 127)] + list(" \t\n\r\v\f") * 3 + [chr(c) for c in range(0, 32)]
    + list("\u0085         　")
    + list("​﻿᠎") + list("٠٤١۴१４１\U0001d7d2")
    + ["+", "-", "0", "4", "1"] * 4
)


def gen_bytes(rng):
    return bytes(rng.randrange(256) for _ in range(rng.randint(0, 8)))


def gen_mutation(rng):
    s = list("41\n")
    for _ in range(rng.randint(1, 3)):
        op = rng.choice(["ins", "del", "rep"])
        pos = rng.randint(0, len(s))
        if op == "ins":
            s.insert(pos, rng.choice(POOL))
        elif s and pos < len(s):
            if op == "del":
                del s[pos]
            else:
                s[pos] = rng.choice(POOL)
    text = "".join(s)
    enc = rng.choice(["utf-8"] * 8 + ["utf-8-sig", "utf-16"])
    return text.encode(enc, "surrogatepass")


def gen_numeral(rng):
    ws = list(" \t\n\r\v\f") + [" ", "　", "\x1c", "\x1f", " "]
    pad = lambda: "".join(rng.choice(ws) for _ in range(rng.choice([0, 0, 1, 2, 3])))  # noqa: E731
    sign = rng.choice(["", "", "", "+", "-"])
    zeros = "0" * rng.choice([0, 0, 0, 1, 2, 5])
    body = rng.choice(["41", "41", "41", "40", "45", "37", "4", "410", "0"])
    return (pad() + sign + zeros + body + pad()).encode("utf-8")


def gen_long(rng):
    """Digit strings near Python's 4,300-digit int() limit, half of them 41 with leading zeros."""
    length = rng.randint(4290, 4310)
    if rng.random() < 0.5:
        return b"0" * (length - 2) + b"41\n"
    return bytes(rng.choice(b"0123456789") for _ in range(length)) + b"\n"


GENERATORS = {"random-bytes": gen_bytes, "mutations-of-41": gen_mutation, "numerals": gen_numeral,
              "long-digit-strings": gen_long}


def main(argv):
    common.require_pins("before fuzz")
    n = rv.count_server_errors()
    expected = os.path.join(common.TESTS_DIR, "expected.json")
    check_main = common.load_check_answer_main()
    names = sorted(rv.CHOICES)
    combos = [dict(zip(names, v)) for v in itertools.product(*(rv.CHOICES[k] for k in names))]
    rng = random.Random(SEED)
    summary = {}
    examples = defaultdict(list)
    with tempfile.TemporaryDirectory(prefix="fz_") as ws:
        os.makedirs(os.path.join(ws, "out"))
        path = os.path.join(ws, "out", "answer.txt")
        for gname, gen in GENERATORS.items():
            c = Counter()
            for _ in range(PER_GENERATOR):
                data = gen(rng)
                with open(path, "wb") as f:
                    f.write(data)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        rc = check_main(["check_answer.py", path, expected])
                    g = "pass" if rc == 0 else "fail"
                except Exception as e:  # a grading failure, counted apart from verdicts
                    g = "fail"
                    c[f"exception:{type(e).__name__}"] += 1
                    examples[f"exception:{type(e).__name__}"].append(data)
                p = rv.grade(ws, n)[0]
                c["inputs"] += 1
                c[f"grader_{g}"] += 1
                c[f"replacement_{p}"] += 1
                if g == p:
                    continue
                agreeing = [cb for cb in combos if rv.grade(ws, n, cb)[0] == g]
                if agreeing:
                    # Minimal sets of entries whose non-proposed readings give the grader's verdict.
                    sets = [frozenset(k for k in names if cb[k] != rv.PROPOSED[k]) for cb in agreeing]
                    minimal = sorted({s for s in sets if not any(o < s for o in sets)}, key=sorted)
                    label = " | ".join("+".join(sorted(ENTRY_OF[k] for k in s)) for s in minimal)
                    cls = f"decision:{label}:grader_{g}"
                else:
                    cls = f"defect:grader_{g}"
                c[cls] += 1
                examples[cls].append(data)
            summary[gname] = dict(sorted(c.items()))

    # Smallest examples per class, confirmed through verify.sh.
    confirm = {}
    for cls, exs in sorted(examples.items()):
        exs = sorted(set(exs), key=lambda b: (len(b), b))[:2]
        rows = []
        for data in exs:
            with tempfile.TemporaryDirectory(prefix="fc_") as ws:
                common.materialize(ws, {"out/answer.txt": data})
                code, out, err = common.run_verify(ws)
                rows.append({"answer_hex": data.hex(), "answer_repr": repr(data[:60]),
                             "verify_sh_exit": code, "verify_sh_output": out[:80],
                             "traceback": "Traceback" in err, "replacement": rv.grade(ws, n)[0]})
        confirm[cls] = rows
    common.require_pins("after fuzz")
    result = {"seed": SEED, "per_generator": PER_GENERATOR, "counts": summary, "confirmed_examples": confirm}
    os.makedirs(os.path.dirname(os.path.abspath(argv[0])), exist_ok=True)
    with open(argv[0], "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
