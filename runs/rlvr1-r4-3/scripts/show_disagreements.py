"""Print a few panel disagreements for one check, from responses outside the held-out set.

Usage: python show_disagreements.py <instruction_id> <grader A|B> <grader verdict 0|1> <R verdict 0|1> [k] [chars]
Prints the answer part only (text after </think> for the thinking model), cut to `chars`.
"""
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(AUDIT, "..", "case")
iid, g, gv, rv = sys.argv[1], sys.argv[2], sys.argv[3] == "1", sys.argv[4] == "1"
k = int(sys.argv[5]) if len(sys.argv) > 5 else 4
chars = int(sys.argv[6]) if len(sys.argv) > 6 else 300
held = set(open(os.path.join(AUDIT, "frozen", "heldout_uuids.txt"), encoding="utf-8").read().split())
idx = {"A": 1, "B": 2}[g]
hits = []
with open(os.path.join(AUDIT, "results", "panel_verdicts.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["uuid"] in held:
            continue
        for j, c in enumerate(r["c"]):
            if c[0] == iid and c[idx] is not None and c[idx] == gv and c[3] == rv:
                hits.append((r["folder"], r["run"], r["uuid"], j))
print(len(hits), "non-held-out hits")
random.Random(1).shuffle(hits)
recs = {}
with open(os.path.join(CASE, "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
    for line in f:
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        recs[rec["uuid"]] = rec
want = {(h[0], h[1], h[2]): h[3] for h in hits[:k]}
for (folder, run, uuid), j in want.items():
    with open(os.path.join(CASE, "panel", folder, run + ".jsonl"), encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if p["uuid"] == uuid:
                raw = p["raw_response"]
                ans = raw[raw.rfind("</think>") + 8:] if "</think>" in raw else raw
                print("=" * 20, folder, run, uuid, "kwargs:", json.dumps(recs[uuid]["kwargs"][j], ensure_ascii=False)[:120])
                print(json.dumps(ans.strip()[:chars], ensure_ascii=False))
                if len(ans.strip()) > chars:
                    print("   ... tail:", json.dumps(ans.strip()[-120:], ensure_ascii=False))
                break
