# Audit: graders of the Nemotron RLVR1 instruction-following rows

Offline stand-in for the issue tracker (the skill's "issue"). Entries are added in time order below the Progress section; times are UTC from `date -u`.

## Progress

- [x] Step 1: pin the inputs (2026-11-12 11:30)
- [x] Step 2: contracts, hash da7e3e7a… recorded 2026-11-12 11:33:26 UTC
- [x] Step 3: 252 fixtures, tests, replacement grader (11:49)
- [x] Step 4: properties, metamorphic, fuzz, content-free (12:04)
- [x] Step 5: stored panel graded by NV, VS, VG, R, RF (12:11)
- [ ] Step 6: blinded review: NOT RUN in this exercise (no reviewers)
- [x] Step 7: audit/AUDIT.md written (12:11); every quoted command rechecked

Next: nothing required; optional: step 6 review when reviewers exist (design in the Step 6 entry).

## Step 1. Pinned inputs (2026-11-12 11:30 UTC)

Taken from case/TASK.md, case/SOURCES.md, case/panel/CONFIGS.md, case/deps/requirements.lock.txt and the stored run records only (no grader code read yet).

| Input | Pin | Source |
|---|---|---|
| Grader 1 (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files, blobs in SOURCES.md | case/reference/skyrl_gym |
| Checkers that grader 1 runs, and reference for grader 2 | NVIDIA verifiable-instructions `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (no tests) | case/reference/verifiable-instructions |
| Grader 2 (task-curation deterministic gate) | Marin `af9c6789…`, `lib/verifyit/src/verifyit/` (every file) and `experiments/post_training/task_curation/datasets/nemotron_ultra/{graders,conversation}.py` | case/grader |
| Installed packages | `.venv` CPython 3.12.10; 27 packages as `deps/requirements.lock.txt` (sha256 `9e794ccf8f29…caf8`): nltk 3.10.3, langdetect 1.0.9, immutabledict 4.3.1, absl-py 2.5.0, regex 2026.9.29, marin-verifyit and verifiable-instructions from git at the two commits above | lockfile |
| NLTK data | `punkt_tab` from zip sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`; 77 files, each in MANIFEST.sha256 | case/deps/nltk_data |
| Dataset | open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 @ `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a…0b1b`; the 11,817 `instruction_following_simple_agent` rows, jsonl sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` | case/data |
| Per-row hashes | `audit/frozen/row_hashes.tsv` (index, uuid, sha256 of canonical JSON of uuid + prompt messages + instruction_id_list + kwargs), file sha256 `186ad2dc97aacdf93d553183b675954e7148ce27570ad610d1a9f50a7d975c1e`; 11,817 distinct uuids | audit/scripts/pin_inputs.py |
| Prompt rendering | one user message (the row's `prompt`), no system message, the model's own chat template at its pinned revision; `record_json.prompt` equals the user message in all 11,817 rows | data, CONFIGS.md |
| Request settings in the data | temperature 1.0, top-p 1.0, no tools, parallel_tool_calls false (`request_json`); no output budget or stop sequence recorded | data |
| Response extraction | SkyRL: `final_answer_text` before grading (TASK.md); task curation: `strip_candidate_reasoning_blocks=True` (TASK.md). Exact rules recorded after step 2 from code | TASK.md |
| Grading settings | SkyRL `grading_mode` default `binary`; no row sets `grading_mode`; SkyRL session `verifyit_enabled` default false (the value used by an RL run is not recorded in this case) | TASK.md, data |
| Panel generation | vLLM 0.11.0, torch 2.8.0+cu128, transformers 4.57.1, Python 3.12.3, one GPU; model revisions, token limits and `max_model_len` per CONFIGS.md (sha256 `0f48c4c0…93af5b93`) | CONFIGS.md |

Panel records (stored, step 1 counts; audit/scripts/pin_inputs.py):

| Run file | Responses | finish=length | contains `<think>` | contains `</think>` | empty |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct/sample0 | 4,000 | 65 | 3 | 0 | 0 |
| Qwen3-4B-Instruct-2507/greedy | 1,000 | 92 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507/greedy_repeat | 1,000 | 81 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507/sample0 | 11,817 | 620 | 11 | 0 | 0 |
| Qwen3-4B-Thinking-2507/sample0 (thinking) | 1,500 | 166 | 1 | 1,361 | 0 |
| OLMo-2-1124-7B-Instruct/sample0 | 3,998 | 39 | 0 | 0 | 1 |

Every panel uuid is a data uuid; no duplicates within a run file.

Unverified inputs (cannot be fetched offline):

- The upstream sources themselves (GitHub commits, the HF parquet). Verify with `git -C marin rev-parse af9c6789e878bed1a6fc9513232bcfc54ac73b3a` plus `git hash-object` on each file in SOURCES.md, and `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet --revision 600262dd37891b86075a80517e61dbfb105d7cbe` then `sha256sum`.
- Generation settings that change the graded text and are not in CONFIGS.md: stop sequences, the vLLM reasoning parser (if any), and whether a reasoning field was merged into `raw_response`. The generation manifests are not included. For the thinking model, `raw_response` holds `</think>` in 1,361 of 1,500 responses and `<think>` in 1, which suggests the chat template opens the think block in the prompt and no reasoning parser split the output.
- The RL run's SkyRL session config (`verifyit_enabled`, any `grading_mode` override) and its rollout token budget: not part of the case.

Pin checks: `audit/scripts/verify_pins.py` checks the 177 manifest files, that the installed `verifyit` (69 files) and `verifiable_instructions` (5 files) are byte-identical to the case copies, the frozen files, and that no `__pycache__` was written under case/. Run 2026-11-12 11:28 UTC: all pins match.

## Step 2. Contract hash (2026-11-12 11:33:26 UTC)

`audit/CONTRACTS.md` v1, sha256 `da7e3e7a38f48bcab8237a48632971a2e4319071700be4ecdd690d0e2e8940d4`, frozen as `audit/frozen/CONTRACTS_v1.md`. Recorded before any grader code (case/reference/**/*.py, case/grader/**/*.py) was opened. 47 contracts, general rules G1-G9, 45 decision entries. Later contract changes are logged below with their reason.

Data observations made while writing the contracts (from prompts only):

- `length_constraints:nth_paragraph_first_word`: 77 of 515 constraints ask for paragraph `nth_paragraph` > `num_paragraphs` ("There should be 2 paragraphs ... Paragraph 3 must start with word X"): no response can satisfy them.
- `keywords:word_count_different_numbers`: the prompt text never shows the row's `relation` kwarg ("should appear {frequency} times"); 526 constraints, 320 `at least`, 206 `less than`.
- `detectable_content:postscript`: 147 of 324 `P.S.` prompts show the marker as `P.S` (its final dot dropped where the instruction is joined into a sentence).
- `language:response_language`: 30 language codes; each prompt names the language in English (e.g. `pa` = Punjabi).

## Step 1 (continued, after the contract hash): inputs that only the code shows (2026-11-12 11:43 UTC)

- SkyRL extraction, `final_answer_text` (answer_extraction.py): removes every `<think>…</think>`, `<thinking>…</thinking>`, `<|start_think|>…<|end_think|>` block, keeps the text after the last closing marker, returns `""` when an opening marker is left, then strips whitespace and a trailing `<|eot_id|>`. A response with neither marker is graded whole; this includes a thinking model's response whose reasoning never closed (the template supplied `<think>`), which is then graded as the answer.
- Task-curation extraction, `grade_judge._answer_text(text, True, strip_outer=False)`: the same rules, byte for byte the same algorithm. `empty_output=EmptyOutputPolicy.GRADE`: an empty candidate is graded, not zeroed.
- SkyRL session: `advance` grades `final_answer_text(turn.text)`; any checker exception (`instruction_errors`) makes the transition `INFRA_ERROR` with reward 0.0. Rows route `skyrl_gym` in the data, and the session raises unless `route == "task_session"`; the lowering that would rewrite the route is not in the case (unverified).
- `grade_instruction_following` sets `langdetect.DetectorFactory.seed = 0`; `build_instruction` passes kwargs without `None`, and NVIDIA's `build_description` draws from the unseeded global `random` when an argument is missing or out of range (`ParagraphFirstWordCheck` redraws `nth_paragraph = randint(1, num_paragraphs + 1)` when `nth_paragraph > num_paragraphs`).
- `grade_nemotron_instructions` (SkyRL with `verifyit_enabled`): NVIDIA's checkers inside verifyit's ifeval grader, in a subprocess (`call_bounded`, timeout 30 s), except `language:response_language` (bare `langdetect.detect == code`, no exception handler), `change_case:english_capital`/`english_lowercase` (`isupper()/islower()` and langdetect `en`), `detectable_format:json_format` (fenced JSON through verifyit's JSON-schema grader), and the three `punctuation:*` ids, which run verifyit's own checks.
- Task-curation conversion (`convert_instruction_following`): `resolve_checks` on all constraints at conversion (all 47 ids resolve); `SEMANTIC_INSTRUCTION_CONSTRAINTS` go to the judge; judge model `GLM_MODEL`, rubric checklist (judge not in this case).
- NLTK: `word_tokenize` and `count_sentences` (`nltk:tokenizers/punkt/english.pickle`, served from `punkt_tab` by nltk 3.10.3) both load from `deps/nltk_data`; `_ensure_nltk_data` downloads `punkt_tab` from the network when it is missing (an unpinned fallback; offline here it is found locally).

## Step 3 entry: contract v2 (2026-11-12 11:42:57 UTC)

`audit/CONTRACTS.md` v2, sha256 `309bb967c3b5c049e7a324ec66ccfe43390ab197811b0747b66079c178ff799e` (frozen `audit/frozen/CONTRACTS_v2.md`). Changes, each marked [v2] in the file:

1. G6: punctuation attached to a word is not part of it (it never was under G3; v1 had folded it into D-first-last-markup, which now covers only markdown markup and quotes). Reason: `Development,` has the first word `Development` under every reading; v1's table wrongly made that a decision.
2. D-postscript-marker split into D-postscript-case and D-postscript-dot. Reason: two independent questions; where the prompt shows the marker without its dot (147 rows) the dot is optional under every reading.
3. New D-end-case. Reason: v1 required exact case without a decision entry; a careful reader could defend case-insensitive matching (for example when another constraint of the row requires lowercase).
4. New D-start-end-single. Reason: v1 did not say whether a one-word response starts and ends with the same word.
5. end_checker: the phrase must not be the tail of a longer word (`Many other questions?`). Reason: clarification of "this exact phrase"; no reading accepts a different word.

48 decision entries after v2. These changes were made after reading the grader code; each reason above is from the instruction text, not from a grader's behavior.

## Step 3 entry: contract v3 (2026-11-12 11:48:01 UTC)

`audit/CONTRACTS.md` v3, sha256 `9321fe40c76d3d531b6f4216d63da6b7685b764a325e39808fc3557d77635fca` (frozen `audit/frozen/CONTRACTS_v3.md`). Change: D-keyword-case covers keyword occurrence (`keywords:*`, `copy:repeat_phrase`); the first/last-word checks compare ignoring case under every reading. Reason: a sentence's first word is capitalized by convention, so `Development` is the word `development`; listing case as a decision there made the first fixture of `first_word:first_word_answer` depend on a reading no careful reader holds.

## Step 3. Fixtures and replacement grader (2026-11-12 11:49 UTC)

- 252 fixtures (246 per-check, 6 graded-text extraction), labeled from the contracts alone: `audit/tests/fixture_defs.py` (sha256 `96c5e7df775d11b0505351b9be27ae74b228dd7df93d8b8036993f1f93b518dd`). Each has the decision entries whose other reading flips its label (`deps`); a check (`scripts/run_fixtures.py`) confirms that switching those entries in the replacement flips the label (0 exceptions) and that the replacement passes all 252.
- Fixture ids: instruction family + first 16 hex of sha256 over (id, kwargs, response, extra); records in `audit/fixtures_hand.jsonl` (merged into `audit/fixtures.jsonl`), per-grader verdicts in `audit/out/fixture_results.json`.
- Tests: `audit/tests/test_fixtures.py` runs every fixture on NV (SkyRL default), VS (SkyRL `verifyit_enabled`), VG (task-curation gate) and R (replacement). Wrong current verdicts are `xfail(strict=True)` (`audit/tests/expected_wrong.json`, sha256 `60efbf760a5e068c1db65f00520340ee5d4a64c301d55dc546fca12c1ea4ce0c`). The global RNG is seeded (20261112) before each grader call because NVIDIA's `ParagraphFirstWordCheck` draws from it.
- Classification of a wrong verdict: a decision when switching the fixture's `deps` makes the replacement agree with the grader, otherwise a finding.

| Grader | correct | wrong: finding | wrong: decision | no check (semantic) |
|---|---|---|---|---|
| NV, SkyRL default (NVIDIA checkers) | 176 | 41 | 35 | 0 |
| VS, SkyRL `verifyit_enabled` | 175 | 41 | 36 | 0 |
| VG, task-curation gate (verifyit checks) | 167 | 43 | 22 | 20 |
| R, replacement (proposed readings) | 252 | 0 | 0 | 0 |
| RF, replacement with NVIDIA's side of each decision | 218 | 0 | 34 | 0 |

The fixtures show defects that a grader change can fix, so the audit has a replacement grader: `audit/replacement.py` (sha256 `0b5eb34ba49a3fbd770047175457293d137750558fc2d40ec80c489beadd7661`), one switch per decision entry (48), plus `fixes_only()` (NVIDIA's side of every decision). Harness: `audit/harness.py` (sha256 `8212c7c432abe3863b7adc90084ac14453eb52c3b87ec254924178c21e07a9ac`). Limitation: the replacement's language identification (english_capital/lowercase, response_language) is langdetect (seed 0) on the text without code blocks and URLs, failing a text with no letters; it implements the contract only as well as langdetect identifies languages.

Test run 2026-11-12 11:49 UTC: `770 passed, 20 skipped, 218 xfailed`.

## Step 5 setup: held-out responses (recorded before any panel response is graded)

Held-out set: every panel response whose row uuid has `int(sha256(uuid), 16) % 10 < 3` (about 30% of rows, the same rows in every run file). Any change to the replacement grader prompted by panel responses may look only at the other 70%; panel results are reported on all responses and on the held-out part separately. Script: `audit/scripts/grade_panel.py` (per-response seed for the global RNG: sha256 of `run file/uuid`).

Replacement change 2026-11-12 11:51 UTC (prompted by a panel response in OLMo-2 sample0, a crash, not a verdict): `no_adjacent_consecutive` raised `TypeError` when a word's first letter lowercases to two characters (`İ`); such a letter is now outside a-z, as the contract says. No verdict on any other input changes.

## Step 5 entry: contract v4 and replacement changes prompted by development responses (2026-11-12 11:59 UTC)

Reading NV-vs-replacement disagreements on development (non-held-out) responses only (`scripts/inspect_disagreements.py` skips held-out uuids) showed four places where contract v3 did not decide a case the text leaves open, and two clarifications. `audit/CONTRACTS.md` v4, sha256 `af4ab1bd1ae156921fac3275e6c3e7f161a7fa07d0b881b533c6c3cdc9ecfa14` (frozen `audit/frozen/CONTRACTS_v4.md`):

1. sentence_hyphens: Qwen3-4B-Instruct joins dash-separated clauses without terminal punctuation (`… begin – our therapists offer care – …`); v3's sentence rule saw one sentence and passed it. v4: a dash with whitespace beside it is a connection with spaces (fail under every reading); new D-hyphen-dash (an en/em dash is not a hyphen).
2. New D-two-sep-edge: a `******` after the second response (or before the first).
3. New D-consecutive-script: Russian responses; "the alphabet" for Cyrillic words (v3 limited the check to a-z without a reason in the text).
4. New D-postscript-line: `… - P.P.S Esta información …` at the end of a one-paragraph answer.
5. Clarifications: a postscript marker or section marker may follow an opening quote or bracket (responses wrapped in quotes or brackets by another constraint of the row).

Fixtures added for each (7; 259 in all), all labeled from v4; the replacement passes all 259. The panel was regraded with the revised replacement; results are reported on all responses and on the held-out 30% separately. Tests at 11:59 UTC: `789 passed, 20 skipped, 227 xfailed`.

Replacement change 2026-11-12 12:01 UTC (found while listing content-free results, not from a panel response): `sentence_hyphens` failed a text with no words, while the contract ("every boundary between consecutive sentences is a single `-`") passes it vacuously; the replacement now follows the contract (fails it only under D-hyphens-single's other reading). Fixtures added: `SCHOOL OF REALISM` (english_capital), all-caps words between CJK punctuation (capital_word_frequency), empty sentence_hyphens: 262 fixtures, replacement passes all; tests `796 passed, 20 skipped, 232 xfailed`. The panel is regraded once more with this final replacement (final run started 12:01 UTC).

## Step 4. Reference comparison and stress tests (2026-11-12 12:04 UTC)

- Reference comparison: grader 1 (SkyRL) runs the reference's checkers itself, through `build_instruction` and `final_answer_text`; grader 2 (verifyit gate) is compared with the reference on every fixture (`out/fixture_results.json`) and on the whole panel (step 5). The reference has no tests; verifyit's own tests are not in the case (only `lib/verifyit/src/verifyit/` was copied), so no grader test that encodes a decision can be listed.
- Property tests (`scripts/step4_properties.py`, hypothesis `find`, 400 examples each, derandomized; `out/properties.json`): 12 properties; counterexamples (smallest) for NV/VS on P4 word-count-exact, P7 nth-paragraph first word followed by `:`/`;`, P9 bullets `- word` (palindrome passes), P10 `Peace, …` first word, P11 phrase glued to a word, P16 repeated `.` counted as a repeated word; for VG on P4, P5 Cyrillic word counts, P6 `***` paragraphs, P14 trailing period, P15 center-word variants. The replacement passes all 12.
- Metamorphic P2 (leading `"  \n"` and trailing `"\n\n\n\n"`, which the contract ignores) changes NVIDIA's verdict for 4 fixtures (`sentence_hyphens` ×2, `paragraphs2` ×2); both pipelines strip the graded text first (`final_answer_text`, `_answer_text`), so this has no effect on either reward.
- Fuzzing (`scripts/step4_fuzz_contentfree.py`, 1,507 random texts × 74 constraint settings, seed 20261112; `out/fuzz.json`): NV raises `IndexError` in `last_word:last_word_answer` on every text without a non-space character (340); in the SkyRL session any such error turns the whole row into `INFRA_ERROR` with reward 0.0, it does not stop the run. VS (300 texts): `json_format` raises `ModuleNotFoundError: yaml` on every text (verifyit's JSON-schema grader needs PyYAML, not in this environment's lockfile), `response_language` raises `LangDetectException` on texts without letters (33), `last_word_answer` `IndexError` (23); VS turns each into a `verification_error` with reward 0.0. VG raised nothing (a crash would count as a failed constraint, logged only). The replacement raised nothing.
- Content-free responses on all 11,817 rows (`out/content_free.json`): an empty answer gets NV reward 1.0 on 1,702 rows (14.4%; the contract passes 1,437, 12.2%, rows whose constraints are all prohibitions), and `INFRA_ERROR` on 625 rows (`last_word_answer`). The VG gate passes it on 810 rows. A restatement of the prompt gets NV reward 1.0 on 746 rows (contract: 458): it passes `detectable_format:constrained_response` 100% (the options are in the prompt), `detectable_content:postscript` 77% (`p.s.` anywhere in a line) and `keywords:palindrome` 100% under NV. `"the " * 200` passes NV on 729 rows.
- Score-level transforms: SkyRL's binary all-or-nothing reward (no row sets `fraction`); verifyit gate all-or-nothing before the judge. Checked by the row-level pipeline fixtures.

## Step 5. Panel results (2026-11-12 12:11 UTC)

Stored responses only (no generation): 23,315 responses, 55,783 constraint verdicts, graded by NV, VS, VG, R (replacement sha256 `b3d8afed7188bd1240d29d5cc7641eeaa58ac2b2f2c74ba4ef3af185854cd1ed`, the final version) and RF. Per-response verdicts: `out/panel_A.jsonl` (sha256 `e155e6da64e745d5bf0057d8a5d295a360864a363bcc99e1b2d612d26507eee0`), `out/panel_B.jsonl` (sha256 `56600a47201a79aa4fd268764a33505dac90ca2cd7f6c3cb6f4cb6dd8d892790`); summary `out/panel_summary.json` (sha256 `f73533b644ca6cf13f3ec14e3603eb9c884a5702f749113f9de69b8af44158ed`), `out/panel_analysis.txt`, `scripts/gate_rates.py`.

- NV vs R: 5,329 disagreements (9.6%), 3,067 not explained by a decision (RF agrees with R), 2,262 by a decision.
- False rewards: 1,006 of 6,469 NV reward-1 responses (15.6%) fail the contract under proposed readings; 537 (8.3%) under NVIDIA's readings.
- Score change R − NV (points, 95% paired bootstrap): thinking +10.0 [+8.1, +12.1]; Qwen3 sampled +3.0 [+2.4, +3.6]; greedy +3.6 [+1.7, +5.5]; Qwen2.5 +0.2 [−0.9, +1.2]; OLMo −0.5 [−1.3, +0.4]. Rerun (greedy vs greedy_repeat, 494 of 1,000 responses differ): NV +0.2 [−0.6, +1.0].
- VG vs R: 8,173 of 50,724 deterministic verdicts (16.1%); 3,007 of 10,192 gate passes (29.5%) fail a deterministic constraint under the contract; 1,612 of 13,123 rejections (12.3%) pass all.
- Coverage: NV 1 infra-error row; VS 473 unscored rows (266 yaml, 204 repeat_phrase `None`, 2 language, 1 last word); VG converts all rows, 90.9% of constraints get a deterministic verdict.
- Extraction: 139 of 1,500 thinking responses never close their reasoning (graded as the answer by both pipelines); 24 responses get an empty SkyRL action, NV rewards 9.

## Step 6. Blinded review: NOT RUN (no reviewers in this exercise)

Result that would change the recommendation (recorded 2026-11-12 12:11 UTC, before any review): the replacement passes every fixture (it does, 263/263), scored coverage is complete (it is), and its error rate is lower than NV's, and lower than VG's on the deterministic constraints, with paired 95% intervals that exclude zero. If it is not lower, the recommendation becomes: fix only the findings whose fixtures have no decision dependency and keep NVIDIA's readings. Planned design (not drawn, not frozen): held-out responses only; strata NV≠R (1,662 held-out verdicts, sample all or most), NV=R (about 170 cases with a consensus), VG≠R (2,432 held-out verdicts); include language-identification cases. No sample was drawn, frozen or rendered.

## Step 7. Report (2026-11-12 12:11 UTC)

`audit/AUDIT.md` (sha256 `6194bc0ae2ca7a455cf2b1c3fea0a2f80ba7f0c63ed91b5106c9fd1f7999b71b` at this entry; later edits logged below). Findings: G1–G6 (pipeline and data), F1–F26 (NVIDIA checkers, in NV and VS), V1–V22 (verifyit checks in VG). Decision entries: 52 (CONTRACTS.md v4). Recommendation: fix the graders; step 6 still needed. `scripts/check_report_commands.py` reran every `repro.py` command quoted in AUDIT.md: 70 distinct claims, 0 mismatches. Final fixtures file `audit/fixtures.jsonl` sha256 `5477e5e2c49e3d7f2dd73d0b202e6f88d0617f787811edb726ede1d99e697aff` (462 lines); `tests/fixture_defs.py` `b35f23f6e1181b982ab5851fdead5a405884fb175fccd3df55185d28d60c4c0b`; `tests/expected_wrong.json` `53e330b1bddfd923457898c691b2e0061f39fa0fb630a61483cbeaf02c442931`.

## Report posted (2026-11-12 12:13 UTC)

The step 7 report is `audit/AUDIT.md` (this offline exercise's equivalent of posting it in the issue). Summary of what it lists:

- Findings, pipeline and data: G1 unclosed reasoning graded as the answer (both pipelines); G2 checker exceptions discard the row (NV `INFRA_ERROR`; VS `verification_error`, 473 panel rows unscored); G3 77 unsatisfiable `nth_paragraph_first_word` constraints graded with a random paragraph index; G4 hidden `relation` of `word_count_different_numbers`; G5 PyYAML undeclared for `verifyit_enabled`, NLTK data downloaded at run time; G6 `P.S.` marker shown without its dot in 147 prompts.
- Findings, NVIDIA checkers (NV, VS): F1 repeat_phrase, F2 count_unique, F3 counting_composition, F4 number_placeholders, F5 postscript, F6 bigram_wrapping, F7 constrained_response, F8 json_format NaN, F9 multiple_sections, F10 number_bullet_lists, F11 highlighted sections, F12 sentence_hyphens, F13 square_brackets, F14 first_word_answer/sent, F15 keyword_specific_position, F16 no_adjacent_consecutive, F17 palindrome, F18 start_end, F19 word_once, F20 response_language on text without letters, F21 nth_paragraph first word with `:`, F22 letter_counting ASCII only, F23 end_checker word tail, F24 english_capital langdetect on all caps, F25 capital_word_frequency CJK-glued tokens, F26 whitespace sensitivity (masked by extraction).
- Findings, verifyit checks (VG): V1–V22; six implement a different requirement (V3 repeat_phrase, V5 lowercase_counting, V11 sentence_hyphens, V12 square_brackets, V14 no_adjacent_consecutive, V19 number_paragraphs).
- Decision entries: the 52 entries of CONTRACTS.md v4, with panel counts, for the maintainers.
- Recommendation: fix the graders; pending the step 6 review described above.

Generated fixtures are tests too: `tests/test_generated.py` with `tests/expected_wrong_generated.json` (199 generated fixtures). Test run 12:13 UTC: `1533 passed, 37 skipped, 278 xfailed`.

## Final check (2026-11-12 12:15 UTC)

AUDIT.md edits after the 12:11 entry: wording only (contract-rule references disambiguated, G5 and extraction counts restated, test counts updated). Final `audit/AUDIT.md` sha256 `dce74aeb22ffee5a4f5f6ffe4eca0365b4175b4463a43e11b3635fb15712e748`. Reran: `pytest tests` → `1533 passed, 37 skipped, 278 xfailed`; `scripts/check_report_commands.py` → 71 distinct `repro.py` claims, 0 mismatches; `scripts/verify_pins.py` → all pins match, no `__pycache__` under case/.
