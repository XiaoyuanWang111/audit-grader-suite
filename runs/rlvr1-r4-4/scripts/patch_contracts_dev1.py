"""One-off edit of audit/CONTRACTS.md: contract changes 5-10 (reasons in ISSUE.md)."""
import os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CONTRACTS.md")
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep("PASS iff the graded text contains the separator `******` exactly once, no longer run of",
    "(Change 8: `D-two-responses-edge`: proposed: a separator at the very start or end is an extra\n"
    "separator and fails; alternative: it is ignored.)\n"
    "PASS iff the graded text contains the separator `******` exactly once, no longer run of")
rep("PASS iff every word written in lowercase occurs, in lowercase, at most N times.",
    "PASS iff every word written in lowercase occurs, in lowercase, at most N times. (Change 10: a word\n"
    "written in lowercase has at least one lowercase letter and no uppercase letter; words of\n"
    "caseless scripts such as Han or Gurmukhi are not lowercase words.)")
rep('alternative: exact case. A mention of "Section 2" inside a sentence is not a marker.',
    'alternative: exact case. A mention of "Section 2" inside a sentence is not a marker. (Change 6:\n'
    'a marker may also follow an opening quote mark, or follow a sentence\'s end and close its line,\n'
    'as in "...the end. SECTION 2" followed by a line break.)')
rep("PASS iff every word (G3) is inside a pair of square brackets that encloses only that word",
    "(Change 10: words are read with the brackets removed, so `[J][u][s][t]` is the word Just split\n"
    "over four pairs and fails.)\n"
    "PASS iff every word (G3) is inside a pair of square brackets that encloses only that word")
rep("PASS iff the response's prose is written in the named language. Proper names, code, numbers,",
    "(Change 9: under the proposed reading, a paragraph of ten or more letters written mostly in\n"
    "another script fails the whole response; this also applies to \"in English\" in the change_case\n"
    "contracts.)\n"
    "PASS iff the response's prose is written in the named language. Proper names, code, numbers,")
rep("paragraphs. `D-divider-form` (see counting_composition): proposed: any line that is a markdown\n"
    "thematic break of asterisks (`***`, `* * *`, `****`); alternative: the literal `***` anywhere.",
    "paragraphs. `D-divider-form` (see counting_composition): proposed (Change 5): a `***` or\n"
    "`* * *` that is not markdown emphasis, wherever it stands (on its own line, or at the end or\n"
    "start of a paragraph's line); alternative: only a line that is exactly `***`.")
rep("Words whose first character is not a Latin letter never form such a pair.",
    "Words whose first character is not a Latin letter never form such a pair.\n"
    "`D-consecutive-script` (Change 7): proposed: only the Latin alphabet a-z; alternative: letters\n"
    "of any alphabet that are neighbours in Unicode order (Cyrillic в then г).") if "Words whose first character is not a Latin letter never form such a pair." in s else None
rep("| D-start-end-one-word (Change 3) | one-word response passes | fails |",
    "| D-start-end-one-word (Change 3) | one-word response passes | fails |\n"
    "| D-consecutive-script (Change 7) | Latin a-z only | any alphabet |\n"
    "| D-two-responses-edge (Change 8) | leading or trailing separator fails | ignored |")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
