"""Print the exact final files of one review case.

Usage: python -I show_case.py CASE_ID

Each file is printed as its path, its byte length, and its exact bytes as a Python literal.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "cases.json"), encoding="utf-8") as f:
    cases = json.load(f)["cases"]
cid = sys.argv[1]
if cid not in cases:
    sys.exit(f"unknown case {cid}")
files = cases[cid]
if not files:
    print("(no files under /workspace apart from the read-only logs)")
for path in sorted(files):
    data = files[path].encode("latin-1")
    print(f"{path}\t{len(data)} bytes\t{data!r}")
