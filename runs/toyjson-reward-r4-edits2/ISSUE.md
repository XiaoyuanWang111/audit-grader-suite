# Audit record: ToyOrders RL reward (`case/reward.py`)

This file stands in for the task's issue (offline exercise: no issue tracker, repository, Hugging Face dataset or job
launcher). Entries are appended in order; times are UTC, read from `date -u` in the same step as writing them.

## 1. Pinned inputs (2026-11-11T01:46:43Z)

Produced by `python -B audit/pin_inputs.py --write` (script sha256 `7abb586d6372…`, output `audit/pins.json` sha256
`89e2e011163be9d0fcba68f314c8519b8905dbee2324c74af74b4a26611f0b38`). Every case file matches `case/MANIFEST.sha256`;
no file uses CR bytes.

| Input | Pin |
|---|---|
| Grader | `case/reward.py` sha256 `e8cbb5566d04077449430f4bd3ef184f9f509afc34762fc89b8e46e0988f2362` (no commit: there is no repository) |
| Reference implementation | none exists (TASK.md: "There is no reference implementation of the reward") |
| Dataset | `case/orders.jsonl` sha256 `f6a5d0a2a4d72fa8658b6160679d757bddda7105449b18757029e9e1e92e20bf`, 12 rows; one sha256 per row in `audit/pins.json` (`orders_row_sha256`), e.g. `o01` `32abe6f65ab4…` |
| Prompt rendering | `case/prompt_template.txt` sha256 `11d2c94c0b96d8461b6106e6ad793f9e8822ef0b4c7797fef044581bba2fc02e`, `{email}` replaced by the order's `email`, sent as the only user message (TASK.md). The template contains other braces (`{"sku": …}`), so the substitution must be a literal replace, not `str.format` |
| Stored rollouts | `case/responses.jsonl` sha256 `d343e478c3a61d5e1b0c57919e2ed30672fcae620e97c9dcf82383e0f77e5753`, 48 rows, 12 per checkpoint `step-0000`, `step-0200`, `step-0400`, `step-0600`; one sha256 per row in `audit/pins.json` (`responses_row_sha256`) |
| Generation settings in the records | `temperature` 1.0 and `max_tokens` 256 on all 48 rows |
| Response extraction | the whole `response` string (TASK.md names no reasoning marker or reasoning field) |
| Reward invocation | the trainer imports `reward.py` and calls `reward(response, reference)` with `reference` from `json.loads(line, parse_float=Decimal)`; offline CLI `python reward.py [--responses …] [--out …]` |
| Task text | `case/TASK.md` sha256 `ee70972e4cbaedcd05be184ee761d7a6f4432edd212acd24ff5ef2d94593bf34` |
| Audit interpreter | CPython 3.12.10 (Windows 11, AMD64), `sys.get_int_max_str_digits()` 4300, recursion limit 1000 |

Unpinned or unverified (each with where it would be verified):

- Python version: TASK.md says only "the Python 3 standard library". Unpinned (finding G1 below).
- Policy model and checkpoint weights, chat template, stop sequences, top_p, serving stack: no field in
  `responses.jsonl` records them. Unverified; they would be verified from the training run's configuration (not
  provided).
- "None was truncated" (TASK.md): the records have no `finish_reason` or token count. Unverified; it would be verified
  from a per-rollout `finish_reason` field, or by re-tokenizing each `response` with the policy's tokenizer and
  checking it is under 256 tokens.
- The trainer's prompt renderer and the trainer's call site of `reward()`: not provided. Unverified; the contract
  takes TASK.md's description.

## 2. Contract (2026-11-11T01:47:27Z)

`audit/CONTRACT.md`, version 1, sha256 `d3a81e334d792b646d7024ea89a9e54798660d6af99cb6e53cbba98b402b6495`, recorded at
2026-11-11T01:47:27Z.

Process deviation, disclosed: the grader code `case/reward.py` was opened in the same step as `case/TASK.md`, before
the contract was written, and `case/responses.jsonl` was read in full before the contract too. The contract was
written from the TASK.md and prompt text, but it was not written blind to the code. No code experiments were run
before the hash above was recorded.

### Decision entries (version 1 of the contract)

The grader's reading column was filled at 2026-11-11T01:57:18Z from the decision fixtures (step 3).

| Id | Proposed reading | Grader's reading | Fixtures |
|---|---|---|---|
| `D-whitespace` | Python `str.strip()` whitespace | proposed (A) | `answer:e79904ef5e29e976`, `answer:978017d532252365`, `customer:44ae1f3195228d07` |
| `D-fence-tab` | tab allowed after the tag | proposed (A) | `answer:7ce335eb306b3203` |
| `D-crlf` | `\r\n` ends a line | **other (B)**: a CRLF fenced answer gets 0.0 | `answer:12d1c458b72de9ec` |
| `D-json-constants` | `NaN`/`Infinity` parse; such a total scores 0 | proposed (A) | `total:cf53ca1a4079c7d8`, `total:1aa61bd040c6658f` |
| `D-qty-decimal` | `2.0` is not an integer | **other (B)**: `2.0` and `2e0` match `qty` 2 | `items:2eff2dbf3a9f5f7b`, `items:d06634d92ba01a40` |
| `D-qty-bool` | `true` is not an integer | proposed (A) | `items:0b4650fd6483fc5b` |
| `D-total-boundary` | inclusive | proposed (A) | `total:9e173617b36d501d`, `total:0abdc1577d47d0fa` |

## Inputs that only the code shows (recorded 2026-11-11T01:57:18Z, after the contract hash)

- Extraction rule: `FENCE = ```(?:json)?[ \t]*\n(.*)\n``` ` (DOTALL), `fullmatch` on `response.strip()`; the group is
  `str.strip()`ped and decoded with `json.JSONDecoder(parse_float=Decimal).raw_decode`, whose end index is discarded.
- `total_score` subtracts in the caller's thread-local `decimal` context (default: precision 28, `Overflow`,
  `InvalidOperation` and `DivisionByZero` trapped). Nothing pins that context (finding G2).
- JSON integers go through `int()`, which refuses more than 4,300 digits (`ValueError`) on Python 3.11+ and the
  3.7.14/3.8.14/3.9.14/3.10.7 security releases, unless `PYTHONINTMAXSTRDIGITS` or `-X int_max_str_digits`
  changes the limit; neither the version nor that setting is pinned (G1). (Corrected 2026-11-11T02:00:34Z: the first
  entry said "since Python 3.11" only.)
- The offline CLI rounds each reward to 4 decimals before averaging; the trainer receives the unrounded float.

## Replacement grader (frozen 2026-11-11T01:54:48Z)

`audit/replacement_reward.py` sha256 `8de793c1dd947308683e7f2952410bba6addfd20f321648e5f7ab587fd218d90`, written from
the contract with one switch per decision entry; modes `proposed` (every proposed reading) and `fixes_only` (every
switch at the grader's reading, so each difference from the grader is a defect fix). It was written before it graded
any stored rollout and has not changed since; no panel result was used to change it, so no held-out split was needed
for it.

Fixtures: `audit/tests/fixtures.py` (102 fixtures: 67 controls, 23 finding fixtures, 12 decision fixtures across 7
entries), tests `audit/tests/test_fixtures.py` and `audit/tests/test_properties.py`; run
`python -B -m unittest discover -s audit/tests`: 390 tests, OK, 32 strict expected failures (23 finding fixtures,
3 decision fixtures tested against the proposed reading where the grader takes the other one, 6 property tests). The replacement passes every fixture in both modes and under each decision's other reading.

## Findings (recorded 2026-11-11T01:57:18Z)

Shares are over the 48 stored rollouts (step 5). No reference implementation exists, so no finding has a reference
status.

| Id | Stage or check | Defect | Fixtures | Panel share |
|---|---|---|---|---|
| F1 | C1 answer extraction | Text after the first JSON value is ignored (`raw_decode` end index discarded), bare or inside a fence; contract: reward 0.0 | 6, e.g. `answer:97e0fa751297a94a` | 6/48 rollouts (j05, j08, j20, j37, j40, j47) get 1.0 instead of 0.0 |
| F2 | C4 items | Score divides by the number of reference items, not max(reference, answer items); duplicate or extra items cost nothing | 6, e.g. `items:83bed4a666b94e20` | 5/48 (j04, j16, j18, j32, j41) get 1.0 instead of 0.875-0.9375 |
| F3 | C1 / C8 | A top-level value that is not an object (array, string, number, `true`, or a leading number such as `1. {...}`) raises `AttributeError` | 5, e.g. `answer:93751ec6a097e138` | 0/48 |
| F4 | C1 / C8 | `json` errors other than `JSONDecodeError` escape: `RecursionError` (deep nesting), `ValueError` (integer over 4,300 digits) | 2 | 0/48 |
| F5 | C5 / C8 | `decimal.Overflow` on a total with a huge exponent, e.g. `1e999999999` | 2 | 0/48 |
| F6 | C5 total | The distance is rounded to 28 significant digits before the comparison, so a total 1e-31 outside the tolerance scores 1 | 2 | 0/48 |
| G1 | Pinned inputs | Python version and its integer-string limit unpinned ("Python 3 standard library"). The F4a input raises `ValueError` under the default limit and scores 0.9 under `-X int_max_str_digits=0` or `PYTHONINTMAXSTRDIGITS=0` (corrected 2026-11-11T02:00:34Z; the first entry tied it to Python >= 3.11 only) | `answer:0300e40cc038df78` | 0/48 |
| G2 | Pinned inputs | The total's verdict depends on the caller's `decimal` context; with precision 9, total 29.975000000001 on o02 scores 1 (`audit/g2_decimal_context.py`) | none | 0/48 under the default context |
| G3 | Harness | No exception guard: one raising response stops the CLI run with no table (`audit/counterexamples/G3.jsonl`); the trainer's handling is unverified | n/a | 0/48 |

Every difference between the grader and the replacement's `fixes_only` mode on the fixtures, the panel and 8,000 fuzz
inputs is reproduced by re-enabling a subset of F1-F6 (`python -B audit/classify.py`: 8,150 cases, 0 unexplained).

## Step 4 (2026-11-11T01:57:18Z)

`python -B audit/stress.py --write` (`audit/stress_results.json`): no reference implementation, so no reference
comparison and no reference unit tests; the grader has no tests of its own. Metamorphic properties: the grader passes
all 11 ignored-edit properties and violates 6 of 15 forbidden-edit properties (numbered labels 48/48 and wrapping in
a list 24/24 by raising, F3; full stop after the answer and a trailing sentence 24/48 each, F1, only on unfenced
answers; a duplicated last item and an extra shipping item 48/48 each, F2). The replacement violates none. Fuzz (seed
20261111, 2,000 inputs per generator): grader exceptions 370 (random text), 19 (mutated correct answers), 1,385
(random JSON values), 774 (random order objects); replacement exceptions 0. Content-free responses: all score 0.0
under both graders, except `[]`, `""` and `0`, which raise in the grader (F3).

## Step 5 panel (2026-11-11T01:57:18Z)

`python -B audit/panel.py --write` (`audit/panel/verdicts.jsonl` sha256 `a3095ae8d2a6…`, `audit/panel/summary.json`
sha256 `a3a4c4d8176a…`). No generation (no compute); the 48 stored rollouts are the panel; a generation rerun was not
possible; regrading is deterministic (48/48 identical). Scored coverage: 48/48 for every grader.

| Checkpoint | Grader mean | Replacement (fixes only) | Replacement (proposed) | Full rewards g / f / p |
|---|---|---|---|---|
| step-0000 | 0.756 | 0.584 | 0.584 | 5 / 2 / 2 |
| step-0200 | 0.971 | 0.960 | 0.929 | 10 / 9 / 7 |
| step-0400 | 0.979 | 0.896 | 0.896 | 11 / 10 / 10 |
| step-0600 | 1.000 | 0.726 | 0.726 | 12 / 6 / 6 |
| all 48 | 0.926 | 0.791 | 0.784 | 38 / 27 / 25 |

False rewards: 11 of the grader's 38 full rewards (F1 6, F2 5) are not full under the contract with the grader's
decision readings, 13 of 38 with the proposed readings (adding j02 and j46, `D-qty-decimal`). The grader never
rewards a rollout below the contract.

## Step 6 pre-registration (recorded 2026-11-11T01:57:18Z, before the sample was drawn)

Review unit: one rollout; label: its reward under the reward specification (a value in [0, 1], or `ambiguous` with a
lean). Error: a grader reward that differs from the consensus reward by more than 1e-4.

Result that would change the step 7 recommendation ("fix: replace `case/reward.py` with the replacement in proposed
mode, after the maintainers settle the decision entries"): the recommendation stands only if the replacement passes
every fixture (true now), scored coverage is complete (true now), and the replacement's error rate is lower than the
grader's with a paired 95% interval that excludes zero. If the paired interval includes zero, the recommendation
falls back to fixing F1-F6 in the grader without adopting the replacement. If the consensus gives a trailing-text
response (F1 cases) or a duplicate-item response (F2 cases) the grader's reward, that finding is reopened as a
possible decision entry before any recommendation.

## Frozen samples (recorded 2026-11-11T01:59:05Z, before any review)

Round 1, drawn by `python -B audit/sample.py` (sha256 `a0bf465bc0b9…`), seed 20261111; reviewer B's order uses seed
20261112. Population: the 48 stored rollouts. Strata (grader vs replacement in proposed mode): disagree 13 of 48,
agree 35 of 48; every rollout of both strata is sampled (census), so the round covers the whole panel. No round has
been reviewed: step 6.4 is not run in this exercise (no subagents).

| File | sha256 |
|---|---|
| `audit/frozen/round1/cases.jsonl` (the case list) | `1769fdd9a2af4d2c6fcfefd25f7c6ae4d55256399ad8474495de53f911ce47dc` |
| `audit/frozen/round1/keys.jsonl` | `bbbf2b8ccba8218fcc163a4a4ff4fa542160084b151396f4f76d73ba1f4fd4b1` |
| `audit/frozen/round1/batch_A.md` | `9668680ca5814ba5c81247b064591711fbfaaf7370f7ef7c6e25e3dca65b1319` |
| `audit/frozen/round1/batch_B.md` | `97eab203c3ba8c24b12db59d129f94933316aae586487950c4b582297d35c204` |
| `audit/frozen/round1/reviewer_prompt_A.md` | `a1e0d86264a14710de79882eba262f8ae0e1d79a5838a8b2065c9122a2b2c508` |
| `audit/frozen/round1/reviewer_prompt_B.md` | `c1847fea34f2342c7b9b37e284c6f84478bb12913333ca8a749ee05b86a44955` |
| `audit/frozen/round1/show_case.py` | `6946101b859dab1179cd8e1e9f1f37048b4b3df0d73d2f108a7daab2d2496e3c` |
| `audit/frozen/round1/sample_meta.json` | `247ac0003860d9729c5e52f83a670df31aed7f4853679daf2365d851159e6cc8` |

## Step 7 report (recorded 2026-11-11T02:03:54Z)

`audit/AUDIT.md` sha256 `607342ff4f036e8ab6b4db814a1e4c6b88f6713fe1984b2792d4f2189a5cc5eb`. Recommendation: fix
the grader (adopt the replacement after `D-crlf` and `D-qty-decimal` are decided, or at minimum fix F1-F6 and
G1-G3), then regrade the training run's checkpoints. The error rate is unmeasured, because step 6.4 was not run;
gate conditions (1) and (2) hold and (3) is open.

Final checks at 2026-11-11T02:03:54Z: `python -B -m unittest discover -s audit/tests` reports 390 tests, OK, with 32
expected failures; `python -B audit/check_report_commands.py` passes 30/30; every case file still matches
`MANIFEST.sha256`; the frozen case list and keys hashes are unchanged; no bytecode was written.

Audit files at the time of the report:

| File | sha256 |
|---|---|
| `audit/CONTRACT.md` | `d3a81e334d792b646d7024ea89a9e54798660d6af99cb6e53cbba98b402b6495` |
| `audit/replacement_reward.py` | `8de793c1dd947308683e7f2952410bba6addfd20f321648e5f7ab587fd218d90` |
| `audit/tests/fixtures.py` | `18baaf63ec85757e8d068935fa55ac9088e312f1dd901ec28685573bb6b0f0b6` |
| `audit/tests/test_fixtures.py` | `c000c9803fc11ae9f9f83c64e6235c24cec715dc7e3572dd37aafa1ddc3a1d11` |
| `audit/tests/test_properties.py` | `0d28188056124245a798d7b40ce6a1750583035122f1822090b8eda2604aceb6` |
| `audit/stress.py` | `f167ff6ae1cbc3375d8f65f8db5de6d1e9d76f48374c234a9ccbcbc3ceef6cf2` |
| `audit/classify.py` | `6c4b91de99d5c767d23556690a7a9de0a8a4d20b5b1b2a3e7c65adaa4e8cae13` |
| `audit/panel.py` | `ae49ed641e895e8f0f1971952f6bbb2c1741956652e69578565daef940668ef5` |
| `audit/panel/verdicts.jsonl` | `a3095ae8d2a6f8588345c67618aaeeda785521cf8d68b83482251e8706cb2da1` |
| `audit/check_report_commands.py` | `7e4a5fdf49f4a5380edb2f345e9df2ef61e0e36db73df2efdd53655aa23fa704` |

The `needs_int_limit` skip condition on fixture `answer:0300e40cc038df78` replaced the earlier `min_py=(3, 11)`
condition at 2026-11-11T02:00:34Z, for the reason given under G1. The fixture's label and id did not change.
