"""Derive, per instruction id, the readings of the decision entries that each grader follows.

For each check and grader, every assignment of readings (A or B) to the check's switchable decision
entries is tried on all fixtures of that check, and the assignment under which the replacement agrees
with the grader on the most fixtures is kept (ties: fewer B readings). "Fixes only" is the replacement
run with these readings: its differences from the grader are then defect fixes, not reading changes.
Writes audit/results/official_readings.json.
"""
import collections
import itertools
import json
import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
import fixture_lib as F  # noqa: E402
import graders as G  # noqa: E402

E = json.load(open(os.path.join(AUDIT, "tests", "expectations.json"), encoding="utf-8"))
by_iid = collections.defaultdict(list)
for line in open(os.path.join(AUDIT, "fixtures.jsonl"), encoding="utf-8"):
    f = json.loads(line)
    if f.get("thinking") is not None:
        continue
    by_iid[f["instruction_id"]].append(f)

official = {"A": {}, "B": {}}
report = {}
for iid, fixtures in sorted(by_iid.items()):
    decisions = [d for d in F.COMMON + F.RELEVANT[iid] if d not in F.UNSWITCHED]
    for g in "AB":
        rows = [(f, E[f["id"]][g]) for f in fixtures if E[f["id"]][g] is not None]
        if not rows:
            continue
        best = None
        for size in range(0, len(decisions) + 1):
            for combo in itertools.combinations(decisions, size):
                readings = {d: "B" for d in combo}
                agree = sum(G.check_r(iid, f["kwargs"], f["response"], readings) == v for f, v in rows)
                if best is None or agree > best[0]:
                    best = (agree, combo)
        official[g][iid] = {d: "B" for d in best[1]}
        report[f"{g} {iid}"] = f"{sorted(best[1])} agrees on {best[0]}/{len(rows)}"
json.dump(official, open(os.path.join(AUDIT, "results", "official_readings.json"), "w", encoding="utf-8"),
          indent=1, sort_keys=True)
for k, v in report.items():
    print(k, v)
