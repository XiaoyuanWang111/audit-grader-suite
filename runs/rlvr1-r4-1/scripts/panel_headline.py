"""Headline numbers for audit/AUDIT.md from audit/out/panel_verdicts.jsonl.

Constraint-level disagreement with the contract (proposed readings) and with "fixes only"
(each grader's own readings), for SkyRL and the gate; row-level false rewards per run; and the
same on the held-out half. These are disagreement rates against the replacement grader, not the
error rate of step 6 (no blinded review in this exercise).
"""
import collections
import json
import pathlib

W = pathlib.Path(__file__).resolve().parents[2]


def pct(a, b):
    return f"{a}/{b} = {100 * a / b:.1f}%" if b else "0/0"


def main():
    recs = [json.loads(l) for l in (W / "audit" / "out" / "panel_verdicts.jsonl").open(encoding="utf-8")]
    for half in ("all", "heldout"):
        rs = recs if half == "all" else [r for r in recs if r["heldout"]]
        c = collections.Counter()
        per_run = collections.defaultdict(collections.Counter)
        for r in rs:
            run = r["folder"].split("__")[1] + "/" + r["run"]
            for i in range(len(r["ids"])):
                s, g, p, o, ov = r["skyrl"][i], r["gate"][i], r["repl"][i], r["off_sk"][i], r["off_vi"][i]
                c["n"] += 1
                c["sk_vs_prop"] += s != p
                c["sk_vs_fo"] += s != o
                if g is not None:
                    c["gn"] += 1
                    c["g_vs_prop"] += g != p
                    c["g_vs_fo"] += g != ov
            pr = per_run[run]
            pr["n"] += 1
            pr["sk1"] += r["skyrl_reward"] == 1.0
            pr["sk1_fo0"] += r["skyrl_reward"] == 1.0 and r["off_sk_reward"] == 0.0
            pr["sk1_p0"] += r["skyrl_reward"] == 1.0 and r["repl_reward"] == 0.0
            offv = [v for v in r["off_vi"] if v is not None]
            pr["gp"] += r["gate_pass"]
            pr["gp_fo_fail"] += r["gate_pass"] and not all(offv)
            pr["gf_fo_pass"] += (not r["gate_pass"]) and all(offv)
        print(f"== {half}: constraint verdicts {c['n']}, gated {c['gn']}")
        print("  SkyRL vs contract (proposed):", pct(c["sk_vs_prop"], c["n"]))
        print("  SkyRL vs fixes only:", pct(c["sk_vs_fo"], c["n"]))
        print("  gate check vs contract (proposed):", pct(c["g_vs_prop"], c["gn"]))
        print("  gate check vs fixes only:", pct(c["g_vs_fo"], c["gn"]))
        tot = collections.Counter()
        for run, pr in per_run.items():
            tot.update(pr)
            print(f"  {run}: SkyRL reward 1.0 = {pr['sk1']}; contradicted (fixes only) {pct(pr['sk1_fo0'], pr['sk1'])};"
                  f" (proposed) {pct(pr['sk1_p0'], pr['sk1'])}; gate passes {pr['gp']}, false gate passes (fixes only)"
                  f" {pct(pr['gp_fo_fail'], pr['gp'])}; false gate failures (fixes only) {pr['gf_fo_pass']}")
        print(f"  TOTAL: SkyRL reward 1.0 = {tot['sk1']}; false rewards (fixes only) {pct(tot['sk1_fo0'], tot['sk1'])};"
              f" (proposed) {pct(tot['sk1_p0'], tot['sk1'])}; gate passes {tot['gp']}; false gate passes (fixes only)"
              f" {pct(tot['gp_fo_fail'], tot['gp'])}; false gate failures (fixes only) {tot['gf_fo_pass']} of"
              f" {tot['n'] - tot['gp']} gate failures")


if __name__ == "__main__":
    main()
