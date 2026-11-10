"""Step 5 analysis of audit/work/panel_verdicts.jsonl.

Prints the tables used in ISSUE.md and AUDIT.md and writes audit/work/panel_summary.json.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/analyze_panel.py
"""
import collections
import json
import os
import statistics
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(W, "audit", "work", "panel_verdicts.jsonl")
rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
N = len(rows)
out = {"rows": N}
print(f"rows {N}")

# ---- coverage and exceptions
cov = {}
for k in ("g", "gl", "r", "rl", "p"):
    cov[k] = sum(1 for r in rows if r[k] is not None) / N
errs = collections.Counter()
for r in rows:
    for who, msg in r["err"].items():
        errs[(who, r["iid"], msg[:70])] += 1
out["coverage"] = cov
out["errors"] = {f"{a}|{b}|{c}": n for (a, b, c), n in errs.items()}
print("coverage", {k: round(v, 5) for k, v in cov.items()})
for (who, iid, msg), n in errs.most_common():
    print(f"  error {who} {iid} x{n}: {msg}")

# ---- per-check pass rates and disagreements
per = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    c = per[r["iid"]]
    c["n"] += 1
    for k in ("g", "gl", "r", "rl", "p"):
        c[k] += bool(r[k])
    c["g!=r"] += (r["g"] != r["r"])
    c["g1p0"] += bool(r["g"]) and not r["p"]
    c["g0p1"] += (not r["g"]) and bool(r["p"])
    c["gl_only"] += (not r["g"]) and bool(r["gl"])
    c["gl_only_p0"] += (not r["g"]) and bool(r["gl"]) and not r["p"]
out["per_check"] = {k: dict(v) for k, v in sorted(per.items())}
print("\nper check: n, pass% grader strict / loose / reference strict / replacement; disagreements grader-ref, grader1-rep0, grader0-rep1")
for iid, c in sorted(per.items()):
    n = c["n"]
    print(f"  {iid:34s} n={n:5d} g={c['g'] / n:6.1%} gl={c['gl'] / n:6.1%} r={c['r'] / n:6.1%} p={c['p'] / n:6.1%}"
          f"  g!=r={c['g!=r']:5d} g1p0={c['g1p0']:5d} g0p1={c['g0p1']:5d} looseonly={c['gl_only']:4d} (rep fails {c['gl_only_p0']})")
tot = collections.Counter()
for c in per.values():
    tot.update(c)
print(f"  TOTAL n={N} g={tot['g'] / N:.4f} gl={tot['gl'] / N:.4f} r={tot['r'] / N:.4f} p={tot['p'] / N:.4f} "
      f"g!=r={tot['g!=r']} g1p0={tot['g1p0']} g0p1={tot['g0p1']} loose-only={tot['gl_only']} (rep fails {tot['gl_only_p0']})")
out["totals"] = dict(tot)

# ---- extraction failures and truncation
ef = [r for r in rows if r["extraction_failure"]]
out["extraction_failures"] = {"instructions": len(ef), "grader_pass": sum(bool(r["g"]) for r in ef),
                              "grader_loose_pass": sum(bool(r["gl"]) for r in ef), "reference_pass": sum(bool(r["r"]) for r in ef)}
print("\nextraction failures (instructions):", out["extraction_failures"])
tr = [r for r in rows if r["finish"] == "length"]
out["truncated"] = {"instructions": len(tr), "grader_pass": sum(bool(r["g"]) for r in tr), "replacement_pass": sum(bool(r["p"]) for r in tr)}
print("truncated (instructions):", out["truncated"])

# ---- loose winners
lw = collections.Counter()
for r in rows:
    if not r["g"] and r["gl"]:
        lw[(r["glw"], bool(r["p"]))] += 1
names = ["response", "no asterisks", "no first line", "no last line", "no first+last", "no first, no *", "no last, no *", "no first+last, no *"]
out["loose_winners"] = {f"{names[w]}|rep_pass={pp}": n for (w, pp), n in sorted(lw.items())}
print("\nloose-only passes by winning variant (and whether the contract passes the full response):")
for (w, pp), n in sorted(lw.items()):
    print(f"  {names[w]:22s} replacement pass={pp}: {n}")

# ---- decision effects: verdicts the switch flips, and grader/replacement disagreements a single switch explains
flip = collections.Counter()
explain = collections.Counter()
dis = [r for r in rows if r["g"] is not None and r["p"] is not None and bool(r["g"]) != bool(r["p"])]
for r in rows:
    for a, v in r["alt"].items():
        if r["p"] is not None and v != r["p"]:
            flip[a] += 1
explained = 0
expl_by_check = collections.Counter()
for r in dis:
    hits = [a for a, v in r["alt"].items() if v == bool(r["g"])]
    if hits:
        explained += 1
        expl_by_check[r["iid"]] += 1
        for a in hits:
            explain[a] += 1
out["decision_flips"] = dict(flip)
out["decision_explains"] = dict(explain)
out["disagreements"] = {"total": len(dis), "explained_by_one_switch": explained,
                        "by_check_unexplained": {k: per[k]["g1p0"] + per[k]["g0p1"] - expl_by_check[k] for k in per}}
print(f"\ngrader vs replacement disagreements: {len(dis)}; explained by one decision switch: {explained}")
print("decision switch: verdicts flipped vs proposed / disagreements it explains")
for a in sorted(flip, key=lambda x: -flip[x]):
    print(f"  {a:24s} flips {flip[a]:6d}  explains {explain[a]:6d}")

# ---- scores per configuration
by_run = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by_run[(r["cfg"], r["run"])][r["key"]].append(r)


def scores(recs_by_key, k):
    inst = [bool(x[k]) for xs in recs_by_key.values() for x in xs]
    prom = [all(bool(x[k]) for x in xs) for xs in recs_by_key.values()]
    return sum(prom) / len(prom), sum(inst) / len(inst)


cfg_runs = collections.defaultdict(dict)
for (cfg, run), d in by_run.items():
    cfg_runs[cfg][run] = {k: scores(d, k) for k in ("g", "gl", "r", "rl", "p")}
out["scores"] = {c: v for c, v in cfg_runs.items()}
print("\nprompt-level strict accuracy per configuration (mean over runs): grader, reference, replacement, replacement-grader;"
      " rerun |greedy - greedy_repeat| grader; sd over sample runs (grader)")
summary = {}
for cfg in sorted(cfg_runs):
    runs = cfg_runs[cfg]
    m = {k: statistics.mean(v[k][0] for v in runs.values()) for k in ("g", "gl", "r", "p")}
    mi = {k: statistics.mean(v[k][1] for v in runs.values()) for k in ("g", "gl", "r", "p")}
    rerun = abs(runs["greedy"]["g"][0] - runs["greedy_repeat"]["g"][0]) if "greedy_repeat" in runs else None
    rerun_p = abs(runs["greedy"]["p"][0] - runs["greedy_repeat"]["p"][0]) if "greedy_repeat" in runs else None
    samp = [v["g"][0] for r, v in runs.items() if r.startswith("sample")]
    sd = statistics.stdev(samp) if len(samp) > 1 else None
    deltas = [v["p"][0] - v["g"][0] for v in runs.values()]
    summary[cfg] = {"runs": len(runs), "prompt": m, "instr": mi, "rerun_diff_g": rerun, "rerun_diff_p": rerun_p,
                    "sample_sd_g": sd, "delta_prompt_mean": statistics.mean(deltas),
                    "delta_prompt_min": min(deltas), "delta_prompt_max": max(deltas)}
    print(f"  {cfg:44s} runs={len(runs):2d} g={m['g']:.3f} gl={m['gl']:.3f} r={m['r']:.3f} p={m['p']:.3f} "
          f"d(p-g)={m['p'] - m['g']:+.3f} [{min(deltas):+.3f},{max(deltas):+.3f}]  rerun={rerun if rerun is None else round(rerun, 3)} "
          f"sd={sd if sd is None else round(sd, 3)} | instr g={mi['g']:.3f} p={mi['p']:.3f} d={mi['p'] - mi['g']:+.3f}")
out["config_summary"] = summary
# ranking change
rank_g = sorted(summary, key=lambda c: -summary[c]["prompt"]["g"])
rank_p = sorted(summary, key=lambda c: -summary[c]["prompt"]["p"])
out["ranking"] = {"grader": rank_g, "replacement": rank_p}
print("\nranking by grader:      ", [c.split("__")[1] if "__" in c else c for c in rank_g])
print("ranking by replacement: ", [c.split("__")[1] if "__" in c else c for c in rank_p])

with open(os.path.join(W, "audit", "work", "panel_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
print("\nwrote audit/work/panel_summary.json")
