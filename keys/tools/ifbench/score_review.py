"""Score the IFBench rerun's blinded review independently of the audit's own analysis.

Gives the error rate of each grader against the reviewers' consensus labels and against the labels where both
verdicts are definite and agree, with two intervals: the merged skill's (percentile bootstrap within strata) and the
follow-up's (the upper end raised by the largest share-times-exact-limit product among a grader's zero-error strata).
Reads the frozen key and strata (`frozen/review_round1/`) and the two label files (`frozen/reviews/`) of the audit
directory. Writes `my_review_scores.json` and `handcheck_cases.txt` into the output folder; the second file lists the
cases to check by hand (the consensus contradicts the replacement; the consensus contradicts a verdict that grader
and replacement share in S2 or S3; disputed cases), with response excerpts whose think blocks are cut.

Usage: python -B keys/tools/ifbench/score_review.py <output folder> [--audit runs/ifbench-r3] [--boot 10000]
"""

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("out", type=Path, help="output folder")
parser.add_argument("--audit", type=Path, default=REPO / "runs" / "ifbench-r3", help="the run's audit directory")
parser.add_argument("--boot", type=int, default=10000, help="bootstrap replicates")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
OUT = args.out
BOOT = args.boot
ROUND = args.audit / "frozen" / "review_round1"
REVIEWS = args.audit / "frozen" / "reviews"
GRADERS = ["grader", "grader_loose", "reference", "reference_loose", "replacement"]
NAMES = {
    "grader": "grader strict",
    "grader_loose": "grader loose",
    "reference": "reference strict",
    "reference_loose": "reference loose",
    "replacement": "replacement",
}


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


key = {record["case_id"]: record for record in load(ROUND / "key.jsonl")}
shown = {record["case_id"]: record for record in load(ROUND / "review_cases.jsonl")}
strata = json.loads((ROUND / "strata.json").read_text(encoding="utf-8"))["strata"]
labels = {x: {r["case_id"]: r for r in load(REVIEWS / f"review_{x}.jsonl")} for x in "AB"}
A, B = labels["A"], labels["B"]
ids = sorted(key)
assert set(ids) == set(A) == set(B) == set(shown) and len(ids) == 458
population = sum(v["population"] for v in strata.values())
weight = {s: v["population"] / population for s, v in strata.items()}
members = defaultdict(list)
for case in ids:
    members[key[case]["stratum"]].append(case)
assert all(len(members[s]) == strata[s]["sample"] for s in strata)

consensus = {c: A[c]["lean"] for c in ids if A[c]["lean"] == B[c]["lean"]}
definite = {c: A[c]["verdict"] for c in ids if A[c]["verdict"] == B[c]["verdict"] != "ambiguous"}


def wrong(case: str, grader: str, truth: dict) -> int:
    return int(("pass" if key[case][grader] else "fail") != truth[case])


def rate(draw: dict, grader: str, truth: dict) -> float:
    total = 0.0
    for stratum, cases in draw.items():
        judged = [c for c in cases if c in truth]
        if judged:
            total += weight[stratum] * sum(wrong(c, grader, truth) for c in judged) / len(judged)
    return total


def percentile(values: list[float]) -> tuple[float, float]:
    values = sorted(values)
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


print(f"population {population:,}; shares " + ", ".join(f"{s} {weight[s]:.4f}" for s in sorted(weight)))
print(
    f"cases {len(ids)}, consensus {len(consensus)}, both definite and agree {len(definite)}, "
    f"bootstrap replicates {BOOT:,}"
)
results = {}
for name, truth in (("consensus", consensus), ("definite", definite)):
    rng = random.Random(10060)
    draws = [{s: [rng.choice(cases) for _ in cases] for s, cases in members.items()} for _ in range(BOOT)]
    print(f"\n=== error rates against the {name} labels ({len(truth)} cases)")
    print("per stratum: errors / cases with a label")
    for stratum in sorted(members):
        judged = [c for c in members[stratum] if c in truth]
        print(
            f"   {stratum} (share {weight[stratum]:.4f}, sample {len(members[stratum])}, labeled {len(judged)}): "
            + ", ".join(f"{NAMES[g]} {sum(wrong(c, g, truth) for c in judged)}" for g in GRADERS)
        )
    results[name] = {}
    for grader in GRADERS:
        point = rate(members, grader, truth)
        low, high = percentile([rate(draw, grader, truth) for draw in draws])
        products = []
        for stratum in members:
            judged = [c for c in members[stratum] if c in truth]
            if judged and not any(wrong(c, grader, truth) for c in judged):
                products.append((weight[stratum] * (1 - 0.025 ** (1 / len(judged))), stratum, len(judged)))
        add = max(products)[0] if products else 0.0
        results[name][grader] = {
            "rate": point,
            "boot": [low, high],
            "zero_error_strata": [(s, n, round(p, 6)) for p, s, n in products],
            "upper_new_rule": high + add,
        }
        note = ""
        if products:
            note = f"; zero-error strata {[(s, n) for _, s, n in products]}, upper end by the new rule {high + add:.2%}"
        print(f"   {NAMES[grader]:16s} {point:6.2%}  bootstrap [{low:.2%}, {high:.2%}]{note}")
    for other in ("replacement", "reference"):
        diffs = [rate(draw, "grader", truth) - rate(draw, other, truth) for draw in draws]
        low, high = percentile(diffs)
        point = rate(members, "grader", truth) - rate(members, other, truth)
        results[name][f"grader_minus_{other}"] = {"diff": point, "boot": [low, high]}
        print(f"   grader strict minus {NAMES[other]}: {point:+.2%}  bootstrap [{low:+.2%}, {high:+.2%}]")

# Per check, consensus labels.
per_check = defaultdict(Counter)
for case in consensus:
    counter = per_check[key[case]["check"]]
    counter["n"] += 1
    for grader in ("grader", "reference", "replacement"):
        counter[grader] += wrong(case, grader, consensus)
print("\n=== per check with an error (consensus cases): n, grader, reference, replacement")
for check, counter in sorted(per_check.items(), key=lambda item: (-item[1]["grader"], item[0])):
    if counter["grader"] or counter["replacement"] or counter["reference"]:
        print(
            f"   {check:36s} {counter['n']:3d} {counter['grader']:3d} {counter['reference']:3d} "
            f"{counter['replacement']:3d}"
        )
print(f"checks in the sample: {len({key[c]['check'] for c in ids})}; with a consensus case: {len(per_check)}")

THINK = re.compile(r"<think>.*?</think>", re.S)


def excerpt(text: str, limit: int) -> str:
    text = THINK.sub("[think block cut]", text)
    if "<think>" in text:
        text = text[: text.index("<think>")] + "[unclosed think block cut]"
    text = text.replace(chr(13), "")
    return text if len(text) <= limit else text[:limit] + f" ...[{len(text) - limit:,} more characters]"


def describe(case: str, limit: int = 900) -> str:
    record, case_shown = key[case], shown[case]
    lines = [
        f"##### {case} | {record['stratum']} | {record['check']} | key {record['key']} j {record['j']} | "
        f"{record['cfg']} {record['run']} | finish {record['finish_reason']}",
        f"verdicts: grader {record['grader']} (loose {record['grader_loose']}), reference {record['reference']} "
        f"(loose {record['reference_loose']}), replacement {record['replacement']}, "
        f"alternatives {record['replacement_alt']}",
        f"consensus: {consensus.get(case, 'DISPUTED')}",
        f"   A {A[case]['verdict']}/{A[case]['lean']}/{A[case]['confidence']}: {A[case]['reason']}",
        f"   B {B[case]['verdict']}/{B[case]['lean']}/{B[case]['confidence']}: {B[case]['reason']}",
        f"requirement: {excerpt(str(case_shown['requirement']), 700)}",
        f"response ({len(case_shown['response']):,} characters): {excerpt(case_shown['response'], limit)!r}",
        "",
    ]
    return "\n".join(lines)


groups = {
    "replacement contradicts the consensus": [c for c in ids if c in consensus and wrong(c, "replacement", consensus)],
    "S2 and S3: the consensus contradicts the verdict that grader and replacement share": [
        c for c in ids if c in consensus and key[c]["stratum"] in ("S2", "S3") and wrong(c, "grader", consensus)
    ],
    "disputed (leans differ)": [c for c in ids if c not in consensus],
}
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "handcheck_cases.txt", "w", encoding="utf-8", newline="\n") as handle:
    for title, cases in groups.items():
        by_stratum = Counter(key[c]["stratum"] for c in cases)
        by_check = Counter(key[c]["check"] for c in cases)
        print(f"\n=== {title}: {len(cases)} {dict(by_stratum)}")
        print("   by check: " + ", ".join(f"{check} {count}" for check, count in by_check.most_common()))
        handle.write(f"\n################ {title}: {len(cases)}\n\n")
        for case in sorted(cases, key=lambda c: (key[c]["check"], c)):
            handle.write(describe(case) + "\n")
(OUT / "my_review_scores.json").write_text(json.dumps(results, indent=1), encoding="utf-8", newline="\n")
print(f"\nwrote {OUT / 'handcheck_cases.txt'} and my_review_scores.json")
