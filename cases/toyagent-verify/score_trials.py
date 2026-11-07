"""Score stored trials of the count-server-errors task from their result.json files.

Usage:
    python score_trials.py [TRIALS_DIR]

Prints, per agent configuration, the number of trials, the number that passed, and the score.
"""

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def trial_reward(result):
    exit_code = result.get("verifier_exit_code")
    return 0.0 if exit_code else 1.0


def load_results(trials_dir):
    results = []
    for name in sorted(os.listdir(trials_dir)):
        path = os.path.join(trials_dir, name, "result.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                results.append(json.load(f))
    return results


def main(argv):
    trials_dir = argv[0] if argv else os.path.join(HERE, "trials")
    rewards = defaultdict(list)
    for result in load_results(trials_dir):
        rewards[result["config"]].append(trial_reward(result))
    print(f"{'config':<22}{'trials':>7}{'passed':>8}{'score':>8}")
    for config in sorted(rewards):
        rs = rewards[config]
        print(f"{config:<22}{len(rs):>7}{int(sum(rs)):>8}{100.0 * sum(rs) / len(rs):>8.1f}")


if __name__ == "__main__":
    main(sys.argv[1:])
