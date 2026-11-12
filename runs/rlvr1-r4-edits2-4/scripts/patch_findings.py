from pathlib import Path
p = Path("<W>/audit/lib/findings.py")
s = p.read_text(encoding="utf-8")
s = s.replace('''    "G1": (''', '''    "F47": ("skyrl", ["language:response_language", "change_case:english_capital", "change_case:english_lowercase"], "One langdetect call on the whole text decides the language: a full sentence in another language passes when the rest dominates, and repetitive or upper-case English can be detected as another language."),
    "G1": (''', 1)
s = s.replace('''    ("copy:repeat_phrase", "skyrl", "*", "F5"),''', '''    ("copy:repeat_phrase", "skyrl", "*", "F5"),
    ("copy:repeat_phrase", "gate", "*", "F6"),
    ("length_constraints:number_paragraphs", "gate", "*", "F16"),''', 1)
s = s.replace('''    ("language:response_language", "skyrl", "F41"),''', '''    ("language:response_language", "skyrl", "F47"),''', 1)
s += '''

def check_candidates(iid, grader):
    """Findings registered for this check and grader (fallback attribution)."""
    return [fid for fid, (graders, checks, _) in FINDINGS.items() if grader in graders.split(",") and iid in checks]
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
