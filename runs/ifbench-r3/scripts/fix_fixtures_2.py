p = "audit/tests/fixtures_data.py"
s = open(p, encoding="utf-8").read()
rep = [
('   note="only \'and\' in three surface forms (case, trailing comma)", grader="F-conj-surface-forms")',
 '   note="only \'and\' in three surface forms (case, trailing comma)", grader="F-conj-surface-forms",\n   reference="F-conj-surface-forms")'),
('fx("ratio:overlap", "pass", "decision", _OV, key="149", note="5 of 38 distinct response word trigrams (13.2%) occur in the reference",\n   decisions=("D-overlap",))',
 'fx("ratio:overlap", "pass", "decision", _OV, key="149", note="5 of 38 distinct response word trigrams (13.2%) occur in the reference",\n   decisions=("D-overlap",), grader="D-overlap")'),
('fx("words:start_verb", "pass", "pass", "Imagine an empire built on eternal suffering.", key="257")',
 'fx("words:start_verb", "pass", "pass", "Imagine an empire built on eternal suffering.", key="257",\n   note="the tagger reads \'Imagine\' as a proper noun", grader="F-startverb-tagger", reference="F-startverb-tagger")\nfx("words:start_verb", "pass", "pass", "Consider an empire where minds suffer.", key="257")'),
('fx("words:start_verb", "pass", "defect", "Build an empire of endless pain.", key="257", note="tagger check")',
 'fx("words:start_verb", "pass", "defect", "Build an empire of endless pain.", key="257", note="tagger reads \'Build\' as a proper noun",\n   grader="F-startverb-tagger", reference="F-startverb-tagger")\nfx("words:start_verb", "pass", "defect", "Explore the idea of an empire.", key="257", note="tagger reads \'Explore\' as a preposition",\n   grader="F-startverb-tagger", reference="F-startverb-tagger")'),
('fx("repeat:repeat_change", "fail", "near-miss", _RQ.strip(), key="61", note="first word unchanged")',
 'fx("repeat:repeat_change", "fail", "near-miss", _RQ.strip(), key="61", note="first word unchanged")\nfx("repeat:repeat_change", "fail", "defect", _RQ.strip() + "\n", key="61", note="first word unchanged, trailing newline",\n   grader="F-repeatchange-whitespace", reference="F-repeatchange-whitespace")'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
