# Audit of the ToyOrders reward (`case/reward.py`)

Written 2026-11-07T00:23Z (UTC). Record of inputs, hashes and decisions: `audit/ISSUE.md`.
Contract: `audit/CONTRACT.md`, sha256 `8f3b0839…cb65ba80`, recorded before the grader was read.

**Recommendation: fix the grader.** The specification is clear on every defect that changes
a verdict on the stored rollouts, and each fix is a small local change (listed at the end).
Re-score the training run with the fixed reward before reading anything into its curve.

## Error rate and effect on scores

The blinded review (step 6) did not run, so there is no consensus-based error rate. The
rates below compare the grader with the replacement grader (`audit/replacement/reward_contract.py`),
an implementation of the contract. "Fixes only" runs the replacement with the grader's own
reading of every decision entry, so each difference from the grader is a defect fix.
"Proposed" uses the audit's proposed readings.

- On the 48 stored rollouts, the grader's reward differs from fixes only on **11 of 48
  (22.9%)**, and from proposed on 13 of 48 (27.1%). Every difference is upward: the grader
  never scores a rollout lower than the contract does.
- As an RL reward: **11 of the grader's 38 full rewards (28.9%) are false rewards** (13,
  34.2%, under the proposed readings). 14.6% of the grader's total reward is in excess of the
  contract's.
- Mean reward falls from 0.926 to 0.791 under fixes only (-0.135, 95% interval [-0.227,
  -0.052], resampling rollouts within checkpoints).
- The grader and the contract rank the checkpoints differently:

| Checkpoint | Grader | Fixes only | Proposed | Fixes only minus grader [95% CI] | Full rewards: grader / fixes only / proposed |
|---|---|---|---|---|---|
| step-0000 | 0.756 | 0.584 | 0.584 | -0.172 [-0.417, +0.000] | 5 / 2 / 2 |
| step-0200 | 0.971 | 0.960 | 0.929 | -0.010 [-0.031, +0.000] | 10 / 9 / 7 |
| step-0400 | 0.979 | 0.896 | 0.896 | -0.083 [-0.250, +0.000] | 11 / 10 / 10 |
| step-0600 | 1.000 | 0.726 | 0.726 | -0.274 [-0.521, -0.049] | 12 / 6 / 6 |

  The grader rises at every checkpoint and gives step-0600 a perfect score. Under fixes only,
  step-0200 is best and step-0600 is 0.235 lower (95% interval [-0.488, -0.009], 12 orders
  paired). Each checkpoint has one rollout per order and no rerun exists, so sampling noise
  is measured only by the bootstrap over orders.
- What the gap is made of: two defects, F1 and F3. Rollouts that only these defects reward:
  3 of 12 at step-0000, 1 at step-0200, 1 at step-0400, **6 of 12 at step-0600**. At
  step-0600, three rollouts append a sentence after the JSON (F1) and three add extra items
  (F3): a duplicated line (j04), a second line for a product with another quantity (j16),
  and both quantities listed for each product (j32). The grader pays all six in full. One
  rollout pair illustrates the drift: for order o05, step-0000 put the shipping fee in an
  extra key (penalized, 0.9), and step-0200 put it in an extra item `SHIPPING` (unpenalized,
  1.0). These are single rollouts, not a measured trend.
- Scored coverage is 48 of 48: no stored rollout raises. But the grader raises on 5,094 of
  20,000 fuzz cases (a count that depends on the fuzzer's inputs), and one such response
  stops the command-line run with no output (F2, F4, F5).

Pass rates per check on the 48 rollouts. A response that fails the answer gate scores 0 on
every field, so the grader's F1 passes raise its field rates too.

| Check | Grader | Fixes only | Proposed |
|---|---|---|---|
| answer gate | 46 of 48 | 40 of 48 | 40 of 48 |
| customer | 45 | 39 | 39 |
| date | 44 | 38 | 38 |
| items, mean score | 0.951 | 0.786 | 0.755 |
| total | 44 | 38 | 38 |
| extra keys, mean count | 0.042 | 0.042 | 0.042 |

## Findings

There is no reference implementation, so no finding has a status there. Each counterexample
is an exact input (a Python string literal) graded against the reference of the named order.
`python -I -B audit/scripts/repro.py <id>` prints the grader's verdict for it, and, for F1
to F7 and G2,
`cd case && python -I -B reward.py --responses ../audit/tests/counterexamples/<id>.jsonl`
reproduces it through the grader's own command line (it prints the reward as the mean, or
the traceback). The fixture ids are in `audit/tests/fixtures.py` and
`audit/runs/fixture_table.md`.

| Id | Check or stage | Counterexample (order) | Grader | Contract | Share of panel verdicts |
|---|---|---|---|---|---|
| F1 | `answer`: parser | `'{"total":24}x'` (o10) | 0.25 | 0.0 | 6 of 48 (12.5%) |
| F2 | `answer`: type check | `'0'` (o01) | raises `AttributeError` | 0.0 | 0 of 48 |
| F3 | `items` | `'{"items":[{"sku":"EF-310","qty":3},0]}'` (o02) | 0.25 | 0.125 | 5 of 48 (10.4%) |
| F4 | `total` | `'{"total":1e1000000}'` (o01) | raises `decimal.Overflow` | 0.0 | 0 of 48 |
| F5 | `answer`: parser | `'{"a": ' + '[' * 2997 + ']' * 2997 + '}'` (o01) | raises `RecursionError` | 0.0 | 0 of 48 |
| F6 | `total` | `'{"total":64.4949999999999999999999999999999}'` (o01) | 0.25 | 0.0 | 0 of 48 |
| F7 | `answer`: fence | `'```json\t\n{"total":24}\n```'` (o10) | 0.25 | 0.0 | 0 of 48 |
| G1 | inputs | not a verdict: the run records omit the policy and decoding settings | | | all 48 |
| G2 | inputs | `'{"total": ' + '1' * 4301 + '}'` (o01) | raises `ValueError` on CPython 3.11+, 0.0 before | 0.0 | 0 of 48 |
| G3 | inputs | o01's correct answer with `"total": 64.5051`, run with `decimal.getcontext().prec = 1` | 1.0 (0.75 at the default context) | 0.75 | 0 of 48 at the default context |

In the fuzz run, the fix for each finding alone changes the grader's verdict on this many of
the 20,000 cases: F1 2,949, F2 5,085, F3 1,992, F4 9, F7 126 (a case can count under two).
F5 and F6 need inputs the fuzzer does not generate and appear in fixtures only.

- **F1. Text after the JSON object is ignored.** `parse_answer` uses
  `JSONDecoder.raw_decode`, which parses the first JSON value and returns without checking
  what follows. A sentence after the object, a second object, a second fenced block, a stray
  `}`, or a note after the object inside the fence all keep the object's full score.
  Contract 1.3: "a single JSON object with nothing around it but whitespace; otherwise the
  reward is 0.0". (Text after a closing fence is caught, by accident: the fence pattern then
  fails and parsing starts at the backticks, as for rollout j25.) Panel: j05, j08, j20, j37,
  j40, j47, each 1.0 instead of 0.0. Fixtures: `answer:c7668539d879` (smallest),
  `answer:dd145da60d75` and five more; property tests `text_after_object`,
  `text_inside_fence_after_object` and `second_copy` fail on all 12 orders.
- **F2. A top-level value that is not an object raises.** When `raw_decode` returns a list,
  string, number or boolean, `reward` calls `.get` on it and raises `AttributeError`. That
  includes every response that starts with such a value, because of F1: `2 items: ...`,
  `"Maria Lopez"`, `true`, `NaN`, `[{...}]`. Contract 1.3 gives 0.0, and section 5 requires
  a float for every text. In the command line one such response stops the run before any
  output is written (`audit/tests/test_cli.py`, `test_one_bad_response_does_not_stop_the_run`);
  how the trainer handles the exception is not recorded. Fuzz: 5,085 of 20,000 cases.
  Fixtures: `answer:11390f2d6b59` (smallest) and five more.
- **F3. Extra answer items cost nothing.** `items_score` returns `matched / len(expected)`;
  the specification divides by "the larger of the number of reference items and the number
  of answer items". Duplicated lines, invented lines (`DELIVERY`, `SHIPPING`), elements that
  are not objects, and hedging (listing every plausible quantity) keep full item credit:
  listing `EF-310` with quantities 1 to 5 earns 1.0 (contract 0.8, `items:cf632d8ff30b`).
  Panel: j04, j16, j18, j32, j41, each 1.0 instead of 0.875 to 0.9375. Fixtures:
  `items:88e302a5e1a1` (smallest) and five more; property tests `extra_wrong_item` and
  `duplicated_item` fail on all 12 orders.
- **F4. An extreme exponent in `total` raises.** `abs(Decimal(value) - Decimal(expected))`
  overflows the decimal context for a total such as `1e1000000` (9 characters), and
  `decimal.Overflow` escapes. Contract section 5. Fuzz: 9 cases. Fixtures:
  `total:1eddd8169402` (smallest), `total:ec4078727109`.
- **F5. Parser errors other than `JSONDecodeError` escape.** Nesting of 2,997 levels or more
  raises `RecursionError` (CPython 3.12.10 on Windows; the limit varies by version and
  platform), and an integer of 4,301 digits or more raises `ValueError` on CPython 3.11 and
  later (G2). Contract 1.3 and section 5. Reaching 2,997 brackets in 256 tokens needs about
  12 brackets per token; whether the policy's tokenizer allows that is not recorded (G1).
  Fixtures: `answer:e47b38c65853`, `answer:61b335f2cb49`.
- **F6. The total comparison is rounded.** The subtraction runs at the context's 28
  significant digits, so a total just outside the 0.005 band can round onto it and score 1.
  The specification reads numbers exactly. Needs a total with 31 or more decimal places;
  negligible in practice. Fixtures: `total:9e787b9b6aad` (smallest), `total:33d89b7726af`.
- **F7. A tab after the fence tag is accepted.** The pattern allows `[ \t]*` after the tag;
  the text says "spaces may follow the tag", and the same item says "whitespace" where it
  means any whitespace. Fixtures: `answer:1ef757bb1da3` (smallest), `answer:9e344dbc0010`.
  Fixing the specification to allow tabs would close this finding as well.
- **G1. Generation inputs are not recorded.** The run records keep `temperature` (1.0) and
  `max_tokens` (256) only: no policy model or revision, tokenizer, chat template, stop
  sequences, `top_p` or reasoning parser, and no `finish_reason`, so "None was truncated"
  cannot be checked (the longest response is 203 characters, and none ends mid-JSON).
- **G2. The interpreter version is not pinned.** "Python 3 standard library" leaves the
  version open; F5's limits and the Unicode tables behind `str.casefold` and `str.strip`
  change with it. This audit ran CPython 3.12.10.
- **G3. The reward depends on the caller's decimal context.** The trainer owns the thread's
  `decimal` context; its precision decides F6-type rounding (with precision 1 the
  counterexample above passes), and its traps decide F4 (with the `Overflow` trap off, F4's
  input returns 0.0). `python -I -B audit/scripts/repro.py G3` shows both.

Not a finding: the command line rounds each reward to 4 decimals before the mean, the
full-reward count and the `--out` lines, while the trainer receives the unrounded float. No
reward that a 256-token response can earn rounds to 1.0, so no count changes.

## Decision entries

For the evaluation's maintainers. Each has a switch in the replacement grader.

| Entry | Question | Reading A | Reading B | Grader | Proposed | Panel effect |
|---|---|---|---|---|---|---|
| D-fence-newline | Do CR and CRLF end a line in the fence rule? | no: `'```json\r\n{...}\r\n```'` scores 0.0 | yes: it is scored as a fenced block | A | B | none (no response has a CR) |
| D-inner-whitespace | May non-JSON whitespace such as U+00A0 surround the object inside a fence? | yes: strip, then parse | no: parse as it is | A | A | none |
| D-qty-bool | Is `true` an integer equal to 1? | no | yes | A | A | none |
| D-qty-integral | Is `2.0` (or `2e0`) an integer equal to 2? | no: only a JSON integer | yes: any integral value | B | A | j02 1.0 to 0.875, j46 1.0 to 0.75 (both step-0200) |
| D-total-boundary | Does a total exactly 0.005 off score 1? | yes: inclusive | no | A | A | none |

The grader takes the non-proposed reading on two entries. Adopting the proposals changes
two panel verdicts, both through D-qty-integral (step-0200 mean 0.960 to 0.929). Reasons are
in `audit/CONTRACT.md`.

## Steps run

| Step | Status |
|---|---|
| 1. Pin the inputs | Run. Every case file is pinned by sha256 and checked before and after each run (`audit/scripts/pin_inputs.py --check`); per-row and per-prompt hashes in `audit/ISSUE.md`. No grader commit, dataset revision or run configuration exists beyond these files: G1 to G3. |
| 2. Contract | Run. Written from the prompt and the specification and hashed at 2026-11-06T23:57:08Z, before `case/reward.py` was opened. No later change. |
| 3. Fixtures | Run. 125 fixtures (31 pass, 31 near-miss, 63 fail) as tests in `audit/tests/`. The grader is wrong on 32, kept as strict expected failures (`unittest.expectedFailure`, since pytest is not installed; `pytest.mark.xfail(strict=True)` when it is). The replacement passes all 125 under every reading. |
| 4. Reference comparison and stress | Partly run. There is no reference implementation, so the comparison and the reference's unit tests were skipped, and the grader has no tests of its own. Run: 25 property tests over all 12 orders (the grader fails 6) and a fence metamorphic relation; a seeded fuzzer, 20,000 cases (`audit/scripts/fuzz.py`); the aggregation and clipping, and the command line's mean, full count, `--out` and rounding; content-free responses. |
| 5. Panel | Run on the 48 stored rollouts only. No compute, so no new responses and no rerun of a configuration; 24 rollouts were held out (seed 20261106) before any was read, and the replacement was frozen before grading. |
| 6. Blinded review | Not run: no reviewer runs can be started. Steps 6.1 to 6.3 were done: the pre-registered gate, the sample (all 24 held-out rollouts, 8 disagreements and 16 agreements, seed 20261108) frozen by sha256 `1a3fcf31…b47943dd`, and two batch files in different orders, a helper and the reviewer prompt in `audit/frozen/`. |
| 7. Report | This file. |

Skipped because this exercise has none of them: the issue tracker (`audit/ISSUE.md` stands
in), the repository's grader test directory and `manage-pr`, the research branch, the Hugging
Face dataset for frozen samples (`audit/frozen/` stands in), the job launcher, and
`docs/dev-guide/writing-style/issues.md`.

Content-free responses (step 4): the empty response, whitespace only, the restated prompt,
the echoed email and a plain-text restatement fail the answer gate and get 0.0. A schema
skeleton (`{"customer": "", ...}`) and an object of the prompt's placeholders pass only the
gate and get 0.0. The correct answer repeated three times passes every check and gets 1.0
(contract 0.0, F1).

## What would change the recommendation

Recorded in `audit/ISSUE.md` before the review. If the review runs, the recommendation
changes when: (1) the reviewers' leans side with the grader on 4 or more of the 7 sampled F1
and F3 disagreements (then reword the specification first); (2) the replacement's error rate
is not lower than the grader's with a paired 95% interval that excludes zero (then do not
adopt it); or (3) Cohen's kappa between the leans is below 0.6, or a quarter or more of the
verdicts are `ambiguous` (then rewrite the reward specification).

## The fix

1. Parse with `json.JSONDecoder(parse_float=Decimal).decode` on the extracted answer (F1),
   return 0.0 when the value is not a `dict` (F2), and treat any parse exception as a failed
   gate (F5).
2. Divide the items score by `max(len(expected), len(value))` (F3).
3. Compare the total exactly: `lo <= value <= hi` with `lo, hi` computed in a local context,
   and 0 for non-finite values (F4, F6, G3).
4. Allow only spaces after the fence tag, or change the specification to allow tabs (F7).
5. Count an exception as a grading failure, separately from model accuracy, so one response
   cannot stop a run.
6. Pin the interpreter version and record the generation settings and `finish_reason` with
   each rollout (G1, G2).
7. Decide D-fence-newline and D-qty-integral; the replacement implements both readings.

The replacement grader implements 1 to 4 (`audit/replacement/reward_contract.py`), and the
strict expected failures in `audit/tests/` mark what the fixed grader must pass.

## Reproduce

From `<run directory>`:

```text
python -I -B audit/scripts/pin_inputs.py --check
python -I -B -m unittest discover -s audit/tests -t audit/tests     # 306 tests, OK, 39 expected failures
python -I -B audit/scripts/repro.py                                 # every counterexample
python -I -B audit/scripts/fuzz.py --n 20000 --seed 7
python -I -B audit/scripts/panel.py                                 # step 5 tables
python -I -B audit/scripts/trajectory.py                            # checkpoint differences
python -I -B audit/scripts/draw_review_sample.py                    # step 6.1 to 6.3; seeded, rewrites audit/frozen/review_r1_* with the same hashes
```
