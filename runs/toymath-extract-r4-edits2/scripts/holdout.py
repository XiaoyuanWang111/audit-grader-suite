"""Set aside held-out panel responses before the replacement grader sees the panel.

For each model, draw 6 of its 12 responses with a fixed seed. The drawn ids are
held out: no change to the replacement grader may be based on them. Uses only
the `id` and `model` fields, so it reads no response text.

Run from W:  python -B audit/scripts/holdout.py
Writes audit/frozen/holdout_ids.txt (one id per line, sorted) and prints its sha256.
"""
import hashlib
import json
import pathlib
import random

W = pathlib.Path(__file__).resolve().parents[2]
SEED = 20261111
PER_MODEL = 6


def main():
    rows = [json.loads(l) for l in (W / "case" / "responses.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_model = {}
    for r in rows:
        by_model.setdefault(r["model"], []).append(r["id"])
    rng = random.Random(SEED)
    held = []
    for model in sorted(by_model):
        ids = sorted(by_model[model])
        held.extend(rng.sample(ids, PER_MODEL))
    held.sort()
    out = W / "audit" / "frozen" / "holdout_ids.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(i + "\n" for i in held), encoding="utf-8", newline="\n")
    print(f"seed {SEED}, {PER_MODEL} per model, {len(held)} held out of {len(rows)}")
    print(" ".join(held))
    print("sha256", hashlib.sha256(out.read_bytes()).hexdigest(), out.relative_to(W).as_posix())


if __name__ == "__main__":
    main()
