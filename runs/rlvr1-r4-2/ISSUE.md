# Audit: graders of the RLVR1 instruction-following rows (SkyRL reward and task-curation gate)

This file stands in for the task's issue (offline exercise, no tracker). Entries are appended in order; each dated entry was written at the UTC time it gives, read from `date -u` in the same step.

## Progress

- [x] Step 1, pin the inputs (records, configuration and lockfile only), 2026-11-11T11:24Z
- [x] Step 2, contracts: `audit/CONTRACTS.md` v1 hashed 11:28Z before any grader code was read; v2 11:36Z, v3 11:55Z, v4 11:59Z (reasons in the contract's section 7)
- [x] Step 1 (cont.), pins that only the code shows
- [x] Step 3, 226 fixtures (`audit/tests/fixtures.py`), replacement grader `audit/lib/contract_grader.py` (44 switches), tests
- [x] Step 4, pipeline and property tests, fuzzing (`audit/scripts/fuzz.py`), content-free responses (`audit/scripts/content_free.py`)
- [x] Step 5, panel (stored responses only): `audit/scripts/panel.py`, `panel_report.py`, `fixes_only.py`, `unsatisfiable.py`
- [x] Step 6, not run in this exercise (no reviewers); the result that would change the recommendation is recorded in section 6
- [x] Step 7, report `audit/AUDIT.md` (section "Report" below); tests and report commands rechecked at the end of the session

Run all tests (539 passed, 167 xfailed at 12:09Z; every `audit/repro.py` command rechecked, output identical to `audit/out/repro_all.txt`): `cd <W> && NLTK_DATA=$PWD/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --rootdir audit audit/tests`

Reproduce every finding: same environment, `.venv/Scripts/python.exe audit/repro.py all` (expected output: `audit/out/repro_all.txt`).

Next, outside this exercise: step 6 on held-out responses (design in section 6); verify the unverified inputs (section 1); send the decision table to the maintainers.

## 1. Pinned inputs (from records, configuration and lockfile)

Recorded 2026-11-11T11:24Z. Every file under `case/` matched `case/MANIFEST.sha256` (`sha256sum -c`, 177 entries, no failure); MANIFEST.sha256 itself has sha256 `ccd2dc76e7ea9abeb77274c3ff43f691567f352c359c93cdd0fc7066a1747f23`, TASK.md `16e66ffc...05332`, SOURCES.md `5bb0d240...76410`.

| Input | Pin | Source of the pin |
|---|---|---|
| Grader A, SkyRL reward | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files with the git blobs in `case/SOURCES.md` | TASK.md, SOURCES.md |
| Checkers run by grader A, also the reference | `abukharin-nv/verifiable-instructions` `f46a5ac87b1400a4f8973039844b6be9b56e3faf`; installed copy in `.venv/Lib/site-packages/verifiable_instructions` is byte-identical to `case/reference/verifiable-instructions/verifiable_instructions/` (`diff -r -q`, no difference) | TASK.md, lockfile, checked |
| Grader B, task-curation gate | Marin `af9c678...`, `lib/verifyit/src/verifyit/` (installed copy byte-identical to `case/grader/verifyit/`, checked with `diff -r -q`) and `experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` blob `b8a1271f...` | TASK.md, lockfile, checked |
| Dataset | HF `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` revision `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a...0fc0b1b`; the 11,817 extracted rows sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` | SOURCES.md, manifest |
| One hash per row | `audit/frozen/row_hashes.tsv` (line, uuid, sha256 of the JSON line, sha256 of uuid+prompt+ids+kwargs), sha256 `f62bd2c062aa2033141984f9c551dd945f62deeee014a01ec0bf1507933df291`; 11,817 rows, no duplicate uuid | audit/scripts/row_hashes.py |
| Prompt rendering | one user message per row, no system message, no tools; the record's `prompt` equals the message text in all 11,817 rows; each model's chat template at the revision in `panel/CONFIGS.md` | data, CONFIGS.md |
| Row request settings | `request_json` = temperature 1.0, top-p 1.0, no tools, `parallel_tool_calls` false, in all rows; no row sets `grading_mode` (all 11,817 are `None`) | data |
| Panel generation | vLLM 0.11.0, torch 2.8.0+cu128, transformers 4.57.1; per-run model revision, decoding, token limit (2,048; 8,192 thinking) and `max_model_len` as in `panel/CONFIGS.md` | CONFIGS.md |
| Stop sequences, reasoning parser, reasoning-merge policy | not recorded in CONFIGS.md; `raw_response` is "the generated text" | unverified, see below |
| Python | CPython 3.12.10, 27 packages of `case/deps/requirements.lock.txt` (nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, ...) | lockfile |
| NLTK data | `punkt_tab` zip sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`, 77 files under `case/deps/nltk_data/` (in the manifest) | SOURCES.md |

Unverified inputs (cannot be fetched offline):

- The parquet file itself (`data/train.parquet` at revision `600262dd...`): verify with `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet --repo-type dataset --revision 600262dd37891b86075a80517e61dbfb105d7cbe` then `sha256sum`.
- The panel's stop sequences, reasoning parser and any reasoning-merge policy: the generation manifests are not in the case (`panel/CONFIGS.md` says so). Verify from the manifests of the generation run.
- Which NLTK data and package versions the RL training job loads: the rest of Marin (its lockfile and the job's image) is not in the case. Verify against Marin's `uv.lock` at `af9c678` and the job image.

## 2. Contract hash (recorded before any grader code was read)

2026-11-11T11:28Z: `audit/CONTRACTS.md` version 1, sha256 `02ace44b8e41f040f76857faaf92c89ebf0621ea30b1f199f4bc3a5f9847ef62`; a frozen copy is `audit/frozen/CONTRACTS_v1.md` (same hash). Up to this time the audit had read only `case/TASK.md`, `case/SOURCES.md`, `panel/CONFIGS.md`, the lockfile, the data file and the skill; no file under `case/reference/` or `case/grader/` had been opened. Version 1 has 37 decision entries. Later changes are listed in "Contract changes" with their reasons.

## Contract changes

- 2026-11-11T11:36Z: `audit/CONTRACTS.md` version 2, sha256 `75a88ce5153b620e74b4ae0594e979306450e0e6ee553adcc34f71bb03aaa70f` (frozen copy `audit/frozen/CONTRACTS_v2.md`). Seven changes, each with its reason in the contract's section 7: `D-keyword-match` and `D-edge-markup` narrowed, `D-palindrome-length` clarified, five new decision entries (`D-section-count`, `D-end-case`, `D-bracket-punct`, `D-divider-edge`, `D-postscript-case`) that keep version 1's proposal, and clarifications for `nth_paragraph_first_word` (nth > N is unsatisfiable), `sentence_hyphens` and `quotation`. All were prompted by reading the grader code; none changes a version 1 proposal. 42 decision entries.

- 2026-11-11T11:55Z: version 3, sha256 `61fc514cd38c2c41e3e0f98f5625409916b86a2798077938de9f777154bf843c` (`audit/frozen/CONTRACTS_v3.md`). After the first panel run, from non-held-out responses: sentence boundaries (CJK marks, angle-bracket and emphasis closers, dots inside tokens), possessives and elided clitics count as the base word, uncased scripts have no lowercase words, `D-language-mixed` applies to the English checks, new `D-hyphen-inner`. No version 1 or 2 proposal changed.
- 2026-11-11T11:59Z: version 4, sha256 `40b8f8d8e12e116eae9d5a5fe518a957b0af3985143b47b379eb39637ca743a1` (`audit/frozen/CONTRACTS_v4.md`). New `D-hyphen-plural`: 993 of the replacement's 1,002 `sentence_hyphens` passes contain no join between sentences. Proposal keeps the literal reading. 44 decision entries.

## 1 (cont.). Pins that only the code shows (recorded after the contract hash)

- Extraction, grader A: `final_answer_text` (`answer_extraction.py`) removes every closed `<think>`/`<thinking>`/`<|start_think|>` block, keeps the text after the last closing marker, returns `""` when an opening marker is left unclosed, then strips whitespace and a trailing `<|eot_id|>`. A response with no marker at all is graded whole, even when the chat template opened the reasoning block and the model never closed it.
- Extraction, grader B: `grade_judge._answer_text(candidate, True, strip_outer=False)`, the same rule (copy of the same code). `convert_instruction_following` sets `empty_output=EmptyOutputPolicy.GRADE`, so an empty extraction is graded by the gate, not scored 0.
- Grader A builds each check with `build_instruction` and kwargs without `None`; with `grading_mode` absent the reward is binary. A check that raises is recorded in `instruction_errors`; `NemotronTaskSession._advance` then returns reward 0.0 with outcome `INFRA_ERROR` ("Verifier configuration failed").
- Grader B (`grade_judge._passes`) counts a raising check as failed, logs a warning and does not separate it.
- NLTK: grader A's `_ensure_nltk_data` looks for `tokenizers/punkt_tab` on NLTK's search path and, when missing, downloads it with `nltk.download("punkt_tab")` (no version or hash). NVIDIA's `count_sentences` loads `nltk:tokenizers/punkt/english.pickle`, which nltk 3.10.3 serves from `punkt_tab`; with `NLTK_DATA` set to `case/deps/nltk_data` it loads the pinned files (checked: `count_sentences("One. Two. Three.") == 3`). Grader B uses no NLTK.
- langdetect: grader A sets `DetectorFactory.seed = 0` before each row. verifyit's gate uses no language detector.
- `random`: NVIDIA's `build_description` draws from the process-global `random` module when a kwarg is missing or out of range; in this data that happens for the 77 `nth_paragraph_first_word` constraints with `nth_paragraph` > `num_paragraphs` (see the findings).
- Not in the case, so unverified: `skyrl_gym/source_task.py` (`session_parameters`), which builds the session's `extras`; as given, `NemotronTaskSession.__init__` raises unless `extra_info.nemotron_ultra.route == "task_session"`, and all 11,817 rows store `"skyrl_gym"`. Verify in Marin at `af9c678` that the lowering step rewrites the route.

## 5. Panel: held-out responses (recorded before any panel verdict was examined)

2026-11-11T11:50Z. Held-out set for any later replacement change and for step 6: every panel response whose row uuid has a sha256 (of the uuid string, UTF-8) starting with hex digit 0, 1 or 2 (about 3/16 of rows, the same rows in every run). The replacement may be changed only from the other responses; the held-out responses are not used to change it. Before this entry the replacement was changed twice, both crash fixes, not verdict tuning: a deeply nested JSON input raised `RecursionError` (found by the fuzzer) and a dotted capital I (`İ`, two characters when lowercased) raised `TypeError` in `no_adjacent_consecutive` on the first panel run, which stopped that run at 2,500 responses; the run was repeated in full after the fix.

## 6. Blinded review: not run; result recorded in advance

2026-11-11T12:04Z. No reviewers are available in this exercise, so no sample was drawn, frozen or rendered. When step 6 runs, the result that would change the recommendation (fix both graders, with the replacement grader as the reference for the fix) is:

- For grader A and for grader B separately: the replacement passes every fixture, its scored coverage is complete (it gives a verdict on all 55,783 panel constraints; B's gate covers 50,724 by design), and its error rate is lower than the grader's with a paired 95% interval that excludes zero. If the interval includes zero for a grader, the recommendation for that grader becomes "fix the listed findings only" (no replacement).
- If the replacement's own error rate has an upper 95% bound above 5% on the agreement stratum, the replacement is not fit to be the reference, and the recommendation becomes "fix the findings in the existing code, then re-audit".
- Sample design: draw from the held-out responses (section 5), stratified by (A vs R agree/disagree) x (B vs R agree/disagree, deterministic constraints only); take all or most disagreements and at least 130 consensus cases from the A-R agreement stratum (about 89% of verdicts) so the upper bound of a zero-error stratum stays below 2%. Record the seed, the stratum sizes and the sha256 of the case list here before any review starts.

## Findings (detail, counterexamples and commands: `audit/AUDIT.md`, section 9)

Grader A = SkyRL reward (NVIDIA checkers, the reference); grader B = task-curation gate (verifyit). Share = panel verdicts of the check that the finding changes.

- F1 (A) keyword matched as a substring (`existence`, `frequency`, `word_once`): 59 verdicts.
- F2 (A, B) `word_once` requires exactly one occurrence: A 776/1,808, B 742/1,808.
- F3 (A, B) `word_count_different_numbers` applies a hidden relation (206 data constraints with `less than`): 266/1,015 each.
- F4 (A) `repeat_phrase` checks only the last match; earlier first word breaks matching: 57/1,059.
- F5 (B) `repeat_phrase` counts unchanged copies: 486/1,059.
- F6 (A) `postscript` marker found anywhere: 132/1,277.
- F7 (A) `constrained_response` passes several options: 3/243.
- F8 (A, B) `multiple_sections` markers counted anywhere: 36/917 each.
- F9 (A, B) `number_bullet_lists` counts rules, italic starts, `-5` lines: A 21/1,019.
- F10 (A, B) `number_highlighted_sections` counts spaced asterisks: A 8, B 6.
- F11 (A) first word with trailing punctuation fails (`first_word_answer`, `first_word_sent`): 67/1,089, plus 44 shared with F39.
- F12 (A) `keyword_specific_position` counts punctuation tokens: 15 (shared with F39).
- F13 (A) `count_unique` counts repeated punctuation tokens: 94/1,341.
- F14 (A, B) `start_end` punctuation tokens and trailing punctuation: A 35, B 64 of 989.
- F15 (A) `no_adjacent_consecutive` compares digits and punctuation: 162/1,499.
- F16 (B) `no_adjacent_consecutive` checks repeated words instead: 872/1,499.
- F17 (A, B) `palindrome` accepts tokens without letters: A 36, B 166 of 1,165.
- F18 (A) `response_language` passes when detection fails: 9/1,600; all 780 on the empty answer.
- F19 (A) `last_word_answer` raises on empty text, recorded as INFRA_ERROR: 625 rows on the empty answer.
- F20 (A) `***` inside a line splits paragraphs: 184 verdicts.
- F21 (B) `number_paragraphs` ignores the `***` divider: 479/1,345.
- F22 (B) `paragraphs`, `paragraphs2` pass any two or more paragraphs: 675 verdicts.
- F23 (A) contractions split into two words: 29 verdicts.
- F24 (B) ASCII-only words in every word-based check: 160 verdicts.
- F25 (A) `letter_counting` counts ASCII letters only: 87/961.
- F26 (A) empty brackets count as placeholders: 1/1,201.
- F27 (A) `bigram_wrapping` leaves an odd last word unchecked: 160/1,157.
- F28 (A, B) `counting_composition` wrong separator and counts (1 data row).
- F29 (A) `nth_paragraph_first_word` with nth > N draws a random paragraph (77 data constraints): 23 verdicts.
- F30 (A, B) seven asterisks accepted as the separator: 31/557 each.
- F31 (B) `lowercase_counting` inverted: 1,314/1,712.
- F32 (B) `square_brackets` passes one bracketed span: 550/1,079.
- F33 (B) `sentence_hyphens` tests word hyphenation: 1 verdict after decisions.
- F34 (B) `quotation` accepts single quotes: 0 verdicts.
- F35 (B) whitespace title accepted: 0 verdicts.
- F36 (B) sentence splitting (abbreviations, closing quotes, CJK): 84/1,131.
- F37 (A) `lowercase_counting` counts ASCII words only: 48/1,712.
- F38 (A) `square_brackets` passes `[a]and[b]`: 2/1,079.
- F39 (A) sentence splitting (dots inside tokens, CJK marks): 103 verdicts, plus 59 shared.
- F40 (B) `postscript` marker after markdown not found: 7/1,277.
- P1 (A, B) extraction: unclosed reasoning graded as the answer (139 thinking responses); literal `<think>` empties an answer (14 instruct responses).
- P2 (A) NLTK `punkt_tab` downloaded at runtime, unversioned, when missing.
- P5 (B) a raising check is counted as a failed constraint, not a grading failure.

Data observations (not grader defects): 108 rows that no response can satisfy (lower bound, `audit/out/unsatisfiable.json`); 147 `P.S.` markers rendered as "P.S".

## Decision entries

44 entries, each with both readings, an example and the proposed reading (A) in `audit/CONTRACTS.md` section 6, and with which reading each grader follows and the panel effect in `audit/AUDIT.md` section 10: D-outer-whitespace, D-word, D-word-cjk, D-word-case, D-keyword-match, D-sentence, D-edge-markup, D-allcaps-single, D-english, D-repeat-center, D-repeat-original, D-lowercase-counting, D-placeholder-link, D-postscript-end, D-postscript-dot, D-bigram-odd, D-constrained-exact, D-json-scalar, D-section-case, D-section-preamble, D-section-numbering, D-bullet-marker, D-highlight-bold, D-brackets-per-word, D-title-position, D-letter-case, D-consecutive-order, D-palindrome-length, D-word-count-relation, D-language-mixed, D-blank-run, D-letter-unit, D-comma-chars, D-dot-chars, D-exclamation-chars, D-end-trailing, D-quote-chars, D-section-count, D-end-case, D-bracket-punct, D-divider-edge, D-postscript-case, D-hyphen-inner, D-hyphen-plural.

## Frozen files and outputs (sha256)

No review sample was frozen (step 6 not run). Recorded 2026-11-11T12:08Z:

- `audit/frozen/row_hashes.tsv` f62bd2c062aa2033141984f9c551dd945f62deeee014a01ec0bf1507933df291
- `audit/frozen/CONTRACTS_v1.md` 02ace44b8e41f040f76857faaf92c89ebf0621ea30b1f199f4bc3a5f9847ef62
- `audit/frozen/CONTRACTS_v2.md` 75a88ce5153b620e74b4ae0594e979306450e0e6ee553adcc34f71bb03aaa70f
- `audit/frozen/CONTRACTS_v3.md` 61fc514cd38c2c41e3e0f98f5625409916b86a2798077938de9f777154bf843c
- `audit/frozen/CONTRACTS_v4.md` 40b8f8d8e12e116eae9d5a5fe518a957b0af3985143b47b379eb39637ca743a1
- `audit/out/panel_verdicts.jsonl` 8cdce6b3a146a8b5cebb700310aca1713279d4fe44fce89392c77969684cd3ee
- `audit/out/panel_report.json` b0418ddf4746afdf0b5ac3d4ff03d72913fd130d3a8e055eb010072d11194302
- `audit/lib/contract_grader.py` bbb1463fd3d3c70c889d71b3f481d0e68def680a8bcf0511d6484cfa423336ba (the replacement that produced the panel verdicts)
- `audit/tests/fixtures.py` cec81cad4a5e59bb8fd482fb70af3e6dfea83fc029ccb2f118cfd3bf543872ea

## Report

2026-11-11T12:10Z: step 7 report written to `audit/AUDIT.md`, sha256 `95e6276e6eb096f2232e41d0aa5cb3b2bf1176de2394eafccbcd205ab4b993c8`. Recommendation: fix both graders; step 6 still has to estimate the error rates before the replacement grader can stand in for either. `case/` still matches `case/MANIFEST.sha256` (177 entries, no failure).
