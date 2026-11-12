"""Look at how the requirement text appears in the prompts (data only)."""
import json
import collections
import random
import re

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(PATH, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

# Do prompt (message) and record prompt agree?
same = 0
nmsg = collections.Counter()
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    nmsg[(len(r["prompt"]), r["prompt"][0]["role"])] += 1
    if r["prompt"][0]["content"] == rec["prompt"]:
        same += 1
print("message == record prompt:", same, "of", len(rows), "msg shapes", nmsg)

# Lead-in phrases before the list of requirements
leads = collections.Counter()
for r in rows:
    c = r["prompt"][0]["content"]
    m = re.search(r"\n\n([^\n]*)\n1\. ", c)
    leads[m.group(1) if m else None] += 1
print("lead-in lines (top 40):")
for k, v in leads.most_common(40):
    print(f"  {v:5d} {k!r}")
print("distinct lead-ins", len(leads))

random.seed(0)
for r in random.sample(rows, 6):
    c = r["prompt"][0]["content"]
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    print("=====", rec["instruction_id_list"], rec["kwargs"])
    print(c[-700:])
