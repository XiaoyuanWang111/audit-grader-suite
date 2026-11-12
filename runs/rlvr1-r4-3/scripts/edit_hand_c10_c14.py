"""One-off edit of fixtures_hand.py for contract changes C10-C14 (kept for the record)."""
import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(AUDIT, "fixtures_hand.py")
s = open(p, encoding="utf-8").read()
edits = [
    ('("combination:two_responses", {}, "******\\nFirst answer.\\n******\\nSecond answer.", "fail", "two separators"),',
     '("combination:two_responses", {}, "******\\nFirst answer.\\n******\\nSecond answer.", "pass", "a leading separator is ignored (D-separator-edge; label changed by contract change C11)"),\n'
     '    ("combination:two_responses", {}, "First answer.\\n******\\n******\\nSecond answer.", "fail", "two separators in a row"),'),
    ('("length_constraints:number_paragraphs", {"num_paragraphs": 1}, "Just one paragraph without dividers.", "pass", "one part"),',
     '("length_constraints:number_paragraphs", {"num_paragraphs": 1}, "Just one paragraph without dividers.", "pass", "one part"),\n'
     '    ("length_constraints:number_paragraphs", {"num_paragraphs": 1}, "***\\n\\nOne paragraph after a stray divider.", "pass", "leading divider ignored (D-separator-edge)"),\n'
     '    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First part of the text. *** Second part of the text.", "pass", "inline divider between spaces (D-divider-inline)"),'),
    ('("detectable_format:sentence_hyphens", {}, "I like well-made tea.-You like coffee.", "pass", "hyphenated word inside a sentence"),',
     '("detectable_format:sentence_hyphens", {}, "I like well-made tea.-You like coffee.", "pass", "hyphenated word inside a sentence"),\n'
     '    ("detectable_format:sentence_hyphens", {}, "Visit the park - see the lake - enjoy the view", "fail", "clauses joined by spaced hyphens (C10)"),\n'
     '    ("detectable_format:sentence_hyphens", {}, "We went home\\u2014it was late\\u2014we slept", "fail", "clauses joined by em dashes (C10)"),'),
    ('("keywords:palindrome", {}, "Mom is here.", "pass", "Mom"),',
     '("keywords:palindrome", {}, "Mom is here.", "pass", "Mom"),\n'
     '    ("keywords:palindrome", {}, "Is a da vinci here?", "fail", "a da reads the same backwards by chance; not a palindrome phrase (C13)"),'),
    ('"## SECTION 1\\nFirst.\\n## SECTION 2\\nSecond.", "pass", "markdown headings"),',
     '"## SECTION 1\\nFirst.\\n## SECTION 2\\nSecond.", "pass", "markdown headings"),\n'
     '    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "\\"SECTION 1\\nFirst.\\nSECTION 2\\nSecond.\\"", "pass", "a quote before the first marker (C14)"),'),
]
for a, b in edits:
    if s.count(a) != 1:
        sys.exit("not found: " + a[:70])
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("edited")
