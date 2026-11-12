"""Step 5 analysis of audit/work/panel_verdicts.jsonl.

Prints and writes audit/work/panel_summary.json:
- per run: responses, truncations, extraction failures, empty graded text, errors;
- per check: verdict counts, pass rates of A, B, R, disagreements with R split into
  decision-explained (some subset of the relevant alternative readings makes R agree) and
  unexplained (a defect candidate);
- per run: score of A (SkyRL reward) and of R as a reward, gate pass rate of B and R, paired
  differences with 95% bootstrap intervals over rows;
- false rewards: A reward 1.0 that R contradicts under the proposed readings, and under every
  reading considered;
- the greedy rerun difference.

Usage: analyze_panel.py [all|heldout|dev]
"""
import collections
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from heldout import is_heldout  # noqa: E402

SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language",
            "letters:letter_counting"}
subset_name = sys.argv[1] if len(sys.argv) > 1 else "all"

recs = []
with open(os.path.join(AUDIT, "work", "panel_verdicts.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        h = is_heldout(r["run"], r["uuid"])
        if subset_name == "heldout" and not h:
            continue
        if subset_name == "dev" and h:
            continue
        recs.append(r)


def explained(c, grader_verdict):
    """Minimal subsets of alternative readings under which R gives the grader's verdict."""
    subsets = [k for k, v in c["R_alt"].items() if v == grader_verdict]
    if not subsets:
        return None
    best = min(len(k.split("+")) for k in subsets)
    return sorted(k for k in subsets if len(k.split("+")) == best)


def robust_fail(c):
    """R fails the constraint under the proposed readings and under every alternative considered."""
    return (not c["R"]) and all(v is False for v in c["R_alt"].values())


# ---------------------------------------------------------------- per run
runs = collections.OrderedDict()
for r in recs:
    s = runs.setdefault(r["run"], collections.Counter())
    s["responses"] += 1
    s["finish_length"] += r["finish_reason"] == "length"
    s["extraction_failure"] += r["extraction_failure"]
    s["A_text_empty"] += r["a_text_empty"]
    s["B_text_empty"] += r["b_text_empty"]
    s["A_errors"] += sum(1 for c in r["constraints"] if c["A_err"])
    s["A_rows_with_error"] += any(c["A_err"] for c in r["constraints"])
    s["B_errors"] += sum(1 for c in r["constraints"] if c["B_err"])
    s["constraints"] += len(r["constraints"])
    if r["extraction_failure"]:
        s["extraction_failure_A_reward1"] += all(c["A"] for c in r["constraints"])
        s["extraction_failure_B_gate_pass"] += all(c["B"] for c in r["constraints"] if c["iid"] not in SEMANTIC)

# ---------------------------------------------------------------- per check
checks = collections.defaultdict(collections.Counter)
expl_counter = collections.defaultdict(collections.Counter)
for r in recs:
    for c in r["constraints"]:
        k = checks[c["iid"]]
        k["n"] += 1
        if r["extraction_failure"]:
            k["extraction_failure"] += 1
            k["A_pass_on_extraction_failure"] += c["A"]
            k["B_pass_on_extraction_failure"] += c["B"]
            continue
        k["A_pass"] += c["A"]
        k["B_pass"] += c["B"]
        k["R_pass"] += c["R"]
        k["A_err"] += bool(c["A_err"])
        for g in ("A", "B"):
            if g == "B" and c["iid"] in SEMANTIC:
                continue
            if c[g] != c["R"]:
                k[f"{g}_disagree"] += 1
                k[f"{g}_false_pass" if c[g] else f"{g}_false_fail"] += 1
                e = explained(c, c[g])
                if e is None:
                    k[f"{g}_unexplained"] += 1
                    k[f"{g}_unexplained_{'pass' if c[g] else 'fail'}"] += 1
                else:
                    k[f"{g}_decision"] += 1
                    expl_counter[(g, c["iid"])][" | ".join(e)] += 1
        if c["iid"] not in SEMANTIC and c["A"] != c["B"]:
            k["A_vs_B_disagree"] += 1


# ---------------------------------------------------------------- per run scores
def boot(diffs, n=2000, seed=0):
    rng = random.Random(seed)
    m = len(diffs)
    if m == 0:
        return (0.0, 0.0)
    vals = []
    for _ in range(n):
        s = 0.0
        for _ in range(m):
            s += diffs[rng.randrange(m)]
        vals.append(s / m)
    vals.sort()
    return (vals[int(0.025 * n)], vals[int(0.975 * n) - 1])


scores = collections.OrderedDict()
false_rewards = collections.OrderedDict()
for run in runs:
    rows = [r for r in recs if r["run"] == run]
    a = [1.0 if all(c["A"] for c in r["constraints"]) else 0.0 for r in rows]
    rr = [1.0 if all(c["R"] for c in r["constraints"]) else 0.0 for r in rows]
    bg = [1.0 if all(c["B"] for c in r["constraints"] if c["iid"] not in SEMANTIC) else 0.0 for r in rows]
    rg = [1.0 if all(c["R"] for c in r["constraints"] if c["iid"] not in SEMANTIC) else 0.0 for r in rows]
    n = len(rows)
    d1 = [x - y for x, y in zip(rr, a)]
    d2 = [x - y for x, y in zip(rg, bg)]
    scores[run] = {
        "rows": n,
        "A_reward": sum(a) / n, "R_reward": sum(rr) / n, "R_minus_A": sum(d1) / n, "R_minus_A_ci": boot(d1),
        "B_gate": sum(bg) / n, "R_gate": sum(rg) / n, "R_gate_minus_B": sum(d2) / n, "R_gate_minus_B_ci": boot(d2),
        "A_rows_changed": sum(1 for x in d1 if x), "B_rows_changed": sum(1 for x in d2 if x),
    }

    # fixes only: R's verdict, except where the grader's verdict is one of the allowed readings
    def fix(c, g):
        if c[g] != c["R"] and any(v == c[g] for v in c["R_alt"].values()):
            return c[g]
        return c["R"]

    # sensitivity: also keep the grader's verdict on checks where R is least reliable
    UNSURE = {"detectable_format:sentence_hyphens", "language:response_language",
              "detectable_format:bigram_wrapping"}

    def fix_sure(c, g):
        return c[g] if c["iid"] in UNSURE else fix(c, g)

    for tag, fn in (("fix", fix), ("fixsure", fix_sure)):
        fa = [1.0 if (not r["extraction_failure"]) and all(fn(c, "A") for c in r["constraints"]) else 0.0 for r in rows]
        fb = [1.0 if (not r["extraction_failure"]) and all(fn(c, "B") for c in r["constraints"] if c["iid"] not in SEMANTIC) else 0.0 for r in rows]
        da = [x - y for x, y in zip(fa, a)]
        db = [x - y for x, y in zip(fb, bg)]
        scores[run][f"A_{tag}"] = sum(fa) / n
        scores[run][f"A_{tag}_minus_A"] = sum(da) / n
        scores[run][f"A_{tag}_minus_A_ci"] = boot(da)
        scores[run][f"A_{tag}_gained_lost"] = (sum(1 for x in da if x > 0), sum(1 for x in da if x < 0))
        scores[run][f"B_{tag}"] = sum(fb) / n
        scores[run][f"B_{tag}_minus_B"] = sum(db) / n
        scores[run][f"B_{tag}_minus_B_ci"] = boot(db)
        scores[run][f"B_{tag}_gained_lost"] = (sum(1 for x in db if x > 0), sum(1 for x in db if x < 0))
    fr_prop = fr_rob = a1 = 0
    b_fr_prop = b_fr_rob = b1 = 0
    for r in rows:
        if all(c["A"] for c in r["constraints"]):
            a1 += 1
            if not all(c["R"] for c in r["constraints"]):
                fr_prop += 1
            if r["extraction_failure"] or any(robust_fail(c) for c in r["constraints"]):
                fr_rob += 1
        gate_cons = [c for c in r["constraints"] if c["iid"] not in SEMANTIC]
        if all(c["B"] for c in gate_cons):
            b1 += 1
            if not all(c["R"] for c in gate_cons):
                b_fr_prop += 1
            if r["extraction_failure"] or any(robust_fail(c) for c in gate_cons):
                b_fr_rob += 1
    false_rewards[run] = {"A_reward1": a1, "A_false_proposed": fr_prop, "A_false_every_reading": fr_rob,
                          "B_gate_pass": b1, "B_false_proposed": b_fr_prop, "B_false_every_reading": b_fr_rob}

# ---------------------------------------------------------------- greedy rerun
rerun = {}
g1 = {r["uuid"]: r for r in recs if r["run"].endswith("greedy.jsonl")}
g2 = {r["uuid"]: r for r in recs if r["run"].endswith("greedy_repeat.jsonl")}
common = sorted(set(g1) & set(g2))
if common:
    def rw(r, g):
        return 1.0 if all(c[g] for c in r["constraints"]) else 0.0

    def gate(r, g):
        return 1.0 if all(c[g] for c in r["constraints"] if c["iid"] not in SEMANTIC) else 0.0
    for g in ("A", "R"):
        d = [rw(g2[u], g) - rw(g1[u], g) for u in common]
        rerun[f"{g}_reward_repeat_minus_greedy"] = (sum(d) / len(d), boot(d), sum(1 for x in d if x))
    for g in ("B", "R"):
        d = [gate(g2[u], g) - gate(g1[u], g) for u in common]
        rerun[f"{g}_gate_repeat_minus_greedy"] = (sum(d) / len(d), boot(d), sum(1 for x in d if x))
    rerun["identical_raw_responses"] = None
    rerun["rows"] = len(common)

summary = {"subset": subset_name, "responses": len(recs), "runs": runs, "checks": checks,
           "decision_explanations": {f"{g}|{i}": dict(v.most_common()) for (g, i), v in expl_counter.items()},
           "scores": scores, "false_rewards": false_rewards, "rerun": rerun}
with open(os.path.join(AUDIT, "work", f"panel_summary_{subset_name}.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=1, default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))

print(f"subset={subset_name} responses={len(recs)}")
for run, s in runs.items():
    print(run, dict(s))
print("\nper check: n, pass% A B R | A vs R: disagree (unexplained pass/fail, decision) | B vs R: same | A_err")
tot = collections.Counter()
for iid in sorted(checks):
    k = checks[iid]
    tot.update(k)
    n = k["n"]
    print(f"{iid:<46} {n:>5} {100*k['A_pass']/n:5.1f} {100*k['B_pass']/n:5.1f} {100*k['R_pass']/n:5.1f} | "
          f"A {k['A_disagree']:>4} ({k['A_unexplained_pass']:>4}/{k['A_unexplained_fail']:>4}, {k['A_decision']:>4}) | "
          f"B {k['B_disagree']:>4} ({k['B_unexplained_pass']:>4}/{k['B_unexplained_fail']:>4}, {k['B_decision']:>4}) | {k['A_err']}")
print("TOTAL", {k: tot[k] for k in ["n", "A_disagree", "A_unexplained", "A_decision", "B_disagree", "B_unexplained", "B_decision", "A_err"]})
print("\nscores (row level, mean over rows)")
for run, s in scores.items():
    print(f"{run:<55} n={s['rows']:>5} A={s['A_reward']:.3f} R={s['R_reward']:.3f} R-A={s['R_minus_A']:+.3f} "
          f"[{s['R_minus_A_ci'][0]:+.3f},{s['R_minus_A_ci'][1]:+.3f}] | Bgate={s['B_gate']:.3f} Rgate={s['R_gate']:.3f} "
          f"R-B={s['R_gate_minus_B']:+.3f} [{s['R_gate_minus_B_ci'][0]:+.3f},{s['R_gate_minus_B_ci'][1]:+.3f}]")
print("\nfalse rewards")
for run, s in false_rewards.items():
    print(run, s)
print("\nrerun", rerun)
print("\nfixes only (grader readings kept where allowed) and sensitivity without sentence_hyphens/language/bigram")
for run, s in scores.items():
    print(f"{run:<55} A={s['A_reward']:.3f} Afix={s['A_fix']:.3f} ({s['A_fix_minus_A']:+.3f} [{s['A_fix_minus_A_ci'][0]:+.3f},{s['A_fix_minus_A_ci'][1]:+.3f}] +{s['A_fix_gained_lost'][0]}/-{s['A_fix_gained_lost'][1]}) "
          f"Afixsure={s['A_fixsure']:.3f} ({s['A_fixsure_minus_A']:+.3f}) | B={s['B_gate']:.3f} Bfix={s['B_fix']:.3f} ({s['B_fix_minus_B']:+.3f} [{s['B_fix_minus_B_ci'][0]:+.3f},{s['B_fix_minus_B_ci'][1]:+.3f}] +{s['B_fix_gained_lost'][0]}/-{s['B_fix_gained_lost'][1]}) Bfixsure={s['B_fixsure']:.3f} ({s['B_fixsure_minus_B']:+.3f})")
nA = sum(k["n"] - k["extraction_failure"] for k in checks.values())
nB = sum(k["n"] - k["extraction_failure"] for i, k in checks.items() if i not in SEMANTIC)
uA = sum(k["A_unexplained"] for k in checks.values())
uB = sum(k["B_unexplained"] for k in checks.values())
print(f"\nverdicts outside extraction failures: A {nA}, B (gate ids) {nB}; unexplained disagreements with R: A {uA} ({100*uA/nA:.1f}%), B {uB} ({100*uB/nB:.1f}%)")
