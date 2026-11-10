"""Replacement fixes found by inspecting NON-held-out disagreements (audit/scripts/inspect_disagreements.py)."""
p = "audit/replacement/ifbench_contract.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


# 1. words:start_verb: tag the first word both as written and lower-cased; third-person forms; "here's" is not a verb
rep("reflect focus visualize ponder contemplate observe introduce present behold here's\"\"\".split())",
    "reflect focus visualize ponder contemplate observe introduce present\"\"\".split())")
rep('''    toks2 = [first.lower()] + toks[1:] if toks else [first.lower()]
    tag = nltk.pos_tag(toks2)[0][1]
    if R(sw, "D-verb") == "B" and tag in ("VBG", "VBN"):
        return False
    return tag.startswith("VB") or first.lower() in IMPERATIVES''',
    '''    toks2 = [first.lower()] + toks[1:] if toks else [first.lower()]
    tags = {nltk.pos_tag(toks2)[0][1], nltk.pos_tag([first] + toks[1:] if toks else [first])[0][1]}
    low = first.lower()
    stem_ok = low in IMPERATIVES or (low.endswith("s") and (low[:-1] in IMPERATIVES or low[:-2] in IMPERATIVES))
    if R(sw, "D-verb") == "B":
        tags = {t for t in tags if t not in ("VBG", "VBN")}
        if low.endswith("ing") or low.endswith("ed"):
            return False
    return any(t.startswith("VB") for t in tags) or stem_ok''')
# 2. format:thesis: HTML wrappers (<p>, <blockquote>, <div>) may precede the italic thesis; HTML headings are headings
rep('''def _is_heading(l):
    l = l.strip()
    return bool(l) and (l.startswith("#") or re.fullmatch(r"(\\*\\*|__)[^*_]+(\\*\\*|__):?", l) is not None)''',
    '''def _is_heading(l):
    l = l.strip()
    return bool(l) and (l.startswith("#") or re.fullmatch(r"(\\*\\*|__)[^*_]+(\\*\\*|__):?", l) is not None
                        or re.fullmatch(r"<(h[1-6]|b|strong)>.*?</\\1>:?", l, flags=re.I) is not None)''')
rep('''        m = re.match(r"\\s*(?:[-*>]\\s+)?<(i|em)>(.*?)</\\1>", s, flags=re.I | re.S)''',
    '''        m = re.match(r"\\s*(?:<(?!/?(?:i|em)\\b)[a-z][^>]*>\\s*)*(?:[-*>]\\s+)?<(i|em)>(.*?)</\\1>", s, flags=re.I | re.S)''')
# 3. format:quote_unquote: guillemets and low-high quotes are quotation marks too
rep('''    for m in re.finditer(r'"[^"\\n]+"|''', '''    for m in re.finditer(r'\u00ab[^\u00bb]+\u00bb|\u201e[^\u201c\u201d]+[\u201c\u201d]|"[^"\\n]+"|''')
# 4. format:list: the contract names *, \u2022 and "-" as other bullet symbols, not numbers
rep('''    other_bullet = [l for l in lines if re.match(r"^\\s*([*\u2022]|\\d+[.)])\\s", l) or''',
    '''    other_bullet = [l for l in lines if re.match(r"^\\s*[*\u2022]\\s", l) or''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
