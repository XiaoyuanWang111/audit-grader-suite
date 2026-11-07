"""Step 5: how each grader ranks the checkpoints of the training run.

    python -I -B audit/scripts/trajectory.py

Reads audit/runs/panel_verdicts.jsonl. For each pair of checkpoints, the difference in mean
reward under each grader, with a 95% bootstrap interval that resamples the 12 orders (paired:
the same orders for both checkpoints). Also counts, per checkpoint, the rollouts whose grader
reward depends on each finding or decision. Writes audit/runs/trajectory.json.
"""
import collections
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
BOOT, SEED = 10000, 20261109


def main():
    rows = [json.loads(l) for l in open(ROOT / "audit" / "runs" / "panel_verdicts.jsonl", encoding="utf-8")]
    table = collections.defaultdict(dict)
    for r in rows:
        table[r["checkpoint"]][r["order_id"]] = r
    ckpts = sorted(table)
    orders = sorted(table[ckpts[0]])
    rng = random.Random(SEED)
    out = {"pairs": {}, "per_checkpoint_counts": {}}
    for i, a in enumerate(ckpts):
        for b in ckpts[i + 1:]:
            entry = {}
            for grader in ("grader", "fixes_only", "proposed"):
                d = [table[b][o][grader] - table[a][o][grader] for o in orders]
                means = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(BOOT))
                entry[grader] = {"diff": sum(d) / len(d), "ci95": [means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]]}
            out["pairs"]["%s -> %s" % (a, b)] = entry
    for c in ckpts:
        counts = collections.Counter()
        for o in orders:
            for k in table[c][o]["findings"] + table[c][o]["decisions"]:
                counts[k] += 1
        out["per_checkpoint_counts"][c] = dict(counts)
    (ROOT / "audit" / "runs" / "trajectory.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for pair, entry in out["pairs"].items():
        print("%-24s" % pair + "  ".join("%s %+.3f [%+.3f, %+.3f]" % (g, e["diff"], *e["ci95"]) for g, e in entry.items()))
    print(json.dumps(out["per_checkpoint_counts"]))


if __name__ == "__main__":
    main()
