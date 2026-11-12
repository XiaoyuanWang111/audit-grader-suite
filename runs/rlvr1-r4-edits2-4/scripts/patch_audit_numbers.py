"""One-off corrections to AUDIT.md numbers after verification."""
from pathlib import Path

p = Path("<W>/audit/AUDIT.md")
s = p.read_text(encoding="utf-8")
reps = [
    ("so every score change above except the held-out \"Proposed\" ones exceeds the rerun difference.",
     "so every fixes-only change exceeds the rerun difference and has an interval that excludes zero; the proposed changes for the two held-out runs have intervals that include zero."),
    ("The gate's verifyit checks implement a different requirement than the prompt states for at least eight instruction ids (F6, F9, F10, F11, F13, F14, F16, F17); NVIDIA's checkers, which are both the SkyRL reward and the reference, have 35 defects of their own.",
     "The gate's verifyit checks implement a different requirement than the prompt states for at least nine instruction ids (F6, F9 to F14, F16, F17), and the gate has 26 checker findings in all; NVIDIA's checkers, which are both the SkyRL reward and the reference, have 32 (10 of them shared with the gate). Both pipelines also grade unclosed reasoning as the answer (G1)."),
    ("| D-word-units | hyphenated words and contractions are one word | split at `-` and `'` | `well-known don't`: 2 / 4 words | A | B | 179 | 126 |",
     "| D-word-units | hyphenated words and contractions are one word | split at `-` and `'` | `well-known don't`: 2 / 4 words | A | B | 188 | 137 |"),
    ("| D-word-cjk | each CJK character is a word | a run between spaces is a word | `我喜欢猫`: 4 / 1 | open (B used) | B | 42 | 37 |",
     "| D-word-cjk | each CJK character is a word | a run between spaces is a word | `我喜欢猫`: 4 / 1 | open (B used) | B | 45 | 52 |"),
    ("| D-keyword-inflection | only the exact word | inflected forms count | `cats` for cat: fail / pass | A | B (substring) | 91 | 34 |",
     "| D-keyword-inflection | only the exact word | inflected forms count | `cats` for cat: fail / pass | A | B (substring) | 97 | 39 |"),
    ("| D-capital-word | `I`, `A` are all-capital words | only 2+ letters | `I am OK`: 2 / 1 | A | A | 3 | 80 |",
     "| D-capital-word | `I`, `A` are all-capital words | only 2+ letters | `I am OK`: 2 / 1 | A | A | 5 | 80 |"),
    ("| D-language-mixed | the response is in the language (names, code allowed) | every sentence is | — | A | A | 15 | 12 |",
     "| D-language-mixed | the response is in the language (names, code allowed) | every sentence is | — | A | A | 15 | 14 |"),
    ("| D-lowercase-count | lowercase occurrences only | case-insensitive counts | `The the the`, N 2: pass / fail | A | — | 13 | 3 |",
     "| D-lowercase-count | lowercase occurrences only | case-insensitive counts | `The the the`, N 2: pass / fail | A | — | 13 | 5 |"),
    ("460 metamorphic (42 bases, 376 ignored edits, 42 forbidden edits)",
     "460 metamorphic (46 checks: bases, 375 ignored edits and 46 forbidden edits, after removing responses already in the set)"),
    ("Result: 2,886 passed, 77 skipped (judged constraints have no gate verdict), 450 xfailed. The replacement has 6 expected failures, all recorded with their reason: one fuzz line and the HTML-tag edit inside a closing `>>` on bigram_wrapping, the whole-text language check that misses one English sentence in a French answer, the Afrikaans case above, and two fuzz lines with an uncertain label (`İ` as the letter i). Five fuzz lines whose label is only the replacement's (a title made of an HTML tag, `İ`) are marked \"unattributed\".",
     "Result: 2,886 passed, 77 skipped (judged constraints have no gate verdict), 450 xfailed. The replacement has 3 expected failures, each recorded with its reason: an HTML tag just before a closing `>>` on bigram_wrapping, the whole-text language check that misses one English sentence in a French answer, and the Afrikaans case above. Five grader verdicts on fuzz lines whose label is only the replacement's (a title made of an HTML tag; `İ` read as the letter i) are marked \"unattributed\"; their labels are uncertain."),
    ("- **Metamorphic tests** (`audit/scripts/run_metamorphic.py`, 42 checks, 376 ignored edits:",
     "- **Metamorphic tests** (`audit/scripts/run_metamorphic.py`, 46 checks, 375 ignored edits:"),
    ("SkyRL flipped a passing answer to fail 57 times on 13 checks", "SkyRL flipped a passing answer to fail 57 times on 14 checks"),
    ("the gate 18 times (F29,", "the gate 18 times on 8 checks (F29,"),
    ("On the panel, the gate and NVIDIA's checkers disagree on 7,515 of 48,526 gate verdicts (main runs). The largest cells:",
     "On the panel, the gate and NVIDIA's checkers disagree on 7,515 of 48,526 gate verdicts (five main runs). The largest cells, over all six runs:"),
]
for a, b in reps:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
