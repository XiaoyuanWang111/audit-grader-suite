"""One-off edit of audit/tests/fixtures.py (kept for the record): make variant positions and
letter case such that unrelated decision entries do not change the fixture's verdict."""
import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures.py"
s = p.read_text(encoding="utf-8")
rep = [
    ('"Time flies when making fun. Time flies while having fun.", T, "two one-word variants"',
     '"Time flies while having fun. Time flies whilst having fun.", T, "two one-word variants"'),
    ('"Time flies when having fun. Time flies when making fun.", F, "one copy and one variant: one variant"',
     '"Time flies when having fun. Time flies while having fun.", F, "one copy and one variant: one variant"'),
    ('"Laughter is the best medicine. Laughter was the best medicine. Laughter is a best medicine.", T,',
     '"Laughter is a best medicine. Laughter is our best medicine. Laughter is the best medicine.", T,'),
    ('"time flies when making fun\\ntime flies while having fun", T, "variants in lowercase on two lines"',
     '"time flies while having fun\\ntime flies whilst having fun", T, "variants in lowercase on two lines"'),
    ('"1. Time flies when making fun!\\n2. Time flies while having fun!", T, "variants in a numbered list"',
     '"1. Time flies while having fun!\\n2. Time flies whilst having fun!", T, "variants in a numbered list"'),
    ('"Development, as a field, matters.", T, "comma after the first word"',
     '"development, as a field, matters.", T, "comma after the first word"'),
    ("'\"Development\" is the word.', T, \"quoted first word\"",
     "'\"development\" is the word.', T, \"quoted first word\""),
    ('"Peace, friends, comes first. Peace stays.", T, "comma after the word"',
     '"peace, friends, comes first. peace stays.", T, "comma after the word"'),
    ('"Rain falls.\\n\\n\\n\\nIf it stops, we go out.", T, "two blank lines between"',
     '"Rain falls.\\n\\n\\n\\nif it stops, we go out.", T, "two blank lines between"'),
    ('"If: rain falls.\\n\\nThen we stay.", T, "colon after the first word"',
     '"if: rain falls.\\n\\nThen we stay.", T, "colon after the first word"'),
]
for a, b in rep:
    if s.count(a) != 1:
        raise SystemExit(f"not found once: {a}")
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("edited", len(rep))
