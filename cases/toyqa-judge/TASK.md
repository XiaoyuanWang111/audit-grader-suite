# ToyQA: short factual answers graded by an LLM judge

ToyQA 1.0 has 12 short factual questions, each with a gold target and, for some, other accepted answers. A model
answers each question once. A judge model grades each answer as correct, incorrect or not attempted, and the
benchmark reports accuracy, accuracy on attempted questions, and their F-score.

## Files

| File | What it is |
|---|---|
| `prompt_template.txt` | the prompt the answering model sees, with `{question}` replaced by the question |
| `questions.jsonl` | the 12 questions: `question_id`, `question`, `gold`, `aliases` (other accepted answers) |
| `judge_template.txt` | the judge prompt template, with the grading rubric |
| `judge_pipeline.py` | the pipeline under audit, the one the evaluation runs |
| `judges.py` | the two judge back ends for offline runs (not under audit): `RecordedJudge` and `FakeJudge` |
| `judge_replies.jsonl` | the judge model's replies in the stored run |
| `reference/pipeline_ref.py` | the benchmark authors' original pipeline, released with ToyQA 1.0 |
| `responses.jsonl` | 48 stored responses from the last evaluation run (4 models, 12 questions each) |
| `MANIFEST.sha256` | sha256 of every other file in this directory |

## What the answering model sees

`prompt_template.txt` with `{question}` replaced by the question, sent as the only user message, with no system
prompt and the model's own chat template:

```text
Answer the question below with a short answer. If you do not know the answer, say so.

Question: {question}
```

## What the judge sees

`judge_template.txt` with `{question}`, `{target}` and `{predicted_answer}` filled in, sent as the only user message.
It holds the rubric: grade A (CORRECT), B (INCORRECT) or C (NOT_ATTEMPTED), and reply with the letter only.

## Pipeline (from the ToyQA README)

1. Graded text. If the response contains `</think>`, the graded text is the text after the last `</think>`;
   otherwise it is the whole response. Leading and trailing whitespace is removed. A response that contains `<think>`
   but no `</think>` has reasoning that never closed: it gets the label `extraction_failure` and is not sent to the
   judge.
2. Judge prompt. The graded text is cut to its first 300 characters (Python string characters), and that text fills
   `{predicted_answer}`. `{target}` is the gold target, followed by ` (also accepted: X, Y)` when the question has
   aliases. `{question}` is the question.
3. Judge call. The judge model `judge-m1` gets the prompt as one user message, at temperature 0 with `max_tokens` 32.
   The evaluation's judge client caches replies by prompt and call number, so identical prompts get the same
   replies.
4. Reply parsing. The grade is the last capital letter A, B or C in the reply that stands alone: no ASCII letter or
   digit (A-Z, a-z, 0-9) directly before or after it. If a reply has no such letter, the judge is called again with
   the same prompt (call 2). If neither call gives a grade, the label is `judge_error`.
5. Labels. A is `correct`, B is `incorrect` and C is `not_attempted`. `extraction_failure` and `judge_error` are
   labels of their own.
6. Aggregation, per model over its 12 questions: accuracy = correct / 12; attempted = correct + incorrect;
   correct given attempted (cga) = correct / attempted, or 0 when nothing was attempted; F-score = harmonic mean of
   accuracy and cga, or 0 when both are 0; not-attempted rate = not_attempted / 12. Extraction failures and judge
   errors count in the denominator of accuracy, are never correct, are not attempts, and are reported as counts.

## How the pipeline is run

From this directory:

```text
python judge_pipeline.py                          # recorded judge, responses.jsonl
python judge_pipeline.py --judge fake --responses other.jsonl --out labels.jsonl
```

It prints one row per model and, with `--out`, writes one JSON line per response with its label, the grade, the
number of judge calls and the prompt's sha256. A response file is JSON lines with at least `id`, `model`,
`question_id` and `response`. The module's functions (`extract_graded_text`, `render_prompt`, `call_judge`,
`parse_grade`, `grade_response`, `aggregate`) can be imported for tests.

The reference pipeline:

```text
python reference/pipeline_ref.py questions.jsonl responses.jsonl [recorded|fake] [labels_out.jsonl]
```

## Judge back ends (not under audit)

`--judge recorded` replays `judge_replies.jsonl`: for each distinct judge prompt of the stored run, the reply of
call 1 and of call 2 at the deployed settings, keyed by the sha256 of the UTF-8 prompt. The stored run used call 1,
and call 2 only as the retry of step 4; call 2 also serves as a repeat of each judgment. It covers only the prompts
of the stored run, and raises `LookupError` for any other prompt. `--judge fake` is a deterministic stand-in for
tests, described in the docstring of `judges.py`; it is not a model of the deployed judge.

## Stored responses

`responses.jsonl` holds the 48 responses of the last evaluation run: models `orca-7b`, `puffin-13b`,
`heron-32b-think` and `ibis-8b-think`, one response per question. The two `-think` models write their reasoning
inside `<think>` ... `</think>` in the response text; the serving stack has no reasoning parser and returns no
separate reasoning field. Fields: `id`, `model`, `question_id`, `response`, `finish_reason` (`stop`, or `length`
when the output budget ran out), and the generation settings, which were the same for every model: temperature 0,
`max_tokens` 192, no stop sequences, each model's own chat template.

## Pinned inputs

Every file in this directory, by the sha256 in `MANIFEST.sha256`; the judge model and its settings as in step 3.
The pipelines need only the Python 3 standard library and run offline.
