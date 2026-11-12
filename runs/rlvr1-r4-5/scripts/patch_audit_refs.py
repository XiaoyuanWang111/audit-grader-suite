p = "<W>/audit/AUDIT.md"
s = open(p, encoding="utf-8").read()
rep = [
("| G1: unclosed reasoning is an extraction failure and fails every check; the reasoning is never graded |",
 "| Contract rule G1: unclosed reasoning is an extraction failure and fails every check; the reasoning is never graded |"),
("| G9: an exception is a per-constraint grading failure counted apart from model accuracy; it must not discard the row's other verdicts |",
 "| Contract rule G9: an exception is a per-constraint grading failure counted apart from model accuracy; it must not discard the row's other verdicts |"),
("| G3/G6: punctuation attached to a word is not part of it; `!!` ends one sentence |",
 "| Contract rules G3/G6: punctuation attached to a word is not part of it; `!!` ends one sentence |"),
("| G2: surrounding whitespace is ignored |", "| Contract rule G2: surrounding whitespace is ignored |"),
("Contract broken | Share affected (panel) | Status in reference |",
 "Contract broken (rules G1-G9 are CONTRACTS.md's general rules, not findings) | Share affected (panel) | Status in reference |"),
("| 91 of 282 panel verdicts on these rows: NV fail, contract pass |",
 "| 91 of 282 panel verdicts on these rows: NV fail, contract pass (section 5 counts them under D-postscript-dot) |"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
