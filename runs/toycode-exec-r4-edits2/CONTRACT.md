# ToyCode 1.0 grader contract

Written from `case/TASK.md` (the README grading rule), `case/prompt_template.txt`, the task prompts in
`case/tasks.jsonl` and the stored tests in `case/tests.json`, before reading `grade.py`, `runner.py` or
`reference/harness_ref.py`. Each clause has an id, used by fixtures and findings.

## Unit, labels and denominator

- A trial is one stored response for one (model, task) pair. The grader has two labels, `pass` and `fail`.
- A model's score is 100 x (number of the 10 tasks whose response passes) / 10. A task with no response for a
  model counts as `fail`; the denominator is always 10 (C-AGG-1).
- Scored coverage: every (model, task) pair that has a response gets exactly one verdict (C-AGG-2).
- None of the models emits a reasoning block, so there is no end-of-reasoning marker and no extraction failure
  label; a response whose code cannot be extracted or parsed is `fail`.

## C-EXT: code extraction (graded text)

- C-EXT-1. Lines are the response split at line breaks. A fence line is a whole line consisting of exactly three
  backticks at the start of the line, then an optional language tag of ASCII letters, digits, `_`, `+` or `-`, then
  optional trailing spaces or tabs. Regex for an opening fence: `^```[A-Za-z0-9_+-]*[ \t]*$`. A closing fence is a
  line `^```[ \t]*$` (no tag).
- C-EXT-2. A line with leading spaces before the backticks, four or more backticks, or a tag with any other
  character (a space inside it, `{`, `.`, `=`) is not a fence line.
- C-EXT-3. The code is the lines strictly between the first opening fence and the next closing fence after it.
  Later blocks are ignored, even if they hold more code.
- C-EXT-4. An opening fence with no closing fence after it does not make a fenced block. If the response has no
  fenced block, the whole response is the code (a response that is bare code passes extraction).
- C-EXT-5. An empty fenced block gives empty code: it parses, defines no function, and fails every test.
- Decision D-crlf: whether `\r\n` ends a line, so that "```python\r" is a fence line. Proposed: yes.

## C-IMP: import check

- C-IMP-1. The code is parsed with Python's `ast` (CPython 3.12). A parse failure fails the task.
- C-IMP-2. Every `import` and `from ... import` statement anywhere in the tree (module level, inside functions,
  `if`, `try`, class bodies) is checked. Allowed modules: math, itertools, collections, functools, re, heapq,
  bisect, string, typing. A name is compared by its part before the first dot (`collections.abc` -> `collections`,
  allowed; `os.path` -> `os`, not allowed). `import a, b` fails if either is not allowed.
- C-IMP-3. A relative import (`from . import x`, `from .m import x`) fails.
- C-IMP-4. `from __future__ import annotations` names `__future__`, which is not on the list: fail.
- C-IMP-5. An alias does not matter (`import math as m` is allowed; `import os as math` is not).
- Decision D-dynamic-import: the prompt says "You may import only these standard-library modules"; the README
  check names only `import` statements. Reading A (README): `__import__("os")` or `importlib` reached without an
  import statement passes the import check. Reading B (prompt): any import mechanism counts, so it fails.
  Proposed: A for the import check (the README defines the check), and report the exposure separately.

## C-EXE: execution

- C-EXE-1. The code runs in a fresh Python process with the grader's own interpreter (`sys.executable`), one
  process per task, so one response cannot affect another response's verdict.
- C-EXE-2. The limit is 4 seconds of wall time for the whole task: loading the code plus every test. A task that
  reaches the limit fails. The budget is not per test: three tests of 1.5 s each make 4.5 s and fail.
- C-EXE-3. An exception while loading the code (top-level code raising) leaves the function missing or the
  process dead; the task fails.
- C-EXE-4. What the code prints (stdout or stderr), at top level or inside the function, does not change the
  verdict. Output that looks like grader output must not turn a failing task into a pass.
- C-EXE-5. The verdict reflects the actual calls: if the process exits or is killed before every test has run
  and passed, the task fails; code that ends the process early (`exit()`, `raise SystemExit`, `os._exit`) or that
  tampers with the harness cannot produce a pass for tests that did not pass.

## C-TST: tests

- C-TST-1. The function is the name `entry_point` defined by the code. If it is missing (or not callable), every
  test fails.
- C-TST-2. Each test calls the function with a fresh (deep) copy of the test's `args`, so a function that mutates
  its arguments cannot change another test's inputs or expected value.
- C-TST-3. A test with `expected` passes iff the return value `== expected` in Python, where `expected` is the
  value as loaded by `json`: arrays are lists, `null` is `None`, `true`/`false` are booleans, numbers are int or
  float. Consequences: `2.0` vs `2` passes; `True` vs `1` passes; a tuple vs a list fails (`(1, 2) != [1, 2]`); a
  list of tuples vs a list of lists fails; `None` vs `[]` fails.
- C-TST-4. A test with `raises: "X"` passes iff the call raises an instance of the built-in class `X` or of a
  subclass. A normal return fails it; another exception (for example plain `Exception` for `ValueError`) fails it.
- C-TST-5. Any other exception raised by a call fails that test, including `BaseException` subclasses such as
  `SystemExit` and `KeyboardInterrupt`.
- Decision D-eq-object: the README says Python `==`. Reading A (literal): a return value whose own `__eq__`
  answers True passes, whatever its type. Reading B (value): the return value must be plain data equal to the
  expected value. Proposed: A only for the built-in types the task's docstring names (numbers, str, bool, None,
  list); an object of a user-defined class whose `__eq__` always answers True does not "return" the value and
  fails. Only matters for deliberate reward hacking; no stored response does it.

## C-TASK: the stored tests against each task's docstring

Each stored test must follow from the docstring the model sees.

- t01 second_largest: all five tests follow (`[]` and `[7]` have fewer than two distinct values -> None).
- t02 is_palindrome: `"Was it a car or a cat I saw"` -> True does not follow from "reads the same forwards and
  backwards" literally: the string differs from its reverse (case and spaces). It holds only if case and spaces
  are ignored. Decision D-palindrome-normalization. Reading A (literal, `s == s[::-1]`): the expected value
  should be False. Reading B (normalized: ignore case and non-alphanumerics): True, as stored. Proposed: A,
  because the docstring names no normalization and the tests are hidden from the model; the fix is to state the
  normalization in the docstring or to change the test.
- t03 parse_duration: follows ("abc" and "" are not durations -> ValueError).
- t04 chunk: follows. Coverage note: no test with a negative size.
- t05 median: follows (2 or 2.0 both equal 2).
- t06 run_length: follows.
- t07 fib: follows; fib(80) = 23416728348467685 checked.
- t08 merge_intervals: follows; the docstring asks for a list of `[start, end]` lists, so tuples fail.
- t09 flatten: follows.
- t10 binary_search: follows.

## Agent-task questions (TASK.md is a code task, not an agent task)

- There is no answer file; the graded state is the response text. An empty response is bare code `""`: it
  parses, has no function, and fails.
- Every stored response is in the denominator, including ones with `finish_reason` other than `stop`
  (a truncated response fails if its code does not parse or its tests fail).
- The grader may not use the network; the README says the grader runs offline. The model's code has no stated
  network permission; with only the allowed modules it has no network access unless D-dynamic-import reading A
  lets it reach `socket`.
