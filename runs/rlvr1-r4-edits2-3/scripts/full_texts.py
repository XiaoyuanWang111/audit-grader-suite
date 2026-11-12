"""Print, for each instruction id, the full requirement text of one or two rows (data only)."""
import json
import collections
import sys

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"
LEADS = [
    "Please follow these instructions in your response:",
    "Your response should comply with these constraints:",
    "Make sure to adhere to these requirements:",
    "Please ensure your answer follows these guidelines:",
    "Your response should satisfy these conditions:",
]
want = set(sys.argv[1:])
rows = []
with open(PATH, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

shown = collections.Counter()
for i, r in enumerate(rows):
    c = r["prompt"][0]["content"]
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    ids = rec["instruction_id_list"]
    for iid in ids:
        if want and iid not in want:
            continue
        if shown[iid] >= 2:
            continue
        # prefer rows where this id is the last numbered item
        if ids[-1] != iid:
            continue
        idx = max(c.rfind(lead) for lead in LEADS)
        if idx < 0:
            continue
        shown[iid] += 1
        print("=" * 20, "row", i, iid, rec["kwargs"])
        print(c[idx:][:1200])
