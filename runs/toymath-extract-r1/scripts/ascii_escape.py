"""Rewrite non-ASCII characters in a Python source file as escapes (only valid inside string literals).

Usage: python -I audit/scripts/ascii_escape.py FILE [FILE ...]
"""
import sys

BS = chr(92)


def esc(ch):
    o = ord(ch)
    if o < 0x100:
        return BS + "x%02x" % o
    if o < 0x10000:
        return BS + "u%04x" % o
    return BS + "U%08x" % o


for path in sys.argv[1:]:
    with open(path, encoding="utf-8", newline="") as f:
        src = f.read()
    out = "".join(esc(c) if ord(c) > 127 else c for c in src)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(path, "non-ASCII replaced:", sum(1 for c in src if ord(c) > 127))
