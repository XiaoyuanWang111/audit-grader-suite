"""One-off patch 2 of the replacement (development responses only; logged in ISSUE.md)."""
import os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "replacement", "contract_grader.py")
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


# R change 10: any non-letter, non-digit character may follow a postscript marker (fullwidth colon)
rep(r'''    pat = r"(?m)^" + MARKDOWN_LEAD + core_pat + r"\.?(?=[\s:.\-–—*_)]|$)"''',
    r'''    pat = r"(?m)^" + MARKDOWN_LEAD + core_pat + r"\.?(?![\p{L}\p{N}])"''')
rep(r'''ANY_PS = re.compile(r"(?mi)^" + MARKDOWN_LEAD + r"(?:P\.\s?)+S\.?(?=[\s:.\-*_)]|$)")''',
    r'''ANY_PS = re.compile(r"(?mi)^" + MARKDOWN_LEAD + r"(?:P\.\s?)+S\.?(?![\p{L}\p{N}])")''')

# R change 11 (replaces the word-merging test of change 6): a pair holding one letter that touches
# another one-letter pair encloses a fragment of a word, not a word
rep(r'''    keep = [i for i, ch in enumerate(t) if ch not in "[]"]
    flat = "".join(t[i] for i in keep)
    for m in WORD_RE.finditer(flat):
        ids = {span_id[keep[x]] for x in range(m.start(), m.end())}
        if len(ids) != 1 or -1 in ids:
            return False
    return True''',
    r'''    for (a1, b1, i1), (a2, b2, i2) in zip(spans, spans[1:]):
        if b1 == a2 and len(i1.strip()) == 1 and len(i2.strip()) == 1 and i1.strip().isalpha() and i2.strip().isalpha():
            return False
    return True''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
