# ToyOps count-server-errors: an agent task graded by a verifier script

ToyOps is a set of small sandboxed shell tasks for agents. This case holds one task, `count-server-errors`: the
agent must count the server errors in three web-server access logs and write the count to an answer file. After the
agent stops, a verifier script grades the answer file, and a scoring script turns the verifier's exit statuses into
rewards and scores.

## Files

| File | What it is |
|---|---|
| `task/instruction.md` | the task text the agent sees |
| `task/environment/logs/` | the sandbox's input files, mounted read-only at `/workspace/logs` |
| `task/tests/verify.sh`, `task/tests/check_answer.py`, `task/tests/expected.json` | the verifier under audit |
| `score_trials.py` | the scoring script under audit: reward per trial and score per configuration |
| `trials/tNN/result.json`, `trials/tNN/workspace/` | 36 stored trials: the run record and the final sandbox files |
| `MANIFEST.sha256` | sha256 of every other file in this directory |

## What the agent sees

The agent program is `agentx` 0.4, a tool-calling agent whose one tool runs a shell command in the sandbox and
returns its output. It sends `task/instruction.md` unchanged as the first user message, after its fixed system
prompt, and stops when the model ends its turn without a tool call, after 40 steps, or after 600 seconds:

```text
The directory /workspace/logs holds the access logs of a web server: access.log, access.log.1 and access.log.2.gz (gzip-compressed). Each line is one request, and the HTTP status code is the field right after the quoted request.

Count the requests in all three files whose status code is a server error (500 to 599). Write the count as a decimal integer to /workspace/out/answer.txt.

/workspace/logs is read-only. The sandbox has no network access.
```

## Sandbox and verifier

- Image `toyops/count-server-errors:1.0` (Debian, Python 3.12, bash 5.2, gzip), no network.
- `/workspace/logs` holds the three files of `task/environment/logs/`, read-only. `/workspace/out` is an empty
  directory. Everything under `/workspace` except `/workspace/logs` is writable.
- After the agent stops, whether it finished, stopped with an error or timed out, the harness copies `task/tests/`
  to `/tests` in the same container and runs `bash /tests/verify.sh` with `WORKSPACE=/workspace`,
  `TESTS_DIR=/tests` and `PYTHON=python3`. It stores the exit status in `result.json` as `verifier_exit_code` and
  the output as `verifier_output`. If the container was lost before the verifier could run, `verifier_exit_code` is
  `null`.
- `score_trials.py` reads every `trials/*/result.json` and prints, per configuration, the trials, the passes and
  the score.

## Scoring rule (from the ToyOps README)

1. A trial passes when `/workspace/out/answer.txt` holds the correct count: the number of requests in the three log
   files whose status code is 500 to 599 (`expected.json` stores it). Whitespace around the content, including a
   final newline, is ignored. A trial whose `/workspace/out/answer.txt` is missing or empty fails.
2. The verifier runs on the final sandbox of every trial, whether the agent finished, stopped with an error or timed
   out, and its exit status alone decides the trial: 0 passes and anything else fails. A trial whose verifier did
   not run (`verifier_exit_code` null) fails.
3. A trial's reward is 1 if it passes and 0 otherwise. A configuration's score is its mean reward over all of its
   trials.

## Running it offline

The trial snapshots replace the container. From this directory, with bash (Git Bash on Windows):

```text
WORKSPACE=trials/t01/workspace TESTS_DIR=task/tests PYTHON=python3 bash task/tests/verify.sh; echo "exit $?"
python score_trials.py                            # scores trials/*/result.json
```

Use `PYTHON=python` where `python3` is not the interpreter's name.

## Stored trials

36 trials of `agentx` 0.4 with four models (`agentx+falcon-70b`, `agentx+merlin-32b`, `agentx+osprey-14b`,
`agentx+kestrel-8b`), 9 trials per configuration, all at temperature 0.7. Each `trials/tNN/` holds `result.json`
(`trial_id`, `task`, `config`, `agent_status` (`completed`, `error` or `timeout`), `agent_error`, `agent_steps`,
`verifier_exit_code`, `verifier_output`) and `workspace/`, every file under `/workspace` at the end of the trial
except the read-only logs. Empty directories are not stored.

## Pinned inputs

Every file in this directory, by the sha256 in `MANIFEST.sha256`; the agent program `agentx` 0.4 and the image tag
above, which are not stored here.
