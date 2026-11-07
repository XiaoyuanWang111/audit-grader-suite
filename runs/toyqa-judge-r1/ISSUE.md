# Audit: ToyQA 1.0 LLM-judge pipeline (`case/judge_pipeline.py`)

This file stands in for the task's issue (offline exercise: no issue tracker). Entries are appended in order, each
with the UTC time read from the clock in the same step. Paths are relative to the audit run's root, the folder that
holds `case/` and `audit/`.

## Step 1. Pinned inputs (2026-11-06T22:25:54Z)

Pinned before any code was read, from `case/TASK.md`, the manifest and the stored run records only.

`python -I audit/scripts/check_pins.py` checks every hash below; it printed `pins: OK` at 22:25:54Z.

| Input | Pin | Source |
|---|---|---|
| Grader under audit | `case/judge_pipeline.py` sha256 `6f14e7270c60adf8e3ab00c8025ee81c548486e96078176368494013250d63f6` | manifest (no repository, so no commit) |
| Reference implementation | `case/reference/pipeline_ref.py` sha256 `7edd7358db7c5491ce798ef83a0e73d440b24473dbd380ab8dbbed0e5f894112` | manifest (no commit) |
| Judge back ends (not under audit) | `case/judges.py` sha256 `2da4af67154b8c1fb6211dca4336c96db75dcf79f3238ad3204effca60584c53` | manifest |
| Task text | `case/TASK.md` sha256 `709c352881630711490ce5e524148ab86134906edeee99960550335ebd041c95` | manifest |
| Dataset | `case/questions.jsonl` sha256 `b3a8cba68bcb2fc5a5a44e097068669ac6a4a33502da4288e877b16a889c07de`, 12 rows; one sha256 per row (raw UTF-8 line, no newline) in `audit/pins/rows.sha256` | manifest; row hashes computed here |
| Answer prompt | `case/prompt_template.txt` sha256 `b996b5aca0b100fccd0009b1af0023ee6bc8936178db2314d7e21abed2110a73`, sent as the only user message, no system prompt | manifest; TASK.md |
| Judge prompt template | `case/judge_template.txt` sha256 `83abe854cd4e08a43d0bf59e59c0b6b38dbb4c947c12c71fbcac80992853cd4d` (ends with one `\n`, no CR bytes) | manifest |
| Stored responses | `case/responses.jsonl` sha256 `a61ab1fd9678a1a9c69e75a9ef90246b5cf432432b61f5e42991653b84e07f6a`, 48 rows (4 models x 12 questions, ids unique, one row per model and question); row hashes in `audit/pins/rows.sha256` | manifest |
| Stored judge replies | `case/judge_replies.jsonl` sha256 `48d96f38b5d807f9e42a90f539853bf24dfa192fad87d2c911645600dc6ddc3b`, 68 rows: 34 prompt hashes x calls 1 and 2; fields `call`, `prompt_sha256`, `reply` only | manifest |
| Manifest itself | `case/MANIFEST.sha256` sha256 `480efb03f62b3f8c4cedadaab55089e7c4570fd173426cf7f4eb2ac5c5c48084` | computed here |
| Row-hash list | `audit/pins/rows.sha256` sha256 `f509fe54aafcf5a56a4ffccd309cb41b7a732eb696e2a55e363e902a6546793b` | computed here |
| Generation settings | `temperature` 0.0 and `max_tokens` 192 on all 48 rows; `finish_reason` `stop` on 45 rows, `length` on 3 (all `ibis-8b-think`) | `responses.jsonl` fields |
| Reasoning handling | no reasoning parser on the server, no separate reasoning field (the rows have none); the `-think` models' reasoning is inline in `response` | TASK.md; consistent with the rows' fields |
| Extraction rule | TASK.md pipeline step 1 (after the last `</think>`, stripped; `<think>` without `</think>` is `extraction_failure`) | TASK.md; the code's rule is recorded after the contract hash |
| Judge call | model `judge-m1`, one user message, temperature 0, `max_tokens` 32; the client caches replies by prompt and call number | TASK.md step 3 only |
| Reply parser | TASK.md step 4 (last standalone capital A/B/C; one retry; else `judge_error`) | TASK.md; the code's parser is recorded after the contract hash |
| Dependencies | Python 3 standard library only, offline | TASK.md; local interpreter Python 3.12.10 |

Unverified, with where the value would be and how to check it:

- U1. Stop sequences. TASK.md says none, but `responses.jsonl` has no `stop` field. Would be verified by
  `python -I -c "import json;print({json.dumps(json.loads(l).get('stop')) for l in open('case/responses.jsonl',encoding='utf-8')})"`
  printing `{'[]'}` or `{'null'}` on a run record that carries the field.
- U2. Judge model and judge decoding settings in the stored run. `judge_replies.jsonl` rows have no `model`,
  `temperature` or `max_tokens` field, so the stored run cannot be checked against TASK.md step 3. Would be verified by
  the same one-liner over `case/judge_replies.jsonl` with `.get('model')`, `.get('temperature')`, `.get('max_tokens')`.
- U3. Python version of the stored run (not recorded). The parser rule names ASCII classes, so the version should not
  change a verdict; recorded for completeness.

Unpinned by the benchmark (reported as protocol findings in step 7):

- The answering models' chat templates and checkpoints: TASK.md says "each model's own chat template" and names the
  models (`orca-7b`, `puffin-13b`, `heron-32b-think`, `ibis-8b-think`) with no revision or template hash, and the rows
  carry none. A template change can move the `<think>` marker into or out of the response text, which changes the
  graded text (pipeline step 1).

Skipped in this offline exercise: no issue tracker (this file is the record), no repository or commit to pin, no
Hugging Face dataset revision (the dataset is pinned by file and row hashes instead).

Deviation from the working-directory rule, recorded for the auditor's record: the first listing command at 22:20Z
also wrote a list of the `case/` file names to a temporary file under `/tmp`. Nothing outside this folder was read.
All later scratch files are under `audit/work/`.

## Step 2. Contract (2026-11-06T22:28:22Z)

`audit/CONTRACT.md` v1, sha256 `89cff5642dab9c67da3d45effc8b9a76978d07d9c6b8f5fef754bc0a86e16bdd` (8,124 bytes, LF),
recorded at 22:28:22Z, before any of `case/judge_pipeline.py`, `case/judges.py`, `case/reference/pipeline_ref.py` or
the stored response texts was opened. Sources: TASK.md, `judge_template.txt`, `questions.jsonl`.

Decision entries in v1 (all about the judge's grade, clause K; the deterministic stages have none):

- `D-multiple-candidates`: gold plus another candidate (q01 `Canberra or Sydney`). A, or B. Proposed B.
- `D-unlisted-equivalent`: a form of the gold that is neither gold nor alias beyond the four named differences
  (q05 `Márquez`). B, or A. Proposed B.
- `D-cut-off-answer`: a predicted answer cut before it names anything (q01 `The capital of Australia is Canb`). C, or B.
  Proposed C.

## Step 1, continued. Rules that only the code shows (2026-11-06T22:30:59Z, after the contract hash)

Grader under audit, `case/judge_pipeline.py` (sha256 `6f14e727…`):

- Extraction (`extract_graded_text`, lines 40-46): text after the last `</think>` (`rsplit`), stripped; `None` for
  `<think>` without `</think>`. `grade_response` (lines 79-81) maps `None` to the label `not_attempted`.
- Rendering (`render_prompt`, line 57): `graded_text.splitlines()[0][:300]`, the first line of the graded text, cut to
  300 characters, filled in with `str.format`; the template is read as UTF-8 with its final newline.
- Judge call (`call_judge`): `judge(prompt, call)` for call 1, then call 2 if call 1 gave no grade. The code passes
  no model name, temperature or `max_tokens`; the back ends take only the prompt and the call number.
- Reply parser (`parse_grade`, lines 25 and 62-64): `re.compile(r"[ABC]").search(reply)`, the first capital A, B or C
  anywhere in the reply, inside words included.
- Labels: A, B, C to `correct`, `incorrect`, `not_attempted`; no grade after two calls to `judge_error`.
- Aggregation (`aggregate`): denominators `len(questions)` (12); `attempted`, `cga`, F and the not-attempted rate as
  in TASK.md; percentages rounded to 0.1.
- Dependencies: `argparse`, `json`, `os`, `re`, `sys`, `collections` (standard library) and `judges.py`.

Reference, `case/reference/pipeline_ref.py` (sha256 `7edd7358…`): text after the last `</think>`
(`split(...)[-1]`), stripped, `extraction_failure` for an unclosed `<think>`; `answer[:300]`; parser
`(?<![A-Za-z0-9])([ABC])(?![A-Za-z0-9])`, last match; calls 1 and 2; same aggregation. Standard library only.

Judge back ends, `case/judges.py` (sha256 `2da4af67…`): `RecordedJudge` keys replies by (sha256 of the UTF-8 prompt,
call) and raises `LookupError` otherwise; `FakeJudge` always replies a bare `A`, `B` or `C`, so parser and retry
fixtures need a scripted stand-in (`audit/tests/toyqa_audit_lib.py`, `ScriptedJudge`).

## Steps 3 and 4. Fixtures, reference comparison, stress tests (2026-11-06T22:40:07Z)

Suite: `python -I -m unittest discover -s audit/tests` ran 247 tests, `OK (expected failures=35)`. pytest is not
installed, so strict expected failures use `unittest.expectedFailure` (an unexpected success fails the run); the shim in
`audit/tests/toyqa_audit_lib.py` switches to `pytest.mark.xfail(strict=True)` when pytest is present.

- 68 stage fixtures (`audit/tests/test_fixtures.py`: 12 extraction, 12 row-label, 12 rendering, 27 parser,
  5 aggregation), run on the grader, the reference and the replacement: 204 tests. The grader fails 26, all marked.
  The reference and the replacement pass all 68.
- 2 end-to-end CLI fixtures (`audit/tests/test_cli.py`, fake judge, run as a subprocess the way the evaluation runs
  the pipeline): the grader fails both (marked); the reference and the replacement pass both.
- 13 properties (`audit/tests/test_properties.py`, 400 seeded cases each, 50 for the end-to-end one): the grader
  fails 7, all marked; the reference and the replacement pass all.
- Fuzz (`python -I audit/scripts/fuzz.py`, 20,000 cases per part, summary `audit/work/fuzz_summary.json`): grader
  parser 12,368 and 4,415 mismatches on two reply generators, 0 exceptions; grader renderer 11,764 prompt mismatches
  and 1,024 IndexError (every empty text); grader rows 3,847 `extraction_failure -> not_attempted` and 5,116
  IndexError. Reference: 0 mismatches, 0 exceptions in every part. One exception stops the grader's whole run: no
  table, no `--out` file, exit status 1.
- Content-free responses (`python -I audit/scripts/content_free.py`, 9 kinds x 12 questions): in the grader, empty,
  whitespace-only and empty-after-reasoning raise IndexError, and repeated lines, the restated instructions and a
  multi-line rubric injection reach the judge cut to their first line. In the reference and the replacement all 108
  reach the judge as the contract says. None can be graded by the deployed judge here (no recorded replies).
- Neither the reference nor the grader ships unit tests, so no reference assertion can be checked against the
  replacement and no grader test encodes a decision.

Findings so far (the grader under audit; the reference is correct on each):

- F1. Extraction failures get the label `not_attempted` (`grade_response`, line 81). Breaks E2, L1, G4, G5.
- F2. The judge sees only the first line of the graded text (`render_prompt`, line 57, `splitlines()[0]`). Breaks R1.
- F3. An empty graded text raises IndexError at the same line, and the exception stops the whole run. Breaks E5, R1.
- F4. The reply parser takes the first capital A, B or C anywhere in the reply, inside words included (lines 25 and
  63). Breaks P1, P2, P3 (a reply such as `CORRECT` gets grade C instead of a retry).

Replacement frozen before step 5: `audit/replacement/toyqa_replacement.py` sha256
`027e5aafab453a9df5af1b53553f46ff3bdf317c44ae16e46e0691022cc10928`. It was written from the contract; no stored
response had been read when it was frozen, so all 48 stored responses are held out from its development.

## Step 5. Model panel from the stored run (run between 2026-11-06T22:42:31Z and 22:45:53Z, recorded 22:45:53Z)

No compute: the panel is the stored run, 48 responses (4 models x 12 questions, one decode each, temperature 0) with
the recorded judge replies (call 1 and call 2 for each of 34 prompts). `python -I audit/scripts/panel.py` checked the
pins before and after (`pins: OK` both times) and wrote `audit/work/panel/`.

- Stored records before grading (`python -I audit/scripts/stored_records.py`, reasoning masked): 3 responses have
  `finish_reason` `length`, all `ibis-8b-think` (a08, a20, a40), and all three have reasoning that never closed;
  24 responses contain `<think>`, 21 contain `</think>`, none has `</think>` without `<think>` or more than one
  `</think>`; no graded text is empty or has more than one line; 2 graded texts exceed 300 characters (a19, a47).
- Scored coverage: 48/48 rows labeled by the grader, the reference, the replacement and every stage variant; every
  judged prompt of every pipeline is in `judge_replies.jsonl`. The reference and the replacement give the same label
  on all 48 rows.
- Grader versus the contract pipeline (= reference = replacement): 10 of 48 verdicts differ. F1 changes 3 (a08, a20,
  a40), F4 changes 7 (a09, a16, a22, a24, a32, a34, a35), F2 and F3 change none on this run.
- Judge repeat: call 2 repeats each of the 34 judgments; 1 prompt (a06) flips, B to A, and 1 call-1 reply (a32) has no
  grade. Rescoring the contract pipeline with call 2 first moves only puffin-13b, accuracy +8.3.
- Rerun of an answering-model configuration: not possible without compute; the judge repeat is the only rerun.

## Step 6. Result that would change the recommendation (pre-registered 2026-11-06T22:45:53Z, before any draw or review)

The step 7 recommendation will be to fix the grader: bring its four failing stages to the contract, which the
reference already implements. That holds if (a) the replacement passes every fixture, (b) it passes the property
tests, (c) scored coverage is complete, and (d) in a blinded review of the frozen round-1 sample the replacement's
error rate is lower than the grader's, with a 95% paired bootstrap interval (resampling within strata) for
grader minus replacement that excludes zero. (a) to (c) hold now; (d) needs the review, which this exercise does not run.

- If (d) fails (the paired interval includes zero or favours the grader), the recommendation becomes: admit the
  grader's verdicts for this run, and still fix F1 and F3, which break the task text whatever the review says.
- If the reviewers mark a gold target or alias as wrong, or a question as having two right answers, on 2 or more of
  the 12 questions, the recommendation becomes: replace the benchmark.

## Step 6.1-6.2. Round-1 sample drawn and frozen (2026-11-06T22:47:23Z)

`python -I audit/scripts/draw_sample.py`, seed 61106 (reruns give the same bytes). Population: the 48 verdicts of the
stored run, stratified by whether the grader's label differs from the replacement's: 10 disagreements, 38
agreements. Round 1 takes every case of both strata (48 cases, ids T01 to T48 in seeded order); reviewer B's order is
a second seeded permutation, in the draw record. All 48 responses are held out from the replacement's development
(it was frozen before step 5 and has not changed).

| Frozen file | sha256 |
|---|---|
| `audit/frozen/round1_cases.jsonl` (case id, question id, response-row sha256; no model, no verdict) | `1fa32c81e9ffd70e8ed8c4d3bdd71c475435820a386ad3c43ba2988e120d69fb` |
| `audit/frozen/round1_keys.jsonl` (response id, source model, stratum, every pipeline's label, judge grades) | `c74dac741e3d80f4961ee666689ea020ad765fa54947326e5104c9a61e1703a7` |
| `audit/frozen/round1_draw.json` (seed, script hash, stratum sizes, reviewer orders, the two hashes above) | `2840a1e70d5647a53ed1620ddfbb40b21de406031bff9cfb3c7a3029519ab757` |

`audit/pins/audit_files.sha256` lists these three files, `audit/CONTRACT.md` (still v1, `89cff564…`) and the
replacement (still `027e5aaf…`); `check_pins.py` verifies them on every run.

Steps 6.3 to 6.5 (batch rendering, two blinded reviews, error rates) were not run: this exercise allows no
subagents. No review exists, so `audit/frozen/` holds no review files.

## Step 7. Report (2026-11-06T22:54:16Z)

`audit/AUDIT.md`, sha256 `1c87a930e4624315a3551c2436ed39f4ac1bb64a4547ea8d47ac921455734f8a`. Final checks at
22:54:16Z: 247 tests `OK (expected failures=35)`, `pins: OK (9 case files, manifest, 60 rows, 5 audit files)`.

- Error rate: not measured (step 6 review not run). Floor from the stored run: 10 of the grader's 48 verdicts (20.8%)
  contradict the task text under every reading, given the recorded judge replies; 0 of 48 for the reference and the
  replacement.
- Score change, grader to contract (accuracy / cga / F, points): orca-7b −8.3 / −8.3 / −8.3; puffin-13b
  +16.7 / +13.3 / +15.6; heron-32b-think +8.3 / +9.1 / +8.7; ibis-8b-think −8.3 / −33.3 / −16.5, not-attempted rate
  −41.7, extraction failures 0 to 3. By F-score, puffin-13b and ibis-8b-think swap places.
- Findings: F1 (3 of 48 verdicts), F2 (0 of 48), F3 (0 of 48; stops the run when it fires), F4 (7 of 48), G1
  (unpinned chat templates and checkpoints). The reference is correct on F1 to F4.
- Decision entries: `D-multiple-candidates` (3 stored cases, judged inconsistently), `D-unlisted-equivalent`
  (none stored), `D-cut-off-answer` (1 stored case, a47).
- Recommendation: fix the grader (F1 to F4, as the reference does), pin the chat templates, send the decision entries
  to the maintainers; the pre-registered gate's review part is still open.

Errata to earlier entries, left unedited above:

- Steps 3 and 4: the properties draw 400 seeded cases each, except `prop_scores_ignore_row_order` (100) and the
  end-to-end `prop_not_attempted_rate_counts_only_grade_c` (50).
- Step 6 pre-registration: "its four failing stages" means the four findings F1 to F4, which sit in three stages
  (label mapping, prompt rendering, reply parsing). The gate itself is unchanged.
