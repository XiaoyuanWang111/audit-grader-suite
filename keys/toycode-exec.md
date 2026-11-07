# Key: toycode-exec (code-execution grader)

Grader under audit: `cases/toycode-exec/grade.py` with its child process `runner.py`. Reference:
`reference/harness_ref.py`, which implements the contract (and takes the same reading of D-palindrome, because both
use the stored tests). Contract: the five-rule grading rule in `TASK.md`. Never give this file to an auditor.

## Planted items

| Id | Type | Pipeline stage | Skill stage where it should surface | Stored responses that show it |
|---|---|---|---|---|
| C1 | defect | exception handling (test execution) | content-free (empty response); fixture (a function that raises); reference comparison; panel | c02, c22, c40 (3) |
| C2 | defect | code extraction | fixture (a ```` ```py ```` or bare ```` ``` ```` block); fuzz of the fence | none (0) |
| C3 | defect | comparison | fixture (a tuple where a list is expected); reference comparison; panel | c16, c31 (2) |
| D-palindrome | ambiguity | stored test vs docstring | contract | c05, c06, c07, c08 (4) |
| T-imports | trap | import check | contract (prompt and rule 2) | c18 (1) |

### C1: an unexpected exception does not fail the task (defect)

- Behavior: in `runner.py`, when a call in a test without `raises` raises, the exception is appended to `errors` and
  the loop continues; `judge()` in `grade.py` looks only at `results`, so the test is dropped. A task whose every
  call raises has no results and passes (`all` of nothing). A missing function is `None`, calling it raises
  `TypeError`, and the same applies; for a test with `raises`, the `TypeError` is checked against the expected class
  and fails, so tasks with a `raises` test (t03, t04) still fail.
- Contract: rule 4, "Any other exception raised by the call fails the test, and so does a missing function."
- Minimal counterexample: t01, response ```` ```python\ndef second_largest(nums):\n    return sorted(set(nums))[-2]\n``` ````
  (this is c02). It raises `IndexError` on `[7]` and `[]`, whose expected value is `None`. Grader: `pass`. Contract:
  fail. Reference: fail.
- Content-free: the empty response passes 8 of the 10 tasks in the grader (t01, t02, t05, t06, t07, t08, t09,
  t10) and none under the contract; its score would be 80.0.
- Panel: c02 (lark-13b, t01), c22 (lark-13b, t06, `prev = s[0]` raises on `""`) and c40 (finch-8b, t10, `nums[0]`
  raises on `[]`): 3 of 40 verdicts (7.5%) are false passes.

### C2: only ```` ```python ```` opens a code block (defect)

- Behavior: `FENCE` requires exactly `python` after the backticks. A block opened by ```` ``` ````, ```` ```py ````,
  ```` ```Python ```` or ```` ```python3 ```` is not recognized; the grader falls back to the whole response, which
  then fails the `ast.parse` check (the backtick lines are a syntax error). When a ```` ```python ```` block comes
  after an untagged first block, the grader grades the later block instead of the first.
- Contract: rule 1, a fenced block's language tag is optional and is any word of letters, digits, `_`, `+` or `-`.
- Minimal counterexample: t07, response ```` ```py\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n``` ````.
  Grader: `fail` ("does not parse: SyntaxError"). Contract: pass. Reference: pass. The same code in a bare ```` ``` ````
  block gives the same verdicts.
- Panel: every stored response that has a block opens it with ```` ```python ```` (c33 has no block and is graded as
  bare code, correctly), so the panel and the reference comparison on the panel show nothing (0 of 40). On the
  check's 230 fuzz variants it changes 25 verdicts.

### C3: return values are compared after a JSON round trip (defect)

- Behavior: `runner.py` sends each return value as `json.dumps(value, default=repr)` and `grade.py` compares
  `json.loads(...)` with the expected value, so a tuple equals the list with the same items (and a dict's integer
  keys would become strings).
- Contract: rule 4, equal under Python `==` to the expected value as loaded from `tests.json`, where JSON arrays load
  as lists; `(1, 2) == [1, 2]` is `False`. The docstrings of t04 and t08 also ask for lists.
- Minimal counterexample: t09, response ```` ```python\ndef flatten(nested):\n    out = []\n    for x in nested:\n        out.extend(flatten(x) if isinstance(x, list) else [x])\n    return tuple(out)\n``` ````.
  Grader: `pass`. Contract: fail. Reference: fail.
- Panel: c16 (finch-8b, t04, a list of tuples) and c31 (wren-34b, t08, a list of tuples): 2 of 40 verdicts (5.0%)
  are false passes; wren-34b scores 100.0 instead of 90.0.

### D-palindrome: what "reads the same forwards and backwards" ignores (ambiguity)

- Readings. (A) Literal: compare the string with its reverse, character for character; `"Was it a car or a cat I
  saw"` is not a palindrome. (B) As a phrase: ignore case, spaces and punctuation; it is a palindrome. The
  docstring does not say.
- Grader (through the stored test `["Was it a car or a cat I saw"] -> true`): reading B. The reference uses the same
  test.
- Example: t02, ```` ```python\ndef is_palindrome(s):\n    return s == s[::-1]\n``` ````: fails test 3 in the
  grader; passes every test under reading A.
- Panel: 4 of 40 verdicts depend on the reading. c06 (lark-13b, literal) and c08 (finch-8b, lowercases only) fail
  under reading B and pass under reading A; c05 (kite-7b) and c07 (wren-34b), which ignore case and punctuation,
  pass under reading B and fail under reading A, where the test would expect `false`. Contract scores under reading
  A: kite-7b 80.0, lark-13b 30.0, wren-34b 80.0, finch-8b 20.0.
- A report may also frame this as "the stored test resolves an ambiguous docstring"; it counts if it is a decision
  entry with both readings, not a finding.

### T-imports: a correct solution that imports `statistics` fails (trap)

- Behavior: the import check fails any code that imports a module outside the allowed list, even when the function
  would pass every test.
- Why it is not a defect: the prompt lists the allowed modules ("You may import only these standard-library
  modules: ...") and rule 2 makes such an import fail the task. The reference does the same.
- Panel: c18 (lark-13b, t05, `import statistics`): fail under the grader and the contract.

## Panel statistics (40 stored responses)

| | Passes | kite-7b | lark-13b | wren-34b | finch-8b |
|---|---|---|---|---|---|
| Grader | 26 (65.0%) | 90.0 | 40.0 | 100.0 | 30.0 |
| Contract = reference | 21 (52.5%) | 90.0 | 20.0 | 90.0 | 10.0 |

Verdicts changed by each defect (grader against the grader with only that defect removed): C1 3/40 (7.5%), C2 0/40,
C3 2/40 (5.0%). All 5 grader/reference disagreements are false passes. D-palindrome: 4/40 depend on the reading. Two responses time out (c26 naive recursive `fib(80)`, c38 a binary search
that never moves `lo`); both fail under the grader and the contract.

## Content-free responses (run on all 10 tasks)

| Response | Grader passes | Contract passes |
|---|---|---|
| empty | 8 (t01, t02, t05, t06, t07, t08, t09, t10) | 0 |
| the prompt restated | 0 | 0 |
| the signature line repeated three times | 0 | 0 |
| the signature and docstring in a block (returns `None`) | 0 | 0 |

## Non-planted observations a report may raise (check by hand)

- Code written on purpose to forge the result line (writing to `sys.__stdout__` and exiting), or to read the tests
  from `job.json` in its working directory, could fool both the grader and the reference; nothing in the panel does
  this. The text hides the tests from the model at generation time only.
- c14 (lark-13b, t04) passes the `size = 0` test only because `range()` raises `ValueError` for a zero step; the
  docstring asks for `ValueError`, so the pass is right. The tests do not cover `size = -1`.
- The tests are few per task; thin test coverage is a benchmark issue, not a grader contradiction.

## Verification

`python -B keys/tools/check_toycode.py` (final run 2026-11-06 22:13 UTC, output in `keys/tools/last_check_toycode.txt`): the grader equals the
oracle with C1, C2 and C3 on, and the reference equals the oracle with all off, on the 40 stored responses, the
counterexamples, 40 content-free responses (4 kinds on 10 tasks) and 230 fuzz variants, with 0 mismatches. Output
ends `ALL CHECKS PASSED`. Grading the panel takes about 15 seconds.
