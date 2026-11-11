"""Rerun every `audit/repro.py ...` command quoted in audit/AUDIT.md and check its output.

A quoted command has the form  `audit/repro.py <args>` ... → `<expected line>`  on one line.
The expected line must equal one line of the command's output. Prints one line per command and
a summary; exits 1 on any mismatch.
"""
import os
import pathlib
import re
import shlex
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parents[2]
PY = W / ".venv" / "Scripts" / "python.exe"
PAT = re.compile(r"`audit/repro\.py ([^`]+)`[^\n]*?→ `([^`]+)`")


def main():
    text = (W / "audit" / "AUDIT.md").read_text(encoding="utf-8")
    env = dict(os.environ, NLTK_DATA=str(W / "case" / "deps" / "nltk_data"), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8")
    bad = 0
    n = 0
    for m in PAT.finditer(text):
        args, expected = shlex.split(m.group(1)), m.group(2).strip()
        out = subprocess.run([str(PY), str(W / "audit" / "repro.py"), *args], cwd=W, env=env, capture_output=True,
                             text=True, encoding="utf-8").stdout
        ok = expected in [line.strip() for line in out.splitlines()]
        n += 1
        bad += not ok
        print(("OK  " if ok else "BAD ") + m.group(1) + ("" if ok else f"\n    expected: {expected}\n    got: {out.strip()}"))
    print(f"{n} commands, {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
