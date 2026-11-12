p = 'replacement/contract_grader.py'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) >= 1, old[:80]
    s = s.replace(old, new, 1)


rep('''def words(text: str, d: dict) -> list[str]:
    if d["D-word"] == "joined":''', '''def visible(text: str) -> str:
    return INLINE_HTML.sub("", text)


def words(text: str, d: dict) -> list[str]:
    text = visible(text)
    if d["D-word"] == "joined":''')
rep('''    if instruction_id not in RAW_STRUCTURE_CHECKS and not (
            d["D-edge-word"] == "raw" and instruction_id in EDGE_WORD_CHECKS):
        text = INLINE_HTML.sub("", text)
    return bool(CHECKS[instruction_id](text, kw, d))''', '''    if not text.strip() and d["D-empty"] == "literal" and instruction_id in VACUOUS_PASS:
        return True
    return bool(CHECKS[instruction_id](text, kw, d))


# Under the literal reading of D-empty, an empty text passes the checks that only forbid something
# or quantify over every word or sentence (vacuous truth).
VACUOUS_PASS = {
    "count:count_unique", "detectable_format:bigram_wrapping", "detectable_format:square_brackets",
    "detectable_format:sentence_hyphens", "first_word:first_word_sent", "last_word:last_word_sent",
    "language:response_language", "punctuation:no_comma", "punctuation:punctuation_dot",
    "punctuation:punctuation_exclamation", "keywords:forbidden_words", "keywords:no_adjacent_consecutive",
    "count:lowercase_counting", "change_case:english_lowercase", "change_case:english_capital",
}''')
rep('''        if not letters or any(c.islower() for c in letters):
            continue''', '''        if not any(c.isupper() for c in letters) or any(c.islower() for c in letters):
            continue''')
rep('''def _is_english(t):
    lang = detect_language(t.lower())''', '''def _is_english(t):
    if any(c.isalpha() and not unicodedata.name(c, "").startswith("LATIN") for c in t):
        return False
    lang = detect_language(t.lower())''')
rep('''    "D-placeholder-form": "wordlike",''', '''    "D-placeholder-form": ["wordlike", "blank_ok"],''')
rep('''    if d["D-placeholder-form"] == "any":''', '''    if d["D-placeholder-form"] == "blank_ok":
        found = re.findall(r"\\[[^\\[\\]\\n]*\\]", t)
    elif d["D-placeholder-form"] == "any":''')
rep('''    "D-postscript-pps": False,''', '''    "D-postscript-pps": False,
    "D-postscript-case": "cs",''')
rep('''    "D-postscript-pps": True,''', '''    "D-postscript-pps": True,
    "D-postscript-case": "ci",''')
rep('''"D-postscript-position", "D-postscript-pps"],''', '''"D-postscript-position", "D-postscript-pps", "D-postscript-case"],''')
rep('''    line_re = re.compile(r"^[ \\t>*_#]*" + pattern + r"(?![A-Za-z.])(.*)$", re.MULTILINE)''',
    '''    flags = re.MULTILINE | (re.IGNORECASE if d["D-postscript-case"] == "ci" else 0)
    line_re = re.compile(r"^[ \\t>*_#]*" + pattern + r"(?![A-Za-z.])(.*)$", flags)''')
rep('''    return bool(ws) and len(ws) == len(set(ws))''', '''    return len(ws) == len(set(ws))''')
rep('''def _letter_counting(t, kw, d):
''', '''def _letter_counting(t, kw, d):
    t = visible(t)
''')
rep('''def _letter_frequency(t, kw, d):
    letter = kw["letter"]''', '''def _letter_frequency(t, kw, d):
    t = visible(t)
    letter = kw["letter"]''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched')
