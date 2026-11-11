# ToyCode 1.0 grader audit

Audit of `case/grade.py` with its child `case/runner.py` (the grader under audit), against the task text in
`case/TASK.md`, following `skill/SKILL.md`. Written 2026-11-11 (UTC). All commands below run from this
directory's parent, the working directory `P_v3_toycode-exec`, in Git Bash with CPython 3.12.10.

## Error rate and effect on scores

- **No reviewer-consensus error rate yet.** Step 6 (two blinded reviewers) did not run, because this exercise
  cannot start subagents. The review sample is drawn and frozen (all 40 stored verdicts, hashes in
  `audit/ISSUE.md`).
- **Contract-measured error on the stored panel: 5 of 40 verdicts (12.5%), all false passes, all unambiguous.**
  Three come from F1 (c02, c22, c40: a call raised an exception and the grader ignored it) and two from F2 (c16,
  c31: tuples returned where the docstring asks for lists). The replacement grader built from the contract finds
  them, and the benchmark authors' reference harness, written independently of this audit, gives the same 40
  verdicts as the replacement under the stored tests. These are counts over the whole stored panel, not
  estimates from a sample. Under the proposed reading of decision D-palindrome-normalization, 4 more stored
  verdicts change (9 of 40).
- **Effect on scores (percent of the 10 tasks):**

  | Grader | kite-7b | lark-13b | wren-34b | finch-8b |
  |---|---|---|---|---|
  | Grader under audit (`grade.py`) | 90 | 40 | 100 | 30 |
  | Same, rerun with identical settings | 90 | 40 | 100 | 30 |
  | Reference (`harness_ref.py`) | 90 | 20 | 90 | 10 |
  | Replacement, stored t02 test (`--palindrome normalized`) | 90 | 20 | 90 | 10 |
  | Replacement, all proposed readings | 80 | 30 | 80 | 20 |
  | Grader minus replacement (stored test), points | 0 | +20 | +10 | +20 |

  The grader inflates three of four models by 10 to 20 points and ranks wren-34b (100) above kite-7b (90),
  which the contract ties at 90. The rerun changed no verdict (byte-identical verdict files), so every one of
  these changes exceeds the rerun difference of 0.
- **Exposure beyond the panel.** Under the grader, an empty response scores 80% and a function that always
  raises `ValueError` scores 100%; the reference and the replacement give both 0%. Candidate code can also forge
  the grader's result line without any import statement (F4), and one response can stop the whole run (F5).
- **Recommendation: fix the grader.** Details at the end. The step-6 gate recorded in `audit/ISSUE.md` has not
  been evaluated, so this recommendation stands on the contract, the fixtures and the reference cross-check
  until the review runs.

## What this run did and skipped

| Step | Done | Skipped or substituted |
|---|---|---|
| Records | `audit/ISSUE.md` holds the pins, contract hash and time, decisions, findings and frozen-sample hashes | No issue tracker (`file-issue`), no repository, research branch, `manage-pr` or Hugging Face dataset: fixtures live in `audit/tests/`, frozen samples in `audit/frozen/`. The issue-writing style guide (`docs/dev-guide/writing-style/issues.md`) is not in this run. |
| 1 Pin inputs | All 8 case files match `MANIFEST.sha256` (checked at start and before the panel); row hashes per task, test list and response | Model revisions, chat templates and the grading host are not recorded anywhere (G1) |
| 2 Contract | `audit/CONTRACT.md`, sha256 `f2f85c98...632b1b`, recorded 01:11:23Z before any code was read | |
| 3 Fixtures | 65 fixtures, 1192 unittest tests including 330 metamorphic cases; replacement grader with one switch per decision | pytest is not installed, so the tests use `unittest.expectedFailure` (strict like `xfail(strict=True)`) |
| 4 Reference and stress | Reference run on every fixture and the panel; metamorphic suite; fuzzing; content-free responses | Neither grader nor reference has unit tests to replay |
| 5 Panel | Stored 40 responses graded by every grader and every decision switch, plus reruns | No compute: no new responses, one decoding setting only |
| 6 Review | Gate recorded, sample drawn (seed 20261111), frozen and rendered into two batches | Reviews, consensus, error-rate intervals and kappa not run (no subagents) |

## Inputs (step 1)

Pinned by sha256 in `audit/ISSUE.md`: grader `grade.py` (`ea020bdd...`), `runner.py` (`36953b5b...`), reference
`harness_ref.py` (`4b502d23...`, no upstream commit given), prompt template, 10 tasks, 45 stored tests, 40 stored
responses, TASK.md. Generation settings come from the stored rows: temperature 0, `max_tokens` 1024, no stop
sequences, no reasoning block; all 40 rows have `finish_reason` `stop`. From the code: the grader runs its child
with `sys.executable`, a 4 s `subprocess.run` timeout over the whole child process, the parent environment plus
`PYTHONIOENCODING=utf-8`, and UTF-8 job files, so grading does not depend on the locale. Unpinned: OS,
interpreter patch version, hardware, hash seed, model revisions and chat templates (G1, G2).

## Findings

Shares are over the 40 stored verdicts. "Reference" is the authors' harness. Each command prints the grader's
per-model table; each counterexample row has its own model name, so its row shows its verdict (`passed 1` is a
pass). The exact inputs are the JSON lines in `audit/repro/`, written by `python -B audit/scripts/make_repro.py`.

### F1. A call that raises, or a missing function, counts as a passed test

- Stage: test judging. `runner.py` lines 30-35 put a call that raises on an `expected` test into `errors`;
  `grade.py` `judge` (lines 75-85) reads only `results`, so those tests are skipped. A missing function makes
  every call raise `TypeError`, so it is skipped too. A task without a `raises` test then passes with no working
  code; a task with one passes if the code raises the named exception everywhere.
- Contract broken: C-TST-5 ("any other exception raised by the call fails the test") and C-TST-1 (a missing
  function fails every test).
- Shows it: stored c02 (lark-13b t01, `IndexError` on `[7]` and `[]`), c22 (lark-13b t06, `IndexError` on `""`),
  c40 (finch-8b t10, `IndexError` on `[]`); fixtures `tst:26f75b79d7ee667c`, `tst:ba3b97bed65ce948`,
  `tst:81515ec9358b149b`, `tst:485e1e2927060b84`, `tst:abf33df0b0713d5c`, `ext:9637760b9523ebdb`,
  `ext:f60ccccab4330d3c`; metamorphic edits X03 (rename), X04 (raise first), X10 (empty block), X11 (empty
  response) on the 8 tasks without a `raises` test.
- Share: 3 of 40 (7.5%), all false passes. Reference: correct (fails all of them).
- Counterexample, exact input (task t07, contract verdict fail):
  `{"id": "F1-raise-ValueError", "model": "F1-raise-ValueError", "task_id": "t07", "response": "```python\ndef fib(n):\n    raise ValueError\n```"}`
- Command: `python -B case/grade.py --responses audit/repro/F1_ignored_exceptions.jsonl` prints a pass
  (`1     10    10.0`) on every row: `F1-empty-response` (response `""`), `F1-raise-ValueError`,
  `F1-t03-raise-ValueError`, `stored-c02`, `stored-c22`, `stored-c40`.
- Whole benchmark: `python -B case/grade.py --responses audit/repro/F1_whole_benchmark.jsonl` prints
  `F1-always-ValueError      10     10   100.0` (each task's function is `def <name>(*args): raise ValueError`)
  and `F1-empty-response       8     10    80.0` (10 empty responses).

### F2. Return values are compared after a JSON round trip

- Stage: comparison. `runner.py` line 39 sends `json.dumps(value, default=repr)`; `grade.py` line 83 compares
  `json.loads(...)` with the expected value. A tuple arrives as a list, and any value JSON cannot encode arrives
  as its `repr` string.
- Contract broken: C-TST-3 (Python `==` against the value as loaded from `tests.json`; `(1, 2) != [1, 2]`), and
  the t04 and t08 docstrings, which ask for a list of lists.
- Shows it: stored c16 (finch-8b t04, list of tuples) and c31 (wren-34b t08, list of tuples); fixtures
  `tst:e0033cc11397a9c3`, `tst:b1c25bb7e2130863`, `tst:5833eaaf4eef5e60`; metamorphic X07 (t04, t08, t09) and X08
  (t06).
- Share: 2 of 40 (5%), both false passes. Reference: correct (compares with `==` in the child).
- Counterexample, exact input (stored c16, contract verdict fail):
  `{"task_id": "t04", "response": "```python\ndef chunk(items, size):\n    if size < 1:\n        raise ValueError(\"size must be positive\")\n    return [tuple(items[i:i + size]) for i in range(0, len(items), size)]\n```"}`
- Command: `python -B case/grade.py --responses audit/repro/F2_json_round_trip.jsonl` prints a pass for
  `stored-c16`, `stored-c31` and `F2-repr-proxy` (a `run_length` that returns an object whose `repr` is the
  right string).

### F3. Only a block tagged exactly `python` is extracted

- Stage: code extraction. `grade.py` line 25: `^```python[ \t]*\n(.*?)^```[ \t]*$`. A block tagged `py`,
  `Python`, `python3`, or with no tag is not recognized, so the whole response becomes the code and fails to
  parse; and when the first block is not tagged `python`, the grader skips it and grades a later one.
- Contract broken: C-EXT-1 (any tag of ASCII letters, digits, `_`, `+`, `-`, or none) and C-EXT-3 (the first
  fenced block is the code).
- Shows it: fixtures `ext:44d2149d071d7b9f` (py), `ext:68f2f4bc16ee5f96` (no tag), `ext:9fec917cb39354ee`
  (Python), `ext:3193a7810b73469f` (python3), `ext:99e6e02bfce07de2` (`py+3_x-y`), `ext:5a5ab3b3142274cb`
  (bash block first); metamorphic I05-I08 (40 false fails) and X05 (10 false passes).
- Share: 0 of 40 (39 stored responses open with ```` ```python ````, one has no fence). The stored field that
  measures it on a larger panel is the opening fence line of `response`. Reference: correct.
- Counterexamples, exact inputs (task t07):
  `"```py\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```"`
  (contract pass) and
  `"```bash\npip install toycode\n```\n\n```python\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```"`
  (contract fail: the first block is not Python).
- Command: `python -B case/grade.py --responses audit/repro/F3_python_tag_only.jsonl` prints
  `F3-bash-block-first       1     10    10.0`, `F3-no-tag          0     10     0.0`,
  `F3-tag-py          0     10     0.0`.

### F4. Candidate code can forge the result line (grader and reference)

- Stage: execution protocol. The candidate is `exec`-ed in the same process that reports the verdict, sharing
  its builtins and file descriptor 1, and the parent trusts the last result line on stdout. Two ways that need no
  import statement: write a fake line to fd 1 with `open(1, "w", closefd=False)` and raise `SystemExit`, which
  `except Exception` does not catch, so the child's own line is never printed; or replace `print` in the shared
  builtins dictionary, so the child's final `print` emits the fake line.
- Contract broken: C-EXE-5 (a pass needs every test to have run and passed).
- Shows it: fixtures `exe:8f92ceaa6a9122fc`, `exe:d839c8f6eb570244`.
- Share: 0 of 40 (no stored response tampers). Reference: same defect; both exploits pass it.
- Counterexample, exact input (task t07, response, contract verdict fail):

  ~~~text
  ```python
  def fib(n):
      out = open(1, "w", closefd=False)
      out.write('@@RESULT@@ {"loaded": true, "results": [], "errors": []}' + "\n" + '<<toycode-result>>{"ok": true}' + "\n")
      out.flush()
      raise SystemExit

  ```
  ~~~

- Command: `python -B case/grade.py --responses audit/repro/F4_forged_result.jsonl` prints a pass for
  `F4-builtins-print` and `F4-fd1-systemexit`;
  `python -B case/reference/harness_ref.py case/tasks.jsonl case/tests.json audit/repro/F4_forged_result.jsonl`
  prints `10.0` for both.
- The replacement keeps the expected values out of the child process, reads a result file rather than stdout,
  and compares in the parent, so a forged result can only claim return values the code could have computed.

### F5. One response can stop the whole run (grader and reference)

- Stage: run robustness. `check_imports` catches only `SyntaxError` and `ValueError` from `ast.parse`, but deep
  nesting raises `RecursionError` (or `MemoryError`); 2,997 characters (`"-" * 2996 + "1"`) are enough on CPython
  3.12.10. A forged result line that is not valid JSON makes `json.loads` raise in the parent. Either exception
  leaves `main`: the run exits with status 1, prints no table and writes no verdict file, for every model.
- Contract broken: C-IMP-1 (a parse failure fails the task) and C-EXE-5; the skill counts a grader exception as
  a grading failure for that response, not a stopped run.
- Shows it: fixtures `rob:e638a842d03c255d`, `rob:782119c6cc58d748`; fuzzing (400 random responses, seed
  20261111): 7 grader exceptions (5 `RecursionError`, 2 `JSONDecodeError`), 20 reference exceptions (14
  `RecursionError`, 6 `TypeError` from a forged `[]` payload), 0 in the replacement.
- Share: 0 of 40 (the stored run completed). Reference: same defect.
- Counterexample, exact input: `{"task_id": "t07", "response": "<2996 hyphens>1"}`, next to a passing control row.
- Command: `python -B case/grade.py --responses audit/repro/F5_parse_recursion.jsonl; echo "exit=$?"` prints a
  traceback ending in `RecursionError: maximum recursion depth exceeded during ast construction`, then
  `exit=1`, and no verdict for the control row. `audit/repro/F5_malformed_forge.jsonl` ends in
  `json.decoder.JSONDecodeError` the same way.

### F6. A duplicated row is counted twice (grader and reference)

- Stage: aggregation. `grade.py` lines 122-124 add every passing row to its model's count, so a repeated
  (model, task) row counts twice and a score can exceed 100%.
- Contract broken: C-AGG-1 (a score is the percentage of the 10 tasks passed).
- Shows it: aggregation fixture `agg:duplicate-row`. Share: 0 of 40 (no duplicates stored). Reference: same.
- Counterexample: two identical rows, model `F6-dup`, task t07, a correct `fib`.
- Command: `python -B case/grade.py --responses audit/repro/F6_duplicate_rows.jsonl` prints
  `F6-dup             2     10    20.0` (contract: 10.0).

### G1. The grading platform and the generation models are unpinned

- TASK.md pins "CPython 3.12" without a patch version, OS or hardware, while the 4 s limit is wall time on the
  grading host (`grade.py` line 66); a response near the limit can pass on one host and fail on another. Model
  revisions and chat templates ("each model's own chat template") are not recorded either.
- Share: 0 of 40 measured: the two stored timeouts (c26, exponential recursion for `fib(80)`; c38, a
  non-terminating loop) are far from the limit. Reference: same.
- Would verify it: grading-host fields (CPU, OS, `sys.version`) and model revisions in the run records; no
  such fields exist in `responses.jsonl` or TASK.md (`grep -n "CPython 3.12" case/TASK.md`).

### G2. The hash seed is unpinned

- `grade.py` line 62 passes the parent environment to the child without `PYTHONHASHSEED`, so string hashing,
  and with it the iteration order of a set of strings, is random per child process. A response whose output
  depends on that order gets a random verdict.
- Shows it: hash-seed fixture `test_seed_independence_t06_*`. Share: 0 of 40 (the grader's stored verdicts are
  byte-identical under `PYTHONHASHSEED` 0, 1, 2 and 3). Reference: same. The replacement pins the seed to 0.
- Counterexample, exact input:
  `{"task_id": "t06", "response": "```python\ndef run_length(s):\n    return \"\".join(c + str(s.count(c)) for c in set(s))\n```"}`
- Command: `PYTHONHASHSEED=0 python -B case/grade.py --responses audit/repro/G2_hash_seed.jsonl` prints
  `G2-set-order       0     10     0.0`; with `PYTHONHASHSEED=1` it prints `G2-set-order       1     10    10.0`.

### Observation O1 (no verdict effect)

`from .math import floor` passes the grader's and the reference's import check, because both read
`node.module` and ignore `node.level`; the load then fails with `ImportError`, so the verdict (fail) is right.
Fixture `imp:dd1c0b3525405f0f`.

## Decision entries (for the evaluation's maintainers)

Counted apart from the findings. Each has a switch in the replacement grader.

| Entry | Reading A | Reading B | Example | Proposed | Grader | Reference | Stored verdicts that change |
|---|---|---|---|---|---|---|---|
| D-palindrome-normalization | The docstring literally: `s == s[::-1]`. The stored test `"Was it a car or a cat I saw"` -> True then contradicts it; its expected value would be False | Ignore case and non-alphanumerics, as the stored test assumes | c06 `return s == s[::-1]`: A pass, B fail. c05 (normalizes): A fail, B pass | A for the current text, and fix the task: state the normalization in the docstring (then B) or change the test. Switch `--palindrome literal/normalized` | B | B | 4: c05, c07 lose a pass; c06, c08 gain one |
| D-crlf | `\r\n` ends a line, so "```python\r" is a fence line | Only `\n` ends a line | fixture `ext:c4cb379f434757b0` (the correct `fib` with CRLF line ends): A pass, B fail | A. Switch `--crlf yes/no` | B | B | 0 (no stored `\r`) |
| D-dynamic-import | README: only `import` statements are checked, so `__import__("os")` passes the check | Prompt ("You may import only these modules"): any import mechanism fails | fixture `imp:d3ce90ae7d4f2be1` | A for the check; report the exposure (dynamic imports reach `os` and `subprocess`). Switch `--dynamic-import statement/any` (best effort) | A | A | 0 |
| D-eq-object | Literal `==`, using the returned object's own `__eq__` | The return value must be plain data equal to the expected value | fixture `tst:b53a5153368b7a06` (an object whose `__eq__` always answers True): A pass, B fail | B for user-defined classes. Switch `--eq builtin/literal` | B (as a side effect of F2's JSON round trip) | A | 0 |
| D-main-guard | The code is loaded like a module; an `if __name__ == "__main__":` block does not run | The code runs as a script; the block runs | fixture `exe:b7d68ca2c9ddb4be` (block raises `SystemExit(1)`): A pass, B fail | A (README: "loading the code", then "calls the function"). Switch `--main-guard skip/run` | A | A | 0 |
| D-time-origin | The 4 s start at process start (interpreter start-up counts, about 0.05 s here) | The 4 s start when loading the code begins | only a response within about 0.05 s of the limit | A, as both graders do. Switch `--time-origin process/load` | A | A | 0 |

D-crlf, D-main-guard and D-time-origin come from the README's own wording; D-palindrome-normalization is a
conflict between a stored test and the docstring the model sees. D-main-guard and D-time-origin were added after
the contract hash, with their reasons, in `audit/ISSUE.md` section 2b.

## Stress tests (step 4)

Metamorphic suite (`audit/tests/metamorphic.py`): 19 edits that the contract ignores and 14 that it forbids
(including the content-free responses), each applied to a passing response of all 10 tasks, 330 cases.

| Edit | Contract | Grader wrong on | Cause |
|---|---|---|---|
| I05-I08: tag `py`, no tag, `python3`, `Python` | pass | 10 of 10 each | F3 |
| I01-I04, I09-I19: trailing newline, blank lines, fence-line blanks, prose around, bare code, comments, top-level and in-function `print`, non-ASCII comment, a second block, typing import, typographic quotes in a docstring, numbered and marked-up prose before the block | pass | 0 | |
| X05: a `bash` block before the code | fail | 10 of 10 | F3 |
| X03 rename, X04 raise first, X10 empty block, X11 empty response | fail | 8 of 10 each (tasks without a `raises` test) | F1 |
| X07: list results returned as tuples | fail on t04, t08, t09 | 3 of 3 | F2 |
| X08: result wrapped in an object with a `repr` | fail | 1 (t06) | F2 |
| X01, X02, X06, X09, X12-X14: disallowed imports, unclosed fence, `SystemExit` in the call, restated signature, restated prompt, repeated words | fail | 0 | |

The grader is wrong on 86 of 330 cases; the reference and the replacement on none. Content-free responses: the
empty response and the empty block pass 8 of 10 tasks under the grader; the restated signature, the restated
prompt and repeated words fail everywhere. Fuzzing counts are under F5.

## Panel detail (step 5)

`python -B audit/scripts/panel.py` writes every verdict file and `audit/panel/summary.json`. Scored coverage is
40/40 for every grader and switch. Passes per task (of 4), grader vs replacement with the stored t02 test: t01
3 vs 2 (c02), t04 4 vs 3 (c16), t06 3 vs 2 (c22), t08 3 vs 2 (c31), t10 3 vs 2 (c40); the other five tasks agree.
Only the D-palindrome-normalization switch changes a stored verdict. Grading the 40 responses took about 11 s per
grader here (8 s of it the two timeouts, c26 and c38), against TASK.md's "about 15 seconds". This benchmark is
graded as an evaluation, not as an RL reward; if it were used as one, 5 of the grader's 26 stored passes (19%)
would be false rewards, and F1 lets a policy earn the full reward by raising `ValueError`.

## Blinded review (step 6)

- Gate (recorded before the draw): the recommendation moves to "admit the grader" only if the grader's error
  rate is not higher than the replacement's, and to "replace the benchmark" if the consensus contradicts the
  replacement on more than 2 cases with definite, agreeing verdicts.
- Sample: seed 20261111, strata by grader-vs-replacement disagreement, 9 of 9 disagreements and 31 of 31
  agreements (census). Case list `audit/frozen/cases.jsonl`, sha256
  `503809f1192493a9a78c4c2341a514ae6200ed1de5734c203e6ba679f73d4a74`. Batches A and B (different orders), the
  reviewer prompts filled from `skill/references/reviewer-prompt.md`, the response files and the
  `show_case.py` helper are in `audit/frozen/`; keys (source model, verdicts) are in `keys.jsonl`, never shown to
  reviewers.
- Each case shows the README grading rule and the task's stored tests as the requirement, because the grader's
  verdict is defined by those tests; the reviewer decides whether the response passes them under the rule, and
  may mark a test that the docstring does not support as ambiguous.
- Not run: no reviews, consensus, error-rate intervals, paired difference or kappa. A census of 31 agreements
  with no error found would give each grader a zero-error upper-bound term of
  (31/40) x (1 - 0.025^(1/31)) = 8.7 points, so this population cannot by itself show an error rate below 2%.

## Recommendation: fix the grader

1. F1: count a call that raises on an `expected` test as a failure, and a missing or non-callable function as a
   failed task (the reference does both).
2. F2: compare the return value with `==` against the expected value as loaded from JSON, without serializing it
   (the reference compares in the child; the replacement sends typed values and compares in the parent).
3. F3: extract with the README's tag rule (the reference's regex, or the replacement's line scanner).
4. F4: keep the expected values and the verdict out of the candidate's process, and read results from a channel
   other than the candidate's stdout. The reference has the same defect, so switching to the reference is not
   enough.
5. F5: catch every exception per response (including `RecursionError` and `MemoryError` from `ast.parse` and any
   error while parsing the child's output) and record it as that response's failure.
6. F6: reject or deduplicate repeated (model, task) rows.
7. G1, G2: record the grading host (CPU, OS, `sys.version`) and model revisions with each run, and set
   `PYTHONHASHSEED` for the child.
8. Ask the maintainers to settle the six decision entries; D-palindrome-normalization needs a change to t02's
   docstring or test either way.

`audit/replacement/grade_contract.py` implements 1 to 7 with one switch per decision; it passes all 65
fixtures and 330 metamorphic cases and matches the reference on all 40 stored verdicts under the stored tests.
Run the step-6 review on `audit/frozen/` before adopting it.

## Reproduce

| What | Command | Prints |
|---|---|---|
| All fixture and metamorphic tests | `python -B -m unittest discover -s audit/tests -p "test_*.py"` | `Ran 1192 tests`, `OK (expected failures=121)` |
| Panel | `python -B audit/scripts/panel.py` | the summary JSON; verdicts in `audit/panel/` |
| Fuzz | `python -B audit/scripts/fuzz.py 400 20261111` | exception counts per grader |
| Metamorphic misses | `python -B audit/scripts/run_metamorphic.py` | the grader's wrong verdicts per edit |
| Counterexample files | `python -B audit/scripts/make_repro.py` | `wrote 11 files` |
| Frozen sample | `python -B audit/scripts/draw_sample.py 20261111` | strata sizes; regenerates `audit/frozen/` |

Expected failures in the test run: 23 grader fixtures and 8 reference fixtures (finding or decision), 2
aggregation (F6, both), 2 hash-seed (G2, both), and 86 metamorphic grader cases.
