"""Print short excerpts of panel responses where two graders disagree on one check.

Usage: python audit/scripts/inspect_disagreements.py CHECK A B [N] [CHARS]
  A, B in G, GL, R, RL, X, XP; shows cases with A pass and B fail.
Held-out files (sample7, thinking greedy_repeat) and extraction failures are skipped,
so no reasoning text is printed.
"""
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VD = os.path.join(W, "audit", "frozen", "panel_verdicts")
PANEL = os.path.join(W, "case", "panel")
HELD = {"sample7"}


def main():
    check, a, b = sys.argv[1:4]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    chars = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    hits = []
    for cfg in sorted(os.listdir(VD)):
        for fn in sorted(os.listdir(os.path.join(VD, cfg))):
            run = fn[:-6]
            if run in HELD or ("thinking" in cfg and run == "greedy_repeat"):
                continue
            for i, line in enumerate(open(os.path.join(VD, cfg, fn), encoding="utf-8")):
                rec = json.loads(line)
                if rec["xf"]:
                    continue
                for ins in rec["inst"]:
                    if ins["id"] == check and ins[a] is True and ins[b] is not True:
                        hits.append((cfg, fn, i))
    print(f"{len(hits)} cases ({a} pass, {b} fail) on {check}")
    random.Random(0).shuffle(hits)
    for cfg, fn, i in hits[:n]:
        rec = json.loads(open(os.path.join(PANEL, cfg, fn), encoding="utf-8").read().splitlines()[i])
        print(f"--- {cfg}/{fn} row {i} fin={rec['finish_reason']}")
        print(repr(rec["response"][:chars]))


if __name__ == "__main__":
    main()
