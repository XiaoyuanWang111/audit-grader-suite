"""Print short excerpts of panel responses where two graders disagree on one check.

Usage: python -B audit/scripts/show_disagreements.py <iid> <colA> <colB> [n] [chars]
e.g.   python -B audit/scripts/show_disagreements.py format:list g_strict x_fix 5 200
Only the graded `response` field is printed (never raw_response), truncated.
Held-out runs (sample7; greedy_repeat of the thinking configs) are never shown.
"""
import json
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
iid, ca, cb = sys.argv[1], sys.argv[2], sys.argv[3]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
chars = int(sys.argv[5]) if len(sys.argv) > 5 else 200
hits = []
for f in sorted((W / "audit" / "out" / "panel").glob("*.tsv")):
    with open(f, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(header, line.rstrip("\n").split("\t")))
            heldout = r["run"] == "sample7" or (r["folder"].endswith("__thinking") and r["run"] == "greedy_repeat")
            if r["iid"] == iid and r[ca] != r[cb] and not heldout:
                hits.append(r)
random.Random(0).shuffle(hits)
print(f"{len(hits)} disagreements on {iid} ({ca} vs {cb})")
for r in hits[:n]:
    rec = None
    with open(W / "case" / "panel" / r["folder"] / f"{r['run']}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            x = json.loads(line)
            if str(x["key"]) == r["key"]:
                rec = x
                break
    resp = rec["response"]
    print(f"--- {r['folder']}/{r['run']} key={r['key']} {ca}={r[ca]} {cb}={r[cb]} len={len(resp)}")
    print(json.dumps(resp[:chars], ensure_ascii=True))
