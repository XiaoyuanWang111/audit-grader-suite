"""Print the exact frozen files of one review case: python -I show_case.py CASE_ID"""
import json, pathlib, sys
cases = {json.loads(l)["case_id"]: json.loads(l)
         for l in (pathlib.Path(__file__).resolve().parent / "cases.jsonl").read_text(encoding="utf-8").splitlines()}
case = cases[sys.argv[1]]
if not case["files"]:
    print("(no files under /workspace besides the read-only logs)")
for f in case["files"]:
    b = bytes.fromhex(f["hex"])
    print(f"{f['path']}: {len(b)} bytes")
    print(f"  bytes: {b!r}")
