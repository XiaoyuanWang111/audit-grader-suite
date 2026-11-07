# Audit of the ToyCode 1.0 grader (`case/grade.py`, `case/runner.py`)

Audit of 2026-11-06, following `skill/SKILL.md` offline. The record of every step, with hashes and times, is
`audit/ISSUE.md`; the contract is `audit/CONTRACT.md` (version 2, sha256 `b78f6a96…`; version 1, `9a9237de…`, was
hashed before any grader code was read). Commands below run from the audit run directory
(`<run directory>`) with CPython 3.12.10 on Windows 11.

## Error rate and effect on scores

On the 40 stored responses, `grade.py` contradicts the contract on 5 verdicts (12.5%), taking the grader's own
reading of every decision entry. All 5 are passes that the contract fails: 3 from F1 (an exception in a test is
ignored) and 2 from F2 (tuples compare equal to lists). The reference harness and the replacement grader in
fixes-only mode give the same verdict on all 40 responses. Under the proposed readings, 4 more verdicts differ, all
on t02 (D-palindrome-normalization), for 9 of 40.

| Score, percent of 10 tasks | kite-7b | lark-13b | wren-34b | finch-8b |
|---|---|---|---|---|
| `grade.py` | 90 | 40 | 100 | 30 |
| Contract, fixes only (equal to the reference) | 90 | 20 | 90 | 10 |
| `grade.py` minus fixes only | 0 | +20 | +10 | +20 |
| Contract, proposed reading of every decision entry | 80 | 30 | 80 | 20 |

- A second run of `grade.py` wrote a byte-identical verdict file, so its rerun difference is 0 points and every
  score change above is larger. A generation rerun was not possible, because the exercise has no compute.
- This error rate comes from comparing with the replacement, not from a reviewer consensus. The blinded review of
  step 6 was not run; its sample (all 40 verdicts: 9 where `grade.py` and the proposed readings disagree, 31 where
  they agree) is drawn and frozen, so there is no reviewer-based rate or interval yet.
- Beyond the stored responses, F1 passes responses that contain no working function: an empty response passes 8 of
  the 10 tasks, and a model that answers every task with a function that only raises `ValueError` scores 100.
- D-palindrome-normalization is the one decision entry that changes stored verdicts. Under its proposed literal
  reading, kite-7b and wren-34b lose t02 and lark-13b and finch-8b gain it, 10 points each (last row of the table).

## Recommendation: fix the grader

Fixing is enough. The benchmark itself holds up: 44 of the 45 stored tests follow from their docstrings, and the
reference harness already grades the stored panel as the contract does. Admitting the grader is ruled out, because
F1 and F2 add 20 points to two of the four models on the stored run. The fixes, in order of effect:

1. F1: fail a test whose call raises an unexpected exception, and fail every test when the function is missing, as
   `harness_ref.py` does.
2. F2: compare the returned object with `==` in the child, as `harness_ref.py` does, instead of its JSON form.
3. F5: catch every exception from `ast.parse` and from reading the result line, and fail only that response.
4. F3: open a block on any fence that rule 1 allows, and grade the first block (`harness_ref.py`'s pattern).
5. F6 and G2: send the job on stdin, so that the code sees an empty stdin and an empty working directory; pin
   `PYTHONHASHSEED`; start the child with a clean environment; bind the builtins the runner needs before the code
   runs; and accept only a result line tagged with a per-run nonce that has a result for every test
   (`audit/scripts/contract_grader.py` does all of this). Before the
   grader serves as an RL reward, add process isolation at the OS level; checks inside the process cannot stop code
   that inspects the runner's frames.
6. F4: fail an `ImportFrom` with `level > 0`. F7: count each (model, task) once.
7. G1: record each model's revision, chat template and serving stack in the run records.

The decision entries go to the maintainers; only D-palindrome-normalization changes a stored verdict.

## Findings

| Id | Stage, contract clause | Shown by | Verdicts affected | Reference (`harness_ref.py`) |
|---|---|---|---|---|
| F1 | Tests, C-test 4 and 5 | fixtures `C-test:4cb998c9812e034e`, `C-test:fbcbe6157e477fd9`, `C-test:5764bca8c04003dd`, `C-test:ccf746bd1d3a219d`, `C-test:fc26cd60aa8b6618`; cases c02, c22, c40 | 3 of 40 stored (7.5%); of the 21 stored responses the contract passes, 16 still pass in the grader with the function renamed, and 16 with a `raise` as its first statement | correct |
| F2 | Tests, C-test 2 | fixtures `C-test:2dc112e1a57e5fc8`, `C-test:4075cd8650a9d792`, `C-test:b4000ec4c5962862`; cases c16, c31 | 2 of 40 stored (5%); all 8 stored t04, t08 and t09 responses that the contract passes still pass in the grader with tuple results | correct |
| F3 | Extraction, C-extract 1 and 3 | fixtures `C-extract:b479df0942e821a7`, `C-extract:6dfb9851e03d6638`, `C-extract:19c959cc6b154279`, `C-extract:bafd40d039fe4f33`, `C-extract:74d5208dcbf9d180` | 0 of 40 stored (every stored fence is `` ```python ``); with the tag changed to `py` or removed, all 25 grader passes among the 37 fenced stored responses that finish become fails; 20 of 300 fuzz cases | correct |
| F4 | Import check, C-import 4 | fixture `C-import:0fdf65cb005a5050` | 0 of 40 | same defect |
| F5 | Run, C-task 3 | fixtures `C-import:4d7df43525d14297`, `C-import:dbb01f88cb6029e6`, `C-exec:e82679f75f58a80c`; test `RunLevel.test_run_survives_unparsable_response_grader` | 0 of 40 stored; when triggered, every verdict of the run is lost; 1 of 300 fuzz cases | same defect |
| F6 | Execution, C-exec 5 and 7, C-test 3 | fixtures `C-exec:271f8967eb4adb41`, `C-exec:87f6b6fe5758ca95`, `C-exec:231fdf2ab79ec217` | 0 of 40 (needs code written to exploit the grader) | same defect |
| F7 | Score, C-task 2 | test `RunLevel.test_duplicate_rows_count_once_grader` | 0 of 40 (the stored file has one row per model and task) | same defect |
| G1 | Inputs, step 1 | the record fields of `case/responses.jsonl` | all 40 rows (the generation cannot be reproduced from the records) | not applicable |
| G2 | Inputs, step 1 | test `Reproducibility.test_hash_seed_grader` | 0 of 40 stored (no stored response depends on hash order) | same defect |

Each counterexample below is a response file in the grader's own input format under
`audit/tests/counterexamples/`; the command reproduces the grader's verdict and prints its score table.

### F1: an exception in a test, or a missing function, is ignored

`runner.py` puts a call that raises on an `expected` test into `errors`, and `judge()` in `grade.py` reads only
`results`. A missing function raises `TypeError` on every call and lands in the same list. A task without `raises`
tests (8 of the 10) therefore passes whenever every call raises; t03 and t04 also pass when the function raises
`ValueError`. Contract C-test 4: "Any other exception raised by the call fails the test"; C-test 5: a missing
function fails every test.

- Exact input (`F1.jsonl`, first row): `{"id": "F1-empty", "model": "probe", "task_id": "t10", "response": ""}`.
  Verdict: `pass`, detail `all tests passed`. The contract and the reference fail it.
- Stored case c02 (`lark-13b`, t01): `return sorted(set(nums))[-2]` raises `IndexError` on `[7]` and `[]`; the
  grader passes it.
- Command: `python case/grade.py --responses audit/tests/counterexamples/F1.jsonl --out audit/work/ce_F1.jsonl`
  (all 6 rows pass: the empty response, a `NotImplementedError` stub, a correct `fib` named `fibonacci`, and the
  stored c02, c22, c40).
- Command: `python case/grade.py --responses audit/tests/counterexamples/F1-raise-all.jsonl` prints
  `raiser 10 10 100.0`; each row is `def <entry point>(*args): raise ValueError` in a python block.

### F2: return values are compared after a JSON round trip

`runner.py` sends `json.dumps(value, default=repr)` and `grade.py` compares `json.loads(...) != expected`, so a
tuple becomes a list, and a value that JSON cannot encode is compared as its `repr` string. Contract C-test 2: the
returned object is compared with `==` to the expected value, and JSON arrays load as lists, so `(1, 6) != [1, 6]`.

- Exact input (`F2.jsonl`, first row): task t08, response
  `` "```python\ndef merge_intervals(intervals):\n    out = []\n    for start, end in sorted(intervals):\n        if out and start <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], end)\n        else:\n            out.append([start, end])\n    return [tuple(iv) for iv in out]\n```\n" ``.
  Verdict: `pass`. The contract and the reference fail it.
- Stored cases: c31 (`wren-34b`, t08, appends `(start, end)` tuples) and c16 (`finch-8b`, t04, returns
  `tuple(items[i:i + size])` chunks).
- Command: `python case/grade.py --responses audit/tests/counterexamples/F2.jsonl --out audit/work/ce_F2.jsonl`
  (all 3 rows pass).

### F3: a block opens only on a fence tagged exactly `python`

`FENCE` in `grade.py` is ``^```python[ \t]*\n(.*?)^```[ \t]*$``. A fence tagged `py`, `python3` or `Python`, or not
tagged, is not found, so the whole response, backticks included, is parsed and fails. A response whose first block
has another tag is graded on its first `python` block instead. Contract C-extract 1 and 3: any tag of ASCII letters,
digits, `_`, `+` or `-` opens a block, and only the first block counts.

- Exact input (`F3.jsonl`, first row): task t07, response
  `` "```py\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```\n" ``.
  Verdict: `fail`, detail `does not parse: SyntaxError`. The contract and the reference pass it.
- Exact input (`F3.jsonl`, third row): task t07, response
  `` "Usage:\n\n```\n>>> fib(10)\n55\n```\n\nCode:\n\n```python\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```\n" ``.
  Verdict: `pass`; the contract and the reference grade the first block, which does not parse, and fail it.
- Command: `python case/grade.py --responses audit/tests/counterexamples/F3.jsonl --out audit/work/ce_F3.jsonl`
  (fail, fail, pass).

### F4: a relative import that names an allowed module passes the import check

`check_imports` takes `node.module` and ignores `node.level`, so `from .math import sqrt` reads as `math`. When the
statement sits in a branch that the tests never run, the task passes. Contract C-import 4: a relative import is not
on the list and fails the task.

- Exact input (`F4.jsonl`): task t07, response
  `` "```python\ndef fib(n):\n    if n < 0:\n        from .math import sqrt\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```\n" ``.
  Verdict: `pass`; the reference also passes it, and the contract fails it.
- Command: `python case/grade.py --responses audit/tests/counterexamples/F4.jsonl --out audit/work/ce_F4.jsonl`.

### F5: one response ends the whole run

`check_imports` catches only `SyntaxError` and `ValueError`, but `ast.parse` raises `MemoryError` ("Parser stack
overflowed") on 5,965 or more repeated `-`, `+` or `~` characters, and `RecursionError` on a sum of 2,997 or more
terms. `run_candidate` also calls `json.loads` on the last result line without a guard. Any of these escapes
`main()`: the run exits with code 1 before the verdict file is written, so no response gets a verdict and no score is
printed. Contract C-task 3: an error while grading one response fails that response only. Whether a model with a
1,024-token budget can emit 5,965 dashes depends on its tokenizer, which the records do not pin (unverified).

- Exact input (`F5-parse.jsonl`, second row): task t07, a response of exactly 5,965 `-` characters, between two
  correct rows. Command: `python case/grade.py --responses audit/tests/counterexamples/F5-parse.jsonl --out audit/work/ce_F5-parse.jsonl`
  ends with `MemoryError: Parser stack overflowed - Python source too complex to parse`, exit code 1, no verdict
  file.
- `F5-sum.jsonl`: a correct `fib` followed by `x = 1+1+…+1` with 2,997 terms; `RecursionError: maximum recursion
  depth exceeded during ast construction`.
- `F5-result.jsonl`: task t03, response
  `` "```python\n_fd1 = open(1, \"w\", closefd=False)\n_fd1.write('@@RESULT@@ {\\n<<toycode-result>>{\\n')\n_fd1.flush()\n\ndef parse_duration(text):\n    raise SystemExit(0)\n```\n" ``;
  `json.decoder.JSONDecodeError`.
- The reference stops on all three inputs the same way.

### F6: the response's code can write the verdict or read the tests

The code runs in the runner's own process and working directory. It can write a result line to file descriptor 1
and end the process before the runner prints the real one (the grader reads the last `@@RESULT@@` line); it can read
`job.json`, which holds every expected value, from its working directory; and it can replace
`builtins.isinstance`, which the runner uses to judge `raises` tests. None of the three exploits needs an import
statement. They break contract C-exec 5 (a test that did not run did not pass), C-exec 7 (version 2: the code cannot
read the hidden tests) and C-test 3 (the built-in exception class decides a `raises` test).

- Exact input (`F6.jsonl`, first row): task t03, response
  `` "```python\n_fd1 = open(1, \"w\", closefd=False)\n_fd1.write('@@RESULT@@ {\"loaded\": true, \"results\": [], \"errors\": []}\\n<<toycode-result>>{\"ok\": true}\\n')\n_fd1.flush()\n\ndef parse_duration(text):\n    raise SystemExit(0)\n```\n" ``.
  Verdict: `pass` (the line also carries the reference's marker, and the reference passes it too).
- The second row reads the tests with `eval(open("job.json").read(), …)` and returns the stored answers; the third
  replaces `isinstance` so that `RuntimeError` counts as `ValueError`. Both pass in the grader and the reference.
- Command: `python case/grade.py --responses audit/tests/counterexamples/F6.jsonl --out audit/work/ce_F6.jsonl`
  (all 3 rows pass, on t03, which has two `raises` tests). The replacement fails all three.

### F7: a duplicated row counts twice in the score

`main()` adds one pass per row, so two passing rows for one (model, task) count as two tasks. Contract C-task 2
(version 2): a task counts once, and a score cannot exceed 100.

- Exact input (`F7.jsonl`): two identical rows for model `probe`, task t07, each a correct `fib` in a python block.
- Command: `python case/grade.py --responses audit/tests/counterexamples/F7.jsonl` prints `probe 2 10 20.0`;
  the contract gives 10.0. The reference prints 20.0 too.

### G1: the generation inputs are not recorded

`case/responses.jsonl` records `temperature`, `max_tokens` and `finish_reason`, but not each model's revision, its
chat template or the serving stack, and TASK.md names none of them. The stored responses cannot be regenerated to
check them. Fields that would pin them: `model_revision`, `chat_template_sha256` and `server_version` in each row,
or the run configuration. The wall-time limit also ties verdicts to the evaluation host, which TASK.md does not
name. No stored verdict is near that edge: the slowest stored response that finishes used 0.6 s of the 4 s budget on
the audit machine, and the two that reach the limit are a naive `fib(80)` and an endless loop.

### G2: the child's hash seed, stdin and environment come from the caller

`run_candidate` starts the child with the caller's whole environment (plus two variables) and the caller's stdin, so
`PYTHONHASHSEED`, `PYTHONPATH` and any other `PYTHON*` variable reach it, and the OS and interpreter patch version are
not stated. Iteration order over a set of strings then changes between runs.

- Exact input (`G2.jsonl`): task t06, response
  `` "```python\ndef run_length(s):\n    return \"\".join(f\"{c}{s.count(c)}\" for c in set(s))\n```\n" ``.
- Commands: `PYTHONHASHSEED=0 python case/grade.py --responses audit/tests/counterexamples/G2.jsonl` prints
  `probe 0 10 0.0` (fail, `test 2 failed`); with `PYTHONHASHSEED=1` it prints `probe 1 10 10.0` (pass). With the
  variable unset, each run draws a seed: seeds 1 and 12 of 0 to 15 pass. The reference behaves the same; the
  replacement pins seed 0.

## Decision entries for the maintainers

Each entry is a place where the task text allows two verdicts (`audit/CONTRACT.md`, "Decision entries"). Panel
effect: stored verdicts that change when the replacement switches that entry from the proposed reading.

| Entry | Reading A | Reading B | Proposed | `grade.py` | Reference | Fixture | Panel effect |
|---|---|---|---|---|---|---|---|
| D-palindrome-normalization (t02, test 4) | "reads the same forwards and backwards" is `s == s[::-1]`, so the stored test, which expects `True` for "Was it a car or a cat I saw", is wrong | phrase sense, ignoring case and spaces; the stored test is right | A | B | B | `C-data:3be875c9f4775013`, `C-data:0c8c06024c479ab1` | 4 verdicts (c05, c06, c07, c08); each model moves 10 points |
| D-line-terminator | `\r\n` ends a line, so a CRLF fence opens a block | only `\n` ends a line; a CRLF response has no fence and fails to parse | A | B | B | `C-extract:723aca95a5e46875` | 0 (no stored `\r`) |
| D-load-error | an exception while loading the code fails the task | the tests run on whatever was defined | A | A | A | `C-exec:14a0daf1c993a9c1` | 0 |
| D-main-guard | code under `if __name__ == "__main__":` does not run | it runs | A | A | A | `C-exec:130ef5b1ad4c76ea` | 0 |
| D-dynamic-import | only `import` statements are checked | `__import__` of a module off the list fails | A | A | A | `C-import:e7e01be17b2d6855` | 0 |
| D-numeric-type | Python `==` decides (`90.0` passes for `90`) | the value must have the type the docstring names | A | A | A | `C-test:f2a11b6b4efd9c1d` | 0 under reading B as written; the replacement's switch, which compares with the stored value's type, changes c19 (2.0 for 2) |
| D-eq-object | Python `==` on any returned object | the value must be built from built-in types | B | B (by its JSON round trip) | A | `C-test:c86c0648f5b80e48` | 0 |
| D-time-start | the 4 s budget starts at process start | it covers loading and tests only | A | A | A | none (needs a controlled clock) | 0 |

Under reading A, an object whose `__eq__` always returns `True` passes every task that has no `raises` test, which
is why D-eq-object proposes B.

## Steps

1. Pin the inputs: run. Every file is pinned by sha256 against `case/MANIFEST.sha256`, with one hash per task, test
   list and response row; the manifest matched before and after every grading run. Unpinned inputs are G1 and G2.
2. Contracts: run. Version 1 was hashed at 2026-11-06T23:10:44Z, before any grader code was read; version 2 adds
   C-exec 7 and changes C-task 2, each marked with its reason.
3. Fixtures: run. 55 fixtures in `audit/tests/fixtures.py` (27 controls, 20 for findings, 8 for decisions), plus
   run-level and reproducibility tests; `python -m unittest discover -s audit/tests` runs 301 tests, OK, with 40
   expected failures marked `unittest.expectedFailure` (strict, the substitute for `pytest.mark.xfail(strict=True)`,
   since pytest is not installed).
4. Reference comparison and stress tests: run (`audit/scripts/stress.py`, `audit/scripts/fuzz_attribution.py`).
   The reference ships no unit tests and the grader has none, so none could be run against the replacement. Fuzz
   counts (300 cases, seed 20261106): an exception escaped the grader on 1 and the reference on 4, and all 23
   disagreements between the grader and fixes only are F1, F3 or F5.
5. Panel: run on the 40 stored responses only (`audit/scripts/panel.py`); no response was generated, and no
   generation rerun was possible. Scored coverage was 40 of 40 for every grader.
6. Blinded review: not run, because subagents cannot be started in this exercise. Steps 6.1 to 6.3 were done: the
   decision gate was recorded first, then the sample was drawn with seed 20261106 as a census of both strata, frozen
   (case list sha256 `42f1b459405f9768…`, keys `aa9fa230f107236644…`) and rendered into two blinded batch files.
7. Report: this file.

Skipped, because the exercise has no issue tracker, repository, research branch, Hugging Face dataset or job
launcher: `file-issue` (the record is `audit/ISSUE.md`), the repository's grader test directory and `manage-pr` (the
tests are under `audit/tests/`), the pinned dataset revision (frozen files under `audit/frozen/`, hashed in
`audit/ISSUE.md`), `research-engineering` (scripts under `audit/scripts/`), `use-iris` (no compute), and
`docs/dev-guide/writing-style/issues.md` (not available offline).

## Files

- `audit/ISSUE.md`: record of every step, with times and hashes.
- `audit/CONTRACT.md`, `audit/frozen/contract_v1.md`: the contract, versions 2 and 1.
- `audit/tests/fixtures.py`, `audit/tests/test_fixtures.py`: fixtures and regression tests;
  `audit/tests/counterexamples/*.jsonl`: one response file per finding.
- `audit/scripts/contract_grader.py`, `audit/scripts/contract_runner.py`: the replacement grader, one switch per
  decision entry (`--mode proposed|fixes-only`, `--set ENTRY=A|B`).
- `audit/scripts/pin_inputs.py`, `panel.py`, `stress.py`, `fuzz_attribution.py`, `draw_sample.py`,
  `make_counterexamples.py`, `fixture_table.py`: the audit's scripts.
- `audit/frozen/review_r1_*`, `audit/frozen/print_case.py`: the frozen review sample, keys, batches, reviewer prompt
  and helper.
- `audit/work/`: raw outputs (panel verdicts, stress and fuzz results, test logs).
