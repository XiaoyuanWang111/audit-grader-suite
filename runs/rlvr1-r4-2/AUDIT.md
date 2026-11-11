# Audit of the RLVR1 instruction-following graders

Two graders score the 11,817 instruction-following rows of Marin's Nemotron RLVR1 data (28,219 constraints, 47 instruction ids):

- **Grader A**, the SkyRL reward: `final_answer_text`, then NVIDIA's verifiable-instructions checkers built by `grade_instruction_following` (binary: 1.0 when every constraint passes). NVIDIA's checkers are the data's own grader, so grader A is also the reference implementation.
- **Grader B**, the task-curation gate: `grade_judge._answer_text`, then verifyit's `ifeval` check for every non-semantic constraint (43 of 47 ids); one failure gives reward 0.0, otherwise the LLM judge (not part of this case) scores the row.

Written 2026-11-11 by following `skill/SKILL.md` offline. The record of the audit (pins, contract hashes and times, held-out rule, decision rule for step 6) is `audit/ISSUE.md`; the contracts are `audit/CONTRACTS.md` (version 4).

## 1. Error rate and effect on scores

**No error rate is reported.** Step 6, the blinded review that estimates it, was not run (no reviewers in this exercise). What the audit measured instead, on the stored panel (23,315 responses, 55,783 constraint verdicts), against a replacement grader written from the contracts with their proposed readings:

| | Grader A (SkyRL reward) | Grader B (gate, deterministic constraints) |
|---|---|---|
| Constraint verdicts | 55,783 | 50,724 (90.9%; the other 5,059 go to the judge) |
| Verdicts that contradict the contract under every reading the text allows (findings, extraction) | 2,615 (4.7%) | 6,072 (12.0%) |
| Verdicts that differ only through a decision entry | 3,307 (5.9%) | 2,677 (5.3%) |
| Same, held-out responses only (10,709 A and 9,764 B verdicts) | 5.0% defect, 6.1% decision | 12.0% defect, 5.2% decision |
| Rewards (gate passes) that the replacement fails | 1,057 of 6,478 (16.3%); 481 (7.4%) involve a defect | 4,675 of 10,192 (45.9%); 2,384 (23.4%) involve a defect |
| Failures that the replacement passes | 1,767 | 1,671 |

These shares count the replacement grader's verdict as correct. The replacement has passed every fixture but has not been through a blinded review, so its own errors are inside these numbers; they are measurements of disagreement with attribution, not error rates.

Effect on each run's score (mean reward, or gate pass rate for B, in %; paired bootstrap 95% intervals over responses). "Fixes only" keeps each grader's verdict wherever a decision entry explains it and takes the replacement's verdict where a finding or the extraction stage does, so it isolates the effect of the defects:

| Run (model, decoding) | n | A | A, fixes only | Replacement | Replacement − A | B gate | B, fixes only | Replacement − B |
|---|---|---|---|---|---|---|---|---|
| OLMo-2-1124-7B-Instruct, sampled | 3,998 | 19.1 | 19.5 (+0.4 [−0.2, +1.0]) | 17.8 | −1.3 [−2.2, −0.4] | 32.0 | 24.9 (−7.2 [−8.3, −6.0]) | −14.2 [−15.6, −12.9] |
| Qwen2.5-7B-Instruct, sampled | 4,000 | 20.1 | 18.4 (−1.7 [−2.4, −0.9]) | 19.8 | −0.2 [−1.4, +0.9] | 33.0 | 26.7 (−6.3 [−7.3, −5.3]) | −13.2 [−14.5, −11.8] |
| Qwen3-4B-Instruct-2507, greedy | 1,000 | 29.3 | 31.6 (+2.3 [+1.0, +3.7]) | 34.4 | +5.1 [+3.2, +7.1] | 49.9 | 41.8 (−8.1 [−10.4, −5.8]) | −15.5 [−18.7, −12.3] |
| Qwen3-4B-Instruct-2507, greedy rerun | 1,000 | 29.5 | 32.1 (+2.6 [+1.2, +4.1]) | 35.0 | +5.5 [+3.6, +7.5] | 50.0 | 42.4 (−7.6 [−9.9, −5.3]) | −15.0 [−18.2, −11.9] |
| Qwen3-4B-Instruct-2507, sampled | 11,817 | 29.6 | 32.4 (+2.8 [+2.4, +3.3]) | 34.2 | +4.6 [+4.0, +5.2] | 47.8 | 42.0 (−5.8 [−6.5, −5.1]) | −13.6 [−14.6, −12.7] |
| Qwen3-4B-Thinking-2507, sampled | 1,500 | 55.3 | 59.6 (+4.3 [+2.9, +5.7]) | 63.5 | +8.2 [+6.3, +10.2] | 63.4 | 68.9 (+5.5 [+3.6, +7.5]) | +0.1 [−2.3, +2.5] |

The greedy rerun with identical settings changed 16 row verdicts under grader A (score +0.2 [−0.5, +1.0]) and 27 gate verdicts under grader B (+0.1 [−0.9, +1.1]); fixing the defects moves the same run by +2.3 (A) and −8.1 (B), well outside that noise. Fixes move models by different amounts and in different directions under A (−1.7 to +4.3 points), so the defects change model comparisons, not only levels.

**Recommendation: fix both graders** (section 8). Grader B's checks contradict the task text on 12.0% of its verdicts, and eight of its checks test a different requirement from the one the model sees. Grader A, the reference, has 28 checker findings and 2 pipeline findings of its own; as an RL reward it gives 1.0 to an empty answer on 1,702 of 11,817 rows, and it grades the 139 thinking responses that never close their reasoning on that reasoning (one of them rewarded 1.0; grader B's gate passes 18). Step 6 is still needed before the replacement grader can stand in for either grader (section 7).

## 2. Inputs (step 1)

Pinned in `audit/ISSUE.md`, section 1: Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a` (SkyRL files, verifyit, `graders.py`), NVIDIA `f46a5ac87b1400a4f8973039844b6be9b56e3faf`, the dataset revision `600262dd37891b86075a80517e61dbfb105d7cbe` with one sha256 per row (`audit/frozen/row_hashes.tsv`), the prompt rendering (one user message, no system message, temperature 1.0, top-p 1.0, no row sets `grading_mode`), the panel's generation settings (`panel/CONFIGS.md`), the 27 locked packages and the NLTK `punkt_tab` zip hash. Every case file matched `case/MANIFEST.sha256`, and the installed `verifyit` and `verifiable_instructions` packages are byte-identical to the case copies (`diff -r -q`). Pins that only the code shows were recorded after the contract hash (ISSUE.md, section 1 cont.).

Unverified, with the way to verify each: the parquet file itself (download it at revision `600262dd...` and compare its sha256); the panel's stop sequences, reasoning parser and any reasoning-merge policy (the generation manifests are not in the case); the NLTK data and package versions of the training job (Marin's `uv.lock` and job image at `af9c678`); and whether Marin's lowering step rewrites `extra_info.nemotron_ultra.route`, because `NemotronTaskSession.__init__` raises unless the route is `task_session` and all 11,817 rows store `skyrl_gym` (`skyrl_gym/source_task.py` is not in the case).

Skipped, because this run has no repository, research branch, Hugging Face dataset, issue tracker or job launcher: opening the issue with `file-issue` (kept in `audit/ISSUE.md`), placing the fixtures in Marin's grader test directory and landing them through `manage-pr` (they are in `audit/tests/`), the research branch (scripts are in `audit/scripts/` and `audit/lib/`), the immutable dataset revision for frozen files (they are in `audit/frozen/`, hashes in ISSUE.md), and generating new panel responses through `use-iris` (the stored responses are the panel). `docs/dev-guide/writing-style/issues.md` is not in the case; this report follows the skill's own section 7.

## 3. Contracts and decisions (step 2)

`audit/CONTRACTS.md` gives the graded-text rule, the reward contracts and one contract per instruction id, written from the instruction text in the prompts. Version 1 was hashed at 11:28Z before any grader file was opened; versions 2 to 4 add decision entries and clarifications, each with its reason in the contract's section 7 (two after reading the code, two after the first panel run, using only non-held-out responses). The template check (`audit/scripts/template_check.py`) found every constraint's kwargs in its prompt text, with two exceptions that matter: `keywords:word_count_different_numbers` carries a relation (`at least` 320, `less than` 206) that the text never shows, and 147 `P.S.` postscript markers are rendered as "P.S" in inline prompts.

There are 44 decision entries (section 10). Counted separately from the findings, they explain 3,307 of grader A's and 2,677 of grader B's disagreements with the replacement.

## 4. Fixtures and replacement grader (step 3)

`audit/tests/fixtures.py` holds 226 fixtures labeled from the contracts alone, at least one pass and one fail for each of the 47 instruction ids, each with a stable id (instruction family plus 12 hex digits of a content hash). `audit/tests/test_fixtures.py` runs them on grader A, grader B and the replacement; a fixture that a grader gets wrong is marked `xfail(strict=True)` with the finding or decision that explains it (`audit/tests/known_wrong.py`, written by `audit/scripts/classify_fixtures.py`). A wrong verdict counts as a decision only when the fixture's listed decision entries, read the other way, make it correct; for every finding fixture the classifier also checked that no single entry and not all entries together explain the grader's verdict.

The fixtures showed defects that a change to each grader can fix, so the audit built a replacement grader, `audit/lib/contract_grader.py`, with one switch per decision entry. It passes every fixture, and each fixture's listed switches flip its verdict.

Run all tests (expected: 539 passed, 167 xfailed):

```bash
cd <W>
NLTK_DATA=$PWD/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --rootdir audit audit/tests
```

Of the 148 wrong fixture verdicts of graders A and B, 84 are findings and 64 are decisions.

## 5. Reference comparison and stress tests (step 4)

- Reference comparison. Grader A runs the reference code unmodified, so the comparison is grader B against grader A. On the panel's deterministic constraints they disagree on 7,833 verdicts. Against the replacement, B is wrong on 4,512 of them through a defect and 1,037 through a decision; A is wrong on 710 through a defect and 1,525 through a decision; 49 differ through extraction (P1).
- Tests. NVIDIA's repository has no tests, and neither verifyit's nor Marin's tests are in the case, so no reference assertion could be run against the replacement and no grader test that encodes a decision could be listed.
- Property and metamorphic tests (`audit/tests/test_properties.py`, Hypothesis, derandomized): 10 properties on graders A, B and the replacement, such as "a keyword inside a longer word does not count" (A fails, F1), "a second occurrence does not fail `word_once`" (A and B fail, F2), "a horizontal rule is not a bullet" (A and B fail, F9), "a third paragraph fails a two-paragraph check" (B fails, F22). Row-level tests (`audit/tests/test_pipeline.py`) cover extraction (P1), determinism (F29) and the NLTK download (P2). Together: 25 passed, 19 xfailed.
- Fuzzing (`audit/scripts/fuzz.py`, fixed seed, 400 random inputs per instruction id, 18,800 in all, kwargs from the data): grader A raised on 39 inputs (33 `IndexError` in `last_word_answer` on whitespace-only text, F19; 6 `RecursionError` in `json_format` on 1,000+ nested brackets), grader B on 6 (the same `RecursionError`, which the gate counts as a failed constraint, P5), the replacement on 0. No exception stops a run: grader A records it per constraint and the session turns it into an `INFRA_ERROR` with reward 0.0; grader B's `_passes` swallows it. These are counts that depend on the fuzzer's inputs, not rates.
- Score-level transforms: none beyond the binary all-constraints rule (A) and the gate (B); `grading_mode` `fraction` is never set.
- Content-free responses, graded on all 11,817 rows (`audit/scripts/content_free.py`):

| Response | Grader A reward 1.0 | Grader A `INFRA_ERROR` | Grader B gate passes | Replacement passes |
|---|---|---|---|---|
| Empty | 1,702 | 625 | 810 | 967 |
| `the` repeated 300 times | 735 | 0 | 1,073 | 691 |
| The row's own prompt | 746 | 0 | 1,365 | 463 |

  On the empty answer grader A passes every constraint of `language:response_language` (780, F18), `last_word:last_word_sent` (600), `first_word:first_word_sent` (540), `detectable_format:bigram_wrapping` (575), `count:count_unique`, `count:lowercase_counting`, `detectable_format:sentence_hyphens`, `detectable_format:square_brackets` and the negative checks (`no_comma`, `punctuation_dot`, `punctuation_exclamation`, `forbidden_words`, `no_adjacent_consecutive`). The contract itself is satisfied by an empty answer on 967 rows whose constraints are all negative or vacuous; a reward built only from these constraints pays an empty answer there, whatever the grader. Grader B leaves that to its judge's general criterion; grader A has no such guard.

## 6. Model panel (step 5)

The panel is the six stored runs (`panel/CONFIGS.md`); no response was generated. Every response was graded by grader A, grader B and the replacement, each on the text its own extraction produces (`audit/scripts/panel.py`, `audit/scripts/panel_report.py`, outputs in `audit/out/`). Held-out responses (row uuid whose sha256 starts with 0, 1 or 2) were set aside before any verdict was examined; the replacement's two post-panel contract versions used only the other responses, and the held-out shares in section 1 are within 0.4 points of the rest.

What the stored records show before grading: 1,063 of 23,315 responses hit the token limit (39 OLMo, 65 Qwen2.5, 92 and 81 Qwen3-Instruct greedy and rerun, 620 Qwen3-Instruct sampled, 166 Qwen3-Thinking); 139 of the 1,500 thinking responses never close their reasoning (all truncated); 14 non-reasoning responses contain a literal `<think>`; one OLMo response is empty. Grader A raised on one constraint (one row recorded as `INFRA_ERROR`).

Scored coverage: grader A and the replacement give a verdict on all 55,783 constraint verdicts; grader B's gate on the 50,724 deterministic ones, by design.

Pass rates per instruction id (%, panel verdicts) where the graders differ most:

| Instruction id | n | A | B | Replacement | Main cause |
|---|---|---|---|---|---|
| `keywords:word_once` | 1,808 | 25.5 | 25.9 | 73.4 | F2 |
| `count:lowercase_counting` | 1,712 | 15.2 | 88.4 | 29.1 | F31; `D-lowercase-counting` |
| `keywords:no_adjacent_consecutive` | 1,499 | 23.7 | 76.8 | 23.8 | F16 |
| `detectable_format:square_brackets` | 1,079 | 16.2 | 95.2 | 17.1 | F32 |
| `copy:repeat_phrase` | 1,059 | 8.9 | 45.6 | 4.3 | F5, F4 |
| `length_constraints:number_paragraphs` | 1,345 | 74.1 | 42.4 | 63.5 | F21, F20 |
| `paragraphs:paragraphs2` | 1,391 | 62.5 | 94.3 | 62.5 | F22 |
| `keywords:word_count_different_numbers` | 1,015 | 54.2 | 54.2 | 37.3 | F3; `D-word-count-relation` |
| `detectable_format:sentence_hyphens` | 1,300 | 19.6 | 19.5 | 77.1 | `D-hyphen-plural`, `D-hyphen-inner` |
| `detectable_content:postscript` | 1,277 | 83.3 | 72.4 | 69.5 | F6; postscript decisions |
| `keywords:palindrome` | 1,165 | 90.3 | 63.4 | 79.0 | `D-palindrome-length`, F17 |
| `detectable_format:bigram_wrapping` | 1,157 | 19.4 | judge | 3.2 | F27 |
| `startend:end_checker` | 997 | 87.4 | 68.3 | 71.3 | `D-end-case` |

The full table, every disagreement's cause and each decision's effect are in `audit/out/panel_report.txt`. The replacement's high `sentence_hyphens` pass rate rests on one reading: 993 of its 1,002 passes contain no hyphen join between sentences (613 have no sentence-ending punctuation), and they pass only because unpunctuated text counts as one sentence. `D-hyphen-plural` reading B fails them; step 6 should review these cases first.

False rewards (grader A as an RL reward): 1,057 of the 6,478 responses with reward 1.0 fail under the replacement; 576 of these differ only through decision entries, 472 involve a finding and 9 an extraction difference. On the held-out responses the share is 220 of 1,252 (17.6%). Rows that no response can satisfy (`audit/scripts/unsatisfiable.py`, a lower bound): 108 of 11,817, of which 77 ask for a paragraph beyond the paragraph count; grader A paid 1.0 on 14 panel responses to such rows.

## 7. Blinded review (step 6): not run

No reviewers were available, so no sample was drawn, frozen or rendered, and no error rate, interval, kappa or confusion matrix exists. The recommendation still needs from step 6:

- each grader's error rate with a 95% interval, and the replacement's, from a frozen, stratified sample of held-out responses (ISSUE.md, section 6, records the design and the result that would change the recommendation before any review);
- the paired difference between each grader and the replacement, which decides whether the replacement can serve as the fix's reference;
- reviewer evidence on the decision entries with the largest panel effect: `D-word-case` (1,231 verdicts flip under reading B), `D-hyphen-plural` (992), `D-hyphen-inner` (754), `D-english` (421), `D-word` (398), `D-word-cjk` (351), `D-edge-markup` (306), `D-lowercase-counting` (304), `D-brackets-per-word` (301);
- a check of the replacement's language identification (langdetect, seed 0), which decides `language:response_language` and the English part of the two `change_case` checks.

## 8. Recommendation

**Fix both graders; do not replace the benchmark.** The instruction text is gradable: one replacement grader passes all 226 fixtures, and most disagreements trace to a named defect or decision.

- Grader B: its `ifeval` checks diverge from the text the model sees. Eight test a different requirement (F5 `repeat_phrase`, F16 `no_adjacent_consecutive`, F21 `number_paragraphs`, F22 `paragraphs` and `paragraphs2`, F31 `lowercase_counting`, F32 `square_brackets`, F33 `sentence_hyphens`), and F24 makes every word-based check ignore non-ASCII words, although 765 of the 780 `response_language` constraints ask for a language other than English. Rebuild the checks from NVIDIA's checkers with the fixes below, or from the replacement once step 6 supports it.
- Grader A: fix F1 to F4, F6 to F15, F17 to F20, F23, F25 to F30, F37 to F39, and P1 and P2. For RL, the largest are F2 (43% of `word_once` verdicts), F3 (26% of `word_count_different_numbers`), F27, F20, F15, F6, P1 (truncated thinking responses rewarded on their reasoning) and F29 (a random verdict).
- Both: grade a reasoning model's response that never closes its reasoning as an extraction failure (P1); record a raising check as a grading failure apart from model failures (P5, F19); add a guard against content-free answers to the reward; send the 44 decision entries to the evaluation's maintainers.
- Data: regenerate or drop the 206 `word_count_different_numbers` constraints whose hidden relation is `less than` and the 108 unsatisfiable rows, and render the `P.S.` marker with its dot.
- Upstream: F1 to F4, F6 to F15, F17 to F20, F23, F25 to F30 and F37 to F39 are in NVIDIA's code at `f46a5ac`; send them with their fixtures.

## 9. Findings

Each finding lists its counterexample as exact input (Python string literals) and the command that prints the graders' verdicts next to the contract's. Every command runs from `<W>` in Git Bash after:

```bash
export NLTK_DATA=$PWD/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
```

and has the form `.venv/Scripts/python.exe audit/repro.py <id>` (`audit/repro.py all` runs them all; its output is saved in `audit/out/repro_all.txt`). "Share" is the panel's constraint verdicts of that instruction id that the finding changes, out of all that grader's verdicts of the id, after removing those that a decision entry or the extraction stage explains. "Reference" is NVIDIA's checker at `f46a5ac`, which grader A runs unmodified.

| Id | Grader | Check or stage | Counterexample (check, kwargs, response) | Grader verdict / contract | Contract broken | Share on the panel | Reference |
|---|---|---|---|---|---|---|---|
| F1 | A | `keywords:existence`, `frequency`, `word_once`: keyword matched as a substring | `keywords:existence`, `{'keywords': ['art', 'she']}`, `'She started to finish the task.'` | pass / fail | a keyword is a whole word, never part of an unrelated word | 20/1,856 existence, 24/1,200 frequency, 15/1,808 word_once | same |
| F2 | A, B | `keywords:word_once`: exactly one occurrence required | `keywords:word_once`, `{'keyword': 'beer'}`, `'Beer is good and beer is cheap.'` | A fail, B fail / pass | "Include keyword X" is met by any occurrence | A 776/1,808 (42.9%), B 742/1,808 (41.0%) | same |
| F3 | A, B | `keywords:word_count_different_numbers`: applies a relation the model never sees | `{'keyword': 'refuse', 'frequency': 1, 'relation': 'less than'}`, `'I refuse.'` | A fail, B fail / pass | "should appear N times" is met by N occurrences under both readings; 206 constraints carry `less than` | 266/1,015 (26.2%) each | same |
| F4 | A | `copy:repeat_phrase`: only the last match's difference is checked; an earlier first word on the line breaks matching | `{'phrase': 'All that glitters is not gold', 'small_n': 3}`, `'All that glitters is not gold\nAll that glitters is not gold\nAll that shines is not gold'` | pass / fail | every repetition replaces one word; one variant is not three | 57/1,059 (5.4%) | same |
| F5 | B | `copy:repeat_phrase`: counts unchanged copies of the phrase, at least n | same kwargs with `small_n` 2: `'All that glitters is not gold\nAll that glitters is not gold'`; and `'All that shines is not gold\nAll that sparkles is not gold'` | pass / fail; fail / pass | the repetitions must be transformed | 486/1,059 (45.9%) | not in reference |
| F6 | A | `detectable_content:postscript`: marker found anywhere, also inside `P.P.S.` | `{'postscript_marker': 'P.S.'}`, `'I added a P.S. note at the end, see below.\n\nThat is all.'` | pass / fail | a postscript line starts with the marker | 132/1,277 (10.3%) | same |
| F7 | A | `detectable_format:constrained_response`: any text containing an option passes | `None`, `'My answer is yes. My answer is no.'` | pass / fail | one option, under both readings | 3/243 (1.2%) | same |
| F8 | A, B | `detectable_format:multiple_sections`: markers counted anywhere, inside longer words | `{'num_sections': 2, 'section_spliter': 'SECTION'}`, `'SECTION 1\nThis part mentions SECTION 2 inline only.'` | A pass, B pass / fail | a marker begins a section | 36/917 (3.9%) each | same |
| F9 | A, B | `detectable_format:number_bullet_lists`: horizontal rules (A, B), italic line starts and lines such as `-5 degrees` (A) count as bullets | `{'num_bullets': 2}`, `'* Apples\n* Pears\n\n* * *\n\nDone.'` | A fail, B fail / pass | a rule is not a bullet point | A 21/1,019 (2.1%), B 0 | same |
| F10 | A, B | `detectable_format:number_highlighted_sections`: spaced asterisks count | `{'num_highlights': 2}`, `'Compute 5 * 3 * 2 and *done*.'` | pass, pass / fail | a highlight is `*text*` | A 8/1,070, B 6/1,070 | same |
| F11 | A | `first_word:first_word_answer`, `first_word_sent`: punctuation after the first word makes it a different word | `first_word_answer`, `{'first_word': 'development'}`, `'development, as a concept, matters.'` | fail / pass | a comma is not part of the word | 67/1,089 (6.2%); with F39, 44/1,024 of `first_word_sent` | same |
| F12 | A | `keywords:keyword_specific_position`: NLTK punctuation tokens count as words | `{'keyword': 'village', 'n': 2, 'm': 3}`, `'We walked far. Indeed, the village slept.'` | fail / pass | the third word is `village` | with F39, 15/1,341 (1.1%) | same |
| F13 | A | `count:count_unique`: repeated punctuation tokens count as repeated words | `None`, `'Apples, pears, plums.'` | fail / pass | commas are not words | 94/1,341 (7.0%) | same |
| F14 | A, B | `keywords:start_end`: punctuation tokens taken as the first and last word (A, B); punctuation after the last word ignored (B) | `None`, `'- Hello world -'`; and `'Hello world, I say hello.'` | A pass, B pass / fail; A fail, B pass / fail | nothing may follow the last word | A 35/989 (3.5%), B 64/989 (6.5%) | `'- Hello world -'` same |
| F15 | A | `keywords:no_adjacent_consecutive`: first characters compared even when they are digits or punctuation | `None`, `'Steps 1 2 now'` | fail / pass | digits are not letters of the alphabet | 162/1,499 (10.8%) | same |
| F16 | B | `keywords:no_adjacent_consecutive`: checks for repeated adjacent words instead | `None`, `'A big dog'`; and `'very very good'` | pass / fail; fail / pass | the requirement is about consecutive first letters | 872/1,499 (58.2%) | not in reference |
| F17 | A, B | `keywords:palindrome`: tokens without letters (`-`, `---`) count | `None`, `'Top results\n---\nNotes here'` | pass, pass / fail | `---` is not a palindrome under either reading | A 36/1,165, B 166/1,165 (14.2%) | same |
| F18 | A | `language:response_language`: a detection failure counts as a pass | `{'language': 'es'}`, `'12345 67890'` | pass / fail | no Spanish prose | 9/1,600; passes all 780 data constraints on an empty answer | same |
| F19 | A | `last_word:last_word_answer`: raises `IndexError` on empty or whitespace text; the session records `INFRA_ERROR` | `{'last_word': 'payment'}`, `''` | exception / fail | a model's empty answer is a model failure, not an infrastructure error | 1 panel row; 625 rows on the empty answer; 33 of 400 fuzz inputs | same |
| F20 | A | `length_constraints:number_paragraphs`, `paragraphs:paragraphs`: `***` inside a line splits paragraphs | `{'num_paragraphs': 2}`, `'First paragraph has ***bold italic*** text.\n***\nSecond paragraph.'` | fail / pass | the divider is a line `***` | 80/1,345 and 104/1,150 (9.0%) | same |
| F21 | B | `length_constraints:number_paragraphs`: counts blank-line paragraphs and ignores the `***` divider | `{'num_paragraphs': 2}`, `'First paragraph.\n***\nSecond paragraph.'`; and `'First paragraph.\n\nSecond paragraph.'` | fail / pass; pass / fail | "separated with the markdown divider: ***" | 479/1,345 (35.6%) | not in reference |
| F22 | B | `paragraphs:paragraphs`, `paragraphs2`: two or more paragraphs by either separator pass | `paragraphs:paragraphs`, `{}`, `'First.\n***\nSecond.\n***\nThird.'`; `paragraphs2`, `'A.\n\nB.\n\nC.'` | pass / fail | exactly 2 paragraphs, with the named separator | 240/1,150 (20.9%), 435/1,391 (31.3%) | not in reference |
| F23 | A | `length_constraints:number_words`, `change_case:capital_word_frequency`: contractions split into two words (`Don't`, `I'm`) | `number_words`, `{'num_words': 3, 'relation': 'less than'}`, `"Don't stop."`; `capital_word_frequency`, `{'capital_frequency': 2, 'capital_relation': 'less than'}`, `"I'm sure NASA is fine."` | fail / pass (both) | `Don't` is one word; `I'm` is not an all-capital word | 18/1,443 and 11/1,207 | same |
| F24 | B | every word-based check: verifyit's words are ASCII only | `number_words`, `{'num_words': 5, 'relation': 'at least'}`, `'Это очень хороший и полезный ответ.'`; `last_word_answer`, `{'last_word': 'ask'}`, `'Feel free to ask 朋友'` | fail / pass; pass / fail | Cyrillic and Chinese words are words | 160 verdicts over 7 ids, up to 62/1,443 (4.3%) of `number_words` | not in reference |
| F25 | A | `letters:letter_counting`: counts only ASCII letters | `{'N': 3, 'relation': 'at least'}`, `'Да, конечно, это так.'` | fail / pass | Cyrillic letters are letters | 87/961 (9.1%) | same |
| F26 | A | `detectable_content:number_placeholders`: empty brackets count | `{'num_placeholders': 2}`, `'Dear [], see you at [ ].'` | pass / fail | a placeholder has content | 1/1,201 | same |
| F27 | A | `detectable_format:bigram_wrapping`: with an odd word count the last word is never checked | `None`, `'<<I am>> <<at home>> today'` | pass / fail | `today` is not wrapped | 160/1,157 (13.8%) | same |
| F28 | A, B | `count:counting_composition`: A splits at `***` (the text names `* * *`) and counts punctuation tokens; B checks only that the first n sentences have at least n words | `{'n_sent': 3, 'n_words': 2}`, `'Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Moms smile. Dads cook.'`; and `'Birds sing. Cats sleep. Dogs run.'` | A fail / pass; B pass / fail | 3 paragraphs of exactly 3 sentences of exactly 2 words | 1 data row, 0 panel disagreements | A: same |
| F29 | A | `length_constraints:nth_paragraph_first_word` with `nth_paragraph` > `num_paragraphs`: NVIDIA draws a random paragraph index from the global `random` state | row `{'num_paragraphs': 2, 'nth_paragraph': 3, 'first_word': 'fight'}`, `'Fight one.\n\nFight two.'` | reward 1.0 under `random.seed` 0 to 4, 0.0 under 5 / fail | the text asks for a paragraph that cannot exist; a verdict must not depend on process state | 77 data constraints; 23 panel verdicts (seed 0) | same |
| F30 | A, B | `combination:two_responses`: a run of seven asterisks is taken as the six-asterisk separator | `None`, `'One.\n*******\nTwo.'` | pass, pass / fail | "6 asterisk symbols" | 31/557 (5.6%) each | same |
| F31 | B | `count:lowercase_counting`: requires at least N lowercase words, the opposite direction | `{'N': 2}`, `'the the the end'`; and `'ALL CAPS ONLY.'` | pass / fail; fail / pass | "at most N times" under both readings | 1,314/1,712 (76.8%) | not in reference |
| F32 | B | `detectable_format:square_brackets`: one bracketed span anywhere passes | `None`, `'Hello [world] how are you'` | pass / fail | every word in brackets | 550/1,079 (51.0%) | not in reference |
| F33 | B | `detectable_format:sentence_hyphens`: requires each sentence's words to be joined by hyphens | `None`, `'I like tea.-You like coffee.-We both like cake.'`; and `'I-like-tea. You-like-coffee.'` | fail / pass; pass / fail | sentences joined by hyphens, no spaces between them | 1/1,300 after decisions; most of B's 755 disagreements are explained by `D-hyphen-plural` | not in reference |
| F34 | B | `startend:quotation`: single quotes accepted | `None`, `"'Hello there.'"` | pass / fail | "double quotation marks" | 0 panel verdicts | not in reference |
| F35 | B | `detectable_format:title`: a title of spaces passes | `None`, `'<< >>\nRoses are red.'` | pass / fail | a title has content | 0 panel verdicts | not in reference |
| F36 | B | sentence splitting: an abbreviation dot ends a sentence, a period before a closing quote or bracket does not, CJK marks are ignored | `number_sentences`, `{'num_sentences': 2, 'relation': 'less than'}`, `'Dr. Smith arrived.'`; `{'num_sentences': 2, 'relation': 'at least'}`, `'He said "Stop." Then he left.'` | fail / pass (both) | one sentence; two sentences | 84/1,131 (7.4%) | not in reference |
| F37 | A | `count:lowercase_counting`: only ASCII lowercase words counted | `{'N': 2}`, `'Он сказал да да да да.'` | pass / fail | `да` appears 4 times under both readings | 48/1,712 (2.8%) | same |
| F38 | A | `detectable_format:square_brackets`: a whitespace token with brackets at both ends passes whatever lies between | `None`, `'[Hello]and[world]'` | pass / fail | `and` is outside the brackets | 2/1,079 | same |
| F39 | A | sentence splitting: `split_into_sentences` splits at every dot inside a token (`Node.js`), and it and punkt ignore CJK sentence marks | `last_word_sent`, `{'last_word': 'limit'}`, `'We use Node.js to set the limit.'`; `number_sentences`, `{'num_sentences': 3, 'relation': 'at least'}`, `'第一句。第二句。第三句。'` | fail / pass (both) | one sentence ending in `limit`; three sentences | 103 verdicts over 3 ids (68/1,131 of `number_sentences`), plus 59 shared with F11 and F12 | same |
| F40 | B | `detectable_content:postscript`: a marker after markdown emphasis is not found | `{'postscript_marker': 'P.S.'}`, `'Answer.\n\n**P.S.** Thanks.'` | fail / pass | a bold `P.S.` starts the postscript | 7/1,277 | not in reference (A passes it) |
| P1 | A, B | extraction: a thinking response cut inside its reasoning has no marker (the template opened it), so its reasoning is graded as the answer; a non-reasoning answer that mentions `<think>` is emptied | `audit/repro.py P1`: raw `'Okay so the user wants an answer without commas so I will plan it step by step and then write'` on a `no_comma` row; raw `'Wrap the plan in a <think> tag before you answer.'` on a `keywords:existence ['tag']` row | reward 1.0 / extraction failure; reward 0.0 / 1.0 | contract section 1 (G1, G2) | 141 thinking and 22 instruct responses; A 126 and B 131 verdicts; 9 of grader A's false rewards | not in reference |
| P2 | A | unpinned input: `_ensure_nltk_data` calls `nltk.download("punkt_tab")` (no version, network) when the data is missing | `audit/repro.py P2` (stubs `nltk.data.find` and `nltk.download`; no network) | `nltk.download calls: [('punkt_tab',)]` | every input that can change a verdict is pinned | not measurable on the panel | not in reference |
| P5 | B | a raising check is counted as a failed constraint, not as a grading failure | `json_format`, `None`, `'[' * 5000` | `RecursionError`, counted as fail | grading failures are reported apart from model failures | 6 of 400 fuzz inputs | A raises too and the session marks `INFRA_ERROR` |

Reproduce any row with, for example, `.venv/Scripts/python.exe audit/repro.py F31`; F29, P1, P2 and P5 are rows, row-level runs or monkeypatched calls and print their own lines. Data-level observations that are not grader defects: 108 unsatisfiable rows (section 6) and the 147 `P.S` renderings (section 3). Unassigned disagreements left after attribution: 3 verdicts (one `nth_paragraph_first_word` for A, two `keywords:frequency` for B).

## 10. Decision entries

For the evaluation's maintainers. Proposed reading A for each; "A" and "B" in the grader columns say which reading the grader's fixtures follow ("mixed" when its fixtures go both ways, "-" when no fixture tests it). The last column is how many replacement verdicts (and row rewards) flip on the panel under reading B. Full wording and examples: `audit/CONTRACTS.md`, section 6.

| Entry | Question | Reading A (proposed) | Reading B | Grader A | Grader B | Panel flips under B |
|---|---|---|---|---|---|---|
| D-word-case | Case-insensitive word comparison? | yes | no | B | mixed | 1,231 (509 rows) |
| D-hyphen-plural | Must a `sentence_hyphens` answer join at least two sentences? | no | yes | A | B | 992 (544) |
| D-hyphen-inner | Hyphens inside a sentence allowed? | yes | only between sentences | B | B | 754 (397) |
| D-english | Must an all-caps or lowercase answer be English? | yes | case only | A | B | 421 (241) |
| D-word | What is a word? | letters and digits with inner `'` and `-` | whitespace token | - | - | 398 (234) |
| D-word-cjk | Words in text without spaces | one per CJK character | one per token | B | B | 351 (205) |
| D-edge-markup | Skip markdown around the first or last word? | yes | no | mixed | mixed | 306 (173) |
| D-lowercase-counting | "all lowercase words ... at most N times" | each word at most N | total at most N | B | A | 304 (162) |
| D-brackets-per-word | Each word in its own brackets? | yes | any brackets | A | B | 301 (177) |
| D-word-count-relation | "should appear N times" | exactly N | at least N | B | B | 215 (100) |
| D-sentence | Do line breaks end sentences? | yes | only `.!?` | B | B | 200 (96) |
| D-keyword-match | Do inflections or compound parts count? | no | yes | mixed | mixed | 196 (89) |
| D-palindrome-length | Minimum palindrome length | 3 letters | any | B | A | 194 (66) |
| D-end-case | Case-sensitive end phrase? | yes | no | B | A | 162 (78) |
| D-divider-edge | Leading or trailing `***` fails? | yes | ignored | B | A | 153 (51) |
| D-language-mixed | Other-language prose allowed if minor? | no | yes | B | A | 134 (48) |
| D-letter-case | Letter count includes uppercase? | yes | no | A | A | 119 (48) |
| D-letter-unit | "less than N letters": letters or words? | letters | words | A | judge | 118 (91) |
| D-postscript-dot | `P.S` as shown, or `P.S.` from kwargs? | as shown | kwargs | B | B | 91 (41) |
| D-allcaps-single | `I`, `A` count as all-capital words? | yes | no | A | B | 86 (54) |
| D-constrained-exact | Only the option, nothing else? | yes | option inside text | B | A | 75 (75) |
| D-postscript-end | Postscript must be at the end? | yes | anywhere | B | B | 73 (25) |
| D-postscript-case | `p.s.` accepted? | no | yes | B | B | 60 (20) |
| D-highlight-bold | `**bold**` is a highlight? | yes | no | A | A | 57 (18) |
| D-bracket-punct | Punctuation outside brackets? | allowed | every token bracketed | B | A | 56 (30) |
| D-section-preamble | Text before section 1? | allowed | not allowed | - | - | 54 (19) |
| D-consecutive-order | Consecutive letters in either order? | yes | alphabetical only | B | B | 53 (34) |
| D-repeat-center | Which words are "the center"? | middle word(s) | any inner word | B | A | 31 (20) |
| D-end-trailing | Emphasis or quotes after the end phrase? | allowed | not allowed | mixed | B | 30 (17) |
| D-section-count | "N sections": exactly or at least? | exactly | at least | B | A | 29 (8) |
| D-comma-chars | Fullwidth and ideographic commas? | count | only `,` | B | B | 27 (13) |
| D-section-case | Section word case-sensitive? | yes | no | A | B | 22 (1) |
| D-title-position | Title anywhere? | yes | must open | A | A | 17 (7) |
| D-repeat-original | Unchanged phrase may also appear? | yes, not counted | counts as a repetition | B | B | 14 (8) |
| D-exclamation-chars | `！` counts? | yes | only `!` | B | B | 9 (2) |
| D-blank-run | Several blank lines one break? | yes | each `\n\n` splits | B | A | 7 (2) |
| D-bullet-marker | `-` and `+` bullets count? | yes | only `*` | mixed | mixed | 6 (3) |
| D-placeholder-link | Markdown link text is a placeholder? | yes | no | A | A | 1 (1) |
| D-section-numbering | Numbers 1..N in order? | no | yes | - | - | 1 (0) |
| D-dot-chars | `．` and `…` count as dots? | yes | only `.` | B | B | 1 (1) |
| D-quote-chars | Typographic double quotes? | yes | only `"` | B | A | 1 (0) |
| D-outer-whitespace | Outer whitespace part of the answer? | no | yes | - | - | 0 |
| D-bigram-odd | Last group of one word allowed? | yes | no | A | judge | 0 |
| D-json-scalar | Bare JSON scalar accepted? | no | yes | B | B | 0 |

One open question is not yet an entry: whether a "each sentence" check passes text that has no sentence (an empty answer). The replacement fails `first_word_sent` and `last_word_sent` on such text but passes `sentence_hyphens` and the negative checks; grader A passes all of them.

## 11. Files

- `audit/ISSUE.md`: the issue record (progress, pins, contract hashes and times, held-out rule, step 6 decision rule, frozen-file hashes).
- `audit/CONTRACTS.md`: contracts, decision table, change log; frozen versions in `audit/frozen/`.
- `audit/lib/graders_under_audit.py`: graders A and B as their pipelines run them; `audit/lib/contract_grader.py`: the replacement.
- `audit/tests/`: fixtures and tests; `audit/repro.py`: one command per finding.
- `audit/scripts/`: data checks, panel grading and aggregation, fuzzing, content-free responses, unsatisfiable rows; outputs in `audit/out/`.
