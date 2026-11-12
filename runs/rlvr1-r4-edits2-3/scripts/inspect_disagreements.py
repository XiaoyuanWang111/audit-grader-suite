"""Print development-half examples of one disagreement bucket (never held-out responses).

Usage: inspect_disagreements.py <instruction_id> <grader skyrl|tc> <fp|fn> <defect|decision|any> [k] [chars]
Prints the graded answer (after </think> for the reasoning model) as a short excerpt.
"""

import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "replacement"))

import contract_grader as cg  # noqa: E402

iid, grader, kind, cls = sys.argv[1:5]
k = int(sys.argv[5]) if len(sys.argv) > 5 else 5
chars = int(sys.argv[6]) if len(sys.argv) > 6 else 300
W = os.path.dirname(AUDIT)


def held_out(uuid):
    return int(hashlib.sha256(uuid.encode()).hexdigest()[0], 16) % 2 == 0


raw = {}
cands = []
for line in open(os.path.join(AUDIT, "panel", "verdicts.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    if held_out(r["uuid"]) or r["rep"]["extraction_failure"]:
        continue
    for i, x in enumerate(r["ids"]):
        if x != iid:
            continue
        rep = r["rep"]["results"][i]
        g = r["skyrl"]["results"][i] if grader == "skyrl" else r["tc"]["results"][i]
        if g is None or g == rep:
            continue
        if (kind == "fp") != bool(g):
            continue
        explained = bool(r["flips"][i]) or r["rep"]["all_other"][i] == g
        if cls == "defect" and explained or cls == "decision" and not explained:
            continue
        cands.append((r, i))
random.Random(1).shuffle(cands)
print(f"{len(cands)} development-half cases")
want = {(r["folder"], r["run"], r["uuid"]) for r, _ in cands[:k]}
for path_folder in {w[0] for w in want}:
    pass
for r, i in cands[:k]:
    p = os.path.join(W, "case", "panel", r["folder"], r["run"] + ".jsonl")
    if p not in raw:
        raw[p] = {}
        for line in open(p, encoding="utf-8"):
            x = json.loads(line)
            raw[p][x["uuid"]] = x["raw_response"]
    text = cg.graded_text(raw[p][r["uuid"]], r["reasoning_model"])
    rows = None
    print("=" * 30, r["folder"], r["run"], r["uuid"], "row", r["row"], "flips", r["flips"][i])
    print("   head:", repr(text[:chars]))
    if len(text) > chars:
        print("   tail:", repr(text[-chars // 2:]))
