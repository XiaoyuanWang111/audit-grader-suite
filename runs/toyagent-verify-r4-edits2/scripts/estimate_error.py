"""Step 6.5: error rates from the two reviewers' labels. Not run in this audit (no reviews exist).

Usage: python -B audit/scripts/estimate_error.py [REVIEWS_A REVIEWS_B [CASE_LIST KEYS]]

Defaults: audit/frozen/round1/reviews_{A,B}.jsonl, audit/frozen/keys/round1_case_list.json and round1_keys.json.
A case has a consensus when both leans agree; an error is a grader verdict that differs from it. Rates are per
stratum over cases with a consensus, weighted by population stratum size, with 95% bootstrap intervals that
resample within strata. A stratum where a grader has no error among n consensus cases raises the upper end by
(stratum share) * (1 - 0.025 ** (1 / n)), the largest such product. Also: rates over cases whose two verdicts are
definite and agree, the paired difference (current minus replacement), Cohen's kappa between leans, and the
disputed cases.
"""

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
args = sys.argv[1:]
RA = args[0] if len(args) > 0 else os.path.join(AUDIT, "frozen", "round1", "reviews_A.jsonl")
RB = args[1] if len(args) > 1 else os.path.join(AUDIT, "frozen", "round1", "reviews_B.jsonl")
CL = args[2] if len(args) > 2 else os.path.join(AUDIT, "frozen", "keys", "round1_case_list.json")
KY = args[3] if len(args) > 3 else os.path.join(AUDIT, "frozen", "keys", "round1_keys.json")
GRADERS = ("current", "replacement")
BOOT, SEED = 10000, 20261111


def load_reviews(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["case_id"]] = r
    return out


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a == "pass" for a, _ in pairs) / n
    pb = sum(b == "pass" for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def weighted(cases_by_stratum, pop, total, err):
    """Population-weighted error rate; ERR maps a case to 0/1."""
    rate = 0.0
    for s, cs in cases_by_stratum.items():
        if cs:
            rate += pop[s] / total * sum(err(c) for c in cs) / len(cs)
    return rate


def main():
    for p in (RA, RB):
        if not os.path.isfile(p):
            sys.exit(f"no review file {p}: step 6.4 has not run")
    a, b = load_reviews(RA), load_reviews(RB)
    with open(CL, encoding="utf-8") as f:
        case_list = json.load(f)
    with open(KY, encoding="utf-8") as f:
        keys = json.load(f)
    pop = case_list["population"]
    total = sum(pop.values())
    ids = [c["case_id"] for c in case_list["cases"]]
    missing = [c for c in ids if c not in a or c not in b]
    if missing:
        sys.exit(f"cases without two labels: {missing}")
    consensus = {c: a[c]["lean"] for c in ids if a[c]["lean"] == b[c]["lean"]}
    disputed = [c for c in ids if c not in consensus]
    definite = {c for c in consensus if a[c]["verdict"] == b[c]["verdict"] == consensus[c]}
    print(f"cases {len(ids)}; consensus {len(consensus)}; disputed {len(disputed)}; definite and agreeing "
          f"{len(definite)}; kappa(leans) {kappa([(a[c]['lean'], b[c]['lean']) for c in ids]):.3f}")
    rng = random.Random(SEED)
    for subset_name, subset in (("consensus", set(consensus)), ("definite", definite)):
        by_s = {s: [c for c in ids if c in subset and keys[c]["stratum"] == s] for s in pop}
        results = {}
        for g in GRADERS:
            def err(c, g=g):
                return int(keys[c][g] != consensus[c])
            point = weighted(by_s, pop, total, err)
            boots = []
            for _ in range(BOOT):
                rs = {s: [cs[rng.randrange(len(cs))] for _ in cs] for s, cs in by_s.items()}
                boots.append(weighted(rs, pop, total, err))
            boots.sort()
            lo, hi = boots[int(0.025 * BOOT)], boots[int(0.975 * BOOT) - 1]
            bump = max([pop[s] / total * (1 - 0.025 ** (1 / len(cs))) for s, cs in by_s.items()
                        if cs and sum(err(c) for c in cs) == 0] or [0.0])
            results[g] = point
            print(f"[{subset_name}] {g}: {100 * point:.1f}% [{100 * lo:.1f}, {100 * (hi + bump):.1f}]"
                  f" (zero-error bump {100 * bump:.1f} points)")
        diffs = []
        for _ in range(BOOT):
            rs = {s: [cs[rng.randrange(len(cs))] for _ in cs] for s, cs in by_s.items()}
            diffs.append(weighted(rs, pop, total, lambda c: int(keys[c]["current"] != consensus[c]))
                         - weighted(rs, pop, total, lambda c: int(keys[c]["replacement"] != consensus[c])))
        diffs.sort()
        print(f"[{subset_name}] current minus replacement: {100 * (results['current'] - results['replacement']):+.1f}"
              f" points [{100 * diffs[int(0.025 * BOOT)]:+.1f}, {100 * diffs[int(0.975 * BOOT) - 1]:+.1f}]")
    for c in disputed:
        print(f"disputed {c}: A {a[c]['verdict']}/{a[c]['lean']}, B {b[c]['verdict']}/{b[c]['lean']}")


if __name__ == "__main__":
    main()
