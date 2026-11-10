"""Aggregate the panel verdicts (step 5).

Reads audit/frozen/panel_verdicts/<cfg>/<run>.jsonl and writes:
  audit/frozen/panel_summary.json   all numbers below, machine-readable
  audit/panel_tables.md             the tables the report uses
Prints the headline numbers.
"""
import json
import math
import os
import statistics
from collections import Counter, defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VD = os.path.join(W, "audit", "frozen", "panel_verdicts")
GRADERS = ["G", "GL", "R", "RL", "X", "XP"]
VARIANT_NAMES = ["as is", "* removed", "first line removed", "last line removed", "first+last removed",
                 "* removed, first line removed", "* removed, last line removed", "* removed, first+last removed"]


def load():
    data = {}
    for cfg in sorted(os.listdir(VD)):
        for fn in sorted(os.listdir(os.path.join(VD, cfg))):
            if fn.endswith(".jsonl"):
                data[(cfg, fn[:-6])] = [json.loads(l) for l in open(os.path.join(VD, cfg, fn), encoding="utf-8")]
    return data


def ok(v):
    return v is True


def scores(recs, key, sw=None):
    """prompt-level and instruction-level accuracy for one run under grader key."""
    p = i = n_i = 0
    for rec in recs:
        vs = []
        for ins in rec["inst"]:
            v = ins[key] if sw is None else ins["XS"].get(sw, ins["X"])
            vs.append(ok(v))
        p += all(vs)
        i += sum(vs)
        n_i += len(vs)
    return 100 * p / len(recs), 100 * i / n_i


def main():
    data = load()
    out = {}
    cfgs = sorted({c for c, _ in data})
    # ---- coverage and exceptions ----
    exc = Counter()
    total_inst = 0
    for recs in data.values():
        for rec in recs:
            for ins in rec["inst"]:
                total_inst += 1
                for g in GRADERS:
                    if isinstance(ins[g], str):
                        exc[(g, ins["id"], ins[g])] += 1
                for s, v in ins["XS"].items():
                    if isinstance(v, str):
                        exc[("XS:" + s, ins["id"], v)] += 1
    out["instances"] = total_inst
    out["exceptions"] = {f"{g}|{i}|{e}": c for (g, i, e), c in exc.items()}
    # ---- per check ----
    per = defaultdict(lambda: Counter())
    for (cfg, run), recs in data.items():
        for rec in recs:
            for ins in rec["inst"]:
                c = per[ins["id"]]
                c["n"] += 1
                for g in GRADERS:
                    c[g] += ok(ins[g])
                c["G!=R"] += ok(ins["G"]) != ok(ins["R"])
                c["G>R"] += ok(ins["G"]) and not ok(ins["R"])
                c["G!=X"] += ok(ins["G"]) != ok(ins["X"])
                c["G>X"] += ok(ins["G"]) and not ok(ins["X"])
                c["G<X"] += (not ok(ins["G"])) and ok(ins["X"])
                c["G!=XP"] += ok(ins["G"]) != ok(ins["XP"])
                c["GL>G"] += ok(ins["GL"]) and not ok(ins["G"])
                c["GL>G,X0"] += ok(ins["GL"]) and not ok(ins["G"]) and not ok(ins["X"])
                if rec["xf"]:
                    c["xf"] += 1
                    c["xf_Gpass"] += ok(ins["G"])
    out["per_check"] = {k: dict(v) for k, v in per.items()}
    # ---- per configuration scores ----
    table = {}
    for cfg in cfgs:
        runs = sorted(r for c, r in data if c == cfg)
        row = {}
        for g in GRADERS:
            ps = [scores(data[(cfg, r)], g)[0] for r in runs]
            ins = [scores(data[(cfg, r)], g)[1] for r in runs]
            row[g] = (statistics.mean(ps), statistics.mean(ins))
            row[g + "_greedy"] = scores(data[(cfg, "greedy")], g)
        samples = [r for r in runs if r.startswith("sample")]
        row["n_runs"] = len(runs)
        row["sample_sd_G_prompt"] = statistics.stdev([scores(data[(cfg, r)], "G")[0] for r in samples]) if len(samples) > 1 else None
        g0 = scores(data[(cfg, "greedy")], "G")[0]
        g1 = scores(data[(cfg, "greedy_repeat")], "G")[0]
        row["rerun_diff_G_prompt"] = g1 - g0
        if (cfg, "bi_greedy") in data:
            row["bi_diff_G_prompt"] = scores(data[(cfg, "bi_greedy")], "G")[0] - g0
        # paired per-run change X-G (prompt level), mean and min/max across runs
        d = [scores(data[(cfg, r)], "X")[0] - scores(data[(cfg, r)], "G")[0] for r in runs]
        row["XminusG_runs"] = (statistics.mean(d), min(d), max(d))
        dr = [scores(data[(cfg, r)], "R")[0] - scores(data[(cfg, r)], "G")[0] for r in runs]
        row["RminusG_runs"] = (statistics.mean(dr), min(dr), max(dr))
        dp = [scores(data[(cfg, r)], "XP")[0] - scores(data[(cfg, r)], "G")[0] for r in runs]
        row["XPminusG_runs"] = (statistics.mean(dp), min(dp), max(dp))
        table[cfg] = row
    out["per_config"] = table
    # rank changes
    def rank(key):
        order = sorted(cfgs, key=lambda c: -table[c][key][0])
        return {c: i + 1 for i, c in enumerate(order)}
    out["rank"] = {g: rank(g) for g in GRADERS}
    # ---- decisions: effect of each switch on overall accuracy (X baseline) ----
    sws = sorted({s for recs in data.values() for rec in recs for ins in rec["inst"] for s in ins["XS"]})
    dec = {}
    allrecs = [rec for recs in data.values() for rec in recs]
    base_p, base_i = scores(allrecs, "X")
    for s in sws:
        p, i = scores(allrecs, None, sw=s)
        changed = sum(1 for rec in allrecs for ins in rec["inst"] if s in ins["XS"] and ok(ins["XS"][s]) != ok(ins["X"]))
        affected = sum(1 for rec in allrecs for ins in rec["inst"] if s in ins["XS"])
        dec[s] = {"prompt_delta": p - base_p, "inst_delta": i - base_i, "verdicts_changed": changed, "instances_touched": affected}
    out["decisions"] = dec
    # ---- loose ----
    lv = Counter()
    lv_check = defaultdict(Counter)
    for rec in allrecs:
        for ins in rec["inst"]:
            if ok(ins["GL"]) and not ok(ins["G"]):
                lv[ins["GV"]] += 1
                lv_check[ins["id"]][ins["GV"]] += 1
    out["loose_rescue_by_variant"] = {VARIANT_NAMES[k]: v for k, v in sorted(lv.items())}
    out["loose_rescue_by_check"] = {k: {VARIANT_NAMES[a]: b for a, b in v.items()} for k, v in lv_check.items()}
    # ---- extraction failures and truncation ----
    xf = [rec for rec in allrecs if rec["xf"]]
    out["extraction_failures"] = {"responses": len(xf),
                                  "instances": sum(len(r["inst"]) for r in xf),
                                  "G_pass_instances": sum(ok(i["G"]) for r in xf for i in r["inst"]),
                                  "G_pass_prompts": sum(all(ok(i["G"]) for i in r["inst"]) for r in xf),
                                  "GL_pass_instances": sum(ok(i["GL"]) for r in xf for i in r["inst"])}
    trunc = [rec for rec in allrecs if rec["fin"] == "length"]
    out["truncated"] = {"responses": len(trunc), "G_prompt_pass": sum(all(ok(i["G"]) for i in r["inst"]) for r in trunc)}
    # overall
    out["overall"] = {g: scores(allrecs, g) for g in GRADERS}
    with open(os.path.join(W, "audit", "frozen", "panel_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    write_tables(out, cfgs)
    print("instances", total_inst, "exceptions", sum(exc.values()))
    print("overall", {g: tuple(round(x, 2) for x in v) for g, v in out["overall"].items()})
    print("extraction failures", out["extraction_failures"])
    print("loose rescue", out["loose_rescue_by_variant"])


def write_tables(out, cfgs):
    L = []
    L.append("## Per-configuration scores (mean over the configuration's runs; strict prompt-level accuracy, %)\n")
    L.append("| Configuration | Runs | G | R | X (as-is) | XP (proposed) | X-G mean [min, max over runs] | R-G mean | XP-G mean | G loose | greedy_repeat - greedy (G) | bi_greedy - greedy (G) | SD over sample runs (G) | Rank G -> X |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in cfgs:
        r = out["per_config"][c]
        xg = r["XminusG_runs"]
        sd = r["sample_sd_G_prompt"]
        L.append(f"| {c} | {r['n_runs']} | {r['G'][0]:.2f} | {r['R'][0]:.2f} | {r['X'][0]:.2f} | {r['XP'][0]:.2f} | "
                 f"{xg[0]:+.2f} [{xg[1]:+.2f}, {xg[2]:+.2f}] | {r['RminusG_runs'][0]:+.2f} | {r['XPminusG_runs'][0]:+.2f} | "
                 f"{r['GL'][0]:.2f} | {r['rerun_diff_G_prompt']:+.2f} | "
                 f"{(('%+.2f' % r['bi_diff_G_prompt']) if 'bi_diff_G_prompt' in r else 'n/a')} | "
                 f"{('%.2f' % sd) if sd is not None else 'n/a'} | {out['rank']['G'][c]} -> {out['rank']['X'][c]} |")
    L.append("\n## Per-configuration instruction-level accuracy (%, mean over runs)\n")
    L.append("| Configuration | G | R | X | XP | G loose |")
    L.append("|---|---|---|---|---|---|")
    for c in cfgs:
        r = out["per_config"][c]
        L.append(f"| {c} | {r['G'][1]:.2f} | {r['R'][1]:.2f} | {r['X'][1]:.2f} | {r['XP'][1]:.2f} | {r['GL'][1]:.2f} |")
    L.append("\n## Per-check verdicts over all 78,432 instruction instances\n")
    L.append("| Check | n | G pass % | R pass % | X pass % | XP pass % | G!=R | G!=X | G pass, X fail | G fail, X pass | G loose rescues |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for k in sorted(out["per_check"]):
        c = out["per_check"][k]
        n = c["n"]
        L.append(f"| {k} | {n} | {100*c['G']/n:.1f} | {100*c['R']/n:.1f} | {100*c['X']/n:.1f} | {100*c['XP']/n:.1f} | "
                 f"{c['G!=R']} | {c['G!=X']} | {c['G>X']} | {c['G<X']} | {c['GL>G']} |")
    L.append("\n## Decision switches (X with one decision at its proposed reading, against X as-is, all 68,400 responses)\n")
    L.append("| Decision | Instances touched | Verdicts changed | Prompt-level change (points) | Instruction-level change (points) |")
    L.append("|---|---|---|---|---|")
    for s, d in sorted(out["decisions"].items()):
        L.append(f"| {s} | {d['instances_touched']} | {d['verdicts_changed']} | {d['prompt_delta']:+.3f} | {d['inst_delta']:+.3f} |")
    with open(os.path.join(W, "audit", "panel_tables.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
