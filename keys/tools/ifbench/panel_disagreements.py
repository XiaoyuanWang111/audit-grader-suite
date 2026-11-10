"""Count, per check, the panel verdicts on which the IFBench audit's replacement differs from the grader, and list the
finding and decision ids that the audit's fixtures record for that check. A check with disagreements in a direction
that no recorded finding covers is where an unreported defect can hide.

Reads the audit's panel verdicts (`work/panel_verdicts.jsonl` in the audit directory, plain or gzip-compressed) and
the `fixture_repro.json` that `fixture_repro.py` writes. Read-only.

Usage: python -B keys/tools/ifbench/panel_disagreements.py <panel_verdicts.jsonl[.gz]> <fixture_repro.json> [check ...]
"""

import collections
import gzip
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 3:
    sys.exit(__doc__)
VERDICTS, FIXTURE_REPRO = Path(sys.argv[1]), Path(sys.argv[2])
only = set(sys.argv[3:])

recorded = collections.defaultdict(lambda: {"pass_wrong": set(), "fail_wrong": set()})
for row in json.loads(FIXTURE_REPRO.read_text(encoding="utf-8"))["rows"]:
    if not row["recorded_grader"]:
        continue
    # label pass and grader wrong means the grader failed a response that should pass.
    side = "fail_wrong" if row["label"] == "pass" else "pass_wrong"
    for reason in str(row["recorded_grader"]).replace(";", ",").split(","):
        if reason.strip():
            recorded[row["check"]][side].add(reason.strip())

counts = collections.defaultdict(collections.Counter)
first = None
opener = gzip.open if VERDICTS.suffix == ".gz" else open
with opener(VERDICTS, "rt", encoding="utf-8") as handle:
    for line in handle:
        r = json.loads(line)
        if first is None:
            first = sorted(r)
        if r.get("extraction_failure"):
            counts[r["iid"]]["extraction_failure"] += 1
            continue
        c = counts[r["iid"]]
        c["n"] += 1
        if r["g"] and not r["p"]:
            c["g_pass_p_fail"] += 1
            c["g_pass_p_fail_heldout"] += bool(r.get("heldout"))
        elif not r["g"] and r["p"]:
            c["g_fail_p_pass"] += 1
            c["g_fail_p_pass_heldout"] += bool(r.get("heldout"))
print("row fields:", first)
print(
    f"{'check':34s} {'n':>6s} {'g+ p-':>6s} {'(held)':>6s} {'g- p+':>6s} {'(held)':>6s}  "
    "recorded for g+ wrong | recorded for g- wrong"
)
tot = collections.Counter()
for check in sorted(counts):
    c = counts[check]
    tot.update({k: v for k, v in c.items()})
    if only and check not in only:
        continue
    rec = recorded.get(check, {"pass_wrong": set(), "fail_wrong": set()})
    flag = ""
    if c["g_pass_p_fail"] and not rec["pass_wrong"]:
        flag += " <-- g+ p- with no recorded reason"
    if c["g_fail_p_pass"] and not rec["fail_wrong"]:
        flag += " <-- g- p+ with no recorded reason"
    print(
        f"{check:34s} {c['n']:6d} {c['g_pass_p_fail']:6d} {c['g_pass_p_fail_heldout']:6d} {c['g_fail_p_pass']:6d} "
        f"{c['g_fail_p_pass_heldout']:6d}  "
        f"{','.join(sorted(rec['pass_wrong'])) or '-'} | {','.join(sorted(rec['fail_wrong'])) or '-'}{flag}"
    )
print("total:", dict(tot))
