# Audit: ToyOps `count-server-errors` verifier and scoring script

Grader under audit: `case/task/tests/verify.sh`, `check_answer.py` and
`expected.json` (the verifier), and `case/score_trials.py` (the scoring
script). Paths are relative to `<run directory>`.
The running record (pins, contract hashes and times, findings, decision
entries, frozen-sample hashes) is `audit/ISSUE.md`; the contract is
`audit/CONTRACT.md` (version 2). Written 2026-11-07, offline.

## Result

The blinded review (step 6) did not run, so this report has no
reviewer-consensus error rate. Measured against the contract instead, the
grader's verdict is wrong on 5 of the 36 stored trials (13.9%). All five are
false passes: 5 of the grader's 20 passes (25.0%) are trials that the task's
scoring rule fails. They raise the mean score over the 36 trials from 41.7 to
55.6, +13.9 points [+2.8, +25.0], and two of the four configurations by 22.2
points.

| Configuration | Trials | Score, grader | Score, contract | Change, points [95% bootstrap] | Trials that differ |
|---|---|---|---|---|---|
| `agentx+falcon-70b` | 9 | 77.8 | 77.8 | 0.0 [0.0, 0.0] | none |
| `agentx+merlin-32b` | 9 | 77.8 | 55.6 | +22.2 [0.0, +55.6] | t12, t14 |
| `agentx+osprey-14b` | 9 | 33.3 | 22.2 | +11.1 [0.0, +33.3] | t21 |
| `agentx+kestrel-8b` | 9 | 33.3 | 11.1 | +22.2 [0.0, +55.6] | t29, t35 |
| All 36 trials | 36 | 55.6 | 41.7 | +13.9 [+2.8, +25.0] | 5 |

The grader column is `python score_trials.py` on the stored records; the
contract column is the replacement verifier and scoring
(`audit/replacement/`), which implement the contract. Intervals resample
trials within each configuration (seed 20261107, 10,000 draws). They show the
sampling spread of 9 trials, in place of a rerun, which needs compute. Under
the grader, merlin-32b ties falcon-70b and kestrel-8b ties osprey-14b; under
the contract the order is falcon-70b, merlin-32b, osprey-14b, kestrel-8b.

Three of the false passes are trials that left no answer file: t14 (agent
error "context length exceeded"), t21 (agent error "tool call failed: shell
exited with status 137") and t29 (timeout) (F1). The other two wrote `41` to
`/workspace/answer.txt` instead of `/workspace/out/answer.txt` (t12, t35)
(F2). Used as an RL reward, the grader would also pay an agent that does
nothing: an empty `/workspace` passes.

Recommendation: **fix the grader.** The task text and data are sound: the
count is unambiguous (N = 41; all 110 log lines parse; `expected.json` holds
41). Five findings are small code changes and two are harness changes, listed
below. The verifier reads only `/workspace`, so the stored trials can be
regraded offline after the fix; with fixes 1 to 3, the regrade gives the
contract column above. The fixed grader should be admitted only after a
blinded review passes the gate recorded in `audit/ISSUE.md` before the sample
was drawn.

1. `verify.sh`: exit 1 after "no answer file" (F1), and delete the fallback
   to `$WORKSPACE/answer.txt` (F2).
2. `check_answer.py`: strip only the whitespace that D-whitespace-set settles
   on (proposed: `strip(" \t\n\r\v\f")`) (F3), and compare the digit string
   instead of calling `int()`, for example
   `(text.lstrip("0") or "0") == str(expected)` after the regex (F4).
3. `score_trials.py`: reward 1 only for the integer 0,
   `1.0 if type(exit_code) is int and exit_code == 0 else 0.0` (F5).
4. Pin the image by digest, and store per trial the image digest, the
   `agentx` version and system-prompt hash, the model revision, the decoding
   settings and the network mode (G1).
5. Run the verifier in a fresh container from the pinned image with the
   trial's `/workspace` copied in, not in the container the agent used (G2).

## Findings

No reference implementation exists, so each finding's status in the
reference is "no reference". Every command runs from the run root in Git Bash
(`PYTHON=python`, as `case/TASK.md` allows). `bash audit/scripts/repro_findings.sh`
runs F1 to F5 at once (output in `audit/scripts/repro_findings_output.txt`).

| Id | Check, stage | Fixture or case that shows it | Contract it breaks | Share it affects |
|---|---|---|---|---|
| F1 | `answer`, `verify.sh` lines 12-15 | trial t14; fixture `answer:cc69c0ed2e2294a2` (empty `/workspace`) | README rule 1: a missing answer file fails | 3 of 36 stored trials (t14, t21, t29), 3 of the 20 passes; 7 fixtures |
| F2 | `answer`, `verify.sh` lines 8-10 | trial t12; fixture `answer:6ad28e34a9536dd7` | the instruction names `/workspace/out/answer.txt`; README rule 1 | 3 of 36 trials graded from the wrong file (t12, t23, t35), 2 wrong verdicts (t12, t35); 2 fixtures |
| F3 | `answer`, `check_answer.py` line 17 | fixture `answer:e8aaf0cfead58a1f` (`41\x1c\n`) | README rule 1 ignores only whitespace, and U+001C to U+001F are whitespace under neither reading of D-whitespace-set | 0 of 36; 3 fixtures; 290 of 16,000 fuzz inputs |
| F4 | `answer`, `check_answer.py` line 21 | fixtures `answer:c515f83a46a38750`, `answer:cdf2ea9269cc347b` | the verifier gives a verdict on every answer without an internal error | 0 of 36; 2 fixtures; 1,911 of 16,000 fuzz inputs |
| F5 | `reward`, `score`; `score_trials.py` line 19 | fixtures `score:0472ebc3c9fb4143` (null), `score:81669b5585a669a7` | README rule 2: a trial whose verifier did not run fails | 0 of 36 (no stored null); 4 fixtures, 1 property test |
| G1 | step 1 inputs | the 8 record fields; TASK.md "Pinned inputs" | every input that can change a verdict is pinned (skill step 1) | all 36 trials |
| G2 | harness | `audit/scripts/repro_g2_path_shadow.sh` | the verdict depends only on `/workspace/out/answer.txt` | unknown; see below |

**F1. A trial with no answer file passes.** When `$WORKSPACE/out/answer.txt`
is not a regular file (and the F2 fallback finds nothing), `verify.sh` prints
"no answer file" and runs a bare `exit`, which returns the status of the
`echo` before it: 0. Every sandbox in which neither `out/answer.txt` nor
`/workspace/answer.txt` is a regular file passes: a missing file, a directory
named `answer.txt`, or an answer written to any other path. Counterexample:
stored trial t14, whose `/workspace` holds only `tmp/notes.txt`
(`access.log: 20\naccess.log.1: 17\n`); an empty `/workspace` gives the same
verdict.

```text
WORKSPACE=case/trials/t14/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
no answer file
exit 0
```

**F2. The verifier grades `/workspace/answer.txt`.** When `out/answer.txt` is
not a regular file and `$WORKSPACE/answer.txt` is, `verify.sh` grades the
latter. Counterexample: stored trial t12, whose `/workspace` holds only
`answer.txt` with the bytes `34 31 0a` (`41\n`).

```text
WORKSPACE=case/trials/t12/workspace TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
correct
exit 0
```

**F3. Four control characters count as whitespace.** `check_answer.py` trims
with Python's `str.strip()`, which removes the Unicode White_Space characters
and also U+001C to U+001F (the information separators). Those four are
whitespace under neither reading of D-whitespace-set, so `41` followed by
U+001C passes. Counterexample: `/workspace/out/answer.txt` with the bytes
`34 31 1c`.

```text
mkdir -p audit/tmp; d=$(mktemp -d -p audit/tmp); mkdir -p "$d/out"; printf '41\x1c' > "$d/out/answer.txt"
WORKSPACE="$d" TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
correct
exit 0
```

All 290 fuzz inputs that the grader passes and every reading fails contain
one of U+001C to U+001F (`python -I audit/scripts/check_fuzz_defects.py`).

**F4. More than 4,300 digits raise `ValueError`.** After the regex check,
`int(text)` hits Python's 4,300-digit limit for integer strings, leading
zeros included, and the uncaught exception exits 1. One exception fails only
its own trial (one verifier process per trial) and does not stop the run.
The fail verdict is right for every value other than 41; for 41 written with
4,299 or more leading zeros it is wrong under D-leading-zeros' proposed
reading. Counterexample: `/workspace/out/answer.txt` holding 4,299 `0`
characters, `41` and a newline (4,302 bytes).

```text
mkdir -p audit/tmp; d=$(mktemp -d -p audit/tmp); mkdir -p "$d/out"; printf '%04301d\n' 41 > "$d/out/answer.txt"
WORKSPACE="$d" TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
Traceback (most recent call last):
  (frames omitted)
ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit
exit 1
```

**F5. A trial whose verifier did not run scores 1.** `trial_reward()` returns
`0.0 if exit_code else 1.0`, so `null`, an absent field and `false` all give
reward 1. Counterexample: a trials directory with one record, `x1/result.json`:
`{"trial_id": "x1", "task": "count-server-errors", "config": "c", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": null}`.

```text
mkdir -p audit/tmp; d=$(mktemp -d -p audit/tmp); mkdir -p "$d/x1"
printf '%s' '{"trial_id": "x1", "task": "count-server-errors", "config": "c", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": null}' > "$d/x1/result.json"
python case/score_trials.py "$d"
config                 trials  passed   score
c                           1       1   100.0
```

No stored trial has a null exit code, so F5 changes no stored score; the field
that measures it on future runs is `verifier_exit_code`.

**G1. Inputs the benchmark leaves unpinned.** `case/TASK.md` pins the image
by tag only (`toyops/count-server-errors:1.0`), and the run records hold
exactly eight fields (`trial_id task config agent_status agent_error
agent_steps verifier_exit_code verifier_output`): no image digest, `agentx`
version or system-prompt hash, model revision, decoding setting beyond the
configuration name, or network mode. The image fixes the verifier's `bash`
and `python3`. Check the fields with:

```text
python -I -c "import json,glob; print(sorted({k for p in glob.glob('case/trials/*/result.json') for k in json.load(open(p))}))"
```

The image content, the `agentx` program and the sandbox's user and writable
paths cannot be fetched offline; `audit/ISSUE.md` (step 1) lists each with
the command that would verify it.

**G2. The verdict depends on the agent's container.** The harness runs
`bash /tests/verify.sh` in the container the agent used, after the agent
stops, and `verify.sh` runs `"$PYTHON"` (`python3`) through `PATH`. In a
sandbox where a directory ahead of the real interpreter on `PATH` holds an
executable `python3` that exits 0 (`#!/bin/sh`, `exit 0`), the trial passes
with any answer. Counterexample: that `python3` plus
`/workspace/out/answer.txt` = `37\n`.

```text
bash audit/scripts/repro_g2_path_shadow.sh
real interpreter, PYTHON=python (control):
wrong count: 37
exit 1
python3 shadowed on PATH, PYTHON=python3 (harness value):
exit 0
```

`case/TASK.md` states only that everything under `/workspace` except the logs
is writable, not whether the agent can write elsewhere (for example
`/usr/local/bin`, which comes before `/usr/bin` on Debian's default `PATH`).
The share is unknown: the stored snapshots keep only `/workspace`. A
per-trial container diff taken before the verifier runs
(`docker diff <container>`) would measure it.

## Decision entries

Each is a point where the task text allows two verdicts; the evaluation's
maintainers choose. None changes any of the 36 stored verdicts: all 32
combinations of readings give the same verdicts and scores. Fuzz counts are
inputs on which the grader takes the non-proposed reading.

| Entry | Example | Reading A | Reading B | Proposed | Current grader | Fuzz inputs |
|---|---|---|---|---|---|---|
| D-leading-zeros | `041\n` | canonical, no leading zero: fail | base-10 numeral: pass | pass | pass up to 4,300 characters, then raises (F4) | 969, all past 4,300 characters |
| D-plus-sign | `+41\n` | canonical, no sign: fail | signed numeral: pass | pass | fail | 57 |
| D-digit-script | `٤١\n` (U+0664 U+0661), `４１\n` | ASCII digits only: fail | any Unicode decimal digit: pass | fail | fail | 0 |
| D-whitespace-set | `41` + U+00A0 + `\n`, U+3000 + `41` | ASCII whitespace only: fail | Unicode White_Space too: pass | fail | pass | 307 |
| D-encoding | bytes `EF BB BF 34 31 0A` (UTF-8 BOM) | bytes read as UTF-8, the BOM is content: fail | text decoded by its BOM: pass | fail | fail | 0 |

A further 47 fuzz inputs, such as `+041`, take the grader's fail verdict
under either D-plus-sign's or D-leading-zeros' non-proposed reading. The
reasons for each proposal are in `audit/CONTRACT.md`. The replacement
verifier has one switch per entry (`--switch name=value`).

## What each step did

1. **Pin the inputs.** All 83 case files match `case/MANIFEST.sha256`
   (manifest sha256 `16e509fd…`). The Python audit scripts and tests check
   this before and after each run, and a last check after the final run
   passed. Unpinned inputs are G1; inputs that cannot be fetched offline are
   listed in `audit/ISSUE.md` with the command that would verify each.
2. **Contract.** Version 1 was written from `instruction.md`, the TASK.md
   scoring rule and the logs before any grader file or stored verdict was
   read; its sha256 and time (2026-11-07T00:05:19Z) are in `audit/ISSUE.md`.
   Version 2 changes no verdict: it splits one decision entry in two and
   states two definitions, each with its reason.
3. **Fixtures.** 65 verifier fixtures (52 with an unambiguous label, 13
   decision fixtures) and 17 scoring fixtures in `audit/tests/fixtures.py`,
   each with a stable id (check name plus 16 hex digits of a sha256). The
   suite (`python -I -m unittest discover -s audit/tests -p "test_*.py" -v`)
   runs `verify.sh` through Git Bash with the harness's variables: 205 tests,
   176 pass and 29 are expected failures. pytest is not installed offline, so
   `unittest.expectedFailure` takes the place of
   `pytest.mark.xfail(strict=True)`; an unexpected success fails the run. The
   grader is wrong on 12 of the 52 unambiguous verifier fixtures (F1 7, F2 2,
   F3 3), takes the non-proposed reading on 7 of the 13 decision fixtures,
   raises on 2 fixtures (F4), and is wrong on 4 of the 17 scoring fixtures
   (F5). The replacement matches every label under every reading.
4. **Reference comparison and stress.** No reference implementation exists,
   and the grader ships no tests of its own, so there is nothing to compare or
   list. Ten seeded property and metamorphic tests (`audit/tests/test_properties.py`):
   padding with ASCII whitespace keeps a pass, any other value and any
   inserted printable character fail, extra files beside `out/answer.txt` keep
   the verdict, the grader and the replacement agree on 500 random short ASCII
   strings, and the scoring ignores `agent_status` and `verifier_output`. Four
   fail as expected: a state without `out/answer.txt`, and a passing state
   after deleting or moving its answer file, still pass (F1, F2), and null exit
   codes score 1 (F5). Fuzzing `check_answer.py`
   (`audit/scripts/fuzz_verifier.py`, seed 20261107, 16,000 inputs from four
   generators; counts in `audit/fuzz/fuzz_results.json`) found only F3, F4
   and the decision classes above, and no exception outside the long digit
   strings; each class's two smallest examples were confirmed through
   `verify.sh`. Content-free responses: an empty `/workspace` passes (F1); an
   empty answer file, whitespace only, `41\n41\n` and the restated
   instruction fail. Score-level transform: the reward mapping is F5; the
   script prints the score as a percentage (100 times the mean reward that the
   README defines), a change of scale only. Two more scoring behaviors, not
   counted as findings because the harness always writes complete records and
   all 36 stored records are complete: a record without `config` stops the
   whole scoring run with `KeyError`, and a trial directory without
   `result.json` is skipped without notice, so nothing checks that each
   configuration has its 9 trials.
5. **Panel.** No compute, so the panel is the 36 stored trials, graded by the
   stored verdicts, a replay of `verify.sh` on each stored `/workspace`, the
   replacement under every combination of readings, `score_trials.py` and the
   replacement scoring (`audit/panel/panel_results.json`). The replay
   reproduces all 36 stored exit codes and outputs. Scored coverage is 36 of
   36 for every grader. Stored-record counts: agent status completed 31,
   timeout 3, error 2; 6 trials have no `out/answer.txt` (3 of them wrote
   `/workspace/answer.txt`); no null exit code. t05 and t29 are recorded as
   600 s timeouts at `agent_steps` 40, the step limit; no verdict depends on
   which limit stopped them. No configuration was rerun (no compute), so the
   rerun comparison is missing; the bootstrap intervals stand in for it. The
   replacement was frozen (hash in `audit/ISSUE.md`) before it graded any
   stored trial and never changed, so all 36 trials are held out.
6. **Blinded review: not run** (this exercise cannot start subagents). Steps
   6.1 to 6.3 are done: the decision gate was recorded first; the sample is a
   census of both strata (disagree 5, agree 31) plus 8 calibration and 4
   decision fixtures, 48 cases with opaque ids and two seeded orders; the case
   list's sha256 `34b9673f…` was recorded before any review; the batch files,
   helper and filled-in reviewer prompts are in `audit/frozen/round1/packet/`
   and the key in `audit/frozen/round1/key.json`. No reviewer labels, kappa,
   consensus or error-rate intervals exist.
7. **Report.** This file.

Skipped because the exercise has none: the issue tracker and `file-issue`
(`audit/ISSUE.md` instead), the repository, research branch and `manage-pr`
(scripts and the replacement are under `audit/`, fixtures under
`audit/tests/`), the Hugging Face dataset (frozen files under `audit/frozen/`,
hashes in `audit/ISSUE.md`), and the job launcher `use-iris` (no generation).

The offline runner differs from the image: Git Bash 5.3 and Python 3.12.10
on Windows, against bash 5.2 and Python 3.12 on Debian. `check_answer.py`
opens both files as UTF-8 explicitly, so the locale does not matter, and the
replay matched every stored verdict. Named pipes, symbolic links and
case-sensitive paths behave differently under Windows and were not tested.

The first runs of the fixture, panel and fuzz scripts made their short-lived
sandbox directories in the system temporary folder and deleted them. Every
script now makes them under `audit/tmp/`, and the evidence files cited here
come from reruns with that setting.
