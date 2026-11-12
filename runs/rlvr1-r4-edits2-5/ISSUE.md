# Audit of the RLVR1 instruction-following graders (offline issue record)

Stands in for the issue tracker (no tracker in this exercise). Entries are
added in order; times are UTC from `date -u`.

## Progress

- [x] Step 1: pin inputs (inputs that only code shows are added after the contract hash, below).
- [x] Step 2: contracts written from the requirement texts, hash recorded 2026-11-12T11:22:25Z, before any grader code was read.
- [x] Step 3: 205 hand and extraction fixtures (`audit/tests/fixture_defs.py` → `audit/scripts/build_fixtures.py` → `audit/fixtures.jsonl`, `audit/tests/known_failures.json`); replacement grader `audit/replacement/contract_grader.py` passes all; `pytest audit/tests` green (xfail strict for current grader failures).
- [x] Step 4: property/metamorphic (`scripts/step4_properties.py`), fuzz (`scripts/step4_fuzz.py 300 20261112`, then `scripts/filter_fuzz.py`), content-free (`scripts/step4_content_free.py`, all rows + per-check fixtures); all merged by `scripts/build_fixtures.py work/property_fixtures.jsonl work/fuzz_fixtures.jsonl work/content_free_fixtures.jsonl` into 945 fixtures (final counts in the step 3 entry); tests green.
- [x] Step 5: panel (stored responses in case/panel/ only): `scripts/panel_grade.py` → `work/panel_verdicts.jsonl` (frozen copy `frozen/panel_verdicts.jsonl`), `scripts/panel_analyze.py` → `work/panel_summary.json`, `scripts/panel_extra.py` → `work/panel_tables.md`.
- [ ] Step 6: not run in this exercise (no reviewers); what it must provide is in AUDIT.md section 6.
- [x] Step 7: `audit/AUDIT.md` written 2026-11-12T11:59–12:10Z. Final checks at 12:10:52Z: `pytest` 2,209 passed, 74 skipped, 552 xfailed; the 56 appendix commands extracted from AUDIT.md and run in Git Bash all print the stated verdicts (`scripts/check_report_appendix.py`, then `bash work/appendix_commands.sh | python scripts/check_commands.py`); `case/MANIFEST.sha256` still verifies (nothing under `case/` or `skill/` changed).

Rebuild everything: `bash audit/scripts/run_all.sh` (about 2 minutes; ends with the two command checks).

Next (if the session continues): step 6 needs reviewers; otherwise only polish.

## Step 1. Pinned inputs (from run records, configuration and lockfiles)

| Input | Pin | Source |
|---|---|---|
| Grader A (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files, blobs in `case/SOURCES.md` | SOURCES.md, MANIFEST.sha256 |
| Checkers run by grader A, also the reference for grader B | NVIDIA verifiable-instructions `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (installed in `.venv` from git; copy in `case/reference/verifiable-instructions/`) | SOURCES.md, requirements.lock.txt |
| Grader B (task-curation deterministic gate) | Marin `af9c6789…` `lib/verifyit/src/verifyit/` (installed as `marin-verifyit` from git), `experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` | SOURCES.md, requirements.lock.txt |
| Data | open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 @ `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a…0b1b` (parquet not available offline: unverified, see below); extract `case/data/rlvr1_instruction_following.jsonl` sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159`, 11,817 rows, 28,219 constraints, 47 ids | SOURCES.md; recomputed |
| One hash per row | `audit/frozen/row_hashes.tsv` (uuid, sha256 of canonical JSON of uuid, prompt, instruction_id_list, kwargs; written by `audit/scripts/survey_data.py`), file sha256 `3cfefa3ef97c50fe217cba6894f2fe1602af0a1f29d5515d1c46fa540feec2b7` | computed 2026-11-12 |
| Prompt rendering | One user message per row, no system message, no tools (`request_json`: temperature 1.0, top-p 1.0); panel: each model's chat template at its HF revision, vLLM 0.11.0 | data rows, panel/CONFIGS.md |
| Generation settings of the panel | per `panel/CONFIGS.md`: token limit 2,048 (8,192 thinking), `max_model_len` 8,192 / 4,096 (OLMo) / 14,336 (thinking); stored per response as `max_tokens`, `finish_reason`, `num_tokens` | panel/CONFIGS.md, run files |
| Python and packages | CPython 3.12.10; `case/deps/requirements.lock.txt` sha256 `9e794ccf8f290b5ec41f1b54f64ebefb097a8980b3eaf015c85156400174caf8` (27 packages: nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, …) | lockfile |
| NLTK data | `punkt_tab` from zip sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`, 77 files hashed in MANIFEST.sha256 | SOURCES.md |
| Case files | `sha256sum -c case/MANIFEST.sha256` passed 2026-11-12T11:17Z (all 176 entries) | recomputed |

Unpinned or unverified (step 1):

- U1. Stop sequences, the chat template text and the server's reasoning parser of the panel runs are not in the stored records or CONFIGS.md (only model revisions). The thinking run's `raw_response` holds the reasoning and answer in one text (1,361 of 1,500 contain `</think>`; the opening `<think>` is in the rendered prompt). Verify from the generation manifests (not included): `gen/<folder>/manifest` fields for `stop`, `chat_template`, `reasoning_parser`.
- U2. The parquet itself (`data/train.parquet` at `600262dd…`) is not available offline; verify with `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet --revision 600262dd37891b86075a80517e61dbfb105d7cbe` then `sha256sum`.
- U3. The RL training run's generation settings (the policy's token limit, chat template, reasoning parser and stop sequences) are not part of this case; only the panel's are pinned.

## Step 2. Contract

- `audit/CONTRACTS.md` v1 sha256 `08c19d79cbc003b850acc96e22748957f884aa3ec450ade9f30b71c10f0c6e68`, recorded 2026-11-12T11:22:25Z, before any grader code was read (only TASK.md, SOURCES.md, CONFIGS.md, the lockfile and the data had been read). Frozen copy: `audit/frozen/CONTRACTS_v1.md` (same hash).
- Later contract changes are listed here with their reason.

### Inputs that only the code shows (pinned after the contract hash, 2026-11-12T11:27Z)

- Extraction, grader A: `final_answer_text` (`skyrl_gym/envs/nemotron_ultra/answer_extraction.py`, blob `7e88cf74…`): removes closed `<think>…</think>`, `<thinking>…</thinking>`, `<|start_think|>…<|end_think|>` blocks, keeps the text after the last closing marker, returns `""` when an opening marker remains, strips whitespace and a trailing `<|eot_id|>`. Text with no marker at all is graded whole.
- Extraction, grader B: `_answer_text(…, strip_reasoning=True)` in `verifyit/modes/grade_judge.py` (blob `3cb9b310…`): the same rule; `EmptyOutputPolicy.GRADE`, so an empty answer is graded, not zeroed.
- Grader A exceptions: `grade_instruction_following` records each checker exception in `instruction_errors`; `NemotronTaskSession._advance` turns any error into reward 0.0 with `Outcome.INFRA_ERROR` ("Verifier configuration failed"). Grader B: `_passes` logs a crashed check and counts it as failed (reward 0.0, a model failure).
- Grader A randomness: `build_description` draws missing or out-of-range kwargs with the unseeded `random` module; `_ensure_nltk_data` sets `langdetect.DetectorFactory.seed = 0`.
- NLTK: `count_sentences` loads `nltk:tokenizers/punkt/english.pickle`, which nltk 3.10.3 resolves to `PunktTokenizer('english')` from `punkt_tab`; `_ensure_nltk_data` downloads `punkt_tab` at grading time when it is missing (no version or hash check).
- langdetect 1.0.9 language profiles (bundled in the package); all 30 language codes of the data are supported.
- SkyRL's other reward `grade_nemotron_instructions` (`envs/instruction_verifyit.py`, used only when `verifyit_enabled`) builds the same NVIDIA checkers through `build_instruction`, except `punctuation:no_comma`, `punctuation_dot` and `punctuation_exclamation`, which go to verifyit's checks of the same ASCII characters. Not audited separately.

### Contract changes

- v1 → v2, 2026-11-12T11:27Z: D-edge-word narrowed. Punctuation and quotation marks next to a word are never part of the word (the shared D-word definition already says so), so only markdown symbols at the edge (`*`, `_`, `#`, backticks) remain a decision. Reason: planning the fixtures showed the v1 entry mixed an unambiguous case with a real ambiguity. v2 sha256 `255b3de523f53b2dde454695e3a87ad14c19330d6ba23cb2cbc3e64677f9e62f`, 2026-11-12T11:27:55Z, frozen as `audit/frozen/CONTRACTS_v2.md`.

- v2 → v3, 2026-11-12T11:46:37Z (before the panel run): added D-empty, D-hyphen-scope, D-start-end-one-word, D-postscript-case, a blank-span alternative of D-placeholder-form, numbers as palindromes, inline HTML tags are not words, a `***` that is not alone on its line is not a divider, capital words need an uppercase letter, non-Latin letters are not English under D-english. Reasons: each came from a fixture, property or fuzz case where the v2 text was silent or where a second reading turned out defensible (listed in AUDIT.md). v3 sha256 `8b96a9e89196ab93e594efb23fea4b2930d3d38b36a7c7a113ea307842a277d7` (`audit/frozen/CONTRACTS_v3.md`).

## Step 3. Fixtures and replacement grader (2026-11-12T11:30–11:45Z)

- Replacement grader: `audit/replacement/contract_grader.py`, one switch per decision entry (`PROPOSED`, `ALTERNATIVES`, `DECISIONS_BY_CHECK`). The version that graded the panel is frozen as `audit/frozen/contract_grader_panel.py`, sha256 `72190fc0f96b1af3c5d8eb7a64aa611c025a7e89ff698b549482ee705f7ee86d`.
- Classification rule (`scripts/fixture_lib.py: classify/explain`): a wrong verdict is a decision when some combination of non-proposed readings of the check's decision entries gives the grader's verdict (the entries are named); otherwise a finding.
- Fixture ids: instruction id plus the first 16 hex digits of sha256 of `[instruction_id, kwargs, response]`.
- Fuzz labels and content-free labels come from the replacement (contract, proposed readings); the finding groups were read by hand; 12 fuzz finding groups whose label rests on details the contract does not state (a bullet holding only `?`, `*** P.S.` lines, `SECTION` and its number on separate lines, …) were dropped by `scripts/filter_fuzz.py` (`work/fuzz_candidates.jsonl` keeps them).
- Final fixture set (after v4, duplicates removed): 945 = 205 hand, 3 extraction, 514 property/metamorphic, 99 fuzz, 124 content-free; `fixtures.jsonl` sha256 `2565feab41feec97725d5936bd8cfc3b4b99b81213814a6a8831fba5215fe380` at 2026-11-12T12:05Z (each rebuild changes it, because the G3 fixture records how many of 30 random gradings grader A passed), `tests/known_failures.json` sha256 `094821d63f6f90b10a19b010a2ebb6841d1ee79db193af23e0defe587e6900fd` (stable). Tests: 2,209 passed, 74 skipped (semantic constraints in grader B), 552 xfailed.

## Step 4. Reference comparison and stress tests (2026-11-12T11:35–11:46Z)

- Reference unit tests: the NVIDIA repository has no tests; verifyit's and SkyRL's own tests are not part of this case, so no grader test that encodes a decision could be listed.
- Fuzz (300 random responses per check, seed 20261112): 11 exceptions, all grader A `last_word:last_word_answer` IndexError on whitespace-only text; no verifyit exception. All 47 ids are known to verifyit (no import rejection). One exception does not stop a run: grader A turns it into `INFRA_ERROR`, reward 0; grader B counts it as a failed constraint.
- Content-free responses over all 11,817 rows (`work/content_free_summary.json`): the empty response gets grader A reward 1.0 on 1,702 rows and passes grader B's gate on 716 rows (then the LLM judge decides); under the literal reading of D-empty the contract would pass 2,022 rows, so 1,621 of the 1,702 are decision D-empty and 81 are finding A-F2 (`word_count_different_numbers` "less than"). The repeated text "Hello world. …" gets A reward 1.0 on 273 rows (replacement 238); the restatement of the prompt gets A reward 1.0 on 746 rows (replacement 466) and passes B's gate on 1,271 rows.
- Score-level transforms: none beyond the binary all-pass of grader A and the gate-then-judge fraction of grader B; both follow TASK.md (checked by reading `grade_instruction_following` and `grade_judge_candidate`).

## Panel held-out split (declared 2026-11-12T11:46Z, before the panel run)

The replacement was not changed from panel responses before this point. If panel disagreements prompt a replacement change, only the first 300 responses of each run file are inspected for it (development part); all later responses are held out, and the report gives the held-out numbers separately.

## Step 5. Panel (2026-11-12T11:47–11:58Z)

- First run with replacement v3 (`frozen/contract_grader_panel.py`). Inspection of development disagreements (n < 300 per run file only; `scripts/panel_inspect.py`, short answer excerpts, no reasoning text) found no replacement bug but showed (1) rows that pair `change_case:english_lowercase`/`english_capital` with `end_checker` (93), `postscript` (71) or `multiple_sections` (20), which a case-sensitive reading makes unsatisfiable, (2) postscripts that follow a sentence on the same line, (3) leading or trailing `******` separators. Contract v4 (2026-11-12T11:58:48Z, sha256 `076eafa835777038f411534d3a0f76c7283155483732f8219af117ca17dbb8b7`, `frozen/CONTRACTS_v4.md`): D-end-case, D-postscript-case, D-sections-case proposals changed to case-insensitive; D-postscript-line and D-two-responses-edge added. Replacement v4: `frozen/contract_grader_v4.py` sha256 `eae2bb9169ef7ac2f72fab71e30db0cbcf4745ee85ec4df8152a84a318613a36`. Panel regraded; held-out numbers reported separately.
- Panel verdicts: `frozen/panel_verdicts.jsonl` sha256 `4f864eeb9b8b0143a72a1141693d4114a7ec07f9ed875806a8477d34669c756e` (23,315 responses).
- Main numbers: grader A differs from the contract on 10.3% of 55,783 constraint verdicts (4.6% findings, 5.6% decisions); grader B on 17.2% of 50,724 gate verdicts (12.0% findings, 5.0% decisions). A's false rewards 986 / 6,475 (15.2%; held-out 919 / 5,868, 15.7%); 435 with at least one finding. Fixing findings only moves A's score −1.3 to +5.6 points per run and B's gate pass rate −7.9 to +4.7; the greedy rerun moved A by +0.2 and B by +0.1.
- Grader A is not deterministic: on the 161 panel responses to the 77 unsatisfiable rows (G3), 23 changed row reward across 10 gradings, and two full panel gradings gave Qwen2.5 803 and 801 passes.

## Decision entries

Listed in `audit/CONTRACTS.md` (D-*) with proposed readings; each entry's grader behavior and panel effect is in AUDIT.md section 4. Largest: D-empty (1,621 rows of empty-answer reward), D-hyphen-scope, D-keyword-match, D-lowercase-counting-scope, D-palindrome-length, D-bare-count.

## Findings

Ids: G = pipeline and data, A-F = grader A (SkyRL reward / NVIDIA checkers), B-F = grader B (verifyit gate). Counterexamples, commands, panel shares and reference status in AUDIT.md section 3; fixtures with class `finding` in `audit/fixtures.jsonl`.

- G1 unclosed reasoning graded as the answer (A, B); G2 a literal `<think>` in a non-reasoning answer empties it (A, B); G3 77 unsatisfiable `nth_paragraph_first_word` rows, randomized by A; G4 A raises on an empty `last_word_answer` and reports `INFRA_ERROR`; G5 NLTK data downloaded at grading time, unpinned. U1–U3 unpinned inputs (step 1).
- A-F1 `word_once` exactly one substring; A-F2 hidden `relation` in `word_count_different_numbers` (also B); A-F3 punctuation next to the first word; A-F4 `keyword_specific_position` counts punctuation, case-sensitive; A-F5 `count_unique` counts punctuation; A-F6 `counting_composition` divider and punctuation; A-F7 `bigram_wrapping` odd last word / unspaced text pass; A-F8 two constrained options pass; A-F9 inline section mentions count (also B); A-F10 `---` and italic lines count as bullets; A-F11 punctuation outside brackets fails; A-F12 `no_adjacent_consecutive` skips words behind punctuation, compares digits; A-F13 symbol tokens are palindromes; A-F14 `p.s.` matched inside words; A-F15 language passes text without letters; A-F16 inline `***` splits paragraphs; A-F17 list label `1.` is a sentence (also B); A-F18 `repeat_phrase` only checks the last copy; A-F19 langdetect misses upper-case English; A-F20 CJK sentence marks not split (also B); A-F21 HTML tag letters counted; A-F22 markdown asterisks counted by `count_unique`.
- B-F1 `repeat_phrase` counts unchanged copies; B-F2 `lowercase_counting` "at least"; B-F3 `no_adjacent_consecutive` checks duplicates; B-F4 `number_paragraphs` ignores `***`; B-F5 `paragraphs`/`paragraphs2` accept 2+ with either separator; B-F6 `square_brackets` needs one span; B-F7 `counting_composition` approximate; B-F8 `start_end` ignores trailing punctuation; B-F9 single quotes accepted; B-F10 ASCII-only words; B-F11 abbreviations end sentences; B-F12 phrase palindromes missed, `---` counted; B-F13 `* *` counted as a highlight; B-F14 blank title; B-F15 one-line JSON fence rejected.
