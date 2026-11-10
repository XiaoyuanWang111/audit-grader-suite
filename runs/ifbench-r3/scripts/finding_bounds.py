"""Per-check bound on the panel verdicts that the checker findings can affect (step 5 data, no labels).

For every check: the panel verdicts where the grader (strict) and the replacement (proposed
readings) disagree, split into those that one switched decision reproduces (the grader's verdict
equals the replacement's under that reading: a decision, not a finding) and the rest. The rest is
an upper bound on the verdicts that the check's findings change; when a check has several findings
they share it. Extraction failures (G1) are excluded and counted under F-extract-unclosed.
Output: audit/work/finding_bounds.json and a printed table.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/finding_bounds.py
"""
import collections
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    per = collections.defaultdict(collections.Counter)
    total = 0
    with open(os.path.join(W, "audit", "work", "panel_verdicts.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)
            if v["extraction_failure"]:
                continue
            total += 1
            c = per[v["iid"]]
            c["n"] += 1
            if v["g"] != v["p"]:
                explained = any(a == v["g"] for a in v["alt"].values())
                kind = "explained" if explained else "unexplained"
                c[kind] += 1
                c[f"{kind}_{'g1p0' if v['g'] else 'g0p1'}"] += 1
    out = {"verdicts": total, "per_check": {k: dict(v) for k, v in sorted(per.items())}}
    print(f"{total} panel verdicts without extraction failures")
    print(f"{'check':34s} {'n':>5s} {'differ':>6s} {'by a decision':>13s} {'rest':>5s} {'rest g1p0':>9s} {'rest g0p1':>9s}")
    for k, c in sorted(per.items(), key=lambda kv: -kv[1]["unexplained"]):
        d = c["explained"] + c["unexplained"]
        if d:
            print(f"{k:34s} {c['n']:5d} {d:6d} {c['explained']:13d} {c['unexplained']:5d} "
                  f"{c['unexplained_g1p0']:9d} {c['unexplained_g0p1']:9d}")
    with open(os.path.join(W, "audit", "work", "finding_bounds.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
