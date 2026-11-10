p = "audit/tests/fixtures_data.py"
s = open(p, encoding="utf-8").read()
rep = [
('fx("sentence:alliteration_increment", "fail", "near-miss", "Big bulbs glow. Many mighty machines. Soft songs sound sweetly.",\n   note="runs 2, 3, 4 ... wait: see note", )',
 'fx("sentence:alliteration_increment", "fail", "near-miss", "Big bulbs glow. Many mighty machines. Soft songs sound.",\n   note="runs 2, 3, 3")'),
('_OV = ("Is it easier to urbanize a jungle " +\n       "cities grow faster near rivers because water supports farms factories homes and trade routes across wide open plains")\nfx("ratio:overlap", "pass", "decision", _OV, key="149", note="5 of 25 response word trigrams (20%) ... see test for exact value",\n   decisions=("D-overlap",))',
 '_OV = "Is it easier to urbanize a jungle " + words(33)\nfx("ratio:overlap", "pass", "decision", _OV, key="149", note="5 of 38 distinct response word trigrams (13.2%) occur in the reference",\n   decisions=("D-overlap",))'),
('fx("count:unique_word_count", "pass", "pass", "The the THE " + words(35) + ".", key="24")',
 'fx("count:unique_word_count", "pass", "pass", "The the THE " + words(35) + ".", key="24", decisions=("D-unique",))'),
('fx("count:person_names", "fail", "near-miss", "Emma met Liam and emma again.", key="27", decisions=("D-names-case",))',
 'fx("count:person_names", "fail", "near-miss", "Emma met Liam and emma again.", key="27")'),
('fx("ratio:stop_words", "fail", "near-miss", "Python extracts the basename of a path very quickly today.", key="173",\n   note="the, of, a, very = 4 of 10")',
 'fx("ratio:stop_words", "fail", "near-miss", "Python extracts the basename.", key="173", note="1 of 4 = 25%")'),
('[f"Zz{chr(122 - i // 26)}{chr(122 - i % 26)}land"', '[f"Y{chr(122 - i // 26)}{chr(122 - i % 26)}land"'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
