"""Replacement verifier for ToyOps count-server-errors, written from audit/CONTRACT.md (C1).

It grades the sandbox state the trial left: the file WORKSPACE/out/answer.txt and nothing else. It has one switch per
decision entry; the defaults are the contract's proposed readings (reading A of every entry).

Usage:
    python -I replacement_verifier.py WORKSPACE [--whitespace ascii|unicode] [--leading-zeros allow|reject]
        [--plus-sign allow|reject] [--digits ascii|unicode] [--surrounding-text reject|allow]
        [--bom bytes|decode] [--symlink follow|regular] [--expected N]

Exit status 0 passes and 1 fails. It never raises on any answer content.
"""

import argparse
import os
import re
import sys
import unicodedata

# C0: the count computed from the logs by audit/scripts/count_from_logs.py.
N = 41

# ASCII whitespace, POSIX [:space:] in the C locale.
ASCII_WS = " \t\n\r\x0b\x0c"
# The Unicode White_Space property (PropList.txt). Python's str.isspace() is wider: it adds U+001C..U+001F.
UNICODE_WS = (ASCII_WS + "\x85\xa0 " + "".join(chr(c) for c in range(0x2000, 0x200B))
              + "    　")

# Decision entry -> (switch name, proposed value, alternative value).
DECISIONS = {
    "D-whitespace": ("whitespace", "ascii", "unicode"),
    "D-leading-zeros": ("leading_zeros", "allow", "reject"),
    "D-plus-sign": ("plus_sign", "allow", "reject"),
    "D-digits": ("digits", "ascii", "unicode"),
    "D-surrounding-text": ("surrounding_text", "reject", "allow"),
    "D-bom": ("bom", "bytes", "decode"),
    "D-symlink": ("symlink", "follow", "regular"),
}
PROPOSED = {switch: proposed for switch, proposed, _ in DECISIONS.values()}


def switches_for(alternatives=()):
    """Switch values with the named decision entries flipped to their alternative reading."""
    sw = dict(PROPOSED)
    for entry in alternatives:
        switch, _, alternative = DECISIONS[entry]
        sw[switch] = alternative
    return sw


def _decode(raw, bom):
    if bom == "decode":
        if raw.startswith(b"\xef\xbb\xbf"):
            return raw[3:].decode("utf-8")
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return raw.decode("utf-16")
    return raw.decode("utf-8")  # strict: bytes that are not UTF-8 make the content unreadable


def _ascii_digits(token, digits):
    """The token's digits as an ASCII string, or None if it holds a character that is not an allowed digit."""
    out = []
    for ch in token:
        if "0" <= ch <= "9":
            out.append(ch)
        elif digits == "unicode" and unicodedata.category(ch) == "Nd":
            out.append(str(unicodedata.decimal(ch)))
        else:
            return None
    return "".join(out) or None


def integer_matches(token, n, sw):
    """(passes, reason) for one candidate integer token."""
    if token.startswith("+"):
        if sw["plus_sign"] != "allow":
            return False, "plus sign"
        token = token[1:]
    digits = _ascii_digits(token, sw["digits"])
    if digits is None:
        return False, "not a decimal integer"
    if len(digits) > 1 and digits[0] == "0" and sw["leading_zeros"] != "allow":
        return False, "leading zero"
    value = digits.lstrip("0") or "0"  # compared as text, so any length is safe
    if value != str(n):
        return False, "wrong count"
    return True, "correct"


def grade_text(raw, n=N, sw=None):
    """Grade the bytes of an answer file that exists. Returns (verdict, reason)."""
    sw = sw or PROPOSED
    if not raw:
        return "fail", "empty answer file"
    try:
        text = _decode(raw, sw["bom"])
    except UnicodeDecodeError:
        return "fail", "not UTF-8 text"
    ws = ASCII_WS if sw["whitespace"] == "ascii" else UNICODE_WS
    text = text.strip(ws)
    if not text:
        return "fail", "whitespace only"
    if any(unicodedata.category(ch) == "Cc" and ch not in ASCII_WS for ch in text):
        return "fail", "control character"
    if sw["surrounding_text"] == "allow":
        # Reading B: the file may hold other words if it holds exactly one integer. A chunk is a maximal run of
        # word characters and number punctuation; a sentence-final "." or "," is dropped; "41.0", "4,1", "4_1"
        # and "5xx" are not integers.
        digit = "[0-9]" if sw["digits"] == "ascii" else r"\d"
        chunks = [c.rstrip(".,") for c in re.findall(r"[\w.,+\-]+", text)]
        tokens = [c for c in chunks if re.fullmatch(rf"[+\-]?{digit}+", c)]
        if len(tokens) != 1:
            return "fail", f"{len(tokens)} standalone integers"
        text = tokens[0]
    if text.startswith("-"):
        return "fail", "negative number"
    ok, reason = integer_matches(text, n, sw)
    return ("pass" if ok else "fail"), reason


def grade_workspace(workspace, n=N, sw=None):
    """Grade a trial's final sandbox, given as the directory that was /workspace. Returns (verdict, reason)."""
    sw = sw or PROPOSED
    path = os.path.join(workspace, "out", "answer.txt")
    if os.path.islink(path) and sw["symlink"] == "regular":
        return "fail", "answer path is a symbolic link"
    if not os.path.isfile(path):  # follows links; a directory or a dangling link is not a file
        return "fail", "no answer file"
    with open(path, "rb") as f:
        raw = f.read()
    return grade_text(raw, n, sw)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workspace")
    ap.add_argument("--expected", type=int, default=N)
    for switch, proposed, alternative in DECISIONS.values():
        ap.add_argument("--" + switch.replace("_", "-"), dest=switch, choices=[proposed, alternative],
                        default=proposed)
    args = ap.parse_args(argv)
    sw = {switch: getattr(args, switch) for switch, _, _ in DECISIONS.values()}
    verdict, reason = grade_workspace(args.workspace, args.expected, sw)
    print(f"{verdict}: {reason}")
    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
