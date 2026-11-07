"""Step 5 preparation: set aside held-out rollouts before the panel is graded or read.

    python -I audit/scripts/heldout_split.py

For each checkpoint, draws 6 of its 12 rollouts as held out, with random.Random(SEED), and
writes audit/frozen/heldout_split.json. Only rollout ids, checkpoints and order ids are read;
the response texts are not.
"""
import json
import pathlib
import random

SEED = 20261106
ROOT = pathlib.Path(__file__).resolve().parents[2]


def main():
    rows = [json.loads(line) for line in (ROOT / "case" / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    by_ckpt = {}
    for r in rows:
        by_ckpt.setdefault(r["checkpoint"], []).append(r["id"])
    rng = random.Random(SEED)
    heldout = []
    for ckpt in sorted(by_ckpt):
        ids = sorted(by_ckpt[ckpt])
        heldout.extend(sorted(rng.sample(ids, len(ids) // 2)))
    heldout_set = set(heldout)
    out = {
        "seed": SEED,
        "rule": "per checkpoint, random.Random(seed).sample(sorted ids, 6), checkpoints in sorted order",
        "heldout": sorted(heldout),
        "development": sorted(r["id"] for r in rows if r["id"] not in heldout_set),
    }
    path = ROOT / "audit" / "frozen" / "heldout_split.json"
    path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("held out:", len(out["heldout"]), out["heldout"])
    print("development:", len(out["development"]))


if __name__ == "__main__":
    main()
