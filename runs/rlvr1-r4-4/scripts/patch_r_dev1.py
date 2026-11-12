"""One-off patch: replacement-grader changes found on development panel responses (logged in ISSUE.md)."""
import os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "replacement", "contract_grader.py")
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


# R change 7: a *** that is not markdown emphasis is a divider, wherever it stands (contract change 6)
rep(r'''        parts = DIVIDER_LINE.split(text)''', r'''        parts = _mark_dividers(text).split("\x00")''')
rep(r'''def divider_paragraphs(text: str, r: dict) -> list[str] | None:''',
    r'''def _mark_dividers(text: str) -> str:
    """Replace every `***` (or `* * *`) that is not markdown emphasis with a NUL separator.

    On each line, an opening `***` (followed by a non-space) pairs with a later closing `***`
    (preceded by a non-space) as bold-italic emphasis; every unpaired run is a divider.
    """
    out_lines = []
    for line in text.split("\n"):
        if DIVIDER_LINE.fullmatch(line):
            out_lines.append("\x00")
            continue
        runs = list(re.finditer(r"(?<!\*)\*\*\*(?!\*)", line))
        paired = set()
        i = 0
        while i < len(runs):
            m = runs[i]
            nxt = line[m.end():m.end() + 1]
            if nxt and not nxt.isspace():
                for j in range(i + 1, len(runs)):
                    prev = line[runs[j].start() - 1:runs[j].start()]
                    if prev and not prev.isspace():
                        paired.update({i, j})
                        i = j
                        break
            i += 1
        new = line
        for k in sorted(set(range(len(runs))) - paired, reverse=True):
            new = new[:runs[k].start()] + "\x00" + new[runs[k].end():]
        out_lines.append(new)
    return "\n".join(out_lines)


def divider_paragraphs(text: str, r: dict) -> list[str] | None:''')

# R change 3: a lowercase word needs a lowercase letter (words of caseless scripts are not lowercase)
rep(r'''    lower_forms = [core(w) for w in ws if any(c.isalpha() for c in w) and not any(c.isupper() for c in w)]''',
    r'''    lower_forms = [core(w) for w in ws if any(c.islower() for c in w) and not any(c.isupper() for c in w)]''')

# R change 4: a section marker may follow a quote mark, or stand after a sentence and end its line
rep(r'''MARKDOWN_LEAD = r"[ \t>#*_~`]*"''', r'''MARKDOWN_LEAD = r"[ \t>#*_~`\"“']*"''')
rep(r'''    pat = re.compile(r"(?m)^" + MARKDOWN_LEAD + re.escape(spl) + r"[ \t]+(\d+|[IVXLC]+|[A-Za-z])\b(.*)$", flags)
    ms = list(pat.finditer(t))''',
    r'''    pat = re.compile(r"(?m)^" + MARKDOWN_LEAD + re.escape(spl) + r"[ \t]+(\d+|[IVXLC]+|[A-Za-z])\b(.*)$", flags)
    mid = re.compile(r"(?m)(?<=[.!?:。][ \t]{1,3})" + re.escape(spl) + r"[ \t]+(\d+|[IVXLC]+|[A-Za-z])()[ \t:.*]*$", flags)
    ms = sorted(list(pat.finditer(t)) + list(mid.finditer(t)), key=lambda m: m.start())''')

# R change 5: asterisk emphasis may stand inside a word (CommonMark); underscore emphasis may not
rep(r'''    bold = re.compile(r"(?<![*\w])(\*\*\*?|__)(?![\s*_])([^\n*]+?)(?<![\s*_])\1(?![*\w])")
    ital = re.compile(r"(?<![*\w])([*_])(?![\s*_])([^\n*_]+?)(?<![\s*_])\1(?![*\w])")''',
    r'''    bold = re.compile(r"(?<!\*)(\*\*\*?)(?![\s*])([^\n*]+?)(?<![\s*])\1(?!\*)|(?<![\w_])(__)(?![\s_])([^\n_]+?)(?<![\s_])__(?![\w_])")
    ital = re.compile(r"(?<!\*)(\*)(?![\s*])([^\n*]+?)(?<![\s*])\*(?!\*)|(?<![\w_])(_)(?![\s_])([^\n_]+?)(?<![\s_])_(?![\w_])")''')
rep(r'''        n += len([m for m in bold.finditer(t) if m.group(2).strip()])''',
    r'''        n += len([m for m in bold.finditer(t) if (m.group(2) or m.group(4) or "").strip()])''')
rep(r'''    n += len([m for m in ital.finditer(t2) if m.group(2).strip() and''',
    r'''    n += len([m for m in ital.finditer(t2) if (m.group(2) or m.group(4) or "").strip() and''')

# R change 6: every word, read with the brackets removed, must sit inside one bracket pair
rep(r'''    for _, _, inner in spans:
        k = len(words(inner, {**r, "D-word": "proposed"}))
        if r["D-bracket-group"] == "proposed" and k > 1:
            return False
    return True''',
    r'''    for _, _, inner in spans:
        k = len(words(inner, {**r, "D-word": "proposed"}))
        if r["D-bracket-group"] == "proposed" and k > 1:
            return False
    span_id = [-1] * len(t)
    for n_, (a, b, _) in enumerate(spans):
        for x in range(a + 1, b - 1):
            span_id[x] = n_
    keep = [i for i, ch in enumerate(t) if ch not in "[]"]
    flat = "".join(t[i] for i in keep)
    for m in WORD_RE.finditer(flat):
        ids = {span_id[keep[x]] for x in range(m.start(), m.end())}
        if len(ids) != 1 or -1 in ids:
            return False
    return True''')

# R change 1: a spaced hyphen or dash joins two sentences with spaces
rep(r'''    if "\n" in s:
        return False
    hy = ''', r'''    if "\n" in s:
        return False
    if re.search(r"\s[-‐‑–—]+\s", s):
        return False
    hy = ''')

# R change 8 (contract change 7): D-consecutive-script; the alternative compares letters of any alphabet
rep(r'''        firsts.append(c if c and "a" <= c <= "z" else None)''',
    r'''        if r["D-consecutive-script"] == "alt":
            firsts.append(c if c and c.isalpha() else None)
        else:
            firsts.append(c if c and "a" <= c <= "z" else None)''')
rep(r'''    "D-start-end-one-word",
]''', r'''    "D-start-end-one-word", "D-consecutive-script", "D-two-responses-edge",
]''')

# R change 9 (contract change 8): D-two-responses-edge; the alternative ignores a separator at the start or end
rep(r'''def _c_two_responses(t, kw, r):
    runs = re.findall(r"\*{6,}", t)''',
    r'''def _c_two_responses(t, kw, r):
    if r["D-two-responses-edge"] == "alt":
        t = re.sub(r"^\s*\*{6}\s*|\s*\*{6}\s*$", "", t)
    runs = re.findall(r"\*{6,}", t)''')

# R change 2: "entire response in <language>": every paragraph of 10+ letters is at least half in its script
rep(r'''    if share < need:
        return False
    if script == "Latin":''',
    r'''    if share < need:
        return False
    if r["D-language-mixed"] == "proposed":
        for para in re.split(r"\n[ \t]*\n", text):
            pl = [c for c in para if c.isalpha()]
            if len(pl) >= 10 and sum(1 for c in pl if _in_script(c, script)) / len(pl) < 0.5:
                return False
    if script == "Latin":''')

open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
