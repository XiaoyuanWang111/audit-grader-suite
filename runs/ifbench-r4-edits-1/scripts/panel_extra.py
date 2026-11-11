"""Step 5 extras over audit/work/panel/*.jsonl:

- pooled scores per grader (prompt- and instruction-level, strict and loose)
- attribution of grader/replacement disagreements: "decision" when some
  measured alternative reading gives the grader's verdict, else "finding or
  replacement error" (the blinded review would settle the latter)
- configuration ranking under grader vs replacement (Kendall tau, swaps)
- held-out-only disagreement rates
Writes audit/work/panel_extra.json.
"""
import collections
import itertools
import json
import statistics

import common

P = common.W / "audit" / "work" / "panel"
summ = json.load(open(common.W / "audit" / "work" / "panel_summary.json", encoding="utf-8"))


def held_out(folder, run):
    return run == "sample7" or (folder.endswith("__thinking") and run == "greedy_repeat")


pooled = collections.Counter()
attr = collections.defaultdict(collections.Counter)
attr_ho = collections.Counter()
xf_pass = collections.Counter()
for f in sorted(P.glob("*.jsonl")):
    folder, run = f.stem.rsplit("__", 1)
    ho = held_out(folder, run)
    for line in f.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        pooled["prompts"] += 1
        for g in ("gs", "gl", "rs", "rl", "rep"):
            pooled[g + "_prompt"] += all(c[g] is True for c in e["checks"])
        for c in e["checks"]:
            pooled["checks"] += 1
            for g in ("gs", "gl", "rs", "rl", "rep"):
                pooled[g + "_instr"] += c[g] is True
            gsv, rep = c["gs"] is True, c["rep"] is True
            if gsv == rep:
                continue
            kind = "grader_pass" if gsv else "grader_fail"
            if e["extraction_failure"]:
                cat = "extraction_failure"
            else:
                agree = [a for a, v in c.get("alts", {}).items() if (v is True) == gsv]
                cat = "decision" if agree else "finding_or_replacement"
            attr[c["check"]][f"{kind}:{cat}"] += 1
            attr["ALL"][f"{kind}:{cat}"] += 1
            if ho:
                attr_ho[f"{kind}:{cat}"] += 1
out = {"pooled": {k: (v / pooled["prompts"] if k.endswith("_prompt") else v / pooled["checks"] if k.endswith("_instr") else v)
                  for k, v in pooled.items()},
       "attribution": {k: dict(v) for k, v in sorted(attr.items())}, "attribution_held_out": dict(attr_ho)}

pc = summ["per_config"]
cfgs = sorted(pc)
g = {c: pc[c]["gs"]["prompt_mean"] for c in cfgs}
r = {c: pc[c]["rep"]["prompt_mean"] for c in cfgs}
conc = disc = 0
swaps = []
for a, b in itertools.combinations(cfgs, 2):
    s = (g[a] - g[b]) * (r[a] - r[b])
    if s > 0:
        conc += 1
    elif s < 0:
        disc += 1
        swaps.append((a, b, round(g[a] - g[b], 3), round(r[a] - r[b], 3)))
out["kendall_tau"] = (conc - disc) / (conc + disc)
out["rank_swaps"] = swaps
out["rank_grader"] = sorted(cfgs, key=lambda c: -g[c])
out["rank_replacement"] = sorted(cfgs, key=lambda c: -r[c])
# score change vs noise
noise = []
for c in cfgs:
    d = pc[c]
    noise.append(dict(config=c, delta=d["delta_prompt_rep_minus_gs"], rerun_gs=d["rerun_diff_gs"], rerun_rep=d["rerun_diff_rep"],
                      sd_runs_gs=d["gs"]["prompt_sd"], runs=d["runs"],
                      se_mean_gs=d["gs"]["prompt_sd"] / max(1, d["runs"] - 1) ** 0.5))
out["delta_vs_noise"] = noise
(common.W / "audit" / "work" / "panel_extra.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
print("pooled", {k: round(v, 4) if isinstance(v, float) else v for k, v in out["pooled"].items()})
print("attribution ALL", out["attribution"]["ALL"])
print("attribution held-out", out["attribution_held_out"])
print("kendall tau", round(out["kendall_tau"], 3), "swaps", len(swaps))
for s in swaps:
    print("  ", s)
print("rank grader     ", [c.split("__")[1] if "__" in c else c for c in out["rank_grader"]])
print("rank replacement", [c.split("__")[1] if "__" in c else c for c in out["rank_replacement"]])
big = [n for n in noise if abs(n["delta"]) > max(abs(n["rerun_gs"]), abs(n["rerun_rep"]), 2 * n["sd_runs_gs"])]
print("configs whose |delta| exceeds both rerun diffs and 2x run SD:", len(big), [b["config"] for b in big])
print("\nper-check attribution (finding_or_replacement counts)")
for k, v in out["attribution"].items():
    fr = v.get("grader_pass:finding_or_replacement", 0) + v.get("grader_fail:finding_or_replacement", 0)
    dc = v.get("grader_pass:decision", 0) + v.get("grader_fail:decision", 0)
    if fr or dc:
        print(f"  {k:<34} finding/repl {fr:>5}  decision {dc:>5}  extraction {v.get('grader_pass:extraction_failure', 0):>3}")
