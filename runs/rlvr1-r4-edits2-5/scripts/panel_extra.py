"""Extra step-5 numbers for AUDIT.md: held-out score changes, grader A's nondeterminism on the 77
unsatisfiable nth-paragraph rows, extraction-failure and literal-marker effects, semantic coverage,
and the per-check table. Writes audit/work/panel_tables.md."""
from __future__ import annotations

import collections
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import graders as g  # noqa: E402

V = W / "audit/work/panel_verdicts.jsonl"
S = json.loads((W / "audit/work/panel_summary.json").read_text(encoding="utf-8"))
OUT = W / "audit/work/panel_tables.md"
DATA = W / "case/data/rlvr1_instruction_following.jsonl"
DEV_N = 300
rng = random.Random(20261112)
recs = [json.loads(line) for line in V.open(encoding="utf-8")]
records = {}
for idx, line in enumerate(DATA.open(encoding="utf-8")):
    records[idx] = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])


def boot(d, reps=1000):
    n = len(d)
    m = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return m[25], m[974]


lines = []
# 1. per-run table (full panel and held-out)
lines.append("| Run | Rows | A score | Replacement score | Replacement − A, points [95% CI] | Held-out rows | Held-out replacement − A [95% CI] | B gate pass | Replacement gate pass | Replacement − B gate, points [95% CI] |")
lines.append("|---|---|---|---|---|---|---|---|---|---|")
for file, v in S["runs"].items():
    rows = [r for r in recs if r["file"] == file and r["n"] >= DEV_N]
    d = [float(all(r["R"])) - r["A_reward"] for r in rows]
    lo, hi = boot(d)
    lines.append(f"| {file} | {v['rows']} | {100*v['A_score']:.1f} | {100*v['R_score']:.1f} | {100*v['R_minus_A']:+.1f} [{100*v['R_minus_A_ci'][0]:+.1f}, {100*v['R_minus_A_ci'][1]:+.1f}] | {len(rows)} | {100*sum(d)/len(d):+.1f} [{100*lo:+.1f}, {100*hi:+.1f}] | {100*v['B_gate_pass']:.1f} | {100*v['R_gate_pass']:.1f} | {100*v['Rgate_minus_B']:+.1f} [{100*v['Rgate_minus_B_ci'][0]:+.1f}, {100*v['Rgate_minus_B_ci'][1]:+.1f}] |")
lines.append("")
lines.append("| Run | A passes | A false rewards (replacement fails) | A missed rewards | B false gate passes | B false gate fails |")
lines.append("|---|---|---|---|---|---|")
for file, v in S["runs"].items():
    lines.append(f"| {file} | {int(v['A_passes'])} | {v['A_false_rewards']} ({100*v['A_false_rewards']/max(v['A_passes'],1):.1f}%) | {v['A_missed_rewards']} | {v['B_false_gate_passes']} | {v['B_false_gate_fails']} |")
lines.append("")

# 2. nondeterminism of grader A on the unsatisfiable rows (nth_paragraph > num_paragraphs)
bad_rows = {idx for idx, rec in records.items() if any(
    i == "length_constraints:nth_paragraph_first_word" and k["nth_paragraph"] > k["num_paragraphs"]
    for i, k in zip(rec["instruction_id_list"], rec["kwargs"]))}
panel_bad = [r for r in recs if r["row"] in bad_rows]
raws = {}
flips = passes_any = 0
for r in panel_bad:
    path = W / "case/panel" / r["file"]
    if r["file"] not in raws:
        raws[r["file"]] = path.read_text(encoding="utf-8").splitlines()
    raw = json.loads(raws[r["file"]][r["n"]])["raw_response"]
    rewards = {g.skyrl_row(raw, records[r["row"]])["reward"] for _ in range(10)}
    flips += len(rewards) > 1
    passes_any += 1.0 in rewards
lines.append(f"Unsatisfiable nth-paragraph rows: {len(bad_rows)} rows; {len(panel_bad)} panel responses; grader A's row reward differs across 10 gradings of the same response for {flips}; at least one of the 10 gives reward 1.0 for {passes_any}.")
lines.append("")

# 3. extraction failures and literal markers
ef = [r for r in recs if r["extraction_failure"]]
lines.append(f"Thinking run: {len(ef)} of 1500 responses never close their reasoning; grader A row reward 1.0 on {sum(r['A_reward'] == 1.0 for r in ef)}, grader B gate passed on {sum(r['B_gate'] and r['B_has_gate'] for r in ef)}; constraint passes by A on these: {sum(sum(r['A']) for r in ef)} of {sum(len(r['A']) for r in ef)}.")
lm = [r for r in recs if r["literal_marker"]]
lines.append(f"Non-reasoning responses with a literal opening marker: {len(lm)}; graded as empty by A and B; A reward 1.0 on {sum(r['A_reward'] == 1.0 for r in lm)}; replacement (whole text) reward 1.0 on {sum(all(r['R']) for r in lm)}.")
# 4. semantic coverage
sem = collections.Counter()
for rec in records.values():
    for i in rec["instruction_id_list"]:
        sem["all"] += 1
        sem["semantic"] += i in g.SEMANTIC
    sem["rows_only_semantic"] += all(i in g.SEMANTIC for i in rec["instruction_id_list"])
lines.append(f"Grader B deterministic coverage: {sem['all'] - sem['semantic']} of {sem['all']} constraints get a check; {sem['semantic']} go to the LLM judge; {sem['rows_only_semantic']} rows have no deterministic constraint.")
lines.append("")

# 5. per-check table
lines.append("| Check | Panel verdicts | A pass % | B pass % | Replacement pass % | A ≠ replacement: finding / decision / error | B ≠ replacement: finding / decision |")
lines.append("|---|---|---|---|---|---|---|")
for k, c in S["per_check"].items():
    n = c["n"]
    bn = c.get("B_n", 0)
    bpass = f"{100*c.get('B_pass', 0)/bn:.0f}" if bn else "judge"
    bdis = f"{c.get('B_finding', 0)} / {c.get('B_decision', 0)}" if bn else "–"
    lines.append(f"| `{k}` | {n} | {100*c.get('A_pass', 0)/n:.0f} | {bpass} | {100*c.get('R_pass', 0)/n:.0f} | {c.get('A_finding', 0)} / {c.get('A_decision', 0)} / {c.get('A_grading_failure', 0)} | {bdis} |")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines[:22]))
