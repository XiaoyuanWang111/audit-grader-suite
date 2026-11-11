# Audit: ToyQA 1.0 judge pipeline (`case/judge_pipeline.py`)

This file stands in for the task's issue (no issue tracker in this offline run). It holds the pinned inputs, the
contract hash and time, the decision entries, the findings, and the frozen-sample hashes, and is appended to as the
audit goes. Paths are relative to the audit directory W (`<W>`).

## 1. Pinned inputs (recorded 2026-11-11 01:20 UTC, before the contract)

No repository, so each file is pinned by sha256 instead of a commit. `python -B audit/scripts/pin_inputs.py`
verifies `case/MANIFEST.sha256` (all 9 entries OK) and writes `audit/pins.json` with one sha256 per row of
`questions.jsonl` and `responses.jsonl` (sha256 of the raw UTF-8 line without its newline).

| Input | Value | Source |
|---|---|---|
| Manifest | `MANIFEST.sha256` sha256 `480efb03f62b3f8c4cedadaab55089e7c4570fd173426cf7f4eb2ac5c5c48084` | computed |
| Grader under audit | `judge_pipeline.py` `6f14e7270c60adf8e3ab00c8025ee81c548486e96078176368494013250d63f6` | manifest |
| Reference implementation | `reference/pipeline_ref.py` `7edd7358db7c5491ce798ef83a0e73d440b24473dbd380ab8dbbed0e5f894112`, "released with ToyQA 1.0" | manifest, TASK.md |
| Judge back ends (not under audit, loaded by both pipelines) | `judges.py` `2da4af67154b8c1fb6211dca4336c96db75dcf79f3238ad3204effca60584c53` | manifest |
| Dataset | ToyQA 1.0, `questions.jsonl` `b3a8cba68bcb2fc5a5a44e097068669ac6a4a33502da4288e877b16a889c07de`, 12 rows; row hashes in `audit/pins.json` (q01 `ca95c38e…`, q12 `f925ff19…`) | manifest |
| Answer prompt | `prompt_template.txt` `b996b5aca0b100fccd0009b1af0023ee6bc8936178db2314d7e21abed2110a73`; `{question}` replaced; only user message; no system prompt; each model's own chat template | TASK.md |
| Generation settings | temperature 0 and `max_tokens` 192 in every row (fields `temperature`, `max_tokens`); no stop sequences; no reasoning parser; no separate reasoning field (no such field in any row) | responses.jsonl, TASK.md |
| Extraction rule | text after the last `</think>`, else whole response; strip; `<think>` without `</think>` is `extraction_failure` | TASK.md (README step 1) |
| Judge | model `judge-m1`, temperature 0, `max_tokens` 32, prompt as one user message, client cache by (prompt, call number) | TASK.md (README step 3) |
| Judge template | `judge_template.txt` `83abe854cd4e08a43d0bf59e59c0b6b38dbb4c947c12c71fbcac80992853cd4d` (ASCII, LF, ends in a newline) | manifest |
| Reply parser | last standalone capital A/B/C, ASCII-alnum boundaries; retry once; else `judge_error` | TASK.md (README step 4) |
| Stored judge replies | `judge_replies.jsonl` `48d96f38b5d807f9e42a90f539853bf24dfa192fad87d2c911645600dc6ddc3b`: 68 rows = 34 prompt hashes x calls 1 and 2; fields `call`, `prompt_sha256`, `reply` only | manifest, records |
| Stored responses | `responses.jsonl` `a61ab1fd9678a1a9c69e75a9ef90246b5cf432432b61f5e42991653b84e07f6a`: 48 rows, 4 models x 12; `finish_reason` `length` on 3 rows, all `ibis-8b-think` | manifest, records |
| Task text | `TASK.md` `709c352881630711490ce5e524148ab86134906edeee99960550335ebd041c95` | manifest |
| Dependencies | Python 3 standard library only; audit interpreter Python 3.12.10 (the run's Python version is not recorded) | TASK.md, local |

Unpinned or unverified (each also a protocol finding below):

- Answering models (`orca-7b`, `puffin-13b`, `heron-32b-think`, `ibis-8b-think`) have names but no revision, and
  "each model's own chat template" has no revision or hash; the response records carry neither. The serving stack
  and its version are not recorded. This blocks regenerating the panel, not regrading it.
- Judge model `judge-m1` has a name but no revision or snapshot. Its settings (temperature 0, `max_tokens` 32) are
  stated in the README only; `judge_replies.jsonl` has no settings or model field. Unverified: no offline command
  can check it; the record field that would verify it is a per-reply `model`/`settings` field, which the stored
  run lacks.
- The Python version of the evaluation run is not recorded.

## 2. Contract

- File: `audit/CONTRACT.md`, sha256 `0ce9b0511c32440b4accd0a9871f9188fcf8610c46b20ec04b62ed5f041299b0`, recorded
  2026-11-11 01:22:10 UTC, before any of `judge_pipeline.py`, `judges.py` or `reference/pipeline_ref.py` was opened.
- Decision entries opened with the contract: `D-whitespace`, `D-reopened-think`, `D-judge-window`,
  `D-judge-exception`, `D-missing-response` (readings and proposals in the contract file).

## 2a. Contract change

- 2026-11-11 01:33:16 UTC: `audit/CONTRACT.md` now sha256
  `2db31dc3f135a8f40b4f359d51a38594f8bdd6c142c0b399fed642279fabdec8`. Added `D-hedged-alternatives` after the
  panel showed three answers that name the gold target and another answer as alternatives (a06, a36, a41). No
  contract rule changed; the earlier hash above stays the pre-code record.

## 3-5. Findings (as found; full table in `audit/AUDIT.md`)

| Id | Stage | Defect | Fixtures | Stored panel verdicts affected | Reference |
|---|---|---|---|---|---|
| F1 | C1/C5 extraction label | unclosed reasoning gets `not_attempted`, never `extraction_failure` | 2 | 3 of 48 (a08, a20, a40) | correct |
| F2 | C2 rendering | only the first line (`str.splitlines()[0]`) reaches the judge | 5 | 0 of 48 (no multi-line graded text) | correct |
| F3 | C2 rendering | empty graded text raises `IndexError`, which stops the whole run | 3 + 1 CLI | 0 of 48 | correct |
| F4 | C4 reply parsing | first capital A/B/C anywhere in the reply, not the last standalone one; no retry when call 1 has none | 12 | 7 of 48 (a09, a16, a22, a24, a32, a34, a35) | correct |
| G1 | inputs | answering models, chat templates, serving stack, Python version not pinned | - | - | same |
| G2 | inputs | judge model `judge-m1` has no revision; judge settings absent from the stored records | - | - | same |

Decision entries: `D-whitespace`, `D-reopened-think`, `D-judge-window`, `D-judge-exception`, `D-missing-response`,
`D-hedged-alternatives`. The replacement grader is `audit/replacement/toyqa_replacement.py` (one switch per entry).

## 6. Pre-review record (written before the sample was drawn)

Result that would change the step 7 recommendation ("fix the grader: adopt the replacement's deterministic stages,
keep the judge model and template"):

- The recommendation stands if the replacement passes every fixture, its scored coverage on the panel is 48/48,
  and the blinded review gives it a lower error rate than `judge_pipeline.py` with a paired 95% bootstrap interval
  that excludes zero.
- If that paired interval includes zero, F1-F4 are still fixed on contract grounds (each breaks a README rule), but
  the report claims no measured error-rate gain.
- If the consensus contradicts the replacement (with the recorded judge) on more than 5 of the 38 agreement-stratum
  verdicts, the judge model or template, not only the pipeline code, needs work, and the recommendation becomes
  "fix the pipeline and re-validate the judge".

## 6.1-6.2. Frozen sample (2026-11-11 01:34:22 UTC, before any review)

- Drawn by `python -B audit/scripts/freeze_sample.py`, seed 20261111 (case ids and batch orders; the draw is a
  census). Population: the 48 stored verdicts. Strata: replacement and grader disagree, 10 of 10 drawn; agree,
  38 of 38 drawn.
- `audit/frozen/cases.jsonl` (the case list) sha256 `f6f037c01a647b97201c05f3f888dc6c27a917e890dc5905dea4439b9c96e17e`
- `audit/frozen/keys.jsonl` (source model and every grader's verdict per case) sha256
  `b3ae5db991535b82c6b65f41f1af0f238370514656d9297a0c0f8eb5e9699436`
- `audit/frozen/batch_A.md` `41b13a6dcae6a3563715624deb607eaf0fa8068642a56fed0008d778fc7cb2c6`,
  `audit/frozen/batch_B.md` `bb781872ea8aee45bf1d72dade422244db26d8df839a36b950d73f66ffc98edd` (same cases, two orders)
- `audit/frozen/reviewer_prompt.md` `d2d13d7122f46ed2ceea29348a9e44b8f72b74e019e5988b245a9272ea0a878a`,
  `audit/frozen/show_case.py` `28def74df318ea01543d7a3954d388cb67c74b65d92a747652ed2974e2956500`
- `audit/frozen/SHA256SUMS` (54 files, including the 48 response files) sha256
  `cd15002504f215551e39c955397a71c1b967aac9594b5c43837dfba09fb27c06`
- Reviews: none. Step 6.4-6.5 not run (no subagents in this exercise); `audit/frozen/reviews/` does not exist.

## Log

- 2026-11-11 01:20 UTC: inputs pinned, manifest verified.
- 2026-11-11 01:22 UTC: contract hashed; code reading starts after this entry.
- Between 01:22:10 and 01:33:16 UTC (clock not read in between): replacement written from the contract, then the stored panel graded
  (`python -B audit/scripts/panel.py`); fixtures, property tests and fuzzing added.
- 2026-11-11 01:33 UTC: `D-hedged-alternatives` added to the contract (section 2a).
- 2026-11-11 01:34 UTC: pre-review record written, then the sample drawn and frozen (section 6.1-6.2).
- 2026-11-11 01:36 UTC: step 7 report written to `audit/AUDIT.md`.
- 2026-11-11 01:39:55 UTC: final checks. Manifest re-verified after all runs (9 of 9 OK; no bytecode under `case/`).
  `python -B -m unittest discover -s audit/tests -t audit/tests`: 215 tests OK, 34 expected failures.
  `python -B audit/scripts/verify_report.py`: every command in `audit/AUDIT.md` prints what the report says; frozen
  files match `audit/frozen/SHA256SUMS` (54 of 54).

## Audit artifacts at the final check

| File | sha256 |
|---|---|
| `audit/replacement/toyqa_replacement.py` | `e72af0f8ec2a85b67d504b17b9787b57a8a377d4ee9dfa2c6b41512c4de6caf2` |
| `audit/tests/fixtures.py` | `74e44c21be5d19d354eeeac268ed9ee1c0fbb2a86d87a1637b4ab3f135a4ed27` |
| `audit/tests/test_fixtures.py` | `512e58e511d46cf3de986825f56f27816b20b28ef88f0d8e6b4d3c4438c6adb4` |
| `audit/tests/test_cli.py` | `684b0c2ade3a9930733cd4795ebc9b04396ff339dabae46beeecf7219f91df38` |
| `audit/tests/test_properties.py` | `2b43046fd466b88e933677ef716276c629a9e2ac332b104779e8b4dcd60b6a48` |
| `audit/CONTRACT.md` (current) | `2db31dc3f135a8f40b4f359d51a38594f8bdd6c142c0b399fed642279fabdec8` |

## 7. Report

Posted as `audit/AUDIT.md` (no issue tracker). Recommendation: fix the grader (F1-F4), pin G1-G2, then run the
blinded review on the frozen sample.
