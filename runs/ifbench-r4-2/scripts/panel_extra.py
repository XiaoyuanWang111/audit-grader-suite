"""Extra panel numbers for the report: model rankings under each grader, the
effect of trailing whitespace (D-trim), and per-check shares of changed verdicts.
Reads audit/out/panel_summary.json, audit/out/panel_checks.tsv and the panel files."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))

S = json.load(open(W / "audit/out/panel_summary.json", encoding="utf-8"))["configs"]


def ranking(col):
    return sorted(S, key=lambda f: -S[f][col]["prompt_mean"])


def kendall(a, b):
    pos = {x: i for i, x in enumerate(b)}
    n = len(a)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (pos[a[i]] - pos[a[j]])
            if s < 0:
                conc += 1
            else:
                disc += 1
    return (conc - disc) / (n * (n - 1) / 2), disc


g = ranking("g_strict")
print("== rankings by strict prompt-level accuracy (mean over runs)")
for col in ("r_strict", "x_fix", "x_prop", "x_prop_xf"):
    tau, disc = kendall(g, ranking(col))
    print(f"  grader vs {col}: Kendall tau {tau:.3f}, discordant pairs {disc} of {len(g) * (len(g) - 1) // 2}")
print(f"  {'rank':4s} {'grader':45s} {'repl FIX':45s} {'repl PROPOSED':45s}")
for i, (a, b, c) in enumerate(zip(g, ranking("x_fix"), ranking("x_prop")), 1):
    print(f"  {i:<4d} {a + ' ' + str(S[a]['g_strict']['prompt_mean']):45s} {b + ' ' + str(S[b]['x_fix']['prompt_mean']):45s} "
          f"{c + ' ' + str(S[c]['x_prop']['prompt_mean']):45s}")

# D-trim: regrade responses with trailing whitespace after rstrip
import harness as H  # noqa: E402
rows = H.row_by_key()
flips = Counter()
n_resp = 0
for folder in sorted(p for p in (W / "case/panel").iterdir() if p.is_dir()):
    for rf in sorted(folder.glob("*.jsonl")):
        for line in open(rf, encoding="utf-8"):
            rec = json.loads(line)
            resp = rec["response"] or ""
            if resp == resp.rstrip() or not resp.strip():
                continue
            n_resp += 1
            row = rows[str(rec["key"])]
            a, _ = H.grade_row(row, resp, "grader", "strict")
            b, _ = H.grade_row(row, resp.rstrip(), "grader", "strict")
            for i, iid in enumerate(row["instruction_id_list"]):
                if a[i] != b[i]:
                    flips[(iid, "fail->pass" if b[i] else "pass->fail")] += 1
print(f"== trailing whitespace: {n_resp} stored responses end in whitespace; grader verdict changes after rstrip:")
for (iid, d), n in flips.most_common():
    print(f"  {iid} {d}: {n}")

print("== per-check share of instances where grader and replacement FIX differ (finding-attributable)")
tot = 0
for r in csv.DictReader(open(W / "audit/out/panel_checks.tsv", encoding="utf-8"), delimiter="\t"):
    n, d = int(r["n"]), int(r["g_vs_fix"])
    tot += int(r["n"])
    if d:
        print(f"  {r['iid']:36s} {d:5d}/{n:5d} = {100 * d / n:5.1f}%  (grader pass->FIX fail {r['g1_fix0']}, fail->pass {r['g0_fix1']})")
print("  total instances", tot)
