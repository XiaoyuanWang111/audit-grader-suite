"""Check that every `repro.py <id>` claim in AUDIT.md matches what repro.py prints.

A claim has the form: `repro.py <id>` → NV x, VS y, VG z; contract c
"""
import json
import re
import subprocess
import sys

A = "<W>/audit"
PY = "<W>/.venv/Scripts/python.exe"

text = open(f"{A}/AUDIT.md", encoding="utf-8").read()
claims = re.findall(r"`repro\.py ([a-z_0-9]+:[0-9a-f]{16})` → NV (\w+), VS (\w+), VG (\w+); contract (\w+)", text)
bad = 0
seen = set()
for fid, nv, vs, vg, label in claims:
    if (fid, nv, vs, vg, label) in seen:
        continue
    seen.add((fid, nv, vs, vg, label))
    out = subprocess.run([PY, f"{A}/repro.py", fid], capture_output=True, text=True, encoding="utf-8", cwd=A,
                         env={"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:\\Windows"})
    got = {}
    for line in out.stdout.splitlines():
        for key in ("NV", "VS", "VG", "R", "label (contract)"):
            if line.startswith(key + ": "):
                got[key] = line[len(key) + 2:].split()[0]
    want = {"NV": nv, "VS": vs, "VG": vg, "label (contract)": label}
    diffs = {k: (v, got.get(k)) for k, v in want.items() if got.get(k) != v}
    if diffs:
        bad += 1
        print("MISMATCH", fid, diffs, out.stderr[-300:])
print(f"{len(seen)} distinct claims checked, {bad} mismatches")
sys.exit(1 if bad else 0)
