"""One-off edit of audit/fixtures_src.py: isolate each defect in its fixture (see ISSUE.md)."""
p = "<W>/audit/fixtures_src.py"
s = open(p, encoding="utf-8").read()
reps = [
('F(FA, {"first_word": "development"}, "Development, as a concept, matters.", "pass", "the comma is not part of the word"),',
 'F(FA, {"first_word": "development"}, "development, as a concept, matters.", "pass", "the comma is not part of the word"),'),
('F(FA, {"first_word": "development"}, "Development: a summary.", "pass", "the colon is not part of the word"),',
 'F(FA, {"first_word": "development"}, "development: a summary.", "pass", "the colon is not part of the word"),'),
('F(FS, {"first_word": "we"}, "We, the people, run. We jump!", "pass", "the comma is not part of the word"),',
 'F(FS, {"first_word": "we"}, "we, the people, run. we jump!", "pass", "the comma is not part of the word"),\n'
 '    F(FS, {"first_word": "we"}, "we run\\nthey jump", "fail", "two lines are two sentences (D-sentence-lines)"),'),
('F(NF, NFK, "Intro text.\\n\\nHome: where we live.", "pass", "the colon is not part of the word"),',
 'F(NF, NFK, "Intro text.\\n\\nhome: where we live.", "pass", "the colon is not part of the word"),'),
('F(RP, PHR, "Live each moment to the fullest. Live each day to their fullest.", "pass", "two one-word inner changes"),',
 'F(RP, PHR, "Live each moment to the fullest. Live each day for the fullest.", "pass", "two one-word changes of a middle word"),\n'
 '    F(RP, PHR, "Live each moment to the fullest. Live each day to their fullest.", "pass", "two one-word inner changes"),'),
('F(NC, {}, "Okay, let me think about this answer and plan it", "fail",',
 'F(NC, {}, "Okay let me think about this answer and plan it", "fail",'),
('F(NW, {"relation": "less than", "num_words": 3}, "Don\'t stop.", "pass", "a contraction is one word"),',
 'F(NW, {"relation": "less than", "num_words": 3}, "Don\'t stop.", "pass", "a contraction is one word"),\n'
 '    F(NW, {"relation": "at least", "num_words": 5}, "\u6211\u4eec \u4eca\u5929 \u53bb \u516c\u56ed \u73a9\u3002", "pass", "five space-separated words of another script"),'),
('F(BL, {"num_bullets": 3}, "* one\\n* two\\n* three\\n-5 degrees is cold.", "pass",',
 'F(BL, {"num_bullets": 3}, "* one\\n* two\\n* three\\n\\n* * *\\n\\nDone.", "pass", "* * * is a horizontal rule, not a bullet"),\n'
 '    F(BL, {"num_bullets": 3}, "* one\\n* two\\n* three\\n-5 degrees is cold.", "pass",'),
]
for a, b in reps:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
