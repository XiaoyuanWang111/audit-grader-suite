"""Step 5 analysis of audit/results/panel_verdicts.jsonl.

Writes audit/results/panel_summary.json and prints the tables that audit/AUDIT.md quotes.
Graders: A = SkyRL reward (NVIDIA checkers); B = verifyit gate (43 deterministic ids);
R = replacement, proposed readings; RfixA / RfixB = replacement with the readings grader A / B
follows, so that A vs RfixA isolates A's defects and RfixA vs R isolates the decisions.
A constraint verdict of grader g is "correct" when it equals R, a "decision" when it differs from
R but equals Rfix_g, and a "defect" otherwise.
"""
import collections
import json
import os

import numpy as np

AUDIT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(AUDIT, "results")
CASE = os.path.join(AUDIT, "..", "case")
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language",
            "letters:letter_counting"}
RUN_NAMES = {
    ("Qwen__Qwen3-4B-Instruct-2507", "sample0"): "Qwen3-4B-Instruct-2507 sample0",
    ("Qwen__Qwen3-4B-Instruct-2507", "greedy"): "Qwen3-4B-Instruct-2507 greedy",
    ("Qwen__Qwen3-4B-Instruct-2507", "greedy_repeat"): "Qwen3-4B-Instruct-2507 greedy_repeat",
    ("Qwen__Qwen2.5-7B-Instruct", "sample0"): "Qwen2.5-7B-Instruct sample0",
    ("allenai__OLMo-2-1124-7B-Instruct", "sample0"): "OLMo-2-1124-7B-Instruct sample0",
    ("Qwen__Qwen3-4B-Thinking-2507__thinking", "sample0"): "Qwen3-4B-Thinking-2507 sample0 (thinking)",
}


def load():
    rows = []
    with open(os.path.join(RES, "panel_verdicts.jsonl"), encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def boot_ci(diff, reps=2000, seed=0):
    rng = np.random.default_rng(seed)
    diff = np.asarray(diff, dtype=float)
    n = len(diff)
    means = diff[rng.integers(0, n, size=(reps, n))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def pct(x):
    return round(100 * x, 2)


def main():
    rows = load()
    held = set(open(os.path.join(AUDIT, "frozen", "heldout_uuids.txt"), encoding="utf-8").read().split())
    raw_think = {}
    import glob
    for path in glob.glob(os.path.join(CASE, "panel", "*", "*.jsonl")):
        folder = os.path.basename(os.path.dirname(path))
        run = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                raw_think[(folder, run, p["uuid"])] = "<think>" in p["raw_response"]
    summary = {}

    # ---------------- records and extraction
    by_run = collections.defaultdict(list)
    for r in rows:
        by_run[(r["folder"], r["run"])].append(r)
    rec_table = []
    for key, rs in by_run.items():
        rec_table.append({
            "run": RUN_NAMES[key], "n": len(rs),
            "length": sum(r["finish"] == "length" for r in rs),
            "unclosed_reasoning": sum(r["r_extract_fail"] for r in rs),
            "unclosed_and_A_reward_1": sum(r["r_extract_fail"] and r["a_reward"] == 1.0 for r in rs),
            "literal_think_nonthinking": sum((not r["thinking"]) and raw_think[(r["folder"], r["run"], r["uuid"])] for r in rs),
            "A_text_empty": sum(r["a_text_empty"] for r in rs),
            "A_text_empty_reward_1": sum(r["a_text_empty"] and r["a_reward"] == 1.0 for r in rs),
            "A_exception_rows": sum(bool(r["a_errors"]) for r in rs),
        })
    summary["records"] = rec_table

    # ---------------- row-level scores
    def row_scores(rs):
        A = np.array([r["a_reward"] for r in rs])
        R = np.array([all(c[3] for c in r["c"]) for r in rs], dtype=float)
        RA = np.array([all(c[4] for c in r["c"]) for r in rs], dtype=float)
        gate = lambda r, k: all(c[k] for c in r["c"] if c[0] not in SEMANTIC)
        B = np.array([gate(r, 2) for r in rs], dtype=float)
        RG = np.array([gate(r, 3) for r in rs], dtype=float)
        RB = np.array([gate(r, 5) for r in rs], dtype=float)
        return A, R, RA, B, RG, RB

    score_table = []
    for key, rs in sorted(by_run.items(), key=lambda kv: RUN_NAMES[kv[0]]):
        for subset_name, sub in (("all", rs), ("held-out", [r for r in rs if r["uuid"] in held])):
            A, R, RA, B, RG, RB = row_scores(sub)
            score_table.append({
                "run": RUN_NAMES[key], "subset": subset_name, "n": len(sub),
                "A": pct(A.mean()), "R_proposed": pct(R.mean()), "R_fixes_only_A": pct(RA.mean()),
                "R_minus_A": pct(R.mean() - A.mean()), "R_minus_A_ci": [pct(x) for x in boot_ci(R - A)],
                "fixA_minus_A": pct(RA.mean() - A.mean()), "fixA_minus_A_ci": [pct(x) for x in boot_ci(RA - A)],
                "B_gate": pct(B.mean()), "R_gate": pct(RG.mean()), "R_gate_fixes_only_B": pct(RB.mean()),
                "Rgate_minus_B": pct(RG.mean() - B.mean()), "Rgate_minus_B_ci": [pct(x) for x in boot_ci(RG - B)],
                "fixB_minus_B": pct(RB.mean() - B.mean()), "fixB_minus_B_ci": [pct(x) for x in boot_ci(RB - B)],
                "A_rows_gained_by_R": int(((R == 1) & (A == 0)).sum()), "A_rows_lost_by_R": int(((R == 0) & (A == 1)).sum()),
            })
    summary["scores"] = score_table

    # ---------------- rerun
    g = {r["uuid"]: r for r in by_run[("Qwen__Qwen3-4B-Instruct-2507", "greedy")]}
    gr = {r["uuid"]: r for r in by_run[("Qwen__Qwen3-4B-Instruct-2507", "greedy_repeat")]}
    common = sorted(set(g) & set(gr))
    a1 = np.array([g[u]["a_reward"] for u in common]); a2 = np.array([gr[u]["a_reward"] for u in common])
    r1 = np.array([all(c[3] for c in g[u]["c"]) for u in common], float)
    r2 = np.array([all(c[3] for c in gr[u]["c"]) for u in common], float)
    same_text = 0
    raws = {}
    for run in ("greedy", "greedy_repeat"):
        with open(os.path.join(CASE, "panel", "Qwen__Qwen3-4B-Instruct-2507", run + ".jsonl"), encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                raws[(run, p["uuid"])] = p["raw_response"]
    same_text = sum(raws[("greedy", u)] == raws[("greedy_repeat", u)] for u in common)
    summary["rerun"] = {
        "rows": len(common), "identical_responses": same_text,
        "A_greedy": pct(a1.mean()), "A_repeat": pct(a2.mean()), "A_repeat_minus_greedy": pct(a2.mean() - a1.mean()),
        "A_rows_changed": int((a1 != a2).sum()),
        "R_greedy": pct(r1.mean()), "R_repeat": pct(r2.mean()), "R_repeat_minus_greedy": pct(r2.mean() - r1.mean()),
        "R_rows_changed": int((r1 != r2).sum()),
    }

    # ---------------- per check
    per = collections.defaultdict(collections.Counter)
    for r in rows:
        for iid, a, b, rr, ra, rb in r["c"]:
            p = per[iid]
            p["n"] += 1
            p["A_pass"] += a
            p["R_pass"] += rr
            p["RfixA_pass"] += ra
            p["A_ne_R"] += a != rr
            p["A_defect"] += (a != rr) and (a != ra)
            p["A_decision"] += (a != rr) and (a == ra)
            p["A_false_pass"] += a and not rr
            p["A_false_pass_defect"] += a and not ra
            p["A_false_fail_defect"] += (not a) and ra
            if b is not None:
                p["nB"] += 1
                p["B_pass"] += b
                p["B_ne_R"] += b != rr
                p["B_defect"] += (b != rr) and (b != rb)
                p["B_decision"] += (b != rr) and (b == rb)
                p["B_false_pass_defect"] += b and not rb
                p["A_ne_B"] += a != b
    summary["per_check"] = {k: dict(v) for k, v in sorted(per.items())}
    tot = collections.Counter()
    for v in per.values():
        tot.update(v)
    summary["per_check_total"] = dict(tot)

    # ---------------- A vs B disagreements classified
    ab = collections.Counter()
    for r in rows:
        for iid, a, b, rr, ra, rb in r["c"]:
            if b is None or a == b:
                continue
            ab["disagree"] += 1
            wrong_a = "A ok" if a == rr else ("A decision" if a == ra else "A defect")
            wrong_b = "B ok" if b == rr else ("B decision" if b == rb else "B defect")
            ab[wrong_a + " / " + wrong_b] += 1
    summary["A_vs_B"] = dict(ab)

    # ---------------- false rewards (row level)
    fr = collections.Counter()
    for r in rows:
        if r["a_reward"] == 1.0:
            fr["A_rewards"] += 1
            if not all(c[3] for c in r["c"]):
                fr["A_rewards_R_fails"] += 1
            if not all(c[4] for c in r["c"]):
                fr["A_rewards_fixA_fails"] += 1
        if all(c[2] for c in r["c"] if c[0] not in SEMANTIC):
            fr["B_gate_passes"] += 1
            if not all(c[3] for c in r["c"] if c[0] not in SEMANTIC):
                fr["B_gate_R_fails"] += 1
            if not all(c[5] for c in r["c"] if c[0] not in SEMANTIC):
                fr["B_gate_fixB_fails"] += 1
    summary["false_rewards"] = dict(fr)

    with open(os.path.join(RES, "panel_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: summary[k] for k in ("records", "rerun", "A_vs_B", "false_rewards", "per_check_total")}, indent=1))
    for s in score_table:
        print({k: s[k] for k in ("run", "subset", "n", "A", "R_proposed", "R_fixes_only_A", "R_minus_A", "R_minus_A_ci",
                                 "fixA_minus_A", "fixA_minus_A_ci", "B_gate", "R_gate", "R_gate_fixes_only_B",
                                 "Rgate_minus_B", "fixB_minus_B", "fixB_minus_B_ci")})


if __name__ == "__main__":
    main()
