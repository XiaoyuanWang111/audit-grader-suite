"""Step 5 aggregation over audit/work/panel/*.jsonl.

Prints and writes audit/work/panel_summary.json:
  - per configuration: strict prompt- and instruction-level accuracy of grader,
    reference and replacement (mean over runs, and greedy), grader loose, and
    the change replacement - grader; rerun differences (greedy vs greedy_repeat)
  - scored coverage and exceptions per grader
  - per check: pass rates and grader/replacement and grader/reference disagreements
  - extraction failures and truncation
  - effect of each alternative reading on the replacement's scores
  - the same disagreement counts on the held-out runs only
"""
import collections
import json
import statistics

import common

P = common.W / "audit" / "work" / "panel"
G = ["gs", "gl", "rs", "rl", "rep"]


def held_out(folder, run):
    return run == "sample7" or (folder.endswith("__thinking") and run == "greedy_repeat")


runs = {}
for f in sorted(P.glob("*.jsonl")):
    folder, run = f.stem.rsplit("__", 1)
    if folder.endswith("__thinking") is False and f.stem.count("__") == 2:
        folder, run = f.stem.rsplit("__", 1)
    runs[(folder, run)] = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]

summary = {}
# ---- per run scores
run_scores = {}
cov = collections.Counter()
exc = collections.Counter()
exc_runs = collections.defaultdict(set)
for (folder, run), ents in runs.items():
    sc = {}
    for g in G:
        pl = il = n_i = 0
        for e in ents:
            vs = [c[g] for c in e["checks"]]
            n_i += len(vs)
            il += sum(1 for v in vs if v is True)
            pl += all(v is True for v in vs)
            cov[(g, "expected")] += len(vs)
            cov[(g, "verdict")] += sum(1 for v in vs if v is not None)
        sc[g] = dict(prompt=pl / len(ents), instr=il / n_i)
    for e in ents:
        for g, msg in e.get("errors", {}).items():
            exc[(g, msg)] += 1
            exc_runs[g].add((folder, run))
    run_scores[(folder, run)] = sc

configs = sorted({f for f, _ in runs})
per_config = {}
for cfg in configs:
    rr = sorted(r for f, r in runs if f == cfg)
    d = {"runs": len(rr)}
    for g in G:
        vals = [run_scores[(cfg, r)][g]["prompt"] for r in rr]
        ivals = [run_scores[(cfg, r)][g]["instr"] for r in rr]
        d[g] = dict(prompt_mean=statistics.mean(vals), prompt_sd=statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                    instr_mean=statistics.mean(ivals), greedy_prompt=run_scores[(cfg, "greedy")][g]["prompt"],
                    greedy_instr=run_scores[(cfg, "greedy")][g]["instr"])
    d["delta_prompt_rep_minus_gs"] = d["rep"]["prompt_mean"] - d["gs"]["prompt_mean"]
    d["delta_instr_rep_minus_gs"] = d["rep"]["instr_mean"] - d["gs"]["instr_mean"]
    d["delta_prompt_rs_minus_gs"] = d["rs"]["prompt_mean"] - d["gs"]["prompt_mean"]
    for g in ("gs", "rep"):
        a, b = run_scores[(cfg, "greedy")][g]["prompt"], run_scores[(cfg, "greedy_repeat")][g]["prompt"]
        d[f"rerun_diff_{g}"] = b - a
        if (cfg, "bi_greedy") in run_scores:
            d[f"bi_vs_greedy_{g}"] = run_scores[(cfg, "bi_greedy")][g]["prompt"] - a
    per_config[cfg] = d
summary["per_config"] = per_config
summary["coverage"] = {g: cov[(g, "verdict")] / cov[(g, "expected")] for g in G}
summary["coverage_counts"] = {g: [cov[(g, "verdict")], cov[(g, "expected")]] for g in G}
summary["exceptions"] = [dict(grader=g, error=m, rows=n) for (g, m), n in sorted(exc.items())]
summary["runs_with_exception"] = {g: sorted("/".join(x) for x in v) for g, v in exc_runs.items()}

# ---- per check
pc = collections.defaultdict(lambda: collections.Counter())
ho = collections.defaultdict(lambda: collections.Counter())
examples = collections.defaultdict(list)
xf = collections.Counter()
trunc = collections.Counter()
for (folder, run), ents in runs.items():
    h = held_out(folder, run)
    for e in ents:
        if e["extraction_failure"]:
            xf["responses"] += 1
            for c in e["checks"]:
                xf["checks"] += 1
                xf["grader_pass"] += c["gs"] is True
                xf["reference_pass"] += c["rs"] is True
        for c in e["checks"]:
            k = pc[c["check"]]
            k["n"] += 1
            for g in G:
                k[g] += c[g] is True
            gsv, rep, rsv = c["gs"], c["rep"], c["rs"]
            if gsv is True and rep is False:
                k["gs_pass_rep_fail"] += 1
            if gsv is not True and rep is True:
                k["gs_fail_rep_pass"] += 1
            if gsv is True and rsv is not True:
                k["gs_pass_rs_fail"] += 1
            if gsv is not True and rsv is True:
                k["gs_fail_rs_pass"] += 1
            if c["gl"] is True and rep is False:
                k["gl_pass_rep_fail"] += 1
            if h:
                hk = ho[c["check"]]
                hk["n"] += 1
                hk["gs_pass_rep_fail"] += gsv is True and rep is False
                hk["gs_fail_rep_pass"] += gsv is not True and rep is True
                hk["gs"] += gsv is True
                hk["rep"] += rep is True
            if gsv is not rep and len(examples[c["check"]]) < 400 and not e["extraction_failure"]:
                examples[c["check"]].append(dict(folder=folder, run=run, key=e["key"], gs=gsv, rep=rep, rs=rsv,
                                                 alts=c.get("alts", {})))
            if e["truncated"]:
                trunc["checks"] += 1
                trunc["gs"] += gsv is True
                trunc["rep"] += rep is True
summary["per_check"] = {k: dict(v) for k, v in sorted(pc.items())}
summary["held_out_per_check"] = {k: dict(v) for k, v in sorted(ho.items())}
summary["extraction_failures"] = dict(xf)
summary["truncated"] = dict(trunc)
tot = collections.Counter()
for v in pc.values():
    tot.update(v)
summary["totals"] = dict(tot)
hot = collections.Counter()
for v in ho.values():
    hot.update(v)
summary["held_out_totals"] = dict(hot)

# ---- decision effects (replacement, all runs pooled)
eff = collections.defaultdict(lambda: [0, 0, 0])  # [instr delta, prompts flipped to pass, prompts flipped to fail]
for (folder, run), ents in runs.items():
    for e in ents:
        base_all = all(c["rep"] is True for c in e["checks"])
        alt_keys = {a for c in e["checks"] for a in c.get("alts", {})}
        for a in alt_keys:
            d = 0
            vals = []
            for c in e["checks"]:
                v = c.get("alts", {}).get(a, c["rep"])
                vals.append(v)
                d += (v is True) - (c["rep"] is True)
            eff[a][0] += d
            new_all = all(v is True for v in vals)
            eff[a][1] += (new_all and not base_all)
            eff[a][2] += (base_all and not new_all)
n_prompts = sum(len(v) for v in runs.values())
n_checks = tot["n"]
summary["decision_effects"] = {a: dict(instr_pass_delta=v[0], instr_rate_delta=v[0] / n_checks,
                                       prompts_to_pass=v[1], prompts_to_fail=v[2],
                                       prompt_rate_delta=(v[1] - v[2]) / n_prompts)
                               for a, v in sorted(eff.items(), key=lambda kv: -abs(kv[1][0]))}
summary["n_prompt_responses"] = n_prompts
summary["n_check_verdicts"] = n_checks
(common.W / "audit" / "work" / "panel_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
(common.W / "audit" / "work" / "panel_disagreement_examples.json").write_text(json.dumps(examples, indent=1), encoding="utf-8", newline="\n")

# ---- print
print(f"responses {n_prompts}, check verdicts {n_checks}")
print("coverage", {g: round(v, 6) for g, v in summary["coverage"].items()}, summary["coverage_counts"])
print("exceptions", summary["exceptions"])
print("extraction failures", dict(xf), "truncated", dict(trunc))
print("\nper configuration (strict prompt-level, mean over runs; greedy rerun diffs)")
print(f"{'config':<44}{'runs':>4} {'grader':>7} {'ref':>7} {'repl':>7} {'d(r-g)':>7} {'g_loose':>7} {'rerun_g':>8} {'rerun_r':>8} {'sd_g':>6}")
for cfg, d in per_config.items():
    print(f"{cfg:<44}{d['runs']:>4} {d['gs']['prompt_mean']:>7.3f} {d['rs']['prompt_mean']:>7.3f} {d['rep']['prompt_mean']:>7.3f} "
          f"{d['delta_prompt_rep_minus_gs']:>+7.3f} {d['gl']['prompt_mean']:>7.3f} {d['rerun_diff_gs']:>+8.3f} {d['rerun_diff_rep']:>+8.3f} {d['gs']['prompt_sd']:>6.3f}")
print("\nper check: n, pass rates grader/ref/repl, grader-pass&repl-fail, grader-fail&repl-pass, grader!=ref")
for k, v in summary["per_check"].items():
    n = v["n"]
    print(f"{k:<34}{n:>6} {v.get('gs', 0) / n:>6.3f} {v.get('rs', 0) / n:>6.3f} {v.get('rep', 0) / n:>6.3f} "
          f"{v.get('gs_pass_rep_fail', 0):>6} {v.get('gs_fail_rep_pass', 0):>6} {v.get('gs_pass_rs_fail', 0) + v.get('gs_fail_rs_pass', 0):>6}")
print("totals", {k: summary["totals"].get(k) for k in ("n", "gs", "rs", "rep", "gs_pass_rep_fail", "gs_fail_rep_pass", "gs_pass_rs_fail", "gs_fail_rs_pass", "gl_pass_rep_fail")})
print("held-out totals", summary["held_out_totals"])
print("\ndecision effects (replacement, alt - proposed), top 30 by |instr delta|")
for a, v in list(summary["decision_effects"].items())[:30]:
    print(f"  {a:<34} instr {v['instr_pass_delta']:>+6} ({v['instr_rate_delta']:+.4f})  prompts +{v['prompts_to_pass']} -{v['prompts_to_fail']} ({v['prompt_rate_delta']:+.4f})")
