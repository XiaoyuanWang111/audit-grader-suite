# Audit of the ToyQA 1.0 judge pipeline

Grader under audit: `case/judge_pipeline.py` (sha256 `6f14e727…`). Reference: `case/reference/pipeline_ref.py`
(sha256 `7edd7358…`). Contract: `audit/CONTRACT.md` v1 (sha256 `89cff564…`), written from TASK.md, the judge rubric
and the gold targets before any code was read, and unchanged since. Replacement: `audit/replacement/toyqa_replacement.py`
(sha256 `027e5aaf…`), the contract implemented with the grader's interface. `audit/ISSUE.md` holds the record: every
pin, hash and time. Run every command below from the audit run's root (the folder that holds `case/` and `audit/`),
in bash.

## Error rate and effect on scores

No reviewed error rate exists: the blinded review (step 6) was not run, because this exercise allows no subagents.
Its round-1 sample is drawn and frozen.

The stored run gives a floor. Given the judge's own recorded replies, 10 of the grader's 48 verdicts (20.8%)
contradict the task text under every reading it allows. Three are extraction failures labeled `not_attempted` (F1).
Seven are judge replies that the parser misreads (F4). None of the 10 is a case under a decision entry. The reference
and the replacement give the task text's label on all 48 rows, and agree with each other on all 48. The review would
add any wrong grade from the judge model itself; both pipelines share those.

Scores on the stored run, in percent (accuracy, correct given attempted, F-score, not-attempted rate), and the count
of extraction failures:

| Model | Grader | Contract (reference and replacement) | Change |
|---|---|---|---|
| orca-7b | 83.3, 83.3, 83.3, 0.0; 0 | 75.0, 75.0, 75.0, 0.0; 0 | −8.3, −8.3, −8.3, 0.0; 0 |
| puffin-13b | 50.0, 66.7, 57.1, 25.0; 0 | 66.7, 80.0, 72.7, 16.7; 0 | +16.7, +13.3, +15.6, −8.3; 0 |
| heron-32b-think | 83.3, 90.9, 87.0, 8.3; 0 | 91.7, 100.0, 95.7, 8.3; 0 | +8.3, +9.1, +8.7, 0.0; 0 |
| ibis-8b-think | 58.3, 100.0, 73.7, 41.7; 0 | 50.0, 66.7, 57.1, 0.0; 3 | −8.3, −33.3, −16.5, −41.7; +3 |

The fixes reorder the models. By F-score the grader ranks ibis-8b-think (73.7) above puffin-13b (57.1), and the
contract ranks puffin-13b (72.7) above ibis-8b-think (57.1). F4 causes every change in accuracy, correct given
attempted and F-score. F1 alone moves ibis-8b-think's not-attempted rate from 41.7 to 16.7 and its extraction-failure
count from 0 to 3.

The only rerun available is the judge's. The recorded call 2 repeats each of the 34 judgments, and one flips (a06, B
to A). Scoring the contract pipeline with call 2 first moves only puffin-13b, by +8.3 accuracy points. The grader's
changes are not noise: rerunning it gives the same wrong verdicts. The answering models could not be rerun (no
compute).

## Recommendation

Fix the grader. Three functions in `case/judge_pipeline.py` need to match the contract: the label that
`grade_response` gives an extraction failure (F1), `render_prompt` (F2, F3) and `parse_grade` (F4). The reference
already implements each stage correctly. The replacement is a drop-in with the same functions, arguments and output,
and passes every fixture and property. Pin each answering model's chat template (G1), and send the three decision
entries to the evaluation's maintainers.

The gate pre-registered in `audit/ISSUE.md` has four parts, and three hold now: the replacement passes every fixture,
it passes the property tests, and scored coverage is complete (48 of 48). The fourth needs the blinded review: the
replacement's error rate must come out lower than the grader's, with a 95% paired interval that excludes zero. If
the review fails that part, the pre-registered fallback is to admit this run's verdicts and still fix F1 and F3.

## Findings

| Id | Stage | Shown by | Contract | Share of stored-run verdicts | Reference |
|---|---|---|---|---|---|
| F1 | Label mapping (`grade_response`, line 81) | fixture `label:a15950f0f2959d76`; stored a08, a20, a40 | E2, L1, G4, G5 | 3 of 48 (6.3%), all ibis-8b-think | correct |
| F2 | Prompt rendering (`render_prompt`, line 57) | fixtures `render:c6a76b3fe49e3cd5` and 3 more | R1 | 0 of 48 | correct |
| F3 | Prompt rendering (line 57); run control (`main`) | fixtures `render:76df3bf8ccb96354`, `label:1a4a5735943addb2`, `label:28567da540ac4ca3`, `cli:c67332accfa2349d` | E5, R1 | 0 of 48; one such row stops the run and voids all its verdicts | correct |
| F4 | Reply parsing (`parse_grade`, lines 25 and 62-64) | fixtures `parse:0f8db8316fdb5eed`, `parse:4be52da770f4a171` and 16 more; stored a09, a16, a22, a24, a32, a34, a35 | P1, P2, P3 | 7 of 48 (14.6%) | correct |
| G1 | Inputs (protocol) | the fields of `responses.jsonl` | step 1 | not measurable from the stored run | not applicable |

A fixture id is its stage name plus the first 16 hex digits of the sha256 of its inputs. `audit/tests/test_fixtures.py`
computes the ids, and `python -I -m unittest discover -s audit/tests -v` prints them. Every fixture the grader fails
carries a strict expected-failure mark naming its finding, so a fix must also remove the mark. The same goes for the
grader's failing property tests: two for F1, two for F2 and three for F4. The end-to-end fixture
`cli:73b84d96689a5615` fails on F1 and F2 together.

### F1. Extraction failures get the label `not_attempted`

Input, `audit/tests/data/F1.jsonl`:

```json
{"id": "f1", "model": "m", "question_id": "q01", "response": "<think>The capital of Australia is"}
```

Command: `python -I case/judge_pipeline.py --judge fake --responses audit/tests/data/F1.jsonl --out audit/work/F1.labels.jsonl`.
The grader writes `"label": "not_attempted"` with 0 judge calls, and prints not-attempted 1, extraction failures 0, and
a not-attempted rate of 8.3. The contract (E2) requires `extraction_failure`. The replacement, run the same way,
prints extraction failures 1 and a not-attempted rate of 0.0.

`extract_graded_text` detects the unclosed reasoning correctly. `grade_response` then returns `not_attempted` for it,
which hides each failure among the model's abstentions. On the stored run, F1 accounts for 25.0 of ibis-8b-think's 41.7
not-attempted points. The three rows are its truncated reasonings, a08, a20 and a40 (`finish_reason` `length`).
Accuracy, correct given attempted and F-score do not change, because neither label counts as correct or as attempted.

### F2. The judge sees only the first line of the graded text

Input, `audit/tests/data/F2.jsonl`:

```json
{"id": "f2", "model": "m", "question_id": "q01", "response": "Let me check the list of capitals.\nCanberra"}
```

Commands:

- `python -I -c "import sys; sys.path.insert(0, 'case'); import json, judge_pipeline as p; q = json.loads(open('case/questions.jsonl', encoding='utf-8').readline()); print(repr(p.render_prompt(p.load_template(), q, 'Let me check the list of capitals.\nCanberra').split('<<<\n')[1].split('\n>>>')[0]))"`
  prints `'Let me check the list of capitals.'`. That is the predicted answer the judge gets, and it holds no answer.
  The contract (R1) sends both lines.
- `python -I case/judge_pipeline.py --judge fake --responses audit/tests/data/F2.jsonl --out audit/work/F2.labels.jsonl`
  gives `incorrect` (grade B). The replacement gives `correct` with the same fake judge.

`graded_text.splitlines()[0]` keeps the first line before the 300-character cut. Any line break counts, including
`\r`, U+0085 and U+2028. No stored graded text has a second line (field `response`, 0 of 45 graded texts), so the
stored run is unaffected. The fixtures cover answers such as `Final answer:` followed by `Canberra` on a later line.

### F3. An empty graded text raises IndexError, and the exception stops the run

Input, `audit/tests/data/F3.jsonl`:

```json
{"id": "f3", "model": "m", "question_id": "q02", "response": "<think>I could not recall the year.</think>"}
```

Command: `python -I case/judge_pipeline.py --judge fake --responses audit/tests/data/F3.jsonl`. It exits with
status 1 on `IndexError: list index out of range` in `render_prompt`, line 57, and prints no table. With `--out` it
writes no file. The contract (E5, R1) sends the empty text to the judge. The replacement does, and labels the row
`not_attempted` (the fake judge replies C).

`"".splitlines()` is `[]`. An empty or whitespace-only response triggers it, and so does a response that ends at
`</think>`. `main` has no per-row error handling, so one such row voids every verdict of the run. Fuzzing raised it on
all 1,024 empty texts among 20,000 rendered texts, and on 5,116 of 20,000 random rows. No stored graded text is empty
(field `response`).

### F4. The parser takes the first capital A, B or C anywhere in the reply

Inputs, three judge replies: `After checking the symbol, the grade is B`, `CORRECT`, `Answer: B`.

Command: `python -I -c "import sys; sys.path.insert(0, 'case'); import judge_pipeline as p; print([p.parse_grade(r) for r in ['After checking the symbol, the grade is B', 'CORRECT', 'Answer: B']])"`
prints `['A', 'C', 'A']`. The contract (P1, P2) gives `['B', None, 'B']`. `CORRECT` holds no standalone letter, so
P3 calls the judge again.

The stored run shows the same failure. Run `python -I case/judge_pipeline.py --out audit/work/stored.labels.jsonl`,
then `grep '"a09"' audit/work/stored.labels.jsonl`. It shows a09 (orca-7b, q03, response
`The chemical symbol for tungsten is Tu.`, gold `W`) labeled `correct` with grade A, where the recorded call-1 reply
is `After checking the symbol, the grade is B`.

`re.compile(r"[ABC]").search(reply)` matches the first capital, inside words included, so the retry almost never
runs. 9 of the 34 call-1 replies are more than a bare letter, and the grader misreads 6 of them. Those 6 prompts
cover 7 rows:

| Row | Model | Graded text | Call-1 reply | Grader | Contract |
|---|---|---|---|---|---|
| a09 | orca-7b | `The chemical symbol for tungsten is Tu.` | `After checking the symbol, the grade is B` | correct | incorrect |
| a16 | ibis-8b-think | `Jupiter` | `Clearly wrong: B` | not_attempted | incorrect |
| a22 | puffin-13b | `Skin` | `Comparing it with the gold target: A` | not_attempted | correct |
| a24 | ibis-8b-think | `The liver` | `A liver is not skin. B` | correct | incorrect |
| a32 | ibis-8b-think | `The Nile` | `Cannot be the Amazon, so this is wrong.` (no grade; call 2 replies `B`) | not_attempted | incorrect |
| a34 | puffin-13b | `Iron` | `Based on the gold target, the grade is A.` | incorrect | correct |
| a35 | heron-32b-think | `Iron` | `Based on the gold target, the grade is A.` | incorrect | correct |

Fuzzing found 12,368 and 4,415 mismatches among 20,000 replies from each of two generators, and no exception. All 34
recorded call-2 replies are bare letters, which the grader reads correctly. So F4's effect on a run depends on how
often the judge's first reply is more than a bare letter.

### G1. The answering models' chat templates and checkpoints are not pinned

TASK.md names each answering model and says "each model's own chat template", with no revision or template hash. The
run records carry none either:
`python -I -c "import json; print(sorted({k for l in open('case/responses.jsonl', encoding='utf-8') for k in json.loads(l)}))"`
prints `['finish_reason', 'id', 'max_tokens', 'model', 'question_id', 'response', 'temperature']`. The template decides
whether `<think>` lands in the response text. In this run both thinking models write it there (24 responses), and that
is what lets E2 catch the three truncated reasonings. Under a template that puts `<think>` in the prompt, a truncated
reasoning would carry neither marker. All three pipelines would then send the start of the reasoning to the judge as
the predicted answer.

## Decision entries for the maintainers

All three concern the judge's grade (rubric clause K). The deterministic stages have none, so the replacement has no
switches. The score changes are measured on the stored run, from the contract pipeline's labels
(`python -I audit/scripts/decision_effects.py`).

| Entry | Reading 1 | Reading 2 | Stored cases, judge's grades (call 1, call 2) | Score change on the stored run | Proposed |
|---|---|---|---|---|---|
| `D-multiple-candidates` | A: the gold is given, and nothing says it is wrong | B: the answer also names a candidate that is not the gold (K2) | a06 puffin-13b `Either 1648 or 1658, I believe.` (B, A); a36 ibis-8b-think `Either iron or cobalt.` (A, A); a41 orca-7b `It is either 1 or 2.` (B, B) | Reading 1: orca-7b and puffin-13b +8.3 accuracy. Reading 2: ibis-8b-think −8.3 accuracy, −11.1 correct given attempted | Reading 2 |
| `D-unlisted-equivalent` | B: only the gold, the aliases and the four named differences count | A: any form that names the gold's referent counts | none | none | Reading 1 |
| `D-cut-off-answer` | C: a predicted answer cut before it names an answer gives no answer | B: it is an attempt, and not the gold | a47 heron-32b-think, cut at character 300 before its answer (C, C) | Reading 2: heron-32b-think −8.3 correct given attempted, −4.0 F-score, −8.3 not-attempted rate | Reading 1 |

The judge gives a36 grade A, a41 grade B, and a06 grade B on call 1 and A on call 2. The one judgment that flips on the
repeat is one of these three, which is evidence that the rubric leaves the case open.

## Other results

- The 300-character cut, which TASK.md specifies and all three pipelines apply, removes heron-32b-think's answer
  on a47. Its graded text names the Indian Ocean at character 358, so the judge never sees that answer.
- The output budget, 192 tokens for every model, ended 3 of ibis-8b-think's 12 responses inside their reasoning
  (a08, a20, a40). Under the contract these are extraction failures, which cap ibis-8b-think's accuracy at 75.0.
- Behaviour the task text does not specify, the same in all three pipelines (`python -I audit/scripts/unspecified.py`):
  a second row for one model and question is counted twice. An unknown `question_id` (KeyError), a `null` response
  (TypeError) and a judge back-end error (LookupError for an unrecorded prompt) each stop the whole run.
- Unverified inputs. Stop sequences: TASK.md says there are none, but no record field shows it. The judge model and
  its decoding settings in the stored run: `judge_replies.jsonl` has no model or settings field, and the pipeline code
  passes none to the judge client, so TASK.md step 3 is the only source. `audit/ISSUE.md` gives the command that would
  verify each one.
- Content-free responses (`python -I audit/scripts/content_free.py`, 9 kinds for each of the 12 questions): the
  reference and the replacement send all 108 to the judge as the contract says. The grader raises F3 on the three
  empty kinds, and F2 cuts the three multi-line kinds to their first line. The deployed judge cannot grade them here:
  the recorded judge has replies only for the stored prompts.

## Steps run

| Step | Status |
|---|---|
| 1. Pin the inputs | Run. Files and rows pinned by sha256; `audit/scripts/check_pins.py` passed before the first test run, before and after the panel run, and after the final test run. Skipped: commits and a Hugging Face dataset revision (none exist here) |
| 2. Contract | Run before any code was read; the hash was recorded at 22:28:22Z, and the contract has not changed since |
| 3. Fixtures | Run: 68 stage fixtures on 3 implementations and 2 CLI fixtures, with strict expected failures (`unittest`, since pytest is not installed) |
| 4. Reference comparison and stress tests | Run: the reference on every fixture, 13 properties, a fuzzer, content-free responses. Neither pipeline ships unit tests to cross-check |
| 5. Model panel | Run from the stored run only: 48 responses with their recorded replies, through every pipeline and every per-finding variant, with the judge repeated via call 2. Not run: new responses and a rerun of the answering models (no compute) |
| 6. Blinded review | Not run (no subagents). Done: the decision gate was pre-registered, and the 48-case sample was drawn (seed 61106) and frozen (6.1, 6.2) |
| 7. Report | This file; its summary is in `audit/ISSUE.md` |

Skipped because this exercise has no such systems: the issue tracker (`audit/ISSUE.md` stands in), a repository,
research branch and PRs, the immutable Hugging Face artifact (the frozen files and their hashes are in `audit/frozen/`
and `audit/ISSUE.md`), the job launcher, and the reviewer runs.

One deviation from the working-directory rule: the first listing command also wrote a list of the `case/` file names
to a temporary file under `/tmp`. Nothing outside the audit run's folder was read.

## Reproduce

```text
python -I audit/scripts/check_pins.py           # every pinned input and frozen file
python -I -m unittest discover -s audit/tests   # 247 tests: OK (expected failures=35)
python -I audit/scripts/stored_records.py       # what the stored run shows, reasoning masked
python -I audit/scripts/panel.py                # step 5; writes audit/work/panel/
python -I audit/scripts/fuzz.py                 # writes audit/work/fuzz_summary.json
python -I audit/scripts/content_free.py
python -I audit/scripts/unspecified.py
python -I audit/scripts/decision_effects.py
python -I audit/scripts/draw_sample.py          # rewrites audit/frozen/round1_* with the same bytes
```
