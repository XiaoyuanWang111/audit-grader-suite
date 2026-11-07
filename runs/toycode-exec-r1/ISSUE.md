# Audit: ToyCode 1.0 execution grader (`case/grade.py`, `case/runner.py`)

Offline stand-in for the task's issue. Entries are appended in time order; times are UTC, read from the clock
(`date -u`) when each entry was written.

## 2026-11-06T23:08Z: step 1, pinned inputs (from the files, run records and TASK.md only)

No repository, so every input is pinned by sha256. `case/MANIFEST.sha256` (sha256 `1a8b608ad963…`) matches every file
it lists (`python -I audit/scripts/pin_inputs.py`, output in `audit/work/pin_inputs.out`).

| Input | Pin |
|---|---|
| Grader | `case/grade.py` `ea020bdda3314c85bb2c185697bfa640b5939251dce97fdde1a60aeb8ecd9153`, `case/runner.py` `36953b5beac29ef3e2162551d0e9249226e1ff679b11ae101e847365dd1ecc28` |
| Reference implementation | `case/reference/harness_ref.py` `4b502d23f2dad7aa26ba5dd2c7a5f54072265f5908412675de39918075c6e0ec` (released with ToyCode 1.0; no commit id) |
| Tasks | `case/tasks.jsonl` `6d7374ece0f947ad2a74ee2358225d399871c38c0fc2822e6858b1e1193e0027`, 10 rows; per-row sha256 of the raw line in `pin_inputs.out` (t01 `797d5de3a67d993f` … t10 `86cd90dc7a8206f3`) |
| Tests | `case/tests.json` `b68f1b8f193a8a7286da463ba2191d74bda28d7724223dd4b6ce5cd40820218e`, 45 tests; per-task sha256 of canonical JSON in `pin_inputs.out` |
| Prompt rendering | `case/prompt_template.txt` `e625324a385702293fedc322a5a9d65cbf0e0d8313d912119425b0f53db0a87a`, one `{prompt}` placeholder; the only user message, no system prompt, each model's own chat template (TASK.md) |
| Run records | `case/responses.jsonl` `dc00ec20a4e86e9743a7d82b271b555a639cd582bb11f0fcc174513689d95535`, 40 rows (4 models x 10 tasks), per-row sha256 in `pin_inputs.out` |
| Generation settings | from the records: temperature 0.0 and `max_tokens` 1024 on all 40 rows; `finish_reason` `stop` on all 40 (no truncated response); stop sequences: none (TASK.md, not a record field) |
| Graded text | the whole response: TASK.md says none of the models emits a reasoning block; no response has a `\r` or a non-ASCII character |
| Interpreter | TASK.md: CPython 3.12. Audit machine: CPython 3.12.10 (64-bit, Windows 11) |

Unverified or unpinned (each one is listed again as a finding if the benchmark leaves it unpinned):

- Model revisions, chat templates and the serving stack: no record field holds them (`responses.jsonl` has only
  `id, model, task_id, response, finish_reason, max_tokens, temperature`). Would be verified by a record field such
  as `model_revision` or the run configuration, which this exercise does not include.
- The interpreter patch version and the operating system of the evaluation: TASK.md says only "CPython 3.12".
  Verify with `python -c "import sys, platform; print(sys.version, platform.platform())"` on the evaluation host.
- Grader dependencies that only the code shows are recorded after the contract hash (step 2).

## 2026-11-06T23:10Z: step 2, contract recorded before reading any grader code

- Contract file `audit/CONTRACT.md`, version 1, sha256
  `9a9237dedd35271dcafdee5bac678658bd5c6a3486a26870856eae7826826b56`, hashed at 2026-11-06T23:10:44Z (clock read
  with `date -u`), before any line of `case/grade.py`, `case/runner.py` or `case/reference/harness_ref.py` was opened.
  A copy is frozen as `audit/frozen/contract_v1.md` (same hash).
- Written from `case/TASK.md`, `case/prompt_template.txt`, `case/tasks.jsonl` and `case/tests.json`.
- Decision entries at version 1 (text allows two verdicts; proposals in the contract): D-palindrome-normalization,
  D-line-terminator, D-load-error, D-main-guard, D-dynamic-import, D-numeric-type, D-eq-object, D-time-start.

## 2026-11-06T23:31Z: step 1 (continued), inputs that only the code shows

Recorded after the contract hash, as step 1 requires.

- Grader extraction rule (`grade.py` line 25): the first match of ``^```python[ \t]*\n(.*?)^```[ \t]*$`` (MULTILINE,
  DOTALL), else the whole response. Reference (`harness_ref.py` line 23): the same pattern with the tag
  `[A-Za-z0-9_+-]*`.
- Import check: `ast.walk` over the parsed code; allowed set equal to the prompt's list in both; `ImportFrom.level`
  ignored in both; only `SyntaxError` and `ValueError` from `ast.parse` are caught in both.
- Execution: `[sys.executable, runner.py, job.json]` with `cwd` = a temporary directory that holds `job.json` (code,
  entry point and every test with its expected value); environment = the caller's `os.environ` plus
  `PYTHONIOENCODING=utf-8` and `PYTHONDONTWRITEBYTECODE=1`; stdin inherited from the caller; `timeout=4.0` on the
  whole child process (so interpreter start-up counts). The reference does the same with `harness_ref.py --child`.
- Comparison: the grader's child serializes each return value with `json.dumps(value, default=repr)` and the parent
  compares `json.loads(value) != expected`; `raises` tests are judged in the child with
  `isinstance(exc, getattr(builtins, name))`; an exception on an `expected` test is stored in `errors`, which
  `judge()` never reads. The reference compares `out == test["expected"]` in the child and stops at the first failure.
- Result channel: the last stdout line that starts with `@@RESULT@@ ` (reference: `<<toycode-result>>`).
- Dependencies: standard library only (`argparse, ast, json, os, re, subprocess, sys, tempfile, collections`;
  runner `builtins, copy, io, json, sys`). No lockfile is needed.
- Unpinned by the code: `PYTHONHASHSEED` (inherited; random per child when unset), stdin, the rest of the caller's
  environment (`PYTHONPATH` and other `PYTHON*` variables reach the child), the interpreter patch version and the OS.

## 2026-11-06T23:31Z: step 2 (continued), contract version 2

- `audit/CONTRACT.md` version 2, sha256 `b78f6a96204d7ef41435592a50c8bb10359e38890a3ab08f34db13e855562dfb`.
  Version 1 stays frozen as `audit/frozen/contract_v1.md` (`9a9237dedd35…`).
- Added C-exec 7 (the code cannot read the hidden tests while it runs). Reason: version 1 left out TASK.md's
  sentence "The tests are hidden from the model"; noticed while reading `grade.py`, which writes the tests into the
  child's working directory.
- Changed C-task 2 (a task counts once per model). Reason: version 1 put all duplicate rows outside the text, but rule
  5 counts tasks, which decides the case where the duplicate rows agree.
- No decision entry was added or changed.

## 2026-11-06T23:31Z: step 3, fixtures

- `audit/tests/fixtures.py` (sha256 `9108d9c014a790db…`): 54 fixtures labeled from the contract alone (proposed
  readings): 27 controls, 19 that reproduce a finding and 8 that show a decision entry. Id = check + first 16 hex digits of
  sha256(task_id + "\n" + response).
- `audit/tests/test_fixtures.py` (sha256 `0aa3077f42378da6…`): every fixture against the grader, the reference and the
  replacement; each decision fixture under both readings; a snapshot of today's verdicts; 4 run-level tests through
  each command line; 1 reproducibility test per grader. Fixtures the current code gets wrong carry
  `unittest.expectedFailure` (strict: an unexpected success fails the run).
- Run: `python -m unittest discover -s audit/tests` -> 296 tests, OK, 39 expected failures
  (`audit/work/unittest_run2.txt`). Manifest checked before and after: all files match.
- The grader contradicts the label on 22 of 54 fixtures: 19 under every reading (findings F1 to F6), 3 under the
  proposed reading only (D-line-terminator 1, D-palindrome-normalization 2). The reference contradicts it on 11: 7
  findings (F4, F5, F6) and 4 decisions (D-line-terminator, D-eq-object, D-palindrome-normalization 2).
- A replacement bug found by the reproducibility test and fixed before freezing: the child ran with `-I`, which
  implies `-E` and ignored the pinned `PYTHONHASHSEED`; it now runs with `-s -P`.

## 2026-11-06T23:31Z: replacement grader frozen before the panel

- `audit/scripts/contract_grader.py` sha256 `062dfe5765e42327ce60de8b9dbcd72c8ec46f844b239affa0546a6641ab918c`,
  `audit/scripts/contract_runner.py` sha256 `7f601c20047b2768558d85a621c0c54dd752dad66b8b252eedd5a5c408a37320`.
- It was developed against the fixtures only; none of the 40 stored responses has been graded by it yet, so all 40
  are held out. Any later change to these two files will be listed here with its reason.

## 2026-11-06T23:38Z: step 5, model panel (stored responses only)

No compute in this exercise, so no response was generated; the panel is the 40 stored responses (`kite-7b`,
`lark-13b`, `wren-34b`, `finch-8b`, one greedy response per task). `python audit/scripts/panel.py` graded them with
the grader (twice), the reference, the replacement in fixes-only and proposed modes, and the replacement with each
decision entry flipped from its proposed reading (output `audit/work/panel_run.txt`, verdicts
`audit/work/panel_*.jsonl`, summary `audit/work/panel_summary.json`). Manifest matched before and after every run.

- What the stored records already show: 40 of 40 `finish_reason` = `stop` (no truncation), no reasoning block, every
  fence tagged exactly `python` (so F3 changes no stored verdict), 1 response without a fence (c33), 1 with two blocks
  (c23), 2 responses that reach the time limit in every run (c26 naive `fib`, c38 a `binary_search` that loops).
- Scored coverage: 40 of 40 expected (model, task) items get a verdict in every run.
- Grader rerun: byte-identical verdict file (sha256 `41eaff356aa86cd5…` both times), so the rerun difference is 0
  points for every model. A generation rerun was not possible (no compute).

| Score (percent of 10 tasks) | kite-7b | lark-13b | wren-34b | finch-8b |
|---|---|---|---|---|
| Grader (`case/grade.py`) | 90 | 40 | 100 | 30 |
| Reference (`harness_ref.py`) | 90 | 20 | 90 | 10 |
| Replacement, fixes only | 90 | 20 | 90 | 10 |
| Replacement, proposed readings | 80 | 30 | 80 | 20 |
| Grader minus fixes only | 0 | +20 | +10 | +20 |

- Grader vs fixes only: 5 of 40 verdicts differ, all grader passes that the contract fails: c02 (`lark-13b` t01,
  IndexError on 2 tests, F1), c22 (`lark-13b` t06, IndexError on `""`, F1), c40 (`finch-8b` t10, IndexError on `[]`,
  F1), c16 (`finch-8b` t04, list of tuples, F2), c31 (`wren-34b` t08, list of tuples, F2). The reference agrees with
  fixes only on all 40 verdicts.
- 5 of the grader's 26 passes (19%) contradict the contract (fixes only as correct). The grader is not an RL reward,
  so no false-reward count is reported beyond this share.
- Decision effects on the panel (proposed vs one entry flipped): D-palindrome-normalization 4 verdicts (c05, c06,
  c07, c08: every t02 response flips; 10 points for each model); the D-numeric-type switch 1 (c19 returns 2.0 for an
  expected 2; the switch compares with the stored value's type, which is stricter than reading B for t05, whose
  docstring names no type); D-line-terminator, D-load-error, D-main-guard, D-dynamic-import, D-eq-object and
  D-time-start 0.
- Passes per task (grader / fixes only, of 4): t01 3/2, t02 2/2, t03 2/2, t04 4/3, t05 1/1, t06 3/2, t07 2/2, t08 3/2,
  t09 3/3, t10 3/2.
- Held out: the replacement was frozen before this step and not changed after it, so all 40 responses stay held out.

## 2026-11-06T23:40Z: step 6, decision gate recorded before any review

Recommendation from steps 1 to 5: fix the grader. The blinded review would change it as follows; nothing else from
the review changes it.

- Admit the grader instead, only if the review's consensus sides with the grader on at least 3 of the 5 cases where
  it passes and the replacement (fixes only) fails, so that the paired difference in error rate (grader minus
  replacement) has a 95% interval that includes zero or lies below it. That would mean the contract misreads the
  grading rule, and the contract would be rewritten before anything else.
- Replace the benchmark instead, if the reviewers mark the stored tests ambiguous or wrong (verdict `ambiguous`
  with a reason about the tests, high or medium confidence, both reviewers) on cases from 3 or more of the 10 tasks;
  today only t02's test 4 is in question (D-palindrome-normalization). Rewriting the tests of 3 or more tasks makes a
  new benchmark version.
- Keep "fix the grader" otherwise, with the replacement counted as more reliable only if it also passes every
  fixture (done: 54 of 54), its scored coverage is complete (done: 40 of 40), and its consensus error rate is lower
  than the grader's with a paired 95% interval that excludes zero.

## 2026-11-06T23:41Z: step 6.1 and 6.2, review sample drawn and frozen (no review has started)

- Script `audit/scripts/draw_sample.py`, seed 20261106 (opaque ids), reviewer orders seeded 1 (A) and 2 (B).
- Population: the grader's 40 verdicts on the stored responses, all held out (step 5). Strata by whether the grader
  and the replacement (proposed readings) disagree: disagreements 9 (sampled 9), agreements 31 (sampled 31). The
  population is small, so the round is a census of both strata.
- Frozen files, sha256:

| File | sha256 |
|---|---|
| `audit/frozen/review_r1_cases.jsonl` (case list: id, task, requirement, prompt, response) | `42f1b459405f97680e6012de582d5226252416e3c9941481f15cda9f9eb89db5` |
| `audit/frozen/review_r1_keys.jsonl` (source row, model, stratum, every grader's verdict) | `aa9fa230f107236644a44722752ba76f76c30c6b3332e92f9193bbc930ee837c` |
| `audit/frozen/review_r1_batch_A.md` | `b479916804074ad9c084958769132e82f34f23f0cf4eb0fb2981c0501af21c01` |
| `audit/frozen/review_r1_batch_B.md` | `27443c2ebc82aa0e37d6f4ac78a567aff97aa1effa814006223147c1af5702ae` |
| `audit/frozen/review_r1_reviewer_prompt.md` (from `skill/references/reviewer-prompt.md`, reference-answer rule added) | `b9eb2bd7d322fc778eab34e8317013a8f11efaff2094b6d10190f818c8ffe7d7` |
| `audit/frozen/print_case.py` (helper that prints a case's exact response or its extracted code) | `92018aaf8c99a3f96e7a4f57cde7e701634e807617a5b32e11d87d95a800957c` |

- The batch files show no model name, no response id and no verdict (checked with grep). Step 6.4 (two reviewers)
  is not run in this exercise: no subagents may be started.

## 2026-11-06T23:51Z: step 3 (update), one fixture added

- Added an F1 fixture on t03: a function that always raises `ValueError` (the `raises` tests pass, the errors on the
  other tests are ignored). Reason: found during step 4 that this one-line function passes every task, 10 of 10; it
  is the smallest response that reproduces F1 on a task with `raises` tests.
- `audit/tests/fixtures.py` now sha256 `e53b6c795d423e612e44919e8c9b40e734042a0be713df5a4542456f17540f7c`: 55
  fixtures (27 controls, 20 that reproduce a finding, 8 that show a decision). `test_fixtures.py` unchanged
  (`0aa3077f42378da6…`). Run: 301 tests, OK, 40 expected failures (`audit/work/unittest_run3.txt`). The grader
  contradicts the label on 23 fixtures (20 findings, 3 decisions), the reference on 11 (7 findings, 4 decisions), the
  replacement on none. Manifest matched before and after.

## 2026-11-06T23:51Z: step 4, reference comparison and stress tests

- Reference comparison, panel: grader vs reference 5 of 40 disagreements, all grader defects (c02, c22, c40: F1;
  c16, c31: F2). The reference equals the replacement (fixes only) on all 40.
- Reference comparison, fixtures: see step 3; every reference disagreement with a label is F4, F5, F6 or a decision.
- Unit tests: the reference ships none and the grader has none, so no assertion could be run or listed.
- `python audit/scripts/stress.py --fuzz 300 --seed 20261106` (output `audit/work/stress_run.txt`, summary
  `audit/work/stress_summary.json`); counts below are grader / reference / replacement.
- Edits the contract ignores, on the 38 stored responses that do not time out: a print at load 0/0/0, a helper named
  `main` 0/0/0, spaces after the fences 0/0/0 (37 fenced), fence tag `python` -> `py` 25/0/0, tag removed 25/0/0.
  Appending a prose line changed c33 in all three; c33 has no fence, so the prose becomes code and the change is
  correct.
- Edits the contract forbids, on the 21 stored responses the replacement passes (verdicts still pass): entry point
  renamed 16/0/0, `raise RuntimeError` as the first statement 16/0/0, `import os` 0/0/0, list results turned into
  tuples 8 of 8 / 0 / 0, last closing fence dropped 1/1/1 (c23: the edit removed the second block's fence, the first
  block stays closed, so pass is correct).
- Content-free responses, tasks passed of 10: empty 8/0/0, whitespace only 8/0/0, a `pass` block 8/0/0, the
  signature with `raise NotImplementedError` 8/0/0, a function that always raises `ValueError` 10/0/0 (separate
  run: `audit/tests/counterexamples/F1-raise-all.jsonl`), repeated word, refusal, restated prompt and restated
  signature 0/0/0; 6,000 dashes: the grader and the reference raise `MemoryError` on all 10 tasks, the replacement
  fails them.
- Fuzzer, 300 cases: an exception escaped the grader on 1 (MemoryError), the reference on 4 (3 MemoryError, 1
  RecursionError), the replacement on 0. Grader vs fixes only: 23 disagreements, each attributed by
  `audit/scripts/fuzz_attribution.py`: F3 fence tag 12, F3 usage block before the code 8, F1 2, F5 1; none
  unexplained. Reference vs fixes only: 4, all exceptions (F5).
- One exception stops the run: yes, in the grader and the reference (F5); the verdict file is never written.
- Score level: both divide by the 10 tasks; both count a duplicated (model, task) row twice (F7).

## 2026-11-06T23:51Z: findings and decision entries

Findings (defects; details, counterexamples and commands in `audit/AUDIT.md`):

- F1 (C-test 4, 5): `judge()` never reads `errors`, so an exception on an `expected` test, or a missing function, is
  ignored. Panel: 3 of 40 verdicts (c02, c22, c40). Reference: correct.
- F2 (C-test 2): return values are compared after `json.dumps(default=repr)` and `json.loads`, so tuples equal lists.
  Panel: 2 of 40 (c16, c31). Reference: correct.
- F3 (C-extract 1, 3): a block opens only on a fence tagged exactly `python`. Panel: 0 of 40. Reference: correct.
- F4 (C-import 4): `ImportFrom.level` is ignored, so `from .math import sqrt` passes the check. Panel: 0. Reference:
  same defect.
- F5 (C-task 3): one response ends the whole run: uncaught `MemoryError`/`RecursionError` from `ast.parse`, and
  `JSONDecodeError` on a malformed result line. Panel: 0. Reference: same defect.
- F6 (C-exec 5, C-exec 7, C-test 3): the response's code can write the result line, read `job.json`, or replace
  `builtins.isinstance`, and pass without solving the task. Panel: 0. Reference: same defect.
- F7 (C-task 2): duplicate (model, task) rows count once per row; a model can score above 100. Panel: 0. Reference:
  same defect.
- G1 (step 1): model revisions, chat templates and the serving stack are not in the run records. All 40 rows.
- G2 (step 1): the child's `PYTHONHASHSEED`, stdin and environment come from the caller, and the OS and patch
  version are unstated; an order-dependent response flips with the hash seed. Panel: 0 verdicts. Reference: same.

Decision entries for the maintainers (proposed reading first; panel effect): D-palindrome-normalization (A; 4
verdicts, every model moves 10 points), D-line-terminator (A; 0), D-load-error (A; 0), D-main-guard (A; 0),
D-dynamic-import (A; 0), D-numeric-type (A; 0 under reading B as written), D-eq-object (B; 0), D-time-start (A; 0).

## 2026-11-06T23:56Z: step 7, report

- Report: `audit/AUDIT.md`, sha256 `837984cef1fef155a52f9b7f9e94d2be11e7deb2e97d72a2564e1a07849ca84c`. It leads with
  the panel error rate (5 of 40 verdicts against the contract, all false passes; 9 of 40 under the proposed
  readings), gives each finding's exact counterexample and the command that reproduces the grader's verdict, lists
  the 8 decision entries, and recommends fixing the grader.
- Counterexample files (`audit/tests/counterexamples/`, written by `audit/scripts/make_counterexamples.py`), sha256:
  `F1.jsonl` `f87d664c8774aeb6…`, `F1-raise-all.jsonl` `4a7a2eacd617dc9b…`, `F2.jsonl` `4bc2b7dbcda74227…`,
  `F3.jsonl` `07a9b59debe4e904…`, `F4.jsonl` `a77888c1a5daecc7…`, `F5-parse.jsonl` `8b60bcb317f34719…`,
  `F5-sum.jsonl` `44628ed3318b80b5…`, `F5-result.jsonl` `c81968a226cbeeb9…`, `F6.jsonl` `43b2ed5d24c4ff4a…`,
  `F7.jsonl` `70e5941d42507464…`, `G2.jsonl` `5a804d3238acb22b…`. The grader's outputs on them are in
  `audit/work/ce_*`.
- Not done in this exercise: step 6.4 and 6.5 (no reviewers), generation of new responses and a generation rerun (no
  compute), and every step that needs a repository, research branch, Hugging Face dataset or job launcher.
