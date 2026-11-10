"""Print short excerpts of panel items where the grader (gi) and the replacement with the grader's
readings (xg) disagree, for named checks. Usage: spotcheck.py CHECK [N] [SEED]"""
import csv
import glob
import json
import os
import random
import sys

W = "<W>"
check = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
items = []
for p in sorted(glob.glob(f"{W}/audit/out/panel/*.tsv")):
    cfg, run = os.path.basename(p)[:-4].rsplit("__", 1)
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        if r["check"] == check and r["gi"] != r["xg"]:
            items.append((cfg, run, r["key"], r["gi"], r["xg"]))
print(f"{check}: {len(items)} disagreements; gi=True,xg=False: {sum(1 for i in items if i[3]=='True')}")
for cfg, run, key, gi, xg in rng.sample(items, min(n, len(items))):
    rec = json.loads(open(f"{W}/case/panel/{cfg}/{run}.jsonl", encoding="utf-8").readlines()[int(key)])
    resp = rec["response"]
    print(f"--- {cfg}/{run} key={key} gi={gi} xg={xg} len={len(resp)}")
    print("   ", repr(resp[:260]))
