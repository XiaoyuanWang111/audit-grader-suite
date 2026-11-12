"""Fill the two generated tables into audit/scripts/AUDIT_src.md and write audit/AUDIT.md."""
import os

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(AUDIT, "scripts", "AUDIT_src.md"), encoding="utf-8").read()
dec = open(os.path.join(AUDIT, "results", "decision_table.md"), encoding="utf-8").read().split("\n\n")[0].strip()
per = open(os.path.join(AUDIT, "results", "per_check_table.md"), encoding="utf-8").read().split("\n\n")[0].strip()
assert src.count("<!-- DECISION TABLE -->") == 1 and src.count("<!-- PER CHECK TABLE -->") == 1
# Notes on rows whose generated text is stale or needs a remark (contract change C2; the hidden relation).
patches = [
    ("| Final period optional, colon allowed, case-sensitive |",
     "| Final period optional, colon allowed (case: D-postscript-case, C2) |"),
    ("| N+1 occurrences: fail / pass | - | - |",
     "| N+1 occurrences: fail / pass | `word_count_different_numbers` on its 320 \"at least\" constraints (on the 206 \"less than\" ones neither reading: F-A2) | the same as A (G-2) |"),
    ("| `THE CAPITAL IS 北京 (BEIJING).`: pass / fail | - | - |",
     "| `THE CAPITAL IS 北京 (BEIJING).`: pass / fail | - (langdetect) | no English check at all (G-10) |"),
]
for old, new in patches:
    assert dec.count(old) == 1, old
    dec = dec.replace(old, new)
out = src.replace("<!-- DECISION TABLE -->", dec).replace("<!-- PER CHECK TABLE -->", per)
with open(os.path.join(AUDIT, "AUDIT.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write(out)
print("AUDIT.md", len(out), "chars")
