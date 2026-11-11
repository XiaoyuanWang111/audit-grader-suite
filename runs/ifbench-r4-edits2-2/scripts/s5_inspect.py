"""Print short excerpts of panel disagreements for one check (held-out runs excluded).

usage: s5_inspect.py CHECK DIRECTION [N] [CHARS]
  DIRECTION: g1p0 (grader pass, replacement fail), g0p1, g1r0, g0r1
Prints only the first CHARS characters of each graded response (never thinking text: the
`response` field is the text after </think>; extraction failures are skipped).
"""
import glob
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELD = {l.strip().replace(".jsonl", "") for l in open(os.path.join(W, "audit", "frozen", "heldout_runs.txt"))}
check, direction = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
chars = int(sys.argv[4]) if len(sys.argv) > 4 else 300
want = {"g1p0": ("gs", 1, "ps", 0), "g0p1": ("gs", 0, "ps", 1), "g1r0": ("gs", 1, "rs", 0), "g0r1": ("gs", 0, "rs", 1)}[direction]
hits = []
for p in sorted(glob.glob(os.path.join(W, "audit", "work", "panel_verdicts", "*.jsonl"))):
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        if r["iid"] != check or f"{r['cfg']}/{r['run']}" in HELD or r["xfail"]:
            continue
        if r[want[0]] == want[1] and r[want[2]] == want[3]:
            hits.append(r)
random.Random(1).shuffle(hits)
print(f"{len(hits)} hits")
cache = {}
for r in hits[:n]:
    key = (r["cfg"], r["run"])
    if key not in cache:
        cache[key] = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(W, "case", "panel", r["cfg"], r["run"] + ".jsonl"), encoding="utf-8")}
    rec = cache[key][str(r["key"])] if str(r["key"]) in cache[key] else cache[key][r["key"]]
    resp = rec["response"]
    print(f"--- {r['cfg']}/{r['run']} key={r['key']} finish={r['finish']} len={len(resp)}")
    print("   ", repr(resp[:chars]))
