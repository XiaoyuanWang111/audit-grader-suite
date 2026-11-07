"""Fuzz the verifier's content check (check_answer.main, in-process) against the replacement's readings (step 4).

For each generated answer file, the grader's verdict (or exception) is compared with the replacement under the
proposed readings. A disagreement is a decision when some set of alternative readings makes the replacement agree
(the smallest such sets are named), and a finding when no combination does. The counts depend on this generator's
input distribution, so they are reported as counts, not rates.

Usage: python -I audit/scripts/fuzz_check_answer.py [N_CASES] [SEED]
Writes audit/results/fuzz_check_answer.json.
"""

import collections
import contextlib
import importlib.util
import io
import itertools
import json
import pathlib
import random
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grader_runner as GR  # noqa: E402
import replacement_verifier as RV  # noqa: E402

sys.dont_write_bytecode = True  # importing check_answer.py must not write case/task/tests/__pycache__
CONTENT_ENTRIES = [e for e in RV.DECISIONS if e != "D-symlink"]  # D-symlink does not apply to file content
CLASSES = {
    "key": (["4", "1", "41"], 30),
    "digit": (list("0123456789"), 10),
    "ascii_ws": (list(" \t\n\r\x0b\x0c"), 15),
    "unicode_ws": ([" ", "　", " ", "\u0085", " "], 8),
    "info_sep": (["\x1c", "\x1d", "\x1e", "\x1f"], 5),
    "letter": (list("abcxyzSE"), 10),
    "punct": (list("+-.,_:"), 10),
    "nul": (["\x00"], 3),
    "bom": (["﻿"], 3),
    "nonascii_digit": (["٤", "١", "４", "１"], 6),
}
NAMES = list(CLASSES)
WEIGHTS = [CLASSES[n][1] for n in NAMES]


def piece(rng):
    return rng.choice(CLASSES[rng.choices(NAMES, WEIGHTS)[0]][0])


def generate(rng):
    kind = rng.choices(["random", "mutate", "long", "bytes"], [40, 40, 10, 10])[0]
    if kind == "random":
        data = "".join(piece(rng) for _ in range(rng.randint(0, 8))).encode("utf-8")
    elif kind == "mutate":
        s = rng.choice(["41\n", "41"])
        for _ in range(rng.randint(1, 2)):
            i = rng.randint(0, len(s))
            op = rng.choice(["insert", "replace", "delete"])
            if op == "insert":
                s = s[:i] + piece(rng) + s[i:]
            elif op == "replace" and i < len(s):
                s = s[:i] + piece(rng) + s[i + 1:]
            elif op == "delete" and i < len(s):
                s = s[:i] + s[i + 1:]
        data = s.encode("utf-8")
    elif kind == "long":
        k = rng.randint(4280, 4320)
        data = rng.choice(["0" * (k - 2) + "41", "1" * k, "0" * (k - 2) + "42"]).encode() + rng.choice([b"", b"\n"])
    else:
        data = bytes(rng.randrange(256) for _ in range(rng.randint(1, 6)))
        if rng.random() < 0.5:
            i = rng.randint(0, len(data))
            data = data[:i] + b"41" + data[i:]
    return kind, data


def load_check_answer():
    spec = importlib.util.spec_from_file_location("check_answer_under_audit", GR.TESTS_DIR / "check_answer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grader_verdict(mod, data, workdir):
    p = workdir / "answer.txt"
    p.write_bytes(data)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = mod.main(["check_answer.py", str(p), str(GR.TESTS_DIR / "expected.json")])
    except Exception as e:  # noqa: BLE001 - recorded as a grading failure; verify.sh then exits 1
        return "fail", type(e).__name__
    return ("pass" if code == 0 else "fail"), None


def explaining_sets(data, grader):
    """Smallest sets of alternative readings under which the replacement gives the grader's verdict."""
    for size in range(1, len(CONTENT_ENTRIES) + 1):
        found = [list(c) for c in itertools.combinations(CONTENT_ENTRIES, size)
                 if RV.grade_text(data, sw=RV.switches_for(c))[0] == grader]
        if found:
            return found
    return []


def main(n_cases=3000, seed=20261107):
    rng = random.Random(seed)
    mod = load_check_answer()
    work = GR.new_tmpdir("fuzz_")
    counts = collections.Counter()
    by_kind = collections.Counter()
    examples = collections.defaultdict(list)
    exceptions = collections.Counter()
    try:
        for _ in range(n_cases):
            kind, data = generate(rng)
            by_kind[kind] += 1
            grader, exc = grader_verdict(mod, data, work)
            if exc:
                exceptions[exc] += 1
                examples[f"exception:{exc}"].append(f"{len(data)} bytes, starts {data[:12]!r}")
            proposed = RV.grade_text(data)[0]
            if grader == proposed:
                counts["agree"] += 1
                continue
            sets = explaining_sets(data, grader)
            if sets:
                key = f"decision {' + '.join(sets[0])}" + ("" if len(sets) == 1 else f" (or {len(sets) - 1} more)")
            else:
                key = "finding (no reading gives the grader's verdict)"
            key = f"grader {grader}, proposed {proposed}: {key}"
            counts[key] += 1
            if len(examples[key]) < 4:
                examples[key].append(repr(data[:40]))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    result = {"seed": seed, "cases": n_cases, "generator_kinds": dict(by_kind), "verdict_comparison": dict(counts),
              "exceptions": dict(exceptions), "examples": {k: v[:4] for k, v in examples.items()}}
    out = GR.AUDIT / "results" / "fuzz_check_answer.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=1, ensure_ascii=True))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 3000, int(a[1]) if len(a) > 1 else 20261107)
