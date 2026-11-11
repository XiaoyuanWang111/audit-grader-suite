# Audit: graders of the Nemotron RLVR1 instruction-following rows (offline issue record)

This file stands in for the issue tracker (no tracker in this offline exercise). Entries are
appended in order; times are UTC and were read from the clock (`date -u`) in the same step.

## Progress

- [x] Step 1 (pre-contract part): inputs pinned from the case's records, configuration and lockfile.
- [x] Step 2: contracts (audit/CONTRACTS.md v1), hash recorded 2026-11-11T09:52:20Z before reading grader code.
- [x] Step 1 (post-contract part): extraction rule and dependencies that only the code shows (below).
- [x] Step 3: fixtures (audit/tests/fixtures_data.py, test_fixtures.py, test_pipeline.py; at 10:32Z
      129 fixtures, 262 passed, 126 xfailed); replacement grader audit/lib/contracts_grader.py.
- [x] Step 4: reference comparison (panel), metamorphic edits, fuzzing, content-free responses
      (audit/scripts/stress.py -> audit/results/stress_summary.json, stress_tables.txt).
- [x] Step 5: panel graded (audit/scripts/grade_panel.py -> audit/frozen/panel_verdicts.jsonl.gz;
      analyze_panel.py, analyze_extra.py -> audit/results/).
- [x] Step 6: NOT RUN in this exercise (no reviewers); the pre-review decision rule is recorded below.
- [x] Step 7: audit/AUDIT.md written 10:34Z; tests rerun and every report command checked.

Next (optional improvements): review the 44 residual defect verdicts and the semantic approximations case
by case; step 6 when reviewers are available (rule and strata in the Step 6 entry below).

Layout: audit/lib/pipelines.py runs the two graders as their pipelines do; audit/lib/contracts_grader.py is
the replacement; audit/scripts/ has the analysis scripts; audit/tests/ the fixtures; audit/frozen/ frozen
files (hashes below).

## Step 1. Pinned inputs (2026-11-11T09:50:11Z)

Taken from case/TASK.md, case/SOURCES.md, case/panel/CONFIGS.md, case/deps/requirements.lock.txt and
case/MANIFEST.sha256 only (no grader code read yet).

- Case manifest: `case/MANIFEST.sha256` sha256 `b0a677b8690dfdd2dee18c0e32e9f9d9b0801becdb4e72e0405dc3d03933a12c`;
  `sha256sum -c` on 2026-11-11T09:46Z: every listed file OK (177 entries).
- Grader 1 (SkyRL reward): Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, files under
  `case/reference/skyrl_gym/` with the git blobs listed in `case/SOURCES.md`
  (`instruction_following.py` blob `969e81185985215d885661b58a4c75455e445301`,
  `nemotron_tasks.py` `98a958eb41cb6dde9b2892d6e30a9283397f4511`,
  `answer_extraction.py` `7e88cf74d5013dd85eab460a6bf92f133ad74f43`,
  `aime/utils.py` `6848937295f251e2d7e1888a8680e825d920f575`,
  `instruction_verifyit.py` `6c441f63851ad7d257054e1e9dc1f778314033a6`).
- Checkers that grader 1 runs, and reference implementation for grader 2: NVIDIA
  verifiable-instructions `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (`instructions.py` blob
  `253ec6af3496ffc22ad1a30403566b312033638a`, `instructions_registry.py`
  `bdfe9c097606f4a7ef7649b4c7a09e4d31bf71c5`, `instructions_util.py`
  `60cdc6b1fe6d149825f95ac8b6e9da8a8e7c9cb9`). The repository has no tests.
- Grader 2 (task-curation deterministic gate): Marin `af9c6789...`, verifyit
  (`modes/ifeval.py` blob `575f2a453f75531db3486c0e9b83345dc69ae16e`, `modes/grade_ifeval.py`
  `a2481c0b9f4c168158215f711e12d05c219eb48a`, `modes/grade_judge.py`
  `3cb9b3104c8b5955870ea65d4c653f845e328f12`), and `graders.py` blob
  `b8a1271fcb49cf3aee67805b5d5f475987804bad`.
- Data: huggingface.co/datasets/open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 revision
  `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256
  `fde7259ad17170b6a57292ea85fdd20d9a2428b078cc3aa67cdeab8155fc0b1b` (unverified here: no network; verify
  with `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet
  --repo-type dataset --revision 600262dd... && sha256sum train.parquet`). The case's extract
  `case/data/rlvr1_instruction_following.jsonl` sha256
  `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159` (11,817 rows, 28,219 constraints, 47 ids).
- One hash per row: `audit/frozen/row_hashes.tsv` sha256
  `496221f7ee69c61cb37ed0d58d375be2a7e0925fa7b5f059afa76d96a3463cee` (columns: index, uuid, sha256 of the
  JSON line, sha256 of {uuid, prompt, instruction_id_list, kwargs}; script `audit/scripts/row_hashes.py`).
- Prompt rendering: each row has one user message (`prompt[0].content`, equal to `record_json.prompt` for
  all 11,817 rows) and no system message; `request_json`: temperature 1.0, top-p 1.0, no tools,
  `parallel_tool_calls` false. The chat template is the policy model's (not pinned by the data; the panel's
  models are pinned by revision in `case/panel/CONFIGS.md`).
- Grading settings from the records: no row sets `grading_mode` (binary default per TASK.md); session
  config `verifyit_enabled` default false (TASK.md), so the SkyRL session uses `grade_instruction_following`.
- Panel generation (stored records, `case/panel/CONFIGS.md` sha256
  `0f48c4c0107c757b438964bed933b27176e42dc384c1709f8bd94bad93af5b93`): vLLM 0.11.0, torch 2.8.0+cu128,
  transformers 4.57.1, Python 3.12.3, one GPU; models and revisions:
  Qwen3-4B-Instruct-2507 `cdbee75f...` (sample0 all rows, greedy and greedy_repeat on 1,000 rows),
  Qwen2.5-7B-Instruct `a09a3545...` (sample0, 4,000 rows), OLMo-2-1124-7B-Instruct `470b1fba...`
  (sample0, the same 4,000 rows, 3,998 answered), Qwen3-4B-Thinking-2507 `768f209d...` (sample0, 1,500
  rows, thinking). Token limit 2,048 (8,192 thinking), lowered when the prompt leaves less room.
  Stop sequences and the server's reasoning parser are not recorded in CONFIGS.md (see findings).
  Panel file hashes as in `case/SOURCES.md`:
  - `Qwen__Qwen2.5-7B-Instruct/sample0.jsonl` `0dd1b738749f2a69ecb320629b7becdb048c1ae9a846d21b452a02b8531a1dcc`
  - `Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl` `558f73839c5786146aacf7c0d623178e4b639e82e25a8b675d7d38ce0229bf97`
  - `Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl` `ad0910da8398f7e5c44a32b4ee870db644a136b3130d9854ae24b4d9d91f1a05`
  - `Qwen__Qwen3-4B-Instruct-2507/sample0.jsonl` `b343de37464790d0cd7be7e6441aecf2b645235c54df2f031a9aaa7c4596ef78`
  - `Qwen__Qwen3-4B-Thinking-2507__thinking/sample0.jsonl` `c619fa0bbc2b01c814825976a7d7c3813e80c5dc34852331cc37b555c5eccd7d`
  - `allenai__OLMo-2-1124-7B-Instruct/sample0.jsonl` `bd39b38334cceecb9e0cc274dba6e4c7f40de4c6ee0784bb7ddd6b77c74274f0`
- Grader dependencies (lockfile `case/deps/requirements.lock.txt` sha256
  `9e794ccf8f290b5ec41f1b54f64ebefb097a8980b3eaf015c85156400174caf8`): CPython 3.12.10, nltk 3.10.3,
  langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, regex 2026.9.29, marin-verifyit and
  verifiable-instructions from git at the commits above. NLTK data: `punkt_tab` zip sha256
  `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`, unzipped under
  `case/deps/nltk_data/` (77 files, each in the manifest).
- Unverifiable in this exercise: the upstream repositories and the Hugging Face file (no network). Commands
  that would verify them: `git -C marin rev-parse af9c6789^{tree}` plus `git hash-object` on each file in
  SOURCES.md; the `huggingface-cli` command above.

## Step 2. Contract hash (2026-11-11T09:52:20Z)

`audit/CONTRACTS.md` v1, sha256 `b157ee4011ce0135d08fbe0f34ed4a3a7d2601edca1fed49c187d34a17d056fd`, frozen copy
`audit/frozen/CONTRACTS_v1.md`. Recorded before any grader code (reference/ or grader/ source) was opened.
Later contract changes are logged below as "Contract change" entries with their reason.

Data facts noted while pinning (data only):
- 77 rows ask for paragraph `nth_paragraph` greater than `num_paragraphs` in
  `length_constraints:nth_paragraph_first_word` (for example uuid `35492d20-71a4-4e3c-a92b-cee490cafddf`:
  "There should be 3 paragraphs ... Paragraph 4 must start with word feedback").
- `keywords:word_count_different_numbers` carries a `relation` kwarg (`at least` 320, `less than` 206), but its
  instruction text, "In your response, the word {keyword} should appear {frequency} times.", does not show it.

## Step 1 (post-contract part): pins that only the code shows (2026-11-11T10:06:41Z)

- Graded-text extraction, SkyRL: `final_answer_text` (answer_extraction.py, blob 7e88cf74): removes every
  closed `<think>...</think>` (and two other marker pairs), keeps the text after the last closing marker,
  returns "" when an opening marker is left unclosed, else `strip()` and drop a trailing `<|eot_id|>`. A text
  with no marker at all is returned whole (so a truncated Qwen3-Thinking response, whose `<think>` is in the
  prompt template, is graded as its reasoning).
- Graded-text extraction, task curation: verifyit `_answer_text(text, strip_reasoning=True,
  strip_outer=False)` (grade_judge.py, blob 3cb9b310), the same algorithm; the JudgeSpec sets
  `empty_output=GRADE`, so an empty candidate still runs the gate.
- SkyRL session (nemotron_tasks.py): any checker exception makes the transition `INFRA_ERROR` with reward
  0.0 (not a model failure); `grading_mode` binary; the stop reason is ignored for this agent (a truncated
  response is graded as is). `NemotronTaskSession.__init__` raises "Terminal source rows require a portable
  Harbor task" unless `route == "task_session"`, but all 11,817 rows have `route == "skyrl_gym"` (and
  `env_class == "nemotron_ultra"`). The code that serves route `skyrl_gym` is not in the case: UNVERIFIED
  input. Verify with `git -C marin grep -n "skyrl_gym" af9c6789 -- vendor/skyrl/skyrl-gym`.
- Checker dependencies the code loads: `langdetect` (seeded `DetectorFactory.seed = 0` by
  `_ensure_nltk_data`), `nltk.word_tokenize` and `nltk.data.load("nltk:tokenizers/punkt/english.pickle")`
  (nltk 3.10.3 resolves both to `punkt_tab`), absl logging. `_ensure_nltk_data` downloads `punkt_tab` from
  the network when it is missing (unversioned data; finding G2). NLTK also searches the user's home and
  the venv for data, so `NLTK_DATA` must point at the pinned copy.
- `grade_nemotron_instructions` (verifyit_enabled path, default off) replaces three NVIDIA predicates
  (`language:response_language`, `change_case:english_capital/lowercase`: no LangDetectException fallback)
  and `json_format`; it is not the default reward and is not graded in this audit's panel.
- Check run: `audit/scripts/check_pins.py` at 10:06Z: the 74 installed source files of
  verifiable_instructions and verifyit equal the case copies byte for byte, all 177 manifest entries match,
  punkt_tab resolves to `case/deps/nltk_data`. Rerun after each panel run (logged below).

## Step 3. Fixtures and replacement grader (2026-11-11T10:06:41Z)

- Fixtures: `audit/tests/fixtures_data.py` (sha256 900fdc9d8e0c884b86e8861c008b53f739d6cf33aacd72ebfdf41eb2d94a75c5),
  116 short responses labeled from the contracts; id = check + first 16 hex of sha256 of
  [check, kwargs, response]. Tests: `audit/tests/test_fixtures.py` (30096eae...) runs each fixture on the
  NVIDIA checker (as the SkyRL reward runs it), the verifyit check (as the gate runs it) and the replacement;
  `audit/tests/test_pipeline.py` (7e6b2684...) tests extraction and whole-row rewards. A grader that
  contradicts a label is `xfail(strict=True)`. Run at 10:05Z: 239 passed, 109 xfailed.
- Replacement grader: `audit/lib/contracts_grader.py` (ffcb0687...), one `Readings` switch per decision entry
  (`DECISION_SWITCHES`); it passes every fixture. Built because fixtures show defects a grader change can fix.
- Harness: `audit/lib/pipelines.py` (a84f43ed...) takes `final_answer_text` and `_answer_text` verbatim from
  the case files with `ast` (their modules import packages that are not installed).

### Findings so far (F = checker or pipeline defect; G = data or protocol)

Each has fixtures in fixtures_data.py with the same ref. N = NVIDIA checker / SkyRL reward (also the
reference implementation), V = verifyit gate.
- F01 N,V `keywords:word_count_different_numbers`: graded with the hidden `relation` kwarg; text says "should
  appear {f} times". Exactly f occurrences fail under `less than`; zero occurrences pass.
- F02 N,V `keywords:word_once`: requires exactly one occurrence; text "Include keyword X in your response".
- F03 N `copy:repeat_phrase`: only the last found copy's difference count is checked, so a verbatim copy
  plus one transformed copy passes for small_n=2.
- F04 V `copy:repeat_phrase`: counts verbatim copies (>= small_n); correct transformed copies fail and
  verbatim repeats pass.
- F05 N,V `copy:repeat_phrase`: NVIDIA's regex starts at an earlier occurrence of the first word on the line
  and fails a correct response (V fails it by F04).
- F06 N `detectable_format:constrained_response`: substring test passes a response with two options.
- F07 N `detectable_format:multiple_sections`: tests `>=` num_sections; text "must have N sections".
- F08 V `detectable_format:multiple_sections`: counts mid-line mentions (case-insensitive) as markers.
- F09 V `length_constraints:number_paragraphs`: counts blank-line paragraphs and ignores the `***` divider.
- F10 N,V `length_constraints:number_paragraphs`: NVIDIA splits at `***` inside a line (bold-italic markup).
- F11 V `paragraphs:paragraphs`, `paragraphs:paragraphs2`: pass any 2 or more paragraphs; text says 2.
- F12 N first-word checks (`first_word_answer`, `first_word_sent`, `nth_paragraph_first_word`):
  punctuation right after the word (`Development,`, `Feedback:`) makes the word differ.
- F13 N `keywords:keyword_specific_position`: punctuation tokens count as words.
- F14 N `keywords:palindrome`: a palindrome followed by punctuation is missed; a bullet `-` counts.
- F15 N `keywords:start_end`: compares tokens, so a response starting and ending with `**` passes.
- F16 V `keywords:start_end`: ignores "not even punctuation" after the last word.
- F17 N `keywords:no_adjacent_consecutive`: compares the first character of whitespace tokens, so markup
  or a quotation mark hides the letter.
- F18 V `keywords:no_adjacent_consecutive`: checks adjacent duplicate words, a different requirement.
- F19 N `detectable_format:square_brackets`: punctuation after a bracketed word fails the response.
- F20 V `detectable_format:square_brackets`: passes when any one bracketed span exists.
- F21 N `detectable_format:bigram_wrapping`: punctuation after a group fails; one-word groups pass.
- F22 N `detectable_format:sentence_hyphens`: a hyphenated word inside a sentence fails a correct response.
- F23 V `detectable_format:sentence_hyphens`: passes sentences separated by a space.
- F24 N `count:count_unique`: punctuation tokens count as words, so two commas fail.
- F25 N,V `count:counting_composition` (1 row): NVIDIA splits at `***`, not the instructed `* * *`, and counts
  punctuation tokens as words; verifyit tests `>=` on the first sentences only.
- F26 V `count:lowercase_counting`: inverted: requires at least N lowercase words ("at most N times").
- F27 V `change_case:english_capital/english_lowercase`: no English test (Russian passes).
- F28 V `startend:quotation`: accepts single quotation marks.
- F29 N `detectable_content:postscript`: `P.P.S.` satisfies the `P.S.` marker (unanchored substring).
- F30 N `detectable_format:number_bullet_lists`: a `---` rule and a line starting with an italic span count.
- F31 V `detectable_format:json_format`: an upper-case fence tag (```JSON) fails.
- F32 N,V `detectable_format:json_format`: `NaN`/`Infinity` accepted as JSON.
- F33 N,V empty or whitespace-only `[]`/`[ ]` placeholders (N, V) and `<<   >>` titles (V) count.
- F34 V word-based checks: verifyit's word regex is ASCII-only, so Cyrillic and other scripts have no words.
- F35 V: verifyit splits a word at a typographic apostrophe but not at a straight one (metamorphic).
- F36 N,V `combination:two_responses`: seven asterisks pass as the six-asterisk separator.
- F37 N,V pipeline: unclosed reasoning becomes "", which passes negative checks (reward 1.0 possible).
- F38 N,V pipeline: a truncated response of a model whose template opens `<think>` is graded as its reasoning.
- F39 N pipeline: `last_word_answer` raises IndexError on empty text, so the session reports INFRA_ERROR.
- G1 data: 77 rows ask for paragraph nth > num_paragraphs (unsatisfiable under every reading).
- G2 inputs: NLTK data unversioned and downloaded at run time when missing; panel stop sequences and reasoning
  parser not recorded; the code serving route `skyrl_gym` is not in the case.

### Decision entries exercised by fixtures

D-wcdn-relation, D-constrained-exact, D-section-marker-case, D-markup-around-word, D-palindrome-case,
D-consecutive-order, D-square-brackets-grouping, D-sentence-hyphens-spaces, D-word-case,
D-lowercase-counting-scope, D-allcaps-short-words, D-typographic-quotes, D-postscript-position,
D-postscript-case, D-bullet-markers, D-json-scalar, D-word-apostrophe, D-end-case,
D-end-trailing-nonwords, D-comma-variants, D-dot-variants, D-exclamation-variants, D-keyword-substring,
D-letter-script, D-empty-response. The full table is in audit/CONTRACTS.md.

## Step 5 setup: held-out responses (recorded 2026-11-11T10:08:40Z, before any panel verdict was computed)

Held-out panel responses: int(sha256("<folder>/<run>/<uuid>"), 16) % 5 == 0 (about one in five of each run),
fixed in audit/scripts/grade_panel.py. Any change to the replacement grader prompted by the panel is checked
on the held-out responses only; every change is logged below with its time.

## Contract change C3 and replacement change (2026-11-11T10:18:26Z)

Prompted by panel cases (step 5, after the first panel analysis). Four new decision entries
(D-postscript-line-start, D-section-line-start, D-two-responses-extra-separator, D-sentence-hyphens-dash),
each with a switch in audit/lib/contracts_grader.py, and three clarifications (CJK full stops end sentences,
emphasis after terminal punctuation, quotation marks before a marker); text in audit/CONTRACTS.md section 3.
New fixtures (10:18Z): F40-F43 symptoms and the four entries; F44 in test_pipeline.py. Suite: 257 passed,
122 xfailed. Because these changes were prompted by the panel, the replacement's panel numbers are reported
on all responses and on the held-out responses separately.

## Step 4. Reference comparison and stress tests (2026-11-11T10:24:07Z)

- Reference comparison on the panel's 50,724 gated constraint verdicts: verifyit and NVIDIA disagree on
  7,822 (15.4%). Classified with the replacement under every combination of the relevant decision switches:
  4,710 are verifyit defects (NVIDIA within some reading), 637 are NVIDIA defects (verifyit within some
  reading), 2,475 are decisions. The reference repository has no tests; verifyit's tests are not in the case,
  so no test assertions could be listed.
- Content-free responses on all 11,817 rows (SkyRL reward 1.0 / gate passes / replacement passes):
  empty 1,702 / 810 / 0 (and 625 rows raise IndexError in `last_word:last_word_answer`, an INFRA_ERROR);
  "." 1,144 / 682 / 530; "ok " x200 607 / 1,069 / 562; the row's own prompt 746 / 1,365 / 458.
- Metamorphic edits on panel responses that all graders pass (40 per check): flips where the replacement
  still passes are in audit/results/stress_tables.txt. New symptoms: F45 (verifyit counts a bare hyphen as a
  word), F46 (a numbered label "1." read as a sentence, NVIDIA and verifyit). The rest repeat F12, F17, F19,
  F21, F24 or rest on D-markup-around-word, D-lowercase-counting-scope or D-paragraph-separator-count.
- Fuzzing: 71,379 (check, kwargs, text) cases per grader; exceptions only in NVIDIA
  `last_word:last_word_answer` on empty or whitespace text (IndexError, 15 cases); none in verifyit or the
  replacement (one replacement crash under a non-proposed reading, `"İ".lower()`, fixed before the 10:24Z records; it cannot
  change proposed-reading verdicts).

## Step 5. Panel (2026-11-11T10:24:07Z)

Frozen: `audit/frozen/panel_verdicts.jsonl.gz` sha256
dfd103f29744f13e6e010b21a23df0ad3d83a6fd5d5544cc45152ab8248bb969 (23,315 responses, 55,783 constraint verdicts),
`audit/results/defect_cases.jsonl.gz` d459d908a713c5d3c6298489cb441e1818e1ab45a2998b8144c461be1a5b53b5,
`panel_summary.json` 06f97cfd..., `extra_summary.json` 09f86079..., `stress_summary.json` 8802fb3f...
Replacement at grading time = contracts_grader.py after change C3 (the later `[:1]` fix does not touch the
proposed path). check_pins.py rerun at 10:24Z: OK.

- Stored records: finish_reason `length` on 65 / 92 / 81 / 620 / 166 / 39 responses (Qwen2.5 sample0 /
  Qwen3 greedy / greedy_repeat / Qwen3 sample0 / Qwen3-Thinking / OLMo); 139 of 1,500 Qwen3-Thinking
  responses never close their reasoning (all `length`), and SkyRL grades their reasoning text (F38);
  23 non-reasoning responses leave a literal `<think>` (14) or `<thinking>` (9) unclosed, and SkyRL grades "" for them (F37).
- Constraint verdicts the contract contradicts under every reading (defects): SkyRL 2,253 of 55,783 (4.0%;
  740 false passes, 1,513 false fails); verifyit gate 6,018 of 50,724 (11.9%; 4,286 / 1,732). Decision-only
  disagreements: SkyRL 3,250, verifyit 2,080.
- Prompt-level score change, fixes only (SkyRL / gate), points with 95% bootstrap intervals:
  Qwen2.5 +0.65 [+0.08, +1.30] / -6.05 [-7.10, -5.10]; Qwen3 greedy +2.1 [+0.9, +3.4] / -9.1 [-11.5, -6.9];
  greedy_repeat +2.4 [+1.1, +3.7] / -8.6 [-10.9, -6.4]; Qwen3 sample0 +3.01 [+2.56, +3.44] / -6.46 [-7.21, -5.69];
  Qwen3-Thinking +5.93 [+4.53, +7.40] / +5.07 [+3.33, +6.87]; OLMo +1.05 [+0.53, +1.58] / -7.33 [-8.45, -6.28].
  Rerun (greedy vs greedy_repeat, 506 of 1,000 texts identical): SkyRL 16 prompt verdicts changed, +0.2 points;
  gate 27, +0.1 points.
- False rewards (SkyRL reward 1.0 that the contract contradicts): 343 of 6,471 (5.3%) counting defects only;
  1,059 (16.4%) under the proposed readings. Gate passes contradicted: 2,445 of 10,192 (24.0%) defects only.
- Scored coverage: SkyRL 23,314 of 23,315 responses get a verdict (1 INFRA_ERROR, IndexError on empty text);
  the gate gives a deterministic verdict to 50,724 of 55,783 constraints (90.9%); 166 responses (94 data
  rows) have only judged constraints and pass the gate by default.
- F44 seen in the panel: SkyRL scores of the same responses changed between two grading runs (for example
  Qwen2.5 sample0 20.05% in the first grading run, 19.975% in the second); 161 verdicts on nth > num rows, 12 SkyRL passes.

## Step 6. Not run

No reviewers are available in this exercise, so no sample was drawn, frozen or rendered. Recorded before
any review, as the skill requires: with the replacement, the recommendation to fix would be confirmed if the
replacement passes every fixture (true at 10:23Z), its scored coverage is complete (true: no exception on
the panel), and its error rate on a held-out round is lower than SkyRL's and the gate's with a paired 95%
interval that excludes zero. Stratify by replacement-vs-grader disagreement per grader; the populations
(SkyRL) are 5,503 disagreeing and 50,280 agreeing constraint verdicts.

## Findings update after step 5 (2026-11-11T10:34:55Z)

- New findings from panel cases and stress tests, each with a fixture: F40 (NVIDIA's English test,
  isupper/islower + langdetect on raw text), F41 (whitespace tokens merge words not separated by spaces),
  F42 (sentence split at a period with no following space), F43 (CJK full stop not a sentence end),
  F44 (nth_paragraph > num_paragraphs redrawn at random on each call; test_pipeline.py), F45 (verifyit word
  pattern matches a bare hyphen), F46 (numbered label read as a sentence), F47 (NVIDIA lowercase_counting
  counts only ASCII words).
- F08 withdrawn: its fixture is correct under the other reading of D-section-line-start (added in C3); the
  fixture is now a decision fixture.
- F37 covers `<thinking>` as well as `<think>`: 23 non-reasoning panel responses leave one unclosed (14
  `<think>`, 9 `<thinking>`); SkyRL grades "" for them and gave 8 of them reward 1.0.
- Final fixture set: 129 fixtures (61 finding, 34 decision, 34 control); suite at 10:32Z: 262 passed,
  126 xfailed. Every counterexample row in AUDIT.md was rerun with scripts/repro.py at 10:33Z: 95 rows,
  0 mismatches.
- Note on the frozen panel file: gzip headers carry a timestamp, and the SkyRL verdicts of the 161
  nth > num verdicts are random (F44), so a rerun of grade_panel.py does not reproduce the .gz hash. The
  decompressed content of the file analysed has sha256
  70403305e10a0d91385a0469f4a482070287d8f872aab9e12efc8cd35cf6b028.

## Step 7. Report (2026-11-11T10:34:55Z)

`audit/AUDIT.md` sha256 24c7cd3c64327788b5611b22fe95910aa1a623ccc20fb8c13fd81fb4041a1d85 (after a final note on rerun reproducibility, section 9). Final file hashes:
CONTRACTS.md 3516d83a..., lib/contracts_grader.py b789bb37..., lib/pipelines.py a84f43ed...,
tests/fixtures_data.py f1494c4d..., tests/test_fixtures.py 30096eae..., tests/test_pipeline.py 5d18d250...,
scripts/repro.py 3952ad76..., results/extra_summary.json 35b5fdd8..., results/audit_tables.md 9c09520b...
Recommendation: fix both graders, pending step 6 (not run).
