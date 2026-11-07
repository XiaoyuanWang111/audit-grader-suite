# ToyMath: arithmetic word problems with a numeric answer

ToyMath 1.0 is a 12-problem benchmark of short arithmetic word problems. Each problem has one numeric reference
answer. A model answers each problem once, and a programmatic grader reads the final answer from the response and
compares it with the reference answer.

## Files

| File | What it is |
|---|---|
| `prompt_template.txt` | the prompt the model sees, with `{problem}` replaced by the problem text |
| `problems.jsonl` | the 12 problems: `problem_id`, `problem`, `answer` (the reference answer, a decimal string) |
| `grade.py` | the grader under audit, the one the evaluation runs |
| `reference/grade_ref.py` | the benchmark authors' original grader, released with ToyMath 1.0 |
| `responses.jsonl` | 48 stored responses from the last evaluation run (4 models, 12 problems each) |
| `MANIFEST.sha256` | sha256 of every other file in this directory |

## What the model sees

`prompt_template.txt` with `{problem}` replaced by the `problem` field, sent as the only user message, with no system
prompt and the model's own chat template:

```text
Solve the problem below. Show your reasoning, then end your response with a final line of the form

Answer: <number>

Write the number with digits only, without units or currency symbols. You may use commas as thousands separators (for example 12,500) and a decimal point (for example 3.75).

Problem: {problem}
```

## Scoring rule (from the ToyMath benchmark card)

1. Only the final answer is graded. The answer line is the last line of the response that begins with `Answer:`
   (whitespace before it is allowed, and the match is case-sensitive; lines are split as Python's `str.splitlines`
   splits them). Lines after the answer line are ignored.
2. The answer is the number given on the answer line. A number is an optional `-` (hyphen-minus), then digits, then
   optionally a decimal point and more digits. Commas in the number are ignored, so `12,500` and `12500` are the
   same number.
3. A response with no answer line, or with no number on its answer line, is incorrect.
4. A response is correct when its answer is within 0.01 of the reference answer.
5. A model's score is the percentage of the 12 problems that it answers correctly.

## How the grader is run

From this directory:

```text
python grade.py                                   # grades responses.jsonl against problems.jsonl
python grade.py --responses other.jsonl --out verdicts.jsonl
```

It prints one row per model (counts and the score) and, with `--out`, writes one JSON line per response with the
extracted answer and a verdict: `correct`, `incorrect`, or `no_answer`. A response file is JSON lines with at least
`id`, `model`, `problem_id` and `response`.

The reference grader:

```text
python reference/grade_ref.py problems.jsonl responses.jsonl [verdicts_out.jsonl]
```

## Stored responses

`responses.jsonl` holds the 48 responses of the last evaluation run: models `alpha-7b`, `beta-14b`, `gamma-32b` and
`delta-8b`, one response per problem. Fields: `id`, `model`, `problem_id`, `response`, `finish_reason` (`stop`, or
`length` when the output budget ran out), and the generation settings, which were the same for every model:
temperature 0, `max_tokens` 256, no stop sequences, each model's own chat template. None of these models emits a
reasoning block, and the serving stack has no reasoning parser.

## Pinned inputs

Every file in this directory, by the sha256 in `MANIFEST.sha256`. The grader and the reference need only the Python 3
standard library (3.8 or later) and run offline.
