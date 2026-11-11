# Audit: ToyOps `count-server-errors` verifier and scoring script

Report of step 7 of `skill/SKILL.md`, written 2026-11-11 02:06 UTC. The running record (pinned inputs, contract
hash and time, fixtures, decisions, findings, sample hashes) is `audit/ISSUE.md`. All commands below run in Git
Bash from `<W>` (called W) unless they start with `cd`.

## Error rate and effect on scores

The blinded review (step 6) did not run, because this exercise allows no subagents. There is therefore no
consensus-based error rate. What the audit can state:

- Against the contract labels (written by the auditor from the task text; not blind, not a consensus), the
  current grader is wrong on **5 of the 36 stored trial verdicts, 13.9%** (Clopper-Pearson 95% [4.7, 29.5]).
  All five are passes that the contract fails, so **5 of its 20 rewards (25%, [8.7, 49.1]) are false rewards**.
  Each of the five is mechanical, not a judgment call: three trials left no answer file at all, and two wrote
  the right number to the wrong path.
- The replacement grader (`audit/replacement/`) agrees with the contract labels on all 36. It implements the
  contract, so this agreement is by construction and is not an independent error estimate.
- The offline rerun of `verify.sh` reproduces all 36 stored exit statuses, so the stored verdicts are this
  verifier's verdicts.

| Configuration | Trials | Current score | Replacement score | Change, points (paired bootstrap 95%) | Trials that move |
|---|---|---|---|---|---|
| `agentx+falcon-70b` | 9 | 77.8 | 77.8 | +0.0 | none |
| `agentx+merlin-32b` | 9 | 77.8 | 55.6 | -22.2 [-55.6, +0.0] | t12 (F2), t14 (F1) |
| `agentx+osprey-14b` | 9 | 33.3 | 22.2 | -11.1 [-33.3, +0.0] | t21 (F1) |
| `agentx+kestrel-8b` | 9 | 33.3 | 11.1 | -22.2 [-55.6, +0.0] | t29 (F1), t35 (F2) |
| All 36 | 36 | 55.6 | 41.7 | -13.9 [-25.0, -2.8] | 5 |

The current grader ties falcon-70b with merlin-32b and osprey-14b with kestrel-8b. The contract orders them
falcon-70b > merlin-32b > osprey-14b > kestrel-8b. With 9 trials per configuration one trial is 11.1 points, and
no rerun of a configuration exists to compare these changes with (no compute), so the per-configuration
intervals are wide; the direction of every change is fixed, because every disagreement removes a pass.

Reproduce the two score tables:

```bash
cd <W>/case && python -B score_trials.py
cd <W> && python -B audit/scripts/panel.py && python -B audit/scripts/regrade_trials.py && python -B audit/replacement/score_trials.py audit/panel/regraded_trials
```

The first prints 77.8, 33.3, 77.8, 33.3 for falcon-70b, kestrel-8b, merlin-32b, osprey-14b; the last prints
77.8, 11.1, 55.6, 22.2. `panel.py` prints the per-trial table, the disagreements and the intervals above.

## Recommendation

**Fix the grader.** Three unambiguous defects (F1, F2, F3) each have a one-line fix, and the replacement passes
every fixture with complete scored coverage. The pre-registered condition for this recommendation (in
`audit/ISSUE.md`, step 6) also needs the blinded review to find the replacement's error rate lower than the
current grader's with a paired interval that excludes zero; that review is ready to run (sample frozen, batches
rendered, estimator written) but has not run, so the recommendation is provisional on it.

The fixes:

1. F1: in `verify.sh`, `exit` after `echo "no answer file"` becomes `exit 1`.
2. F2: delete the fallback to `$WORKSPACE/answer.txt` (lines 8 to 10).
3. F3: in `score_trials.py`, `trial_reward` returns `1.0 if type(exit_code) is int and exit_code == 0 else 0.0`.
4. G1, G2: pin the image by digest, store a hash of the task files and the agent's system prompt per trial, run
   the checker with `python3 -I`, and record whether the agent could write outside `/workspace`.

The decision entries below go to the maintainers; only `D-surrounding-text` moves any stored trial.

## Findings

Every finding's status in the reference grader is "no reference": TASK.md names no reference implementation.

### F1. A trial with no answer file passes (`verify.sh`, missing-file branch)

- Defect: `if [ ! -f "$ANSWER" ]; then echo "no answer file"; exit; fi`. A bare `exit` returns the status of the
  last command, `echo`, which is 0.
- Contract broken: README rule 1, "A trial whose `/workspace/out/answer.txt` is missing or empty fails."
- Counterexample (minimal): a sandbox whose `/workspace` holds only the empty directory `out/`, no file
  anywhere: `audit/repro/F1_no_answer/`.

  ```bash
  WORKSPACE=audit/repro/F1_no_answer TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
  ```

  prints `no answer file` and `exit 0`.
- Counterexample (stored trial): t14 (`agentx+merlin-32b`, agent status `error`, "context length exceeded")
  left only `/workspace/tmp/notes.txt` with two partial counts and no answer:

  ```bash
  cd <W>/case && WORKSPACE=trials/t14/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"
  ```

  prints `no answer file` and `exit 0`. t21 (no files at all) and t29 (timeout, only `tmp/scratch.txt`) behave
  the same.
- Fixtures: `verifier:4f53cda18c2baa0c` (empty sandbox), `verifier:4a6140effe24c8de` (empty `out/`),
  `verifier:2d4a6990d3419443` (notes only), `verifier:5155d908af56d922` (answer in `tmp/`),
  `verifier:405ef7ce62fe6965` (`out/answer.txt` is a directory).
- Share affected: 3 of 36 stored verdicts (8.3%; t14, t21, t29), 3 of the 20 passes. In the 64 enumerated
  sandbox layouts, F1 and F2 together give 24 wrong verdicts. An agent that does nothing passes.

### F2. An answer at `/workspace/answer.txt` is graded (`verify.sh`, answer path)

- Defect: `if [ ! -f "$ANSWER" ] && [ -f "$WORKSPACE/answer.txt" ]; then ANSWER="$WORKSPACE/answer.txt"; fi`.
- Contract broken: the instruction and README rule 1 name only `/workspace/out/answer.txt`; a trial whose
  `/workspace/out/answer.txt` is missing fails.
- Counterexample (minimal): `/workspace/answer.txt` holding the bytes `b'41\n'`, empty `out/`:
  `audit/repro/F2_root_answer/`.

  ```bash
  WORKSPACE=audit/repro/F2_root_answer TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
  ```

  prints `correct` and `exit 0`.
- Counterexample (stored trial): t12 (`agentx+merlin-32b`) wrote `b'41\n'` to `/workspace/answer.txt`:

  ```bash
  cd <W>/case && WORKSPACE=trials/t12/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"
  ```

  prints `correct` and `exit 0`. t35 (`agentx+kestrel-8b`) is the same.
- Fixtures: `verifier:64d7e51ce10deb36`, `verifier:61bb4e84a6e4f510`.
- Share affected: 2 of 36 stored verdicts (5.6%; t12, t35). t23 also used the fallback but wrote 37, so its
  verdict (fail) does not change.

### F3. A trial whose verifier did not run gets reward 1 (`score_trials.py`, reward mapping)

- Defect: `return 0.0 if exit_code else 1.0`. `None` (JSON null) and a missing field are falsy, so they give 1.0.
  So do `false`, `0.0` and `[]`, which the harness does not write.
- Contract broken: README rule 2, "A trial whose verifier did not run (`verifier_exit_code` null) fails", and
  rule 3, reward 1 only on a pass.
- Counterexample: a trials directory with one record, `audit/repro/F3_null_trials/t1/result.json`:

  ```json
  {"trial_id": "t1", "task": "count-server-errors", "config": "agentx+test", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": null}
  ```

  ```bash
  python -B case/score_trials.py audit/repro/F3_null_trials
  ```

  prints

  ```text
  config                 trials  passed   score
  agentx+test                 1       1   100.0
  ```

  (1 trial, 1 passed, score 100.0); the contract gives 0 passed and 0.0, which
  `python -B audit/replacement/score_trials.py audit/repro/F3_null_trials` prints.
- Fixtures: `score:766bd63355dc5bd6` (null), `score:9e2325ba76fe4090` (field missing),
  `score:8729d0b68ca87c05` (exit codes 0, 1, null score 66.7 instead of 33.3).
- Share affected: 0 of 36 stored verdicts; no stored record has a null exit code. The stored field that measures
  it is `verifier_exit_code` = null in `result.json` (the share of trials whose container was lost).

### G1. Unpinned inputs (protocol)

- The image is named by a tag (`toyops/count-server-errors:1.0`), which can be repointed; the agent's system
  prompt is not stored; `result.json` records no image digest, agent version or hash of the task files. The
  offline rerun matching all 36 stored exit statuses is the only evidence that the stored trials ran this
  verifier.
- Verify with `docker inspect --format '{{.Id}} {{.RepoDigests}}' toyops/count-server-errors:1.0` (not runnable
  offline). Share affected: not a verdict share.

### G2. The verifier runs in the agent's container without isolation (protocol, unverified)

- The harness runs `verify.sh` in the container the agent used, and the checker runs as `python3` from `PATH`
  without `-I`. TASK.md says everything under `/workspace` except the logs is writable and says nothing about
  the rest of the file system or the user. If the agent could write to the interpreter, its site-packages or its
  home directory's user site, it could set the verdict. Nothing in the stored records shows this happened: the
  snapshots hold only `/workspace`, so they could not show it.
- Verify with `docker run --rm toyops/count-server-errors:1.0 sh -c 'id; python3 -m site; touch
  /usr/local/lib/python3*/site-packages/x && echo writable'` under the agent's user (not runnable offline).
  Share affected: unknown.

### Robustness note R1 (scorer, outside the stored data)

One truncated `result.json`, or one without `config`, stops `score_trials.py` with a traceback before it prints
any table (`audit/fuzz_output.txt`, last section). No stored record is malformed, and TASK.md says the harness
always writes a record, so this changes no verdict here.

## Decision entries for the maintainers

| Id | Question | Proposed reading | What the current grader does | Stored trials affected |
|---|---|---|---|---|
| `D-surrounding-text` | May other words surround the integer? (`41 server errors`) | No: the file holds only the integer | Same as proposed | t09 (`41 server errors\n`, falcon-70b) and t17 (`Total 5xx: 41\n`, merlin-32b) fail; the other reading passes both, raising falcon-70b to 88.9 and merlin-32b to 66.7 |
| `D-whitespace` | Which characters are the ignored whitespace? | ASCII whitespace only | Python's `str.strip()`: the Unicode White_Space set plus U+001C to U+001F | none |
| `D-leading-zeros` | Does `041` count? | Yes | Yes, up to 4,300 digits; longer answers raise `ValueError` and fail | none |
| `D-plus-sign` | Does `+41` count? | No (weakly) | Same as proposed | none |
| `D-nonascii-digits` | Do `４１` or `٤١` count? | No | Same as proposed | none |

Wrong verdicts under the proposed readings that another reading makes right (decisions, not findings, by step
3's rule; none occurs in the stored trials):

- O1. `b'41\x1f\n'` (U+001F after the count) passes: Python's `str.strip()` removes U+001C to U+001F, which are
  whitespace under neither reading of `D-whitespace`. Only the other reading of `D-surrounding-text` makes the
  pass right. Fixtures `verifier:f20550d4ff9fccc4`, `verifier:ca11c01c5ebfb258`.

  ```bash
  WORKSPACE=audit/repro/O1_unit_separator TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
  ```

  prints `correct` and `exit 0`.
- O2. `'41\u00a0\n'` (no-break space; also U+3000, U+0085) passes; right under the other reading of
  `D-whitespace` or of `D-surrounding-text`. Fixtures `verifier:556ea5af0f0bc4ce`, `verifier:ae41aadcd7ee7384`,
  `verifier:131d469371aec69c`.

  ```bash
  WORKSPACE=audit/repro/O2_nbsp TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
  ```

  prints `correct` and `exit 0`.
- O3. 5,000 zeros followed by `41\n` fails through an uncaught `ValueError` (Python's 4,300-digit limit on
  `int()`); right under the other reading of `D-leading-zeros`. The exception fails only that trial. Fixture
  `verifier:ac969af12c767179`.

  ```bash
  WORKSPACE=audit/repro/O3_leading_zeros TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh 2>&1 | tail -1; echo "exit ${PIPESTATUS[0]}"
  ```

  prints

  ```text
  ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5002 digits; use sys.set_int_max_str_digits() to increase the limit
  exit 1
  ```

## What each step did

1. Pinned inputs from TASK.md and the manifest (all 83 files match) before reading any code; the image, the
   agent and the in-image locale are listed as unverified with the commands that would verify them.
2. Contract `audit/CONTRACT.md` (sha256 `bd6b9d96861c58d6c356463c76c2efc4fb4dc4ba69f60c3a0bb65d36f6357b1f`,
   recorded 01:47:50 UTC, before any grader code, `expected.json` or `result.json` was read). Correct count 41
   (20 + 17 + 4); `expected.json` holds 41. The data have three traps the contract settles: one quoted request
   contains a space (a whitespace field split gives 40: t07, t27), the gzip file (skipping it gives 37: seven
   trials), and byte counts that start with 5.
3. 48 verifier fixtures and 11 scorer fixtures (`audit/tests/fixtures.py`), run as unittest tests; the 16 that
   the current grader gets wrong are strict expected failures. Replacement grader built from the contract with
   one switch per decision; it passes every fixture under the proposed readings and every flipped-reading
   fixture.
4. No reference implementation, so no reference comparison or reference tests. 23 metamorphic edits on 4
   passing states (the current grader fails the 3 file-location edits); 5,000-input fuzz of the answer text
   (139 `ValueError`s, every disagreement explained by one decision switch); 64 sandbox layouts; scorer fuzz;
   content-free states (only the empty sandbox passes, through F1).
5. Panel = the 36 stored trials (no compute; no new responses). Results above. Not run: a rerun of a
   configuration with identical settings.
6. Pre-registered decision rule recorded; sample drawn by script with seed 20261111 as a census (5
   disagreements, 31 agreements) and frozen (case list sha256
   `81357f5204bd1c389a68dd4ba5efbddddcb55ed11365a20850114641f6c3e6d9`); two batches in different orders, the
   helper, the decompressed logs and the two filled-in reviewer prompts are in `audit/frozen/round1/`, the keys
   in `audit/frozen/keys/`. **Not run: the two reviewer runs (6.4) and the estimate (6.5).**
   `audit/scripts/estimate_error.py` computes 6.5 once `reviews_A.jsonl` and `reviews_B.jsonl` exist; it was
   checked only on a synthetic input to see that it runs, and that input was deleted.
7. This report.

Skipped because this exercise has no infrastructure for them: opening or updating an issue (`file-issue`; the
record is `audit/ISSUE.md`), the repository's grader test directory and `manage-pr` (the tests live in
`audit/tests/`), a research branch (`research-engineering`), a pinned Hugging Face dataset (frozen files and
hashes are in `audit/frozen/` and `audit/ISSUE.md`), job launches (`use-iris`), and the style guide
`docs/dev-guide/writing-style/issues.md`.

Execution environment: the verifier ran on Git Bash 5.3.15 (Cygwin) and Windows Python 3.12.10 with
`PYTHONUTF8=1`, standing in for the image's bash 5.2 and Debian Python 3.12. The checker opens files with an
explicit UTF-8 encoding and prints only ASCII, and the 36 stored exit statuses reproduce, so the substitution is
unlikely to change a verdict; it was not checked against the image.

## Reproduce everything

```bash
cd <W>
python -B -m unittest discover -s audit/tests -p "test_*.py"    # Ran 186 tests ... OK (expected failures=19)
python -B audit/scripts/fuzz.py 5000 20261111                   # matches audit/fuzz_output.txt
python -B audit/scripts/panel.py                                # matches audit/panel_output.txt
python -B audit/scripts/make_repro.py                           # recreates audit/repro/
```

## Files

| Path | What it is |
|---|---|
| `audit/ISSUE.md` | the audit record (stand-in for the issue) |
| `audit/CONTRACT.md` | contracts and decision entries |
| `audit/tests/` | fixtures, property tests, input checks (`harness.py`, `fixtures.py`, `test_*.py`) |
| `audit/replacement/` | replacement verifier (`tests/verify.sh`, `tests/check_answer.py`, `tests/expected.json`) and scorer |
| `audit/scripts/` | `panel.py`, `fuzz.py`, `draw_sample.py`, `estimate_error.py`, `regrade_trials.py`, `make_repro.py`, `dump_trials.py` |
| `audit/panel/panel_verdicts.json`, `audit/panel_output.txt`, `audit/fuzz_output.txt` | step 4 and 5 outputs |
| `audit/frozen/round1/`, `audit/frozen/keys/` | frozen review sample, batches, helper, prompts; keys and case list |
| `audit/repro/` | the counterexample states cited above |
