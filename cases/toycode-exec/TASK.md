# ToyCode: Python function completion graded by execution

ToyCode 1.0 has 10 small Python function tasks. The model sees a function signature with a docstring and writes the
function. The grader runs the model's code in a separate Python process, calls the function on the task's stored
tests, and passes the task only if every test passes.

## Files

| File | What it is |
|---|---|
| `prompt_template.txt` | the prompt the model sees, with `{prompt}` replaced by the task's `prompt` field |
| `tasks.jsonl` | the 10 tasks: `task_id`, `entry_point` (the function name), `prompt` (signature and docstring) |
| `tests.json` | the stored tests, a list per task id |
| `grade.py`, `runner.py` | the grader under audit (`runner.py` is the child process that `grade.py` starts) |
| `reference/harness_ref.py` | the benchmark authors' original harness, released with ToyCode 1.0 |
| `responses.jsonl` | 40 stored responses from the last evaluation run (4 models, 10 tasks each) |
| `MANIFEST.sha256` | sha256 of every other file in this directory |

## What the model sees

`prompt_template.txt` with `{prompt}` replaced by the task's `prompt`, sent as the only user message, with no system
prompt and the model's own chat template. For example, for `t07`:

```text
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def fib(n):
    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""
```

## Tests

`tests.json` maps each task id to a list of tests. A test is `{"args": [...], "expected": value}` or
`{"args": [...], "raises": "ValueError"}` (the name of a built-in exception class). The tests are hidden from the
model.

## Grading rule (from the ToyCode README)

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

## How the grader is run

From this directory:

```text
python grade.py                                   # grades responses.jsonl
python grade.py --responses other.jsonl --out verdicts.jsonl
```

It prints one row per model and, with `--out`, writes one JSON line per response with a verdict (`pass` or `fail`)
and a short detail. A response file is JSON lines with at least `id`, `model`, `task_id` and `response`. Grading the
40 stored responses takes about 15 seconds (two of them reach the time limit).

The reference harness:

```text
python reference/harness_ref.py tasks.jsonl tests.json responses.jsonl [verdicts_out.jsonl]
```

## Stored responses

`responses.jsonl` holds the 40 responses of the last evaluation run: models `kite-7b`, `lark-13b`, `wren-34b` and
`finch-8b`, one response per task. Fields: `id`, `model`, `task_id`, `response`, `finish_reason`, and the generation
settings, which were the same for every model: temperature 0, `max_tokens` 1024, no stop sequences, each model's own
chat template. None of these models emits a reasoning block.

## Pinned inputs

Every file in this directory, by the sha256 in `MANIFEST.sha256`. The evaluation runs the grader with CPython 3.12;
the grader and the reference need only the standard library and run offline.
