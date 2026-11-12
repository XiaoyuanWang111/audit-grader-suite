"""Set aside held-out panel responses before the panel verdicts are read (skill step 5).

A response is held out when int(sha256("heldout-v1|<run>|<uuid>")[:8], 16) % 4 == 0 (about 25% of
every run file). Writes audit/frozen/heldout_v1.txt (run<TAB>uuid, sorted) and prints its sha256.
"""
import glob
import hashlib
import json
import os

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)


def is_heldout(run: str, uuid: str) -> bool:
    return int(hashlib.sha256(f"heldout-v1|{run}|{uuid}".encode()).hexdigest()[:8], 16) % 4 == 0


if __name__ == "__main__":
    lines = []
    for path in sorted(glob.glob(os.path.join(W, "case", "panel", "*", "*.jsonl"))):
        run = os.path.relpath(path, os.path.join(W, "case", "panel")).replace("\\", "/")
        with open(path, encoding="utf-8") as f:
            for line in f:
                u = json.loads(line)["uuid"]
                if is_heldout(run, u):
                    lines.append(f"{run}\t{u}")
    lines.sort()
    out = os.path.join(AUDIT, "frozen", "heldout_v1.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines), hashlib.sha256(open(out, "rb").read()).hexdigest())
