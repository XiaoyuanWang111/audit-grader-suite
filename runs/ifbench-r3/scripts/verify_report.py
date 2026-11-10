"""Check that every command in Appendix A of audit/AUDIT.md prints exactly the text the report shows.

For each "### <finding>" entry, runs the command given in it from W as a separate process and compares
its standard output with the entry's code block. Prints one line per mismatch and a summary.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/verify_report.py
"""
import os
import re
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    text = open(os.path.join(W, "audit", "AUDIT.md"), encoding="utf-8").read()
    app = text[text.index("<!-- counterexamples:begin -->"):text.index("<!-- counterexamples:end -->")]
    entries = re.findall(r"### (\S+)\n\n`([^`]+)` prints:\n\n```text\n(.*?)\n```", app, flags=re.S)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    bad = 0
    for fid, cmd, expected in entries:
        args = cmd.split()
        args[0] = os.path.join(W, args[0])
        out = subprocess.run(args, cwd=W, env=env, capture_output=True, text=True, encoding="utf-8").stdout
        out = out.replace("\r\n", "\n").rstrip("\n")
        if out != expected:
            bad += 1
            print(f"MISMATCH {fid}")
    print(f"{len(entries)} commands checked, {bad} mismatches")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
