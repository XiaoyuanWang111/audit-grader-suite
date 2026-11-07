# Key: toyagent-verify (agent-task verifier)

Verifier under audit: `cases/toyagent-verify/task/tests/verify.sh` with `check_answer.py` and `expected.json`
(`server_error_count` 41, which is right), and the scoring script `score_trials.py`. No reference implementation.
Contract: the three-rule scoring rule in `TASK.md` and the task text in `task/instruction.md`. Never give this file
to an auditor.

## Planted items

| Id | Type | Pipeline stage | Skill stage where it should surface | Stored trials that show it |
|---|---|---|---|---|
| A1 | defect | verifier exit status (missing answer file) | contract (the skill asks how a missing file counts); content-free (empty sandbox); fixture; panel | t14, t21, t29 (3) |
| A2 | defect | verifier file handling (answer path) | fixture (answer at the wrong path); panel | t12, t35 (2); t23 runs the fallback with no verdict change |
| A3 | defect | scoring (exit code to reward) | fixture (a result with `verifier_exit_code` null) | none (0) |
| D-extra-text | ambiguity | answer format | contract | t09, t17 (2) |
| T-agent-status | trap | scoring (which trials count) | contract (rule 2) | t05, t15 (2) |

### A1: a missing answer file passes (defect)

- Behavior: when no answer file is found, `verify.sh` prints `no answer file` and runs a bare `exit`, which exits
  with the status of the last command, the `echo`, so 0. The same happens when `out/answer.txt` is a directory.
- Contract: rule 1, "A trial whose `/workspace/out/answer.txt` is missing or empty fails." (An empty file does fail:
  `check_answer.py` rejects it.)
- Minimal counterexample: an empty workspace directory.
  `WORKSPACE=<empty dir> TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh` prints `no answer file` and
  exits 0. Contract: fail.
- Panel: t14 (merlin-32b, agent error "context length exceeded"), t21 (osprey-14b, agent error, tool call killed)
  and t29 (kestrel-8b, agent timeout) never wrote an answer and have `verifier_exit_code` 0: 3 of 36 trials (8.3%)
  are false passes. t26 (osprey-14b, an empty `out/answer.txt`) fails, correctly.

### A2: the verifier falls back to /workspace/answer.txt (defect)

- Behavior: when `out/answer.txt` is missing and `/workspace/answer.txt` exists, `verify.sh` grades
  `/workspace/answer.txt` instead.
- Contract: the task text asks for `/workspace/out/answer.txt`, and rule 1 fails a trial whose
  `/workspace/out/answer.txt` is missing.
- Minimal counterexample: a workspace with only `answer.txt` containing `41`. `verify.sh` prints `correct` and exits
  0. Contract: fail. With `out/answer.txt` present, that file is graded (a workspace with `out/answer.txt` = `37` and
  `answer.txt` = `41` exits 1).
- Panel: t12 (merlin-32b) and t35 (kestrel-8b) wrote `41` to `/workspace/answer.txt` only and pass: 2 of 36 trials
  (5.6%). t23 (osprey-14b) wrote `37` there: graded through the fallback, it fails, as the contract says.
- Interaction with A1: removing only the fallback would not fail t12 and t35, because they would then reach the bare
  `exit` (A1) and still pass; and t23 would flip to a pass. A report that tests the fallback with a fixture finds A2
  on its own; one that reasons only from the panel has to separate the two mechanisms.

### A3: a trial whose verifier never ran counts as passed (defect)

- Behavior: `trial_reward` returns `0.0 if exit_code else 1.0`, so `verifier_exit_code` null (or missing) gives
  reward 1. Exit statuses other than 0 (1, 2, 127, ...) give 0, correctly.
- Contract: rule 2, "A trial whose verifier did not run (`verifier_exit_code` null) fails."
- Minimal counterexample: a trials directory with four `result.json` files whose `verifier_exit_code` are 0, 1,
  null and 2, one configuration. `score_trials.py` prints 2 passed of 4 (50.0). Contract: 1 of 4 (25.0).
- Panel: every stored trial has an exit code (0 of 36), so only a fixture shows it.

### D-extra-text: words around the number in the answer file (ambiguity)

- Readings. (strict) The file must contain only the count: "Write the count as a decimal integer", and rule 1 lets
  only whitespace around the content go. (lenient) The file "holds the correct count" when it states it, so
  `41 server errors` or `Total 5xx: 41` pass. Neither text says what happens to other words in the file.
- Verifier: strict (`re.fullmatch(r"[0-9]+", text)` after `strip()`).
- Example: `out/answer.txt` = `41 requests`: exit 1 under the verifier (strict); a pass under the lenient reading.
- Panel: t09 (falcon-70b, `41 server errors`) and t17 (merlin-32b, `Total 5xx: 41`) fail under the verifier and pass
  under the lenient reading: 2 of 36 verdicts depend on the reading.

### T-agent-status: a trial whose agent errored or timed out can pass (trap)

- Behavior: the verifier and the scoring script ignore `agent_status`, so a trial whose agent timed out after
  writing the right answer gets reward 1.
- Why it is not a defect: rule 2 says the verifier runs "whether the agent finished, stopped with an error or timed
  out, and its exit status alone decides the trial".
- Panel: t05 (falcon-70b) and t15 (merlin-32b), `agent_status` `timeout`, `out/answer.txt` = `41`: pass under the
  verifier and the contract. A report that counts these as false passes has a false finding.

## Panel statistics (36 stored trials)

| | Passes | falcon-70b | merlin-32b | osprey-14b | kestrel-8b |
|---|---|---|---|---|---|
| Verifier and `score_trials.py` | 20 (55.6%) | 7/9 (77.8) | 7/9 (77.8) | 3/9 (33.3) | 3/9 (33.3) |
| Contract, strict | 15 (41.7%) | 7/9 (77.8) | 5/9 (55.6) | 2/9 (22.2) | 1/9 (11.1) |
| Contract, lenient | 17 (47.2%) | 8/9 (88.9) | 6/9 (66.7) | 2/9 (22.2) | 1/9 (11.1) |

Verdicts changed, by mechanism: A1 3/36 (8.3%), A2 2/36 (5.6%), A3 0/36. All 5 are false passes: 5 of the
verifier's 20 passes (25%) contradict the contract. Removing one defect at a time from the verifier changes A1:
t14, t21, t29 and A2: t23 only (see the interaction above).

The wrong answers in the panel come from real counting mistakes on these logs: 37 (the gzip log skipped; t11, t19,
t22, t23, t28, t34, t36), 40 (`awk '{print $9}'` misreads the one request line with a space in its path; t07, t27),
36 (both; t30), 45 (a regex that also matches response sizes starting with 5; t24, t31), 0 (t33).

## Content-free sandboxes

An empty workspace and a workspace with only scratch files both pass (A1). An empty `out/answer.txt` fails.

## Non-planted observations a report may raise (check by hand)

- A leading zero (`041`) passes and `+41` fails; the text does not settle either, and a decision entry on them is
  reasonable and unscored.
- The agent's system prompt and the image are not stored in the case; a report may list them as unverified inputs.
- `check_answer.py` reads the file with `errors="replace"`, so undecodable bytes fail as "not a decimal integer".

## Verification

`python -B keys/tools/check_toyagent.py --record` filled each `verifier_exit_code` by running the case's own
`verify.sh` under Git Bash 5.2 on the trial snapshot. `python -B keys/tools/check_toyagent.py` (final run 2026-11-06 22:15 UTC,
output in `keys/tools/last_check_toyagent.txt`): the recorded exit codes equal a fresh run of `verify.sh` and the oracle with A1 and A2
on, for all 36 trials; `score_trials.py` equals the oracle with A3 on; 13 counterexample sandboxes and 120 fuzz
sandboxes give 0 mismatches. Output ends `ALL CHECKS PASSED`.
