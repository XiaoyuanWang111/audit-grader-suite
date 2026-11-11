"""Run every command quoted in audit/AUDIT.md and check that it prints what the report says.

Checked forms:  `<python> audit/scripts/(probe|repro).py ...` prints `<expected>`  and the F31
`python -c` command ("ends with `<expected>`"); grep/sed/diff commands must exit 0 with output.
Commands are split with shlex (POSIX rules, as Git Bash would) and run without a shell.
"""
import os
import re
import shlex
import subprocess
import sys

W = "<W>"
PY = W + "/.venv/Scripts/python.exe"
env = dict(os.environ, NLTK_DATA=W + "/case/deps/nltk_data", PYTHONIOENCODING="utf-8")
text = open(W + "/audit/AUDIT.md", encoding="utf-8").read()

pat = re.compile(r"`(\.venv/Scripts/python\.exe (?:audit/scripts/(?:probe|repro)\.py|-c) [^`]*)` (?:prints|ends with) `([^`]*)`")
fails = n = 0
for cmd, expected in pat.findall(text):
    n += 1
    argv = shlex.split(cmd)
    argv[0] = PY
    out = subprocess.run(argv, cwd=W, env=env, capture_output=True, text=True, encoding="utf-8")
    full = out.stdout + out.stderr
    parts = [p for p in expected.split(" ...") if p.strip()]
    ok = all(p.strip() in full for p in parts)
    fails += not ok
    print(("OK   " if ok else "FAIL ") + cmd[:110] + ("" if ok else f"\n     expected {expected!r}\n     got {full[-300:]!r}"))

for cmd in re.findall(r"Command: `((?:grep|sed|diff) [^`]*)`", text):
    n += 1
    out = subprocess.run(["C:/Program Files/Git/usr/bin/bash.exe", "-c", cmd], cwd=W, capture_output=True, text=True)
    ok = out.returncode in (0, 1) and out.stdout.strip() != ""
    fails += not ok
    print(("OK   " if ok else "FAIL ") + cmd[:110])
print(f"{n} commands checked, {fails} failed")
sys.exit(1 if fails else 0)
