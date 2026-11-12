"""One-off patch: replacement grader v1 -> v2 (reasons recorded in audit/ISSUE.md)."""
from pathlib import Path

p = Path("<W>/audit/lib/contract_grader.py")
s = p.read_text(encoding="utf-8")
repl = [
    ('    "D-consecutive-order": "A",\n', '    "D-consecutive-order": "A",\n    "D-consecutive-script": "A",\n'),
    ('"ph.d", "cf", "al",\n}', '"ph.d", "cf", "al", "p.s", "p.p.s",\n}'),
    ('        found = pattern.findall(text)', '        found = pattern.findall(HTML_TAG.sub(" ", text))'),
    ('        g = HTML_TAG.sub("", g)  # HTML tags are markup, not words\n', ''),
    ('    def c_change_case__english_capital(self, g, kw):\n        if any',
     '    def c_change_case__english_capital(self, g, kw):\n        g = HTML_TAG.sub("", g)\n        if any'),
    ('    def c_change_case__english_lowercase(self, g, kw):\n        if any',
     '    def c_change_case__english_lowercase(self, g, kw):\n        g = HTML_TAG.sub("", g)\n        if any'),
    ('        letter = kw["letter"]\n        if self.r["D-letter-case"]',
     '        letter = kw["letter"]\n        g = HTML_TAG.sub("", g)\n        if self.r["D-letter-case"]'),
    ('            body = re.sub(r"^[\\s*_#>]+", "", p)',
     '            body = re.sub(r"^(?:[\\s*_#>]|</?[A-Za-z][A-Za-z0-9]*>)+", "", p)'),
    ('r"^[ \\t]*[#*_>]*[ \\t]*" + re.escape(splitter)',
     'r"^(?:[ \\t#*_>]|</?[A-Za-z][A-Za-z0-9]*>)*" + re.escape(splitter)'),
    ('            firsts.append(c if "a" <= c <= "z" else None)\n',
     '            if self.r["D-consecutive-script"] == "A":\n                firsts.append(c if "a" <= c <= "z" else None)\n'
     '            else:\n                firsts.append(c if c.isalpha() else None)\n'),
]
for a, b in repl:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
