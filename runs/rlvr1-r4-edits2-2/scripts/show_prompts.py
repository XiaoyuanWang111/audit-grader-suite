"""Print the tail of the prompts of given uuids (instruction part), with ids and kwargs."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")
want = set(sys.argv[1:-1])
tail = int(sys.argv[-1])
for line in open(DATA, encoding="utf-8"):
    row = json.loads(line)
    u = row["extra_info"]["nemotron_ultra"]["uuid"]
    if u not in want:
        continue
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    print("=" * 30, u)
    print(list(zip(rec["instruction_id_list"], rec["kwargs"])))
    print(repr(rec["prompt"][-tail:]))
