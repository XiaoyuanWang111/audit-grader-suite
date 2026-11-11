# Audit record: ToyMath 1.0 grader (`case/grade.py`)

This file stands in for the task's issue (offline exercise, no tracker). It is
append-only: later entries add to it and do not rewrite earlier ones. Paths are
relative to the working directory W =
`<W>`.

## Step 1. Pinned inputs (from TASK.md, MANIFEST.sha256 and the run records only)

Recorded 2026-11-11 00:56 UTC, before the contract and before any grader code
was read. Command: `python -B audit/scripts/pin_inputs.py --rows` (prints
`ALL OK` when every case file matches the manifest).

| Input | Pin | Source |
|---|---|---|
| Grader under audit | `case/grade.py` sha256 `35e8eff6d1cdacf97d8b08aed2d58171466df5174aa1a8b172ceeb0ff5a05a6e` | MANIFEST.sha256 |
| Reference implementation | `case/reference/grade_ref.py` sha256 `46f8a70c5f1eaf886a3ff54bde2cd3271c9c8b6d7ec67f0b3c874eeffa4aa53a` (released with ToyMath 1.0) | MANIFEST.sha256, TASK.md |
| Dataset | `case/problems.jsonl` sha256 `976da248da1f45642778836a7e0a779b821b3366de1e3b6b55055633d03b7f18`, 12 rows | MANIFEST.sha256 |
| Prompt template | `case/prompt_template.txt` sha256 `05e1b62f677b071d290b087c2acefa59b7556ae84a71fbd3911b160ac293f71f`; `{problem}` replaced by the `problem` field, sent as the only user message, no system prompt, each model's own chat template | TASK.md |
| Stored run | `case/responses.jsonl` sha256 `f50586804ce1d72e637635472de1c034f10b32fe435eff6aa2ddb76d485b5964`, 48 rows, 4 models x 12 problems | MANIFEST.sha256 |
| Task text | `case/TASK.md` sha256 `bb4e1b0ae1fdee8239d84b1739d85bf9a9ac36b0f92c11d8a95cce133e48af7b` | MANIFEST.sha256 |
| Manifest | `case/MANIFEST.sha256` sha256 `8cd28ab69c93828970255ce40b5330de3f80436770b4492348ff1a94f22611d1` | computed |
| Generation settings | temperature 0.0 and `max_tokens` 256 on all 48 rows (record fields); no stop sequences; each model's own chat template; no reasoning block, no reasoning parser | `responses.jsonl` fields, TASK.md |
| `finish_reason` | 46 `stop`, 2 `length` | `responses.jsonl` field |
| Response extraction rule | the scoring rule in TASK.md (last line beginning with `Answer:`, `str.splitlines` line split); no reasoning-field merge, since no model emits reasoning | TASK.md |
| Grader dependencies | Python 3 standard library, 3.8 or later; runs offline | TASK.md |
| Audit interpreter | Python 3.12.10 (Windows) | `python --version` |

Row hashes: sha256 of canonical JSON (sorted keys, UTF-8, separators `,` and
`:`) over `problem_id, problem, answer` for problems and over all seven fields
for responses. The full list is printed by the command above; first and last:
p01 `9789e7a3274c…`, p12 `2e60524ba324…`, r01 `f74d0fe2952b…`, r48
`409c86ae358f…`. The audit also checked the reference answers by hand: all 12
are arithmetically right.

Unpinned or unverified (step 1 asks to report these):

- U1. The four models' revisions and chat templates are not pinned ("each
  model's own chat template", no revision or template hash). Location: the
  `model` field of `responses.jsonl` holds only a name. Verify with the serving
  config of the run, which is not in the case. Reported as finding G1.
- U2. The serving stack (name, version) is not recorded. Only the absence of a
  reasoning parser is stated. Part of G1.
- U3. The Python version that ran the evaluation is not recorded ("3.8 or
  later"). Behavior that differs across 3.8 to 3.12 (for example the 4,300-digit
  limit on `int()` from 3.11) would change verdicts only if the grader uses it;
  checked after the code is read.

## Step 2. Contract

- 2026-11-11 00:57 UTC: `audit/CONTRACT.md` sha256
  `45faba4f93144149a0c6b1aaeb9ac0f92c2c11ee51b79c20002ecfc165d8bd8c`, written
  from TASK.md only. No grader code (`case/grade.py`,
  `case/reference/grade_ref.py`) had been opened at this time.
- Decision entries in that version: `D-leading-whitespace`, `D-digits`,
  `D-surrounding-text`, `D-multiple-numbers`, `D-tolerance-boundary`,
  `D-no-number-label`. Proposals: reading A for each.
- Between 2026-11-11 00:57 and 01:01 UTC (clock not read at that moment):
  read `case/grade.py` and `case/reference/grade_ref.py`, after the hash above.
- 2026-11-11 01:01 UTC: held-out panel responses set aside with
  `python -B audit/scripts/holdout.py` (seed 20261111, 6 per model, ids only, no
  response text read): `audit/frozen/holdout_ids.txt` sha256
  `7c630e04e16bd6bfad15681ca49a1ccc905c12f2dfdac5444eb3304e8478710e`. Held out:
  r02 r03 r06 r07 r09 r10 r12 r15 r17 r19 r20 r21 r29 r32 r33 r36 r38 r39 r40
  r42 r43 r45 r46 r48. Done before any grader ran on the panel.
- 2026-11-11 01:01 UTC: contract amended (change log in the file, two entries:
  `D-surrounding-text` reading B restated as "the number alone"; reading C of
  `D-multiple-numbers` labelled `no_answer`). Reason: reading the reference
  showed the strict form of reading B, which the first wording did not state.
  Proposals unchanged. New sha256
  `56fab1ea4d5e182c4a1e76bc099fa349e133945e7147061f264c4e0d52814e8c`.

## Step 1, continued: inputs that only the code shows (recorded after the contract hash)

- Grader extraction (`case/grade.py`): `str.splitlines()`; answer line regex
  `^\s*Answer:(.*)$` per line (Python `\s` = `str.isspace()`, checked over all
  code points: 0 mismatches); number regex `-?\d+(?:\.\d+)?`, first match by
  `re.search` (`\d` = 680 Unicode Nd code points, all accepted by `Decimal`);
  no comma handling. Comparison `abs(a - r) <= 0.01 * max(1, |r|)` in
  `Decimal` at the default context (precision 28). Score
  `100 * correct / (correct + incorrect)`.
- Reference extraction (`case/reference/grade_ref.py`): `str.splitlines()`;
  `line.strip()` then `startswith("Answer:")`; rest `.strip()`, all commas
  removed, `fullmatch` of `-?\d+(\.\d+)?`; comparison `abs(a - r) <= 0.01` in
  `Decimal` (precision 28); labels `correct` and `incorrect` only; score
  `100 * correct / len(problems)`.
- U3 resolved in part: neither grader calls `int()` on response text, so the
  3.11 digit limit does not apply. Both use `\d`, whose code-point set follows
  the interpreter's Unicode database (15.0.0 on the audit's 3.12.10; Python
  3.8 ships 12.1.0, from memory, not checked offline), so under the graders'
  reading of `D-digits` a digit added after Unicode 12.1 is graded differently
  by version. Under the proposed reading (ASCII digits) this is moot.
- Neither grader has unit tests in the case.

## Steps 3 and 4. Fixtures, replacement grader, stress tests

Recorded 2026-11-11 01:10 UTC.

- Replacement grader `audit/replacement/grade_contract.py` v1, sha256
  `f25b47c1243275138d18e8e5ad5dababb7fa8387f052bf156a3cd84fb54cc4f8`, frozen
  here before it graded any panel response. One switch per decision entry;
  defaults are the proposed readings.
- Fixtures `audit/tests/fixtures.py` (86 fixtures: 20 finding, 23 decision, 43
  control), sha256
  `495dbb6ba4dd1b0f9d2ccd33083b0982e2b80a612645d29f8778e19c4bf5c2a6`. Tests:
  `python -B -m unittest discover -s audit/tests` -> 384 tests, OK, 51 expected
  failures (strict). `test_fixtures.py` `c129ed42f494…`, `test_properties.py`
  `6a78eb093627…`, `test_scores.py` `71794db49447…`, `properties.py`
  `37e2f126935f…`, `harness.py` `7d0b98887a1e…`.
- Repro inputs (`python -B audit/scripts/make_repro.py`): F1_commas
  `40e28a98f38c…`, F2_tolerance `f21f385c6654…`, F3_denominator
  `29d9794e45c6…`, F4_precision `ad9fa1153ea8…`, F5_unknown_problem
  `a89d7019aeb5…`, F5_null_response `3f0b87a2f17d…`, F6_duplicate
  `c7424ecdfc79…`, R1_double_comma `95c2ae5f9a4f…`, decisions `b2983f369d52…`.

Findings so far (details and counterexamples in `audit/AUDIT.md`):

- F1 grader, number extraction: commas are not ignored; `Answer: 2,250` (p03)
  reads 2, `incorrect`. Reference: correct.
- F2 grader, comparison: tolerance is `0.01 * max(1, |ref|)`, i.e. 1% for any
  reference above 1; `Answer: 15100` (p07) is `correct`. Reference: correct.
- F3 grader, score: `no_answer` and missing problems leave the denominator;
  1 correct + 11 without an answer line scores 100.0. Reference: correct.
- F4 grader and reference, comparison: the difference is computed at Decimal
  precision 28 and rounded before the tolerance test;
  `Answer: 0.010000000000000000000000000001` (p06) is `correct`.
- F5 grader and reference, run: an unknown `problem_id` (with an answer) or a
  non-string `response` raises and stops the whole run; no score is printed.
- F6 grader and reference, score: a second response from one model to one
  problem is counted again (grader `correct` 13 for 12 problems; reference
  108.3).
- R1 reference only, number extraction: every comma on the answer line is
  deleted before the number is matched; `Answer: 4,,86` (p02) reads 486.
- G1 protocol: model revisions, chat templates and the serving stack are not
  pinned (U1, U2).

Decision entries where the graders take a non-proposed reading: grader
`D-digits` B; reference `D-digits` B, `D-surrounding-text` B (strict),
`D-multiple-numbers` C (through the strict reading), `D-no-number-label` B (it
has no `no_answer` label). Both take A on `D-leading-whitespace` and
`D-tolerance-boundary`.

Stress tests: metamorphic edits (`python -B audit/scripts/property_matrix.py`,
37 edits x 12 problems): the grader breaks `thousands-commas` (p03, p07),
`shift-plus-0.02` (11 of 12 problems), `shift-plus-1` (5 of 12); the reference
breaks the 7 `D-surrounding-text` edits on all 12 problems; the replacement
breaks none. Fuzz (`python -B audit/scripts/fuzz.py 20000 1`): 0 exceptions in
any grader; grader differences from the replacement at its own readings F1 258,
F2 1521, F4 8; reference F4 3 and 270 accepted stray commas (R1 mechanism).
Content-free responses (`python -B audit/scripts/content_free.py`): no grader
gives `correct` on any of the 12 problems; their effect on scores runs through
F3.

## Step 5. Model panel (stored responses only, no generation)

Recorded 2026-11-11 01:13 UTC. No compute in this exercise: the 48 stored
responses are the panel (4 models x 12 problems, one greedy run each).

- Between 2026-11-11 01:10 and 01:13 UTC, dev half first: `python -B audit/scripts/panel.py dev
  --show` (24 responses not held out). Replacement differs from the grader on
  r26 only (F1); reference differs from the replacement on r35 only
  (`D-surrounding-text`). The dev half prompted no change to the replacement:
  v1 (`f25b47c12432…`) stays frozen.
- Full panel: `python -B audit/scripts/panel.py all`. Verdict files:
  `audit/panel/all_table.jsonl` `b25d99e9acea…`, `all_grader.jsonl`
  `a827b90872ad…`, `all_reference.jsonl` `cd5ef5502d63…`,
  `all_replacement.jsonl` `d3260a02b90c…`.
- Stored records: `finish_reason` 46 `stop`, 2 `length` (r12 delta-8b p03,
  r36 delta-8b p09; both end mid-reasoning without an answer line); no
  reasoning markers; no duplicate or unknown (model, problem) pairs; 45 of 48
  responses have an answer line.
- Scored coverage 48/48 for all three graders.
- Score-level disagreements: grader vs replacement r10, r26 (both F1:
  `Answer: 2,250`, `Answer: 15,000`); reference vs replacement r03, r07, r19,
  r35 (`D-surrounding-text`: `$3.50`, `486 students`, `72 km/h`,
  `28.80 dollars`). F1 also changes the grader's extracted number on r09
  (`1,800` read as 1) without changing the verdict.
- Scores (grader as printed / reference / replacement): alpha-7b 75.0 / 75.0 /
  75.0; beta-14b 83.3 / 100.0 / 100.0; delta-8b 33.3 / 25.0 / 25.0; gamma-32b
  100.0 / 66.7 / 100.0. Replacement minus grader: 0, +16.7 (F1, two problems),
  -8.3 (F3: delta-8b's 3 `no_answer` responses leave the grader's denominator,
  3/9 instead of 3/12), 0.
- F2, F4, F5, F6, R1: no panel response triggers them (no grader `correct`
  whose exact difference exceeds 0.01; no row errors).
- Rerun: not available (one stored run per model, no compute). The grader
  itself is deterministic: two runs on the panel give byte-identical output.
- Not an RL reward, so no false-reward count; for reference, the grader's 34
  `correct` verdicts include 0 that the contract contradicts, and its 14
  non-correct verdicts include 2 that it does (r10, r26).

## Step 6. Blinded review

### 6.0 Result that would change the recommendation (recorded 2026-11-11 01:14 UTC, before any review)

Recommendation from steps 3 to 5: fix the grader by adopting the replacement's
behavior for F1 to F6. The review round can change it only as follows.

- The round's population is the 24 held-out responses. The grader and the
  replacement give different labels on exactly one of them (r10,
  `Answer: 2,250`, p03), so that is the whole disagreement stratum, and 23
  responses form the agreement stratum. Every case is drawn.
- Adopting the replacement needs (a) every fixture passed (holds: 86 of 86),
  (b) complete scored coverage (holds: 48 of 48), and (c) a lower error rate
  than the grader, with a paired 95% bootstrap interval that excludes zero.
  In this round the paired difference comes from r10 alone, so (c) holds if
  and only if the consensus on r10 is `correct`.
- If the consensus on r10 is not `correct` (the reviewers do not read
  `2,250` as 2250 under rule 2), F1 becomes a decision entry rather than a
  finding, and the recommendation drops the F1 change. F2, F3, F4, F5 and F6
  do not depend on this round (no held-out response triggers them).
- No result of this round can show an error rate below 2% for either grader:
  with 23 agreement cases and no error, the zero-error bound is
  (23/24) x (1 - 0.025^(1/23)) = 14.2%. Admitting the grader unchanged would
  need a larger panel, and F2 and F3 rule it out regardless.

### 6.1 and 6.2 Sample drawn and frozen (2026-11-11 01:14 UTC, no review has started)

- Script `audit/scripts/draw_sample.py` (sha256 `37cd8506d7b6…`), seed 61111
  (case ids and reviewer A's order), seed 61112 (reviewer B's order).
- Population: the 24 held-out responses. Strata (grader label vs replacement
  label): disagree, population 1, drawn 1 (r10); agree, population 23, drawn
  23. Grader/replacement/reference label triples in the sample: 15
  correct/correct/correct, 3 incorrect/incorrect/incorrect, 3
  correct/correct/incorrect (reference strict reading), 2
  no_answer/no_answer/incorrect (the two truncated responses), 1
  incorrect/correct/correct (r10). 6 cases per model.
- Frozen case list `audit/frozen/round1_sample.txt` sha256
  `3cc353523a9815dbb0e0e82867fcdf5c56fbe917f1a39846f012b64450e7e74b`.
- Keys (source model and every grader's verdict) `audit/frozen/round1_keys.jsonl`
  sha256 `2c25c0fd89af5dbcc8c4ee7ad3fc4f845eaa454933c27e365c357475f534f2ca`.
- Blinded cases `audit/frozen/round1_cases.jsonl` sha256
  `3f5a36dcd43c2b15ae5f57381f0219c1b7ba73f42d70f59cd72df1793ed63dbd`.

### 6.3 Batches rendered

- `audit/frozen/round1_batch_A.md` sha256
  `e42923fedfa48806a1f0e56624c45081ea9113944bb4826094631cbf12ec88ff`,
  `audit/frozen/round1_batch_B.md` sha256
  `b0a5dddc2f592d7601230c2e6698c00038d7e36215bf7036e2b838d362b8fa16`. Each case
  shows an opaque case id, the check's name and text, the prompt, the
  reference answer, and the response between begin and end markers; no model,
  response id or verdict (checked by grep).
- Helper `audit/frozen/show_case.py` sha256 `caf8f5447c30…`; reviewer prompt
  `audit/frozen/reviewer_prompt.md` sha256 `7d402ee02820…`.

### 6.4 and 6.5 Not run

This exercise cannot start subagents, so no reviewer has labelled the round,
and no error rate, interval, kappa or confusion matrix exists. To run it: give
two separate reviewer runs `audit/frozen/reviewer_prompt.md` with batch A and
batch B respectively, write their labels to `audit/frozen/reviews/`, and score
them against `round1_keys.jsonl` as step 6.5 describes.

## Step 7. Report

- 2026-11-11 01:18 UTC: report `audit/AUDIT.md` (sha256
  `2d0ced5f1d9dea73551c2b75a54a8121623910c5ef0a5e37d35cbae7c35f7098`).
  Recommendation: fix the grader (F1 to F6; pin the inputs in G1). Blinded
  error rate not measured (step 6 not run).
- Final checks at that time: `python -B -m unittest discover -s audit/tests`
  -> 384 tests OK, 51 expected failures; `python -B audit/scripts/pin_inputs.py`
  -> ALL OK (no case file changed, no bytecode under case/);
  `python -B audit/scripts/check_report_commands.py` -> 13 commands, 0 differ.
