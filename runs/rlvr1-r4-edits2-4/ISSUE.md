# Audit issue: RLVR1 instruction-following graders (SkyRL reward and task-curation gate)

This file stands in for the issue tracker. Entries are appended in order; times are UTC.

## Progress

- [x] Step 1 (part 1): inputs pinned from the case manifest, run records, configuration and lockfile (below).
- [x] Step 2: contracts written from the prompt text only; hash and time recorded below (2026-11-12T10:30:49Z), before any grader code was read.
- [x] Step 1 (part 2): extraction rule and dependencies that only the code shows (below).
- [x] Step 3: 214 hand-written fixtures (`audit/lib/fixtures_src.py`); replacement grader `audit/lib/contract_grader.py` (v3, one switch per decision entry); harness `audit/lib/harness.py`; `audit/fixtures.jsonl` (853 lines) and `audit/tests/` (2,886 pass, 77 skip, 450 strict xfail).
- [x] Step 4: reference comparison, metamorphic tests (46 checks, 375 edits), fuzzing (1,000 per check), content-free responses on all rows.
- [x] Step 5: panel graded (stored responses only), analysis in `audit/work/`.
- [ ] Step 6: not run in this exercise (no reviewers); criterion recorded below.
- [x] Step 7: `audit/AUDIT.md` written 2026-11-12T11:11Z, numbers verified 11:15Z.

Next (if work continues): step 6 on the held-out runs; inspect the gate `postscript` false passes and the weak replacement cells listed in AUDIT.md section 5.

Rerun everything from `audit/` (each script prints or writes its result): `scripts/run_fixtures.py`, `scripts/run_metamorphic.py`, `scripts/run_content_free.py`, `scripts/run_fuzz.py`, `scripts/run_panel.py`, `scripts/analyze_panel.py`, `scripts/run_fixes_only.py`, `scripts/report_stats.py`, `scripts/build_fixtures.py`, then `-m pytest -p no:cacheprovider -q tests` and `repro.py all`. Set `NLTK_DATA` and `PYTHONDONTWRITEBYTECODE=1` as in case/TASK.md.

## Step 1. Pinned inputs (from records, configuration and lockfiles)

Recorded 2026-11-12T10:25:49Z (clock read before writing). Every file listed in
`case/MANIFEST.sha256` (176 files) matched its sha256 (`sha256sum -c`, no failures).

| Input | Pin |
|---|---|
| Grader under audit 1 (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files in `case/reference/skyrl_gym/` (blobs in `case/SOURCES.md`) |
| Checkers run by grader 1, and reference implementation for grader 2 | github.com/abukharin-nv/verifiable-instructions `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (installed from git, byte-identical to `case/reference/verifiable-instructions/`) |
| Grader under audit 2 (task-curation gate) | Marin `af9c6789…`, `lib/verifyit/src/verifyit/` (installed as `marin-verifyit` from git) and `experiments/post_training/task_curation/datasets/nemotron_ultra/graders.py` |
| Data | open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 @ `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a…0b1b`; extracted rows `case/data/rlvr1_instruction_following.jsonl` sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` (11,817 rows, 28,219 constraints, 47 ids) |
| Row hashes | `audit/work/row_hashes.tsv` (one sha256 per row over uuid, prompt messages, instruction ids, kwargs, request_json; file sha256 `5e91ee6a06100b6c67d7cb1a605141abb34ac019ed20e9e3c83d6dd4d65959fe`); row 0 `3dcf41b6-…` = `6846d0783927…` |
| Prompt rendering | one user message per row, no system message (all 11,817 rows); request settings temperature 1.0, top-p 1.0, no tools; each panel model's chat template at the model revision in `case/panel/CONFIGS.md` |
| Generation (panel) | vLLM 0.11.0, torch 2.8.0+cu128, transformers 4.57.1; token limit 2,048 (8,192 for the thinking model), `max_model_len` per CONFIGS.md; thinking on only for Qwen3-4B-Thinking-2507 |
| Python environment | CPython 3.12.10, 27 packages in `case/deps/requirements.lock.txt` (sha256 `9e794ccf…af5b93`), among them nltk 3.10.3, langdetect 1.0.9, immutabledict 4.3.1, absl-py 2.5.0 |
| NLTK data | `punkt_tab` zip sha256 `e57f6418…0106`, unzipped to `case/deps/nltk_data/` (77 files, each in the manifest) |
| Panel files | sha256 per file in `case/SOURCES.md`, all verified via the manifest; line counts 4,000 / 1,000 / 1,000 / 11,817 / 1,500 / 3,998 |

Unpinned or unverified (to be completed after the code is read):
- The SkyRL session config value `verifyit_enabled` used by the training run: not in any record here (default false per `case/TASK.md`). Location: the training run's SkyRL config; verify by reading the run's config file.
- The panel's `response` and `reasoning_closed` fields were removed from the case files (`case/SOURCES.md`); the extraction rule must be applied again from `raw_response`.

## Step 2. Contract file

- File: `audit/CONTRACTS.md`
- sha256: `cbbfdcae127b0e367ed56d591fcbf747ddd1a872b9650a3154f33e6261c7cf66`
- Time: 2026-11-12T10:30:49Z (clock read in the same step as the hash)
- Read before writing it: `case/TASK.md`, `case/SOURCES.md`, `case/panel/CONFIGS.md`, `case/deps/requirements.lock.txt`, `case/MANIFEST.sha256`, and the prompts (instruction templates and kwargs, `audit/work/instruction_texts.json`, sha256 `71898777…9e53`). No grader or checker code had been opened.
- Decision entries proposed in it: 39 (table in section 2 of the contract file); one (`D-word-cjk`) has no proposal.

Later contract changes and decision entries are appended below with their reasons.

## Step 1 (part 2). Inputs that only the code shows

Recorded 2026-11-12T10:46:43Z, after the contract hash above.

- Graded-text extraction, SkyRL: `final_answer_text` (`answer_extraction.py`, blob `7e88cf74…`): removes complete `<think>…</think>`, `<thinking>…</thinking>`, `<|start_think|>…<|end_think|>` blocks, keeps the text after the last closing marker, returns "" if an opening marker remains, strips, drops a trailing `<|eot_id|>`. A response with no marker at all is returned whole, so a thinking-mode response whose reasoning never closed (the chat template supplies `<think>`) is graded as if the reasoning were the answer.
- Graded-text extraction, task curation: `grade_judge._answer_text(candidate, True, strip_outer=False)` (`grade_judge.py` sha256 `fcc96631…`), the same algorithm; `EmptyOutputPolicy.GRADE`, so an empty answer is graded, not zeroed.
- SkyRL session: `NemotronTaskSession.__init__` raises `ValueError("Terminal source rows require a portable Harbor task")` unless `extra_info.nemotron_ultra.route == "task_session"`; all 11,817 rows have `route = "skyrl_gym"`. How the training run routes these rows (`skyrl_gym.source_task.session_parameters`, `task_records`) is not in the case: unverified. Verify by reading the run's SkyRL config and `skyrl_gym/source_task.py` at Marin `af9c6789`.
- SkyRL session: any checker exception (`instruction_errors`) turns the row into `Outcome.INFRA_ERROR` "Verifier configuration failed" with reward 0.0. `fold_grades` (not in the case) decides whether such rows train.
- NVIDIA checker randomness: `ParagraphFirstWordCheck.build_description` redraws `nth_paragraph = random.randint(1, num_paragraphs + 1)` when `nth_paragraph > num_paragraphs`; 77 rows have such kwargs (data check `audit/scripts/data_checks.py`). The SkyRL reward does not seed `random` and the rows carry no frozen reference (`instruction_reference_seed` absent), so those verdicts are random.
- NLTK: `instructions_util.count_sentences` loads `nltk:tokenizers/punkt/english.pickle`, which nltk 3.10.3 resolves to `PunktTokenizer("english")` over `punkt_tab` (checked); `word_tokenize` also uses `punkt_tab`. `_ensure_nltk_data` downloads `punkt_tab` at run time when it is missing, so the data is not pinned by the code (finding).
- langdetect 1.0.9 with `DetectorFactory.seed = 0` (set in `_ensure_nltk_data`).
- Task-curation gate: `SEMANTIC_INSTRUCTION_CONSTRAINTS` (graders.py line 217) removes `count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`, `letters:letter_counting` from the gate (687 + 575 + 780 + 497 = 2,539 of 28,219 constraints).
- `verifyit_enabled` (SkyRL config) selects `grade_nemotron_instructions` instead; default false; the run's value is unverified (see part 1).

## Contract changes and new decision entries

Each entry: time, change, reason. Contract file unchanged on disk since its hash; changes live here.

- 2026-11-12T10:46:43Z, new `D-lowercase-scope`: (A, proposed) each lowercase word may appear at most N times; (B) all lowercase words together at most N times. Example "The cat sat on a mat." with N 2: A pass, B fail. Reason: on re-reading after the NVIDIA code (which counts the total), "all lowercase words should appear at most N times" admits the collective reading.
- 2026-11-12T10:46:43Z, new `D-section-label`: (A, proposed) the section label X may be a number, a Roman numeral or a letter; (B) digits only. Example `SECTION A … SECTION B`: A pass, B fail. Reason: the contract allowed "a number or word" without naming the choice.
- 2026-11-12T10:46:43Z, new `D-hyphens-spaces`: (A, proposed) spaces inside a sentence are allowed; (B) no whitespace anywhere. Example `The sun rose.-Birds sang.`: A pass, B fail. Reason: verifyit's docstring reads "no spaces" as covering the words of a sentence; the text says "between them".
- 2026-11-12T10:46:43Z, new `D-letter-script` (letters:letter_counting): (A, proposed) every Unicode letter counts; (B) only Latin letters. Example `你好吗`, at least 3: A pass, B fail.
- 2026-11-12T10:46:43Z, new `D-end-case`: (A, proposed) the end phrase must match case; (B) case-insensitive. Example `any other questions?`: A fail, B pass. Reason: "this exact phrase" with a case-only difference.
- 2026-11-12T10:46:43Z, new `D-start-end-single`: (A, proposed) a one-word response starts and ends with the same word; (B) at least two words. Example `Hello`: A pass, B fail.
- 2026-11-12T10:46:43Z, clarification `keywords:palindrome`: a palindromic word may hold letters or digits (`1991`), since numbers are words under section 0. Reason: the contract said "letters" only by oversight.
- 2026-11-12T10:46:43Z, clarification `D-word-case` scope: it covers every word comparison (count_unique, repeat_phrase, keyword position), not only keywords. Reason: one reading of case for all word comparisons.
- 2026-11-12T10:46:43Z, clarification: HTML tags such as `<b>…</b>` are markup; their names are not words. Reason: needed for the step-4 HTML-tag edit; section 0 lists `<` and `>` as markup.

- 2026-11-12T11:00Z, new `D-consecutive-script`: (A, proposed) only Latin letters can be consecutive; (B) letters of any alphabet in code-point order. Example Cyrillic `в г`: A pass, B fail. Reason: the content-free run on a Russian prompt showed NVIDIA reads B; the instruction (in English) does not say which alphabet.
- 2026-11-12T11:12Z, scope of `D-divider-edges` extended to a `******` separator at the start or end of a two-response answer. Reason: all 30 panel passes of `combination:two_responses` that the replacement fails have one (found by inspection; the replacement has no switch for it).

Total decision entries: 46 (39 in the contract file plus the 7 above).

## Replacement grader versions (frozen copies in `audit/frozen/`)

| Version | sha256 | Frozen | Change and reason |
|---|---|---|---|
| v1 | `07d2dc58b3c1b77abf250e1a4f121464295592c463acf018acec19172481f536` | 10:49:17Z | first implementation of the contracts; agreed with all hand-written and metamorphic labels |
| v2 | `32c14abb88eaf712b1753d0198d10a79a95157cee1ed9a256fc27929944b1aaf` | 11:01:48Z | HTML tags removed only for words, case, postscript and section markers (global removal merged code lines into blank-line separators: content-free restatement of a Vue snippet); `p.s`/`p.p.s` abbreviations; `D-consecutive-script` switch. An intermediate copy (`8c918e02…`, 11:00:46Z) was used for one panel pass that was overwritten before any analysis. |
| v3 | `5ea5bebd1ed96e86b3491fdf755eafb3a14234b670276cc13c9e5680034c8be9` | 11:05:49Z | after inspecting Qwen3-4B panel responses: the HTML-tag pattern no longer matches inside `<<word>>`; `D-language-mixed` reading A detects the whole text only (per-sentence detection failed technical lines and Hindi/Nepali); letter counts are literal characters. |

Held-out responses: the Qwen2.5-7B-Instruct and OLMo-2-1124-7B-Instruct runs (7,998 responses) were never inspected; only Qwen3-4B responses were read. AUDIT.md reports v3 numbers for every run and marks the held-out ones.

## Step 6 criterion (recorded before any review; no review was run)

The recommendation (fix both graders) stands unless a blinded review of held-out responses finds that the replacement, at the maintainers' readings, is not more accurate than each grader with a paired 95% interval for the error-rate difference that excludes zero, or that a grader's error-rate upper bound is below 2%.

## Frozen files and outputs (sha256, 2026-11-12T11:15:11Z)

- `audit/fixtures.jsonl` `9986696a7296ba4fd2e615146914c06581d0aff0637e2d0984d0295e1f206089`
- `audit/tests/expected_wrong.json` `2643397db4963bc545e8a9dab45c73368f6c7961981963cd85a25301f3c752c0`
- `audit/tests/test_fixtures.py` `5a24302c3a03d2c16dd77b659a3114defc4a72a6ec4677a8a3b0c961129bd647`
- `audit/repro.py` `c7407d696b0a899edaac458fd517e2c302f6bfaaec12f3b1131a906996eb2fc2`
- `audit/work/panel_verdicts.jsonl` `c5572e788ff5646b89859f183feb09847c1ce8f765535e6f7e756595d2e01da9`
- `audit/work/fixes_only.json` `6673beb4bf9b88c72d1504f7b8f0307f4c09461047c3b911a12b1512289ac400`

## Findings

Recorded 2026-11-12T11:15Z. 48 checker findings (F1 to F48) and 5 pipeline findings (G1 to G5). The full table, with counterexamples, panel shares and reference status, is section 7 of `audit/AUDIT.md`; the register is `audit/lib/findings.py`; `../.venv/Scripts/python.exe repro.py <id>` (from `audit/`) reproduces each.

- SkyRL reward (NVIDIA's checkers; 32 checker findings): F1 F2 F3 F4 F5 F7 F8 F15 F18 F19 F20 F21 F22 F23 F24 F25 F27 F28 F31 F33 F34 F35 F36 F37 F38 F39 F40 F41 F45 F46 F47 F48.
- Task-curation gate (verifyit; 26 checker findings): F2 F3 F6 F9 F10 F11 F12 F13 F14 F16 F17 F20 F22 F23 F25 F26 F27 F29 F30 F31 F32 F33 F42 F43 F44 F48.
- Pipeline: G1 (unclosed reasoning graded as the answer, both), G2 (checker exception becomes INFRA_ERROR, SkyRL), G3 (random paragraph index on 77 unsatisfiable rows, SkyRL), G4 (NLTK data downloaded at run time), G5 (route mismatch, unverified).

Headline panel results (five main runs, 22,315 responses): SkyRL reward 1.0 on 6,178; the fixes-only replacement fails 566 of them (9.2%), the proposed one 938 (15.2%). Fixes-only minus SkyRL score: +5.8 points (Qwen3-4B-Instruct sample0), +8.3 (Qwen3-4B-Thinking), +1.5 and +1.9 (held-out Qwen2.5-7B, OLMo-2); greedy rerun noise +0.2. Error rates are not estimated (step 6 not run).
