"""Fuzz the verifier and the scorer (skill step 4). Prints counts; rates come from steps 5 and 6.

Usage: python -B audit/scripts/fuzz.py [N] [SEED]

1. Answer-content fuzz, in process: N random answer files through case/task/tests/check_answer.py main() and the
   replacement's verdict() under the proposed readings. Counts exceptions (a grading failure: the process would
   exit 1) and disagreements, and attributes each disagreement to the single decision switch that removes it,
   or to "no reading" (a defect).
2. Sandbox-layout enumeration through bash: every combination of out/answer.txt, /workspace/answer.txt and
   tmp/answer.txt being absent, a file holding 41, a file holding 37, or a directory.
3. Scorer fuzz: verifier_exit_code values and malformed records through case/score_trials.py.
"""

import itertools
import os
import random
import shutil
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import harness  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261111

PIECES = [
    "41", "41", "41", "4", "1", "0", "00", "37", "40", "44", "+", "-", ".", ",", "_", "e", "x", " ", " ", "\t",
    "\n", "\n", "\r\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x1f", "\x85", "\xa0", " ", "　",
    "​", "﻿", "\x00", "４１", "٤١", "count: ", " server errors", "**", "“",
    "”", "forty-one",
]


def random_content(rng):
    kind = rng.random()
    if kind < 0.05:
        return bytes(rng.randrange(256) for _ in range(rng.randrange(0, 12)))
    if kind < 0.08:
        return b"0" * rng.choice([4290, 4299, 4300, 4301, 5000]) + b"41" + rng.choice([b"", b"\n"])
    s = "".join(rng.choice(PIECES) for _ in range(rng.randrange(0, 6)))
    if rng.random() < 0.4:
        ws = rng.choice(["", " ", "\n", "\r\n", "\t", "\xa0", "\x1f", "　"])
        s = ws + "41" + rng.choice(["", "\n", " \n", ws])
    enc = "utf-16" if rng.random() < 0.02 else "utf-8"
    return s.encode(enc)


def content_fuzz():
    orig_main = harness.load_original_checker()
    repl = harness.load_replacement_checker()
    proposed = repl["settings"]({})
    flips = {name: dict(proposed, **{name: allowed[1]}) for name, allowed in repl["SWITCHES"].items()}
    expected = 41
    tmpdir = harness.new_tmp("fuzz_")
    exp_path = os.path.join(harness.ORIG_TESTS, "expected.json")
    rng = random.Random(SEED)
    stats = Counter()
    examples = {}
    devnull = open(os.devnull, "w")
    try:
        for i in range(N):
            raw = random_content(rng)
            p = os.path.join(tmpdir, "answer.txt")
            with open(p, "wb") as f:
                f.write(raw)
            old = sys.stdout
            sys.stdout = devnull
            try:
                code = orig_main(["check_answer.py", p, exp_path])
                exc = None
            except Exception as e:  # an uncaught exception exits 1 in the real run
                code, exc = 1, type(e).__name__
            finally:
                sys.stdout = old
            if exc:
                stats["exception:" + exc] += 1
                examples.setdefault("exception:" + exc, raw[:40] + (b"..." if len(raw) > 40 else b""))
            orig = code == 0
            want = repl["verdict"](raw, expected, proposed)
            stats["cases"] += 1
            stats["orig_pass"] += orig
            stats["repl_pass"] += want
            if orig != want:
                why = [n for n, cfg in flips.items() if repl["verdict"](raw, expected, cfg) == orig]
                key = "disagree:" + ("+".join(why) if why else "no reading") + (f" ({exc})" if exc else "")
                stats[key] += 1
                examples.setdefault(key, raw[:40] + (b"..." if len(raw) > 40 else b""))
    finally:
        devnull.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    return stats, examples


def layout_enum():
    options = {"absent": None, "41": b"41\n", "37": b"37\n", "dir": "dir"}
    rows = []
    for out_o, root_o, tmp_o in itertools.product(options, repeat=3):
        files = {}
        for key, opt in (("out/answer.txt", out_o), ("answer.txt", root_o), ("tmp/answer.txt", tmp_o)):
            v = options[opt]
            if v == "dir":
                files[key + "/"] = None
            elif v is not None:
                files[key] = v
        want = "pass" if out_o == "41" else "fail"
        ws = harness.materialize(files)
        try:
            got_o = harness.verdict_of(harness.run_verifier(ws, harness.ORIG_TESTS)[0])
            got_r = harness.verdict_of(harness.run_verifier(ws, harness.REPL_TESTS)[0])
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        rows.append((out_o, root_o, tmp_o, want, got_o, got_r))
    return rows


def scorer_fuzz():
    values = {"0": 0, "1": 1, "2": 2, "-9": -9, "127": 127, "null": None, "missing": "MISSING", '"0"': "0",
              '"1"': "1", "true": True, "false": False, "0.0": 0.0, "[]": []}
    rows = []
    for label, v in values.items():
        rec = {"config": "c", "agent_status": "completed", "verifier_exit_code": v}
        if v == "MISSING":
            del rec["verifier_exit_code"]
        d = harness.write_trials({"t": rec})
        try:
            t_o, out_o, rc_o = harness.run_scorer(d, harness.ORIG_SCORER)
            t_r, out_r, rc_r = harness.run_scorer(d, harness.REPL_SCORER)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        rows.append((label, t_o.get("c", (None, None, None))[1], rc_o, t_r.get("c", (None, None, None))[1], rc_r))
    broken = {
        "result.json truncated": b'{"config": "c", "verifier_exit',
        "result.json without config": b'{"verifier_exit_code": 0}',
    }
    stops = []
    for label, raw in broken.items():
        d = harness.write_trials({"t1": {"config": "c", "verifier_exit_code": 0}, "t2": raw})
        try:
            t_o, out_o, rc_o = harness.run_scorer(d, harness.ORIG_SCORER)
            t_r, out_r, rc_r = harness.run_scorer(d, harness.REPL_SCORER)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        err = out_o.strip().splitlines()[-1] if out_o.strip() else ""
        stops.append((label, rc_o, t_o, err, rc_r, t_r))
    return rows, stops


def main():
    print(f"# answer-content fuzz: N={N} seed={SEED}")
    stats, examples = content_fuzz()
    for k in sorted(stats):
        ex = f"   e.g. {examples[k]!r}" if k in examples else ""
        print(f"{k}: {stats[k]}{ex}")
    print("\n# sandbox layouts (out/answer.txt, /workspace/answer.txt, tmp/answer.txt): contract, current, replacement")
    rows = layout_enum()
    wrong_o = [r for r in rows if r[4] != r[3]]
    wrong_r = [r for r in rows if r[5] != r[3]]
    for r in rows:
        mark = "  <-- current wrong" if r[4] != r[3] else ""
        print(f"out={r[0]:<6} root={r[1]:<6} tmp={r[2]:<6} contract={r[3]} current={r[4]} replacement={r[5]}{mark}")
    print(f"layouts: {len(rows)}; current wrong: {len(wrong_o)}; replacement wrong: {len(wrong_r)}")
    print("\n# scorer: verifier_exit_code value -> passed count (current, exit) (replacement, exit); contract passes only 0")
    rows, stops = scorer_fuzz()
    for r in rows:
        print(f"{r[0]:<8} current passed={r[1]} rc={r[2]}   replacement passed={r[3]} rc={r[4]}")
    print("\n# scorer: one malformed record among two trials")
    for s in stops:
        print(f"{s[0]}: current rc={s[1]} table={s[2]} last line={s[3]!r}; replacement rc={s[4]} table={s[5]}")


if __name__ == "__main__":
    main()
