"""Step 5 analysis of audit/work/panel/*.tsv (written by run_panel.py).

Writes audit/work/panel_summary.json and prints the tables used in AUDIT.md.
Held-out responses (set aside on 2026-11-10, see ISSUE.md): run sample7 of every configuration
that has sampled runs, and greedy_repeat of the two thinking configurations.
"""
import collections
import glob
import json
import os
import statistics

W = "<W>"
COLS = ["config", "run", "key", "idx", "iid", "finish", "ntok", "think_closed", "extraction_failure", "aligned",
        "empty", "gs", "gl", "rs", "rl", "rep", "alts"]
GR = ["gs", "gl", "rs", "rl", "rep"]


def heldout(cfg, run):
    return run == "sample7" or (cfg.endswith("__thinking") and run == "greedy_repeat")


rows = []
for path in sorted(glob.glob(W + "/audit/work/panel/*.tsv")):
    for line in open(path, encoding="utf-8"):
        c = dict(zip(COLS, line.rstrip("\n").split("\t")))
        c["alts"] = json.loads(c["alts"])
        rows.append(c)
gr = {}
for line in open(W + "/audit/work/panel_rep_gr.tsv", encoding="utf-8"):
    c = line.rstrip("\n").split("\t")
    gr[tuple(c[:4])] = c[4]
for r in rows:
    r["repgr"] = gr[(r["config"], r["run"], r["key"], r["idx"])]
GR.append("repgr")
print("rows", len(rows))

S = {}
# ---- record-level counts (per response, idx 0 only)
resp = [r for r in rows if r["idx"] == "0"]
by_cfg = collections.defaultdict(list)
for r in resp:
    by_cfg[r["config"]].append(r)
rec = {}
for cfg, rs in sorted(by_cfg.items()):
    rec[cfg] = dict(responses=len(rs), truncated=sum(r["finish"] == "length" for r in rs),
                    extraction_failures=sum(r["extraction_failure"] == "1" for r in rs),
                    think_tag_in_nonthinking=0 if cfg.endswith("__thinking") else sum(r["think_closed"] == "1" for r in rs),
                    empty=sum(r["empty"] == "1" for r in rs))
S["records"] = rec
print("\n== stored records: truncated (finish_reason=length), extraction failures, empty responses")
for cfg, d in rec.items():
    print(f"  {cfg:45s} n={d['responses']:5d} trunc={d['truncated']:4d} extr_fail={d['extraction_failures']:4d} "
          f"</think>_in_nonthinking={d['think_tag_in_nonthinking']} empty={d['empty']}")

# ---- errors / coverage
err = {g: sum(1 for r in rows if r[g].startswith("ERR")) for g in GR}
S["errors"] = err
S["coverage"] = {g: 1 - err[g] / len(rows) for g in GR}
print("\n== grader exceptions per grader (of", len(rows), "verdicts):", err)


def val(x):
    return x == "1"


# ---- scores per (config, run)
def scores(rs, g):
    by_prompt = collections.defaultdict(list)
    for r in rs:
        by_prompt[(r["config"], r["run"], r["key"])].append(val(r[g]))
    prompt = statistics.mean(all(v) for v in by_prompt.values())
    inst = statistics.mean(val(r[g]) for r in rs)
    return prompt, inst


by_cr = collections.defaultdict(list)
for r in rows:
    by_cr[(r["config"], r["run"])].append(r)
per_run = {}
for (cfg, run), rs in by_cr.items():
    per_run[f"{cfg}|{run}"] = {g: scores(rs, g) for g in GR}
S["per_run"] = per_run

cfgs = sorted({r["config"] for r in rows})
table = {}
print("\n== per configuration: mean over runs of strict prompt-level accuracy (%), grader / reference / replacement; loose")
for cfg in cfgs:
    runs = sorted({run for (c, run) in by_cr if c == cfg})
    m = {g: statistics.mean(per_run[f"{cfg}|{run}"][g][0] for run in runs) for g in GR}
    mi = {g: statistics.mean(per_run[f"{cfg}|{run}"][g][1] for run in runs) for g in GR}
    g0 = per_run[f"{cfg}|greedy"]
    rep_diff = None
    if f"{cfg}|greedy_repeat" in per_run:
        rep_diff = {g: per_run[f"{cfg}|greedy_repeat"][g][0] - g0[g][0] for g in GR}
    samples = [run for run in runs if run.startswith("sample")]
    sd = {g: (statistics.stdev(per_run[f"{cfg}|{run}"][g][0] for run in samples) if len(samples) > 1 else None) for g in GR}
    table[cfg] = dict(runs=len(runs), prompt=m, inst=mi, greedy=g0, rerun_diff=rep_diff, sample_sd=sd)
    print(f"  {cfg:45s} runs={len(runs):2d} G={100*m['gs']:5.1f} R={100*m['rs']:5.1f} Rep={100*m['rep']:5.1f} "
          f"d(Rep-G)={100*(m['rep']-m['gs']):+5.1f} d(R-G)={100*(m['rs']-m['gs']):+5.1f} | loose G={100*m['gl']:5.1f} "
          f"| greedy-repeat d(G)={100*rep_diff['gs']:+.1f} | sample sd(G)={'' if sd['gs'] is None else f'{100*sd['gs']:.1f}'}"
          f" | RepGR={100*m['repgr']:5.1f} d(RepGR-G)={100*(m['repgr']-m['gs']):+5.1f} d(Rep-RepGR)={100*(m['rep']-m['repgr']):+5.1f}")
S["per_config"] = table

# ---- instruction-level and prompt-level, pooled
pooled = {g: scores(rows, g) for g in GR}
S["pooled"] = pooled
print("\n== pooled over all 228 runs: (prompt-level, instruction-level) %")
for g in GR:
    print(f"  {g}: {100*pooled[g][0]:.2f}  {100*pooled[g][1]:.2f}")

# ---- per-check pass rates and disagreements
checks = sorted({r["iid"] for r in rows})
per_check = {}
for iid in checks:
    rs = [r for r in rows if r["iid"] == iid]
    d = {"n": len(rs)}
    for g in GR:
        d[f"pass_{g}"] = sum(val(r[g]) for r in rs) / len(rs)
    d["g_pass_rep_fail"] = sum(val(r["gs"]) and not val(r["rep"]) for r in rs)
    d["g_fail_rep_pass"] = sum((not val(r["gs"])) and val(r["rep"]) for r in rs)
    d["g_pass_ref_fail"] = sum(val(r["gs"]) and not val(r["rs"]) for r in rs)
    d["g_fail_ref_pass"] = sum((not val(r["gs"])) and val(r["rs"]) for r in rs)
    d["g_pass_repgr_fail"] = sum(val(r["gs"]) and not val(r["repgr"]) for r in rs)
    d["g_fail_repgr_pass"] = sum((not val(r["gs"])) and val(r["repgr"]) for r in rs)
    d["loose_only_pass"] = sum(val(r["gl"]) and not val(r["gs"]) for r in rs)
    d["loose_only_pass_rep_fail"] = sum(val(r["gl"]) and not val(r["gs"]) and not val(r["rep"]) for r in rs)
    per_check[iid] = d
S["per_check"] = per_check
print("\n== per check: n, pass% G / R / Rep / looseG, disagreements G>Rep, G<Rep, G>R, G<R")
for iid, d in per_check.items():
    print(f"  {iid:34s} n={d['n']:5d} G={100*d['pass_gs']:5.1f} R={100*d['pass_rs']:5.1f} Rep={100*d['pass_rep']:5.1f} "
          f"L={100*d['pass_gl']:5.1f} | G>Rep {d['g_pass_rep_fail']:5d} G<Rep {d['g_fail_rep_pass']:5d} | "
          f"G>R {d['g_pass_ref_fail']:4d} G<R {d['g_fail_ref_pass']:4d} | G>RepGR {d['g_pass_repgr_fail']:4d} G<RepGR {d['g_fail_repgr_pass']:4d} | looseonly {d['loose_only_pass']:5d} (rep fail {d['loose_only_pass_rep_fail']})")

tot = {k: sum(d[k] for d in per_check.values()) for k in
       ["g_pass_rep_fail", "g_fail_rep_pass", "g_pass_repgr_fail", "g_fail_repgr_pass", "g_pass_ref_fail", "g_fail_ref_pass", "loose_only_pass", "loose_only_pass_rep_fail"]}
S["totals"] = tot
print("\n== totals", tot, "of", len(rows))

# ---- decision switches
sw = collections.defaultdict(lambda: [0, 0, 0])  # changed verdicts, n evaluated, pass delta
for r in rows:
    for k, v in r["alts"].items():
        sw[k][1] += 1
        if v != r["rep"]:
            sw[k][0] += 1
            sw[k][2] += (1 if v == "1" else -1)
S["switches"] = {k: dict(changed=v[0], evaluated=v[1], pass_delta=v[2]) for k, v in sw.items()}
print("\n== decision switches: verdicts changed by the alternative reading (of verdicts evaluated), net pass change")
for k, v in sorted(sw.items(), key=lambda kv: -kv[1][0]):
    print(f"  {k:22s} changed {v[0]:5d} of {v[1]:6d}  net pass {v[2]:+d}")

# ---- extraction failures: what the grader gives them
ef = [r for r in rows if r["extraction_failure"] == "1"]
S["extraction_failure_verdicts"] = dict(n=len(ef), grader_pass=sum(val(r["gs"]) for r in ef),
                                        reference_pass=sum(val(r["rs"]) for r in ef))
print("\n== extraction-failure verdicts (thinking, no </think>):", S["extraction_failure_verdicts"])

# ---- held-out subset scores
ho = [r for r in rows if heldout(r["config"], r["run"])]
S["heldout"] = dict(rows=len(ho), runs=sorted({f"{r['config']}|{r['run']}" for r in ho}),
                    pooled={g: scores(ho, g) for g in GR})
print("\n== held-out:", len(ho), "verdicts in", len(S["heldout"]["runs"]), "runs; pooled", S["heldout"]["pooled"])

json.dump(S, open(W + "/audit/work/panel_summary.json", "w", encoding="utf-8"), indent=1)
