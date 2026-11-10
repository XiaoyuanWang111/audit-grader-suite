"""The earlier IFBench audit's blinded review, from its public data: per review round, stratum and grader, the number
of consensus cases and errors, the bootstrap interval of the weighted error rate, and what the zero-error rule of the
step-6 follow-up changes.

Reads `blind_review.jsonl` and `blind_review_strata.jsonl` from the `data/` folder of the Hugging Face dataset
xiaoyuanwang/ifbench-audit. Read-only.

Usage: python -B keys/tools/ifbench/zero_error_strata.py <data folder>
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit(__doc__)
DATA = Path(sys.argv[1])
rows = [
    json.loads(line) for line in (DATA / "blind_review.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
]
strata = [
    json.loads(line)
    for line in (DATA / "blind_review_strata.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
population = {(s["round"], s["stratum"]): s["population"] for s in strata}
GRADERS = ("marin_strict", "fixes_only", "proposed")


def verdict(value):
    if isinstance(value, bool):
        return "pass" if value else "fail"
    return value


for rnd in (1, 2):
    cases = defaultdict(list)
    for row in rows:
        if row["round"] == rnd and row["source"] == "panel" and row["consensus"] in ("pass", "fail"):
            cases[row["stratum"]].append(row)
    total = sum(population[(rnd, s)] for s in cases)
    print(f"\n=== round {rnd}: strata {[(s, population[(rnd, s)], len(c)) for s, c in cases.items()]}")
    for grader in GRADERS:
        point = 0.0
        parts = {}
        for stratum, items in cases.items():
            errors = sum(verdict(r[grader]) != r["consensus"] for r in items)
            parts[stratum] = (errors, len(items))
            point += population[(rnd, stratum)] / total * errors / len(items)
        rng = random.Random(10060)
        draws = []
        for _ in range(4000):
            value = 0.0
            for stratum, items in cases.items():
                sample = rng.choices(items, k=len(items))
                value += (
                    population[(rnd, stratum)]
                    / total
                    * sum(verdict(r[grader]) != r["consensus"] for r in sample)
                    / len(items)
                )
            draws.append(value)
        draws.sort()
        low, high = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
        added = 0.0
        for stratum, (errors, n) in parts.items():
            if errors == 0:
                added += population[(rnd, stratum)] / total * (1 - 0.025 ** (1 / n))
        print(
            f"  {grader:13s} errors/consensus per stratum {parts}  rate {100 * point:.2f}%  "
            f"bootstrap [{100 * low:.2f}, {100 * high:.2f}]"
            f"  with the zero-error bound: upper {100 * (high + added):.2f}"
        )
