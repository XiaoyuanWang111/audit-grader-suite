"""Replacement verifier for count-server-errors, written from audit/CONTRACT.md.

One switch per decision entry; the defaults are the proposed readings.

    python replacement_verifier.py WORKSPACE [--switch name=value ...]

Exit status 0 passes, 1 fails; prints one line with the verdict and reason.
"""

import argparse
import gzip
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "case", "task", "environment", "logs")
LOG_FILES = ("access.log", "access.log.1", "access.log.2.gz")

# Proposed readings (audit/CONTRACT.md, decision entries).
PROPOSED = {
    "leading_zeros": "allow",    # D-leading-zeros: allow | reject
    "plus_sign": "allow",        # D-plus-sign: allow | reject
    "digit_script": "ascii",     # D-digit-script: ascii | unicode
    "whitespace_set": "ascii",   # D-whitespace-set: ascii | unicode
    "encoding": "utf8",          # D-encoding: utf8 | bom
}
CHOICES = {
    "leading_zeros": ("allow", "reject"),
    "plus_sign": ("allow", "reject"),
    "digit_script": ("ascii", "unicode"),
    "whitespace_set": ("ascii", "unicode"),
    "encoding": ("utf8", "bom"),
}

ASCII_WS = " \t\n\v\f\r"
# Unicode 15.0 White_Space property (PropList.txt), not Python's str.isspace,
# which also treats U+001C..U+001F as whitespace.
UNICODE_WS = "".join(chr(c) for c in [*range(0x09, 0x0E), 0x20, 0x85, 0xA0, 0x1680,
                                       *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F,
                                       0x205F, 0x3000])

LINE_RE = re.compile(r'(\S+) (\S+) (\S+) \[([^\]]*)\] "([^"]*)" (\S+) (\S+)')


def count_server_errors(logs_dir=DEFAULT_LOGS):
    """N from the task text: lines whose field after the quoted request is 500-599."""
    total = 0
    for name in LOG_FILES:
        with open(os.path.join(logs_dir, name), "rb") as f:
            data = f.read()
        if name.endswith(".gz"):
            data = gzip.decompress(data)
        for line in data.decode("ascii").split("\n"):
            if not line:
                continue
            m = LINE_RE.fullmatch(line)
            if m is None:
                raise ValueError(f"unparsed log line in {name}: {line!r}")
            status = m.group(6)
            if re.fullmatch(r"[0-9]{3}", status) and 500 <= int(status) <= 599:
                total += 1
    return total


def decode(data, encoding):
    if encoding == "bom":
        for bom, codec in ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe\x00\x00", "utf-32-le"),
                           (b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe", "utf-16-le"),
                           (b"\xfe\xff", "utf-16-be")):
            if data.startswith(bom):
                return data[len(bom):].decode(codec)
    return data.decode("utf-8")


def parse_count(text, sw):
    """Return the integer's digits as an ASCII string without leading zeros, or None."""
    if sw["plus_sign"] == "allow" and text.startswith("+"):
        text = text[1:]
    if not text:
        return None
    digits = []
    for ch in text:
        if "0" <= ch <= "9":
            digits.append(ch)
        elif sw["digit_script"] == "unicode" and unicodedata.decimal(ch, None) is not None:
            digits.append(str(unicodedata.decimal(ch)))
        else:
            return None
    s = "".join(digits)
    if sw["leading_zeros"] == "reject" and len(s) > 1 and s[0] == "0":
        return None
    return s.lstrip("0") or "0"


def grade(workspace, n, switches=None):
    sw = dict(PROPOSED)
    sw.update(switches or {})
    path = os.path.join(workspace, "out", "answer.txt")
    if not os.path.isfile(path):
        return "fail", "no regular file at out/answer.txt"
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        return "fail", f"answer file unreadable: {type(e).__name__}"
    try:
        text = decode(data, sw["encoding"])
    except UnicodeDecodeError:
        return "fail", "answer file is not text in the accepted encoding"
    text = text.strip(ASCII_WS if sw["whitespace_set"] == "ascii" else UNICODE_WS)
    if not text:
        return "fail", "answer file empty after trimming whitespace"
    digits = parse_count(text, sw)
    if digits is None:
        return "fail", "trimmed content is not a decimal integer"
    if digits != str(n):
        return "fail", "wrong count"
    return "pass", "correct"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("--switch", action="append", default=[])
    ap.add_argument("--n", type=int)
    a = ap.parse_args(argv)
    switches = {}
    for item in a.switch:
        k, v = item.split("=", 1)
        if k not in CHOICES or v not in CHOICES[k]:
            ap.error(f"bad switch {item}")
        switches[k] = v
    n = a.n if a.n is not None else count_server_errors()
    verdict, reason = grade(a.workspace, n, switches)
    print(f"{verdict}: {reason}")
    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
