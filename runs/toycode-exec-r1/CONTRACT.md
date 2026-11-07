# ToyCode 1.0 grader contract

Version 1, written on 2026-11-06 from `case/TASK.md` (the grading rule quoted from the ToyCode README),
`case/prompt_template.txt`, `case/tasks.jsonl` and `case/tests.json`, before any line of `case/grade.py`,
`case/runner.py` or `case/reference/harness_ref.py` was read. Every later change is marked with its date and reason.
Version 2 (2026-11-06T23:31Z) adds C-exec 7 and changes C-task 2; both changes are marked "v2" below. Version 1 is
frozen as `audit/frozen/contract_v1.md`.

The grader turns one response row into one verdict, `pass` or `fail`, through five stages: code extraction (C-extract),
the import check (C-import), execution (C-exec), the tests (C-test), and the task verdict and score (C-task). C-data is
the contract between each stored test and the docstring that the model sees. Where the text allows two verdicts, the
contract states the proposed reading and names the decision entry (`D-<topic>`, listed at the end).

## Terms

- Response: the `response` string of one row.
- Line: the text between two line terminators. The terminators are `\n` and `\r\n` (see D-line-terminator).
- Fence line: a whole line that is three backticks, then zero or more tag characters (ASCII letters, digits, `_`,
  `+`, `-`), then zero or more spaces or tabs. Nothing comes before the backticks: an indented line is not a fence
  line. Four backticks are not three backticks and a tag.
- Bare fence line: a fence line with no tag (three backticks, then only spaces or tabs).

## C-extract (rule 1)

1. Scan the lines in order. The first fence line opens the block, and the first bare fence line after it closes the
   block. The code is the lines strictly between them, joined with `\n`, as written: no dedent, no stripping,
   nothing added.
2. If the response has no fence line, or no bare fence line after the first fence line, the response has no fenced
   block, and the code is the whole response, unchanged. An unclosed fence is therefore part of the code, and the code
   then fails to parse.
3. Only the first block counts; later blocks are ignored, even when the first block lacks the function.
4. A line that has the backticks after other text (`Here: ```python`), an indented fence, a fence with a tag character
   outside the list (`` ```python3.12 ``), and a `~~~` fence are not fence lines.

## C-import (rule 2)

1. The code is parsed with `ast.parse` under the grader's interpreter (CPython 3.12). If it does not parse
   (`SyntaxError`, or any other parse error such as a null byte), the task fails.
2. Every `import` and `from ... import` statement anywhere in the tree is checked: module level and inside functions,
   classes, `if`, `try`, `with` and loop bodies, whether or not the statement would run.
3. For `import a.b, c`, each listed module is checked; for `from a.b import c`, the module `a.b` is checked. A module is
   compared by the part of its name before the first dot, case-sensitively, with the prompt's list:
   `math, itertools, collections, functools, re, heapq, bisect, string, typing`. Any other module fails the task.
4. A relative import (`from . import x`, `from .math import sqrt`) is not on the list and fails the task.
5. `from __future__ import annotations` names the module `__future__`, which is not on the list, so the task fails.
6. Text that only looks like an import, inside a string, docstring or comment, is not a statement and never fails the
   check.
7. A call such as `__import__("os")` is not an import statement (see D-dynamic-import).

## C-exec (rule 3)

1. The code runs in a new Python process started from the grader's own interpreter, one process per response.
   Nothing that one response's code does (globals, monkey-patching, files) reaches another response's grading.
2. One budget of 4 seconds of wall time covers loading the code and running every test of the task. When the budget
   is reached, the task fails, whatever the tests showed before. (Whether interpreter start-up counts: D-time-start.)
3. Output that the code writes to stdout or stderr is not part of the rule and never changes a verdict.
4. The prompt allows helper functions. A helper's name, or any other module-level name the code defines, never
   changes a verdict unless it rebinds the entry point.
5. Ending the process early (`raise SystemExit`, `exit()`, a crash) never passes a test that did not run: a test
   passes only as C-test states. A test that did not run did not pass.
6. An exception raised while loading the code: D-load-error. Code under `if __name__ == "__main__":`: D-main-guard.
7. (v2) The stored tests are hidden from the model (TASK.md, "Tests"), so the code cannot read them while it runs: no
   file, variable or stream that the code can reach holds an expected value, apart from what each call's own
   arguments carry. A response that reads the expected values and returns them fails. Reason: version 1 left out
   this sentence of TASK.md; it was noticed while reading `case/grade.py`, which writes the tests into the child's
   working directory.

## C-test (rule 4)

1. Each test calls the entry point with a fresh deep copy of the test's `args`, as loaded from `tests.json` (arrays
   load as lists, `null` as `None`), as `entry_point(*args)`.
2. A test with `expected` passes when the call returns normally and `result == expected` is true, where `result` is
   the object the call returned (not a serialized copy) and `expected` is the JSON-loaded value. So `(1, 6)` does not
   equal `[1, 6]` and fails, `90.0 == 90` passes, and `True == 1` passes (D-numeric-type). A returned object whose
   class defines its own `__eq__`: D-eq-object.
3. A test with `raises` passes when the call raises an exception `e` with `isinstance(e, <built-in class of that
   name>)`: the built-in class itself or any subclass, including a subclass the response defines
   (`class DurationError(ValueError)`). A class the response names `ValueError` that does not derive from the
   built-in `ValueError` is not that class. Returning normally fails the test.
4. Any other exception raised by the call fails the test, including `BaseException` subclasses such as `SystemExit`
   and `KeyboardInterrupt`. An exception raised while comparing the result fails the test.
5. If the entry point is not defined after the code loads, every test fails.
6. Each test is judged on its own. A function that keeps state between calls is allowed; the fresh copy covers only
   the arguments.

## C-task (rule 5) and run-level rules

1. A response passes when the code is extracted, passes the import check, finishes within the time budget, and every
   stored test of its task passes. Otherwise it fails.
2. A model's score is 100 times the number of the 10 tasks it passes, divided by 10. A task with no response row for
   the model counts as not passed. (v2) A task counts once: if a file has two rows for one model and task and both
   pass, the model has passed one task, so a score cannot exceed 100. When such rows disagree, which one counts is
   outside the text. Reason: version 1 put every duplicate outside the text, but rule 5 counts tasks, which decides
   the case where the rows agree.
3. Every response row gets exactly one verdict. An error while grading one response fails that response only; it never
   stops the run or changes another response's verdict.
4. Extra fields in a response row are ignored.

## C-data: stored tests against the docstrings

Each stored test must follow from its task's docstring, the only task text the model sees.

| Task | Tests | Status |
|---|---|---|
| t01 `second_largest` | `[3,1,2]`→2, `[5,5,4]`→4, `[7]`→None, `[]`→None, `[-1,-2,-3]`→-2 | all follow (distinct values; fewer than two → None) |
| t02 `is_palindrome` | `racecar`→True, `hello`→False, `""`→True, `Was it a car or a cat I saw`→True, `ab`→False | test 4 holds only if case and spaces are ignored: D-palindrome-normalization; the others follow |
| t03 `parse_duration` | `1h30m`→90, `45m`→45, `2h`→120, `abc`→ValueError, `""`→ValueError | all follow |
| t04 `chunk` | `[1..5],2`→`[[1,2],[3,4],[5]]`, `[],3`→`[]`, `[1,2],5`→`[[1,2]]`, `[1],0`→ValueError | all follow (an empty list has no chunks) |
| t05 `median` | `[3,1,2]`→2, `[4,1,3,2]`→2.5, `[5]`→5, `[1,1,2,2]`→1.5 | all follow (even length: mean of the two middle values) |
| t06 `run_length` | `aaab`→`a3b1`, `""`→`""`, `abc`→`a1b1c1`, `zzzz`→`z4` | all follow |
| t07 `fib` | 0→0, 1→1, 10→55, 30→832040, 80→23416728348467685 | all follow (fib(80) checked by iteration) |
| t08 `merge_intervals` | `[[1,3],[2,6],[8,10]]`→`[[1,6],[8,10]]`, `[[1,4],[4,5]]`→`[[1,5]]`, `[]`→`[]`, `[[5,6],[1,2]]`→`[[1,2],[5,6]]` | all follow (touching intervals merge; output sorted) |
| t09 `flatten` | `[1,[2,[3,4]],5]`→`[1,2,3,4,5]`, `[]`→`[]`, `[[[]]]`→`[]`, `[[1],[2,[3]]]`→`[1,2,3]` | all follow |
| t10 `binary_search` | `[1,3,5,7],5`→2, `…,4`→-1, `[],1`→-1, `[2],2`→0, `[1,3,5,7],9`→-1 | all follow |

The time budget is part of the rule, so a correct function that cannot finish `fib(80)` within 4 seconds (naive
recursion) fails under the contract, and a float result such as Binet's formula (`float(fib(80))` is
23416728348467684) fails `==`.

## Decision entries

Each entry has two readings with an example of each verdict, and a proposed reading for the maintainers of the
evaluation that runs the grader.

- **D-palindrome-normalization** (C-data, t02 test 4). Reading A: "the string s reads the same forwards and
  backwards" means `s == s[::-1]`; `"Was it a car or a cat I saw"` is not a palindrome, so `return s == s[::-1]` is
  correct and the stored test is wrong. Reading B: the phrase sense, ignoring case and spaces (and perhaps
  punctuation); the stored test is right and `s == s[::-1]` fails. Proposed: A, because the docstring names "the
  string s" and states no normalization, and under B the set of ignored characters is unstated; the fix is to drop
  or correct test 4, or to state the normalization in the docstring (which changes the prompt).
- **D-line-terminator** (C-extract). Reading A: `\r\n` ends a line, so `` ```python\r\n `` is a fence line. Reading B:
  only `\n` ends a line, the `\r` is a trailing character that is neither a space nor a tab, so a CRLF response has
  no fence line and its whole text (with the backtick lines) is the code and fails to parse. Proposed: A. A lone
  `\r` as a terminator is not proposed.
- **D-load-error** (C-exec). Example: the code defines a correct `median` and then calls `print(median([]))` at module
  level, which raises `IndexError`. Reading A: an exception while loading the code fails the task. Reading B: the tests
  run against whatever the code defined before the exception, so the task passes. Proposed: A (the code is a program
  that must run; the prompt asks for the function definition, not for demo calls).
- **D-main-guard** (C-exec). Example: a correct `fib` followed by `if __name__ == "__main__": assert fib(3) == 3`
  (a wrong assertion). Reading A: the code is loaded as a module, the block does not run, and the task passes.
  Reading B: the code runs as a script, the block raises, and the task fails (with D-load-error A). Proposed: A, since
  rule 3 calls this step "loading the code".
- **D-dynamic-import** (C-import). Example: the code defines a correct function and also has the module-level line
  `os = __import__("os")`. Reading A (README): only import statements are checked, so a dynamic import of any module
  passes the check. Reading B (prompt: "You may import only these standard-library modules"): a dynamic import of a
  module off the list fails. Proposed: A for grading, since the README defines the check by statements; report
  dynamic imports of modules off the list as a count.
- **D-numeric-type** (C-test). Example: t03 returns `90.0` where the docstring says "as an int", or t02 returns `1`
  for `True`. Reading A (README): Python `==` decides, so both pass. Reading B (docstring): the value must have the
  type the docstring names, so both fail. Proposed: A, because the README states the comparison and its JSON loading
  rules.
- **D-eq-object** (C-test). Example: the function returns an instance of a class the response defines with
  `__eq__` returning `True` for everything. Reading A (README, literal): Python `==` says equal, so every `expected`
  test passes. Reading B: "the return value is equal to the expected value" asks for a value; an object that decides
  its own equality is not one, so the test fails. Proposed: B (require a value built from built-in types before
  comparing), because under A a content-free function passes every task that has no `raises` test.
- **D-time-start** (C-exec). Example: code whose loading and tests take 3.9 s after 0.2 s of interpreter start-up.
  Reading A: the budget runs from process start (4.1 s, fail). Reading B: the budget covers only loading the code and
  running the tests (3.9 s, pass). Proposed: A, since the parent can measure only that; the effect is limited to
  responses within a few tenths of a second of the limit.
