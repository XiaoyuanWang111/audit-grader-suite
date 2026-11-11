"""Check that every fixture cited in audit/AUDIT.md exists and that each
`<fixture id>` ... `[verdict]` pair in the findings tables matches what
audit/scripts/repro.py prints for the grader.

Usage: NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/verify_report.py
"""
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "tests"))
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

BY_ID = {f["id"]: f for f in FIXTURES}
text = (W / "audit" / "AUDIT.md").read_text(encoding="utf-8")
ids = set(re.findall(r"`([a-z_-]+:[a-z_-]+:[0-9a-f]{8})`", text))
missing = sorted(i for i in ids if i not in BY_ID)
print(f"fixture ids cited: {len(ids)}; missing from fixtures_data.py: {missing}")

# pairs inside table cells: `id`: ... [verdict]   (also `...:hash` shorthand after a full id)
bad = 0
checked = 0
for line in text.splitlines():
    if not line.startswith("| F-"):
        continue
    cell = line.split("|")[3]
    last_prefix = None
    for m in re.finditer(r"`((?:[a-z_-]+:[a-z_-]+)?(?:\.\.\.)?:?[0-9a-f]{8})`.*?\[(pass|fail|raises `IndexError`)\]", cell):
        ref, verdict = m.group(1), m.group(2)
        if ref.startswith("...:"):
            fid = f"{last_prefix}:{ref[4:]}"
        else:
            fid = ref
            last_prefix = ":".join(fid.split(":")[:2])
        f = BY_ID.get(fid)
        if f is None:
            print("MISSING", fid)
            bad += 1
            continue
        g = H.check_one(f["check"], f["kwargs"], f["response"], which="grader", prompt=f["prompt"])
        got = ("raises `IndexError`" if isinstance(g, str) and "IndexError" in g else
               ("pass" if g is True else "fail" if g is False else g))
        checked += 1
        if got != verdict:
            print(f"MISMATCH {fid}: report says [{verdict}], grader gives {got}")
            bad += 1
print(f"verdict pairs checked: {checked}; mismatches: {bad}")
