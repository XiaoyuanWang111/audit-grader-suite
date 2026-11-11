"""Step 5 analysis of audit/frozen/panel_verdicts.tsv.gz (+ panel_rep_graderreadings.tsv.gz).

Writes audit/frozen/panel_tables.md and audit/frozen/panel_numbers.json.
Usage: panel_analyze.py [--heldout]
"""
import csv
import gzip
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parents[2]
HELDOUT_ONLY = "--heldout" in sys.argv
THINK = ("Qwen__Qwen3-8B__thinking", "Qwen__Qwen3-14B__thinking")


def heldout(cfg, run):
    return run == ("greedy_repeat" if cfg in THINK else "sample0")


rows = list(csv.DictReader(gzip.open(W / "audit/frozen/panel_verdicts.tsv.gz", "rt", encoding="utf-8"), delimiter="\t"))
gr_path = W / "audit/frozen/panel_rep_graderreadings.tsv.gz"
if gr_path.exists():
    gr = {(r["config"], r["run"], r["key"], r["idx"]): r["rep_graderreadings"]
          for r in csv.DictReader(gzip.open(gr_path, "rt", encoding="utf-8"), delimiter="\t")}
    for r in rows:
        r["rep_gr"] = gr[(r["config"], r["run"], r["key"], r["idx"])]
else:
    for r in rows:
        r["rep_gr"] = r["rep"]
if HELDOUT_ONLY:
    rows = [r for r in rows if heldout(r["config"], r["run"])]

COLS = ["g_strict", "g_loose", "r_strict", "r_loose", "rep", "rep_gr"]
ALT = [c for c in rows[0] if c.startswith("alt:")]
out = []
num = {}


def P(s=""):
    out.append(s)


P(f"# Panel tables ({'held-out files only' if HELDOUT_ONLY else 'all 228 files'})")
P()
P(f"Verdict rows (response x instruction): {len(rows)}")

# 1. coverage and exceptions
P("\n## Scored coverage and grading failures\n")
P("| column | verdicts | pass | fail | exception | coverage |")
P("|---|---|---|---|---|---|")
for c in COLS + ALT:
    cnt = Counter("E" if r[c].startswith("E") else r[c] for r in rows)
    exc = Counter(r[c] for r in rows if r[c].startswith("E"))
    if c in COLS:
        P(f"| {c} | {len(rows)} | {cnt['1']} | {cnt['0']} | {cnt['E']} {dict(exc) if exc else ''} | {100 * (len(rows) - cnt['E']) / len(rows):.3f}% |")
    num[f"exceptions:{c}"] = dict(exc)

# 2. scores per configuration
prompts = defaultdict(lambda: defaultdict(list))  # (cfg, run) -> key -> list of rows
for r in rows:
    prompts[(r["config"], r["run"])][r["key"]].append(r)


def score(cfg_run, col, level="prompt"):
    keys = prompts[cfg_run]
    if level == "prompt":
        ok = sum(1 for k, rs in keys.items() if all(x[col] == "1" for x in rs))
        return 100 * ok / len(keys)
    tot = sum(len(rs) for rs in keys.values())
    ok = sum(1 for rs in keys.values() for x in rs if x[col] == "1")
    return 100 * ok / tot


cfgs = sorted({c for c, _ in prompts})
P("\n## Strict prompt-level accuracy per configuration (mean over runs, %)\n")
P("| configuration | runs | grader | reference | replacement | replacement, grader's readings | replacement - grader | of which decisions | of which defects | grader loose | rerun diff (grader, greedy vs greedy_repeat) | rerun diff (replacement) |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|")
per_cfg = {}
for cfg in cfgs:
    runs = sorted(r for c, r in prompts if c == cfg)
    m = {c: statistics.mean(score((cfg, r), c) for r in runs) for c in COLS}
    rr_g = rr_r = float("nan")
    if (cfg, "greedy") in prompts and (cfg, "greedy_repeat") in prompts:
        rr_g = abs(score((cfg, "greedy"), "g_strict") - score((cfg, "greedy_repeat"), "g_strict"))
        rr_r = abs(score((cfg, "greedy"), "rep") - score((cfg, "greedy_repeat"), "rep"))
    per_cfg[cfg] = dict(m, runs=len(runs), rerun_g=rr_g, rerun_rep=rr_r)
    P(f"| {cfg} | {len(runs)} | {m['g_strict']:.2f} | {m['r_strict']:.2f} | {m['rep']:.2f} | {m['rep_gr']:.2f} | "
      f"{m['rep'] - m['g_strict']:+.2f} | {m['rep'] - m['rep_gr']:+.2f} | {m['rep_gr'] - m['g_strict']:+.2f} | {m['g_loose']:.2f} | {rr_g:.2f} | {rr_r:.2f} |")
num["per_cfg"] = per_cfg

# rank changes
rank = lambda col: [c for c, _ in sorted(per_cfg.items(), key=lambda kv: -kv[1][col])]
P("\nRanking by grader strict: " + ", ".join(f"{i + 1}. {c}" for i, c in enumerate(rank("g_strict"))))
P("\nRanking by replacement: " + ", ".join(f"{i + 1}. {c}" for i, c in enumerate(rank("rep"))))
num["rank_grader"], num["rank_rep"] = rank("g_strict"), rank("rep")

# instruction-level
P("\n## Strict instruction-level accuracy per configuration (mean over runs, %)\n")
P("| configuration | grader | reference | replacement | replacement - grader |")
P("|---|---|---|---|---|")
for cfg in cfgs:
    runs = sorted(r for c, r in prompts if c == cfg)
    g = statistics.mean(score((cfg, r), "g_strict", "instr") for r in runs)
    re_ = statistics.mean(score((cfg, r), "r_strict", "instr") for r in runs)
    rp = statistics.mean(score((cfg, r), "rep", "instr") for r in runs)
    P(f"| {cfg} | {g:.2f} | {re_:.2f} | {rp:.2f} | {rp - g:+.2f} |")

# rerun differences between all greedy-type runs
P("\n## Rerun and batch-invariance differences (prompt-level strict, grader)\n")
P("| configuration | greedy | greedy_repeat | greedy_shuffled | bi_greedy | bi_greedy_shuffled | max-min |")
P("|---|---|---|---|---|---|---|")
for cfg in cfgs:
    vals = []
    cells = []
    for run in ["greedy", "greedy_repeat", "greedy_shuffled", "bi_greedy", "bi_greedy_shuffled"]:
        if (cfg, run) in prompts:
            v = score((cfg, run), "g_strict")
            vals.append(v)
            cells.append(f"{v:.2f}")
        else:
            cells.append("-")
    P(f"| {cfg} | " + " | ".join(cells) + (f" | {max(vals) - min(vals):.2f} |" if vals else " | - |"))

# 3. per-check pass rates and disagreements
P("\n## Per-check pass rates (%) and disagreements (counts of verdicts)\n")
P("| check | n | grader | reference | replacement | grader pass, contract fail | grader fail, contract pass | of which defect (vs replacement with grader's readings) | of which decision | grader != reference |")
P("|---|---|---|---|---|---|---|---|---|---|")
by = defaultdict(list)
for r in rows:
    by[r["iid"]].append(r)
perchk = {}
for iid in sorted(by):
    rs = by[iid]
    n = len(rs)
    pr = lambda c: 100 * sum(1 for x in rs if x[c] == "1") / n
    fp = sum(1 for x in rs if x["g_strict"] == "1" and x["rep"] == "0")
    fn = sum(1 for x in rs if x["g_strict"] == "0" and x["rep"] == "1")
    dfx = sum(1 for x in rs if x["g_strict"] != x["rep_gr"])
    ddc = sum(1 for x in rs if x["rep"] != x["rep_gr"])
    gr_ = sum(1 for x in rs if x["g_strict"] != x["r_strict"])
    perchk[iid] = dict(n=n, g=pr("g_strict"), r=pr("r_strict"), rep=pr("rep"), fp=fp, fn=fn, defect=dfx, decision=ddc, g_vs_r=gr_)
    P(f"| {iid} | {n} | {pr('g_strict'):.1f} | {pr('r_strict'):.1f} | {pr('rep'):.1f} | {fp} | {fn} | {dfx} | {ddc} | {gr_} |")
tot_fp = sum(v["fp"] for v in perchk.values())
tot_fn = sum(v["fn"] for v in perchk.values())
tot_def = sum(v["defect"] for v in perchk.values())
tot_dec = sum(v["decision"] for v in perchk.values())
tot_gr = sum(v["g_vs_r"] for v in perchk.values())
P(f"| **all** | {len(rows)} | | | | {tot_fp} | {tot_fn} | {tot_def} | {tot_dec} | {tot_gr} |")
num["perchk"] = perchk
num["totals"] = dict(fp=tot_fp, fn=tot_fn, defect=tot_def, decision=tot_dec, g_vs_r=tot_gr, n=len(rows))

# 4. extraction failures
unc = [r for r in rows if r["unclosed"] == "1"]
P("\n## Responses whose reasoning never closed (extraction failures under G1)\n")
P(f"Verdict rows: {len(unc)}; responses: {len({(r['config'], r['run'], r['key']) for r in unc})}")
P(f"Grader strict passes on them: {sum(1 for r in unc if r['g_strict'] == '1')}; reference strict passes: {sum(1 for r in unc if r['r_strict'] == '1')}; grader loose passes: {sum(1 for r in unc if r['g_loose'] == '1')}")
P("Checks passed by the grader on unclosed reasoning: " + json.dumps(Counter(r["iid"] for r in unc if r["g_strict"] == "1").most_common()))
num["unclosed"] = dict(rows=len(unc), g_pass=sum(1 for r in unc if r["g_strict"] == "1"),
                       r_pass=sum(1 for r in unc if r["r_strict"] == "1"), g_loose_pass=sum(1 for r in unc if r["g_loose"] == "1"))
# prompt-level effect for thinking configs
for cfg in THINK:
    runs = sorted(r for c, r in prompts if c == cfg)
    if not runs:
        continue
    g = statistics.mean(score((cfg, r), "g_strict") for r in runs)
    # grader with extraction failures forced to fail
    def sc(run):
        keys = prompts[(cfg, run)]
        return 100 * sum(1 for rs in keys.values() if all(x["g_strict"] == "1" and x["unclosed"] == "0" for x in rs)) / len(keys)
    g2 = statistics.mean(sc(r) for r in runs)
    P(f"- {cfg}: grader strict {g:.2f}% -> {g2:.2f}% when extraction failures fail every check")

# 5. empties, truncation
P("\n## Stored-record counts\n")
P(f"Empty responses (verdict rows): {sum(1 for r in rows if r['empty'] == '1')}; finish_reason=length rows: {sum(1 for r in rows if r['finish'] == 'length')}")
trunc = [r for r in rows if r["finish"] == "length" and r["unclosed"] == "0"]
P(f"Truncated (length) but reasoning closed or no reasoning: {len(trunc)} rows; grader passes among them: {sum(1 for r in trunc if r['g_strict'] == '1')}")

# 6. decision effects
P("\n## Effect of each decision's alternative reading on the replacement\n")
P("| alternative | verdicts changed | prompt-level accuracy change, mean over configurations (points) |")
P("|---|---|---|")
dec_eff = {}
for c in ALT:
    ch = sum(1 for r in rows if r[c] != r["rep"])
    deltas = []
    for cfg in cfgs:
        runs = sorted(r for cc, r in prompts if cc == cfg)
        deltas.append(statistics.mean(score((cfg, r), c) - score((cfg, r), "rep") for r in runs))
    dec_eff[c] = dict(changed=ch, mean_delta=statistics.mean(deltas))
    P(f"| {c[4:]} | {ch} | {statistics.mean(deltas):+.3f} |")
num["decision_effects"] = dec_eff

# 7. loose vs strict
P("\n## Loose grading (grader)\n")
lp = [r for r in rows if r["g_loose"] == "1" and r["g_strict"] == "0"]
P(f"Verdicts that loose turns into a pass: {len(lp)}; of these the contract (replacement) fails {sum(1 for r in lp if r['rep'] == '0')}")
P("By check: " + json.dumps(Counter(r["iid"] for r in lp if r["rep"] == "0").most_common(20)))
num["loose"] = dict(turned=len(lp), contract_fail=sum(1 for r in lp if r["rep"] == "0"))

name = "panel_tables_heldout" if HELDOUT_ONLY else "panel_tables"
(W / f"audit/frozen/{name}.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
json.dump(num, open(W / f"audit/frozen/{name.replace('tables', 'numbers')}.json", "w", encoding="utf-8"), indent=1, default=str)
print("\n".join(out[:12]))
print(f"... written audit/frozen/{name}.md")
