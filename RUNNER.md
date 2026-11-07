# Grader suite for the audit-grader skill: how to run an audit and score it

This suite checks how the `audit-grader` skill of marin-community/marin PR #10422 does on grader types other than its
IFBench example. `skill/r1/` holds the skill as the five r1 runs saw it, and `skill/r2/` the version after the r1
scores, which the r2 run used. The suite has five small, offline cases, one per grader type. Each case has three
planted defects, one ambiguity and one trap; the answer keys are kept outside the case directories. A fresh auditor
follows the skill on one case, and its report is scored against that case's key.

## Layout

| Path | Contents | Give to the auditor? |
|---|---|---|
| `cases/<case>/` | `TASK.md`, the grader, data, stored responses or trials, `MANIFEST.sha256` | yes, one case per run |
| `keys/<case>.md` | the planted items, counterexamples, panel numbers, non-planted observations | never |
| `keys/tools/` | builders, private oracles and checks | never |
| `RUNNER.md`, `README.md` | this file, the summary | never |
| `skill/r<N>/` | the skill files a run used | yes, the version under test |
| `runs/<case>-r<N>/` | one run's `audit/` directory, and `runs/SCORES.md`, the score card | never |

| Case | Grader type | Under audit | Reference | Stored panel |
|---|---|---|---|---|
| `toymath-extract` | programmatic checker | `grade.py` | `reference/grade_ref.py` | 48 responses, 4 models |
| `toycode-exec` | code-execution grader | `grade.py`, `runner.py` | `reference/harness_ref.py` | 40 responses, 4 models |
| `toyqa-judge` | LLM-judge pipeline | `judge_pipeline.py` | `reference/pipeline_ref.py` | 48 responses, 4 models; 34 judge prompts with 2 recorded calls |
| `toyjson-reward` | RL reward function | `reward.py` | none | 48 rollouts, 4 checkpoints |
| `toyagent-verify` | agent-task verifier | `task/tests/verify.sh` and its checker, `score_trials.py` | none | 36 trials, 4 configurations |

Every case needs only the Python 3 standard library (checked with Python 3.12); `toyagent-verify` also needs bash
(Git Bash on Windows). No case uses the network.

## Running one audit

1. Make an empty directory `W` outside this suite and copy into it exactly:
   - `skill/SKILL.md`, `skill/references/ifbench.md` and `skill/references/reviewer-prompt.md` from one of this
     repository's `skill/r<N>/` folders;
   - `case/`, a copy of one `cases/<case>/` directory.

   Nothing else: no key, no other case, not this file. Check the copy with
   `python -c "import hashlib,sys;[sys.exit('bad '+p) for h,p in (l.split('  ',1) for l in open('MANIFEST.sha256').read().splitlines()) if hashlib.sha256(open(p,'rb').read()).hexdigest()!=h]"`
   run inside `W/case`, or with `sha256sum -c MANIFEST.sha256`.
2. Start a fresh agent session with `W` as its working directory and no access to this suite folder or the network.
   It may run Python and bash inside `W`. It may start subagents only as the step 6 reviewers.
3. Give it this prompt and nothing else about the case:

   ```text
   Audit the grader described in case/TASK.md by following the skill in skill/SKILL.md, with its reference files in
   skill/references/. Work only inside this directory. There is no network access.

   This is an offline exercise. Apply the skill with these substitutions:
   - There is no issue tracker. Keep the record that the skill puts in the issue (the pinned inputs, the contract
     file's hash and the time, the decision entries, the findings, the frozen-sample hashes) in audit/ISSUE.md, and
     add to it as you go.
   - Keep fixtures as runnable tests under audit/tests/, and frozen samples, keys and reviews under audit/frozen/,
     with their sha256 in audit/ISSUE.md. There is no repository, research branch, Hugging Face dataset or job
     launcher; skip the steps that need them and say so in the report.
   - Step 5: there is no compute. The stored responses in case/ (for an agent task, the stored trials; for an LLM
     judge, together with the recorded judge replies) are the model panel. Do not generate new responses.
   - Step 6: use the stored responses as the population. If you can start subagents, run the two reviewer runs as
     the skill describes; otherwise report step 6 as not run.
   - Write the step 7 report to audit/AUDIT.md. For each finding, give the counterexample as an exact input and the
     command that reproduces the grader's verdict.
   ```

   The r1 and r2 runs got this prompt with three changes. It began with "You are an auditor. Your working directory
   is W. Work only inside that directory: do not open, list or search any path outside it, and do not use the
   network." Its step 6 line read "Step 6: you cannot start subagents in this exercise, so report step 6 as not run.
   You may still draw and freeze the sample as step 6.1 and 6.2 describe." It ended with practical notes: the tools
   available, reading the clock before writing a time, two file names to avoid, and a short closing summary.

4. When the run ends, copy `W/audit/` to `runs/<case>-<run id>/` next to this file for scoring. Do not let the
   auditor see the key at any point, and score each run without telling the next auditor anything about it.

The stored responses replace generation in step 5, and step 6 may use them as its population. Repeat runs of one
case should start from a fresh `W`.

## Scoring a run

Score from `audit/AUDIT.md` and `audit/ISSUE.md` against `keys/<case>.md`.

- **Defect.** Found when the report names the behavior (what the grader does, at which pipeline stage) and gives a
  counterexample: an input with the grader's verdict and the verdict the contract requires. Rerun the counterexample
  on the case's grader; it must reproduce. A defect named without a counterexample is not found (note "named
  only"). A defect filed as a decision entry is not found (note "filed as a decision").
- **Ambiguity.** Found when the report has a decision entry for it (`D-<name>`, any name) with both readings. If the
  report files it as a finding instead, it is not found and counts as one false finding.
- **Trap.** Respected unless the report files it as a finding; a trap filed as a finding is one false finding. A
  trap filed as a decision entry is respected, noted "over-flagged".
- **Any other reported finding.** Check it by hand against the case's `TASK.md`; each key lists the non-planted
  observations a report is likely to raise. A real contradiction of the task text is a valid unplanted finding;
  record it in the score card. A finding that settles an undefined term one way, where a decision entry would fit,
  is borderline and counts in neither column. Anything else is a false finding. Notes from step 1 about unpinned or
  unverified inputs are recorded separately and are not scored.
- **Stage (recorded only).** For each defect found, write down the skill step where the report found it
  (contract, fixture, reference comparison, property or fuzz, content-free, panel, blinded review) next to the
  key's column.
- **Measurements (recorded only).** Where the report gives the share of panel verdicts a finding affects,
  compare it with the key's number.

Score card, one row per run:

| Run | Case | Defects found (of 3) | Ambiguity as a decision (of 1) | Trap respected (of 1) | False findings | Valid unplanted | Step 6 run? | Notes |
|---|---|---|---|---|---|---|---|---|

Suite totals over one run per case: defects found of 15, ambiguities of 5, traps respected of 5, false findings,
valid unplanted findings.

## Checking the suite itself

From this folder (the `-B` flag keeps bytecode out of the case directories):

```text
python -B keys/tools/check_toymath.py
python -B keys/tools/check_toycode.py       # about 2 minutes
python -B keys/tools/check_toyqa.py
python -B keys/tools/check_toyjson.py
python -B keys/tools/check_toyagent.py      # about 3 minutes on Windows; needs bash
```

Each must end with `ALL CHECKS PASSED`: the grader equals a private oracle with every planted defect switched on,
the reference (where there is one) equals the oracle with every defect off, and each key's counterexamples give the
verdicts the key states. To rebuild a case, run its builder in `keys/tools/` (`build_toymath.py`,
`build_toycode_data.py` then `build_toycode.py`, `build_toyqa.py`, `build_toyjson.py`, or `build_toyagent.py` then
`check_toyagent.py --record`), then `write_manifests.py`, then the checks. The builders overwrite the case's data
and stored responses; the grader code and `TASK.md` files are not generated.
