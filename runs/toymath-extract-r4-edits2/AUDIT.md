# Audit of the ToyMath 1.0 grader (`case/grade.py`)

Report for step 7, written 2026-11-11 01:16 UTC. The running record (pinned
inputs, contract hash, decision entries, findings, frozen-sample hashes) is in
`audit/ISSUE.md`. Every command below runs from the working directory W
(`<W>`) in Git Bash, and prints
what is shown under it.

**Recommendation: fix the grader.** Its scoring rule is clear, and every
defect found has a small code fix that the replacement grader
(`audit/replacement/grade_contract.py`) already implements and tests.

## Error rate and effect on scores

- **Blinded error rate: not measured.** Step 6 needs two reviewer runs, and
  this exercise cannot start them. The review round is drawn and frozen (24
  held-out responses, batches rendered), so it can run unchanged later.
- **Against the contract, as the replacement grades it, the grader gets 2 of
  the 48 stored verdicts wrong (4.2%).** Both come from finding F1: `Answer: 2,250`
  (r10) and `Answer: 15,000` (r26) are read as 2 and 15. The figure comes from
  the auditor's replacement, not from a blinded consensus.
- **Score effect on the stored run (replacement minus grader, in points):**
  alpha-7b 0.0, beta-14b +16.7 (83.3 to 100.0, F1 on two problems), delta-8b
  -8.3 (33.3 to 25.0, F3: its three responses without an answer line drop out
  of the grader's denominator), gamma-32b 0.0. No rerun exists to set these
  against run-to-run variation, but all graders score the same stored
  responses, so the differences come from grading alone.
- **Two defects are larger than this panel shows.** F2 accepts any answer
  within 1% of a reference above 1: an answer off by 0.02 is `correct` on 11
  of the 12 problems, and one off by 1 on 5 of them. F3 lets a model that
  leaves out the answer line on every problem it is unsure of score 100, as
  long as every answer it does give is correct.

| Model | Grader (as printed) | Replacement (contract) | Reference |
|---|---|---|---|
| alpha-7b | 75.0 | 75.0 | 75.0 |
| beta-14b | 83.3 | 100.0 | 100.0 |
| delta-8b | 33.3 | 25.0 | 25.0 |
| gamma-32b | 100.0 | 100.0 | 66.7 |

```text
$ python -B case/grade.py --out audit/repro/out/panel.jsonl && grep -E '"(r10|r26)"' audit/repro/out/panel.jsonl
model         correct  incorrect  no_answer   score
alpha-7b            9          3          0    75.0
beta-14b           10          2          0    83.3
delta-8b            3          6          3    33.3
gamma-32b          12          0          0   100.0
{"id": "r10", "model": "beta-14b", "problem_id": "p03", "extracted": "2", "verdict": "incorrect"}
{"id": "r26", "model": "beta-14b", "problem_id": "p07", "extracted": "15", "verdict": "incorrect"}
```

```text
$ python -B audit/replacement/grade_contract.py
model         correct  incorrect  no_answer  errors  missing   score
alpha-7b            9          3          0       0        0    75.0
beta-14b           12          0          0       0        0   100.0
delta-8b            3          6          3       0        0    25.0
gamma-32b          12          0          0       0        0   100.0
```

The reference (`case/reference/grade_ref.py`) is not a drop-in fix. It gives
gamma-32b 66.7 because it reads `D-surrounding-text` strictly: `Answer: $3.50`,
`Answer: 486 students`, `Answer: 72 km/h` and `Answer: 28.80 dollars` have no
number for it (r03, r07, r19, r35). It also shares F4, F5 and F6, and adds R1.

## Findings

Shares are over the 48 stored verdicts unless stated. "Fixture" names the
regression test in `audit/tests/fixtures.py`, whose id is
`final-answer:<16 hex>`. The contract is `audit/CONTRACT.md`.

| Id | Stage | Fixture or case | Contract it breaks | Share affected | In the reference |
|---|---|---|---|---|---|
| F1 | number extraction | `comma-2250` (`final-answer:9cd7efa8e6a3b42f`), panel r10, r26 | C2: "Commas in the number are ignored" | 2 verdicts (4.2%), 2 of 4 model scores; 1 more extracted value wrong without a verdict change (r09) | correct (it deletes commas) |
| F2 | comparison | `rel-tol-15100` (`final-answer:c83e94109519cc68`), `rel-tol-29` (`final-answer:c09572c94d73d5f3`) and 10 more | C3: "within 0.01 of the reference answer" | 0 of 48; property tests: a +0.02 shift passes on 11 of 12 problems, +1 on 5 of 12 | correct (absolute 0.01) |
| F3 | score aggregation | `test_scores.TestF3Denominator`, panel delta-8b | C4: score = correct / 12; rule 3 makes a response without an answer line incorrect | 1 of 4 model scores (delta-8b reported 8.3 points high); 3 verdicts left out of the denominator | correct (divides by 12) |
| F4 | comparison | `precision-zero` (`final-answer:5af6a2288b874e5e`), `precision-3.51` (`final-answer:2200f73f0e5a00dd`) | C3: exact decimal comparison | 0 of 48 (needs 29 or more significant digits) | present |
| F5 | run control | `test_scores.TestF5OneBadRowStopsTheRun` | C4: one row's exception must not decide other rows' verdicts | 0 of 48; when triggered, the whole run prints no score | present |
| F6 | score aggregation | `test_scores.TestF6Duplicate` | C4: a problem counts once per model | 0 of 48 (no duplicates stored) | present, and its score can exceed 100% |
| R1 | number extraction (reference only) | `double-comma` (`final-answer:1768756a422ef611`) | C2: a comma joins only digits on both sides of it | 0 of 48 | reference only |
| G1 | protocol (step 1) | `audit/ISSUE.md` U1, U2 | step 1: every input that can change a verdict is pinned | all verdicts depend on it | not applicable |

### F1. Commas are not ignored in the number

The grader's number regex is `-?\d+(?:\.\d+)?` with no comma handling, so it
reads the digits before the first comma. TASK.md rule 2: "Commas in the
number are ignored, so `12,500` and `12500` are the same number." The prompt
itself invites the format ("You may use commas as thousands separators (for
example 12,500)"). Three stored answers use it, and two of them lose a correct
verdict (r10, r26). Fix: join digits across a comma that has a digit on each
side, as `_scan_digits` in the replacement does.

Counterexample: `{"problem_id": "p03", "response": "Answer: 2,250"}`
(reference 2250, contract `correct`).

```text
$ python -B case/grade.py --responses audit/repro/F1_commas.jsonl --out audit/repro/out/F1.jsonl && cat audit/repro/out/F1.jsonl
model         correct  incorrect  no_answer   score
m1                  0          2          0     0.0
{"id": "F1-a", "model": "m1", "problem_id": "p03", "extracted": "2", "verdict": "incorrect"}
{"id": "F1-b", "model": "m1", "problem_id": "p07", "extracted": "15", "verdict": "incorrect"}
```

### F2. The tolerance is 1% of the reference, not 0.01

`is_correct` accepts `abs(answer - reference) <= 0.01 * max(1, abs(reference))`.
For a reference above 1 that is a relative tolerance: 150 on p07 (15000),
7.56 on p11 (756), 0.288 on p09 (28.8). TASK.md rule 4: "within 0.01 of the
reference answer". No stored answer falls in the gap. On a larger panel, the
grader's verdict file measures it: `correct` rows whose `extracted` value
differs from the problem's `answer` by more than 0.01. Fix: compare with 0.01.

Counterexamples: `{"problem_id": "p07", "response": "Answer: 15100"}` and
`{"problem_id": "p09", "response": "Answer: 29"}` (contract `incorrect` for
both; 29 is the rounding a model might give for 28.8).

```text
$ python -B case/grade.py --responses audit/repro/F2_tolerance.jsonl --out audit/repro/out/F2.jsonl && cat audit/repro/out/F2.jsonl
model         correct  incorrect  no_answer   score
m1                  2          0          0   100.0
{"id": "F2-a", "model": "m1", "problem_id": "p07", "extracted": "15100", "verdict": "correct"}
{"id": "F2-b", "model": "m1", "problem_id": "p09", "extracted": "29", "verdict": "correct"}
```

### F3. `no_answer` responses and missing problems leave the denominator

`summarize` divides by `correct + incorrect`. TASK.md rule 3 makes a response
with no answer line (or no number on it) incorrect, and rule 5 scores "the
percentage of the 12 problems". In the stored run, delta-8b's two truncated
responses (`finish_reason` `length`, r12 and r36) and one response without an
answer line (r44) drop out, so it scores 3/9 = 33.3 instead of 3/12 = 25.0.
A problem with no response at all also drops out. The per-response verdicts
are right; only the score is wrong. The measuring fields are the grader's
`no_answer` column and the response count per model. Fix: divide by the
number of problems.

Counterexample `audit/repro/F3_denominator.jsonl`: model `abstainer` answers
p01 with `Answer: 3.5` and p02 to p12 with `I am not sure how to solve this.`
(contract 8.3); model `partial` answers p01 to p11 correctly and has no p12
row (contract 91.7).

```text
$ python -B case/grade.py --responses audit/repro/F3_denominator.jsonl
model         correct  incorrect  no_answer   score
abstainer           1          0         11   100.0
partial            11          0          0   100.0
```

### F4. The difference is rounded to 28 digits before the tolerance test

Both graders compute `abs(answer - reference)` in `Decimal` at the default
context precision of 28 significant digits. A difference with more digits is
rounded first, so 0.010000000000000000000000000001 becomes 0.01 and passes.
The contract compares the written decimals exactly, and the difference
exceeds 0.01 under both readings of `D-tolerance-boundary`. A model would
need 29 or more significant digits to trigger this, so the impact is
negligible, but it is a wrong verdict under every reading. Fix: compute the
difference at a precision that covers both operands (the replacement sets the
precision from the operand lengths and traps `Inexact`).

Counterexample: `{"problem_id": "p06", "response": "Answer: 0.010000000000000000000000000001"}`
(reference 0, contract `incorrect`).

```text
$ python -B case/grade.py --responses audit/repro/F4_precision.jsonl --out audit/repro/out/F4.jsonl && cat audit/repro/out/F4.jsonl
model         correct  incorrect  no_answer   score
m1                  1          0          0   100.0
{"id": "F4-a", "model": "m1", "problem_id": "p06", "extracted": "0.010000000000000000000000000001", "verdict": "correct"}
```

```text
$ python -B case/reference/grade_ref.py case/problems.jsonl audit/repro/F4_precision.jsonl audit/repro/out/F4.ref.jsonl && cat audit/repro/out/F4.ref.jsonl
model        correct  of  score
m1                 1  12    8.3
{"id": "F4-a", "model": "m1", "problem_id": "p06", "answer": "0.010000000000000000000000000001", "verdict": "correct"}
```

### F5. One bad row stops the whole run

A row whose `problem_id` is not in `problems.jsonl` (when it has an answer)
raises `KeyError`, and a row whose `response` is not a string raises
`AttributeError`. Either aborts the run before the score table, so no model
gets a score. Fuzzing found no exception reachable from response text (0 in
20,000 inputs), so this needs a harness or data error, not a model output.
Fix: give such a row its own label (the replacement uses `unknown_problem`
and `grading_error`), count it separately, and keep grading.

Counterexamples: `audit/repro/F5_unknown_problem.jsonl` (a valid p01 row and
`{"problem_id": "p13", "response": "Answer: 1"}`) and
`audit/repro/F5_null_response.jsonl` (a valid p01 row and a p02 row with
`"response": null`).

```text
$ python -B case/grade.py --responses audit/repro/F5_unknown_problem.jsonl 2>&1 | tail -1
KeyError: 'p13'
```

```text
$ python -B case/grade.py --responses audit/repro/F5_null_response.jsonl 2>&1 | tail -1
AttributeError: 'NoneType' object has no attribute 'splitlines'
```

### F6. A duplicate response is counted again

TASK.md: "A model answers each problem once." Neither grader checks this. The
grader counts a second response to a problem as another verdict (13 `correct`
for 12 problems), and the reference can print a score above 100. The stored
run has no duplicates. Fix: reject or flag a second (model, problem) row and
score each problem once.

Counterexample `audit/repro/F6_duplicate.jsonl`: model `dup` answers all 12
problems correctly, plus a second `Answer: 3.5` row for p01.

```text
$ python -B case/grade.py --responses audit/repro/F6_duplicate.jsonl
model         correct  incorrect  no_answer   score
dup                13          0          0   100.0
```

```text
$ python -B case/reference/grade_ref.py case/problems.jsonl audit/repro/F6_duplicate.jsonl
model        correct  of  score
dup               13  12  108.3
```

### R1. The reference deletes every comma on the answer line (reference only)

The reference removes every comma before matching, so commas that are not
between digits join numbers that the response keeps apart. `4,,86` holds the
numbers 4 and 86 under every reading of the contract and never 486. The
grader under audit reads 4 here, which agrees with the contract. Fuzzing
found 270 inputs where this step made the reference accept a trailing comma
(`Answer: 120,`) that its own strict reading would refuse; those verdicts
happen to match the proposed reading.

Counterexample: `{"problem_id": "p02", "response": "Answer: 4,,86"}` (contract
`incorrect`).

```text
$ python -B case/reference/grade_ref.py case/problems.jsonl audit/repro/R1_double_comma.jsonl audit/repro/out/R1.jsonl && cat audit/repro/out/R1.jsonl
model        correct  of  score
m1                 1  12    8.3
{"id": "R1-a", "model": "m1", "problem_id": "p02", "answer": "486", "verdict": "correct"}
```

### G1. Model revisions, chat templates and serving stack are not pinned

TASK.md and the run records name the models (`alpha-7b` and so on) and say
"each model's own chat template", with no revision, template hash or serving
version. The graded text depends on all three. They are unverified, not
wrong. To verify: the run's serving configuration, which is not in the case;
the record field that would carry it is absent from `responses.jsonl` (its
fields are `id`, `model`, `problem_id`, `response`, `finish_reason`,
`temperature`, `max_tokens`).

## Decision entries for the maintainers

Each entry has two readings that a careful reader could defend. The proposal
is the contract's reading (A). "Panel effect" counts the stored verdicts that
change when the replacement switches to the other reading.

| Entry | Reading A (proposed) | Other reading(s) | Example | Grader | Reference | Panel effect |
|---|---|---|---|---|---|---|
| `D-surrounding-text` | other text may surround the number on the answer line | B: the line must hold the number alone (not even a final period) | `Answer: $3.50` (p01): A correct, B no number | A | B | 4 verdicts, all gamma-32b (r03, r07, r19, r35): -33.3 points under B |
| `D-multiple-numbers` | the first number on the line | B: the last number; C: no single number, so no answer | `Answer: 6 muffins cost 16.50, so 3.50` (p01): A incorrect, B correct | A | C (through B of the entry above) | 0 |
| `D-digits` | ASCII 0 to 9 only | B: any Unicode decimal digit | `Answer: ７２` (fullwidth, p05): A no number, B correct | B | B | 0 |
| `D-leading-whitespace` | any character that `str.isspace()` accepts | B: ASCII space and tab only | U+00A0 then `Answer: 72` (p05): A correct, B no answer line | A | A | 0 |
| `D-tolerance-boundary` | a difference of exactly 0.01 passes | B: it fails | `Answer: 0.01` (p06): A correct, B incorrect | A | A | 0 |
| `D-no-number-label` | an answer line without a number is `no_answer` | B: it is `incorrect` | `Answer: unknown` (p02) | A | B (two labels only) | 0, score-neutral |

Only `D-surrounding-text` moves a score on the stored run. Reading B would
cost gamma-32b a third of its score for writing a unit or currency sign that
the prompt asked it to leave out. The scoring rule never makes that slip
incorrect, so the audit proposes A. That one choice is the gap between the
reference's 66.7 for gamma-32b and the grader's 100.0.

```text
$ python -B case/grade.py --responses audit/repro/decisions.jsonl --out audit/repro/out/D.jsonl && cat audit/repro/out/D.jsonl
model         correct  incorrect  no_answer   score
d1                  1          0          0   100.0
d2                  1          0          0   100.0
d3                  1          0          0   100.0
d4                  0          1          0     0.0
d5                  1          0          0   100.0
d6                  0          0          1     0.0
{"id": "D-leading-whitespace", "model": "d1", "problem_id": "p05", "extracted": "72", "verdict": "correct"}
{"id": "D-digits", "model": "d2", "problem_id": "p05", "extracted": "72", "verdict": "correct"}
{"id": "D-surrounding-text", "model": "d3", "problem_id": "p01", "extracted": "3.50", "verdict": "correct"}
{"id": "D-multiple-numbers", "model": "d4", "problem_id": "p01", "extracted": "6", "verdict": "incorrect"}
{"id": "D-tolerance-boundary", "model": "d5", "problem_id": "p06", "extracted": "0.01", "verdict": "correct"}
{"id": "D-no-number-label", "model": "d6", "problem_id": "p02", "extracted": null, "verdict": "no_answer"}
```

## What each step did

1. **Inputs pinned** from TASK.md, `MANIFEST.sha256` and the record fields,
   before any code was read: every case file matches the manifest
   (`python -B audit/scripts/pin_inputs.py --rows`), plus one sha256 per data
   row. Unverified: model revisions, chat templates, serving stack (G1), and
   the evaluation's Python version, which matters only under the graders'
   `D-digits` reading.
2. **Contract** `audit/CONTRACT.md` written from TASK.md alone and hashed at
   00:57 UTC before either grader was opened. Two later amendments, with
   their reasons in the file, restated reading B of `D-surrounding-text` and
   gave reading C of `D-multiple-numbers` its label. No proposal changed.
3. **Fixtures**: 86 (20 finding, 23 decision, 43 control), each labelled from
   the contract and run against all three graders. The replacement passes all
   86, and every alternative reading listed in a fixture. The grader fails 21
   (F1 5, F2 12, F4 2, `D-digits` 2), the reference 12 (F4 2, R1 1,
   `D-digits` 2, `D-surrounding-text` 7).
4. **Reference and stress tests.** On the panel the grader and the reference
   disagree on 6 verdicts: r10 and r26 are grader defects (F1), and r03, r07,
   r19 and r35 are the decision `D-surrounding-text`. No disagreement is a
   reference defect on the panel; R1, F4, F5 and F6 show only on fixtures.
   Neither grader ships unit tests, so there were none to run against the
   replacement. Metamorphic edits: 37 edits
   applied to a passing response of every problem they fit, 422 cases. The grader
   breaks only on thousands commas (F1) and the two value shifts (F2), the
   reference only on the 7 `D-surrounding-text` edits, the replacement on
   none. Fuzzing (`python -B audit/scripts/fuzz.py 20000 1`, counts depend
   on the generator): no exception in any grader. Against the replacement at
   the grader's own readings, the grader differs on 258 inputs through F1,
   1,521 through F2 and 8 through F4. Content-free responses (empty,
   whitespace, repeated text, the prompt or problem restated,
   `Answer: <number>`, `Answer:`) get `correct` from no grader on any
   problem; their only effect on scores runs through F3. The grader has no
   score-level transform besides F3's denominator.
5. **Panel**: the 48 stored responses only, with no new generation. A seeded
   half (24) was held out before any grader ran on the panel. The dev half
   prompted no change to the replacement. Scored coverage is 48/48 for every
   grader. Two responses hit the output budget (`length`), and no response
   holds reasoning markers. No rerun exists to measure run-to-run variation.
6. **Blinded review: not run.** The round was drawn with seed 61111 from the
   24 held-out responses: stratum "grader and replacement disagree", 1 of 1
   (r10); stratum "agree", 23 of 23. It is frozen (case list sha256
   `3cc353523a98…`), and the batches for reviewers A and B (different orders),
   the helper and the filled reviewer prompt are in `audit/frozen/`. The
   result that would change the recommendation was recorded first: the
   replacement wins the paired comparison if and only if the consensus on r10
   is `correct`. With 23 agreement cases, neither grader's interval can end
   below 14.2%.

## Not done in this exercise

- No issue tracker, repository, research branch, Hugging Face dataset or job
  launcher: the record is `audit/ISSUE.md`, the fixtures are `unittest` files
  in `audit/tests/`, frozen material is in `audit/frozen/` with hashes in
  ISSUE.md, and nothing went through `file-issue`, `manage-pr`,
  `research-engineering` or `use-iris`.
- pytest is not installed, so `pytest.mark.xfail(strict=True)` is replaced by
  `unittest.expectedFailure`. An unexpected pass makes the run fail, which has
  the same effect.
- No compute: no new panel responses, no rerun, no second decoding setting.
- Step 6.4 and 6.5 (the reviews and the error-rate estimate) need reviewer
  runs, which this exercise does not allow.

## Reproduce

```text
python -B audit/scripts/pin_inputs.py               # inputs match the manifest
python -B -m unittest discover -s audit/tests       # 384 tests, OK (expected failures=51)
python -B audit/scripts/property_matrix.py          # metamorphic edits
python -B audit/scripts/fuzz.py 20000 1             # fuzz counts
python -B audit/scripts/content_free.py             # content-free responses
python -B audit/scripts/panel.py all                # step 5 panel
python -B audit/scripts/check_report_commands.py    # reruns every "$" command in this file
```
