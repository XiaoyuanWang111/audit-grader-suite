# Audit: ToyOps `count-server-errors` verifier and scoring script

Audited 2026-11-07 (UTC) following `skill/SKILL.md`, offline. The running record (pins, contract hash and time,
findings, decision entries, frozen-sample hashes) is `audit/ISSUE.md`. Commands below run from the audit root, the
folder that holds `case/` and `audit/`, in Git Bash. The image passes `PYTHON=python3`; on this host the
interpreter is named `python`.

## Result

**Error rate: not measured.** The blinded review (step 6) did not run, so there is no reviewed error rate. Measured
against the contract instead, the current verifier gives a wrong verdict on **5 of the 36 stored trials (13.9%)**.
All 5 are passes, so **5 of its 20 passes (25%) are false**. No reading of the task text makes any of them correct:
3 trials left no answer file (F1) and 2 wrote the answer to `/workspace/answer.txt` instead of
`/workspace/out/answer.txt` (F2). The scoring script adds no error on these records, because none has a null exit
status (F3 needs one).

**Effect on scores.** Correcting the 5 verdicts lowers three of the four configuration scores, by 11.1 to 22.2
points. The overall pass rate falls from 55.6% (20/36) to 41.7% (15/36). Both ties in the current scores break:
falcon and merlin are no longer level at 77.8, and osprey and kestrel are no longer level at 33.3.

| Configuration | Current score (passes/9) | Contract, proposed readings | Change, points [95% paired bootstrap over trials] | Trials that flip |
|---|---|---|---|---|
| `agentx+falcon-70b` | 77.8 (7) | 77.8 (7) | 0.0 | none |
| `agentx+merlin-32b` | 77.8 (7) | 55.6 (5) | −22.2 [−55.6, 0.0] | t12 (F2), t14 (F1) |
| `agentx+osprey-14b` | 33.3 (3) | 22.2 (2) | −11.1 [−33.3, 0.0] | t21 (F1) |
| `agentx+kestrel-8b` | 33.3 (3) | 11.1 (1) | −22.2 [−55.6, 0.0] | t29 (F1), t35 (F2) |

The 5 flips come from grading defects and do not depend on sampling. The intervals show how much the change itself
could move with a different draw of 9 trials. No configuration was rerun (there is no compute), so these changes
cannot be compared with a rerun difference. Each 9-trial score has a 95% Wilson interval 41 to 55 points wide (for
example falcon [45.3, 93.7]). One decision entry, `D-surrounding-text`, also changes stored verdicts: under its
non-proposed reading, t09 (`41 server errors`) and t17 (`Total 5xx: 41`) pass, which raises falcon to 88.9 and
merlin to 66.7.

The worst defect is F1: an agent that writes nothing gets reward 1. The 3 stored trials that crashed or timed out
before writing an answer (t14 context length exceeded, t21 shell killed, t29 timeout) were all scored as passes.

## Recommendation: fix the grader

The task text decides every stored case, and each defect is a small code change, so the benchmark does not need
replacing. Admitting the grader as it is would keep rewarding agents that produce no answer.

1. `verify.sh`: end with a nonzero status when the answer file is missing (F1), and delete the fallback to
   `/workspace/answer.txt` (F2).
2. `score_trials.py`: give reward 1 only when `verifier_exit_code` is the integer 0, and 0 for null or a missing
   field (F3).
3. `check_answer.py`: strip only the whitespace that the maintainers choose in `D-whitespace` (proposed: ASCII
   whitespace, `strip(" \t\n\r\x0b\x0c")`) (F4). Compare digit strings (`text.lstrip("0") or "0"` against
   `str(expected)`) instead of calling `int()` (F5).
4. Harness: run the verifier in a fresh container from a pinned image digest, with only `/workspace/out` copied in
   (G1). Record in every `result.json` the image digest, the `agentx` version and a hash of its prompt, the model
   revision, the decoding settings and the sha256 of each verifier file (G2).
5. Make `audit/tests/` the regression suite, and remove each `expectedFailure` when its fix lands. Then rescore
   the stored trials: with the proposed readings, the scores become falcon 77.8, merlin 55.6, osprey 22.2 and
   kestrel 11.1.

The step 6 gate recorded in `ISSUE.md` (01:50:37Z) states which review results would change this recommendation.
It stays provisional until a blinded review runs on the frozen sample.

## Findings

No reference implementation exists (ToyOps ships only this verifier), so no finding has a reference status. The
share counts stored verdicts: 36 trials, one check each.

| Id | Stage | Contract broken | Fixtures (id) | Stored verdicts affected |
|---|---|---|---|---|
| F1 | `verify.sh`, missing answer file | C1: a missing file fails (README rule 1) | `answer-file:63b0aeed606ecf87`, `:d8f9430642993653`, `:87f244f6c26be477`, `:95d28e0cc997f823`; `:47274acbf3e10392` (dangling link, not run here) | 3/36 (8.3%): t14, t21, t29, all false passes |
| F2 | `verify.sh`, which file is graded | C1: only `/workspace/out/answer.txt` is graded | `answer-file:3660b68933683665`, `:de59d63ef63e5068` | 2/36 (5.6%) wrong: t12, t35. t23 was also graded from the wrong file and failed only because its count (37) is wrong |
| F3 | `score_trials.py`, reward | C2: a null `verifier_exit_code` fails (README rule 2) | `score:291a34fd5d90c606`, `:0c5c0efad62e6694`, `:d103d7ebc69dca67` | 0/36: no record has a null status (field `verifier_exit_code`) |
| F4 | `check_answer.py`, whitespace | C1: U+001C..U+001F are not whitespace under either reading of `D-whitespace` | `answer-file:ebaf2abe664110c0`, `:c4c37c497ba93069` | 0/36: no stored answer holds bytes 0x1C to 0x1F |
| F5 | `check_answer.py`, comparison | Step 4: an exception is a grading failure; under `D-leading-zeros` A, `0`×4999 + `41` passes | `answer-file:18217fc43af8aa26`, `:c1f5ed23c2682eb5` | 0/36: no stored answer is longer than 4,300 digits |
| G1 | grading environment | C1: the verifier does not run anything the agent wrote | `answer-file:918bd010e9cff4fb` | Not measurable: trials store only `/workspace`. Measuring it needs a record of the interpreter the verifier ran (path, sha256) and of files changed outside `/workspace` |
| G2 | run records | Step 1: every input that can change a verdict is pinned | none (a missing record) | all 36 records |

### F1: a missing answer file passes

`verify.sh` lines 12 to 15 are `if [ ! -f "$ANSWER" ]; then echo "no answer file"; exit; fi`. A bare `exit` returns
the status of the last command, `echo`, which is 0. A directory or a dangling link at the answer path takes the same
branch.

Counterexample: `/workspace/out` exists and is empty.

```bash
mkdir -p audit/tmp/repro/F1/workspace/out
WORKSPACE=audit/tmp/repro/F1/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
# no answer file
# exit 0
```

The same happens on stored trial t21: `WORKSPACE=case/trials/t21/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"`.

### F2: an answer at `/workspace/answer.txt` is graded

`verify.sh` lines 8 to 10 switch to `$WORKSPACE/answer.txt` when `/workspace/out/answer.txt` is not a regular file.

Counterexample: `/workspace/out` is empty, and `/workspace/answer.txt` holds the bytes `34 31 0a` (`41\n`).

```bash
mkdir -p audit/tmp/repro/F2/workspace/out && printf '41\n' > audit/tmp/repro/F2/workspace/answer.txt
WORKSPACE=audit/tmp/repro/F2/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
# correct
# exit 0
```

### F3: a trial whose verifier did not run gets reward 1

`score_trials.py` computes `return 0.0 if exit_code else 1.0`. A null status, or a record without the field, is
falsy, so it gets reward 1.

Counterexample: one record whose `verifier_exit_code` is null.

```bash
mkdir -p audit/tmp/repro/F3/trials/x01
printf '%s\n' '{"trial_id": "x01", "task": "count-server-errors", "config": "agentx+test", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": ""}' > audit/tmp/repro/F3/trials/x01/result.json
python case/score_trials.py audit/tmp/repro/F3/trials
# config                 trials  passed   score
# agentx+test                 1       1   100.0
```

### F4: U+001C to U+001F around the count are ignored

`check_answer.py` calls `str.strip()`, and Python counts U+001C..U+001F (the file, group, record and unit
separators) as whitespace. Neither POSIX `[:space:]` nor Unicode White_Space includes them. Every other C0 control
character, and DEL, next to `41` fails, as it should; this is checked by `test_control_characters_other_than_1c_1f_fail`.

Counterexample: `/workspace/out/answer.txt` holds the bytes `34 31 1c`.

```bash
mkdir -p audit/tmp/repro/F4/workspace/out && printf '41\034' > audit/tmp/repro/F4/workspace/out/answer.txt
WORKSPACE=audit/tmp/repro/F4/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
# correct
# exit 0
```

### F5: an uncaught exception on answers longer than 4,300 digits

`int(text)` raises ValueError above Python's 4,300-digit limit, which exists in Python 3.11 and later. The verifier
exits 1, so a long answer always fails, but it fails through a traceback. Under the proposed reading of
`D-leading-zeros`, a zero-padded `41` should pass. The fuzzer hit this 142 times in 3,000 cases (a count of its own
input distribution, not a rate).

Counterexample: `/workspace/out/answer.txt` holds 4,999 bytes `0x30`, then `41\n` (5,001 digits).

```bash
mkdir -p audit/tmp/repro/F5/workspace/out && python -c "import sys; sys.stdout.buffer.write(b'0' * 4999 + b'41\n')" > audit/tmp/repro/F5/workspace/out/answer.txt
WORKSPACE=audit/tmp/repro/F5/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
# ... ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5001 digits; ...
# exit 1
```

### G1: the verifier trusts the agent's container

The harness copies `task/tests/` into the container the agent just used and runs `bash /tests/verify.sh` there.
The verifier then calls the interpreter by the bare name `python3`, which PATH resolves, with Python's site
processing on. Whatever the agent left on PATH therefore decides the verdict, and the same holds for Python startup
files (`usercustomize.py`, `.pth`), a background process that rewrites `/tests/expected.json`, or a `/tests`
directory created in advance (depending on how the harness copies into it). Whether an agent can write to those
places depends on the image's user and permissions, which nothing records. This is unverified; the command that
would check it is in `ISSUE.md`.

Counterexample: `/workspace/out/answer.txt` holds `37\n`, and a directory outside `/workspace`, first on PATH,
holds an executable `python3` with the content `#!/bin/sh`, `echo correct`, `exit 0`.

```bash
mkdir -p audit/tmp/repro/G1/workspace/out audit/tmp/repro/G1/bin && printf '37\n' > audit/tmp/repro/G1/workspace/out/answer.txt
printf '#!/bin/sh\necho correct\nexit 0\n' > audit/tmp/repro/G1/bin/python3 && chmod +x audit/tmp/repro/G1/bin/python3
PATH="$PWD/audit/tmp/repro/G1/bin:$PATH" WORKSPACE=audit/tmp/repro/G1/workspace TESTS_DIR=case/task/tests PYTHON=python3 bash case/task/tests/verify.sh; echo "exit $?"
# correct
# exit 0
```

### G2: the run records do not pin what produced them

The image is named by a mutable tag (`toyops/count-server-errors:1.0`) without a digest. `agentx` 0.4's system
prompt is not stored. The records give model names without revisions, and give no decoding settings beyond the
temperature in `TASK.md`. No record says which verifier files ran. Rerunning the pinned verifier reproduces all 36
stored exit statuses and outputs, which is the only link between the records and these files.

```bash
python -c "import json; print(sorted(json.load(open('case/trials/t01/result.json'))))"
# ['agent_error', 'agent_status', 'agent_steps', 'config', 'task', 'trial_id', 'verifier_exit_code', 'verifier_output']
```

All seven counterexamples run in sequence with `bash audit/scripts/repro_findings.sh`. The output of the last run
is in `audit/results/repro_findings.txt`.

## Decision entries (for the evaluation's maintainers)

The text allows two verdicts for each entry below. The replacement grader has one switch per entry. Only
`D-surrounding-text` changes a stored verdict.

| Id | Question | Reading A (proposed) | Reading B | Current verifier | Stored trials affected |
|---|---|---|---|---|---|
| `D-whitespace` | Which characters besides space, tab, LF and CR are ignored around the count? | ASCII whitespace (adds VT, FF): `41\u00a0` fails | Unicode whitespace: NBSP, U+3000 and NEL are ignored | B (`str.strip()`), plus U+001C..U+001F (F4) | 0 |
| `D-leading-zeros` | Is `041` a decimal integer with value 41? | yes, passes | no, fails | A, up to 4,300 digits (above that F5) | 0 |
| `D-plus-sign` | Is `+41` a decimal integer with value 41? | yes, passes | no, fails | B | 0 |
| `D-digits` | Do non-ASCII decimal digits (`٤١`, `４１`) count? | no, fail | yes, pass | A | 0 |
| `D-surrounding-text` | May other text surround the integer (`41 server errors`)? | no, fails | yes, if the file holds exactly one integer and it is 41 | A | 2: t09 (falcon), t17 (merlin); B adds +11.1 to each |
| `D-bom` | Does a byte-order mark or UTF-16 encoding change the content? | yes, `\ufeff41` fails | no, decode by the BOM | A | 0 |
| `D-symlink` | Does a symbolic link at the answer path hold its target's content? | yes, follow it | no, only a regular file counts | A (from the code: `[ -f ]` and `open()` follow links; not run, see Limits) | 0 |

The contract was written with a single `D-numeral` entry. After reading the code, it was split into
`D-leading-zeros` and `D-plus-sign`, because the verifier passes `041` and fails `+41`. No proposed verdict changed.

## Steps

| Step | Status | What it found |
|---|---|---|
| 1. Pin the inputs | Run | All 83 manifest hashes match. Pin checks before and after every run are in `audit/results/pin_checks.log`. Unpinned inputs are G2. Unverified inputs (image digest, image user and writable paths, `agentx` prompt) are listed in `ISSUE.md` with the commands that would verify them |
| 2. Contract | Run | `audit/CONTRACT.md`, hashed at 2026-11-07T01:17:15Z (sha256 `533efaa0e1a3f59a15e476437083fffd2a896f344d2b52a2585d3326654fd4ef`) before any grader code or run record was read. The contract's own count of the logs gives N = 41, which equals `expected.json`. 7 decision entries; one later change, recorded with its reason |
| 3. Fixtures | Run | 58 sandbox-state fixtures run through `bash verify.sh`; 55 ran, and the 3 symlink fixtures were skipped. The verifier differs from the label on 14: 9 are findings (F1 ×4, F2 ×2, F4 ×2, G1 ×1) and 5 are decisions. 10 scoring fixtures; 3 fail (F3). The replacement passes all 55 |
| 4. Reference and stress | Run, no reference | No reference implementation, and the grader has no unit tests that could encode a decision. Property tests: 14, of which 6 fail (F1 ×2, F2, F4 ×2, F5). All 24 file states that `verify.sh` branches on: 9 disagreements (6 F1, 3 F2). Fuzz of the content check, 3,000 cases: 13 findings (F4), 22 `D-whitespace`, 2 `D-plus-sign`, 45 `D-leading-zeros`, 142 exceptions (F5). Content-free responses: only "no answer file" passes (F1); an empty file, whitespace only, repeated text and a copy of the instructions all fail |
| 5. Panel | Stored trials only | The 36 stored trials are the panel; no new responses were generated and no configuration was rerun. Table under Result |
| 6. Blinded review | **Not run** | No subagents in this exercise. The sample was drawn and frozen (6.1, 6.2) and the batches rendered (6.3): a census of 5 disagreements and 31 agreements, seed 20261107, case list sha256 `2021474d2f785eb67cbfa37cc5631008d2b7e328d2e10dfcbb5fe304edbcd2ef`, with keys, two orders, reviewer prompts and a helper in `audit/frozen/round1/` |
| 7. Report | This file | |

What the stored records show (step 5): 31 trials completed, 3 timed out (t05, t15, t29) and 2 ended with an agent
error (t14, t21). 30 trials wrote `/workspace/out/answer.txt`, 3 wrote only `/workspace/answer.txt` (t12, t23, t35)
and 3 wrote no answer (t14, t21, t29). No `verifier_exit_code` is null. The wrong counts trace to known mistakes: 37
(7 trials) skips the `.gz` file; 40 (t07, t27, whose `count.sh` uses `awk '{print $9}'`) misreads the one request
containing a space; 45 (2) also counts response sizes of 500 to 599; 36 (1) makes both of the first two mistakes;
one trial wrote 0, one an empty file, and two added words. The verifier grades all of these correctly. Scored
coverage is 36/36 for every grader.

Further observations on `score_trials.py`, none a finding: it prints 100 × the mean reward, while the README defines
the score as the mean. It skips a trial folder without `result.json` and does not say so. One truncated record, or
one with a null `config`, stops the whole run with no scores (`audit/results/probe_scoring_robustness.json`).

## Skipped steps and substitutions

- No issue tracker: the record is `audit/ISSUE.md` (no `file-issue`).
- No repository or research branch: the fixtures are runnable tests under `audit/tests/` rather than in the grader's
  test directory, and the scripts and the replacement grader are under `audit/scripts/`. Nothing was landed, so
  `manage-pr` and `research-engineering` were not used.
- No Hugging Face dataset: the frozen sample, keys, batches and prompts are under `audit/frozen/round1/`, with their
  sha256 in `ISSUE.md`.
- No job launcher and no compute: `use-iris` was not used, and no new responses were generated.
- pytest is not installed: the tests use `unittest`, with `unittest.expectedFailure` as the strict-xfail
  equivalent (an unexpected success fails the run). Run them with `python -I audit/tests/<file>.py -v`; all three
  files currently pass with their expected failures (14, 3 and 6).

## Limits

- This host is not the image. It runs Windows 11 with Git Bash 5.3.15 (the image has bash 5.2) and Python 3.12.10
  (the image has 3.12). Runs set `PYTHONUTF8=1`, since the image's locale is not recorded. The checker opens files
  with explicit UTF-8, and 12 fixtures (8 with bytes outside ASCII) gave the same verdict with UTF-8 mode on and
  off.
- This host cannot create symbolic links (WinError 1314, and Git Bash's `ln -s` copies the file). So the
  three symlink fixtures (a dangling link, a link to a file in `/workspace`, and a link to `/tests/expected.json`)
  did not run, and the verifier's link behavior above comes from reading its code.
- G1's precondition, an agent that can write to a PATH directory, `/tests` or Python's site directories, is
  unverified.
- The stored trials were read while pinning inputs (step 1), before the replacement was written. Its switches come
  from the contract's decision table, and it was frozen before the panel ran.
- Deviations from the working-folder rule: one probe directory was created in the session's scratchpad and removed
  at once, and one existence check looked at `C:\Windows\System32\bash.exe`, to avoid the WSL launcher. An
  in-process import wrote `case/task/tests/__pycache__/`. It was removed, no pinned file changed, and no verdict read
  it (see `ISSUE.md`, 01:47Z).

## Files

- Record: `audit/ISSUE.md`. Contract: `audit/CONTRACT.md`.
- Tests: `audit/tests/fixtures.py`, `test_verifier_fixtures.py`, `test_scoring.py`, `test_properties.py`.
- Replacement grader: `audit/scripts/replacement_verifier.py`. Panel, fuzz, state enumeration, probes, sample:
  `audit/scripts/panel.py`, `fuzz_check_answer.py`, `enumerate_states.py`, `probe_scoring_robustness.py`,
  `draw_sample.py`. Reproduction: `audit/scripts/repro_findings.sh`.
- Results: `audit/results/` (fixture table, panel, fuzz, states, probes, test logs, pin checks).
- Frozen review sample: `audit/frozen/round1/`.
