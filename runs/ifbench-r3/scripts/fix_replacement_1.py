p = "audit/replacement/ifbench_contract.py"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('''def sentences(text, sw=None):
    """D-sentence. A: punctuation and line breaks end sentences; headings and label lines are not sentences."""
    r = R(sw, "D-sentence")
    text = norm_apos(HTML_TAG.sub("", text))
    if r == "B":
        return [s for s in nltk.sent_tokenize(text) if words(s)]''',
    '''def sentences(text, sw=None, keep_all=False):
    """D-sentence. A: punctuation and line breaks end sentences; headings and label lines are not sentences.

    keep_all keeps segments without words (an emoji after the last period), for format:emoji."""
    r = R(sw, "D-sentence")
    text = norm_apos(HTML_TAG.sub("", text))
    keep = (lambda x: x.strip()) if keep_all else words
    if r == "B":
        return [s for s in nltk.sent_tokenize(text) if keep(s)]''')
rep('''        l = LIST_MARKER.sub("", line).strip()
        for s in nltk.sent_tokenize(l):
            if words(s):
                out.append(s)
    return out''',
    '''        l = LIST_MARKER.sub("", line).strip()
        for s in nltk.sent_tokenize(l):
            if keep(s):
                out.append(s)
    return out''')
rep('''def c_emoji(t, kw, sw):
    ss = sentences(t, sw)''', '''def c_emoji(t, kw, sw):
    ss = sentences(t, sw, keep_all=True)''')
rep('''    for s in fixed:
        s2 = s.rstrip()''', '''    fixed = [s for s in fixed if words(s, sw)]
    if not fixed:
        return R(sw, "D-vacuous") == "B"
    for s in fixed:
        s2 = s.rstrip()''')

start = s.index("def c_char_reverse(t, kw, sw):")
end = s.index("def c_word_reverse(t, kw, sw):")
new_fn = r'''NORMAL_BIGRAMS = ["the national", "national symbol", "symbol of", "of the", "is the", "bald eagle", "the bald",
                  "american bald", "the united", "united states", "national animal", "national bird", "is a", "is an",
                  "the us", "us is", "symbol is", "animal is", "bird is"]


def _order_score(text):
    low = " ".join(re.findall(r"[a-z']+", text.lower()))
    return sum(low.count(b) for b in NORMAL_BIGRAMS)


def c_char_reverse(t, kw, sw):
    s = t.strip()
    rev = " ".join(w[::-1] for w in s.split()) if R(sw, "D-char-reverse") == "B" else s[::-1]
    if _order_score(s) > 0 or re.search(r"\beagle\b", s, re.I):
        return False  # normal-order text in the response
    flipped = " ".join(reversed(rev.split()))
    if _order_score(rev) <= _order_score(flipped):
        return False
    if R(sw, "D-custom-facts") == "B":
        return True
    return bool(re.search(r"\beagle\b", rev, re.I))


'''
s = s[:start] + new_fn + s[end:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
