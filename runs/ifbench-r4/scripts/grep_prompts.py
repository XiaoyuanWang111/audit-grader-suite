"""Print every prompt match of a regex with context. Usage: grep_prompts.py REGEX [PAD]"""
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]
pat = re.compile(sys.argv[1])
pad = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for i, r in enumerate(ROWS):
    for m in pat.finditer(r["prompt"]):
        p = r["prompt"]
        print(i, r["instruction_id_list"], repr(p[max(0, m.start() - pad):m.end() + pad]))
