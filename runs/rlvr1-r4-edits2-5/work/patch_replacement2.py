p = 'replacement/contract_grader.py'
lines = open(p, encoding='utf-8').read().split('\n')


def setline(no, expect, new):
    assert lines[no - 1].strip() == expect.strip(), (no, lines[no - 1])
    lines[no - 1] = new


# Proposed (PROPOSED dict) and alternative (ALTERNATIVES dict) values, swapped for three case entries.
setline(32, '"D-postscript-case": "cs",', '    "D-postscript-case": "ci",\n    "D-postscript-line": "line_or_sentence",\n    "D-two-responses-edge": "fail",')
setline(37, '"D-sections-case": "cs",', '    "D-sections-case": "ci",')
setline(61, '"D-end-case": "cs",', '    "D-end-case": "ci",')
setline(84, '"D-postscript-case": "ci",', '    "D-postscript-case": "cs",\n    "D-postscript-line": "line",\n    "D-two-responses-edge": "ignore",')
setline(89, '"D-sections-case": "ci",', '    "D-sections-case": "cs",')
setline(113, '"D-end-case": "ci",', '    "D-end-case": "cs",')
setline(122, '"combination:two_responses": ["D-asterisk-run"],', '    "combination:two_responses": ["D-asterisk-run", "D-two-responses-edge"],')
setline(128, '"detectable_content:postscript": ["D-postscript-marker", "D-postscript-position", "D-postscript-pps", "D-postscript-case"],',
        '    "detectable_content:postscript": ["D-postscript-marker", "D-postscript-position", "D-postscript-pps", "D-postscript-case", "D-postscript-line"],')
s = '\n'.join(lines)


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)


rep('''    line_re = re.compile(r"^[ \\t>*_#]*" + pattern + r"(?![A-Za-z.])(.*)$", flags)''',
    '''    start = r"^[ \\t>*_#]*" if d["D-postscript-line"] == "line" else r"(?:^[ \\t>*_#]*|(?<=[.!?\\u3002])[ \\t]+[*_]*)"
    line_re = re.compile(start + pattern + r"(?![A-Za-z.])(.*)$", flags)''')
rep('''def _two_responses(t, kw, d):
    if d["D-asterisk-run"] == "substring":''', '''def _two_responses(t, kw, d):
    if d["D-two-responses-edge"] == "ignore":
        t = re.sub(r"^\\s*\\*{6}\\s*", "", t)
        t = re.sub(r"\\s*\\*{6}\\s*$", "", t)
    if d["D-asterisk-run"] == "substring":''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched')
