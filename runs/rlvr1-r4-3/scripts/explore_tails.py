"""Print prompt tails per instruction id (data only, no grader code).

Usage: python explore_tails.py <id-substring> [n] [chars]
"""
import json
import random
import sys

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
want = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
chars = int(sys.argv[3]) if len(sys.argv) > 3 else 500

rows = []
with open(DATA, encoding="utf-8") as f:
    for i, line in enumerate(f):
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        if any(want == iid for iid in rec["instruction_id_list"]):
            rows.append((i, rec))
random.seed(0)
sample = random.sample(rows, min(n, len(rows)))
for i, rec in sample:
    print(f"=== row {i} ids={rec['instruction_id_list']} kwargs={json.dumps(rec['kwargs'], ensure_ascii=False)[:300]}")
    print(rec["prompt"][-chars:])
    print()
