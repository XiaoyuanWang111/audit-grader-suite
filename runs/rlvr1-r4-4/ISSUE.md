# Audit record: graders of the RLVR1 instruction-following rows

Offline stand-in for the task's issue (no tracker in this exercise). Entries are appended in
order; times are UTC from `date -u` read in the same step.

## Progress

- [x] Step 1 (part 1): inputs pinned from configuration, lockfiles and stored run records (below).
- [x] Step 2: contracts written before reading grader code; hash and time recorded (below).
- [x] Step 1 (part 2): extraction rule, dependencies and settings that only the code shows (below).
- [x] Step 3: 265 fixtures (`audit/tests/fixtures_data.py`), replacement grader
  (`audit/replacement/contract_grader.py`), tests `audit/tests/test_fixtures.py`,
  `audit/tests/test_pipeline.py` (642 passed, 141 xfailed at 11:10Z).
- [x] Step 5 (grading): `audit/scripts/grade_panel.py` -> `audit/work/panel_verdicts.jsonl`
  (23,315 responses, A, B, R and R's alternative readings). Held-out set frozen first (below).
- [x] Step 5 (analysis): `audit/scripts/analyze_panel.py {all,heldout,dev}` ->
  `audit/work/analyze_*.out`, `audit/work/panel_summary_*.json`; `audit/scripts/row_drivers.py`.
- [x] Step 4 (part): content-free responses (`audit/scripts/content_free.py`).
- [x] Step 4 (properties): 385 metamorphic and forbidden-edit cases
  (`audit/scripts/make_property_cases.py`, `run_property_cases.py`, `audit/tests/test_properties.py`).
- [x] Step 4 (fuzz): `audit/scripts/fuzz.py 2000` (seed 20261112) -> `audit/tests/fuzz_cases.json`
  (35 hand-checked minimal cases of 41), `audit/work/fuzz.out`; new finding F-A27.
- [ ] Step 6: NOT RUN in this exercise (no reviewers); pre-registration recorded below.
- [x] Step 7: `audit/AUDIT.md` first full version 11:08Z.
- [x] Final (11:25Z): `audit/fixtures.jsonl` (830 lines); test suite 1,635 passed, 33 skipped,
  355 xfailed; every command in AUDIT.md rerun and checked (`audit/scripts/check_report.py`:
  50 verdict claims, 0 problems).

Next (outside this exercise): step 6 blinded review per the pre-registration below; the
maintainers' decisions on the 44 entries.

How to rerun (Git Bash): `cd <W>/case; export
NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1
PYTHONIOENCODING=utf-8`, then `../.venv/Scripts/python.exe ../audit/scripts/<script>.py` or
`cd ../audit && ../.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests`.

## 1. Pinned inputs (from configuration, lockfiles, stored records) — 2026-11-12T10:33Z

Case folder `case/` verified with `sha256sum -c MANIFEST.sha256` (all 176 files OK; manifest
sha256 `7211ad395535d3b5f76cb0ae72dfc2eea3901ef7ec7459209611eb95a0cbf6b2`). The installed
`verifyit` and `verifiable_instructions` in `.venv/Lib/site-packages` are identical to
`case/grader/verifyit/` and `case/reference/verifiable-instructions/verifiable_instructions/`
(`diff -rq`, no difference).

| Input | Pin | Source |
|---|---|---|
| Grader A (SkyRL reward) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, `vendor/skyrl/skyrl-gym/skyrl_gym/` files with blobs in `case/SOURCES.md` | SOURCES.md |
| Grader A's checkers | github.com/abukharin-nv/verifiable-instructions `f46a5ac87b1400a4f8973039844b6be9b56e3faf` | SOURCES.md, lockfile |
| Grader B (task-curation deterministic gate) | Marin `af9c678…`, `lib/verifyit/src/verifyit/` (blobs in SOURCES.md), `graders.py` blob `b8a1271f…` | SOURCES.md, lockfile |
| Reference implementation for B | NVIDIA's checkers above (the data's own grader) | TASK.md |
| Data | HF `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` @ `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259a…0b1b`; the 11,817 rows' jsonl sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` | SOURCES.md |
| Per-row hashes | `audit/frozen/row_hashes.tsv` (sha256 over uuid, prompt messages, instruction ids, kwargs), file sha256 `d453f320344e02bd5eb3dbd5ecbd72f68bbb8e1dbdad9d2e342a62819baf0a1f` | `audit/scripts/survey_data.py` |
| Prompt rendering | one user message, no system message, no tools; request settings temperature 1.0, top-p 1.0 (every row's `request_json`) | data |
| Panel generation | vLLM 0.11.0, torch 2.8.0, transformers 4.57.1; per-model HF revisions, token limits (2,048; 8,192 thinking), `max_model_len` in `case/panel/CONFIGS.md`; panel files' sha256 in SOURCES.md | CONFIGS.md |
| Grader dependencies | Python 3.12.10; nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, regex 2026.9.29 (all 27 packages in `case/deps/requirements.lock.txt`); NLTK `punkt_tab` zip sha256 `e57f6418…0106` | lockfile, SOURCES.md |

Unverified (not in any record of this case):
- Stop sequences, chat-template files and the server's reasoning parser of the panel's runs
  (the generation manifests are not included: `case/SOURCES.md`, section Panel). Would be
  verified by the manifests' `stop`/`chat_template`/`reasoning_parser` fields.
- The RL training run's own settings (output budget, reasoning parser, whether reasoning is
  merged into the text, `verifyit_enabled`): no run configuration is in the case. Would be
  verified from the run's SkyRL session config (`verifyit_enabled`, generator `max_tokens`).
- How Marin's runs pin the dataset revision and the NLTK data (only the case copy is pinned
  here). Would be verified in the data-loading step of the RL run configuration.

Stored-record counts (`audit/scripts/panel_survey.py`, counts only): 23,315 responses in 6 run
files. finish_reason `length`: Qwen2.5-7B 65/4,000; Qwen3-4B-Instruct sample0 620/11,817,
greedy 92/1,000, greedy_repeat 81/1,000; OLMo-2-7B 39/3,998 (1 empty response); Qwen3-4B-Thinking
166/1,500, of which 139 never close `</think>` (extraction failures under the contract) and 27
close it. No response has a separate reasoning field; the thinking run's `raw_response` has the
reasoning followed by `</think>` and no opening `<think>` (one response also contains `<think>`).
Non-reasoning runs: `<think>` appears in 3 Qwen2.5 and 11 Qwen3-Instruct responses.

Data observations (`audit/scripts/data_checks.py`): 28,219 constraints, 47 ids; 501 rows have one
constraint, 6,230 two, 5,086 three; no row sets `grading_mode`; no kwargs value is `None` (17 ids
have kwargs `None` as a whole). 77 `length_constraints:nth_paragraph_first_word` rows ask for
paragraph n of fewer than n paragraphs; 28 rows combine `count:count_unique` with a keyword
that must appear 2+ times; 203 `letters:letter_counting` rows ask for fewer than 2 or 3 letters.

## 2. Contract — recorded 2026-11-12T10:33:56Z, before reading any grader code

- File: `audit/CONTRACTS.md`, frozen copy `audit/frozen/CONTRACTS_v1.md`.
- sha256: `df2a8873119f48a1ff1b4b86d79881c63d0adc7a79e5b812f228c7e6684e725f`.
- Read before writing it: `case/TASK.md`, `case/SOURCES.md`, `case/panel/CONFIGS.md`, the lockfile,
  the prompts of the data rows (instruction texts), and panel counts. No file under
  `case/grader/` or `case/reference/` had been opened.

Later contract changes and decision entries are listed below with their reasons.

### Contract change log

Each change was made after reading grader code, so each is marked with its reason. The contract
file's sha256 after changes 1-4 (2026-11-12T10:51:22Z):
`236c74d3fcca712378e2368a6e2b2e0a8c0bbc78cc724a29fce773be2cc01ada`.

1. `D-divider-form` alternative narrowed to "a line that is exactly `***`". Reason: the first
   alternative ("the literal `***` anywhere") would make bold italic `***word***` a paragraph
   divider, which no careful reader would defend; NVIDIA's split on `***` anywhere is then a
   defect (F-A20), not a reading.
2. New `D-lowercase-scope` (each lowercase word at most N times / at most N lowercase words in
   total). Reason: NVIDIA's `LowercaseCountingChecker` counts the total; on rereading
   "all lowercase words should appear at most N times", the total reading is defensible.
3. New `D-start-end-one-word` (a one-word response passes / fails). Reason: NVIDIA's
   `StartEndChecker` needs two tokens; "start and end with the same word" can be read as needing
   two occurrences.
4. `D-think-markup` alternative made precise: an unclosed `<think>` span runs to the end of the
   response. Reason: both pipelines return empty text for a non-reasoning response with an
   unclosed `<think>`; the earlier alternative left unclosed spans undefined.

Changes to the replacement grader that did not change the contract: the "in English" and
language approximations (share of letters in the expected script >= 0.6, then langdetect with
seed 0; an ASCII answer of at most three words counts as English) were tuned on hand-written
fixtures only, before any panel verdict was read.

## 1 (part 2). Inputs that only the code shows — recorded 2026-11-12T10:40Z

- Graded-text extraction, identical in both pipelines: SkyRL `final_answer_text`
  (`answer_extraction.py`) and verifyit `_answer_text(text, strip_reasoning=True)`
  (`modes/grade_judge.py`, called by `grade_judge_candidate` because `graders.py` sets
  `strip_candidate_reasoning_blocks=True`): delete every closed `<think>`, `<thinking>`,
  `<|start_think|>` block; keep the text after the last closing marker; return "" if an opening
  marker is left; strip whitespace and a trailing `<|eot_id|>`. Neither knows whether the chat
  template opened the reasoning, so a response whose reasoning never closes is graded as the
  answer (finding F-G1).
- Grader A per constraint: `build_instruction(id, kwargs without None)` then `check_following`;
  an exception gives verdict False and an `instruction_errors` entry; `NemotronTaskSession._advance`
  then returns reward 0.0 with outcome INFRA_ERROR ("Verifier configuration failed").
- Grader B per constraint: `resolve_checks` + `_passes`; an exception counts as failed, with only a
  log warning (`grade_judge.py` lines 428-434). `EmptyOutputPolicy.GRADE`: empty text is graded.
- langdetect: `DetectorFactory.seed = 0` set by `_ensure_nltk_data` before every row (pinned).
- NLTK: `_ensure_nltk_data` checks `tokenizers/punkt_tab` and calls `nltk.download("punkt_tab")`
  if it is missing (network, no hash: unpinned in Marin's runs). `count_sentences` loads
  `nltk:tokenizers/punkt/english.pickle`, which nltk 3.10.3 serves from `punkt_tab` (checked:
  `count_sentences("One. Two. Three.") == 3`).
- Global `random` state: NVIDIA `ParagraphFirstWordCheck.build_description` redraws
  `nth_paragraph = random.randint(1, num_paragraphs + 1)` when nth_paragraph > num_paragraphs;
  Marin's `build_instruction` only repairs the case where nth_paragraph is None. The verdict of
  the 77 such rows depends on the process's random state (finding F-G2).
- Session route: every row has `extra_info.nemotron_ultra.route == "skyrl_gym"`, but
  `NemotronTaskSession.__init__` raises unless the route is `task_session`; the step that rewrites
  the route is not in the case. Unverified; would be verified in Marin's task lowering
  (`skyrl_gym.source_task.session_parameters`).
- `verifyit_enabled` (default False) switches grader A to `grade_nemotron_instructions`
  (`envs/instruction_verifyit.py`), which reuses NVIDIA's checkers but replaces the language,
  case, JSON and punctuation checks. Not audited here (not one of the two graders in the task);
  which value the RL run used is unverified (see part 1).
- Reference tests: NVIDIA's repository has no tests; verifyit's and SkyRL's tests are not in the
  case. No reference unit tests could be run against the replacement.

## Held-out panel responses — frozen 2026-11-12T10:50:50Z, before any panel verdict was read

`audit/scripts/heldout.py`: a response is held out when
`int(sha256("heldout-v1|<run>|<uuid>")[:8], 16) % 4 == 0`. 5,756 of 23,315 responses;
`audit/frozen/heldout_v1.txt` sha256
`86aaf172764455a9de753839b484de462b1b669998452df8f6abcb691fd9dbc1`. Replacement grader at that
time: `audit/replacement/contract_grader.py` sha256
`8fc643d06e2910f4febdeebe75eb1a3f344cbb2248567d39d7bdd8642283de81`. Any later change to the
replacement prompted by panel disagreements is developed on non-held-out responses only and
logged below.

## Development-phase changes after reading panel verdicts (development responses only) — 2026-11-12T10:52Z to 11:05Z

Every response inspected while making these changes was outside the held-out set
(`audit/scripts/show_cases.py` and `hyphen_breakdown.py` skip held-out responses).

Contract changes (contract sha256 after them, 11:06:37Z:
`22022c1ac340972b378c6e68ff3f8bae7d146a84f37a388001a0258f4424dcba`):

5. `D-divider-form` proposed reading: a `***` or `* * *` that is not markdown emphasis, wherever it
   stands. Reason: development responses put the divider at the end of a paragraph's line
   ("...。***" then a blank line); a careful reader reads it as the divider.
6. `multiple_sections`: a marker may follow an opening quote mark, or follow a sentence's end and
   close its line. Reason: development responses wrapped the whole answer in quotes, or ran
   "SECTION 2" onto the end of the previous sentence before a line break.
7. New `D-consecutive-script` (Latin alphabet only / any alphabet). Reason: NVIDIA compares
   Cyrillic letters; for a Russian answer "the alphabet" can be read as the Cyrillic one.
8. New `D-two-responses-edge` (a leading or trailing `******` fails / is ignored). Reason:
   NVIDIA ignores empty first or last parts; "only responses are separated" allows both readings.
9. Language and "in English": under the proposed reading, a paragraph of ten or more letters
   written mostly in another script fails "entire response". Reason: development responses
   ended with whole paragraphs in Chinese.
10. Clarifications: a lowercase word needs a lowercase letter (caseless scripts are not
    lowercase); `[J][u][s][t]` encloses letters, not a word.

Replacement changes (code only), each found on a development response where the replacement
contradicted its own contract:

- R1 sentence_hyphens: a spaced hyphen or dash (" - ") is a sentence connection with spaces.
- R2 language: per-paragraph script share (change 9).
- R3 lowercase words need a lowercase letter (change 10).
- R4 section markers after a quote mark or at the end of a sentence line (change 6).
- R5 asterisk emphasis may stand inside a word (CommonMark); Chinese `*重点*` was missed.
- R6/R11 square brackets: a one-letter pair touching another one-letter pair encloses a fragment
  of a word (change 10).
- R7 divider detection (change 5). R8 `D-consecutive-script` switch. R9 `D-two-responses-edge`
  switch. R10 any non-letter, non-digit character may follow a postscript marker (fullwidth
  colon "：").

Replacement frozen for the report: `audit/replacement/contract_grader.py` sha256
`ca2516fa43b2b92344099ae7b36655db2ee03d220896e6658653efe7f4a430f4` (11:05:24Z). Panel verdicts
regraded with it: `audit/work/panel_verdicts.jsonl`. Held-out results are reported next to the
whole-panel results in AUDIT.md; they agree within their intervals.

Known limits of the replacement (where step 6 is most needed): sentence_hyphens cannot see a
sentence boundary that has no terminal punctuation; the language and "in English" checks are
approximations (script share plus langdetect); bigram_wrapping and word counts treat a run of
Han characters as one word. AUDIT.md reports every score change with and without
sentence_hyphens, response_language and bigram_wrapping.

## Findings and decisions

The full list, with counterexamples, commands, panel shares and reference status, is in
`audit/AUDIT.md` (sections 3 and 4). Fixture ids per finding: `audit/tests/known_failures.json`.

## Step 6 pre-registration (recorded 2026-11-12T11:11Z; the review itself is not run in this exercise)

Result that would change the recommendation ("fix both graders"): in a blinded review drawn from
the held-out responses (`audit/frozen/heldout_v1.txt`), stratified per grader by whether it
disagrees with the replacement (all or most disagreements sampled, plus about 130 agreements per
grader), the recommendation stands if each grader's error rate exceeds the replacement's with a
paired 95% interval that excludes zero, the replacement passes every fixture (it does: 265 of
265) and scored coverage is complete (it is). If the paired interval includes zero for grader A,
the recommendation for A becomes "admit, after F-G1 to F-G3 are fixed"; grader B's
recommendation does not depend on the review for F-B1 to F-B7, whose counterexamples hold under
every reading.

## Step 7

Report: `audit/AUDIT.md` (first full version 2026-11-12T11:08Z).

### Findings index (details, counterexamples, commands and shares: AUDIT.md section 3)

Pipeline and data: F-G1 unclosed reasoning graded as the answer (both graders); F-G2 grader A's
verdict on the 77 nth > num rows depends on the global random state; F-G3 checker exception
(empty text, `last_word_answer`) voids the row; F-G4 308 impossible rows; F-G5 content-free
responses earn reward (empty text: 1,702 rows under A); F-G6 NLTK data downloaded unpinned.

Grader A (NVIDIA checkers): F-A1 word_once exactly once; F-A2 hidden relation in
word_count_different_numbers; F-A3 first-word checks with attached punctuation/markdown; F-A4
keyword position case and punctuation tokens; F-A5 count_unique counts punctuation; F-A6
counting_composition rejects `* * *`; F-A7 blank placeholders; F-A8 postscript (P.P.S counts as
P.S., P.S: rejected, mid-line markers); F-A9 bigram groups; F-A10 several options; F-A11 sections
>= N, empty, double spaces; F-A12 bullet miscounts; F-A13 arithmetic asterisks; F-A14 hyphens in
sentences; F-A15 brackets with punctuation, letter fragments; F-A16 non-letters in
no_adjacent_consecutive; F-A17 palindrome case/punctuation; F-A18 start_end leading markdown;
F-A19 empty text passes the language check; F-A20 `***word***` splits paragraphs; F-A21
contractions are two words; F-A22 7-asterisk separator; F-A23 repeat_phrase case; F-A24
langdetect on all-caps English; F-A25 lowercase_counting ASCII only; F-A26 letter_counting ASCII
only; F-A27 sentence checks pass a text with no sentence (found by fuzzing).

Grader B (verifyit ifeval): F-B1 no_adjacent_consecutive tests repeated words; F-B2
lowercase_counting inverted; F-B3 repeat_phrase counts unchanged copies; F-B4 square_brackets any
bracket; F-B5 sentence_hyphens wrong property; F-B6 number_paragraphs ignores `***`; F-B7
paragraphs/paragraphs2 accept 2 or more; F-B8 ASCII-only words; F-B9 start_end trailing
punctuation; F-B10 quotation single quotes; F-B11 postscript markdown/`P.S:`; F-B12 markdown
option; F-B13 ```` ```JSON ```` fence; F-B14 section mentions, empty sections; F-B15 `* * *` as a
bullet; F-B16 arithmetic asterisks; F-B17 blank title; F-B18 word_once exactly once; F-B19 hidden
relation; F-B20 counting_composition; F-B21 7-asterisk separator; F-B22 phrase palindromes.

### Decision entries (44; proposals and panel counts: AUDIT.md section 4, CONTRACTS.md)

D-think-markup, D-word, D-keyword-boundary, D-sentence, D-appear-n-times,
D-capital-single-letter, D-english-part, D-repeat-original, D-repeat-center, D-unique-case,
D-divider-form, D-divider-empty, D-lowercase-count, D-lowercase-scope, D-placeholder-kind,
D-postscript-end, D-postscript-case, D-bigram-odd, D-constrained-exact, D-json-toplevel,
D-sections-numbering, D-sections-preamble, D-sections-case, D-bullet-marker, D-bullet-nested,
D-highlight-bold, D-hyphen-dash, D-bracket-group, D-title-position, D-letter-case,
D-consecutive-order, D-palindrome-length, D-language-mixed, D-blank-run, D-letters-unit,
D-comma-chars, D-dot-chars, D-excl-chars, D-end-trailing, D-end-case, D-quote-chars,
D-start-end-one-word, D-consecutive-script, D-two-responses-edge.

### Frozen files and hashes

    df2a8873119f48a1ff1b4b86d79881c63d0adc7a79e5b812f228c7e6684e725f *frozen/CONTRACTS_v1.md
    86aaf172764455a9de753839b484de462b1b669998452df8f6abcb691fd9dbc1 *frozen/heldout_v1.txt
    d453f320344e02bd5eb3dbd5ecbd72f68bbb8e1dbdad9d2e342a62819baf0a1f *frozen/row_hashes.tsv
    22022c1ac340972b378c6e68ff3f8bae7d146a84f37a388001a0258f4424dcba *CONTRACTS.md
    ca2516fa43b2b92344099ae7b36655db2ee03d220896e6658653efe7f4a430f4 *replacement/contract_grader.py
    583568e1fadea71847abdbfa3bca4e9b1640450f1e8d19e21b39015ac862d513 *tests/fixtures_data.py
