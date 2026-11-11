# Audit of the RLVR1 instruction-following graders

The audit covers the two graders that score Marin's 11,817 Nemotron RLVR1 instruction-following rows (28,219 constraints, 47 instruction ids): the SkyRL reward `grade_instruction_following`, which runs NVIDIA's verifiable-instructions checkers, and the deterministic gate of the task-curation grader, which runs verifyit's `ifeval` checks. It followed `skill/SKILL.md` offline. The running record is `audit/ISSUE.md`.

## Result

Recommendation: **fix both graders** before using them as a reward. This rests on steps 1 to 5. Step 6 (the blinded review) did not run in this exercise, so this report has no error rate. Below, "disagreement" means a disagreement with the audit's replacement grader (`audit/replacement.py`, written from `audit/CONTRACTS.md`), not an error confirmed by reviewers.

Two variants of the replacement are compared with each grader:

- **Fixes only** takes the grader's own reading of every decision entry, check by check (`replacement.OFFICIAL`). Its disagreements with a grader remain even under the grader's own readings, so they are defects rather than decisions.
- **Proposed** takes the readings the audit proposes for the decision entries.

Effect on scores. On the stored panel (6 runs, 4 models, 23,315 responses), fixing only the SkyRL defects raises every model's score by 2.3 to 8.6 points, and every 95% bootstrap interval excludes zero. A same-settings greedy rerun moved the SkyRL score by +0.2 points [−0.5, +1.0].

| Run | Responses | SkyRL score | Fixes only | SkyRL − fixes only (held-out half) | Proposed | SkyRL − proposed | Gate pass | Gate − fixes only |
|---|---|---|---|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 29.3 | 33.5 | −4.2 [−5.8, −2.6] (−6.1) | 33.2 | −3.9 [−5.9, −2.0] | 49.9 | +6.8 [+4.2, +9.5] |
| Qwen3-4B-Instruct-2507 greedy repeat | 1,000 | 29.5 | 33.9 | −4.4 [−6.0, −2.7] (−6.5) | 33.5 | −4.0 [−5.9, −2.1] | 50.0 | +6.3 [+3.7, +9.1] |
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 29.5 | 34.3 | −4.8 [−5.3, −4.3] (−5.3) | 33.1 | −3.5 [−4.2, −2.9] | 47.8 | +4.4 [+3.7, +5.3] |
| Qwen2.5-7B-Instruct sample0 | 4,000 | 20.0 | 23.5 | −3.5 [−4.3, −2.6] (−3.7) | 20.0 | +0.0 [−1.1, +1.1] | 33.0 | +6.2 [+5.1, +7.3] |
| OLMo-2-1124-7B-Instruct sample0 | 3,998 | 19.1 | 21.4 | −2.3 [−3.0, −1.7] (−2.4) | 17.9 | +1.2 [+0.3, +2.1] | 32.0 | +6.9 [+5.7, +8.2] |
| Qwen3-4B-Thinking-2507 sample0 | 1,500 | 55.3 | 63.9 | −8.6 [−10.3, −6.9] (−10.1) | 64.7 | −9.4 [−11.5, −7.5] | 63.4 | −5.9 [−8.1, −3.8] |

Scores are percentages of rows with reward 1.0; gate pass is the percentage of rows whose deterministic constraints all pass, where the judge then decides the reward. Intervals are paired 95% bootstrap intervals over responses (2,000 resamples, `audit/scripts/panel_analyze.py`).

The verdicts behind the scores:

- **Constraint verdicts.** SkyRL disagrees with fixes only on 3,492 of 55,783 verdicts (6.3%; held-out half 6.3%) and with proposed on 10.0%. The gate's checks disagree with verifyit's fixes only on 7,466 of 50,724 gated verdicts (14.7%) and with proposed on 16.2%.
- **False rewards (SkyRL).** Of the 6,472 responses with SkyRL reward 1.0, the contract contradicts 396 under fixes only (6.1%; held-out half 5.5%) and 1,043 under proposed (16.1%).
- **False gate passes.** Of 10,192 gate passes, 2,711 (26.6%) fail a deterministic constraint under fixes only. They go to the judge, whose general criterion says "Formal style and formatting constraints are checked separately" (`graders.py`), so the judge is not asked to catch them.
- **False gate failures.** Of 13,123 gate failures, 1,618 (12.3%) satisfy every deterministic constraint under fixes only, and each of them gets reward 0.0.
- **Scored coverage.** The replacement gives a verdict on every constraint. SkyRL scores 23,314 of 23,315 responses; the remaining one raises a checker exception, which the session reports as `INFRA_ERROR`. The gate checks 50,724 constraints deterministically and leaves 5,059 semantic ones to the judge.

The largest defects:

- **Both graders: `keywords:word_once`.** A response that uses keyword X twice fails "Include keyword X in your response" (920 SkyRL and 853 gate false failures of 1,808 verdicts).
- **verifyit: three checks that test something else.** `count:lowercase_counting` checks the opposite of the text (1,181 false passes of 1,712), `keywords:no_adjacent_consecutive` checks for repeated words (858 false passes of 1,499), and `detectable_format:square_brackets` passes any response that contains one bracket pair (663 false passes of 1,079).
- **Both pipelines: graded-text extraction.** It grades the thinking text of an unclosed Qwen3 reasoning block and empties any answer that contains a literal `<think>`.
- **Data.** 77 rows ask for paragraph N+1 of N paragraphs, which no response can satisfy, and SkyRL then checks a randomly drawn paragraph. 526 rows hide the comparison relation of `keywords:word_count_different_numbers`.

What the fix covers:

- Make the extraction fail an unclosed reasoning block and keep a literal marker in a non-reasoning answer (G1, G2).
- Drop or repair the 77 impossible rows (G3), and either show the relation in the 526 `word_count_different_numbers` prompts or grade them by the shown text (G4).
- Rewrite verifyit's checks that test something other than the text (V1 to V8, V13) and fix the defects shared with the reference (S1 to S21).
- Pin the NLTK data (G5), and record a checker exception as a failed constraint rather than an infrastructure error (G6).

Replacing the benchmark is not needed: apart from G3, G4 and the 147 prose-joined prompts that show the marker `P.S.` as `P.S` (D-ps-marker), every constraint's prompt text matches its kwargs (`audit/scripts/template_coverage.py`).

## Scope and what was skipped

- Step 1: inputs are pinned in `audit/ISSUE.md` (manifest and installed-package hashes verified, one sha256 per row in `audit/frozen/row_hashes.tsv`). Inputs that could not be checked offline are listed there as unverified, with the command that would check each: the source parquet on Hugging Face, the panel's generation manifests (stop sequences, reasoning parser), the RL training run's own settings, and the lowering code that sets each row's route.
- Step 2: `audit/CONTRACTS.md` v1 was hashed (`c79ad255…`, 2026-11-11T09:52:44Z) before any grader code was read. The changes after that are logged in its section 3: 9 decision entries added and two alternative readings added to existing entries, all with their reasons. No proposed reading changed.
- Steps 3 and 4: 208 fixtures, 3 extraction fixtures, 6 targeted tests and 14 property tests in `audit/tests/`. Running `pytest audit/tests` gives 511 passed and 153 strict xfails.
- Step 5: the stored panel only (no compute in this exercise). The held-out half (first hex digit of sha256(uuid) ≥ 8) was fixed before grading. After the first panel pass, the replacement was changed using development-half disagreements only (`audit/ISSUE.md`, "Step 5 note"). Held-out numbers are shown next to the full ones.
- Step 6: **not run**. Nothing was drawn, frozen or rendered.
- Not available here and skipped: the issue tracker (`audit/ISSUE.md` stands in), a repository and research branch (scripts live in `audit/`), a Hugging Face dataset for frozen samples (`audit/frozen/`, sha256 in `audit/ISSUE.md`), `manage-pr`, and `use-iris`. The reference implementation has no tests, and verifyit's tests are not in the case, so step 4 found no reference test list to run.

## How to reproduce a verdict

From `<W>`, in Git Bash:

```bash
export NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe audit/repro.py <fixture id>
```

`audit/repro.py` prints the fixture's exact input, then `skyrl=… verifyit=… contract=…`. `skyrl` is the NVIDIA checker as `grade_instruction_following` applies it. `verifyit` is the curation check as `grade_judge_candidate` applies it, or `not-gated` for the four semantic ids. `contract` is the replacement under the proposed readings. Each finding below gives its counterexample, the command and the expected output line. `audit/scripts/check_report_commands.py` reruns every command in this file and compares the output.

## Findings

Panel counts give how many of the check's panel verdicts the defect affects, measured as disagreements with fixes only: FP is a false pass, FF a false fail, and n the check's verdicts on the panel. For SkyRL, the reference is the grader itself (NVIDIA's code at `f46a5ac`), so every SkyRL checker finding is also present in the reference. For verifyit, the last column says whether NVIDIA's checker has the same defect.

### Pipeline and data findings

**G1. Unclosed reasoning is graded as the answer** (graded-text extraction, both pipelines). Qwen3's chat template supplies the opening `<think>`, so a response whose reasoning never closes contains no marker at all. `final_answer_text` and `_answer_text` both return such text whole, and its thinking is graded. The contract says it is an extraction failure that fails every check. Panel: 139 of 1,500 Qwen3-4B-Thinking responses are unclosed; SkyRL gives 1 of them reward 1.0, and 18 pass the gate and go to the judge.
Input: reasoning model, raw text `Okay the user wants no commas so I will avoid them entirely and keep going`, constraint `punctuation:no_comma`.
`audit/repro.py --extraction unclosed-thinking` → `skyrl_reward=1.0 gate_passed=True contract_reward=0.0`

**G2. A literal `<think>` empties a non-reasoning answer** (graded-text extraction, both pipelines). Any unmatched opening marker makes the extraction return `""`. The empty text then passes prohibitions such as `punctuation:no_comma` (G7). No reading of the contract makes the comma-bearing answer pass: `D-literal-think` grades either the whole answer or the text before the marker, and both contain the comma. Panel: 22 non-reasoning responses contain a marker, and SkyRL gives 8 of them reward 1.0.
Input: non-reasoning model, raw text `Hello, use the <think> tag here`, constraint `punctuation:no_comma`.
`audit/repro.py --extraction literal-think-tag` → `skyrl_reward=1.0 gate_passed=True contract_reward=0.0`

**G3. 77 rows ask for an impossible paragraph, and SkyRL then checks a random one** (data and `length_constraints:nth_paragraph_first_word`). In 77 rows the prompt says "There should be N paragraphs" and also "Paragraph N+1 must start with word X", so no response can comply. NVIDIA's `build_description` replaces such an index with `random.randint(1, N+1)` from Python's global RNG. The verdict therefore depends on the RNG state, and some responses pass. Panel: 161 responses to these rows; for 45 of them the verdict changes across 20 seeds and passes under at least one. verifyit fails them every time, which is correct. The fix for these rows is a data repair: drop them, or rewrite them with a valid index. No row carries a frozen reference (`instruction_reference_seed` is absent from every `record_json`), and freezing with `instruction_references.py` would only make the random index reproducible, not satisfiable.
Input: kwargs `{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}`, text `Intro text.\n\nHistory matters.`
`audit/repro.py --nth-rng` → `skyrl verdicts for random.seed(0..9): [True, False, False, False, False, False, False, True, False, True] verifyit= False contract= False`

**G4. `keywords:word_count_different_numbers` hides its relation** (data, both graders). The prompt says "the word X should appear N times", while the kwargs also carry `relation`: `less than` in 206 constraints and `at least` in 320. Both graders apply the hidden relation. With `less than`, a response with exactly N occurrences fails and one with none passes, and no reading of the text allows that. The `at least` case is decision `D-word-count-relation`. Panel, fixes only: SkyRL FP 146 and FF 249, the gate FP 188 and FF 215, of 1,015 verdicts.
Input: kwargs `{"keyword": "policy", "frequency": 2, "relation": "less than"}`.
`audit/repro.py keywords:word_count_different_numbers:4d9ae016b37d` (text `This policy and that policy differ.`) → `skyrl=False verifyit=False contract=True`
`audit/repro.py keywords:word_count_different_numbers:b7d809aaee5a` (text `One policy only.`) → `skyrl=True verifyit=True contract=False`

**G5. NLTK data is downloaded at grading time** (unpinned input, SkyRL). If `tokenizers/punkt_tab` is missing, `_ensure_nltk_data` calls `nltk.download("punkt_tab")`, which has no version and no hash. Six SkyRL checks depend on that file: `number_sentences` (punkt), and `capital_word_frequency`, `count_unique`, `counting_composition`, `keyword_specific_position` and `start_end` (`word_tokenize`). In this case the data is pinned by the zip's sha256 under `case/deps/`, but Marin's code pins nothing.

**G6. A checker exception is reported as an infrastructure failure** (SkyRL session). `last_word:last_word_answer` raises `IndexError` on an empty or whitespace-only answer. `grade_instruction_following` counts that constraint as failed, but `NemotronTaskSession._advance` then returns `Outcome.INFRA_ERROR` ("Verifier configuration failed") instead of a graded 0.0. The empty answer hits all 625 such constraints, the fuzzer hit 180 of 3,000 texts, and the panel has one case. In the non-default `grade_nemotron_instructions` path, NVIDIA's `copy:repeat_phrase` returns `None` (two exact copies) and langdetect raises on text without letters (`12345`); both become `verification_error` with reward 0.0, which was checked by hand.
`audit/repro.py --empty-last-word` → `skyrl_reward=0.0 results=[False] instruction_errors=['IndexError: list index out of range']`

**G7. Content-free responses earn full SkyRL reward** (both graders; `audit/scripts/step4_content_free.py`).

| Response | Rows with SkyRL reward 1.0 | Gate passes | Contract reward 1.0 |
|---|---|---|---|
| empty text | 1,702 | 810 | 967 |
| a single `.` | 1,144 | 682 | 829 |
| restating the prompt's requirement text | 813 | 1,308 | 558 |

The contract applies each check literally (`D-empty`), so pure prohibitions also pass an empty text. The SkyRL excess over the contract comes from checker defects: language detection failing open (S16), `first_word:first_word_sent` and `last_word:last_word_sent` passing when there is no sentence, `bigram_wrapping` passing vacuously (S5), `.` counting as a palindrome (S15), and the hidden `less than` relation (G4). SkyRL has no criterion for content at all, so a row whose constraints are all prohibitions is solved by an empty answer even under the contract. That is a property of the task, which the maintainers should know about.

### SkyRL (NVIDIA checker) findings

Each of these is also present in the reference (the same code). Where verifyit has the same defect, the finding says so.

| Id | Check | Counterexample (fixture id) | Contract broken | Panel, fixes only |
|---|---|---|---|---|
| S1 | `keywords:word_once` | `We fix it and fix it again.` (`keywords:word_once:c67fb421612a`) | "Include keyword fix" holds with two occurrences; the checker requires exactly one, counting substrings. verifyit has the same defect. | SkyRL FF 920 / 1,808; gate FF 853 |
| S2 | `count:count_unique` | `Cats sleep. Dogs bark.` (`count:count_unique:9cd87e0b94da`) | Punctuation is not a word; `word_tokenize` makes the two periods a repeated "word". | FF 111 / 1,341 (SkyRL only; judged in curation) |
| S3 | `count:counting_composition` | three paragraphs split by the instructed `* * *` (`count:counting_composition:90d639689afa`), and the same with `***` (`…:9da6d8970e4b`) | The text's divider is `* * *`, but the checker splits on `***`; it also counts the period as a word, so `exactly 2 words` cannot be met. | 1 constraint |
| S4 | `detectable_content:postscript` | `Remember the P.S. note in my letter.` (`…postscript:090ea1d7c178`); a `P.P.S.` line for marker `P.S.` (`…postscript:0abed6f46391`) | The marker must start a line; the pattern has no line anchor, and `p.p.s.` contains `p.s.`. | FP 137 / 1,277 |
| S5 | `detectable_format:bigram_wrapping` | `<<I am>> <<at home>> today` (`…bigram_wrapping:4770ecf17552`); `<<In>> <<spark>> <<using>> <<select>>` (`…:b95bcf240b88`); one unspaced Chinese sentence (`…:047f0a889d6f`); empty text (`…:284673f89c4b`) | Every word must sit in a two-word group; the checker only tests whether token 2k starts with `<<` and token 2k+1 ends with `>>`. | FP 187 / 1,157 (SkyRL only) |
| S6 | `detectable_format:constrained_response` | `My answer is yes. My answer is no.` (`…constrained_response:0848d7a85791`) | The answer must be one of the options; a response containing two of them passes. | FP 3 / 243 |
| S7 | `detectable_format:multiple_sections` | `This answer has one part. See SECTION 2 of the manual.` with 1 section (`…multiple_sections:a1f94585247f`) | A marker begins a section at the start of a line; the checker counts it anywhere. verifyit has the same defect. | FP 42 / 917; gate FP 37 |
| S8 | `detectable_format:number_bullet_lists` | a `---` rule (`…number_bullet_lists:4a8b628d0685`), a line starting with `*Note:*` (`…:b6f76f574d2b`), a line starting with `-5` (`…:c61d23e15734`) | A rule, an italic start and a negative number are not bullets; the checker counts every line that starts with `-` or with `*` followed by anything but `*`. | FF 18, FP 3 / 1,019 |
| S9 | `detectable_format:number_highlighted_sections` | `Compute 2 * 3 * 4 now.` with 1 highlight (`…number_highlighted_sections:bf401f59c7f0`) | Multiplication signs are not emphasis. verifyit has the same defect. | FP 33 / 1,070; gate FP 32 |
| S10 | `detectable_format:sentence_hyphens` | `This is a well-known fact.-Everyone agrees.` (`…sentence_hyphens:20ec17c6530b`) | A hyphen inside a word is not a sentence joint; the checker splits at every `-`. | FF 495, FP 59 / 1,300 (most FF are hyphen-joined answers without terminal punctuation) |
| S11 | `detectable_format:square_brackets` | `[Hello], [world].` (`…square_brackets:831b57263789`) | Punctuation outside the brackets is not a word; the checker requires every whitespace token to start with `[` and end with `]`. | FF 61, FP 34 / 1,079 |
| S12 | first and last word: `first_word:first_word_answer`, `first_word:first_word_sent`, `length_constraints:nth_paragraph_first_word`, `last_word:last_word_answer`, `keywords:start_end` | `development, as a field, matters.` (`first_word:first_word_answer:9797c7c8db2b`); `"development" is the word.` (`…:cbce66c76591`); `peace, friends, comes first. peace stays.` (`first_word:first_word_sent:32c4ea0f38b8`); `if: rain falls.` + paragraph (`length_constraints:nth_paragraph_first_word:0226746e53f1`); `- "hello" there my friend hello` (`keywords:start_end:1c1575fb20fd`) | Punctuation attached to a word is not part of it; the checkers compare the raw whitespace token. Panel cases include `history—expression.` as a last token. | FF: first word 121 / 1,089, per sentence 89 / 1,024, last word 67 / 1,285, nth paragraph 5 / 1,048, start-end 9 / 989 |
| S13 | `keywords:keyword_specific_position` | `I live nearby. Well, the village is big.` with n=2, m=3 (`…keyword_specific_position:1f964c286318`) | A comma is not a word; `word_tokenize` makes it word 2. | FF 15, FP 3 / 1,341 |
| S14 | `keywords:no_adjacent_consecutive` | `"Apples" bring joy.` (`…no_adjacent_consecutive:82e0c4612db5`); `Room 1 2 here.` (`…:5d7ea658ecbd`) | Compare the first letters of words; the checker compares the first characters of tokens, so a quote mark hides `a`→`b`, and the digits 1 and 2 fail. | FP 77, FF 5 / 1,499 |
| S15 | `keywords:palindrome` | `Items:\n- one\n- two` (`…palindrome:9d5c8c233244`); `Level ground.` (`…:6d0b9ebee094`); `Fast racecar.` (`…:fe4dbe1fc0a0`) | A palindrome is a word or phrase; the checker passes any token equal to its reverse (`-`, `.`, `1`), compares case-sensitively, and keeps attached punctuation. | FP 20, FF 56 / 1,165; `.` alone passes all 618 constraints |
| S16 | `language:response_language` | `12345 !!!` (`…response_language:49fc9594ce17`); empty text (`…:63eb3cf12cff`) | No text, no language; langdetect's exception is counted as a pass. | FP 9, FF 8 / 1,600 (SkyRL only); empty text passes all 780 |
| S17 | `change_case:english_capital` | `THE NEW LIBRARY OPENS ON MONDAY, AND STUDENTS CAN BORROW BOOKS, LAPTOPS, AND CAMERAS.` (`…english_capital:ef5ebf1081e9`); `TO JEST PROCES ARTYSTYCZNY, ZALEŻNY OD OSOBY I JEJ STYLU.` (`…:f43997e63290`) | The response must be English; the checker fails the English text and passes the Polish one, because langdetect run on uppercase text answers `de` for the first and `en` for the second. | FF 84, FP 20 / 1,534 |
| S18 | `length_constraints:nth_paragraph_first_word` | `x\n\n\n\nfoo here\n\nbar here` with 3 paragraphs, paragraph 3 = `foo` (`…nth_paragraph_first_word:86062b0e0b35`) | Paragraph 3 is `bar here`; the checker counts non-empty pieces but indexes the raw split list, empty pieces included. | FP 14 / 1,048 |
| S19 | `detectable_content:number_placeholders` | `Fill in [] and [ ].` (`…number_placeholders:435f03a4dbbe`) | Empty brackets are not placeholders. | FP 8 / 1,201 |
| S20 | `count:lowercase_counting` | `это это это слово` with N=2 (`count:lowercase_counting:ed55143a55ad`) | Lowercase words in any script count; `\b[a-z]+\b` sees only ASCII. | FP 75, FF 10 / 1,712 |
| S21 | `length_constraints:number_sentences` | `今天很好。我们去公园。然后回家。` at least 3 (`…number_sentences:f116f8d17a7b`) | `。` ends a sentence; English punkt does not split on it. verifyit has the same defect. | FF 58, FP 18 / 1,131; gate FF 70 |

Commands and expected output for each counterexample, checked by `audit/scripts/check_report_commands.py`:

- `audit/repro.py keywords:word_once:c67fb421612a` → `skyrl=False verifyit=False contract=True`
- `audit/repro.py count:count_unique:9cd87e0b94da` → `skyrl=False verifyit=not-gated contract=True`
- `audit/repro.py count:counting_composition:90d639689afa` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py count:counting_composition:9da6d8970e4b` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py detectable_content:postscript:090ea1d7c178` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py detectable_content:postscript:0abed6f46391` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py detectable_format:bigram_wrapping:4770ecf17552` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py detectable_format:bigram_wrapping:b95bcf240b88` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py detectable_format:bigram_wrapping:047f0a889d6f` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py detectable_format:bigram_wrapping:284673f89c4b` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py detectable_format:constrained_response:0848d7a85791` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py detectable_format:multiple_sections:a1f94585247f` → `skyrl=True verifyit=True contract=False`
- `audit/repro.py detectable_format:number_bullet_lists:4a8b628d0685` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py detectable_format:number_bullet_lists:b6f76f574d2b` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py detectable_format:number_bullet_lists:c61d23e15734` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py detectable_format:number_highlighted_sections:bf401f59c7f0` → `skyrl=True verifyit=True contract=False`
- `audit/repro.py detectable_format:sentence_hyphens:20ec17c6530b` → `skyrl=False verifyit=False contract=True`
- `audit/repro.py detectable_format:square_brackets:831b57263789` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py first_word:first_word_answer:9797c7c8db2b` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py first_word:first_word_answer:cbce66c76591` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py first_word:first_word_sent:32c4ea0f38b8` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py length_constraints:nth_paragraph_first_word:0226746e53f1` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py keywords:start_end:1c1575fb20fd` → `skyrl=False verifyit=False contract=True`
- `audit/repro.py keywords:keyword_specific_position:1f964c286318` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py keywords:no_adjacent_consecutive:82e0c4612db5` → `skyrl=True verifyit=True contract=False`
- `audit/repro.py keywords:no_adjacent_consecutive:5d7ea658ecbd` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py keywords:palindrome:9d5c8c233244` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py keywords:palindrome:6d0b9ebee094` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py keywords:palindrome:fe4dbe1fc0a0` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py language:response_language:49fc9594ce17` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py language:response_language:63eb3cf12cff` → `skyrl=True verifyit=not-gated contract=False`
- `audit/repro.py change_case:english_capital:ef5ebf1081e9` → `skyrl=False verifyit=True contract=True`
- `audit/repro.py change_case:english_capital:f43997e63290` → `skyrl=True verifyit=True contract=False`
- `audit/repro.py length_constraints:nth_paragraph_first_word:86062b0e0b35` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py detectable_content:number_placeholders:435f03a4dbbe` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py count:lowercase_counting:ed55143a55ad` → `skyrl=True verifyit=False contract=False`
- `audit/repro.py length_constraints:number_sentences:f116f8d17a7b` → `skyrl=False verifyit=False contract=True`

### Task-curation (verifyit `ifeval`) findings

The reference column says whether NVIDIA's checker has the same defect.

| Id | Check | Counterexample (fixture id) | Contract broken | Panel, fixes only | In the reference? |
|---|---|---|---|---|---|
| V1 | `keywords:no_adjacent_consecutive` | `A big cat.` (`…no_adjacent_consecutive:0fd993dd1f23`); `The the end.` (`…:5dc70516d8d4`) | It checks for adjacent repeated words, not consecutive first letters. | FP 858, FF 64 / 1,499 | No (NVIDIA checks letters, with S14) |
| V2 | `count:lowercase_counting` | `the cat and the dog and the bird` with N=2 (`…lowercase_counting:925fbcb1888c`); `NASA ESA JAXA` (`…:49a831aa0548`) | "at most N times" is checked as "at least N lowercase words". | FP 1,181, FF 172 / 1,712 | No (NVIDIA counts at most, as a total: decision `D-lowercase-scope`) |
| V3 | `detectable_format:square_brackets` | `[Hello] world` (`…square_brackets:799dc08735ce`) | Every word must be bracketed; one bracket pair anywhere passes. | FP 663 / 1,079 | No |
| V4 | `copy:repeat_phrase` | `Time flies while having fun. Time flies whilst having fun.` (`…repeat_phrase:227d1bebe372`); two unchanged copies (`…:0168ab427276`); variants in a numbered list (`…:032a1d2d625e`) | Each repetition replaces one word; the check counts unchanged copies, at least N. | FP 461, FF 56 / 1,059 | No (NVIDIA counts variants) |
| V5 | `paragraphs:paragraphs`, `paragraphs:paragraphs2` | three `***` paragraphs (`paragraphs:paragraphs:928085d3d333`); two blank-line paragraphs for the `***` id (`…:1b6ebbfe0f60`); three blank-line paragraphs (`paragraphs:paragraphs2:d7b0631d5cee`) | "There should be 2 paragraphs" with a given separator; the check passes 2 or more paragraphs by either separator. | FP 284 / 1,150 and 442 / 1,391 | No |
| V6 | `length_constraints:number_paragraphs` | `First paragraph.\n***\nSecond paragraph.` (`…number_paragraphs:4750a35a5627`); the same with blank lines around `***` (`…:ff4d43abf085`); two blank-line paragraphs, no divider (`…:6799f5ab1aec`) | Paragraphs are separated by the `***` divider; the check counts blank-line paragraphs and ignores the divider. | FF 388, FP 104 / 1,345 | No |
| V7 | `detectable_format:sentence_hyphens` | `I like tea.-You like coffee.-We both like water.` (`…sentence_hyphens:c2f2c77f5a8b`); `This is a well-known fact.-Everyone agrees.` (`…:20ec17c6530b`) | Sentences are joined by hyphens; the check instead requires every sentence to contain a hyphen and no space. | FF 440, FP 2 / 1,300 | Different defect (S10) |
| V8 | `change_case:english_capital`, `change_case:english_lowercase` | French in capitals (`…english_capital:ad12daf0c0cc`); Polish in capitals (`…english_capital:f43997e63290`); Spanish in lowercase (`…english_lowercase:4a660b518e5a`) | "in English": the checks never test the language. | FP 99 / 1,534 and 121 / 1,208 | No (NVIDIA tests it, with S17) |
| V9 | `detectable_format:json_format` | `` ```json {"a": 1} ``` `` (`…json_format:6c5af5d369fe`); `` ```JSON `` fence (`…:27e1d2926988`) | Markdown ticks are allowed; the fence pattern needs a line break and a lowercase tag. | 0 on the panel | No |
| V10 | `keywords:start_end` | `Hello there my friend hello.` (`…start_end:a7b73552fa4f`); `- "hello" there my friend hello` (`…:1c1575fb20fd`) | Nothing may follow the last word, and a list dash is not a word; the check ignores the trailing period and its `WORD` pattern matches a lone `-`. | FP 56, FF 24 / 989 | Partly (the dash, S12) |
| V11 | `detectable_format:title` | `<< >>\nText.` (`…title:bfaf630a6f2a`) | A blank title is not a title. | 0 beyond extraction | No |
| V12 | `startend:quotation` | `'Hello there.'` (`…quotation:69768847ade0`) | Single quotation marks are not double quotation marks. | 0 on the panel | No |
| V13 | `count:counting_composition` | `Birds sing all day long. Dogs bark at night. Cats purr softly.` (`…counting_composition:6f3659fe3315`) | The check tests "at least n_sent sentences with at least n_words words" and ignores the paragraphs. | 1 constraint | Different defect (S3) |
| V14 | every word-based check (palindromes, first and last words, counts) | `Я знаю, оно здесь.` (`keywords:palindrome:cd16cb348637`) | Words in any script; `WORD = [A-Za-z0-9'\-]+` sees only ASCII. | palindrome FF 189 / 1,165; the count also holds multi-word palindromes, which the contract accepts and verifyit never checks | No (NVIDIA uses whitespace tokens) |
| V15 | `keywords:word_once` | S1 | as S1 | FF 853 / 1,808 | Yes (S1) |
| V16 | `keywords:word_count_different_numbers` | G4 | as G4 | FP 188, FF 215 / 1,015 | Yes (G4) |
| V17 | `detectable_format:multiple_sections` | S7 | as S7 | FP 37 / 917 | Yes |
| V18 | `detectable_format:number_highlighted_sections` | S9 | as S9 | FP 32 / 1,070 | Yes |
| V19 | `length_constraints:number_sentences` | S21 | as S21 | FF 70 / 1,131 | Yes |

- `audit/repro.py keywords:no_adjacent_consecutive:0fd993dd1f23` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py keywords:no_adjacent_consecutive:5dc70516d8d4` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py count:lowercase_counting:925fbcb1888c` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py count:lowercase_counting:49a831aa0548` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py detectable_format:square_brackets:799dc08735ce` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py copy:repeat_phrase:227d1bebe372` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py copy:repeat_phrase:0168ab427276` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py copy:repeat_phrase:032a1d2d625e` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py paragraphs:paragraphs:928085d3d333` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py paragraphs:paragraphs:1b6ebbfe0f60` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py paragraphs:paragraphs2:d7b0631d5cee` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py length_constraints:number_paragraphs:4750a35a5627` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py length_constraints:number_paragraphs:ff4d43abf085` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py length_constraints:number_paragraphs:6799f5ab1aec` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py detectable_format:sentence_hyphens:c2f2c77f5a8b` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py change_case:english_capital:ad12daf0c0cc` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py change_case:english_lowercase:4a660b518e5a` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py detectable_format:json_format:6c5af5d369fe` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py detectable_format:json_format:27e1d2926988` → `skyrl=True verifyit=False contract=True`
- `audit/repro.py keywords:start_end:a7b73552fa4f` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py detectable_format:title:bfaf630a6f2a` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py startend:quotation:69768847ade0` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py count:counting_composition:6f3659fe3315` → `skyrl=False verifyit=True contract=False`
- `audit/repro.py keywords:palindrome:cd16cb348637` → `skyrl=True verifyit=False contract=True`

Not a grader finding but unverified: every row has `route = "skyrl_gym"`, while `NemotronTaskSession` raises unless the route is `task_session`. The lowering code that may rewrite the route is not in the case (`audit/ISSUE.md`).

## Decision entries for the maintainers

There are 46 entries (`audit/CONTRACTS.md`, sections 2 and 3). Each has a switch in `audit/replacement.py`. The table gives the audit's proposed reading, the alternative, each grader's reading, and how many panel disagreements a single alternative reading explains (SkyRL / gate, from `panel_summary.json`, `decision_counts`). The counts overlap, because one disagreement can be explained by several entries.

| Entry | Question | Proposed | Alternative | SkyRL reads | verifyit reads | Explains (SkyRL / gate) |
|---|---|---|---|---|---|---|
| D-hyphens-single | Does a one-sentence response satisfy sentence_hyphens? | yes | needs a joint | yes, unless the sentence holds a hyphenated word (S10) | needs a hyphen in each sentence (V7) | 489 / 439 |
| D-word | What is a word? | letter/digit runs, internal `'` `-` | whitespace tokens; or split at `'` `-` | mixed per check | ASCII runs | 416 / 284 |
| D-lowercase-scope | "all lowercase words … at most N times": each or total? | each word | total | total | inverted (V2) | 275 / 11 |
| D-keyword-match | Does `options` contain the keyword `option`? | no, whole words | substring | substring (existence, frequency, word_once); whole word (forbidden) | whole word | 272 / 129 |
| D-word-case | Case in word comparisons | ignore | exact | ignore, except count_unique, keyword position, palindrome, repeat_phrase | ignore | 250 / 137 |
| D-palindrome | Minimum palindrome | 3+ letters | any word incl. `a` | any token (S15) | 3+ ASCII letters | 162 / 9 |
| D-end-case | Case of the end phrase | exact | ignore | ignore | exact | 161 / 0 |
| D-divider | Form of the `***` divider | own line | any substring | any substring | ignored (V6) | 159 / 132 |
| D-word-count-relation | word_count_different_numbers with hidden `at least` | exactly N | at least N | at least | at least | 150 / 150 |
| D-divider-edges | Divider before the first or after the last paragraph | breaks the count | ignored | ignored | ignored (`paragraphs:paragraphs` only; V6 ignores dividers) | 140 / 53 |
| D-sentence | Do line breaks end sentences? | yes | no | no | no | 121 / 132 |
| D-consecutive-alphabet | Alphabet in a non-Latin answer | Latin only | the answer's own | any character by code point | n/a (V1) | 108 / 33 |
| D-letter-counting | "Answer with at least N letters": which letters | any script | Latin only | Latin only | counts words (judged) | 96 / – |
| D-ps-marker | `P.S` without its period when the prompt shows `P.S` | passes | fails | fails | fails | 95 / 95 |
| D-repeat-exact-copy | Do unchanged copies count toward N? | no | yes | yes (if the last match differs) | only copies count (V4) | 78 / 9 |
| D-constrained-surround | Text around the option | not allowed | allowed | allowed | not allowed | 75 / 0 |
| D-ps-case | `p.s.` for marker `P.S.` | fails | passes | passes | passes | 63 / 63 |
| D-dot-chars | `。` `．` `…` count as dots | yes | ASCII only | ASCII only | ASCII only | 55 / 55 |
| D-consecutive-order | `c` then `b` | consecutive | ascending only | ascending only | n/a | 45 / 40 |
| D-start-end-single | One-word response | passes | needs two words | needs two tokens | passes | 42 / 13 |
| D-sections-exact | "must have N sections" | exactly | at least | at least | exactly | 29 / 0 |
| D-two-responses-edges | `******` at the very start or end | breaks it | ignored | ignored | ignored | 29 / 29 |
| D-end-trailing | Non-word characters after the end phrase | not allowed | allowed | a closing `"` allowed | not allowed | 28 / 0 |
| D-comma-chars | `，` `、` `،` count as commas | yes | ASCII only | ASCII only | ASCII only | 27 / 27 |
| D-word-markup | `**Word**` is the word | yes | no | no (first word, start-end) | no at line starts (postscript, sections) | 24 / 11 |
| D-brackets-each | One word per bracket group | yes | groups may hold several | yes | any group (V3) | 22 / 170 |
| D-repeat-center | Which word may be replaced | any inner word | the middle word(s) | any inner word | n/a | 17 / 19 |
| D-lowercase-count | `The` counts as `the` | no | yes | n/a | n/a | 13 / 3 |
| D-exclamation-chars | `！` `¡` count | yes | ASCII only | ASCII only | ASCII only | 9 / 9 |
| D-paragraph-split | `\n \n` or `\n\n\n\n` between paragraphs | separates | exact `\n\n` only | exact | blank runs | 6 / 2 |
| D-capital-word | Does `I` count as a capital word? | yes | no | yes | no | 3 / 80 |
| D-quote-chars | Curly double quotes | count | ASCII only | ASCII only | count (plus single quotes, V12) | 1 / 0 |
| D-two-responses-separator | 7 or more asterisks as the separator | no | yes | yes | yes | 1 / 1 |
| D-sections-case | `Section 1` for splitter `SECTION` | fails | passes | fails | passes | 0 / 21 |
| D-literal-think | Literal `<think>` in a non-reasoning answer | graded whole | strip from the marker | neither: empties the answer (G2) | same | – |
| D-english | How "in English" is decided | language ID on the whole text | every sentence English | langdetect on uppercase text (S17) | not tested (V8) | – |
| D-language-mixed | Latin names or code in a non-Latin answer | allowed | not allowed | langdetect | judged | – |
| D-placeholder | Do `[1]` and links count as placeholders? | yes | no | yes | yes | 0 / 0 |
| D-bigram-odd | Final one-word group | allowed | not allowed | final word unchecked (S5) | judged | 0 / – |
| D-json-value | Must the JSON be an object or array? | yes | any value | any | any | 0 / 0 |
| D-bullet-marker | Do `+` bullets count? | yes | `*` only | `*` and `-` | `*` and `-` | 0 / 0 |
| D-bullet-nested | Do nested bullets count? | yes | no | yes | yes | 0 / 0 |
| D-highlight-markup | Does `**x**` count as a highlight? | yes | no | yes | yes | 0 / 0 |
| D-title-position | Title position | anywhere | first line | anywhere | anywhere | 0 / 0 |
| D-letter-case | Case in letter counts | ignore | lowercase only | ignore | ignore | 0 / 0 |
| D-empty | Empty graded text | literal | fails every check | literal, plus the vacuous passes of G7 | literal | – |

Entries the maintainers should settle first, by panel volume: D-hyphens-single, D-word, D-lowercase-scope, D-keyword-match, D-word-case, D-palindrome, D-end-case and D-divider. Two entries make some rows unsatisfiable under the proposed reading:

- **D-end-case.** 48 rows pair the end phrase with `change_case:english_lowercase`.
- **D-ps-case.** 34 rows pair the postscript with `english_lowercase`.

## What step 6 still has to provide

The recommendation still needs the result recorded in `audit/ISSUE.md` ("Step 6 plan, not run"). That result has three conditions:

- The replacement passes every fixture.
- Scored coverage is complete.
- For each grader, the error rate of the replacement under the maintainers' readings is lower than the grader's, with a paired 95% interval that excludes zero.

The sample should stratify by disagreement between the grader and the replacement (fixes only), drawn from the held-out half. The SkyRL population is the 27,950 held-out constraint verdicts, of which 1,752 disagree; the gate's is 25,449 gated verdicts, of which 3,801 disagree. Sample all or most disagreements, plus about 175 agreements per grader. The agreement stratum holds 93.7% of the SkyRL population, so if the review finds no error there, it needs n ≥ 172 to keep that stratum's added upper bound, 0.937 × (1 − 0.025^(1/n)), below 2 points. Language-model reviewers would use `skill/references/reviewer-prompt.md` with a helper that prints the exact graded text.

Until that review exists, every rate in this report is a disagreement with the audit's own replacement. Fixtures and spot checks support the replacement, but no independent reviewer has confirmed it. Its language identification (langdetect on lowercased text) and its sentence splitter are approximations.

## Files

- `audit/ISSUE.md`: the record, including progress, pinned inputs, the contract hash, the logged changes, step results and frozen hashes.
- `audit/CONTRACTS.md`: the contracts and decision entries. v1 is frozen as `audit/frozen/CONTRACTS_v1.md`.
- `audit/replacement.py`, `audit/harness.py`, `audit/repro.py`.
- `audit/tests/`: `fixtures.py`, `fixture_expectations.json`, `test_fixtures.py`, `test_properties.py` and `conftest.py`.
- `audit/scripts/`: the scripts behind each step: `verify_manifest`, `row_hashes`, `survey_*`, `template_coverage`, `check_runtime_inputs`, `classify_fixtures`, `step4_content_free`, `step4_fuzz`, `panel_grade`, `panel_analyze`, `panel_headline`, `show_disagreements` and `check_report_commands`.
- `audit/out/`: generated outputs, including `panel_verdicts.jsonl` (per-response verdicts), `panel_summary.json` and `.txt`, `panel_headline.txt`, and the step 4 outputs.
