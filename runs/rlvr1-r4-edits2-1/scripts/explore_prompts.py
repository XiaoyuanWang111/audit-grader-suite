"""Look at how instructions appear in prompts (data only, no grader code)."""
import json
import random
import re
from collections import Counter

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]
random.seed(0)
# lead-in lines before the requirement list
lead = Counter()
for r in rows:
    p = r["prompt"][0]["content"]
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    assert p == rec["prompt"], "prompt mismatch"
    m = re.search(r"\n\n([^\n]*)\n1\. ", p)
    lead[m.group(1) if m else None] += 1
for k, c in lead.most_common(40):
    print(c, repr(k)[:150])
print("distinct lead-ins", len(lead))
