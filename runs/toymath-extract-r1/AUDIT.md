# ToyMath 1.0: audit of the grader `case/grade.py`

Run root: `<run directory>`. Every path below is relative to it, and every
command runs in bash from it. The audit record is `audit/ISSUE.md`, the contract `audit/CONTRACT.md`.

## Error rate and effect on scores

The blinded review (step 6) was not run, so there is no review-based error rate. Against the contract, as
implemented by the replacement grader with the proposed readings, `grade.py` gets 2 of the 48 stored verdicts
wrong (4.2%). Both are correct answers graded `incorrect`: r10 `Answer: 2,250` and r26 `Answer: 15,000`, from
beta-14b (F1). It also gives 2 of the 4 models a wrong score. For beta-14b, the cause is those two verdicts.
For delta-8b, the cause is its score formula, which leaves 3 `no_answer` responses out of the denominator (F3).
None of its 34 `correct` verdicts on the panel contradicts the contract. Its 1% tolerance (F2) can produce false
corrects, but no stored answer falls in that band.

| Score (of 12 problems) | alpha-7b | beta-14b | delta-8b | gamma-32b | Rank order |
|---|---|---|---|---|---|
| `grade.py`, as printed | 75.0 | 83.3 | 33.3 | 100.0 | gamma, beta, alpha, delta |
| replacement, proposed readings | 75.0 | 100.0 | 25.0 | 100.0 | beta = gamma, alpha, delta |
| reference `grade_ref.py`, as printed | 75.0 | 100.0 | 25.0 | 66.7 | beta, alpha, gamma, delta |
| `grade.py` minus replacement | 0.0 | −16.7 (F1) | +8.3 (F3) | 0.0 | |

The reference differs from the contract on 4 verdicts, all from one decision entry, `D-answer-line-form`.
These are gamma-32b's answer lines with a unit or `$` after the number: r03 `$3.50`, r07 `486 students`,
r19 `72 km/h` and r35 `28.80 dollars`. The reference requires the whole line to be one number. That reading
moves gamma-32b from 100.0 to 66.7, a larger change than any finding makes to a stored score. Under that
reading, `grade.py` would be wrong on those 4 verdicts as well, 6 of 48 in all. No other decision entry changes
a stored verdict. These score changes cannot be compared with generation noise: that needs a rerun of a model
at identical settings, and there was no compute (step 5). Two runs of each grader gave identical verdicts.

## Recommendation: fix the grader

F1, F2 and F3 contradict the card's rules R2, R4 and R5 on fixtures whose labels need no reading. F1 and F3
change two of the four stored scores. The benchmark itself holds up: all 12 reference answers are right, and
the card's rules give one verdict for every response once the six decision entries are chosen. The fix
consists of these changes:

1. Commas between digits are part of the number, and are removed before parsing (F1).
2. Correct means r − 0.01 ≤ x ≤ r + 0.01, using exact `Decimal` comparisons, which never round (F2, F4).
   With no subtraction, nothing overflows (F5).
3. A response that still raises is recorded as a grading failure for that response, counted apart from model
   accuracy, and the run goes on (F5).
4. The score is correct / 12. A `no_answer` and a missing problem count as not correct, and each model's
   row shows the number of problems missing (F3).
5. A file with two responses from one model to one problem, or an unknown `problem_id`, is rejected (F6).
6. Each run record stores the model revision, chat template, serving stack and version, seed and stop
   sequences, and the Python version is pinned (G1).

`audit/scripts/grade_contract.py` implements items 1, 2, 4 and 5, with one switch per decision entry. It
raised on none of the fixtures or fuzz inputs, but it does not implement item 3. With `--digits unicode`
(`grade.py`'s digit reading), it differs from `grade.py` on 1,163 of the 20,003 fuzz inputs, and each
difference is F1, F2 or F5. The maintainers should then decide the six entries below, `D-answer-line-form`
first.

Gate status (`audit/ISSUE.md`, step 6, recorded before any review). The replacement passes every fixture and
property test, and its scored coverage is complete (48 of 48 verdicts, denominator 12). The fourth condition
is a lower review error rate than `grade.py`'s, with a paired interval that excludes zero. The review was not
run, and this 48-response panel cannot meet that condition whatever the reviewers say: the two differing
verdicts sit in a 6-case stratum.

## Findings

| Id | Stage | Counterexample (exact input) | Contract broken | Panel share | Reference |
|---|---|---|---|---|---|
| F1 | S2, number | p07 `Answer: 15,000` gives `incorrect` (reads 15); p12 `Answer: 15,000` gives `correct` | R2: commas in the number are ignored | 2 of 48 verdicts (r10, r26); r09's extracted value is wrong too (1 for `1,800`), its verdict right by chance | fixed: removes commas |
| F2 | S3, comparison | p02 `Answer: 482` gives `correct`; p07 `Answer: 14900` gives `correct` | R4: within 0.01 | 0 of 48 | fixed: absolute 0.01 |
| F3 | S4, score | 12 rows: p01 to p06 answered right, p07 to p12 empty, scores 100.0 | R3, R5: no answer is incorrect, the score is out of 12 | delta-8b's score, 3 of 48 verdicts left out (r12, r36, r44) | fixed: divides by 12 |
| F4 | S3, comparison | p06 `Answer: 0.010000000000000000000000000001` gives `correct` | S3.3: exact comparison (the distance exceeds 0.01 by 1e-30) | 0 of 48 | same defect |
| F5 | robustness | p02 `Answer: ` followed by 1,000,000 nines raises `decimal.Overflow`, which ends the run with no verdicts or scores | S4.4: grading never raises | 0 of 48; a 256-token response cannot hold such a number | same defect |
| F6 | S4, score | all 12 answered right, plus p01 answered right again: `grade.py` reports 13 correct, the reference prints 108.3 | S4.3: a problem never counts twice | 0 of 48: the run has one response per model and problem | same defect |
| G1 | protocol | the run records have no field for model revision, chat template, serving stack, seed or stop sequences; "Python 3.8 or later" changes what `\d` matches: U+11F54 KAWI DIGIT FOUR is a digit on Python 3.12, and Python 3.8's Unicode 12.1 predates it (3.8 not available here, so unverified) | step 1: pin every input that can change a verdict | all 48 responses | not applicable |

Fixtures. `grade.py` fails 24 of the 146 fixtures under every reading (F1 7, F2 15, F4 2, one of them also F2),
and 5 more only under the proposed readings (decisions). Property tests: `grade.py` fails P1, thousands
separators (48 of 240 cases), and P7, more than 0.01 off (21 of 72). The reference and the replacement pass all
10 properties. Content-free responses (empty, whitespace, the restated prompt, a repeated word, number lists)
pass under no grader. But under `grade.py` their `no_answer` leaves the denominator (F3), so giving one costs
a model nothing.

For a larger panel, the stored fields that measure each share are as follows. F2: grade.py's `--out` field
`extracted` against the problem's `answer`; count the `correct` verdicts where |extracted − answer| > 0.01.
F3: the per-model count of `"verdict": "no_answer"`, plus the (`model`, `problem_id`) pairs missing from the
response file. F4: `extracted` values whose distance from `answer` needs more than 28 significant digits.
F5: the length of `response`. F6: repeated (`model`, `problem_id`) pairs in the response file.

### Reproducing each finding

The input files are in `audit/tests/counterexamples/`. The outputs below are cut to the lines that show each
defect; the full outputs are in `audit/out/counterexamples.log`.

F1, both rows of `F1.jsonl`: `{"id": "F1a", "model": "m", "problem_id": "p07", "response": "Answer: 15,000"}` and
`{"id": "F1b", "model": "m", "problem_id": "p12", "response": "Answer: 15,000"}`.

```text
$ (cd case && python grade.py --responses ../audit/tests/counterexamples/F1.jsonl --out ../audit/out/F1.grade.jsonl) && cat audit/out/F1.grade.jsonl
{"id": "F1a", "model": "m", "problem_id": "p07", "extracted": "15", "verdict": "incorrect"}
{"id": "F1b", "model": "m", "problem_id": "p12", "extracted": "15", "verdict": "correct"}
```

F2, `F2.jsonl`: p02 `"Answer: 482"` and p07 `"Answer: 14900"`. `grade.py` accepts any answer within 4.86 of
p02's 486, and within 150 of p07's 15000.

```text
$ (cd case && python grade.py --responses ../audit/tests/counterexamples/F2.jsonl --out ../audit/out/F2.grade.jsonl) && cat audit/out/F2.grade.jsonl
{"id": "F2a", "model": "m", "problem_id": "p02", "extracted": "482", "verdict": "correct"}
{"id": "F2b", "model": "m", "problem_id": "p07", "extracted": "14900", "verdict": "correct"}
```

F3, `F3.jsonl`: 12 rows for model `m`. Problems p01 to p06 have `"Answer: <reference answer>"`, and p07 to p12
have `""`. `grade.py` prints 100.0, where the contract and the reference give 50.0.

```text
$ (cd case && python grade.py --responses ../audit/tests/counterexamples/F3.jsonl)
model         correct  incorrect  no_answer   score
m                   6          0          6   100.0
$ (cd case && python reference/grade_ref.py problems.jsonl ../audit/tests/counterexamples/F3.jsonl)
m                  6  12   50.0
```

F4, `F4.jsonl`: `{"id": "F4a", "model": "m", "problem_id": "p06", "response": "Answer: 0.010000000000000000000000000001"}`.
Both graders say `correct`.

```text
$ (cd case && python grade.py --responses ../audit/tests/counterexamples/F4.jsonl --out ../audit/out/F4.grade.jsonl) && cat audit/out/F4.grade.jsonl
{"id": "F4a", "model": "m", "problem_id": "p06", "extracted": "0.010000000000000000000000000001", "verdict": "correct"}
$ (cd case && python reference/grade_ref.py problems.jsonl ../audit/tests/counterexamples/F4.jsonl ../audit/out/F4.ref.jsonl) && cat audit/out/F4.ref.jsonl
{"id": "F4a", "model": "m", "problem_id": "p06", "answer": "0.010000000000000000000000000001", "verdict": "correct"}
```

F5, one row, p02, response `"Answer: "` followed by 1,000,000 `9` characters. The first command writes it. The
error comes from the subtraction x − r, whose result rounds to 10^1,000,000, past the context's largest exponent.

```text
$ python -c "import json;print(json.dumps({\"id\":\"F5\",\"model\":\"m\",\"problem_id\":\"p02\",\"response\":\"Answer: \"+\"9\"*1000000}))" > audit/out/F5.jsonl
$ (cd case && python grade.py --responses ../audit/out/F5.jsonl --out ../audit/out/F5.grade.jsonl); echo "exit $?"
decimal.Overflow: [<class 'decimal.Overflow'>]
exit 1                      (and no audit/out/F5.grade.jsonl is written)
$ (cd case && python reference/grade_ref.py problems.jsonl ../audit/out/F5.jsonl ../audit/out/F5.ref.jsonl)
decimal.Overflow: [<class 'decimal.Overflow'>]
```

F6, `F6.jsonl`: the 12 problems answered with their reference answers, plus a 13th row
`{"id": "F6_dup", "model": "m", "problem_id": "p01", "response": "Answer: 3.5"}`.

```text
$ (cd case && python grade.py --responses ../audit/tests/counterexamples/F6.jsonl)
m                  13          0          0   100.0
$ (cd case && python reference/grade_ref.py problems.jsonl ../audit/tests/counterexamples/F6.jsonl)
m                 13  12  108.3
```

G1: `python -c "import json;print(sorted(json.loads(open('case/responses.jsonl').readline())))"` prints
`['finish_reason', 'id', 'max_tokens', 'model', 'problem_id', 'response', 'temperature']`.

## Decision entries for the maintainers

Each entry is a point where the card allows two verdicts. The proposed reading is (a). Panel effects come from
the replacement with that one entry switched to (b).

| Entry | (a), proposed | (b) | `grade.py` | Reference | Stored verdicts that (b) changes | Example, (a) / (b) |
|---|---|---|---|---|---|---|
| `D-answer-line-form` | the answer is the first number after `Answer:`; other text on the line is allowed | the text after `Answer:`, stripped and without commas, must be one number | (a) | (b) | 4 of 48, all gamma-32b (100.0 / 66.7) | p05 `Answer: 72 km/h`: correct / no_answer |
| `D-multiple-numbers` | first number | last number | (a) | moot under (b) above | 0 | p03 `Answer: 2500 - 700 + 450 = 2250`: incorrect / correct |
| `D-comma-grouping` | a comma between two digits is ignored | a comma is ignored only in a valid thousands group | neither: its number ends at every comma (F1), which matches (b) on `1,5` | (a) | 0 | p12 `Answer: 1,5`: correct / incorrect |
| `D-digits` | ASCII 0 to 9 | any Unicode decimal digit | (b) | (b) | 0 | p02 `Answer: ４８６` (fullwidth): no_answer / correct |
| `D-leading-whitespace` | any `str.isspace()` character | space and tab only | (a) | (a) | 0 | p02, a no-break space then `Answer: 486`: correct / no_answer |
| `D-tolerance-boundary` | a distance of exactly 0.01 is within | it is not | (a) | (a) | 0 | p01 `Answer: 3.51`: correct / incorrect |

Reasons for (a) on `D-answer-line-form`: R3 calls a response incorrect when it has "no number on its answer
line", which presupposes searching the line for a number. The prompt's "a final line of the form
`Answer: <number>`" and "without units or currency symbols" support (b). I added this entry after reading the
reference (`audit/ISSUE.md`, contract change 1); the other five were in the contract before any code was read.

## Steps run

| Step | Status |
|---|---|
| 1. Pin the inputs | Run. Six files match the manifest; per-row hashes for the dataset and for each rendered prompt are in `audit/ISSUE.md`; pins checked before and after every grading run. Unpinned inputs: finding G1. |
| 2. Contract | Run. Hashed at 2026-11-06T22:29:07Z, before any code was read; one later change, recorded with its reason. |
| 3. Fixtures | Run. 146 fixtures, 1 isolated fixture and 7 score cases in `audit/tests/`; 197 tests, 40 of them strict expected failures, all OK (`audit/out/tests_verbose.log`). |
| 4. Reference comparison and stress tests | Run: reference on every fixture and on the panel, 10 property tests (1,248 cases), fuzzing (20,003 inputs), content-free responses, score transforms. Neither grader has unit tests to check. |
| 5. Model panel | Run on the 48 stored responses only. No generation, so no generation rerun; two delta-8b responses (r12, r36) stopped at the output budget with no answer line, and no response has a reasoning block. |
| 6. Blinded review | Not run, because no subagents can be started. 6.1 and 6.2 were run: 60 cases (6 disagreements, 42 agreements, 12 calibration fixtures), seed 61106, frozen with sha256 in `audit/ISSUE.md`. |
| 7. Report | This file. |

Substitutions for this offline run. There is no issue tracker, so the issue record is `audit/ISSUE.md`.
There is no repository, research branch, Hugging Face dataset or job launcher, so nothing was committed,
pushed, uploaded or launched. The scripts are in `audit/scripts/`, and the frozen sample and its keys in
`audit/frozen/`. Without pytest, the strict marks fall back to `unittest.expectedFailure`, which also fails a
run on an unexpected pass (`audit/tests/_xfail.py`).
