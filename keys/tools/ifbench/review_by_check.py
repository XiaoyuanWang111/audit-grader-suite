"""Show the IFBench review's round-1 cases of the given checks: stratum, grader, reference and replacement verdicts,
both reviewers' labels and reasons, and the consensus (the lean, when both leans agree).

Joins the frozen key (`frozen/review_round1/key.jsonl`) with the two label files (`frozen/reviews/`) of the audit
directory. Prints no response text. Read-only.

Usage: python -B keys/tools/ifbench/review_by_check.py [--audit runs/ifbench-r3] <reason characters> <check> [...]
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
args = sys.argv[1:]
audit = Path("runs/ifbench-r3")
if args[:1] == ["--audit"]:
    audit, args = Path(args[1]), args[2:]
if len(args) < 2:
    sys.exit(__doc__)
limit = int(args[0])


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def word(verdict: bool) -> str:
    return "pass" if verdict else "fail"


labels = {
    name: {row["case_id"]: row for row in load(audit / "frozen" / "reviews" / f"review_{name}.jsonl")} for name in "AB"
}
rows = load(audit / "frozen" / "review_round1" / "key.jsonl")
for row in rows:
    a, b = labels["A"][row["case_id"]], labels["B"][row["case_id"]]
    row["A"], row["B"] = a, b
    row["consensus"] = a["lean"] if a["lean"] == b["lean"] else None

for check in args[1:]:
    hits = [r for r in rows if r["check"] == check]
    tally = Counter((r["stratum"], word(r["grader"]), word(r["replacement"]), str(r["consensus"])) for r in hits)
    print(f"=== {check}: {len(hits)} reviewed cases")
    for (stratum, grader, replacement, consensus), count in sorted(tally.items()):
        print(f"    {stratum} grader={grader} replacement={replacement} consensus={consensus}: {count}")
    for r in hits:
        if r["grader"] == r["replacement"] and r["consensus"] == word(r["grader"]):
            continue
        a, b = r["A"], r["B"]
        print(
            f"  - {r['case_id']} {r['stratum']} key {r['key']} grader={word(r['grader'])} ref={word(r['reference'])}"
            f" repl={word(r['replacement'])} consensus={r['consensus']} alt={r.get('replacement_alt')}\n"
            f"      A {a['verdict']}/{a['lean']}/{a['confidence']}: {a['reason'][:limit]}\n"
            f"      B {b['verdict']}/{b['lean']}/{b['confidence']}: {b['reason'][:limit]}"
        )
