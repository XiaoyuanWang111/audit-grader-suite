"""Step 5: aggregate panel verdicts (audit/work/panel_verdicts/*.jsonl).

Writes audit/work/panel_tables.md and audit/work/panel_stats.json:
- scored coverage per grader (verdicts that are not exceptions)
- pass rate per check for grader strict/loose, reference strict/loose, replacement
- disagreements per check (grader vs replacement, grader vs reference)
- prompt-level and instruction-level accuracy per configuration and run, with the change
  replacement - grader, and rerun differences (greedy vs greedy_repeat / bi_greedy /
  greedy_shuffled) for comparison
- extraction failures and truncated responses
Use --heldout-only / --exclude-heldout to restrict the population.
"""
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELD = {l.strip().replace(".jsonl", "") for l in open(os.path.join(W, "audit", "frozen", "heldout_runs.txt"))}

rows = []
for p in sorted(glob.glob(os.path.join(W, "audit", "work", "panel_verdicts", "*.jsonl"))):
    for line in open(p, encoding="utf-8"):
        if line.strip():
            rows.append(json.loads(line))
tag = "all"
if "--heldout-only" in sys.argv:
    rows = [r for r in rows if f"{r['cfg']}/{r['run']}" in HELD]
    tag = "heldout"
elif "--exclude-heldout" in sys.argv:
    rows = [r for r in rows if f"{r['cfg']}/{r['run']}" not in HELD]
    tag = "exclude_heldout"

G = ["gs", "gl", "rs", "rl", "ps"]
NAMES = {"gs": "grader strict", "gl": "grader loose", "rs": "reference strict", "rl": "reference loose",
         "ps": "replacement"}
out = {"population": tag, "instances": len(rows)}

# coverage
out["coverage"] = {g: sum(1 for r in rows if r[g] != -1) / len(rows) for g in G}
out["exceptions"] = {g: sum(1 for r in rows if r[g] == -1) for g in G}

# per check pass rates and disagreements
by_check = defaultdict(list)
for r in rows:
    by_check[r["iid"]].append(r)
check_tab = {}
for iid, rs_ in sorted(by_check.items()):
    n = len(rs_)
    d = {"n": n}
    for g in G:
        d[g] = sum(1 for r in rs_ if r[g] == 1) / n
    d["g1_p0"] = sum(1 for r in rs_ if r["gs"] == 1 and r["ps"] == 0)
    d["g0_p1"] = sum(1 for r in rs_ if r["gs"] == 0 and r["ps"] == 1)
    d["g1_r0"] = sum(1 for r in rs_ if r["gs"] == 1 and r["rs"] == 0)
    d["g0_r1"] = sum(1 for r in rs_ if r["gs"] == 0 and r["rs"] == 1)
    d["loose_only"] = sum(1 for r in rs_ if r["gl"] == 1 and r["gs"] == 0)
    d["loose_only_rep_fail"] = sum(1 for r in rs_ if r["gl"] == 1 and r["gs"] == 0 and r["ps"] == 0)
    check_tab[iid] = d
out["checks"] = check_tab
tot = len(rows)
out["disagree"] = {
    "grader_vs_replacement": sum(1 for r in rows if r["gs"] != r["ps"]),
    "grader_pass_replacement_fail": sum(1 for r in rows if r["gs"] == 1 and r["ps"] == 0),
    "grader_fail_replacement_pass": sum(1 for r in rows if r["gs"] == 0 and r["ps"] == 1),
    "grader_vs_reference": sum(1 for r in rows if r["gs"] != r["rs"]),
    "grader_pass_reference_fail": sum(1 for r in rows if r["gs"] == 1 and r["rs"] == 0),
    "grader_fail_reference_pass": sum(1 for r in rows if r["gs"] == 0 and r["rs"] == 1),
    "reference_vs_replacement": sum(1 for r in rows if r["rs"] != r["ps"]),
    "loose_pass_strict_fail": sum(1 for r in rows if r["gl"] == 1 and r["gs"] == 0),
    "loose_pass_strict_fail_replacement_fail": sum(1 for r in rows if r["gl"] == 1 and r["gs"] == 0 and r["ps"] == 0),
    "grader_passes": sum(1 for r in rows if r["gs"] == 1),
    "total": tot,
}

# per run accuracies
by_run = defaultdict(lambda: defaultdict(list))
for r in rows:
    by_run[(r["cfg"], r["run"])][r["key"]].append(r)
run_tab = {}
for (cfg, run), prompts in sorted(by_run.items()):
    d = {"prompts": len(prompts)}
    for g in G:
        d["prompt_" + g] = sum(1 for k, lst in prompts.items() if all(x[g] == 1 for x in lst)) / len(prompts)
        inst = [x for lst in prompts.values() for x in lst]
        d["inst_" + g] = sum(1 for x in inst if x[g] == 1) / len(inst)
    run_tab[f"{cfg}/{run}"] = d
out["runs"] = run_tab

# per configuration summary
cfgs = sorted({k.split("/")[0] for k in run_tab})
cfg_tab = {}
for c in cfgs:
    runs = {k.split("/")[1]: v for k, v in run_tab.items() if k.split("/")[0] == c}
    d = {"n_runs": len(runs)}
    for g in G:
        vals = [v["prompt_" + g] for v in runs.values()]
        d["mean_prompt_" + g] = statistics.mean(vals)
    d["delta_prompt_ps_gs"] = d["mean_prompt_ps"] - d["mean_prompt_gs"]
    d["delta_prompt_rs_gs"] = d["mean_prompt_rs"] - d["mean_prompt_gs"]
    if "greedy" in runs:
        d["greedy_prompt_gs"] = runs["greedy"]["prompt_gs"]
        d["greedy_prompt_ps"] = runs["greedy"]["prompt_ps"]
        d["greedy_delta_ps_gs"] = runs["greedy"]["prompt_ps"] - runs["greedy"]["prompt_gs"]
        for other in ["greedy_repeat", "greedy_shuffled", "bi_greedy", "bi_greedy_shuffled"]:
            if other in runs:
                d["rerun_" + other + "_gs"] = runs[other]["prompt_gs"] - runs["greedy"]["prompt_gs"]
    samples = [v["prompt_gs"] for k, v in runs.items() if k.startswith("sample")]
    if len(samples) >= 2:
        d["sample_sd_gs"] = statistics.stdev(samples)
        d["sample_sd_delta"] = statistics.stdev([runs[k]["prompt_ps"] - runs[k]["prompt_gs"] for k in runs if k.startswith("sample")])
    cfg_tab[c] = d
out["configs"] = cfg_tab

# extraction failures and truncation
def rate(sub, g):
    return (sum(1 for r in sub if r[g] == 1) / len(sub)) if sub else None
xf = [r for r in rows if r["xfail"]]
tr = [r for r in rows if r["finish"] == "length"]
out["extraction_failures"] = {"instances": len(xf), "responses": len({(r["cfg"], r["run"], r["key"]) for r in xf}),
                              "grader_pass_rate": rate(xf, "gs"), "reference_pass_rate": rate(xf, "rs"),
                              "grader_passes": sum(1 for r in xf if r["gs"] == 1)}
out["truncated"] = {"instances": len(tr), "responses": len({(r["cfg"], r["run"], r["key"]) for r in tr}),
                    "grader_pass_rate": rate(tr, "gs"), "replacement_pass_rate": rate(tr, "ps"),
                    "untruncated_grader_pass_rate": rate([r for r in rows if r["finish"] != "length"], "gs")}

json.dump(out, open(os.path.join(W, "audit", "work", f"panel_stats_{tag}.json"), "w"), indent=1)

# markdown tables
L = [f"# Panel tables ({tag}; {len(rows)} instruction instances)", ""]
L.append("Coverage (share with a verdict): " + ", ".join(f"{NAMES[g]} {out['coverage'][g]:.4%}" for g in G))
L.append("")
L.append("| configuration | runs | grader strict | replacement | change | reference strict | grader loose | greedy change | rerun diffs (greedy_repeat / shuffled / bi) | sample SD |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for c, d in cfg_tab.items():
    rr = " / ".join(f"{d.get('rerun_' + o + '_gs', float('nan')) * 100:+.1f}" for o in ["greedy_repeat", "greedy_shuffled", "bi_greedy"])
    sd = f"{d['sample_sd_gs'] * 100:.1f}" if "sample_sd_gs" in d else "-"
    L.append(f"| {c} | {d['n_runs']} | {d['mean_prompt_gs'] * 100:.1f} | {d['mean_prompt_ps'] * 100:.1f} | "
             f"{d['delta_prompt_ps_gs'] * 100:+.1f} | {d['mean_prompt_rs'] * 100:.1f} | {d['mean_prompt_gl'] * 100:.1f} | "
             f"{d.get('greedy_delta_ps_gs', float('nan')) * 100:+.1f} | {rr} | {sd} |")
L.append("")
L.append("| check | n | grader | replacement | reference | grader loose | grader pass, repl. fail | grader fail, repl. pass | grader vs ref |")
L.append("|---|---|---|---|---|---|---|---|---|")
for iid, d in check_tab.items():
    L.append(f"| {iid} | {d['n']} | {d['gs'] * 100:.1f} | {d['ps'] * 100:.1f} | {d['rs'] * 100:.1f} | {d['gl'] * 100:.1f} | "
             f"{d['g1_p0']} | {d['g0_p1']} | {d['g1_r0'] + d['g0_r1']} |")
open(os.path.join(W, "audit", "work", f"panel_tables_{tag}.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print(json.dumps({k: out[k] for k in ["population", "instances", "coverage", "exceptions", "disagree",
                                       "extraction_failures", "truncated"]}, indent=1))
