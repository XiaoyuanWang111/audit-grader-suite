"""Inspect the data file's structure (keys, settings) without printing long text."""
import json
import sys
from collections import Counter

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

with open(DATA, encoding="utf-8") as f:
    row = json.loads(f.readline())

def shape(x, depth=0):
    pad = "  " * depth
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, (dict, list)):
                print(f"{pad}{k}: {type(v).__name__}")
                shape(v, depth + 1)
            else:
                s = repr(v)
                print(f"{pad}{k}: {s[:120]}")
    elif isinstance(x, list):
        print(f"{pad}[list of {len(x)}]")
        if x:
            shape(x[0], depth + 1)

shape(row)
rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
print("---- record_json keys")
for k, v in rec.items():
    print(k, repr(v)[:300])
