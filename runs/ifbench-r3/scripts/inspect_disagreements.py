"""Print a few grader/replacement disagreements from NON-held-out runs (held-out runs are never used to tune the replacement).

Usage: .venv/Scripts/python.exe -B audit/scripts/inspect_disagreements.py CHECK DIRECTION [N] [CHARS]
DIRECTION: g1p0 (grader pass, replacement fail) or g0p1.
"""
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
import ifb  # noqa: E402

check, direction = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 2
chars = int(sys.argv[4]) if len(sys.argv) > 4 else 300
want_g = direction == "g1p0"
rows = [json.loads(l) for l in open(os.path.join(W, "audit", "work", "panel_verdicts.jsonl"), encoding="utf-8")]
cand = [r for r in rows if r["iid"] == check and not r["heldout"] and not r["extraction_failure"]
        and bool(r["g"]) == want_g and bool(r["p"]) != want_g]
random.Random(7).shuffle(cand)
recs = {}
for r in cand[:n]:
    path = os.path.join(ifb.CASE, "panel", r["cfg"], r["run"] + ".jsonl")
    if path not in recs:
        recs[path] = [json.loads(l) for l in open(path, encoding="utf-8")]
    rec = [x for x in recs[path] if x["key"] == r["key"]][0]
    t = rec["response"]
    print(f"--- {check} {direction} {r['cfg']}/{r['run']} key={r['key']} len={len(t)} alt={r['alt']}")
    print(repr(t[:chars]))
print(f"[{len(cand)} non-held-out candidates]")
