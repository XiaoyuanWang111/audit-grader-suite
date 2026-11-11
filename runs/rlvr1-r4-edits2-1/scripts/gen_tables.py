"""Print markdown tables for audit/AUDIT.md: fixture counterexamples (with live verdicts) and the
per-check panel table. Output: audit/results/audit_tables.md."""
import json
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
logging.disable(logging.CRITICAL)
import absl.logging  # noqa: E402

absl.logging.set_verbosity(absl.logging.FATAL)
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

out = []


def v(b):
    return "pass" if b else "fail"


def cell(s):
    return s.replace("|", "\\|").replace("\n", "\\n")


out.append("| Ref | Fixture id (repro argument) | Check, kwargs | Exact response (Python repr) | Contract | NVIDIA/SkyRL | verifyit gate |")
out.append("|---|---|---|---|---|---|---|")
for fx in sorted([f for f in FIXTURES if f["kind"] in ("finding", "decision")], key=lambda f: (f["kind"], f["ref"])):
    nv = P.nvidia_check(fx["check"], fx["kwargs"], fx["response"])
    vi = None if fx["check"] in P.SEMANTIC else P.verifyit_check(fx["check"], fx["kwargs"], fx["response"])
    nvs = v(nv[0]) + (" (IndexError)" if nv[1] else "")
    vis = "judge" if vi is None else v(vi[0])
    kw = json.dumps(fx["kwargs"], ensure_ascii=False)
    out.append(f"| {fx['ref']} | `{fx['id']}` | `{fx['check']}` {cell(kw)} | `{cell(repr(fx['response']))}` | "
               f"{v(fx['label'])} | {nvs} | {vis} |")

summ = json.load(open(os.path.join(HERE, "..", "results", "panel_summary.json"), encoding="utf-8"))
out.append("")
out.append("| Check | Verdicts | Pass % replacement | Pass % SkyRL | SkyRL defects (false pass / false fail) | SkyRL decision-only | Pass % gate | Gate defects (fp / ff) | Gate decision-only |")
out.append("|---|---|---|---|---|---|---|---|---|")
for iid, c in sorted(summ["per_check"].items()):
    n = c["n"]
    vn = c.get("vi_n", 0)
    gate = f"{100 * c.get('vi_pass', 0) / vn:.1f}" if vn else "judge"
    gd = f"{c.get('vi_defect', 0)} ({c.get('vi_defect_falsepass', 0)} / {c.get('vi_defect_falsefail', 0)})" if vn else "-"
    out.append(f"| `{iid}` | {n} | {100 * c['rp_pass'] / n:.1f} | {100 * c['sk_pass'] / n:.1f} | "
               f"{c.get('sk_defect', 0)} ({c.get('sk_defect_falsepass', 0)} / {c.get('sk_defect_falsefail', 0)}) | "
               f"{c.get('sk_decision', 0)} | {gate} | {gd} | {c.get('vi_decision', 0) if vn else '-'} |")
# decision table: entries from CONTRACTS.md, sensitivity from extra_summary.json, fixture ids
extra = json.load(open(os.path.join(HERE, "..", "results", "extra_summary.json"), encoding="utf-8"))
entries = {}
for line in open(os.path.join(HERE, "..", "CONTRACTS.md"), encoding="utf-8"):
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    if line.startswith("| D-") and len(parts) == 3:
        entries[parts[0]] = (parts[1], parts[2])
# contract change C1 swapped the proposal of D-end-trailing-nonwords
entries["D-end-trailing-nonwords"] = ("non-word characters (closing quotes, punctuation, markup) may follow the phrase; no word may (change C1)",
                                      "nothing but whitespace may follow the phrase")
fx_by_entry = {}
for fx in FIXTURES:
    if fx["kind"] == "decision":
        fx_by_entry.setdefault(fx["ref"], []).append(fx["id"])
n_resp = 23315
out.append("")
out.append("| Entry | Proposed reading | Other reading | Constraint verdicts that change (panel) | Net prompt score change, points (all 23,315 responses) | Fixture |")
out.append("|---|---|---|---|---|---|")
for entry, (prop, other) in sorted(entries.items(), key=lambda kv: -extra["sensitivity"].get(kv[0], {}).get("constraint_changes", 0)):
    s = extra["sensitivity"].get(entry, {})
    fxs = ", ".join(f"`{i}`" for i in fx_by_entry.get(entry, [])[:2]) or "-"
    out.append(f"| {entry} | {prop} | {other} | {s.get('constraint_changes', '-')} | "
               f"{100 * s.get('prompt_delta', 0) / n_resp:+.2f} | {fxs} |")
with open(os.path.join(HERE, "..", "results", "audit_tables.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out[:5]))
print(f"... {len(out)} lines")
