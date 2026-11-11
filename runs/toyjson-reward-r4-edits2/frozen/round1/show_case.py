"""Print a review case's exact response (repr first, then the raw text) and its reference.

    python -B audit/frozen/round1/show_case.py C07
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8") as f:
    cases = {c["case_id"]: c for c in map(json.loads, f)}
c = cases[sys.argv[1]]
print("repr:", repr(c["response"]))
print("length:", len(c["response"]))
print("reference:", c["reference"])
print("----- raw response -----")
print(c["response"])
