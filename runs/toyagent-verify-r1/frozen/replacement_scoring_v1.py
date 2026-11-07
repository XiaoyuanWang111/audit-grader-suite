"""Replacement scoring for count-server-errors, written from audit/CONTRACT.md.

Reward 1 only when verifier_exit_code is the integer 0; 0 for any other value,
null, or an absent field. Score = mean reward over every trial of a config.

    python replacement_scoring.py [TRIALS_DIR]
"""

import json
import os
import sys
from collections import defaultdict


def reward(result):
    code = result.get("verifier_exit_code")
    return 1 if type(code) is int and code == 0 else 0


def scores(results):
    by_config = defaultdict(list)
    for r in results:
        by_config[r["config"]].append(reward(r))
    return {c: (len(rs), sum(rs), sum(rs) / len(rs)) for c, rs in sorted(by_config.items())}


def load(trials_dir):
    out = []
    for name in sorted(os.listdir(trials_dir)):
        path = os.path.join(trials_dir, name, "result.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def main(argv):
    trials_dir = argv[0] if argv else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "case", "trials")
    print(f"{'config':<22}{'trials':>7}{'passed':>8}{'score':>8}")
    for c, (n, p, s) in scores(load(trials_dir)).items():
        print(f"{c:<22}{n:>7}{p:>8}{s:>8.3f}")


if __name__ == "__main__":
    main(sys.argv[1:])
