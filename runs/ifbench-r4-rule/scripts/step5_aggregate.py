"""Step 5 aggregation over audit/out/panel/*.tsv.

Prints (and writes audit/out/step5_summary.md):
  - per configuration: prompt-level and instruction-level accuracy, mean over runs, for
    G (grader strict, float kwargs, exception = fail), Gi (int-cast), R (reference strict),
    GL/GLi/RL (loose), X (replacement, if present), and the same with extraction failures failed;
  - rerun differences (greedy vs greedy_repeat, greedy vs greedy_shuffled, bi_greedy vs
    bi_greedy_shuffled, sample spread) next to the grader-vs-reference differences;
  - per check: pass rates and G-vs-R / Gi-vs-R / Gi-vs-X disagreements;
  - scored coverage (items with a verdict) per implementation;
  - extraction failures, truncation, empty responses;
  - loose-pass-but-strict-fail counts per check (F42).
"""
import collections
import csv
import glob
import json
import os
import statistics
import sys

W = "<W>"
files = sorted(glob.glob(f"{W}/audit/out/panel/*.tsv"))
IMPLS = ["g", "gi", "r", "gl", "gli", "rl"]
lines_out = []


def P(s=""):
    print(s)
    lines_out.append(s)


def tv(v):
    return v == "True"


data = {}  # (cfg, run) -> list of rows
for p in files:
    base = os.path.basename(p)[:-4]
    cfg, run = base.rsplit("__", 1)
    with open(p, encoding="utf-8") as f:
        data[(cfg, run)] = list(csv.DictReader(f, delimiter="\t"))
has_x = all("x" in rows[0] and "xg" in rows[0] for rows in data.values())
if has_x:
    IMPLS += ["x", "xg"]


def scores(rows, impl, fail_unclosed=False):
    by_key = collections.defaultdict(list)
    for r in rows:
        ok = tv(r[impl]) and not (fail_unclosed and "U" in r["flags"])
        by_key[r["key"]].append(ok)
    prompt = sum(all(v) for v in by_key.values()) / len(by_key)
    inst = sum(sum(v) for v in by_key.values()) / sum(len(v) for v in by_key.values())
    return prompt, inst


cfgs = sorted({c for c, _ in data})
P(f"# Step 5 panel summary\n\n{len(data)} run files, {sum(len(v) for v in data.values())} (row, check) items, "
  f"{len(cfgs)} configurations. Accuracies are means over a configuration's runs, in percent.\n")
P("## Prompt-level accuracy (strict unless marked loose)\n")
hdr = "| configuration | runs | G (as loaded) | Gi (int kwargs) | R (reference) | G-R | Gi-R |" + (" XG (replacement, grader readings) | X (replacement, proposed readings) | XG-Gi (defects) | X-XG (decisions, G1) | X-G (total) |" if has_x else "") + " GL loose | RL loose | R, extraction failures failed |"
P(hdr)
P("|" + "---|" * (hdr.count("|") - 1))
per_cfg = {}
for c in cfgs:
    runs = sorted(r for cc, r in data if cc == c)
    m = {i: statistics.mean(scores(data[(c, r)], i)[0] for r in runs) * 100 for i in IMPLS}
    ru = statistics.mean(scores(data[(c, r)], "r", True)[0] for r in runs) * 100
    per_cfg[c] = m
    row = f"| {c} | {len(runs)} | {m['g']:.2f} | {m['gi']:.2f} | {m['r']:.2f} | {m['g']-m['r']:+.2f} | {m['gi']-m['r']:+.2f} |"
    if has_x:
        row += f" {m['xg']:.2f} | {m['x']:.2f} | {m['xg']-m['gi']:+.2f} | {m['x']-m['xg']:+.2f} | {m['x']-m['g']:+.2f} |"
    row += f" {m['gl']:.2f} | {m['rl']:.2f} | {ru:.2f} |"
    P(row)

P("\n## Instruction-level accuracy (strict)\n")
P("| configuration | G | Gi | R | G-R | Gi-R |" + (" X | X-Gi |" if has_x else ""))
P("|---|---|---|---|---|---|" + ("---|---|" if has_x else ""))
for c in cfgs:
    runs = sorted(r for cc, r in data if cc == c)
    m = {i: statistics.mean(scores(data[(c, r)], i)[1] for r in runs) * 100 for i in IMPLS}
    row = f"| {c} | {m['g']:.2f} | {m['gi']:.2f} | {m['r']:.2f} | {m['g']-m['r']:+.2f} | {m['gi']-m['r']:+.2f} |"
    if has_x:
        row += f" {m['x']:.2f} | {m['x']-m['gi']:+.2f} |"
    P(row)

P("\n## Rerun differences (prompt-level, reference strict R and grader G)\n")
P("| configuration | greedy | greedy_repeat - greedy (R) | greedy_shuffled - greedy (R) | bi_greedy_shuffled - bi_greedy (R) | sample sd (R) | sample sd (G) | max abs(G-R) over runs |")
P("|---|---|---|---|---|---|---|---|")
for c in cfgs:
    s = {r: {i: scores(data[(c, r)], i)[0] * 100 for i in ("g", "r")} for cc, r in data if cc == c}
    d = lambda a, b, i="r": (f"{s[a][i]-s[b][i]:+.2f}" if a in s and b in s else "n/a")  # noqa: E731
    samp = [s[r] for r in s if r.startswith("sample")]
    sdr = f"{statistics.stdev(x['r'] for x in samp):.2f}" if len(samp) > 1 else "n/a"
    sdg = f"{statistics.stdev(x['g'] for x in samp):.2f}" if len(samp) > 1 else "n/a"
    mx = max(abs(x["g"] - x["r"]) for x in s.values())
    P(f"| {c} | {s['greedy']['r']:.2f} | {d('greedy_repeat','greedy')} | {d('greedy_shuffled','greedy')} | {d('bi_greedy_shuffled','bi_greedy')} | {sdr} | {sdg} | {mx:.2f} |")

P("\n## Per check (all runs pooled)\n")
pc = collections.defaultdict(lambda: collections.Counter())
for rows in data.values():
    for r in rows:
        c = pc[r["check"]]
        c["n"] += 1
        for i in IMPLS:
            if tv(r[i]):
                c[i] += 1
            if r[i].startswith("EXC"):
                c[i + "_exc"] += 1
        c["g_ne_r"] += r["g"] != r["r"]
        c["gi_ne_r"] += r["gi"] != r["r"]
        if has_x:
            c["gi_ne_x"] += r["gi"] != r["x"]
            c["gi_ne_xg"] += r["gi"] != r["xg"]
            c["xg_ne_x"] += r["xg"] != r["x"]
        c["loose_rescue_g"] += (r["gli"] == "True" and r["gi"] != "True")
        c["loose_rescue_r"] += (r["rl"] == "True" and r["r"] != "True")
P("| check | items | G pass % | Gi pass % | R pass % | G exceptions | G!=R | Gi!=R |" + (" X pass % | Gi!=X | Gi!=XG (defects) | XG!=X (decisions, G1) |" if has_x else "") + " loose-only passes (Gi) |")
P("|---|---|---|---|---|---|---|---|" + ("---|---|---|---|" if has_x else "") + "---|")
for chk in sorted(pc):
    c = pc[chk]
    n = c["n"]
    row = f"| {chk} | {n} | {100*c['g']/n:.1f} | {100*c['gi']/n:.1f} | {100*c['r']/n:.1f} | {c['g_exc']} | {c['g_ne_r']} | {c['gi_ne_r']} |"
    if has_x:
        row += f" {100*c['x']/n:.1f} | {c['gi_ne_x']} | {c['gi_ne_xg']} | {c['xg_ne_x']} |"
    row += f" {c['loose_rescue_g']} |"
    P(row)

tot = collections.Counter()
for rows in data.values():
    for r in rows:
        tot["items"] += 1
        for i in IMPLS:
            tot[i + "_verdict"] += not r[i].startswith("EXC")
P("\n## Scored coverage (items with a verdict / expected items)\n")
for i in IMPLS:
    P(f"- {i}: {tot[i + '_verdict']}/{tot['items']} = {100*tot[i + '_verdict']/tot['items']:.3f}%")

P("\n## Responses: extraction failures, truncation, empty\n")
fl = collections.Counter()
unclosed_pass = collections.Counter()
for (c, run), rows in data.items():
    seen = set()
    for r in rows:
        k = (c, run, r["key"])
        if k not in seen:
            seen.add(k)
            for ch in "UTE":
                if ch in r["flags"]:
                    fl[(c, ch)] += 1
        if "U" in r["flags"]:
            for i in ("g", "gi", "r"):
                unclosed_pass[(c, i)] += tv(r[i])
P("| configuration | unclosed reasoning (extraction failures) | checks passed on them (G / Gi / R) | truncated | empty |")
P("|---|---|---|---|---|")
for c in cfgs:
    P(f"| {c} | {fl[(c,'U')]} | {unclosed_pass[(c,'g')]} / {unclosed_pass[(c,'gi')]} / {unclosed_pass[(c,'r')]} | {fl[(c,'T')]} | {fl[(c,'E')]} |")

if has_x:
    HELD = lambda c, r: (r == "sample7") or (c.endswith("__thinking") and r == "greedy_repeat")  # noqa: E731
    P("\n## Held-out runs only (sample7; greedy_repeat for the thinking configurations), prompt-level\n")
    P("| configuration | run | G | Gi | R | XG | X | X-G | X-XG |")
    P("|---|---|---|---|---|---|---|---|---|")
    hs = collections.defaultdict(list)
    for (c, r), rows in sorted(data.items()):
        if HELD(c, r):
            s_ = {i: scores(rows, i)[0] * 100 for i in ("g", "gi", "r", "xg", "x")}
            for i, v in s_.items():
                hs[i].append(v)
            P(f"| {c} | {r} | {s_['g']:.2f} | {s_['gi']:.2f} | {s_['r']:.2f} | {s_['xg']:.2f} | {s_['x']:.2f} | {s_['x']-s_['g']:+.2f} | {s_['x']-s_['xg']:+.2f} |")
    P(f"| mean of {len(hs['g'])} held-out runs | | {statistics.mean(hs['g']):.2f} | {statistics.mean(hs['gi']):.2f} | {statistics.mean(hs['r']):.2f} | {statistics.mean(hs['xg']):.2f} | {statistics.mean(hs['x']):.2f} | {statistics.mean(hs['x'])-statistics.mean(hs['g']):+.2f} | {statistics.mean(hs['x'])-statistics.mean(hs['xg']):+.2f} |")
    # verdict-level disagreement shares
    tot_items = sum(len(v) for v in data.values())
    for a, b in (("g", "r"), ("gi", "r"), ("gi", "xg"), ("xg", "x"), ("g", "x")):
        n = sum(1 for rows in data.values() for r in rows if r[a] != r[b])
        P(f"- verdicts where {a} != {b}: {n}/{tot_items} = {100*n/tot_items:.2f}%")

open(f"{W}/audit/out/step5_summary.md", "w", encoding="utf-8", newline="\n").write("\n".join(lines_out) + "\n")

# reference pipeline equivalence: run_eval.py output vs in-process verdicts (marin greedy)
ref_out = f"{W}/audit/out/ref_check/marin8b_greedy-eval_results_strict.jsonl"
if os.path.exists(ref_out) and ("marin-community__marin-8b-instruct", "greedy") in data:
    rows = data[("marin-community__marin-8b-instruct", "greedy")]
    mine = collections.defaultdict(list)
    for r in rows:
        mine[int(r["key"])].append(r["r"] == "True")
    sys.path.insert(0, f"{W}/audit/lib")
    import harness as H
    prompt2key = {x["prompt"].strip(): int(x["key"]) for x in H.dataset()}
    mism = 0
    for l in open(ref_out, encoding="utf-8"):
        o = json.loads(l)
        k = prompt2key[o["prompt"].strip()]
        mism += o["follow_instruction_list"] != mine[k]
    print(f"\nreference run_eval.py vs in-process reference verdicts (marin greedy): {mism} rows differ of 300")
