"""Run every command block of audit/AUDIT.md and compare its output with the backticked
text in the "Prints"/"Print" line after the block. Run from Git Bash (needs `bash` on PATH).
"""

import os
import re
import subprocess
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = ("cd " + AUDIT.replace("\\", "/") + "\n"
       "export NLTK_DATA=../case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1\n"
       "P=../.venv/Scripts/python.exe\n")

text = open(os.path.join(AUDIT, "AUDIT.md"), encoding="utf-8").read()
blocks = list(re.finditer(r"```bash\n(.*?)```\n(.*?)(?=\n\n|\n```|\Z)", text, re.DOTALL))
BASH = os.environ.get("GIT_BASH", r"C:\Program Files\Git\usr\bin\bash.exe")  # not WSL's bash
ok = bad = 0
for m in blocks:
    body, after = m.group(1), m.group(2)
    if "repro.py" not in body:
        continue
    expected = re.findall(r"`([^`]*)`", after.split("\n")[0] + " " + " ".join(after.split("\n")[1:3]))
    expected = [e for e in expected if e.startswith("skyrl=")]
    out = subprocess.run([BASH, "-c", PRE + body], capture_output=True, text=True, encoding="utf-8")
    lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
    if "uniq -c" in body:
        got = {re.sub(r"^\s*\d+\s+", "", ln) for ln in lines}
        good = "skyrl=pass task_curation=fail contract=fail" in got and any(g.startswith("skyrl=fail") for g in got)
    else:
        good = lines == expected
    if good:
        ok += 1
    else:
        bad += 1
        print("MISMATCH:", body.strip()[:150])
        print("   expected:", expected)
        print("   got     :", lines, out.stderr[-300:])
print(f"command blocks checked: {ok + bad}, matching: {ok}, mismatching: {bad}")
sys.exit(1 if bad else 0)
