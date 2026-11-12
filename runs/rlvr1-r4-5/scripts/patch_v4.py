"""One-off edit of audit/replacement.py for contract v4 (see ISSUE.md)."""
p = "<W>/audit/replacement.py"
s = open(p, encoding="utf-8").read()
rep = [
    ('''    "D-quote-curly",
)''', '''    "D-quote-curly", "D-hyphen-dash", "D-two-sep-edge", "D-consecutive-script", "D-postscript-line",
)'''),
    ('''"D-end-case": ALT, "D-quote-curly": ALT,
}''', '''"D-end-case": ALT, "D-quote-curly": ALT,
    "D-hyphen-dash": PROPOSED, "D-two-sep-edge": ALT, "D-consecutive-script": PROPOSED, "D-postscript-line": ALT,
}'''),
    ('''        if len(seps) != 1:
            return False
        a, b = t[: seps[0].start()], t[seps[0].end():]''', '''        if self.alt("D-two-sep-edge"):  # separators with no response before or after them are ignored
            seps = [m for m in seps if self.words(t[: m.start()]) and self.words(t[m.end():])]
        if len(seps) != 1:
            return False
        a, b = t[: seps[0].start()], t[seps[0].end():]'''),
    (r'''        pat = r"^[ \t]*(?:[*_>#]+[ \t]*)?" + re.escape(base) + dot + r"(?![A-Za-z])"''',
     r'''        if self.alt("D-postscript-line"):
            lead = r"(?:^|(?<=\s)|(?<=[\[(\"'“‘*_]))"
        else:
            lead = r"^[ \t]*(?:[*_>#\[(\"'“‘]+[ \t]*)?"
        pat = lead + re.escape(base) + dot + r"(?![A-Za-z])"'''),
    (r'''        pat = re.compile(r"^[ \t]*(?:#{1,6}[ \t]*)?(?:[*_]{1,3})?" + re.escape(spl) + r"[ \t]+(\d+)\b", flags)''',
     r'''        pat = re.compile(r"^[ \t]*[\"'“\[(]?[ \t]*(?:#{1,6}[ \t]*)?(?:[*_]{1,3})?" + re.escape(spl) + r"[ \t]+(\d+)\b", flags)'''),
    ('''        if not self.alt("D-sentence-lines"):
            if "\\n" in s:
                return False
        for m in TERMINAL.finditer(s):''', '''        if not self.alt("D-sentence-lines"):
            if "\\n" in s:
                return False
        dashes = "-\\u2010\\u2011\\u2012\\u2013\\u2014\\u2015" if self.alt("D-hyphen-dash") else "-\\u2010\\u2011"
        if re.search(r"\\s[" + dashes + r"]|[" + dashes + r"]\\s", s):
            return False  # clauses joined by a dash with a space: spaces between sentences
        if not self.alt("D-hyphen-dash") and re.search("[\\u2012\\u2013\\u2014\\u2015]", s):
            return False  # an en or em dash is not a hyphen
        for m in TERMINAL.finditer(s):'''),
    ('''            nxt = s[end]
            if nxt == "-":''', '''            nxt = s[end]
            if nxt in dashes:'''),
    ('''            c = w[0].lower()
            firsts.append(c if len(c) == 1 and "a" <= c <= "z" else None)
        for a, b in zip(firsts, firsts[1:]):
            if a is None or b is None:
                continue''', '''            c = w[0].lower()
            if len(c) == 1 and "a" <= c <= "z":
                firsts.append(("latin", c))
            elif len(c) == 1 and "\\u0430" <= c <= "\\u044f" and not self.alt("D-consecutive-script"):
                firsts.append(("cyrillic", c))
            elif len(c) == 1 and "\\u03b1" <= c <= "\\u03c9" and c != "\\u03c2" and not self.alt("D-consecutive-script"):
                firsts.append(("greek", c))
            else:
                firsts.append(None)
        for a, b in zip(firsts, firsts[1:]):
            if a is None or b is None or a[0] != b[0]:
                continue
            a, b = a[1], b[1]'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
