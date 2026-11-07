"""Score table from audit/panel/panel_results.json: per configuration and pooled.

Change = grader score minus contract (replacement) score, in points, with a 95%
percentile bootstrap interval over trials (pooled: resampled within each
configuration). Seeded.

    python -I audit/scripts/score_summary.py audit/panel/panel_results.json
"""

import json
import random
import sys

SEED = 20261107
REPS = 10000


def main(argv):
    with open(argv[0], encoding="utf-8") as f:
        panel = json.load(f)
    trials = panel["trials"]
    configs = sorted({t["config"] for t in trials})
    by = {c: [(1 if t["grader"] == "pass" else 0, 1 if t["replacement"] == "pass" else 0)
              for t in trials if t["config"] == c] for c in configs}
    rng = random.Random(SEED)
    print(f"{'configuration':<20}{'trials':>7}{'grader':>9}{'contract':>10}{'change':>9}   95% interval   differing trials")
    for c in configs:
        xs = by[c]
        g = 100 * sum(a for a, _ in xs) / len(xs)
        p = 100 * sum(b for _, b in xs) / len(xs)
        boots = sorted(100 * sum(a - b for a, b in (rng.choice(xs) for _ in xs)) / len(xs) for _ in range(REPS))
        lo, hi = boots[int(0.025 * REPS)], boots[int(0.975 * REPS) - 1]
        diff = [t["trial_id"] for t in trials if t["config"] == c and t["grader"] != t["replacement"]]
        print(f"{c:<20}{len(xs):>7}{g:>9.1f}{p:>10.1f}{g - p:>+9.1f}   [{lo:+.1f}, {hi:+.1f}]   {' '.join(diff) or '-'}")
    allx = [x for c in configs for x in by[c]]
    g = 100 * sum(a for a, _ in allx) / len(allx)
    p = 100 * sum(b for _, b in allx) / len(allx)
    boots = []
    for _ in range(REPS):
        s = [rng.choice(by[c]) for c in configs for _ in by[c]]
        boots.append(100 * sum(a - b for a, b in s) / len(s))
    boots.sort()
    print(f"{'all 36 trials':<20}{len(allx):>7}{g:>9.1f}{p:>10.1f}{g - p:>+9.1f}   [{boots[int(0.025 * REPS)]:+.1f}, {boots[int(0.975 * REPS) - 1]:+.1f}]")
    gp = sum(a for a, _ in allx)
    fp = sum(1 for a, b in allx if a == 1 and b == 0)
    print(f"grader passes {gp}, of which contradicted by the contract {fp} ({100 * fp / gp:.1f}%); "
          f"wrong verdicts {fp + sum(1 for a, b in allx if a == 0 and b == 1)} of {len(allx)}")


if __name__ == "__main__":
    main(sys.argv[1:])
