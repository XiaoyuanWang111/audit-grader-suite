# Audit of the RLVR1 instruction-following graders

Audit of the two graders that score the 11,817 instruction-following rows of Marin's Nemotron RLVR1 data
(`case/TASK.md`): grader A, the SkyRL reward `grade_instruction_following`, which runs NVIDIA's
verifiable-instructions checkers on the text that `final_answer_text` extracts; and grader B, the
deterministic gate of Marin's task-curation grader, which runs verifyit's `ifeval` checks on the 43
instruction ids that do not go to the LLM judge. NVIDIA's checkers are also the reference implementation
for grader B. Written 2026-11-12T10:18Z, following `skill/SKILL.md`; the record is `audit/ISSUE.md`, the
contracts `audit/CONTRACTS.md`.

## 1. Error rate and effect on scores

**Error rate: not estimated.** Step 6 (the blinded review) did not run in this exercise, so there is no
consensus label and no error rate with an interval. The numbers below are disagreements with the
replacement grader (`audit/replacement/contracts_grader.py`), which implements the contracts with one
switch per decision entry. The replacement passes all 2,181 fixtures but has not been reviewed blind,
its language checks are approximations, and six contract changes (C9 to C14) were fitted to panel
responses outside the held-out set; held-out numbers are given next to the panel numbers.

On the 55,783 constraint verdicts of the stored panel (23,315 responses from five models):

| | Grader A (SkyRL reward) | Grader B (verifyit gate, 43 ids) |
|---|---|---|
| Verdicts | 55,783 | 50,724 |
| Differ from the replacement (proposed readings) | 5,290 (9.5%) | 7,921 (15.6%) |
| of which the grader's own readings explain (decision) | 1,764 (3.2%) | 1,183 (2.3%) |
| of which no reading explains (defect) | 3,526 (6.3%) | 6,738 (13.3%) |
| Rows the grader passes (reward 1 / gate open) | 6,478 | 10,192 |
| of those, the replacement fails (proposed readings) | 998 (15.4%) | 2,922 (28.7%) |
| of those, the replacement fails with the grader's own readings: false rewards from defects alone | 617 (9.5%) | 2,784 (27.3%) |

A "decision" here means that the replacement, run with the readings this grader follows
(`audit/results/official_readings.json`, derived per check from the fixtures), returns the grader's
verdict; a "defect" means it does not.

Effect on each model's score, in points, with 95% bootstrap intervals over rows (`audit/panel_analysis.py`).
"Fixes only" runs the replacement with the readings grader A (or B) follows, so its difference from the
grader comes from defect fixes alone; "proposed" also applies the proposed reading of every decision entry.
Grader B's columns compare gates only (the judge is out of scope).

| Run | Rows | A score | Fixes only − A | Proposed − A | B gate | Fixes only − B | Proposed − B |
|---|---|---|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 29.56 | +3.18 [+2.65, +3.75] | +3.27 [+2.67, +3.88] | 47.75 | −6.62 [−7.39, −5.87] | −5.97 [−6.84, −5.20] |
| same, held-out rows | 2,363 | 29.33 | +3.51 [+2.33, +4.74] | +3.72 [+2.37, +5.04] | 47.36 | −6.26 [−8.04, −4.53] | −5.97 [−7.83, −4.15] |
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 29.30 | +2.20 [+0.6, +3.9] | +3.10 [+1.3, +5.1] | 49.90 | −8.70 [−11.2, −6.2] | −9.20 [−11.9, −6.5] |
| same, held-out rows | 187 | 31.02 | +2.14 [−1.07, +5.88] | +2.67 [−1.60, +6.95] | 48.13 | −8.56 [−14.44, −3.20] | −8.56 [−14.44, −2.67] |
| Qwen3-4B-Instruct-2507 greedy_repeat | 1,000 | 29.50 | +2.50 [+0.8, +4.2] | +3.20 [+1.3, +5.2] | 50.00 | −8.30 [−10.8, −5.8] | −8.80 [−11.6, −6.1] |
| Qwen3-4B-Thinking-2507 sample0 | 1,500 | 55.33 | +8.47 [+6.73, +10.27] | +9.27 [+7.27, +11.40] | 63.40 | +2.07 [−0.07, +4.20] | +4.47 [+2.40, +6.60] |
| same, held-out rows | 285 | 56.84 | +6.67 [+2.46, +10.53] | +7.37 [+2.46, +12.28] | 61.75 | +3.51 [−1.40, +8.42] | +5.61 [+0.70, +10.18] |
| Qwen2.5-7B-Instruct sample0 | 4,000 | 20.08 | +2.00 [+1.07, +2.83] | +1.15 [+0.05, +2.17] | 32.98 | −7.95 [−9.03, −6.83] | −5.55 [−6.78, −4.30] |
| same, held-out rows | 787 | 19.19 | +2.92 [+0.76, +5.21] | +2.03 [−0.38, +4.45] | 31.51 | −6.86 [−9.66, −4.19] | −4.57 [−7.50, −1.65] |
| OLMo-2-1124-7B-Instruct sample0 | 3,998 | 19.11 | +1.30 [+0.60, +2.00] | −0.30 [−1.15, +0.58] | 32.02 | −7.83 [−9.00, −6.68] | −6.95 [−8.23, −5.73] |
| same, held-out rows | 787 | 19.70 | 0.00 [−1.65, +1.65] | −1.02 [−3.05, +1.02] | 32.02 | −8.64 [−11.31, −5.97] | −7.62 [−10.55, −4.83] |

Rerun noise: `greedy_repeat` reran `greedy` with identical settings. 506 of the 1,000 responses are
byte-identical; grader A's score moved by +0.2 points (16 row verdicts changed) and the replacement's by
+0.3 (17 changed). The fixes move the same greedy run by +2.2 to +3.1 points, more than ten times the
rerun difference, although the 187-row held-out slice of the greedy run alone is too small to exclude zero.

**Recommendation: fix both graders, and fix the data.** Grader A is usable after the fixes in section 3;
grader B's gate should not open the judge as it stands: on 13.3% of its verdicts no reading of the text
gives its answer, it inverts one check (`count:lowercase_counting`) and checks a different property in
four others (`keywords:no_adjacent_consecutive`, `detectable_format:square_brackets`,
`copy:repeat_phrase`, `detectable_format:sentence_hyphens`). The extraction defect P1 and the
content-free rewards P3 affect both. Adopting the replacement itself as the fix still needs step 6
(section 6).

## 2. What was run

- Step 1: inputs pinned in `audit/ISSUE.md` (manifest of 177 files verified; the 89 source files match
  their git blobs; installed packages byte-identical to the case copies; one sha256 per data row in
  `audit/frozen/row_hashes.tsv`). Unverified inputs are listed there: the training run's SkyRL config
  and generation settings, the panel's stop sequences and reasoning parser, and which code grades rows
  whose `route` is `skyrl_gym` (finding P7).
- Step 2: `audit/CONTRACTS.md`, hashed at 2026-11-12T09:36:16Z before any grader code was read, then
  changed 14 times (C1 to C14), each change dated and explained; 48 decision entries.
- Step 3: 251 hand fixtures and 7 pipeline fixtures (raw model text through extraction), labeled from the
  contracts.
- Step 4: 1,259 property fixtures and 434 metamorphic fixtures (labels known by construction), 141
  content-free fixtures, 89 fuzz fixtures (the smallest response, by deletion, on which a grader and the
  replacement disagree, label checked by hand), from 14,100 fuzz runs; content-free responses graded on
  all 11,817 rows. All 2,181 fixtures are in `audit/fixtures.jsonl`; `audit/tests/test_fixtures.py` runs
  them on the replacement and both graders, with `xfail(strict=True)` on each verdict a grader gets wrong:
  5,805 passed, 644 xfailed. On the fixtures grader A is wrong 303 times (194 findings, 109 decisions)
  and grader B 341 times (265 findings, 76 decisions).
- Reference comparison: NVIDIA's checkers have no tests, so there were no reference assertions to run.
  Grader A and grader B disagree on 7,833 panel gate verdicts: grader B is wrong and A right on 5,464
  (4,935 defect, 529 decision), grader A wrong and B right on 2,369 (1,204 defect, 1,165 decision).
- Step 5: no compute; the panel is the stored responses in `case/panel/`. Every response was graded by
  grader A as the session calls it (`final_answer_text`, then `grade_instruction_following`, with
  `random.seed(0)` before each row), by grader B's gate (`_answer_text`, then each gate check) and by the
  replacement (`audit/panel_grade.py`, `audit/results/panel_verdicts.jsonl`). Held-out uuids (2,363 of
  11,817) were frozen before any panel verdict was read.
- Skipped because the exercise has no issue tracker, repository, research branch, Hugging Face dataset
  or job launcher: opening an issue, landing fixture tests and fixes through a PR, publishing frozen
  samples, and launching generation. Their records live in `audit/` instead.
- Step 6: not run (section 6).

## 3. Findings

Each counterexample is an exact input: the instruction id, the kwargs and the response (a JSON string).
Each row's command prints the label from the contract and each grader's verdict; run it from
`<W>` (it sets `NLTK_DATA` itself). "Share" is the panel count of the
check's verdicts that the grader gets wrong under no reading (defect class); findings on the same check
share it. "Reference status" says whether the other grader has the same defect (for grader B, NVIDIA's
checkers in grader A are the reference).

Command form: `.venv/Scripts/python.exe audit/repro.py --id <fixture id>`

### Grader A: SkyRL reward with NVIDIA's checkers

| Id | Check | Counterexample (fixture id: kwargs; response) | Verdicts | Contract it breaks | Share on the panel | Reference status |
|---|---|---|---|---|---|---|
| F-A1 | `keywords:word_once` | `keywords:word_once:63bf12f176dea2b6`: `{"keyword": "tea"}`; `"Tea is good. I like tea."` | label pass; A fail | "Include keyword tea" asks for at least one occurrence; the checker demands exactly one, counted as a substring | 907 of 1,808 (50.2%), all false fails | B has it too (G-1) |
| F-A2 | `keywords:word_count_different_numbers` | `keywords:word_count_different_numbers:569d7120cada2ee0`: `{"keyword": "tea", "frequency": 2, "relation": "less than"}`; `"Tea is good. I like tea."` | label pass; A fail | The prompt says "should appear 2 times"; the checker applies the hidden `relation` kwarg, and "less than 2" contradicts every reading | 302 of the 393 "less than" verdicts; 190 of 622 "at least" verdicts are decision D-count-exact | B has it too (G-2); root cause in the data (P4) |
| F-A3 | `copy:repeat_phrase` | `copy:repeat_phrase:f3ff93fdebb4decb`: `{"phrase": "Every cloud has a silver lining", "small_n": 2}`; `"Every cloud has a silver lining. Every cloud had a silver lining."` | label fail; A pass | Every repetition must be transformed; the checker keeps only the last match's difference count, so verbatim copies pass, and it matches case-sensitively (`copy:repeat_phrase:8c00dfccc0a206f5`: label pass, A fail) | 58 of 1,059 | B differs (G-6) |
| F-A4 | `count:count_unique` | `count:count_unique:6e36f21b7ac257e9`: `{}`; `"Apples, pears, plums, figs."` | label pass; A fail | Commas are not words; NLTK tokens make the repeated comma a repeated word | 157 of 1,341 | B judges this id with the LLM |
| F-A5 | `count:counting_composition` | `count:counting_composition:895893f80458e7d5`: `{"n_sent": 2, "n_words": 2}`; `"Birds sing. Cats sleep.\n* * *\nDogs bark. Fish swim.\n* * *\nKids play. Adults work."` | label pass; A fail | The prompt shows the divider `* * *`; the checker splits at `***` and counts periods as words | 1 row in the data | B differs (G-16) |
| F-A6 | `detectable_content:postscript` | `detectable_content:postscript:ea5c3cbebd2f8fdd`: `{"postscript_marker": "P.S."}`; `"Main text.\n\nP.P.S. Remember the meeting."` | label fail; A pass | A P.P.S. is not a P.S.; the pattern is unanchored, so it also matches inside words (`detectable_content:postscript:2e5d8df71daeea73`, `"sP.s."`) and inside a restated instruction (497 of 644 rows on the restated-instruction response) | 18 of 1,277 | not in B |
| F-A7 | `detectable_format:bigram_wrapping` | `detectable_format:bigram_wrapping:4770ecf17552f75c`: `{}`; `"<<I am>> <<at home>> today"` | label fail; A pass | Every word must be in a two-word unit; the checker only looks at the outer brackets of even-position token pairs, so a trailing bare word, one-word units and empty text pass | 187 of 1,157, all false passes | B judges this id with the LLM |
| F-A8 | `detectable_format:constrained_response` | `detectable_format:constrained_response:0848d7a857912939`: `{}`; `"My answer is yes. My answer is no."` | label fail; A pass | One option, not two; the checker passes any text that contains an option | 3 of 243 (75 more are decision D-constrained) | not in B |
| F-A9 | `detectable_format:multiple_sections` | `detectable_format:multiple_sections:d64c8ce4bd4ad86c`: `{"num_sections": 2, "section_spliter": "SECTION"}`; `"SECTION 1\nFirst part.\nSECTION 2\nSecond part.\nSECTION 3\nThird part."` | label fail; A pass | "Must have 2 sections" means exactly 2; the checker accepts at least 2 and counts markers anywhere in the text (`detectable_format:multiple_sections:399b81dd2478fdb3`) | 44 of 917 | B counts inline markers too (G-17) |
| F-A10 | `detectable_format:number_bullet_lists` | `detectable_format:number_bullet_lists:a95b6a0eb5846be8`: `{"num_bullets": 2}`; `"Intro\n\n* First point.\n* Second point.\n\n---\n\nEnd"` | label pass; A fail | A `---` rule and a line starting with italic `*Note:*` (`detectable_format:number_bullet_lists:d0a24c8ea1c66dac`) are not bullet points | 21 of 1,019 | not in B |
| F-A11 | `detectable_format:number_highlighted_sections` | `detectable_format:number_highlighted_sections:bf401f59c7f0d7e1`: `{"num_highlights": 1}`; `"Compute 2 * 3 * 4 now."` | label fail; A pass | Spaced multiplication signs are not markdown emphasis | 9 of 1,070 | B has it too (G-19) |
| F-A12 | `detectable_format:sentence_hyphens` | `detectable_format:sentence_hyphens:43cdb00c9b5b33e4`: `{}`; `"I like well-made tea.-You like coffee."` | label pass; A fail | A hyphenated word inside a sentence is allowed; em dashes are not hyphens (`detectable_format:sentence_hyphens:711c006963e7242b`: label fail, A pass) | 527 of 1,300 | B differs (G-9) |
| F-A13 | `detectable_format:square_brackets` | `detectable_format:square_brackets:831b57263789b79f`: `{}`; `"[Hello], [world]."` | label pass; A fail | Every word is bracketed; punctuation outside the brackets is not a word | 89 of 1,079 | B differs (G-5) |
| F-A14 | `first_word:first_word_answer`, `first_word:first_word_sent` | `first_word:first_word_answer:3c231de2547e61df`: `{"first_word": "development"}`; `"development, as a process, matters."` | label pass; A fail | The first word is "development"; the checker compares the whitespace token with its comma (also `first_word:first_word_sent:5a8168178dff58e5`) | 113 of 1,089 and 118 of 1,024 | not in B |
| F-A15 | `keywords:keyword_specific_position` | `keywords:keyword_specific_position:f93ca93f84e08b03`: `{"keyword": "skirt", "n": 1, "m": 1}`; `"Skirt colors vary. I like red."` | label pass; A fail | The keyword matches regardless of case, and a comma is not a word (`keywords:keyword_specific_position:12c4a519456e3d5f`) | 25 of 1,341 | not in B |
| F-A16 | `keywords:no_adjacent_consecutive` | `keywords:no_adjacent_consecutive:2ce11b2df62e193a`: `{}`; `"Room 1 2 3 here."` | label pass; A fail | Digits are not letters of the alphabet; markup hides adjacent words (`keywords:no_adjacent_consecutive:d0c76537a4fb4a98`, `"Dogs **eat** bones."`: label fail, A pass) | 176 of 1,499 | B differs (G-4) |
| F-A17 | `keywords:palindrome` | `keywords:palindrome:3929d8ed48c9ef9a`: `{}`; `"Level up now."` | label pass; A fail | "Level" is a palindrome; the checker compares whitespace tokens case-sensitively with punctuation attached, and counts a lone pipe character as a palindrome (`keywords:palindrome:7b4f37a8294437cd`) | 51 of 1,165 (219 more are decision D-palindrome) | B has the ASCII-only part |
| F-A18 | `length_constraints:nth_paragraph_first_word` | `length_constraints:nth_paragraph_first_word:67c7b7c214dc81a4`: `{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "hole"}`; `"First paragraph here.\n\nHole digging is fun."` | label fail; A pass (with `random.seed(0)`) | Paragraph 3 of 2 cannot exist; `build_description` redraws `nth_paragraph` at random on every call, so the verdict depends on Python's global random state | 161 panel constraints have nth > num: 23 pass at seed 0, and 45 change verdict across seeds 0 to 19 | not in B (B fails them) |
| F-A19 | `length_constraints:number_paragraphs`, `paragraphs:paragraphs` | `length_constraints:number_paragraphs:a84f8de3c1747b54`: `{"num_paragraphs": 3}`; `"First ***bold italic*** paragraph without a divider line."` | label fail; A pass | `***` glued to words is bold italic, not a divider; the checker splits at any `***`, also inside `****` | 43 of 1,345 and 43 of 1,150 | B differs (G-7, G-8) |
| F-A20 | `combination:two_responses` | `combination:two_responses:623abc890e8a842b`: `{}`; `"First answer.\n*******\nSecond answer."` | label fail; A pass | Seven asterisks are not the 6-asterisk separator | 6 of 557 | B has it too (G-18) |
| F-A21 | `language:response_language`, `change_case:english_capital` | `language:response_language:7fda78595dee0648`: `{"language": "fi"}`; `""` | label fail; A pass | Empty text is not Finnish; a `LangDetectException` counts as followed, so empty and symbol-only answers pass (780 of 780 rows on the empty response). All-capital French passes `english_capital` (`change_case:english_capital:92ee671b7f50930c`) | 17 of 1,600 and 104 of 1,534 (measured against a langdetect-based approximation) | B judges language with the LLM and has no English check (G-10) |
| F-A22 | `last_word:last_word_answer` | `last_word:last_word_answer:21dfed07e2b11581`: `{"last_word": "limit"}`; `""` | label fail; A fail with `IndexError` | A checker exception is a grading failure: the session turns it into outcome `INFRA_ERROR` with reward 0 for the whole row | 1 panel row (uuid `003597dc-859c-4e4d-b0e6-b68d998ba578`); 6 of 14,100 fuzz runs, all this check | not in B |
| F-A23 | `count:lowercase_counting` | `count:lowercase_counting:b1f3caa859fcdde2`: `{"N": 2}`; `"x'v<t"` | label pass; A fail | The checker counts ASCII `[a-z]+` runs, so a contraction is two words and non-ASCII lowercase words are not counted | 56 of 1,712 (272 more are decision D-lowercase-counting-scope) | B inverts the check (G-3) |
| F-A24 | `keywords:forbidden_words` | `keywords:forbidden_words:394a3be743c3bcaf`: `{"forbidden_words": ["benefit", "refrigerator"]}`; `"refrigerator_"` | label fail; A pass | The word is present; `\b` treats `_` as a letter | 1 of 1,687 | B has it too |

### Grader B: verifyit's gate checks

| Id | Check | Counterexample (fixture id: kwargs; response) | Verdicts | Contract it breaks | Share on the panel | Reference (NVIDIA) status |
|---|---|---|---|---|---|---|
| G-1 | `keywords:word_once` | `keywords:word_once:63bf12f176dea2b6`: `{"keyword": "tea"}`; `"Tea is good. I like tea."` | label pass; B fail | At least one occurrence, not exactly one | 865 of 1,808 | same defect (F-A1) |
| G-2 | `keywords:word_count_different_numbers` | `keywords:word_count_different_numbers:9b463cd2f3639ed7`: `{"keyword": "tea", "frequency": 2, "relation": "less than"}`; `"Tea is good."` | label fail; B pass | "Should appear 2 times"; the hidden relation is applied | 490 of 1,015 | same defect (F-A2) |
| G-3 | `count:lowercase_counting` | `count:lowercase_counting:fcffc5067ba27761`: `{"N": 2}`; `"the the the end"` | label fail; B pass | "At most N times"; the check passes when there are at least N lowercase words, and fails `"Hi."` (`count:lowercase_counting:c8b9fd371a07994b`) | 1,357 of 1,712 (1,187 false passes) | NVIDIA counts at most N in total (decision D-lowercase-counting-scope) |
| G-4 | `keywords:no_adjacent_consecutive` | `keywords:no_adjacent_consecutive:0fd993dd1f231a68`: `{}`; `"A big cat."` | label fail; B pass | The check tests adjacent duplicate words, not words starting with consecutive letters | 882 of 1,499 | NVIDIA tests the right property, with F-A16 |
| G-5 | `detectable_format:square_brackets` | `detectable_format:square_brackets:799dc08735ce2125`: `{}`; `"[Hello] world"` | label fail; B pass | Every word must be bracketed; the check passes when any bracketed span exists | 663 of 1,079 | NVIDIA checks every token (F-A13) |
| G-6 | `copy:repeat_phrase` | `copy:repeat_phrase:c6059a371558fad5`: `{"phrase": "Every cloud has a silver lining", "small_n": 2}`; `"Every cloud has a silver lining. Every cloud has a silver lining."` | label fail; B pass | The check counts verbatim copies (at least n) and fails transformed ones (`copy:repeat_phrase:bf8394ac5364061d`: label pass, B fail) | 515 of 1,059 | NVIDIA looks for one-word changes (F-A3) |
| G-7 | `length_constraints:number_paragraphs` | `length_constraints:number_paragraphs:4750a35a5627bd6d`: `{"num_paragraphs": 2}`; `"First paragraph.\n***\nSecond paragraph."` | label pass; B fail | Paragraphs are separated by the `***` divider; the check counts blank-line blocks and ignores `***` (`length_constraints:number_paragraphs:6799f5ab1aec62c2` passes with no divider) | 460 of 1,345 | NVIDIA splits at `***` (F-A19) |
| G-8 | `paragraphs:paragraphs`, `paragraphs:paragraphs2` | `paragraphs:paragraphs2:4ee668c1c630deed`: `{}`; `"One.\n\nTwo.\n\nThree."` | label fail; B pass | "There should be 2 paragraphs" means exactly 2; both checks accept 2 or more, and each accepts the other's separator (`paragraphs:paragraphs:07d3973dca93fe99`, `paragraphs:paragraphs2:b213e7ca14f06fa5`) | 442 of 1,391 and 186 of 1,150 | NVIDIA requires exactly 2 |
| G-9 | `detectable_format:sentence_hyphens` | `detectable_format:sentence_hyphens:c2f2c77f5a8b6d0b`: `{}`; `"I like tea.-You like coffee.-We both like water."` | label pass; B fail | Sentences are joined to each other by hyphens; the check instead requires hyphens and no spaces inside every sentence | 269 of 1,300 differ from the replacement (7 defect, 262 counted as decision D-hyphens-single by the derived readings) | NVIDIA has F-A12 |
| G-10 | `change_case:english_lowercase`, `change_case:english_capital` | `change_case:english_lowercase:dc02af210c0dd93c`: `{}`; `"esta es una respuesta corta en español y no en inglés, sobre el clima de hoy."` | label fail; B pass | "Your entire response should be in English"; the checks test letter case only | 142 of 1,208 and 110 of 1,534 (against the langdetect approximation) | NVIDIA checks the language (F-A21) |
| G-11 | `startend:quotation` | `startend:quotation:bee52c210a0c7de3`: `{}`; `"'Hello world.'"` | label fail; B pass | Single quotes are not double quotation marks, and a lone `"` (`startend:quotation:22f4b844cf040172`) wraps nothing | 3 of 810 | not in NVIDIA |
| G-12 | `detectable_format:title` | `detectable_format:title:9d05bab6507f4644`: `{}`; `"<< >>\nRoses are red."` | label fail; B pass | An empty title is not a title | 11 of 1,189 | not in NVIDIA |
| G-13 | `detectable_content:postscript` | `detectable_content:postscript:f8bdbc749b462b0a`: `{"postscript_marker": "P.S."}`; `"Main text.\n\n**P.S.** Remember the meeting."` | label pass; B fail | Bold markup before the marker | 19 of 1,277 | not in NVIDIA |
| G-14 | `keywords:start_end` | `keywords:start_end:a7b73552fa4f8d10`: `{}`; `"Hello there my friend hello."` | label fail; B pass | "Do not write anything after the last word, not even punctuation" | 75 of 989 | not in NVIDIA |
| G-15 | `length_constraints:number_words` | `length_constraints:number_words:49e174f988e7161a`: `{"num_words": 5, "relation": "less than"}`; `"One - two - three - four"` | label pass; B fail | A dash is not a word; the word pattern also skips every non-ASCII word | 71 of 1,443 (136 more are decision D-word) | not in NVIDIA |
| G-16 | `count:counting_composition` | `count:counting_composition:0c35023793d57c19`: `{"n_sent": 2, "n_words": 2}`; `"Birds sing loudly. Cats sleep.\n* * *\nDogs bark. Fish swim.\n* * *\nKids play. Adults work."` | label fail; B pass | "Exactly 2 words"; the check accepts at least, and does not count paragraphs (`count:counting_composition:558c02088149bbdd`) | 1 row in the data | NVIDIA differs (F-A5) |
| G-17 | `detectable_format:multiple_sections` | `detectable_format:multiple_sections:399b81dd2478fdb3`: `{"num_sections": 2, "section_spliter": "SECTION"}`; `"This answer mentions SECTION 1 and SECTION 2 inline only."` | label fail; B pass | Markers must begin sections | 14 of 917 | same defect (F-A9) |
| G-18 | `combination:two_responses` | `combination:two_responses:623abc890e8a842b`: `{}`; `"First answer.\n*******\nSecond answer."` | label fail; B pass | Seven asterisks are not the separator | 6 of 557 | same defect (F-A20) |
| G-19 | `detectable_format:number_highlighted_sections` | `detectable_format:number_highlighted_sections:bf401f59c7f0d7e1`: `{"num_highlights": 1}`; `"Compute 2 * 3 * 4 now."` | label fail; B pass | Not emphasis | 7 of 1,070 | same defect (F-A11) |

### Pipeline, data and protocol findings

| Id | Stage | Counterexample (fixture id: kwargs; raw model text) | Verdicts | Contract it breaks | Share on the panel | Status |
|---|---|---|---|---|---|---|
| P1 | Graded-text extraction, both graders | `punctuation:no_comma:1ebb8847247d59fd`: `{}`; `"<<Yes>>, <<I>> <<think>> <<so>>"` (a non-reasoning model's answer) | label fail; A pass, B pass | The graded text of a non-reasoning model is its whole answer. `final_answer_text` and verifyit's `_answer_text` return `""` when `<think>`, `<thinking>` or `<\|start_think\|>` occurs anywhere, and the bigram-wrapped word `<<think>>` contains `<think>`; the empty text then passes every prohibition. The same answer fails `keywords:existence` (`keywords:existence:fdf272f661c8e916`) and passes `language:response_language` (`language:response_language:b56713b791c7edc4`) | 23 panel answers emptied this way (22 bigram-wrapped answers containing `<<think>>` or `<<thinking>>`, one after `</think>`); grader A gave 8 of them reward 1 | the same algorithm in both graders |
| P2 | Graded-text extraction, both graders | `punctuation:no_comma:5a607955a5372161`: `{}`; `"Okay the user wants an answer without commas so I will plan it carefully and then"` (reasoning model, `<think>` opened by the chat template, never closed) | label fail; A pass, B pass | Reasoning that never closes is an extraction failure and fails every check; both graders grade the reasoning as the answer | 139 of 1,500 thinking responses (all stopped at the token limit); grader A rewarded 1, grader B's gate passed 18 | both graders |
| P3 | Content-free responses | the empty response on every row (`audit/scripts/extra_measures.py`) | — | Under D-empty reading A an empty answer passes only rows whose constraints all forbid something: 1,303 rows (11.0%); under reading B, none | Grader A rewards the empty answer on 1,702 of 11,817 rows (14.4%), grader B's gate passes it on 810. Beyond the contract, A passes empty text on every `language:response_language` row (F-A21) and every `bigram_wrapping` row (F-A7). A word repeated 40 times earns reward 1 on 731 rows; the restated instructions on 791 | — |
| P4 | Data: hidden relation | 526 `keywords:word_count_different_numbers` constraints | — | The prompt says "should appear N times", while the kwargs carry `relation` "at least" (320) or "less than" (206) | root cause of F-A2 and G-2 | data |
| P5 | Data: unsatisfiable or contradictory rows | `length_constraints:nth_paragraph_first_word` with `nth_paragraph` > `num_paragraphs` (77 rows, e.g. uuid `35492d20-71a4-4e3c-a92b-cee490cafddf`: 3 paragraphs, paragraph 4 must start with "feedback"); an exact mixed-case end phrase with all lowercase or all capitals (93 rows, under D-end-phrase-case reading A); "Answer with less than 2 (or 3) letters" with a constraint that needs words (189 rows); `P.S` shown without its period in 186 prompts whose kwarg is `P.S.` (D-postscript-marker) | — | No response can satisfy the first group; a grader that passes them hands out false rewards (F-A18) | 77 + 93 + 189 rows | data |
| P6 | Unpinned dependency, grader A | `_ensure_nltk_data` | — | NLTK `punkt_tab` is downloaded from the network when missing, and NLTK data has no version; the case pins it by sha256 only in `deps/` | every grader A verdict that tokenizes | — |
| P7 | Grading path not determinable | every row stores `route: "skyrl_gym"` | — | `NemotronTaskSession.__init__` raises unless `route == "task_session"`; the code that maps these rows to the session (`skyrl_gym.source_task`) or the `nemotron_ultra` env class is not in the case, so which reward runs in training is unverified | all rows | unverified input, `audit/ISSUE.md` |

Fuzzing (14,100 random responses, 300 per instruction id with the data's kwargs): grader A raised 6
exceptions, all F-A22; grader B raised none. Fuzz counts depend on the generator and are not rates.

## 4. Decision entries

48 entries, where the instruction text allows two verdicts. Reading A is the audit's proposal and what
the replacement does; the maintainers choose. The last two columns name the checks on which each grader
follows reading B, derived from the fixtures (`audit/scripts/official_readings.py`); entries D-english and
D-language have no switch in the replacement, whose language checks are a langdetect approximation.

<!-- DECISION TABLE -->

Panel verdicts that a grader gets "wrong" only through a reading: 1,764 for grader A and 1,183 for
grader B (per check in section 5). The entries that move the most verdicts are D-lowercase-counting-scope
(272 for A, which counts all lowercase words together), D-palindrome (219 for A, which counts one-letter
words), D-postscript-marker and D-postscript-position (217 for A, 97 for B: `P.S:`, `P.S` without the
period, or a mention inside a sentence), D-end-phrase and D-end-phrase-case (168 for A), D-word (135 for
A and 136 for B on `number_words`, Han characters as words), D-letters-count (96 for A, which counts
ASCII letters only) and D-constrained (75 for A, which accepts extra text). For an RL reward, D-empty
matters beyond its verdict count: under its reading A, 1,303 rows reward an empty answer (P3).

## 5. Panel details

Stored records (`audit/results/panel_summary.json`): token-limit stops 65 (Qwen2.5-7B-Instruct), 92 and
81 (Qwen3-4B-Instruct greedy and rerun), 620 (Qwen3-4B-Instruct sample0), 166 (Qwen3-4B-Thinking, of which
139 never closed their reasoning) and 39 (OLMo-2-7B). One OLMo response is empty. Literal `<think>` occurs
in 14 non-reasoning answers; counting `<thinking>` too, 23 answers are emptied by extraction (P1). Grader A
raised one exception (F-A22). Scored coverage: grader A gave a verdict on all 55,783 constraints (one of
them through the exception path, which the session reports as an infrastructure error for its row);
grader B's gate on all 50,724 deterministic constraints; the replacement on all 55,783.

Per check, all panel runs together (A defect: differs from the replacement under no reading; A decision:
differs only through grader A's readings; the same for B):

<!-- PER CHECK TABLE -->

## 6. Step 6 not run: what the recommendation still needs

No reviewers were available, so no sample was drawn, frozen or rendered. The recommendation to fix both
graders rests on fixtures whose labels the contracts settle; the size of each effect rests on the
replacement, which nobody has reviewed. Before the replacement replaces either grader, step 6 needs:

- the decision gate already recorded in `audit/ISSUE.md`: a lower error rate for the replacement than for
  grader A (and for B's gate), with a paired 95% interval that excludes zero;
- a frozen sample from the held-out uuids, stratified by whether grader A and the replacement disagree
  (5,290 disagreements, 50,493 agreements on the panel), with all or most disagreements and at least 130
  agreements that reach a consensus, rendered without source model or grader verdicts;
- two reviewer runs per case with `skill/references/reviewer-prompt.md`, Cohen's kappa between leans, and
  the disputed cases listed;
- review evidence for the decision entries that move the most verdicts, and for the language checks, where
  the replacement is only an approximation.

## 7. Limitations

- Labels of property, metamorphic and content-free fixtures come from construction or from the contract;
  fuzz labels are the replacement's verdict, checked by hand, and fuzz fixtures whose label rests on the
  language approximation were dropped.
- The replacement approximates "in English" and "in the named language" with langdetect on lowercased
  prose; its verdicts on those checks are not evidence of an error by either grader unless the language
  is plainly wrong (as in the fixtures).
- D-word reading A counts each Han character as a word, which makes `count:count_unique` strict for Chinese
  answers; this is a decision, not a finding.
- The "fixes only" readings were derived per check by best agreement on the fixtures; where a grader
  follows neither reading consistently, some of its verdicts are counted as defects that a finer switch
  would call decisions.
- The audit did not run grader A's `verifyit_enabled` variant (`grade_nemotron_instructions`), which swaps
  four predicates and the punctuation checks.

## 8. Files

- `audit/ISSUE.md`: the record (pins, contract hash and changes, held-out freeze, step 6 gate, hashes).
- `audit/CONTRACTS.md`: contracts, decision entries, changes C1 to C14.
- `audit/fixtures.jsonl`, `audit/tests/test_fixtures.py`, `audit/tests/expectations.json`: fixtures and tests
  (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests`).
- `audit/repro.py`: prints one fixture's label and verdicts; `audit/graders.py`: adapters for both graders.
- `audit/replacement/contracts_grader.py`: the replacement grader.
- `audit/fixtures_hand.py`, `audit/stress_tests.py`, `audit/build_fixtures.py`, `audit/fixture_lib.py`:
  fixture sources and classification.
- `audit/panel_grade.py`, `audit/panel_analysis.py`, `audit/scripts/extra_measures.py`,
  `audit/scripts/official_readings.py`: panel grading and measures; outputs in `audit/results/`.
- `audit/frozen/row_hashes.tsv`, `audit/frozen/heldout_uuids.txt`: frozen inputs.
- `audit/scripts/AUDIT_src.md` and `audit/scripts/build_report.py`: this report's source, with the two
  generated tables filled in by the script.
