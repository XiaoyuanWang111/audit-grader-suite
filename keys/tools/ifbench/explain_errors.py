"""Sort the IFBench review's grader errors by whether a decision switch of the replacement grader accounts for them.

An error is a case where a grader's verdict differs from the reviewers' consensus. The frozen key stores, per case,
the replacement's verdict under every alternative reading that applies to the case's check (`replacement_alt`, for
example {"D-vacuous:B": true}), whether or not it changes the verdict. A replacement error is "explained by a
decision" when some stored alternative reading gives the consensus verdict. Read-only.

Usage: python -B keys/tools/ifbench/explain_errors.py [--audit runs/ifbench-r3]
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--audit", type=Path, default=REPO / "runs" / "ifbench-r3", help="the run's audit directory")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
ROUND = args.audit / "frozen" / "review_round1"
REVIEWS = args.audit / "frozen" / "reviews"


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


key = {record["case_id"]: record for record in load(ROUND / "key.jsonl")}
strata = json.loads((ROUND / "strata.json").read_text(encoding="utf-8"))["strata"]
labels = {x: {r["case_id"]: r for r in load(REVIEWS / f"review_{x}.jsonl")} for x in "AB"}
A, B = labels["A"], labels["B"]
consensus = {c: A[c]["lean"] == "pass" for c in key if A[c]["lean"] == B[c]["lean"]}
definite = {c for c in consensus if A[c]["verdict"] != "ambiguous" and B[c]["verdict"] != "ambiguous"}
population = sum(v["population"] for v in strata.values())

alt_names = Counter()
for record in key.values():
    for name in record["replacement_alt"]:
        alt_names[name] += 1
print(
    f"alternative readings stored in the key ({sum(1 for r in key.values() if r['replacement_alt'])} of {len(key)} "
    "cases have one):"
)
for name, count in alt_names.most_common():
    print(f"   {name:34s} {count}")

print("\n=== replacement differs from the consensus")
rows = defaultdict(Counter)
unexplained = []
for case, truth in consensus.items():
    record = key[case]
    if record["replacement"] == truth:
        continue
    fixing = sorted(name for name, verdict in record["replacement_alt"].items() if verdict == truth)
    bucket = "explained by " + "+".join(fixing) if fixing else "no alternative reading gives the consensus"
    rows[(record["check"], bucket)][record["stratum"]] += 1
    rows[(record["check"], bucket)]["definite" if case in definite else "one or both ambiguous"] += 1
    if not fixing:
        unexplained.append(case)
for (check, bucket), counter in sorted(rows.items()):
    print(f"   {check:30s} {bucket:58s} {dict(counter)}")
total = sum(1 for c, t in consensus.items() if key[c]["replacement"] != t)
print(
    f"replacement errors {total}; explained by a stored alternative {total - len(unexplained)}; "
    f"unexplained {len(unexplained)}: {sorted(unexplained)}"
)

print(
    "\n=== grader (strict) differs from the consensus, by stratum and by whether the replacement agrees with the "
    "consensus"
)
table = Counter()
for case, truth in consensus.items():
    record = key[case]
    if record["grader"] != truth:
        table[
            (record["stratum"], "replacement right" if record["replacement"] == truth else "replacement also wrong")
        ] += 1
for item, count in sorted(table.items()):
    print(f"   {item}: {count}")

print("\n=== where the consensus sides with the grader against the replacement, by check: cases, of which both definite")
side = defaultdict(Counter)
for case, truth in consensus.items():
    record = key[case]
    if record["stratum"] in ("S1a", "S1b"):
        winner = "grader" if record["grader"] == truth else "replacement"
        side[record["check"]][winner] += 1
        if case in definite:
            side[record["check"]][winner + " definite"] += 1
for check, counter in sorted(side.items(), key=lambda item: -(item[1]["grader"])):
    if counter["grader"]:
        print(
            f"   {check:32s} grader right {counter['grader']:3d} (definite {counter['grader definite']:3d}); "
            f"replacement right {counter['replacement']:3d} (definite {counter['replacement definite']:3d})"
        )
