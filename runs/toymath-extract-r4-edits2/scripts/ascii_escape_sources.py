"""Rewrite raw non-ASCII characters in the audit's Python sources as \\uXXXX escapes.

Only safe where every such character sits inside a string literal (checked by
hand for the files below). Run from W:  python -B audit/scripts/ascii_escape_sources.py
"""
import pathlib

BS = chr(92)
FILES = ["audit/tests/fixtures.py", "audit/tests/properties.py", "audit/scripts/fuzz.py",
         "audit/scripts/make_repro.py"]

W = pathlib.Path(__file__).resolve().parents[2]
for rel in FILES:
    p = W / rel
    src = p.read_text(encoding="utf-8")
    out = "".join(c if ord(c) < 128 else f"{BS}u{ord(c):04x}" for c in src)
    if out != src:
        p.write_text(out, encoding="utf-8", newline="\n")
        print(f"escaped {sum(1 for c in src if ord(c) >= 128)} characters in {rel}")
