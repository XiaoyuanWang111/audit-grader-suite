# Audit of the RLVR1 instruction-following graders (offline issue record)

This file stands in for the issue tracker. Entries are added in order; times are UTC.

## Progress

- [x] Step 1, pin the inputs (records, configuration, lockfiles): 2026-11-11 11:26Z.
- [x] Step 2, contracts written and hashed before any grader code was read: 2026-11-11 11:28Z.
- [x] Step 1 addendum: extraction rules and dependencies that only the code shows (2026-11-11 11:43Z, below).
- [x] Step 3, fixtures: `audit/tests/` (203 fixtures x 3 graders + 7 pipeline tests; at 12:03Z 484 pass, 121 strict xfail), replacement grader `audit/replacement.py` (passes all 203).
- [x] Step 4, reference comparison, metamorphic edits, fuzzing, content-free responses: `audit/scripts/step4.py`, `audit/out/step4.json` (11:59Z).
- [x] Step 5, panel (stored responses only): final grading 11:59Z, `audit/out/panel/`, `audit/out/panel_summary.json`.
- [ ] Step 6, blinded review: NOT RUN in this exercise (no reviewers). No sample drawn or frozen. AUDIT.md section 9 says what it needs.
- [x] Step 7, report `audit/AUDIT.md` (12:00Z, revised 12:03Z). Every `repro.py` command rechecked at 12:03Z (`audit/out/repro_all.txt`).

Next (if the work continues): record the step-6 threshold below, draw the held-out review sample, freeze it, run two blinded reviewers; extend the replacement's language checks; send findings and decision entries to the maintainers.

How to resume: every script is under `audit/scripts/`, run from `case/` with `NLTK_DATA` and `PYTHONDONTWRITEBYTECODE=1` set (see `case/TASK.md`). Tests: `../.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q ../audit/tests`.

## Step 1. Pinned inputs (from records, configuration and lockfiles)

| Input | Value | How verified |
|---|---|---|
| Grader 1 (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files listed in `case/SOURCES.md` with git blobs | `case/MANIFEST.sha256` checked with `sha256sum -c`: all 176 entries OK |
| Checkers run by grader 1, and reference implementation | NVIDIA `verifiable-instructions` at `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (no tests) | installed copy in `.venv/Lib/site-packages/verifiable_instructions` is byte-identical to `case/reference/verifiable-instructions/verifiable_instructions` (`diff -r`) |
| Grader 2 (task-curation gate) | Marin `af9c678...`: `experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` (blob `b8a1271f`), verifyit `lib/verifyit/src/verifyit/` | installed `.venv/Lib/site-packages/verifyit` byte-identical to `case/grader/verifyit` (`diff -r`) |
| Data | HF `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` @ `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a...0b1b`; the 11,817 rows with agent `instruction_following_simple_agent`; `case/data/rlvr1_instruction_following.jsonl` sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` | manifest; the parquet itself is not in the case (unverified here; verify with `sha256sum train.parquet` after `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet --revision 600262dd...`) |
| Row hashes | `audit/frozen/row_hashes.tsv` (11,817 rows: line, uuid, sha256 of the JSON line, sha256 of `[uuid, prompt, instruction_id_list, kwargs]`), file sha256 `afee27bd658403e088a53b7cc4287f529e164649a8782673543bc4b540c205ba` | `audit/scripts/row_hashes.py`; uuids are unique |
| Prompt rendering | one user message, no system message; stored request settings temperature 1.0, top-p 1.0, no tools, `parallel_tool_calls` false (`request_json`) | every row checked |
| Constraint parameters | `instruction_id_list` and `kwargs` in `extra_info.nemotron_ultra.record_json`; 28,219 constraints, 47 ids; 1, 2 or 3 constraints per row (501 / 6,230 / 5,086 rows); no row sets `grading_mode` | `audit/scripts/explore_data.py` |
| Reward aggregation | SkyRL: binary (all constraints pass = 1.0); curation: deterministic gate then LLM judge fraction | `case/TASK.md` |
| Grader dependencies | Python 3.12.10; lockfile `case/deps/requirements.lock.txt` (nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, regex 2026.9.29, ...); NLTK `punkt_tab` zip sha256 `e57f6418...0106`, unzipped files in the manifest | manifest, `diff -r` |
| NVIDIA's own dependency pins | `requirements.txt`: `nltk>=3.8`, `langdetect>=1.0.9`, `absl-py>=1.0.0`, `immutabledict>=2.0.0` (lower bounds only) | read |
| Panel generation | vLLM 0.11.0, torch 2.8.0, transformers 4.57.1; model revisions, token limits (2,048; 8,192 thinking) and `max_model_len` in `case/panel/CONFIGS.md`; chat template = each model's at its revision; no reasoning parser: `raw_response` is the generated text | `case/panel/CONFIGS.md`; panel file sha256s in `case/SOURCES.md` and manifest |

Unverified or unpinned (from records):

- U1. Which reward the RL run used: the session config field `verifyit_enabled` (default false) decides between `grade_instruction_following` and `grade_nemotron_instructions`. No run configuration is in the case. Location: the RL job's SkyRL session config.
- U2. The policy's generation settings during RL (output budget, chat template, reasoning parser, whether a reasoning field is merged into the answer): not in the case. Location: the RL job's config and rollout records.
- U3. NLTK data has no version; it is pinned only by the zip hash above. NVIDIA's `requirements.txt` gives lower bounds only, so a fresh install of the checkers can resolve other versions of nltk and langdetect (finding candidate; see step 1 addendum).

Panel records (counted before grading; `audit/scripts/panel_stats.py`, output `audit/scripts/out/panel_stats.txt`):

| Run | Responses | finish `length` | `</think>` present | reasoning unclosed | empty |
|---|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 620 | 0 | 0 (11 contain a literal `<think>` with no close) | 0 |
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 92 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507 greedy_repeat | 1,000 | 81 | 0 | 0 | 0 |
| Qwen2.5-7B-Instruct sample0 | 4,000 | 65 | 0 | 0 (3 contain a literal `<think>`) | 0 |
| OLMo-2-1124-7B-Instruct sample0 | 3,998 | 39 | 0 | 0 | 1 |
| Qwen3-4B-Thinking-2507 sample0 (thinking) | 1,500 | 166 | 1,361 | 139 (all `length`) | 0 |

## Step 2. Contract

- File: `audit/CONTRACTS.md`, sha256 `c76b255f1448fde4bc386673ecf59de87f927678d7a8cd7d845e68f9836ef14a`, recorded 2026-11-11T11:28:31Z, before any grader or checker code was opened. Frozen copy: `audit/frozen/CONTRACTS_v1_2026-11-11T1128Z.md` (same sha256).
- Up to this point only the data, the panel records, `case/TASK.md`, `case/SOURCES.md`, `case/panel/CONFIGS.md`, the lockfile and NVIDIA's `requirements.txt` had been read.
- The contract has 36 decision entries (`D-...`), listed at its end.

Contract changes after this point are listed here with their reason.

- 2026-11-11T11:37Z, after reading the grader code: six changes, listed with reasons in `audit/CONTRACTS.md`, section "Changes after v1" (new D-postscript-case and D-lowercase-total; D-end-phrase and D-sections split into one entry per question; D-paragraph-separator extended to whitespace-only lines; nth_paragraph > num_paragraphs made explicit). Contract file sha256 after the change: `13a7cd220325f351e20693859d4db216e2388434b61672e47b2f40bf320d9e0d`.

## Step 1 addendum (pinned after the contract hash; only the code shows these)

- SkyRL extraction: `final_answer_text` (answer_extraction.py, blob `7e88cf74`): removes closed `<think>...</think>`, `<thinking>...</thinking>`, `<|start_think|>...<|end_think|>` blocks, keeps the text after the last closing marker, returns `""` if an opening marker remains, strips whitespace and a trailing `<|eot_id|>`. A response that has no marker at all is returned whole. The session ignores `stop_reason` for this agent.
- Curation extraction: `grade_judge._answer_text(candidate, True, strip_outer=False)`, the same algorithm; `empty_output=EmptyOutputPolicy.GRADE`, so empty text is graded.
- SkyRL error policy: a checker exception sets `instruction_errors`; `NemotronTaskSession._advance` then returns `Outcome.INFRA_ERROR` with reward 0.0 for the whole row. Curation: `grade_judge._passes` counts an exception as a failed check.
- SkyRL randomness: `build_description` draws from Python's global `random` when a kwarg is missing or out of range (`nth_paragraph > num_paragraphs` in 77 constraints); `build_instruction` repairs only a missing `nth_paragraph`.
- langdetect: `_ensure_nltk_data` sets `DetectorFactory.seed = 0` before every grading call (deterministic).
- NLTK: NVIDIA's `count_sentences` loads `tokenizers/punkt/english.pickle`; nltk 3.10.3 redirects that to `punkt_tab` (`nltk/data.py`, `switch_punkt`). `_ensure_nltk_data` downloads `punkt_tab` from the network at grading time when it is missing, with no hash check. With nltk < 3.8.2 (allowed by NVIDIA's `nltk>=3.8`) the pickle itself is needed and nothing installs it.
- Audit harness: `audit/harness.py` loads `final_answer_text` and `_answer_text` from their source files with `ast` (unchanged code) because their modules import packages that are not installed; it restricts `nltk.data.path` to `case/deps/nltk_data`.

## Decision entries

See `audit/CONTRACTS.md`, section "Decision entries" (36 in v1, 41 after the changes). Evidence per entry is in the report.

## Fixtures and frozen files

| File | sha256 | Content |
|---|---|---|
| `audit/frozen/row_hashes.tsv` | `afee27bd658403e088a53b7cc4287f529e164649a8782673543bc4b540c205ba` | one hash per data row |
| `audit/frozen/CONTRACTS_v1_2026-11-11T1128Z.md` | `c76b255f1448fde4bc386673ecf59de87f927678d7a8cd7d845e68f9836ef14a` | contract before code was read |
| `audit/tests/fixtures_data.py` (11:43Z) | `0ecef7ff3cd8d69b879d617b7ca1aed365f99a755ae36f81dcbac092aad17552` | 194 fixtures |
| `audit/tests/known_wrong.py` (11:43Z) | `e61c4effa2294b35eb19b435aa796ab72f923775febc757b72c293644d66dc55` | the strict-xfail map |

## Findings

Ids: N = NVIDIA checker (SkyRL reward; NVIDIA is also the reference), V = verifyit check (curation gate), B = both, P = pipeline or data. Full list with counterexamples in `audit/AUDIT.md`.

- 11:43Z, from fixtures and code: N1-N17, V1-V15, B1-B6, P1-P4 (see AUDIT.md). Shares come from step 5.

## Step 5 record

- 2026-11-11T11:44:47Z: panel graded (`audit/scripts/grade_panel.py`, 23,315 responses, 0 crashes) with replacement.py sha256 `3c69e899...5a`. The first run crashed on one OLMo response in the replacement's `no_adjacent_consecutive` (`"İ".lower()` is two characters); fixed before any verdict was looked at.
- Held-out split, recorded before any panel verdict was inspected: development = the four Qwen3-4B runs (Instruct sample0, greedy, greedy_repeat; Thinking sample0); held out = Qwen2.5-7B-Instruct sample0 and OLMo-2-1124-7B-Instruct sample0 (the same 4,000 rows). Replacement changes prompted by panel disagreements are made only from development responses, and the held-out runs are regraded after each change.
- Verdict files (first complete run, 11:44Z): sha256 Qwen2.5 `0bfe5647...4d10`, Qwen3 greedy `17eb87ff...c55f`, greedy_repeat `c4e57093...8765`, Qwen3 sample0 `bda28c48...3e08`, Thinking `7a327d6d...14f2`, OLMo `43736c0d...b548`.

## Later record entries

- 2026-11-11T11:49Z: replacement changes prompted by development-set disagreements (contract changes 7-11): CJK sentence ends, spaced hyphens in sentence_hyphens, seven-letter minimum for phrase palindromes, internal periods inside words, D-alphabet. Held-out runs regraded after the change.
- Between 2026-11-11T11:51Z and 11:54Z (no clock read at the edit; bounded by the two regrades): replacement changes prompted by step-4 metamorphic tests (not by panel verdicts): HTML tags are markup, not words; markup around a section splitter word.
- 2026-11-11T11:59Z: contract change 12 (D-postscript-line), prompted by development-set postscript disagreements; panel regraded; fixtures now 203 (new: B7 empty postscript, D-postscript-line, CJK sentences, non-Latin words, `- ` bullet before the first word, phrase palindromes, D-alphabet, spaced hyphens).
- Final files (12:03Z): `CONTRACTS.md` `092c84e8c93815c210b5130c3dfc8371634a21ac3d5fb83a15da0ca2952fa6f0`; `replacement.py` `3e2d4f95e5a85ae34732dbde4380af29766771d3d8e6eb8c30f7d180e13940d1`; `harness.py` `c8d2f8cbe279671dba555540a68ff1c03cd1f496ef3d9993a184e01df0e672f0`; `tests/fixtures_data.py` `abb8b855516f8804f26b6a9fe4de7abd55ccb85f504a336fa18e3def41cf6ddd`; `tests/known_wrong.py` `e37ebc6a2efccdadcd24a2c66688a0cff619e0a73efd95d315c58fd69e5e3d12`; `out/panel_summary.json` `8bd259804f5ae606bc1727cb47b77027734c52381fe18c23248f4d43a315f509`; `out/step4.json` `4c238802271075c6f28a2c9a3dd604b14ad3001d282dd3d7bb13aeab9ca25275`.
- Final panel verdict files (11:59Z): `Qwen__Qwen2.5-7B-Instruct__sample0.jsonl` `634a3859af4723c8b836d60ade02011beb968112a813d2011f6f020659502b5d`; `Qwen__Qwen3-4B-Instruct-2507__greedy.jsonl` `431b956f02302d29b60beff90a0793f48f1cab1e37af6c899fa04eb05c9b4bd1`; `Qwen__Qwen3-4B-Instruct-2507__greedy_repeat.jsonl` `c2e697f4cecfb0ac3578706fbed24b1b9bbfda071a33815f19182a336439012b`; `Qwen__Qwen3-4B-Instruct-2507__sample0.jsonl` `11a0177b95621b35c8a6bf618270b28447c7e1e05cab2378f93debba858a36e9`; `Qwen__Qwen3-4B-Thinking-2507__thinking__sample0.jsonl` `8e7b10a75283e0e8c06fddfaf4e2e0ce43f6aeaf40fd0bce41cb8ba34a08ed7c`; `allenai__OLMo-2-1124-7B-Instruct__sample0.jsonl` `7fe8f2010efa40b2f90a59274c475d8338bb6cebd991b3b102d9a923017097bd`.
- Case integrity at 12:03Z: `case/MANIFEST.sha256` all OK; installed verifyit and verifiable_instructions still byte-identical to the case copies; no `__pycache__` under `case/`.

## Findings (final list; details, counterexamples and shares in AUDIT.md section 5)

- SkyRL / NVIDIA: N1 repeat_phrase, N2 count_unique tokens, N3 counting_composition, N4 postscript anywhere / P.P.S, N5 two options, N6 sections >=, N7 bullet false positives, N8 double-counted bold, N9 hyphenated words, N10 bracket punctuation, N11 first/last word with attached punctuation or markup, N12 punctuation tokens as words, N13 digits and quotes in no_adjacent, N14 palindrome tokens, N15 langdetect (all-caps misdetection, exception = pass), N16 IndexError on empty answer, N17 random nth_paragraph re-draw, N18 CJK sentence ends.
- Both: B1 word_once exactly once, B2 hidden "less than" relation, B3 seven asterisks, B4 empty brackets, B5 NaN JSON, B6 `* * *` as bullet, B7 bare postscript marker.
- Curation / verifyit: V1 no English check, V2 repeat_phrase counts unchanged copies, V3 counting_composition approximation, V4 lowercase_counting inverted, V5 markup before P.S., V6 upper-case JSON fence, V7 mid-line section mentions, V8 divider as highlight, V9 sentence_hyphens semantics, V10 any bracket passes, V11 adjacent duplicates instead of consecutive letters, V12 trailing punctuation in start_end, V13 number_paragraphs ignores ***, V14 paragraphs >= 2 with either separator, V15 single quotes, V16 ASCII-only words and `-` as a word, V17 phrase palindromes, V18 CJK sentence ends.
- Pipeline / data: P1 truncated reasoning graded as the answer, P2 unclosed `<think>` graded as empty text, P3 one exception voids the SkyRL row, P4 unpinned NLTK data and versions, P5 hidden relation and infeasible nth_paragraph rows.

## Step 6 (not run)

The result that would change the recommendation, proposed for the record before any review: the replacement passes every fixture, its scored coverage is complete, and its error rate on the held-out sample is lower than each grader's with a paired 95% interval that excludes zero. If that fails for a grader, the recommendation for that grader is reconsidered.
