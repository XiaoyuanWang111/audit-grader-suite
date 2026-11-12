# Audit of the RLVR1 instruction-following graders (SkyRL reward and verifyit gate)

This file stands in for the issue that the audit-grader skill keeps its record in.
Entries are appended in order; times are UTC and read from `date -u` in the same step.

## Progress

- [x] Step 1, pin the inputs (records, configuration and lockfiles only): 2026-11-12T09:32Z
- [x] Step 2, contracts: `audit/CONTRACTS.md` hashed 2026-11-12T09:36:16Z before any code was read
- [x] Step 3, fixtures: 251 hand + 7 pipeline fixtures, replacement grader `audit/replacement/contracts_grader.py`
- [x] Step 4, stress tests: 1,259 property, 434 metamorphic, 141 content-free, 89 fuzz fixtures (`audit/stress_tests.py`);
      2,181 fixtures in `audit/fixtures.jsonl`; `audit/tests/test_fixtures.py`: 5,805 passed, 644 xfailed (strict)
- [x] Step 5 grading: `audit/panel_grade.py` graded all 23,315 stored responses (`audit/results/panel_verdicts.jsonl`)
- [x] Step 5 analysis: `audit/panel_analysis.py`, `audit/scripts/extra_measures.py` (`audit/results/`)
- [ ] Step 6, blinded review: NOT RUN in this exercise (no reviewers); gate and design recorded below
- [x] Step 7: `audit/AUDIT.md` written 2026-11-12T10:24Z; `audit/scripts/verify_report.py` reran all 49 verdict
      claims of its findings tables through `audit/repro.py`: 0 problems

Next (if the session continues): improve AUDIT.md; rerun `audit/tests` and `audit/scripts/verify_report.py`
after any change. To rebuild everything: `stress_tests.py all`, `build_fixtures.py`,
`scripts/official_readings.py`, `panel_grade.py`, `panel_analysis.py`, `scripts/extra_measures.py`,
`scripts/build_report.py` (all under `audit/`, run with `.venv/Scripts/python.exe`).

## Step 1. Pinned inputs (2026-11-12T09:32:46Z)

Taken from `case/TASK.md`, `case/SOURCES.md`, `case/panel/CONFIGS.md` and `case/deps/requirements.lock.txt`
(no grader code read yet). `sha256sum -c case/MANIFEST.sha256` passed for all 177 files
(manifest sha256 `bd6c0c9f67db123d21ac7d54b411d70124e0844d9e02c033f11174dd62147a97`).

| Input | Pin |
|---|---|
| Grader A (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files listed in `case/SOURCES.md` with git blobs |
| Checkers run by grader A | NVIDIA `abukharin-nv/verifiable-instructions` `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (blobs in `case/SOURCES.md`) |
| Grader B (task-curation gate) | Marin `af9c678…`, `lib/verifyit/src/verifyit/` and `experiments/post_training/task_curation/datasets/nemotron_ultra/{graders.py,conversation.py}` |
| Reference implementation for grader B | NVIDIA's checkers above (the data's own grader, per `case/TASK.md`) |
| Installed packages | `marin-verifyit` and `verifiable-instructions` installed from git at the two commits; `audit/scripts/pin_inputs.py` found the 69 installed verifyit files and the 5 installed verifiable_instructions files byte-identical to the case copies |
| Python | CPython 3.12.10, `.venv`, 27 packages of `deps/requirements.lock.txt` (sha256 `9e794ccf…caf8`): nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, regex 2026.9.29, numpy 2.5.4, pandas 3.0.6, pyarrow 26.0.0 |
| NLTK data | `punkt_tab` from `punkt_tab.zip` sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`, 77 files hashed in the manifest |
| Dataset | `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` revision `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a…0b1b`; the 11,817 rows with agent `instruction_following_simple_agent` in `case/data/rlvr1_instruction_following.jsonl` sha256 `96144deb…4159` |
| Row hashes | `audit/frozen/row_hashes.tsv` (one line sha256 and one content sha256 per row over uuid, prompt, instruction ids, kwargs and request settings), sha256 `1f099ba9b1f9627f715039227e7823fe1d854ee5f0143f9f9e88d55a9a1591a5` |
| Prompt rendering | one user message (the row's `prompt`), no system message, no tools; each panel model's own chat template at the pinned model revision (`case/panel/CONFIGS.md`) |
| Stored request settings | `request_json`: temperature 1.0, top-p 1.0, no tools, `parallel_tool_calls` false, on every row |
| Panel generation | vLLM 0.11.0, torch 2.8.0, transformers 4.57.1; token limit 2,048 (8,192 for Qwen3-4B-Thinking-2507), `max_model_len` 8,192 / 4,096 (OLMo) / 14,336 (thinking); model revisions in `case/panel/CONFIGS.md` (sha256 `0f48c4c0…af93`) |
| Grading mode | no row sets `grading_mode`, so both pipelines use `binary` |
| Grader B constraint split | `SEMANTIC_INSTRUCTION_CONSTRAINTS` = `count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`, `letters:letter_counting` go to the LLM judge (out of scope); the other 43 ids are gate checks |

Unverified inputs (cannot be fetched offline):

- The SkyRL session configuration of any training run that used this reward (`verifyit_enabled`, default false per `case/TASK.md`). Location: the run's SkyRL config. Verify with the run's stored config (`grep verifyit_enabled <run config>`).
- The training run's generation settings (stop sequences, chat template, reasoning parser, any merge of a reasoning field into the text): no training-run records are in the case. Location: the training run's config and its vLLM server arguments.
- The panel's stop sequences and reasoning parser: `case/panel/CONFIGS.md` gives neither; the generation manifests are not included. The fields `response` and `reasoning_closed` that the generation script derived were removed. Location: `gen/<folder>/<run>.manifest` of the panel's generation run.
- That each git blob in `case/SOURCES.md` is the one at the named commit: needs the network (`git ls-tree -r af9c678 <path>` in a Marin clone, and the same for NVIDIA at `f46a5ac`). Offline, `audit/scripts/check_blobs.py` recomputed the git blob sha1 and size of all 89 listed files: 0 mismatches.

## Step 2. Contract hash (2026-11-12T09:36:16Z)

`audit/CONTRACTS.md` sha256 `d6647369ba928c565b677dd1998eb73b089652ec4ec0a3d8909fb32f28981801`,
recorded at 2026-11-12T09:36:16Z, before any grader code was read. Up to this point the audit
read only `case/TASK.md`, `case/SOURCES.md`, `case/panel/CONFIGS.md`, the lockfile, the data rows
and the skill. It has 40 decision entries (table at the end of the contract file). Later
changes to the contract file are listed below with their reasons.

### Contract changes

(none yet)

## Step 1, continued. Inputs that only the code shows (recorded 2026-11-12T09:39:55Z, after the contract hash)

- Graded-text extraction, grader A: `final_answer_text` (`envs/nemotron_ultra/answer_extraction.py`) removes every
  `<think>…</think>`, `<thinking>…</thinking>` and `<|start_think|>…<|end_think|>` pair, cuts the text after the last
  closing marker, returns `""` when an opening marker is left, then strips whitespace and one trailing `<|eot_id|>`.
  A response with no marker at all is graded whole, so a thinking response whose `<think>` came from the chat
  template and whose reasoning never closed is graded as if the reasoning were the answer.
- Graded-text extraction, grader B: `_answer_text(candidate, True, strip_outer=False)` in `modes/grade_judge.py`,
  the same algorithm (with `strip_reasoning=True` the `strip_outer=False` argument has no effect).
- Grader A wrapper: `grade_instruction_following` drops `None` kwargs, builds each checker with NVIDIA's
  `build_description(**kwargs)` and calls `check_following`; an exception makes that constraint False and is
  recorded in `instruction_errors`; `NemotronTaskSession._advance` then returns reward 0.0 with outcome
  `INFRA_ERROR` for the whole row. `turn.stop_reason` is not used for this agent: a truncated response is graded.
- Grader A language detection: `langdetect` 1.0.9 with `DetectorFactory.seed = 0` set by `_ensure_nltk_data`; a
  `LangDetectException` counts as instruction followed (NVIDIA `ResponseLanguageChecker`,
  `CapitalLettersEnglishChecker`, `LowercaseLettersEnglishChecker`).
- Grader A randomness: NVIDIA's `build_description` draws a random value when a kwarg is missing or out of range;
  `ParagraphFirstWordCheck` redraws `nth_paragraph` from `randint(1, num_paragraphs + 1)` when
  `nth_paragraph > num_paragraphs` (77 constraints in the data). The verdict then depends on Python's global
  random state.
- NLTK data used by grader A: `punkt_tab` (via `nltk.word_tokenize` and `count_sentences`, which asks for
  `tokenizers/punkt/english.pickle`; nltk 3.10.3 serves it from `punkt_tab`). `nltk.data.find` resolves
  `tokenizers/punkt_tab/english/` to `case/deps/nltk_data`. `_ensure_nltk_data` downloads `punkt_tab` from the
  network when it is missing, and NLTK data has no version.
- Grader B: verifyit's checks in `modes/ifeval.py` are pure standard library (no NLTK, no langdetect).
  `convert_instruction_following` sets `empty_output=EmptyOutputPolicy.GRADE`, so an empty answer is graded by
  the checks; an exception in a check counts as a failed check (`_passes`), and the judge is not called.
- The session's other reward (`grade_nemotron_instructions`, used when `verifyit_enabled`) runs NVIDIA's checkers
  except four replaced predicates (`language:response_language`, `change_case:english_capital`,
  `change_case:english_lowercase`, `detectable_format:json_format`) and verifyit's checks for `punctuation:*`,
  each call in a subprocess under a 30 s deadline.
- Grading path: `NemotronTaskSession.__init__` raises unless `extra_info.nemotron_ultra.route == "task_session"`,
  and all 11,817 rows store `route: "skyrl_gym"` (env_class `nemotron_ultra`). Which code grades these rows in
  training therefore depends on `skyrl_gym.source_task.session_parameters` or on the `nemotron_ultra` env class,
  neither of which is in the case. Unverified: location Marin `af9c678`
  `vendor/skyrl/skyrl-gym/skyrl_gym/source_task.py` and `envs/nemotron_ultra/env.py`; verify with
  `git show af9c678:vendor/skyrl/skyrl-gym/skyrl_gym/source_task.py | grep -n route`.

### Contract changes (2026-11-12T09:48:23Z)

C1 (D-word clarified), C2 (new D-postscript-case), C3 (new D-start-end-leading), C4 (D-empty clarified),
with reasons, in section 3 of `audit/CONTRACTS.md`. All four came from writing fixtures, before any
fixture was run against a grader. The contract now has 43 decision entries.

### Contract changes (2026-11-12T09:56:48Z)

C5 (new D-start-end-single), C6 (new D-end-phrase-case), C7 (D-empty extended to symbol-only text for the
"every item" checks), C8 (optional space in section markers), with reasons, in section 3 of
`audit/CONTRACTS.md`. All four came from reviewing the fuzz fixtures; no panel verdict had been read.
The contract has 45 decision entries. The replacement also had a bug, fixed at the same time: it counted
an empty bold span `****` as a highlight, which the contract excludes.

Held-out panel responses, frozen before any panel verdict was read (2026-11-12T09:55:15Z):
`audit/frozen/heldout_uuids.txt`, 2,363 of the 11,817 uuids (seed 20261112), sha256
`cafbfb6b8026f80e2568fbca81b165b41b17dffd7f311592795b7446830f3258`. Every panel response to these rows is
held out from replacement-grader development.

### Contract changes prompted by the panel (2026-11-12T10:07:09Z)

C9 to C14, with reasons, in section 3 of `audit/CONTRACTS.md`. They came from reading panel disagreements
(between the graders and the replacement) on responses outside the held-out set, with
`audit/scripts/show_disagreements.py`, which skips held-out uuids. The replacement as it was before them is kept
in `audit/scripts/contracts_grader_before_C9.py.txt`. Because these changes were fitted to panel responses,
the report gives every panel number for the held-out subset as well. The contract now has 48 decision entries
(D-first-last-word split into D-first-last-case and D-first-last-markup; new D-separator-edge,
D-divider-inline).

## Step 6. Not run; decision gate recorded for when it is (2026-11-12T10:17:12Z)

No reviewers are available in this exercise, so no sample was drawn, frozen or rendered, and no error
rate exists. The result that would change the recommendation, recorded before any review:

- The replacement passes every fixture (true now: 2,181 of 2,181), its scored coverage is complete (true
  now: 55,783 of 55,783 panel constraint verdicts), and a blinded review finds its error rate lower than
  grader A's with a paired 95% interval that excludes zero. Without that, the recommendation stays "fix
  the grader" for the defects that fixtures prove, but the replacement must not be adopted as the fix.
- For grader B's gate the same comparison, on its 43 deterministic ids.
- Design for the review when it runs: draw from the held-out uuids (`audit/frozen/heldout_uuids.txt`)
  first; stratify by whether grader A and the replacement disagree on a constraint verdict (panel: 5,290
  disagreements, 50,493 agreements); take all or most disagreements and at least 130 agreements with a
  consensus, so that a zero-error agreement stratum (about 90% of verdicts) bounds that stratum's
  contribution below about 2.5%.

## Artifact hashes (2026-11-12T10:17:12Z)

| File | sha256 |
|---|---|
| `audit/CONTRACTS.md` (with changes C1 to C14) | `f227b19d0b9fdbeee021086cb981e577b9db59c64e6b5e65c56f0d2dce1ceca1` |
| `audit/fixtures.jsonl` (2,181 fixtures) | `145b6fdf97286c1ee4f24d7a4bc39d88e6a764ff496b1be7abe1c035ba187502` |
| `audit/tests/expectations.json` | `7780e345d08b8d0c437a55f58cd3f79f67e071e15cd9a4656910e968d09c64f9` |
| `audit/replacement/contracts_grader.py` | `f20c310ac21d1c5a5e10f66af0fbf2d19bc276b1a8369b0f3c98f45e48a4e0f2` |
| `audit/results/panel_verdicts.jsonl` | `708ff83f0a25d3994973d35920c7c9f9fa168f1eeba04e103aaad267b5dd486b` |
| `audit/results/official_readings.json` | `f332a195ad88a32362d1d448c6ad1d0b2752213b15126714b81a7dcf7aca2709` |
| `audit/frozen/row_hashes.tsv` | `1f099ba9b1f9627f715039227e7823fe1d854ee5f0143f9f9e88d55a9a1591a5` |
| `audit/frozen/heldout_uuids.txt` | `cafbfb6b8026f80e2568fbca81b165b41b17dffd7f311592795b7446830f3258` |

## Step 7. Report (2026-11-12T10:24:15Z)

`audit/AUDIT.md`, sha256 `29bf8473a1a7cebc035af0f1227f268892a79e6560ec624da128eff9f6260d21` as of 2026-11-12T10:26:15Z (built from
`audit/scripts/AUDIT_src.md` by `audit/scripts/build_report.py`). Error rate: not estimated (step 6 not run).
Disagreement with the replacement on the panel: grader A 5,290 of 55,783 constraint verdicts (3,526 with no
reading that explains them), grader B 7,921 of 50,724 (6,738). Recommendation: fix both graders and the data;
the replacement needs step 6 before it can serve as the fix.

Findings (details, counterexamples and commands in `audit/AUDIT.md` section 3):

- Grader A (NVIDIA checkers through SkyRL): F-A1 `word_once` exact-one count; F-A2 hidden relation in
  `word_count_different_numbers`; F-A3 `repeat_phrase` last-match bug and case; F-A4 `count_unique` counts
  punctuation; F-A5 `counting_composition` wrong divider; F-A6 unanchored postscript; F-A7 `bigram_wrapping`
  pair check; F-A8 two constrained options pass; F-A9 sections "at least" and inline; F-A10 rules and italics
  as bullets; F-A11 spaced asterisks as highlights; F-A12 `sentence_hyphens`; F-A13 square brackets and
  punctuation; F-A14 first word with attached punctuation; F-A15 keyword position case and commas; F-A16
  digits and markup in `no_adjacent_consecutive`; F-A17 palindrome case and symbols; F-A18 random redraw of
  `nth_paragraph`; F-A19 `***` inside other asterisk runs; F-A20 seven asterisks; F-A21 language exception
  counts as followed; F-A22 `IndexError` on empty text; F-A23 ASCII lowercase runs; F-A24 underscore boundary.
- Grader B (verifyit gate): G-1 to G-19, among them G-3 (inverted `lowercase_counting`), G-4
  (`no_adjacent_consecutive` checks duplicates), G-5 (`square_brackets` checks any span), G-6
  (`repeat_phrase` counts verbatim copies), G-7/G-8 (paragraph checks), G-10 (no English check).
- Pipeline, data, protocol: P1 `<think>` inside an answer empties it (both graders); P2 unclosed reasoning
  graded as the answer; P3 content-free rewards (empty answer: reward 1 on 1,702 rows under A); P4 hidden
  relation in the data; P5 unsatisfiable rows; P6 NLTK data downloaded unpinned; P7 grading path unverified.

Decision entries: 48, listed with both readings, examples and each grader's readings in `audit/AUDIT.md`
section 4 (generated from `audit/CONTRACTS.md` and `audit/results/official_readings.json`).

### Final checks (2026-11-12T10:26:15Z)

`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests`: 5,805 passed, 644 xfailed.
`audit/scripts/verify_report.py`: 49 verdict claims of `audit/AUDIT.md` reproduced by `audit/repro.py`, 0 problems.
`sha256sum -c case/MANIFEST.sha256`: all 177 files unchanged; no `__pycache__` under `case/` or `skill/`.
