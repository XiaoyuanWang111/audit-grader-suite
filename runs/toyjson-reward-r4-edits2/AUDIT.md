# Audit of the ToyOrders RL reward (`case/reward.py`)

Written 2026-11-11T02:01:49Z. Grader `case/reward.py` sha256 `e8cbb556…2f8362`; task text `case/TASK.md`; the record
of pins, contract hash, decisions, findings and frozen-sample hashes is `audit/ISSUE.md`. All commands run from the
audit's working directory with CPython 3.12.10; `python -B audit/check_report_commands.py` reruns every command below
and checks its output (30/30 pass).

## Result

**Error rate: not measured.** Step 6 (the blinded two-reviewer review) was not run, because this exercise allows no
subagents. Its sample is drawn and frozen (`audit/frozen/round1/`, census of all 48 stored rollouts, sha256 of the
case list in `audit/ISSUE.md`), with batch files and reviewer prompts ready.

**Effect on scores, measured against the contract.** The figures below compare the grader with the replacement
grader written from the contract (`audit/replacement_reward.py`). They are contract-based, not review-based. "Fixes
only" sets every decision entry to the grader's own reading, so each difference is a defect; "proposed" uses the
audit's proposed readings. Means over the 12 stored rollouts per checkpoint; intervals are 95% paired bootstraps
over rollouts (`python -B audit/panel.py`):

| Checkpoint | Grader | Fixes only | Proposed | Full rewards (grader / fixes only / proposed) | Grader minus fixes only |
|---|---|---|---|---|---|
| step-0000 | 0.756 | 0.584 | 0.584 | 5 / 2 / 2 | +0.172 [+0.000, +0.417] |
| step-0200 | 0.971 | 0.960 | 0.929 | 10 / 9 / 7 | +0.010 [+0.000, +0.031] |
| step-0400 | 0.979 | 0.896 | 0.896 | 11 / 10 / 10 | +0.083 [+0.000, +0.250] |
| step-0600 | 1.000 | 0.726 | 0.726 | 12 / 6 / 6 | +0.274 [+0.045, +0.521] |
| all 48 | 0.926 | 0.791 | 0.784 | 38 / 27 / 25 | +0.135 [+0.050, +0.237] |

- The grader shows the policy improving to a perfect 1.000 at step-0600. Under the contract, step-0600 scores
  0.726, below step-0200 (0.929 to 0.960), and 6 of its 12 full rewards are false.
- False rewards: 11 of the grader's 38 full rewards (28.9%) contradict the contract under the grader's own decision
  readings (F1: 6, F2: 5). With the proposed readings the count is 13 of 38 (34.2%), adding j02 and j46
  (`D-qty-decimal`). The rewards in excess of the contract total 14.6% of the grader's reward mass (15.4% with the
  proposed readings). The grader never rewards a rollout below the contract.
- The rollouts that exploit F1 or F2 number 3, 1, 1 and 6 at the four checkpoints. At step-0600 three rollouts
  append a sentence after the JSON (F1) and three list duplicate or enumerated items (F2). This is consistent with
  the policy learning both exploits, but one rollout per order and checkpoint, and no rerun, cannot establish a trend.
- Robustness: the grader raises on four kinds of input (F3 to F5), contrary to the task's requirement that it
  return a float for every response. One such response stops the offline run (G3). The panel triggers none; seeded
  fuzzing (2,000 inputs per generator) gives 370, 19, 1,385 and 774 grader exceptions across the four generators,
  and none from the replacement.
- Every difference between the grader and the fixes-only replacement on the 102 fixtures, the 48 rollouts and 8,000
  fuzz inputs is reproduced by re-enabling some subset of F1 to F6 (`python -B audit/classify.py`: 8,150 cases,
  0 unexplained).

**Recommendation: fix the grader.** Replace `case/reward.py` with the replacement (`--mode proposed`, after the
maintainers settle `D-crlf` and `D-qty-decimal`, the two entries where the grader departs from the proposed
reading), or at minimum fix F1 to F6 and G1 to G3 in place. Then regrade the training run's checkpoints: the
reward that trained them overstated the late checkpoints. The decision rule recorded before the sample was drawn
says that adopting the replacement needs (1) every fixture passing, (2) complete scored coverage, and (3) a lower
error rate than the grader's, with a paired interval that excludes zero. (1) and (2) hold; (3) is unmeasured until
the review runs. If (3) fails, the recommendation falls back to fixing F1 to F6 in place. The benchmark does not
need replacing: its specification is clear, and the defects are in the implementation.

## Findings

No reference implementation exists (TASK.md), so no finding has a reference status. "Share" is over the 48 stored
rollouts. For a larger set of rollouts, every share is measured by regrading the stored `response` field: the
reward is a deterministic function of `response` and the order's `reference`, and `classify.explain` attributes
each difference to these findings. "Contract" is the clause of `audit/CONTRACT.md` (sha256 `d3a81e33…`) and of
TASK.md that the verdict breaks. Each counterexample file holds the exact input as one JSON line (order `o02`,
reference: Kenji Watanabe, 2026-01-15, EF-310 x3, total 29.97). The grader command uses the grader's own command
line; the contract's value comes from `python -B audit/replacement_reward.py --responses <same file>`.

| Id | Stage or check | Contract broken | Fixtures | Share |
|---|---|---|---|---|
| F1 | Answer extraction | C1.4-C1.5; TASK.md: "a single JSON object with nothing around it but whitespace; otherwise the reward is 0.0" | 6, e.g. `answer:97e0fa751297a94a` | 6/48 (12.5%): j05, j08, j20, j37, j40, j47 get 1.0, contract 0.0 |
| F2 | `items` | C4; TASK.md: divide "by the larger of the number of reference items and the number of answer items" | 6, e.g. `items:83bed4a666b94e20` | 5/48 (10.4%): j04, j16, j18, j32, j41 get 1.0, contract 0.875 to 0.9375 |
| F3 | Extraction, robustness | C1.5, C8: "must return a float for every response" | 5, e.g. `answer:93751ec6a097e138` | 0/48 |
| F4 | Extraction, robustness | C1.5, C8 | `answer:107b473745bd1dec`, `answer:0300e40cc038df78` | 0/48 |
| F5 | `total`, robustness | C5, C8 | `total:c197ae2ec197c446`, `total:96c2adf2bb40dc08` | 0/48 |
| F6 | `total` | C5: exact distance at most 0.005 ("numbers are read exactly") | `total:e56a1cb3f525a70d`, `total:98c2931995549f4e` | 0/48 |
| G1 | Pinned inputs | Step 1: every input that can change a verdict is pinned | `answer:0300e40cc038df78` | 0/48 |
| G2 | Pinned inputs | Step 1 | none (script) | 0/48 under the default context |
| G3 | Harness | Step 4: a grading exception must not stop the run | none (file) | 0/48 |

### F1: text after the JSON object is ignored

`parse_answer` decodes with `JSONDecoder.raw_decode` and discards the end index, so anything after the first JSON
value is accepted, whether the answer is bare or inside a fence. A bare answer followed by text earns full reward.
The same answer in a fence followed by text earns 0.0 (j25), because the fence regex then fails and the text starts
with a backtick. On the panel: j05 and j37 at step-0000, j47 at step-0400, and j08, j20 and j40 at step-0600 (for
example j08 appends "Extraction complete." on its own line).

- Input (`audit/counterexamples/F1.jsonl`), the correct object followed by a full stop:
  `{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}.`
- `python -B case/reward.py --responses audit/counterexamples/F1.jsonl` prints the following (reward 1.0, one full
  reward). Contract: 0.0.

  ```text
  checkpoint   rollouts    mean  full
  F1                  1   1.000     1
  ```
- Fix: parse with `json.loads` (it rejects "Extra data"), or require the end index to reach the end of the answer.

### F2: duplicate and extra items cost nothing

`items_score` returns `matched / len(expected)` and never counts the answer's items. Repeating a correct item,
adding an invented line (j18 adds a `SHIPPING` item, j41 a `DELIVERY` item) or listing every quantity for every SKU
keeps the full score. A policy can therefore enumerate candidates at no cost (j32 lists both SKUs with both
quantities).

- Input (`audit/counterexamples/F2.jsonl`):
  `{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}, {"sku": "EF-310", "qty": 3}], "total": 29.97}`
- `python -B case/reward.py --responses audit/counterexamples/F2.jsonl` prints the following. Contract: 0.875
  (items 1/2).

  ```text
  checkpoint   rollouts    mean  full
  F2                  1   1.000     1
  ```
- Fix: divide by `max(len(expected), len(value))`.

### F3: a top-level value that is not an object raises

When the answer starts with a JSON value that is not an object, `raw_decode` returns it, and `answer.get` raises
`AttributeError`. Such answers include an array, a string, a number, `true`, `[...]` around the object, or a
response that opens with a number (`1. {...}` or `2 items: ...`). The only exception is `null`, which happens to
return 0.0. Numbered labels before each line raise on all 48 property cases.

- Input (`audit/counterexamples/F3.jsonl`): `[]`
- `python -B case/reward.py --responses audit/counterexamples/F3.jsonl` exits 1 with
  `AttributeError: 'list' object has no attribute 'get'` and prints no table. Contract: 0.0.
- Fix: return 0.0 unless the parsed value is a `dict`.

### F4: json errors other than `JSONDecodeError` escape

`parse_answer` catches only `json.JSONDecodeError`. Deep nesting raises `RecursionError`. An integer of more than
4,300 digits raises `ValueError` under the interpreter's default integer-string limit (see G1).

- Input F4a (`audit/counterexamples/F4a.jsonl`), as a Python expression:
  `'{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97, "n": 1' + '0' * 4300 + '}'`
- `python -B case/reward.py --responses audit/counterexamples/F4a.jsonl` exits 1 with
  `ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; ...`.
  Contract: 0.0 (the `json` module does not parse the answer).
- Input F4b (`audit/counterexamples/F4b.jsonl`): `'[' * 100000 + ']' * 100000`
- `python -B case/reward.py --responses audit/counterexamples/F4b.jsonl` exits 1 with
  `RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string`. Contract: 0.0.
- Fix: also catch `ValueError` (the parent of `JSONDecodeError`) and `RecursionError`, and return 0.0.

### F5: `decimal.Overflow` on a total with a huge exponent

`total_score` computes `Decimal(value) - Decimal(expected)` in the default context, whose `Emax` is 999999 with
`Overflow` trapped.

- Input (`audit/counterexamples/F5.jsonl`):
  `{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 1e999999999}`
- `python -B case/reward.py --responses audit/counterexamples/F5.jsonl` exits 1 with
  `decimal.Overflow: [<class 'decimal.Overflow'>]`. Contract: 0.75 (a number, not within 0.005).
- Fix: compare the total with exact bounds (`reference - 0.005 <= total <= reference + 0.005`; `Decimal` comparisons
  are exact and use no context), as the replacement does.

### F6: the total's distance is rounded to 28 digits

The subtraction rounds to the context's 28 significant digits. A distance just above 0.005 then rounds to exactly
0.005 and passes, although TASK.md says numbers are read exactly.

- Input (`audit/counterexamples/F6.jsonl`), total 29.975 followed by 27 zeros and a 1:
  `{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.9750000000000000000000000000001}`
- `python -B case/reward.py --responses audit/counterexamples/F6.jsonl` prints the following. Contract: 0.75
  (distance 0.005 + 1e-31). Wrong under both readings of `D-total-boundary`.

  ```text
  checkpoint   rollouts    mean  full
  F6                  1   1.000     1
  ```
- Fix: the exact comparison under F5.

### G1: the Python version and its integer-string limit are unpinned

TASK.md pins "the Python 3 standard library" only. Since Python 3.11 (and the 3.7.14, 3.8.14, 3.9.14 and 3.10.7
security releases), `int()` refuses strings of more than 4,300 digits unless `PYTHONINTMAXSTRDIGITS` or
`-X int_max_str_digits` changes the limit, so the same response raises on one interpreter and scores on another.

- Input: F4a's.
- `python -B -X int_max_str_digits=0 case/reward.py --responses audit/counterexamples/F4a.jsonl` prints the
  following, where the default setting raises (F4a above). Setting `PYTHONINTMAXSTRDIGITS=0` in the environment does
  the same.

  ```text
  checkpoint   rollouts    mean  full
  F4a                 1   0.900     0
  ```
- Fix: pin the interpreter version and set the limit explicitly, or make the reward independent of it (F4's fix
  plus a documented reading for very long integers).

### G2: the total's verdict depends on the caller's decimal context

`total_score` does its arithmetic in the thread-local `decimal` context of whatever process imports `reward.py`.
Nothing pins that context.

- Input: the o02 object with `"total": 29.975000000001`.
- `python -B audit/g2_decimal_context.py` prints the response and then the following; the second line comes after
  the caller sets precision 9 (the precision of `decimal.BasicContext`). Contract: 0.75.

  ```text
  default context (prec 28): 0.75
  caller set prec 9:         1.0
  ```
- Fix: the exact comparison under F5, or `decimal.localcontext()` with fixed settings inside `total_score`.

### G3: one exception stops the run

`main()` has no exception guard, so the first raising response ends the offline run with a traceback and no
results. The trainer calls `reward()` directly; whether it catches exceptions is unverified, since its code is not
provided.

- Input (`audit/counterexamples/G3.jsonl`): three rows for o02, the correct object, `[]`, and the correct object.
- `python -B case/reward.py --responses audit/counterexamples/G3.jsonl` exits 1 with the F3 traceback and prints no
  table. `python -B audit/replacement_reward.py --responses audit/counterexamples/G3.jsonl` prints a table whose
  row is `G3                  3   0.667     2`.
- Fix: F3 to F5 remove the known exceptions. The harness should also count any remaining exception as a per-rollout
  grading failure, logged and kept out of the policy's accuracy, rather than a crash.

## Decision entries

These need a reading from the evaluation's maintainers. They are counted separately from the findings. Fixture
ids are in `audit/tests/fixtures.py`; the replacement has one switch per entry.

| Id | Question | Reading A (proposed) | Reading B | Grader | Panel share |
|---|---|---|---|---|---|
| `D-crlf` | Does `\r\n` end a line in the fence rule? | Yes: `"```json\r\n" + V + "\r\n```"` scores 1.0 | No: 0.0 | **B** | 0/48 |
| `D-qty-decimal` | Is `qty` 2.0 (or `2e0`, read as `Decimal`) "an integer"? | No: o01 with AB-100 `"qty": 2.0` scores 0.875 | Yes: 1.0 | **B** | 2/48 (j02, j46) |
| `D-whitespace` | Which characters are "whitespace" (end strip, around the object, customer strip)? | `str.strip()` set: `V` + U+00A0 scores 1.0 | JSON whitespace only: 0.0 | A | 0/48 |
| `D-fence-tab` | May a tab follow the tag ("spaces may follow the tag")? | Yes: 1.0 | No: 0.0 | A | 0/48 |
| `D-json-constants` | Do `NaN` and `Infinity` (accepted by Python's `json`) belong in a valid answer? | Yes: `"total": NaN` scores 0.75 | No: answer invalid, 0.0 | A | 0/48 |
| `D-qty-bool` | Is `true` an integer equal to 1? | No: 0.875 | Yes: 1.0 | A | 0/48 |
| `D-total-boundary` | Is a distance of exactly 0.005 "within 0.005"? | Yes: o01 with 64.505 scores 1.0 | No: 0.75 | A | 0/48 |

The reasons for each proposal are in `audit/CONTRACT.md`. The two entries where the grader takes reading B
reproduce on order o02. `audit/counterexamples/D-qty-decimal.jsonl` holds the correct object with `"qty": 3.0`, and
`audit/counterexamples/D-crlf.jsonl` holds `"```json\r\n"` + the correct object + `"\r\n```"`.
`python -B case/reward.py --responses audit/counterexamples/D-qty-decimal.jsonl` and then the same command with
`D-crlf.jsonl` print the following rows. The replacement in proposed mode gives 0.750 and 1.000.

```text
D-qty-decimal        1   1.000     1
D-crlf              1   0.000     0
```

## What each step did, and what was not run

1. Pins (`audit/pin_inputs.py`, `audit/pins.json`): every case file matches `MANIFEST.sha256`, with one sha256 per
   order and per rollout. The generation settings in the records are temperature 1.0 and `max_tokens` 256. Not
   verifiable from the records, with what would verify each: the policy model, chat template, stop sequences and
   serving stack (the training run's configuration); "none was truncated" (no `finish_reason` field); the trainer's
   prompt renderer and call site. The template contains other braces, so it must be filled by literal replacement,
   not `str.format`. There is no grader commit, because there is no repository.
2. Contract (`audit/CONTRACT.md`), with its hash and time in `audit/ISSUE.md`: version 1, 7 decision entries, no
   later changes.
3. Fixtures (`audit/tests/`): 102 fixtures (67 controls, 23 finding fixtures, 12 decision fixtures), 26 metamorphic
   properties, and seeded fuzz and robustness tests. `python -B -m unittest discover -s audit/tests` reports
   `Ran 390 tests`, `OK (expected failures=32)`. pytest is not installed, so `unittest.expectedFailure` stands in
   for `xfail(strict=True)`: since Python 3.4 an unexpected success fails the run. Built a replacement grader,
   because F1 to F6 are fixable in code.
4. Stress (`audit/stress.py`, `audit/stress_results.json`): no reference implementation, so there was no reference
   comparison and no reference unit tests, and the grader has no tests of its own. The grader passes all 11
   ignored-edit properties and violates 6 of the 15 forbidden-edit properties. Content-free responses (empty,
   whitespace, repeated text, the restated instructions, the email, `{}`, empty fields, a schema placeholder,
   `null`) all score 0.0. `[]`, `""` and `0` raise (F3). The only score-level transform is the CLI's rounding to 4
   decimals before averaging, and it cannot turn a non-full reward into 1.0.
5. Panel (`audit/panel.py`, `audit/panel/`): the 48 stored rollouts, with no generation (no compute in this
   exercise). The records show 7 fenced answers, 7 answers with text after the JSON (F1's six and j25), 1
   Python-dict answer (j45), 2 decimal quantities (j02, j46), 1 string total (j29), 2 extra top-level keys (j17,
   j34), 5 answers with extra items, and no reasoning markers. Scored coverage is 48/48 for every grader. A rerun at
   identical generation settings was not possible; regrading is deterministic (48/48 identical). The replacement
   was frozen before it graded the panel and never changed, so no held-out split was needed.
6. Blinded review: **not run** (no subagents). Steps 6.1 to 6.3 are done: the decision rule was recorded before the
   draw, the sample is a census in two strata (13 disagreements and 35 agreements between the grader and the
   proposed replacement), and the case list, keys, two batch orders, the filled reviewer prompts and the helper are
   frozen with their sha256 in `audit/ISSUE.md`. When the review runs, each case is one rollout, its label is the
   reward the specification assigns (or `ambiguous` with a lean), and the error rate follows step 6.5.
7. This report.

Skipped because this exercise has no infrastructure for them: the issue tracker (`audit/ISSUE.md` stands in), the
repository, research branch and `manage-pr` (fixtures stay under `audit/tests/`), the Hugging Face artifact (frozen
files under `audit/frozen/` with their hashes in `audit/ISSUE.md`), `use-iris` and response generation, the step 5
rerun, and the issue-style guide `docs/dev-guide/writing-style/issues.md`. `skill/references/validation.md` was not
provided.

## Limitations

- The grader code (`case/reward.py`) and the stored rollouts were read before the contract was written. The
  contract follows the TASK.md text, but it was not written blind to the code (disclosed in `audit/ISSUE.md`).
- One auditor wrote the contract, the fixture labels and the replacement, so all three may share the same misreading.
  The step 6 review is where independent labels would come from, and it has not run. The panel figures above
  measure agreement with this auditor's contract, not an error rate.
- The panel is one training run, one rollout per order per checkpoint, with no rerun, so the per-checkpoint
  intervals are wide.
- The fuzz counts depend on the generators in `audit/stress.py`, so they are counts, not rates.
