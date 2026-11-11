"""Replacement checker for count-server-errors, written from audit/CONTRACT.md (check V).

Usage: python3 check_answer.py ANSWER_FILE EXPECTED_JSON

Exit status 0 when ANSWER_FILE holds the expected count, 1 otherwise (including a missing or unreadable file).
Never raises on agent-controlled input.

One switch per decision entry, read from the environment (proposed reading first):

    D_SURROUNDING_TEXT  strict   | embedded   the file holds only the integer, or the integer may sit in text
    D_WHITESPACE        ascii    | unicode    which characters around the content are ignored
    D_LEADING_ZEROS     allow    | forbid     whether "041" counts
    D_PLUS_SIGN         forbid   | allow      whether "+41" counts
    D_NONASCII_DIGITS   forbid   | allow      whether non-ASCII decimal digits ("４１") count
"""

import json
import os
import re
import sys
import unicodedata

ASCII_WS = " \t\n\r\v\f"
# Characters with the Unicode White_Space property (Unicode 15). Python's str.isspace() also accepts
# U+001C..U+001F, which are not White_Space; they are deliberately absent here.
UNICODE_WS = (
    "\t\n\v\f\r \x85\xa0 "
    "           "
    "    　"
)

SWITCHES = {
    "D_SURROUNDING_TEXT": ("strict", "embedded"),
    "D_WHITESPACE": ("ascii", "unicode"),
    "D_LEADING_ZEROS": ("allow", "forbid"),
    "D_PLUS_SIGN": ("forbid", "allow"),
    "D_NONASCII_DIGITS": ("forbid", "allow"),
}


def settings(env):
    out = {}
    for name, allowed in SWITCHES.items():
        value = env.get(name, allowed[0])
        if value not in allowed:
            raise SystemExit(f"bad {name}={value!r}; expected one of {allowed}")
        out[name] = value
    return out


def _is_digit(ch, nonascii):
    if "0" <= ch <= "9":
        return True
    return nonascii and unicodedata.category(ch) == "Nd"


def _ascii_digits(s):
    return "".join(str(unicodedata.digit(ch)) for ch in s)


def integer_value_string(token, cfg):
    """Return the canonical ASCII decimal string of TOKEN, or None if TOKEN is not an allowed decimal integer."""
    nonascii = cfg["D_NONASCII_DIGITS"] == "allow"
    if token.startswith("+") and cfg["D_PLUS_SIGN"] == "allow":
        token = token[1:]
    if not token or not all(_is_digit(ch, nonascii) for ch in token):
        return None
    digits = _ascii_digits(token)
    if len(digits) > 1 and digits[0] == "0" and cfg["D_LEADING_ZEROS"] == "forbid":
        return None
    return digits.lstrip("0") or "0"


def embedded_tokens(text, cfg):
    """Standalone integer tokens: digit runs not touching letters, digits, '_', a sign or a decimal point."""
    nonascii = cfg["D_NONASCII_DIGITS"] == "allow"
    digit = r"\d" if nonascii else "[0-9]"
    sign = r"\+?" if cfg["D_PLUS_SIGN"] == "allow" else ""
    pattern = rf"(?<![\w.+\-]){sign}{digit}+(?![\w]|\.{digit})"
    return re.findall(pattern, text)


def verdict(raw, expected, cfg):
    """True when the bytes RAW of the answer file hold EXPECTED under the switches CFG."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    ws = ASCII_WS if cfg["D_WHITESPACE"] == "ascii" else UNICODE_WS
    text = text.strip(ws)
    if not text:
        return False
    want = str(expected)
    if cfg["D_SURROUNDING_TEXT"] == "strict":
        return integer_value_string(text, cfg) == want
    tokens = embedded_tokens(text, cfg)
    return len(tokens) == 1 and integer_value_string(tokens[0], cfg) == want


def main(argv, env):
    cfg = settings(env)
    answer_path, expected_path = argv[1], argv[2]
    with open(expected_path, encoding="utf-8") as f:
        expected = json.load(f)["server_error_count"]
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
        print(f"bad expected count {expected!r}")
        return 2
    try:
        if not os.path.isfile(answer_path):
            print("no answer file")
            return 1
        with open(answer_path, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(f"answer file unreadable: {type(e).__name__}")
        return 1
    if verdict(raw, expected, cfg):
        print("correct")
        return 0
    print("incorrect")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv, os.environ))
