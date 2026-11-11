"""Replacement scorer for count-server-errors, written from audit/CONTRACT.md (check S).

Usage:
    python score_trials.py TRIALS_DIR

Every trial directory counts in its configuration's denominator. Reward is 1 only when verifier_exit_code is
the integer 0; null, a missing field, any other code, or a trial directory without a readable result.json
gives 0. A trial without a readable result.json cannot be attributed to a configuration, so it is listed
under "<unattributed>" instead of being dropped.
"""

import json
import os
import sys
from collections import defaultdict


def trial_reward(result):
    code = result.get("verifier_exit_code")
    return 1.0 if (type(code) is int and code == 0) else 0.0


def load_results(trials_dir):
    out = []
    for name in sorted(os.listdir(trials_dir)):
        d = os.path.join(trials_dir, name)
        if not os.path.isdir(d):
            continue
        path = os.path.join(d, "result.json")
        try:
            with open(path, encoding="utf-8") as f:
                result = json.load(f)
            if not isinstance(result, dict):
                raise ValueError("result.json is not an object")
        except (OSError, ValueError) as e:
            result = {"config": "<unattributed>", "verifier_exit_code": None, "_load_error": type(e).__name__}
        out.append(result)
    return out


def scores(results):
    rewards = defaultdict(list)
    for result in results:
        rewards[str(result.get("config", "<unattributed>"))].append(trial_reward(result))
    return {c: (len(rs), int(sum(rs)), 100.0 * sum(rs) / len(rs)) for c, rs in rewards.items()}


def main(argv):
    trials_dir = argv[0]
    table = scores(load_results(trials_dir))
    print(f"{'config':<22}{'trials':>7}{'passed':>8}{'score':>8}")
    for config in sorted(table):
        n, p, s = table[config]
        print(f"{config:<22}{n:>7}{p:>8}{s:>8.1f}")


if __name__ == "__main__":
    main(sys.argv[1:])
