"""Rerun every command in audit/AUDIT.md and compare its output with the report.

A checked block is a ```text fence whose first line starts with "$ ". The rest
of the block is the expected output (stdout and stderr together). Commands run
in Git Bash from W.

Run from W:  python -B audit/scripts/check_report_commands.py
Exit status 1 if any output differs.
"""
import pathlib
import re
import shutil
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parents[2]


def main():
    bash = shutil.which("bash")
    if bash is None or "system32" in bash.lower():
        sys.exit(f"need Git Bash on PATH, found {bash!r}")
    text = (W / "audit" / "AUDIT.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```text\n(\$ .*?)```", text, flags=re.S)
    bad = 0
    for block in blocks:
        lines = block.rstrip("\n").split("\n")
        cmd = lines[0][2:]
        expected = lines[1:]
        p = subprocess.run([bash, "-c", cmd], cwd=str(W), capture_output=True, text=True, encoding="utf-8")
        got = (p.stdout + p.stderr).rstrip("\n").split("\n")
        ok = got == expected
        bad += not ok
        print(("OK    " if ok else "DIFF  ") + cmd)
        if not ok:
            for i in range(max(len(got), len(expected))):
                g = got[i] if i < len(got) else "<missing>"
                e = expected[i] if i < len(expected) else "<missing>"
                if g != e:
                    print(f"   line {i + 1}: report {e!r}\n            output {g!r}")
    print(f"{len(blocks)} commands, {bad} differ")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
