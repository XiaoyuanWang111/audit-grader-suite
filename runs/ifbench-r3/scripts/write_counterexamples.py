"""Fill the counterexample appendix of audit/AUDIT.md from audit/scripts/repro.py.

For every finding, the appendix shows the command and, in a code block, exactly what that command
prints (the input as a Python literal, the contract label, and the verdicts). The text between the
markers `<!-- counterexamples:begin -->` and `<!-- counterexamples:end -->` is replaced; the rest of
AUDIT.md is left as it is.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/write_counterexamples.py
"""
import contextlib
import io
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "scripts"))
import repro  # noqa: E402

BEGIN, END = "<!-- counterexamples:begin -->", "<!-- counterexamples:end -->"
CMD = ".venv/Scripts/python.exe -B audit/scripts/repro.py"


def capture(fid):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if not repro.special(fid):
            for f in repro.FIXTURES + repro.POST:
                if f.grader == fid:
                    repro.show_fixture(f)
    return buf.getvalue().rstrip("\n")


def main():
    repro.ifb.verify_pins()
    order = repro.SPECIAL[:4]
    for f in repro.FIXTURES:
        if f.grader.startswith("F-") and f.grader not in order:
            order.append(f.grader)
    order += repro.SPECIAL[4:]
    order += [f.grader for f in repro.POST]
    parts = [BEGIN, ""]
    for fid in order:
        parts += [f"### {fid}", "", f"`{CMD} {fid}` prints:", "", "```text", capture(fid), "```", ""]
    parts.append(END)
    path = os.path.join(W, "audit", "AUDIT.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    a, b = text.index(BEGIN), text.index(END) + len(END)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text[:a] + "\n".join(parts) + text[b:])
    print(f"wrote {len(order)} counterexamples into audit/AUDIT.md")


if __name__ == "__main__":
    main()
