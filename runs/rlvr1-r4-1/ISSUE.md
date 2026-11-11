# Audit: graders of the RLVR1 instruction-following rows (SkyRL reward and task-curation gate)

This file stands in for the issue (offline exercise). Entries are appended in order; times are UTC from `date -u`.

## Progress

- [x] Step 1: inputs pinned from records, configuration and lockfiles (2026-11-11T09:48Z). Code-only inputs added after the contract hash.
- [x] Step 2: contracts (audit/CONTRACTS.md v1), hash recorded at 2026-11-11T09:52:44Z before any grader code was read.
- [x] Step 3: 208 fixtures + 3 extraction fixtures + 6 targeted tests (audit/tests/), replacement grader audit/replacement.py (first at 10:10Z, extended 10:30Z). 
- [x] Step 4: property tests, fuzzing, content-free responses, reference comparison (10:33Z). `pytest audit/tests` (fixtures + properties): 511 passed, 153 strict xfails (10:42Z).
- [x] Step 5: all 23,315 stored responses graded by SkyRL, the gate, the replacement (proposed) and fixes only (10:40Z).
- [ ] Step 6: NOT RUN in this exercise (no reviewers); its plan and decision rule are recorded below.
- [x] Step 7: audit/AUDIT.md written (10:42Z, final 10:47Z); all 67 commands it quotes verified by audit/scripts/check_report_commands.py; tests and manifest rechecked.

Next (if work continues): run step 6 with reviewers on the held-out half per the plan below; have the maintainers settle the decision entries; then rerun audit/scripts/panel_grade.py, panel_analyze.py, panel_headline.py with the chosen readings.

## Step 1. Pinned inputs (2026-11-11T09:48Z)

Verified by `audit/scripts/verify_manifest.py`: all 177 files in `case/MANIFEST.sha256` match (0 missing, 0 mismatched, 0 unlisted); the installed `verifyit` and `verifiable_instructions` packages in `.venv` are byte-identical to `case/grader/verifyit/` and `case/reference/verifiable-instructions/verifiable_instructions/` (74 files compared, 0 differ). `case/MANIFEST.sha256` itself: sha256 `932e03515646bd1811e79e603de2d4bd1961d3a1d997bf37cd6a720125fce6b4`.

| Input | Pin | Source |
|---|---|---|
| Grader 1: SkyRL reward (`grade_instruction_following`, session `NemotronTaskSession`) | Marin `af9c6789e878bed1a6fc9513232bcfc54ac73b3a`, files and git blobs in `case/SOURCES.md` | SOURCES.md, MANIFEST |
| Checkers run by grader 1, and reference for grader 2 | NVIDIA `abukharin-nv/verifiable-instructions` at `f46a5ac87b1400a4f8973039844b6be9b56e3faf` (no tests in the repository) | SOURCES.md, lockfile |
| Grader 2: task-curation gate (`convert_instruction_following`, verifyit `ifeval` checks, `grade_judge_candidate`) | Marin `af9c678…`, `lib/verifyit` installed as `marin-verifyit @ git+…@af9c678…` | lockfile, SOURCES.md |
| Dataset | HF `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` rev `600262dd37891b86075a80517e61dbfb105d7cbe`, `data/train.parquet` sha256 `fde7259ad17170b6a57292ea85fdd20d9a2428b078cc3aa67cdeab8155fc0b1b` (not available offline: unverified); subset file `case/data/rlvr1_instruction_following.jsonl` sha256 `96144deb8ce5c19d197bdc0006600666b4a0a023f1ed99b36f9cb3a790024159`, 11,817 rows, 28,219 constraints, 47 ids | TASK.md, SOURCES.md |
| One hash per row | `audit/frozen/row_hashes.tsv` (sha256 over canonical JSON of uuid, prompt messages, instruction ids, kwargs), file sha256 `186ad2dc97aacdf93d553183b675954e7148ce27570ad610d1a9f50a7d975c1e`. Row 0 `3dcf41b6-…` → `fb6d56460f23…` | `audit/scripts/row_hashes.py` |
| Prompt rendering | one user message per row (0 rows with a system message, checked), `record_json.prompt` equals the user message in all rows (checked); stored request settings temperature 1.0, top-p 1.0, no tools; the requirement list is in the user message (numbered list in 3,625 rows, prose joined with "and" in the rest) | data |
| Panel generation | vLLM 0.11.0, torch 2.8.0+cu128, transformers 4.57.1, Python 3.12.3, one GPU; per model: revision, token limit 2,048 (8,192 thinking), `max_model_len`; chat template = each model's at the pinned revision | `case/panel/CONFIGS.md` |
| Panel files | 6 run files, sha256 in SOURCES.md, verified by manifest | SOURCES.md |
| Grader dependencies | Python 3.12.10; nltk 3.10.3, langdetect 1.0.9, absl-py 2.5.0, immutabledict 4.3.1, regex 2026.9.29 and the rest of `case/deps/requirements.lock.txt`; NLTK `punkt_tab` from zip sha256 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106` (77 files, manifest-verified) | lockfile, SOURCES.md |

Unverified inputs (cannot be fetched offline):

- The source parquet: `huggingface.co/datasets/open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30` at `600262dd…`, `data/train.parquet`. Verify with `huggingface-cli download open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3-2026-09-30 data/train.parquet --repo-type dataset --revision 600262dd37891b86075a80517e61dbfb105d7cbe` then `sha256sum`, and rebuild the subset by filtering `extra_info.nemotron_ultra.agent == "instruction_following_simple_agent"`.
- The panel's generation manifests (not included): stop sequences, the server's reasoning parser, and whether a reasoning field was merged are not recorded in CONFIGS.md. The stored `raw_response` of the thinking model contains its thinking followed by `</think>` (1,361 of 1,500), so no reasoning parser split it.
- The RL training run's own settings (policy token limit, chat template, reasoning parser, the session config's `verifyit_enabled`): no run record is part of the case. TASK.md gives the default `verifyit_enabled=false`.

Panel record counts (from the stored records, before grading):

| Run file | Responses | `finish_reason` length | contains `</think>` | contains `<think>` | empty |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct sample0 | 4,000 | 65 | 0 | 3 | 0 |
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 92 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507 greedy_repeat | 1,000 | 81 | 0 | 0 | 0 |
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 620 | 0 | 11 | 0 |
| Qwen3-4B-Thinking-2507 sample0 | 1,500 | 166 | 1,361 | 1 | 0 |
| OLMo-2-1124-7B-Instruct sample0 | 3,998 | 39 | 0 | 0 | 1 |

## Step 2. Contract hash (2026-11-11T09:52:44Z)

`audit/CONTRACTS.md` v1, sha256 `c79ad25540480f8ca413a42545d84442841a96deb8b02aeb1a40fc5ca28496e3`, frozen copy `audit/frozen/CONTRACTS_v1.md` (same hash). Written from the prompt text and kwargs only; no file under `case/grader/` or `case/reference/` had been opened. It holds 47 contracts and 37 decision entries (table in section 2 of the file). Later changes are logged below with their reason.

## Step 1 (continued). Inputs that only the code shows (recorded 2026-11-11T09:58Z, after the contract hash)

- Graded-text extraction, both pipelines: `final_answer_text` (SkyRL, `answer_extraction.py`) and `_answer_text(..., strip_reasoning=True)` (verifyit `grade_judge.py`, used because `convert_instruction_following` sets `strip_candidate_reasoning_blocks=True`) are the same algorithm: delete every paired `<think>…</think>`, `<thinking>…</thinking>`, `<|start_think|>…<|end_think|>` block; keep the text after the last closing marker; return `""` if an opening marker is still present; strip whitespace and a trailing `<|eot_id|>`. A response with no marker at all (Qwen3 thinking whose reasoning never closed, because the chat template supplies the opening `<think>`) is returned whole, thinking included.
- Task-curation empty-output policy: `EmptyOutputPolicy.GRADE` (an empty candidate is graded by the checks, not zeroed).
- SkyRL session: a checker exception sets `instruction_errors`; `NemotronTaskSession._advance` then returns reward 0.0 with `Outcome.INFRA_ERROR` ("Verifier configuration failed"). `grade_instruction_following` itself records the constraint as failed.
- langdetect: `_ensure_nltk_data` sets `DetectorFactory.seed = 0` before grading (SkyRL). The verifyit `ifeval` checks do not use langdetect.
- NLTK data: `_ensure_nltk_data` checks for `tokenizers/punkt_tab` and, if missing, calls `nltk.download("punkt_tab")` at grading time (network, no version or hash). `count_sentences` loads `nltk:tokenizers/punkt/english.pickle`; under nltk 3.10.3 this resolves to `PunktTokenizer` over `punkt_tab` (checked: `audit/scripts/check_runtime_inputs.py`, the old `punkt` pickle is not installed and not needed).
- Python RNG: building the 28,219 constraints with their kwargs consumes the global `random` state in 77 constructions, all `length_constraints:nth_paragraph_first_word` with `nth_paragraph = num_paragraphs + 1`; NVIDIA's `build_description` then draws `nth_paragraph = random.randint(1, num_paragraphs + 1)` (`audit/scripts/check_runtime_inputs.py`).
- Second SkyRL reward `grade_nemotron_instructions` (only when the session config sets `verifyit_enabled`): routes `punctuation:*` to verifyit's checks, replaces `language:response_language`, `change_case:english_capital/english_lowercase` with direct `langdetect.detect` calls (no exception handling), and `detectable_format:json_format` with a JSON-schema parse; it runs the rest of NVIDIA's checkers under verifyit's `_check`, which turns a non-boolean return into an error (reward 0.0, `verification_error`).

Unverified (outside the case):

- Every row has `extra_info.nemotron_ultra.route = "skyrl_gym"`, while `NemotronTaskSession.__init__` raises `ValueError("Terminal source rows require a portable Harbor task")` unless the route is `"task_session"`. The lowering code (`skyrl_gym.source_task.session_parameters`) that would rewrite the route is not in the case. Verify by running `session_parameters` on a lowered row at Marin `af9c678` (`vendor/skyrl/skyrl-gym/skyrl_gym/source_task.py`).
- What the trainer does with `Outcome.INFRA_ERROR` (dropped or trained as reward 0.0) is not in the case.

## Step 2 (continued). Contract changes (2026-11-11T10:09Z)

`audit/CONTRACTS.md` section 3 adds seven decision entries for wording that v1 read one way without an entry (D-word third reading, D-word-markup, D-ps-case, D-sections-exact, D-lowercase-scope, D-end-case, D-letter-counting alternative). No pass/fail condition changed; each entry's reason is in the table. Current file sha256 `72c72151e21e4d34dde3e8242df93e5ac15fb2963fba8f67db1508e7c560c82d` (v1 frozen as `audit/frozen/CONTRACTS_v1.md`).

## Step 3. Fixtures and replacement grader (2026-11-11T10:10Z)

- `audit/tests/fixtures.py` (sha256 `fb783b0b7581412000eacafac474281b4694442e2549a82f2901902c693ff24d`): 194 fixtures over all 47 checks, labeled from the contracts; id = check + 12 hex of sha256(check, kwargs, text). Plus 3 extraction fixtures.
- `audit/replacement.py` (sha256 `dd01016cfa84388a9916fbad451bd205395e20a3c508e34dc9ab3d6cb6ec7adc`): the contracts, one switch per decision entry (`Readings`), proposed readings by default. It agrees with every fixture label.
- `audit/harness.py` (sha256 `eaa486b3b33af207ab70970b029fd033ec145deba3bfff689892cbe11fb8df46`): runs both graders as their pipelines do (`final_answer_text` / `_answer_text` loaded from the pinned files with `ast`).
- `audit/scripts/classify_fixtures.py` grades every fixture with both graders and classifies each disagreement: a decision when one alternative reading (or a pair) makes the replacement give the grader's verdict, naming the entries; otherwise a finding. Output frozen as `audit/tests/fixture_expectations.json` = `audit/frozen/fixture_expectations_v1.json`, sha256 `095dada9c523d4fdacb57f580df70174cfc4dca4bd59903f54fb8fbf42959015`.
- `audit/tests/test_fixtures.py` (sha256 `8e6c2b30caa12d54b42195c6fa0c5988ce1e4392beb3bdfda6df961189f1168a`) marks each grader disagreement `xfail(strict=True)`. Result: 460 passed, 123 xfailed.

| Grader | Fixtures graded | Agree with the label | Disagree: finding | Disagree: decision |
|---|---|---|---|---|
| SkyRL (NVIDIA checkers) | 194 | 126 | 31 | 37 |
| Task-curation gate (verifyit) | 180 (14 semantic fixtures not gated) | 131 | 30 | 19 |

Extraction fixtures: an unclosed Qwen3 reasoning text and a non-reasoning answer with a comma before a literal `<think>` both get SkyRL reward 1.0 and pass the curation gate on `punctuation:no_comma`, where the contract fails them (findings F-extract-1, F-extract-2 below).

## Step 5 plan, recorded before grading the panel (2026-11-11T10:14Z)

- Panel = the 6 stored run files (23,315 responses); no new generation (no compute in this exercise).
- Held-out rule, fixed now: a response is held out when the first hex digit of sha256(uuid) is 8-f (about half of the rows, the same rows in every run). Any change to `audit/replacement.py` prompted by panel disagreements may look only at the other half (development); final numbers are reported on both halves separately if the replacement changes.
- SkyRL verdicts depend on Python's global RNG for the 77 `nth_paragraph = num_paragraphs + 1` constraints. For reproducible panel numbers each response is graded after `random.seed(<first 8 hex of sha256(uuid)>)`; the RNG dependence is measured separately with 20 seeds.

## Step 4. Reference comparison and stress tests (2026-11-11T10:33Z)

- Reference comparison: NVIDIA's checkers are grader 1 itself and the reference for verifyit. Both were run on all 208 fixtures (`audit/tests/fixture_expectations.json`) and on the whole panel (step 5); every verifyit-vs-reference disagreement on the panel is attributed by the replacement (`panel_summary.json`, keys `gate_vs_skyrl_*`).
- Reference unit tests: the NVIDIA repository has no tests, and verifyit's own tests are not part of the case, so no test list could be checked against the contracts.
- Property tests `audit/tests/test_properties.py` (hypothesis, derandomized, no example database): 14 properties x 3 graders; 29 pass, 13 strict xfails, each naming the broken contract (SkyRL fails 6 properties, verifyit 7).
- Fuzzing `audit/scripts/step4_fuzz.py 3000 20261111` (3,000 generated texts x 47 checks x 2 graders): the only exception is NVIDIA `last_word:last_word_answer` `IndexError` on whitespace-only text (180 texts); verifyit raised none. No exception stops a run: `grade_instruction_following` and verifyit's `_passes` both catch it, but the SkyRL session then reports `Outcome.INFRA_ERROR` (reward 0.0). The non-default `grade_nemotron_instructions` turns NVIDIA's `None` return of `copy:repeat_phrase` and langdetect's exception into `verification_error` (reward 0.0), checked by hand (two exact copies; text "12345").
- Score-level transforms: SkyRL binary all-pass; no row sets `grading_mode`, so `fraction` is never used. The curation gate is all-or-nothing over deterministic constraints before the judge.
- Content-free responses `audit/scripts/step4_content_free.py` (full output `audit/out/step4_content_free.txt`): the empty response gets SkyRL reward 1.0 on 1,702 of 11,817 rows (contract, applied literally: 967) and passes the curation gate on 810 rows; a single "." gets SkyRL reward 1.0 on 1,144 rows (contract 829); "data " x 300 gets 436 (contract 567); restating the prompt's requirement text gets 813 (contract 558) and passes the gate on 1,308 rows. Checks that pass the empty response for SkyRL beyond the contract: `language:response_language` (780 of 780, langdetect exception counted as a pass), `first_word:first_word_sent` and `last_word:last_word_sent` (all, no sentence to fail), `detectable_format:bigram_wrapping` (all), `keywords:word_count_different_numbers` with hidden `less than` (206). The empty text raises `IndexError` in all 625 `last_word:last_word_answer` constraints.

## Step 5 note: replacement changes after the first panel pass (2026-11-11T10:30Z)

Looking only at development-half disagreements (`audit/scripts/show_disagreements.py`, held-out rows excluded), the replacement got one implementation fix (`sentence_hyphens` spaced hyphens) and four decision entries (D-divider-edges, D-two-responses-edges, D-consecutive-alphabet, D-start-end-single; proposed readings unchanged), plus 14 fixtures. Panel numbers below are reported for all rows and for the held-out half. A "fixes only" configuration (`replacement.OFFICIAL`) applies each grader's own reading of every decision entry per check, so that its differences from a grader are defects.

## Step 3 (updated) and step 5 results (2026-11-11T10:42Z)

Fixtures v2: `audit/tests/fixtures.py` sha256 `b8153d4cf50b5a300f40edd5878d82b6062c980847917d01b7a5760329929bcb` (208 fixtures); expectations `audit/tests/fixture_expectations.json` = `audit/frozen/fixture_expectations_v2.json` sha256 `4e9338e7260531c51fcf58f64f29968085319086fbaf022cb4e6a5e0362eb1ce`. SkyRL: 128 agree, 39 finding fixtures, 41 decision fixtures; verifyit (191 gated): 137 agree, 34 findings, 20 decisions.
Code: `audit/replacement.py` `5ddf22f4bcd269493c3b444ecaf31d11b4f738594214c2f27b4f6d34acd62124`, `audit/harness.py` `eaa486b3…`, `audit/repro.py` `0bd985a8838707409c7aa7bbcfac4093a8a5fbb6fd5e2a713eef66dca1901507`, `audit/CONTRACTS.md` `c8f4ba09e5d5dad02aa478f42d8028ea2ea7594ad8696cee2ea390b4861284d3`.
Panel outputs: `audit/out/panel_verdicts.jsonl` `f3f1d22141ace04e73ac990a098200cb2d5663788979db13727ba6028d629972`, `audit/out/panel_summary.json` `747c3afa984278cf7baf476d719e2a173895fda134ad2268615cc0b7b21e3610`, step 4 `step4_content_free.json` `84458453…`, `step4_fuzz.json` `4c6dd2e1…`.

Step 5 headline (full numbers in audit/AUDIT.md and audit/out/panel_headline.txt):
- SkyRL minus fixes only, per run (points, 95% bootstrap): Qwen3-4B-Instruct greedy −4.2 [−5.8, −2.6], greedy_repeat −4.4, sample0 −4.8 [−5.3, −4.3], Qwen2.5-7B −3.5 [−4.3, −2.6], OLMo-2-7B −2.3 [−3.0, −1.7], Qwen3-4B-Thinking −8.6 [−10.3, −6.9]; held-out half −2.4 to −10.1.
- Rerun (greedy vs greedy_repeat, 1,000 rows, 506 identical responses): SkyRL +0.2 [−0.5, +1.0], 16 row verdicts flip.
- False rewards: 396 of 6,472 SkyRL passes contradicted under fixes only (6.1%; held-out 5.5%); 1,043 under proposed (16.1%).
- Gate: 2,711 of 10,192 gate passes (26.6%) fail a deterministic constraint under fixes only; 1,618 of 13,123 gate failures (12.3%) satisfy all of them.
- Extraction: 139 of 1,500 thinking responses unclosed (SkyRL reward 1.0 on 1; 18 pass the gate); 22 non-reasoning responses contain a reasoning marker (SkyRL reward 1.0 on 8).
- `nth_paragraph` impossible rows: 161 panel responses, verdict varies over 20 seeds for 45.

## Findings (2026-11-11T10:42Z)

Full table with counterexamples, commands, contracts, panel shares and reference status: audit/AUDIT.md.
- Pipeline and data: G1 unclosed reasoning graded; G2 literal `<think>` empties the answer; G3 77 impossible nth_paragraph rows + random paragraph index; G4 hidden relation in word_count_different_numbers (206 `less than`); G5 runtime NLTK download (unpinned); G6 checker exception reported as INFRA_ERROR; G7 content-free responses (empty text: SkyRL reward 1.0 on 1,702 rows).
- SkyRL / NVIDIA checkers: S1 word_once exactly once; S2 count_unique punctuation; S3 counting_composition divider and punctuation; S4 postscript anywhere / P.P.S; S5 bigram_wrapping vacuous; S6 constrained_response two options; S7 multiple_sections mid-sentence; S8 bullet lines `---`, `-5`, `*x`; S9 highlights from `*` arithmetic; S10 sentence_hyphens hyphenated words; S11 square_brackets punctuation; S12 first/last word punctuation; S13 keyword position punctuation tokens; S14 adjacent letters behind punctuation, digits; S15 palindrome tokens; S16 language exception passes; S17 langdetect on uppercase; S18 nth paragraph indexing; S19 empty placeholders; S20 lowercase ASCII-only; S21 CJK sentence ends.
- verifyit: V1 no_adjacent_consecutive checks duplicates; V2 lowercase_counting inverted; V3 square_brackets any bracket; V4 repeat_phrase counts copies; V5 paragraphs ≥2 by either separator; V6 number_paragraphs ignores ***; V7 sentence_hyphens wrong semantics; V8 no English check; V9 JSON fence; V10 start_end trailing punctuation and lone dash; V11 blank title; V12 single quotes; V13 counting_composition; V14 ASCII-only words; V15-V19 shared with S1, G4, S7, S9, S21.

## Decision entries

46 entries, table in audit/AUDIT.md ("Decision entries for the maintainers") and audit/CONTRACTS.md sections 2-3, each with the grader readings and the panel disagreements it explains.

## Step 6 plan, not run (recorded 2026-11-11T10:42Z, before any review)

Result that would confirm the recommendation to fix (adopt the replacement under the maintainers' readings): the replacement passes every fixture; scored coverage is complete; and for each grader, the replacement's error rate is lower than the grader's with a paired 95% bootstrap interval that excludes zero. If instead the grader's error-rate interval upper end is below 2% for a pipeline, the recommendation for that pipeline would change to admit.
Sample design: population = held-out half (SkyRL: 27,950 constraint verdicts, 1,752 disagreeing with fixes only; gate: 25,449 gated verdicts, 3,801 disagreeing). Strata = disagree / agree per grader; sample all or most disagreements and about 175 agreements per grader: for a zero-error agreement stratum holding 93.7% of the population, 0.937 × (1 − 0.025^(1/n)) < 0.02 needs n ≥ 172. Seeded draw, sha256 of the case list recorded here before any review; two reviewers per case in separate runs and orders, with skill/references/reviewer-prompt.md.

## Step 7. Report and final checks (2026-11-11T10:47Z)

- audit/AUDIT.md sha256 `c3265bd87b1f3ccb7fa3a004c69d8c5c21b8915fdcb3c4cb69dee10eb275f3b4` (posted here in place of an issue comment). Recommendation: fix both graders (with the data repairs G3, G4); step 6 not run.
- `audit/scripts/check_report_commands.py`: 67 quoted commands rerun, 0 mismatches.
- `pytest audit/tests`: 511 passed, 153 strict xfails.
- After the runs, `audit/scripts/verify_manifest.py` still reports 177 case files matching, installed packages identical; skill files unchanged (SKILL.md `35ff6cb9…`, ifbench.md `4f36a6a5…`, reviewer-prompt.md `02776f17…`); no `__pycache__` under case/ or skill/.
