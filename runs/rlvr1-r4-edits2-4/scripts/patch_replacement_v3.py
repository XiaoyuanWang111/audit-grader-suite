"""One-off patch: replacement grader v2 -> v3 (reasons recorded in audit/ISSUE.md)."""
from pathlib import Path

p = Path("<W>/audit/lib/contract_grader.py")
s = p.read_text(encoding="utf-8")
repl = [
    # 1. an HTML tag is never part of a << >> group
    ('HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*\\s*/?>")',
     'HTML_TAG = re.compile(r"(?<!<)</?[A-Za-z][A-Za-z0-9]*\\s*/?>(?!>)")'),
    # 2. reading A of D-language-mixed: whole-text detection only; B: every sentence of 3+ words
    ('''        """Reading A: the whole text and every sentence of 5+ words detect as the language
        (names, numbers, code and short phrases are allowed). Reading B: every sentence."""
        if self.detect(text) != code:
            return False
        min_words = 5 if self.r["D-language-mixed"] == "A" else 1''',
     '''        """Reading A: the whole text detects as the language (langdetect, an approximation that
        misses a sentence in another language). Reading B: also every sentence of 3+ words."""
        if self.detect(text) != code:
            return False
        if self.r["D-language-mixed"] == "A":
            return True
        min_words = 3'''),
    # 3. letter counts are literal characters (no HTML stripping)
    ('        letter = kw["letter"]\n        g = HTML_TAG.sub("", g)\n', '        letter = kw["letter"]\n'),
]
for a, b in repl:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched v3")
