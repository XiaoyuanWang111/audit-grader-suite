p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()
old = "## Decision entries\n\n(pending)\n"
new = """## Decision entries

47 entries, each with both readings, an example of each and the proposed reading, in the table at
the end of `audit/CONTRACT.md` (version 2): D-vacuous, D-word, D-word-numbers, D-sentence,
D-paragraph, D-match, D-keyword-count, D-conj, D-number, D-names-case, D-pronoun, D-punct-set,
D-unique, D-between, D-japanese, D-emoji-position, D-indent, D-list, D-options, D-template,
D-paren, D-subbullet, D-section, D-title, D-overlap, D-balance, D-char-count, D-different-words,
D-stopwords, D-repeat-change, D-repeat-simple, D-span, D-alliteration, D-alphabet-start, D-y,
D-syllables, D-palindrome, D-prime-length, D-repeat-count, D-verb, D-vowel, D-custom-facts,
D-custom-extra-text, D-csv, D-char-reverse, D-mcq, D-trailing-ws.

Where the grader takes a non-proposed reading (from the step 3 fixtures and the step 5 switch
counts): D-vacuous B (a lone period passes 14 checks that the contract fails, step 4), D-word C (standalone punctuation tokens are
words), D-sentence B (line breaks do not end sentences), D-match B (substring keyword counts),
D-conj B, D-punct-set below B (see F-punct-six-marks), D-overlap D (character trigrams), D-paren C,
D-subbullet B, D-section B, D-title B, D-template C, D-csv C and E, D-custom-facts B and C,
D-palindrome B and C, D-repeat-change C, D-paragraph C, D-options D, D-indent C. Counts of the
panel verdicts each switch changes are in `audit/work/analyze_panel.log`.
"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
