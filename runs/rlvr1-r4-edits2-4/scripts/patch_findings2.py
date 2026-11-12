from pathlib import Path
p = Path("<W>/audit/lib/findings.py")
s = p.read_text(encoding="utf-8")
s = s.replace('''METAMORPHIC_REFS = [
''', '''METAMORPHIC_REFS = [
    ("detectable_format:bigram_wrapping", "replacement", "html", "replacement limitation: an HTML tag before >> is not removed"),
''', 1)
s = s.replace('''FORBIDDEN_REFS = [
''', '''FORBIDDEN_REFS = [
    ("language:response_language", "replacement", "replacement limitation: whole-text langdetect misses one foreign sentence"),
''', 1)
s = s.replace('''    "G1": (''', '''    "F48": ("skyrl,gate", ["length_constraints:number_sentences", "first_word:first_word_sent", "last_word:last_word_sent", "keywords:keyword_specific_position"], "CJK sentence ends (。！？) are not sentence boundaries: a Chinese answer of many sentences counts as one."),
    "G1": (''', 1)
s = s.replace('"F46": ("skyrl", ["count:lowercase_counting"], "HTML tag names count as lowercase words."),',
              '"F46": ("skyrl", ["count:lowercase_counting"], "Counts only ASCII words matching [a-z]+: lowercase words in other scripts are ignored, and HTML tag names count as lowercase words."),')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
