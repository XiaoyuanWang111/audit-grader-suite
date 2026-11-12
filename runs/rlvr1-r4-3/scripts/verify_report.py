"""Check that every repro command in audit/AUDIT.md prints what the report says.

For each findings row, the first fixture id is the counterexample; the row's "label X; A Y[, B Z]"
claim is compared with the output of `audit/repro.py --id <id>` run as a subprocess. Secondary ids
with an explicit claim ("`id`: label X, A Y") are checked the same way; ids without a claim must exist.
"""
import json
import os
import re
import subprocess
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)
PY = os.path.join(W, ".venv", "Scripts", "python.exe")
ID = r"([a-z_]+:[a-z_0-9]+:[0-9a-f]{16})"
ids_known = {json.loads(l)["id"] for l in open(os.path.join(AUDIT, "fixtures.jsonl"), encoding="utf-8")}
report = open(os.path.join(AUDIT, "AUDIT.md"), encoding="utf-8").read()


def run(fid):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    out = subprocess.run([PY, os.path.join(AUDIT, "repro.py"), "--id", fid], capture_output=True, text=True,
                         encoding="utf-8", env=env, cwd=W).stdout
    got = {}
    for line in out.splitlines():
        if line.startswith("contract label:"):
            got["label"] = line.split(":", 1)[1].strip()
        elif line.startswith("grader A"):
            got["A"] = "pass" if "): pass" in line else "fail"
            got["A_exc"] = "exception" in line
        elif line.startswith("grader B"):
            got["B"] = "none" if "no deterministic" in line else ("pass" if "): pass" in line else "fail")
    return got


checks = []
for line in report.splitlines():
    if not re.match(r"^\| (F-A\d+|G-\d+|P\d+) \|", line):
        continue
    rid = line.split("|")[1].strip()
    ids = re.findall("`" + ID + "`", line)
    for fid in ids:
        if fid not in ids_known:
            checks.append((rid, fid, "MISSING", None, None))
    m = re.search(r"label (pass|fail); ([AB]) (pass|fail)(?:, B (pass|fail))?", line)
    if ids and m:
        claim = {"label": m.group(1), m.group(2): m.group(3)}
        if m.group(4):
            claim["B"] = m.group(4)
        checks.append((rid, ids[0], "main", claim, None))
    for sm in re.finditer("`" + ID + r"`(?:, `[^`]*`)?: label (pass|fail), ([AB]) (pass|fail)", line):
        checks.append((rid, sm.group(1), "secondary", {"label": sm.group(2), sm.group(3): sm.group(4)}, None))

bad = 0
for rid, fid, kind, claim, _ in checks:
    if kind == "MISSING":
        bad += 1
        print("MISSING fixture id", rid, fid)
        continue
    got = run(fid)
    ok = all(got.get(k) == v for k, v in claim.items())
    if not ok:
        bad += 1
    print(("OK  " if ok else "BAD ") + f"{rid:6s} {kind:9s} {fid:70s} claim={claim} got={ {k: got.get(k) for k in claim} }")
print(f"{len(checks)} claims checked, {bad} problems")
sys.exit(1 if bad else 0)
