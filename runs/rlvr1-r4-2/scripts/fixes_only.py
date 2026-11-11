"""Defect-only score change (step 5): per run, the score each grader would give if only its findings
were fixed. A constraint's verdict is the grader's own when it agrees with R or when a single decision
entry's reading B (or all consulted entries together) reproduces it; otherwise R's verdict. A response
whose extractions differ (P1) takes R's verdicts. Writes audit/out/fixes_only.json.
"""
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np

W = Path(__file__).resolve().parents[2]


def boot(diffs, n=2000, seed=0):
    d = np.asarray(diffs, dtype=float)
    idx = np.random.default_rng(seed).integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    return [100 * float(d.mean()), 100 * float(np.percentile(m, 2.5)), 100 * float(np.percentile(m, 97.5))]


def fixed_verdict(rec, c, g):
    gv = c[g]
    if gv is None:
        return None
    if rec["extraction_differs_" + g]:
        return c["R"]
    if gv is c["R"] or c.get(g + "_explained") or c.get(g + "_explained_all_used"):
        return gv
    return c["R"]


def main():
    runs = OrderedDict()
    for line in (W / "audit" / "out" / "panel_verdicts.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        runs.setdefault(rec["file"], []).append(rec)
    out = {}
    for f, rs in runs.items():
        a, a_fix, b, b_fix = [], [], [], []
        for rec in rs:
            a.append(rec["A_session_reward"])
            vs = [fixed_verdict(rec, c, "A") for c in rec["cons"]]
            a_fix.append(float(not rec["r_extraction_failed"] and all(vs)))
            b.append(1.0 if rec["B_gate"] else 0.0)
            vb = [fixed_verdict(rec, c, "B") for c in rec["cons"] if c["B"] is not None]
            b_fix.append(float(not rec["r_extraction_failed"] and all(vb)))
        out[f] = {"A": 100 * np.mean(a), "A_fixed": 100 * np.mean(a_fix), "A_fixed_minus_A": boot([y - x for x, y in zip(a, a_fix)]),
                  "B": 100 * np.mean(b), "B_fixed": 100 * np.mean(b_fix), "B_fixed_minus_B": boot([y - x for x, y in zip(b, b_fix)])}
        o = out[f]
        print(f"{f:<60} A {o['A']:.1f} -> {o['A_fixed']:.1f} ({o['A_fixed_minus_A'][0]:+.1f} [{o['A_fixed_minus_A'][1]:+.1f},{o['A_fixed_minus_A'][2]:+.1f}])"
              f"   B gate {o['B']:.1f} -> {o['B_fixed']:.1f} ({o['B_fixed_minus_B'][0]:+.1f} [{o['B_fixed_minus_B'][1]:+.1f},{o['B_fixed_minus_B'][2]:+.1f}])")
    (W / "audit" / "out" / "fixes_only.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
