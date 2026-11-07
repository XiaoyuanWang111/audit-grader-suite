"""Print a case's exact response files: python -I show_case.py CASE_ID"""
import json, os, sys
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.json"), encoding="utf-8"))
files = d[sys.argv[1]]
if not files:
    print("(no files under /workspace)")
for rel in sorted(files):
    if files[rel] is None:
        print(f"/workspace/{rel}: directory")
        continue
    b = bytes.fromhex(files[rel])
    print(f"/workspace/{rel}: {len(b)} bytes")
    print("  hex:  " + b.hex(" "))
    print("  repr: " + repr(b))
