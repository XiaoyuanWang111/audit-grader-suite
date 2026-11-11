"""Print prompt tails for single-constraint rows, a few per id (data only)."""
import json
import random
import sys
from collections import defaultdict

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]
random.seed(1)
want = sys.argv[1] if len(sys.argv) > 1 else None
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
by = defaultdict(list)
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    for iid in rec["instruction_id_list"]:
        by[iid].append((r, rec))
for iid in sorted(by):
    if want and iid != want:
        continue
    items = by[iid]
    singles = [x for x in items if len(x[1]["instruction_id_list"]) == 1]
    pick = random.sample(singles, min(n, len(singles))) if singles else []
    pick += random.sample(items, min(n, len(items)))
    print("=" * 30, iid, "rows", len(items), "singles", len(singles))
    for r, rec in pick:
        p = rec["prompt"]
        print("--- ids", rec["instruction_id_list"], "kwargs", json.dumps(rec["kwargs"], ensure_ascii=False)[:300])
        print("TAIL:", repr(p[-500:]))
