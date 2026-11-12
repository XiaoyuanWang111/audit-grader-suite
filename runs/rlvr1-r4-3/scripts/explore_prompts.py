"""Explore how instruction texts appear in the prompts (data only, no grader code)."""
import collections
import json
import re
import sys

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        rows.append(rec)

# Header phrases that introduce the numbered list of requirements
header_counter = collections.Counter()
numbered = 0
for rec in rows:
    p = rec["prompt"]
    m = re.search(r"\n([^\n]*)\n1\. ", p)
    if m:
        numbered += 1
        header_counter[m.group(1)[-80:]] += 1
print("numbered", numbered, "of", len(rows))
for h, c in header_counter.most_common(30):
    print(c, repr(h))
