"""Analyse panel verdicts (audit/out/panel/*.tsv) and the stored run records.

Prints and writes:
  audit/out/panel_records.tsv     per configuration: truncation, unclosed thinking, trailing whitespace
  audit/out/panel_scores.tsv      per configuration and grader: strict prompt / instruction accuracy (mean over runs)
  audit/out/panel_checks.tsv      per check: pass rates per grader, disagreement counts
  audit/out/panel_loose.tsv       per check: loose-only passes and how many the contract (replacement FIX) fails
  audit/out/panel_summary.json    headline numbers
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parents[2]
PANEL = W / "case" / "panel"
OUT = W / "audit" / "out"
COLS = ["g_strict", "g_loose", "r_strict", "r_loose", "x_fix", "x_prop"]


def load():
    recs = []
    for f in sorted((OUT / "panel").glob("*.tsv")):
        with open(f, encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                recs.append(dict(zip(header, parts)))
    return recs


def records_summary():
    out = {}
    for folder in sorted(p for p in PANEL.iterdir() if p.is_dir()):
        c = Counter()
        for rf in sorted(folder.glob("*.jsonl")):
            for line in open(rf, encoding="utf-8"):
                rec = json.loads(line)
                raw = rec.get("raw_response") or ""
                resp = rec.get("response") or ""
                c["responses"] += 1
                c["finish_length"] += rec.get("finish_reason") == "length"
                c["think_open"] += "<think>" in raw
                c["think_unclosed"] += ("<think>" in raw or folder.name.endswith("__thinking")) and "</think>" not in raw
                c["empty_response"] += not resp.strip()
                c["trailing_ws"] += resp != resp.rstrip()
                c["leading_ws_raw"] += raw != raw.lstrip()
                c["resp_has_think_tag"] += "<think>" in resp or "</think>" in resp
                if rec.get("finish_reason") == "length" and "</think>" in raw:
                    c["length_after_think_close"] += 1
        out[folder.name] = c
    return out


def main():
    recs = load()
    rs = records_summary()
    keys = ["responses", "finish_length", "think_open", "think_unclosed", "length_after_think_close",
            "empty_response", "trailing_ws", "resp_has_think_tag"]
    with open(OUT / "panel_records.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("folder\t" + "\t".join(keys) + "\n")
        for f, c in rs.items():
            fh.write(f + "\t" + "\t".join(str(c[k]) for k in keys) + "\n")
    tot = Counter()
    for c in rs.values():
        tot.update(c)
    print("== stored records")
    print("total", {k: tot[k] for k in keys})
    for f, c in rs.items():
        if c["finish_length"] or c["think_unclosed"] or c["trailing_ws"]:
            print(f"  {f:45s} length={c['finish_length']:5d} unclosed_think={c['think_unclosed']:4d} trailing_ws={c['trailing_ws']:4d} empty={c['empty_response']}")

    # coverage
    exp = len(recs)
    cov = {col: sum(1 for r in recs if r[col] in ("0", "1")) for col in COLS}
    print("== scored coverage (instances with a verdict / expected instances)")
    for col in COLS:
        print(f"  {col}: {cov[col]}/{exp}")

    # unclosed thinking: how the grader treats extraction failures
    unc = [r for r in recs if r["folder"].endswith("__thinking") and r["think_close"] == "0"]
    print("== thinking configs: instances whose completion never closes </think>:", len(unc),
          "grader strict passes:", sum(r["g_strict"] == "1" for r in unc),
          "loose passes:", sum(r["g_loose"] == "1" for r in unc))

    # scores per configuration and run
    by_run = defaultdict(lambda: defaultdict(list))  # (folder, run) -> col -> list of (key, idx, v)
    for r in recs:
        by_run[(r["folder"], r["run"])]["rows"].append(r)

    def run_scores(rows, col, extraction_fail=False):
        prompts = defaultdict(list)
        for r in rows:
            v = r[col] == "1"
            if extraction_fail and r["folder"].endswith("__thinking") and r["think_close"] == "0":
                v = False
            prompts[r["key"]].append(v)
        inst = [v for vs in prompts.values() for v in vs]
        return 100 * sum(all(vs) for vs in prompts.values()) / len(prompts), 100 * sum(inst) / len(inst)

    score = {}
    for (folder, run), d in by_run.items():
        for col in COLS:
            score[(folder, run, col)] = run_scores(d["rows"], col)
        score[(folder, run, "x_prop_xf")] = run_scores(d["rows"], "x_prop", extraction_fail=True)
        score[(folder, run, "x_fix_xf")] = run_scores(d["rows"], "x_fix", extraction_fail=True)
    folders = sorted({f for f, _ in by_run})
    cols2 = COLS + ["x_fix_xf", "x_prop_xf"]
    summary = {"configs": {}}
    with open(OUT / "panel_scores.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fh.write("folder\tgrader\truns\tstrict_prompt_mean\tstrict_inst_mean\tgreedy\tgreedy_repeat\tbi_greedy\tsample_sd\n")
        for folder in folders:
            runs = sorted(r for f, r in by_run if f == folder)
            summary["configs"][folder] = {}
            for col in cols2:
                pv = [score[(folder, r, col)][0] for r in runs]
                iv = [score[(folder, r, col)][1] for r in runs]
                samples = [score[(folder, r, col)][0] for r in runs if r.startswith("sample")]
                g = score.get((folder, "greedy", col), (float("nan"),))[0]
                gr = score.get((folder, "greedy_repeat", col), (float("nan"),))[0]
                bg = score.get((folder, "bi_greedy", col), (float("nan"),))[0]
                sd = statistics.stdev(samples) if len(samples) > 1 else float("nan")
                fh.write(f"{folder}\t{col}\t{len(runs)}\t{statistics.mean(pv):.2f}\t{statistics.mean(iv):.2f}\t"
                         f"{g:.2f}\t{gr:.2f}\t{bg:.2f}\t{sd:.2f}\n")
                summary["configs"][folder][col] = dict(prompt_mean=round(statistics.mean(pv), 2),
                                                       inst_mean=round(statistics.mean(iv), 2),
                                                       greedy=round(g, 2), greedy_repeat=round(gr, 2),
                                                       bi_greedy=round(bg, 2), sample_sd=round(sd, 2) if sd == sd else None,
                                                       per_run={r: round(score[(folder, r, col)][0], 2) for r in runs})
    print("== strict prompt-level accuracy, mean over runs (instruction-level in brackets)")
    print(f"  {'config':45s} " + " ".join(f"{c:>15s}" for c in ["grader", "reference", "repl_FIX", "repl_PROP", "PROP+xfail", "g_loose"]))
    for folder in folders:
        s = summary["configs"][folder]
        vals = [s["g_strict"], s["r_strict"], s["x_fix"], s["x_prop"], s["x_prop_xf"], s["g_loose"]]
        print(f"  {folder:45s} " + " ".join(f"{v['prompt_mean']:6.2f} [{v['inst_mean']:5.2f}]" for v in vals))
    print("== score change vs grader (strict prompt-level, mean over runs) and rerun differences")
    print(f"  {'config':45s} {'ref-g':>7s} {'FIX-g':>7s} {'PROP-g':>7s} {'|g-rep|':>8s} {'|g-bi|':>7s} {'sampleSD':>8s}")
    for folder in folders:
        s = summary["configs"][folder]
        g = s["g_strict"]
        print(f"  {folder:45s} {s['r_strict']['prompt_mean'] - g['prompt_mean']:7.2f} "
              f"{s['x_fix']['prompt_mean'] - g['prompt_mean']:7.2f} {s['x_prop']['prompt_mean'] - g['prompt_mean']:7.2f} "
              f"{abs(g['greedy'] - g['greedy_repeat']):8.2f} {abs(g['greedy'] - g['bi_greedy']) if g['bi_greedy'] == g['bi_greedy'] else float('nan'):7.2f} "
              f"{g['sample_sd'] if g['sample_sd'] is not None else float('nan'):8.2f}")

    # per check
    per = defaultdict(Counter)
    for r in recs:
        c = per[r["iid"]]
        c["n"] += 1
        for col in COLS:
            c[col] += r[col] == "1"
        c["g_vs_r"] += r["g_strict"] != r["r_strict"]
        c["g_vs_fix"] += r["g_strict"] != r["x_fix"]
        c["g_vs_prop"] += r["g_strict"] != r["x_prop"]
        c["fix_vs_prop"] += r["x_fix"] != r["x_prop"]
        c["g1_fix0"] += r["g_strict"] == "1" and r["x_fix"] == "0"
        c["g0_fix1"] += r["g_strict"] == "0" and r["x_fix"] == "1"
        c["loose_only"] += r["g_loose"] == "1" and r["g_strict"] == "0"
        c["loose_only_fix0"] += r["g_loose"] == "1" and r["g_strict"] == "0" and r["x_fix"] == "0"
        c["loose_only_prop0"] += r["g_loose"] == "1" and r["g_strict"] == "0" and r["x_prop"] == "0"
    with open(OUT / "panel_checks.tsv", "w", newline="\n", encoding="utf-8") as fh:
        fields = ["n"] + COLS + ["g_vs_r", "g_vs_fix", "g1_fix0", "g0_fix1", "g_vs_prop", "fix_vs_prop",
                                 "loose_only", "loose_only_fix0", "loose_only_prop0"]
        fh.write("iid\t" + "\t".join(fields) + "\n")
        for iid in sorted(per):
            fh.write(iid + "\t" + "\t".join(str(per[iid][k]) for k in fields) + "\n")
    tot = Counter()
    for c in per.values():
        tot.update(c)
    print("== verdict disagreements over all instances:", dict(n=tot["n"], g_vs_r=tot["g_vs_r"], g_vs_fix=tot["g_vs_fix"],
          g1_fix0=tot["g1_fix0"], g0_fix1=tot["g0_fix1"], g_vs_prop=tot["g_vs_prop"], fix_vs_prop=tot["fix_vs_prop"],
          loose_only=tot["loose_only"], loose_only_fix0=tot["loose_only_fix0"]))
    print(f"  {'check':36s} {'n':>6s} {'g%':>6s} {'r%':>6s} {'fix%':>6s} {'prop%':>6s} {'g!=r':>6s} {'g!=fix':>7s} {'g1f0':>6s} {'g0f1':>6s} {'fix!=prop':>9s} {'looseonly':>9s} {'lo&fix0':>7s}")
    for iid in sorted(per, key=lambda k: -per[k]["g_vs_fix"]):
        c = per[iid]
        n = c["n"]
        print(f"  {iid:36s} {n:6d} {100*c['g_strict']/n:6.1f} {100*c['r_strict']/n:6.1f} {100*c['x_fix']/n:6.1f} {100*c['x_prop']/n:6.1f} "
              f"{c['g_vs_r']:6d} {c['g_vs_fix']:7d} {c['g1_fix0']:6d} {c['g0_fix1']:6d} {c['fix_vs_prop']:9d} {c['loose_only']:9d} {c['loose_only_fix0']:7d}")
    summary["totals"] = {k: tot[k] for k in tot}
    summary["records_total"] = {k: int(v) for k, v in Counter().items()}
    with open(OUT / "panel_summary.json", "w", newline="\n", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)


if __name__ == "__main__":
    main()
