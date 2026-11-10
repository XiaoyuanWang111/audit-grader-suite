"""Acceptance check of the two blinded reviewers' label files in the IFBench rerun.

Checks the format (458 lines, every case once, the five fields with valid values, at most 40 words of reason), the
prompt's no-quoting rule (no reason copies more than ten consecutive words of the case), independence between the two
files (identical or near-identical reasons), and prints the agreement tables with Cohen's kappa. The run checked the
reviewers' own copies before handing them to the auditor; the copies in the audit's `frozen/reviews/` are
byte-identical. Read-only.

Usage: python -B keys/tools/ifbench/check_reviews.py [--audit runs/ifbench-r3]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--audit", type=Path, default=REPO / "runs" / "ifbench-r3", help="the run's audit directory")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
ROUND = args.audit / "frozen" / "review_round1"
REVIEWS = args.audit / "frozen" / "reviews"
FIELDS = ["case_id", "verdict", "lean", "confidence", "reason"]
VERDICTS = ("pass", "fail", "ambiguous")
LEANS = ("pass", "fail")
CONFIDENCE = ("high", "medium", "low")
WORD = re.compile(r"[A-Za-z0-9']+")


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    labels = sorted({label for pair in pairs for label in pair})
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[label] * right[label] for label in labels) / (n * n)
    return (observed - expected) / (1 - expected) if expected < 1 else float("nan")


cases = {record["case_id"]: record for record in load(ROUND / "review_cases.jsonl")}
strata = {record["case_id"]: record["stratum"] for record in load(ROUND / "cases.jsonl")}
print(f"review cases: {len(cases)}; fields shown to reviewers: {sorted(next(iter(cases.values())))}")
assert set(cases) == set(strata)

labels = {}
problems = 0
for letter in "AB":
    path = REVIEWS / f"review_{letter}.jsonl"
    raw = path.read_bytes()
    lines = raw.decode("utf-8").split("\n")
    print(
        f"\n=== review_{letter}.jsonl: {len(raw):,} bytes, CR bytes {raw.count(b'\r')}, "
        f"ends with newline {raw.endswith(b'\n')}"
    )
    records = [json.loads(line) for line in lines if line.strip()]
    blank = sum(1 for line in lines[:-1] if not line.strip())
    ids = [record.get("case_id") for record in records]
    duplicates = [case for case, count in Counter(ids).items() if count > 1]
    missing = sorted(set(cases) - set(ids))
    extra = sorted(set(ids) - set(cases))
    bad_keys = [record.get("case_id") for record in records if list(record) != FIELDS]
    bad_values = [
        record["case_id"]
        for record in records
        if record.get("verdict") not in VERDICTS
        or record.get("lean") not in LEANS
        or record.get("confidence") not in CONFIDENCE
    ]
    mismatched = [r["case_id"] for r in records if r.get("verdict") in LEANS and r.get("lean") != r.get("verdict")]
    long_reasons = [
        (r["case_id"], len(r["reason"].split())) for r in records if len(str(r.get("reason", "")).split()) > 40
    ]
    empty = [r["case_id"] for r in records if not str(r.get("reason", "")).strip()]
    print(
        f"records {len(records)}, blank lines inside {blank}, duplicates {len(duplicates)}, missing {len(missing)}, "
        f"unknown ids {len(extra)}"
    )
    print(
        f"wrong field list {len(bad_keys)}, invalid values {len(bad_values)}, "
        f"definite verdict with a different lean {len(mismatched)}"
    )
    print(f"reasons over 40 words {len(long_reasons)} {long_reasons[:8]}, empty reasons {len(empty)}")
    problems += (
        blank
        + len(duplicates)
        + len(missing)
        + len(extra)
        + len(bad_keys)
        + len(bad_values)
        + len(mismatched)
        + len(empty)
    )
    by = {record["case_id"]: record for record in records}
    labels[letter] = by
    print(
        "verdicts:", dict(Counter(r["verdict"] for r in records)), "| leans:", dict(Counter(r["lean"] for r in records))
    )
    print("confidence:", dict(Counter(r["confidence"] for r in records)))
    print("ambiguous leans:", dict(Counter(r["lean"] for r in records if r["verdict"] == "ambiguous")))
    words = [len(r["reason"].split()) for r in records]
    digits = sum(1 for r in records if re.search(r"\d", r["reason"]))
    print(
        f"reason words: median {sorted(words)[len(words) // 2]}, max {max(words)}; "
        f"reasons with a number {digits} ({digits / len(records):.0%})"
    )
    # No-quoting rule: more than ten consecutive words of the case text inside the reason.
    copied = []
    for record in records:
        case = cases.get(record["case_id"])
        if not case:
            continue
        source = " ".join(WORD.findall((case["response"] + " " + case["prompt"]).lower()))
        tokens = WORD.findall(record["reason"].lower())
        for start in range(0, max(0, len(tokens) - 10)):
            if " " + " ".join(tokens[start : start + 11]) + " " in " " + source + " ":
                copied.append(record["case_id"])
                break
    print(f"reasons copying more than ten consecutive words of the case: {len(copied)} {copied[:6]}")
    by_stratum = Counter((strata[r["case_id"]], r["verdict"]) for r in records if r["case_id"] in strata)
    for stratum in sorted({s for s, _ in by_stratum}):
        print(f"   {stratum}: " + ", ".join(f"{verdict} {by_stratum[(stratum, verdict)]}" for verdict in VERDICTS))

a, b = labels["A"], labels["B"]
shared = [case for case in cases if case in a and case in b]
print(f"\n=== A against B on {len(shared)} cases")
lean_pairs = [(a[c]["lean"], b[c]["lean"]) for c in shared]
verdict_pairs = [(a[c]["verdict"], b[c]["verdict"]) for c in shared]
table = Counter(lean_pairs)
print("leans      B pass  B fail")
for left in LEANS:
    print(f"  A {left:5s} {table[(left, 'pass')]:6d} {table[(left, 'fail')]:7d}")
agree = sum(x == y for x, y in lean_pairs)
print(f"lean agreement {agree}/{len(shared)} = {agree / len(shared):.1%}; Cohen's kappa (leans) {kappa(lean_pairs):.3f}")
table = Counter(verdict_pairs)
print("verdicts      B pass  B fail  B ambiguous")
for left in VERDICTS:
    print(f"  A {left:9s} {table[(left, 'pass')]:5d} {table[(left, 'fail')]:7d} {table[(left, 'ambiguous')]:8d}")
print(f"Cohen's kappa (three verdicts) {kappa(verdict_pairs):.3f}")
definite = [c for c in shared if a[c]["verdict"] in LEANS and b[c]["verdict"] in LEANS]
definite_agree = [c for c in definite if a[c]["verdict"] == b[c]["verdict"]]
either_ambiguous = [c for c in shared if "ambiguous" in (a[c]["verdict"], b[c]["verdict"])]
print(
    f"both definite {len(definite)}, of which agree {len(definite_agree)}; "
    f"either reviewer ambiguous {len(either_ambiguous)} ({len(either_ambiguous) / len(shared):.1%})"
)
print("by stratum: cases, consensus (leans agree), disputed, kappa (leans), both definite and agree")
for stratum in sorted(set(strata.values())):
    members = [c for c in shared if strata[c] == stratum]
    pairs = [(a[c]["lean"], b[c]["lean"]) for c in members]
    consensus = sum(x == y for x, y in pairs)
    kap = kappa(pairs) if len({p for pair in pairs for p in pair}) > 1 else float("nan")
    both = sum(1 for c in members if c in set(definite_agree))
    print(f"   {stratum}: {len(members)}, {consensus}, {len(members) - consensus}, {kap:.3f}, {both}")
same = [c for c in shared if a[c]["reason"].strip().lower() == b[c]["reason"].strip().lower()]
overlap = []
for c in shared:
    left, right = set(WORD.findall(a[c]["reason"].lower())), set(WORD.findall(b[c]["reason"].lower()))
    overlap.append(len(left & right) / max(1, len(left | right)))
overlap.sort()
print(
    f"identical reasons {len(same)}; word-set overlap of the two reasons per case: "
    f"median {overlap[len(overlap) // 2]:.2f}, "
    f"95th percentile {overlap[int(len(overlap) * 0.95)]:.2f}, max {overlap[-1]:.2f}"
)
order = {letter: [record["case_id"] for record in load(REVIEWS / f"review_{letter}.jsonl")] for letter in "AB"}
print(f"A and B wrote the cases in the same order: {order['A'] == order['B']}")
print(f"\nformat problems: {problems}")
