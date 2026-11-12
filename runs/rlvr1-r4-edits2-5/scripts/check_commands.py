"""Check the output of work/report_commands.sh (the AUDIT.md commands run literally in Git Bash)
against the verdicts the report states. Usage: bash work/report_commands.sh | python scripts/check_commands.py"""
import json
import re
import sys

text = sys.stdin.read()
blocks = re.split(r"^== ", text, flags=re.MULTILINE)[1:]
bad = 0
for b in blocks:
    head, _, body = b.partition("\n")
    fid, _, exp = head.partition(" ")
    expected = json.loads(exp)
    got = {}
    for line in body.splitlines():
        m = re.match(r"^([ABC])\s+.*?:\s*(.*)$", line)
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        if key in got:
            continue
        if rest.startswith("passes in"):
            k, n = map(int, re.findall(r"\d+", rest)[:2])
            got[key] = "some" if 0 < k < n else ("pass" if k == n else "fail")
        elif "exception" in rest:
            got[key] = "exception"
        elif rest.startswith("judged"):
            got[key] = "judge"
        else:
            got[key] = rest.split()[0]
    ok = all(got.get(k) == v for k, v in expected.items())
    bad += not ok
    if not ok:
        print("MISMATCH", fid, "expected", expected, "got", got)
print(f"{len(blocks) - bad} of {len(blocks)} report commands print what the report states")
