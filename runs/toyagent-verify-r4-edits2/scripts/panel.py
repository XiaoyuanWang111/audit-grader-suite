"""Step 5: grade the 36 stored trials with the current grader and the replacement, and compare scores.

Usage: python -B audit/scripts/panel.py [OUT_JSON]

For each trial: copy its stored workspace to a temporary sandbox (adding the empty out/ directory that every
sandbox starts with, since empty directories are not stored), run case/task/tests/verify.sh as the harness does
and compare its exit status with the stored verifier_exit_code, then run the replacement under the proposed
readings and under each decision's other reading. Scores: the current pipeline (stored exit codes through
case/score_trials.py) and the replacement pipeline (replacement exit codes through audit/replacement/score_trials.py).
Checks the case manifest before and after the run.
"""

import json
import os
import random
import shutil
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import harness  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(harness.AUDIT, "panel", "panel_verdicts.json")
TRIALS = os.path.join(harness.CASE, "trials")
FLIPS = {
    "D-surrounding-text": {"D_SURROUNDING_TEXT": "embedded"},
    "D-whitespace": {"D_WHITESPACE": "unicode"},
    "D-leading-zeros": {"D_LEADING_ZEROS": "forbid"},
    "D-plus-sign": {"D_PLUS_SIGN": "allow"},
    "D-nonascii-digits": {"D_NONASCII_DIGITS": "allow"},
}
BOOT = 10000
SEED = 20261111


def snapshot(trial):
    """The stored final sandbox of a trial as a files dict (out/ added)."""
    files = {"out/": None}
    ws = os.path.join(TRIALS, trial, "workspace")
    if os.path.isdir(ws):
        for root, dirs, names in os.walk(ws):
            for n in names:
                p = os.path.join(root, n)
                rel = os.path.relpath(p, ws).replace(os.sep, "/")
                with open(p, "rb") as f:
                    files[rel] = f.read()
    return files


def grade_all():
    rows = []
    for trial in sorted(os.listdir(TRIALS)):
        with open(os.path.join(TRIALS, trial, "result.json"), encoding="utf-8") as f:
            rec = json.load(f)
        files = snapshot(trial)
        ws = harness.materialize(files)
        try:
            cur_code, cur_out = harness.run_verifier(ws, harness.ORIG_TESTS)
            rep_code, rep_out = harness.run_verifier(ws, harness.REPL_TESTS)
            flips = {d: harness.run_verifier(ws, harness.REPL_TESTS, env)[0] for d, env in FLIPS.items()}
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        answer = files.get("out/answer.txt")
        rows.append({
            "trial": trial, "config": rec["config"], "agent_status": rec["agent_status"],
            "stored_exit": rec["verifier_exit_code"], "stored_output": rec["verifier_output"],
            "rerun_exit": cur_code, "rerun_output": cur_out,
            "replacement_exit": rep_code, "replacement_output": rep_out,
            "flip_exit": flips,
            "answer_files": sorted(k for k in files if k.endswith("answer.txt")),
            "out_answer": None if answer is None else answer.decode("utf-8", "replace"),
        })
    return rows


def reward_current(code):  # the rule in case/score_trials.py
    return 0.0 if code else 1.0


def reward_contract(code):
    return 1.0 if (type(code) is int and code == 0) else 0.0


def boot_ci(pairs, rng):
    """Paired bootstrap over trials: 95% interval of mean(b) - mean(a), in points."""
    n = len(pairs)
    diffs = []
    for _ in range(BOOT):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(100.0 * sum(b - a for a, b in s) / n)
    diffs.sort()
    return diffs[int(0.025 * BOOT)], diffs[int(0.975 * BOOT) - 1]


def main():
    problems = harness.check_manifest()
    print(f"manifest before: {'OK' if not problems else problems}")
    rows = grade_all()
    problems = harness.check_manifest()
    print(f"manifest after: {'OK' if not problems else problems}")

    print("\n# stored records")
    print("agent_status:", dict(Counter(r["agent_status"] for r in rows)))
    print("stored verifier_exit_code:", dict(Counter(str(r["stored_exit"]) for r in rows)))
    print("stored verifier_output:", dict(Counter(r["stored_output"] for r in rows)))
    print("answer file locations:", dict(Counter(",".join(r["answer_files"]) or "<none>" for r in rows)))
    print("out/answer.txt contents:", dict(Counter(repr(r["out_answer"]) for r in rows)))
    repro = sum(r["rerun_exit"] == r["stored_exit"] for r in rows)
    print(f"offline rerun of verify.sh reproduces the stored exit status: {repro}/{len(rows)}")

    print("\n# per trial: stored exit, rerun exit, replacement exit, flips that change the replacement")
    for r in rows:
        flips = [d for d, c in r["flip_exit"].items() if (c == 0) != (r["replacement_exit"] == 0)]
        mark = "  <-- disagree" if (r["stored_exit"] == 0) != (r["replacement_exit"] == 0) else ""
        print(f"{r['trial']} {r['config']:<18} {r['agent_status']:<9} files={','.join(r['answer_files']) or '-':<26}"
              f" stored={r['stored_exit']} rerun={r['rerun_exit']} repl={r['replacement_exit']}"
              f" flips={','.join(flips) or '-'}{mark}")

    rng = random.Random(SEED)
    by_cfg = defaultdict(list)
    for r in rows:
        by_cfg[r["config"]].append(r)
    print("\n# scores (percent of the configuration's 9 trials); change = replacement minus current, paired"
          f" bootstrap 95% interval over trials ({BOOT} resamples, seed {SEED})")
    header = f"{'config':<20}{'n':>3}{'current':>9}{'replacement':>13}{'change':>9}  interval"
    for d in FLIPS:
        header += f"  {d}"
    print(header)
    summary = {}
    all_pairs = []
    for cfg in sorted(by_cfg):
        rs = by_cfg[cfg]
        cur = [reward_current(r["stored_exit"]) for r in rs]
        rep = [reward_contract(r["replacement_exit"]) for r in rs]
        pairs = list(zip(cur, rep))
        all_pairs += pairs
        lo, hi = boot_ci(pairs, rng)
        line = (f"{cfg:<20}{len(rs):>3}{100 * sum(cur) / len(rs):>9.1f}{100 * sum(rep) / len(rs):>13.1f}"
                f"{100 * (sum(rep) - sum(cur)) / len(rs):>+9.1f}  [{lo:+.1f}, {hi:+.1f}]")
        flips = {}
        for d in FLIPS:
            fs = [reward_contract(r["flip_exit"][d]) for r in rs]
            flips[d] = 100 * sum(fs) / len(rs)
            line += f"  {flips[d]:.1f}"
        print(line)
        summary[cfg] = {"n": len(rs), "current": 100 * sum(cur) / len(rs), "replacement": 100 * sum(rep) / len(rs),
                        "change_ci": [lo, hi], "flips": flips}
    n = len(rows)
    cur_pass = [r for r in rows if reward_current(r["stored_exit"]) == 1.0]
    false_rewards = [r["trial"] for r in cur_pass if r["replacement_exit"] != 0]
    disagree = [r["trial"] for r in rows if (r["stored_exit"] == 0) != (r["replacement_exit"] == 0)]
    missed = [r["trial"] for r in rows if r["stored_exit"] != 0 and r["replacement_exit"] == 0]
    print(f"\nall trials: current passes {len(cur_pass)}/{n}, replacement passes "
          f"{sum(r['replacement_exit'] == 0 for r in rows)}/{n}")
    print(f"verdict disagreements: {len(disagree)}/{n} {disagree}")
    print(f"false rewards (current pass, contract fail): {len(false_rewards)}/{len(cur_pass)} passes {false_rewards}")
    print(f"current fails that the contract passes: {len(missed)} {missed}")
    print(f"scored coverage: current {sum(r['stored_exit'] is not None for r in rows)}/{n}, "
          f"replacement {sum(r['replacement_exit'] is not None for r in rows)}/{n}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"rows": rows, "summary": summary}, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"\nwrote {os.path.relpath(OUT, harness.ROOT)}")


if __name__ == "__main__":
    main()
