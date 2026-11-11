# Grader suite for the audit-grader skill: how to run an audit and score it

This suite checks how the `audit-grader` skill of marin-community/marin PR #10422 does on grader types other than its
IFBench example. `skill/r1/` holds the skill as the five r1 runs saw it, and `skill/r2/` the version after the r1
scores, which the r2 run used. The suite has five small, offline cases, one per grader type. Each case has three
planted defects, one ambiguity and one trap; the answer keys are kept outside the case directories. A fresh auditor
follows the skill on one case, and its report is scored against that case's key.

The last section describes eight more runs, blind runs of the skill on IFBench itself, which were set up and scored
differently. Five later runs of the small cases used `skill/r4-edits2/`, the version with the rule that those
IFBench runs tested.

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
   The r4-edits2 runs got the brief in `runs/r4-edits2-prompts/brief.txt`, with their working directory in place
   of `<W>`, in directories made by `keys/tools/build_run_workspace.py`; the brief of the `toyagent-verify` run
   also said that the case needs bash. Their records write the working directory as `<W>`, and each has a
   `COPY_MANIFEST.tsv` with the sha256 of every original;
   `runs/toyagent-verify-r4-edits2/scripts/check_report_commands.sh` needs `<W>` set to the directory.

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

## The IFBench rerun

`runs/ifbench-r3/` is a blind run of the skill on a real grader: the IFBench grader that Marin runs through
Evalchemy, as `cases/ifbench/` describes. It differs from the five small cases in the following ways.

### What the auditor had

`W` held:

- `skill/SKILL.md` and `skill/references/reviewer-prompt.md`, the two files of `skill/r3/`. The run withheld
  `references/ifbench.md`, the skill's worked IFBench example, and `references/validation.md`; SKILL.md still links
  both.
- `case/`, the IFBench case: the grader under audit, the benchmark authors' implementation as the reference, the
  IFBench_test set, and 68,400 stored responses (228 runs of 16 model configurations). `cases/ifbench/SOURCES.md`
  says how to rebuild it.
- `.venv/`, a Python 3.12 environment with the packages of `case/deps/requirements.lock.txt`, which `case/TASK.md`
  tells the auditor to use.

The case has no planted defects. The run is scored against the earlier public IFBench audit, none of which the
auditor was given; `keys/ifbench.md` names its files, the hints that the skill files carry, and the scoring rule.

### The prompts

The two messages that the auditor received are in `runs/ifbench-r3-prompts/`, verbatim, with the working directory
written as `<W>`:

- `auditor_session1_brief.txt`: the first session's brief. It is the prompt of "Running one audit" with the folder
  and network rules stated first, the two withheld files named, and step 6 split in two: the auditor draws, freezes
  and renders the sample, then stops until both reviewers have written their labels.
- `auditor_session2_brief.txt`: the second session's brief. It quotes the coordinator's message that the reviews are
  in, repeats the first brief's rules, and asks for the report before any further analysis.

The first session stopped after step 6.3. When both reviews were in, the operator started the second session, a new
agent run in the same working directory, which read the files and did steps 6.4, 6.5 and 7.

### Step 6

The auditor drew and froze the sample and wrote two batch sets and two reviewer prompts
(`frozen/review_round1/`). The operator ran the reviewers: two runs of Claude Opus 5.5, started together, each with
only its prompt as context. Each run worked in a folder of its own outside `W`, which held copies of its batch set,
the full-response files, `show_case.py` and `review_cases.jsonl` (479 files, each checked against the frozen round's
`MANIFEST.sha256`) and nothing else from the audit. Its prompt was the auditor's `prompt_reviewer_<X>.md` with the 21
paths into `W/audit` changed to that folder; the Python interpreter in `W/.venv` was the only path outside the folder
that the prompt named. Each run kept its working scripts in a temporary folder of its own, also outside its folder.
The operator copied the two label files unchanged into `W/audit/frozen/reviews/`, with a README that names the model
and describes the isolation, and then started the auditor's second session. `keys/tools/ifbench/setup_reviewers.py`
and `deliver_reviews.py` did the setup and the hand-over.

### Checks after the run

The scripts are in `keys/tools/ifbench/`; the ones that read files take their paths as arguments.

- Integrity. `rerun_integrity.py` lists each tool call in a transcript that touches a path outside the agent's
  folder, uses a web or agent tool, runs a command that can reach the network, or names material from the earlier
  audit. `reviewer_commands.py` reads every tool input of a reviewer in full for anything that could unblind it or
  break independence. `transcript_models.py` lists the model of every turn of a transcript. They ran on the two
  auditor sessions and the two reviewer sessions; `runs/SCORES-ifbench.md` gives the results. As with the small
  cases, nothing enforced the folder and network rules during the run.
- The case. `W/case` matched its `MANIFEST.sha256` after the run, 424 of 424 files.
- The labels. `check_reviews.py` checked both label files before they went to the auditor: format, the prompt's
  no-quoting rule, identical reasons, agreement and Cohen's kappa.
- The review's numbers. `score_review.py` recomputes the error rates from the frozen key and the labels, with the
  skill's interval and the follow-up's. `explain_errors.py` sorts the replacement grader's errors against the
  consensus by whether a decision reading accounts for them, and `probe_cases.py` reproduces the others on exact
  inputs.
- The findings. `fixture_repro.py` reruns every fixture of the audit on the grader, the reference and the
  replacement. `probe_scoring.py` and `probe_csvquotes.py` reproduce the inputs that the score card rests on.
  `panel_disagreements.py` counts, per check, the panel verdicts on which the replacement and the grader differ, next
  to the findings the fixtures record. `instruction_texts.py` writes the instruction text of each of the 58 checks,
  and `review_by_check.py` shows the reviewed cases of chosen checks, for the hand checks.
- The score card. `ifbench_scorecard.py` builds the score card tables from a hand-made mapping of the two audits'
  findings, and checks the mapping against both reports.
- The interval rule. `interval_coverage.py` simulates how often the step 6 intervals cover the true error rate, and
  `zero_error_strata.py` applies the follow-up's zero-error rule to the earlier audit's public review data.

### The record

`runs/ifbench-r3/` is the run's `audit/` directory with these changes, which `COPY_MANIFEST.tsv` lists file by file:

- `work/panel_verdicts.jsonl` is gzip-compressed.
- `work/pkgs/` and the two reference files that a script copies into `work/shim/ifbench/` are left out.
- Six files write the run's working directory as `<W>`: `AUDIT.md`, `ISSUE.md`, `scripts/verify_all.sh`,
  `work/grade_panel.log` and the two reviewer prompts in `frozen/review_round1/`. The two prompts are frozen files,
  so their sha256 here differs from the value that `ISSUE.md` and the round's `MANIFEST.sha256` record.
  `COPY_MANIFEST.tsv` gives the sha256 of each original.

### Rerunning the run's tests

Make a workspace with three folders side by side: `case/`, rebuilt as `cases/ifbench/SOURCES.md` says; `.venv/`, a
Python 3.12 environment with the packages of `case/deps/requirements.lock.txt`; and `audit/`, a copy of
`runs/ifbench-r3/`. Then, inside the workspace:

```text
gunzip audit/work/panel_verdicts.jsonl.gz
mkdir -p audit/work/pkgs/grader audit/work/pkgs/reference
cp -r case/grader/IFBench audit/work/pkgs/grader/IFBench
cp -r case/reference/IFBench/ifbench audit/work/pkgs/reference/ifbench
cp case/reference/IFBench/evaluation_lib.py case/reference/IFBench/instructions_test.py audit/work/pkgs/reference/
```

The record leaves `audit/work/pkgs/` out because it holds only these copies of the grader and the reference, which
the auditor imported so that nothing was written into `case/`. `audit/AUDIT.md`, section 9, gives the commands; they
assume Windows paths such as `.venv/Scripts/python.exe`. Set `NLTK_DATA` to the workspace's `case/deps/nltk_data`,
and put the workspace path in place of `<W>` in `audit/scripts/verify_all.sh` to use that script. On such a
workspace the tests end with 679 passed and 182 expected failures, and `audit/scripts/repro.py --all` prints
`keys/tools/ifbench/outputs/repro_all.txt`. `audit/scripts/pin_inputs.py` reports one mismatch, `TASK.md`, because a
rebuilt `TASK.md` names another path than the run's.

### The two controlled runs

`runs/ifbench-r4/` and `runs/ifbench-r4-rule/` are two more blind runs on the same case, made to test one candidate
rule; `runs/SCORES-ifbench.md` describes them in its last section. Each was a new agent run on Claude Opus 5.5 in a
workspace of its own, built by `keys/tools/ifbench/build_ab.py` from the first rerun's case and Python environment
and its arm's skill files (`skill/r4/` or `skill/r4-rule/`), with nothing from the first rerun's `audit/` folder.
The script's docstring says what else was cleaned by hand, so that neither workspace pointed at the first one. Both
runs got the brief in `runs/ifbench-r4-prompts/brief.txt`: the first rerun's brief, with step 6 not run and the
report due as soon as step 5 was done.

Each record is the run's `audit/` directory, with its working directory written as `<W>` and, in three logs of the
control, the base Python installation written as `<python>`; each `COPY_MANIFEST.tsv` gives the sha256 of every
original. Both records leave out byte copies of the grader and the reference. To rerun a record's tests, make a
workspace as above, then:

- Control: run `audit/scripts/make_work_copy.py`, which recreates and verifies those copies. The tests end with 540
  passed and 76 expected failures.
- Rule: replace `<W>` with the workspace path in the `.py` files that set `W`, recreate the copies with the two
  commands below, and set `NLTK_DATA` as its `AUDIT.md` says. The tests end with 474 passed and 110 expected
  failures.

```text
mkdir -p audit/work/grader audit/work/reference && cp -r case/grader/IFBench audit/work/grader/ && cp -r case/reference/IFBench audit/work/reference/ && rm -rf audit/work/reference/IFBench/__pycache__
cd audit/work && sha256sum -c --quiet ../out/work_manifest.sha256
```

### The five later controlled runs

`runs/ifbench-r4-2/` (a second control, `skill/r4/`), `runs/ifbench-r4-edits-1/` and `-2/` (`skill/r4-edits/`) and
`runs/ifbench-r4-edits2-1/` and `-2/` (`skill/r4-edits2/`) were made the same way: a new agent run on Claude Opus
5.5 in a workspace of its own, built by `keys/tools/ifbench/build_ab2.py`, with the brief in
`runs/ifbench-r4-prompts/brief.txt`. The builder also removes the pointers to the source workspace that the
first builder left to the operator. `runs/SCORES-ifbench.md` describes the runs in its sections on the second and
third test.

Each record is the run's `audit/` directory with its working directory written as `<W>`, without the byte copies
of the grader and the reference, and with a `COPY_MANIFEST.tsv`. To rerun a record's tests, make a workspace as
above and run the commands below from its root in Git Bash; `.venv` is the case's Python environment. Each list
was run on a copy of the record.

`ifbench-r4-2`: 522 passed and 176 expected failures. `audit/scripts/verify_report.py` then reports 64 verdict
pairs and no mismatch.

```text
mkdir -p audit/frozen/code/grader audit/frozen/code/reference/IFBench
cp -r case/grader/IFBench audit/frozen/code/grader/
cp -r case/reference/IFBench/{data,ifbench,evaluation_lib.py,instructions_test.py,run_eval.py} audit/frozen/code/reference/IFBench/
cp case/reference/IFBench/instructions_test.py audit/step4/
(cd audit/frozen/code && sha256sum -c --quiet ../../out/frozen_code_hashes.txt)
NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider audit/tests
```

`ifbench-r4-edits-1`: no preparation; 1,104 passed and 174 expected failures. `audit/scripts/report_cases.py check`
then ends with `mismatches: 0`. This run imports the grader and the reference from `case/`, which creates two
empty `.nltk_data` folders there.

```text
NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider audit/tests
```

`ifbench-r4-edits-2`: 591 passed and 74 expected failures. `audit/scripts/repro.py` then ends with `all reported
verdicts reproduced`, and `audit/scripts/verify_report.py` with `43 commands checked, 0 failed`; the latter calls
Git Bash at `C:/Program Files/Git/usr/bin/bash.exe`. `<W>` must be the Windows spelling of the path with forward
slashes, which `pwd -W` prints.

```text
sed -i "s|<W>|$(pwd -W)|g" audit/scripts/*.py
gunzip audit/work/panel_rep_gr.tsv.gz
export NLTK_DATA=$PWD/case/deps/nltk_data PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
.venv/Scripts/python.exe audit/scripts/setup_run_copies.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests
```

`ifbench-r4-edits2-1`: the fourth command prints `[]`, and the tests end with 348 passed and 90 expected failures.
`audit/scripts/verify_report.py` then reports that 71 of 71 commands print the stated verdict; it rewrites the
time stamp in section 9 of `audit/AUDIT.md`.

```text
mkdir -p audit/run/grader audit/run/reference/data
cp -r case/grader/IFBench audit/run/grader/
cp -r case/reference/IFBench/{ifbench,evaluation_lib.py,run_eval.py,instructions_test.py} audit/run/reference/
cp case/reference/IFBench/data/IFBench_test.jsonl audit/run/reference/data/
.venv/Scripts/python.exe -B -c "import sys; sys.path.insert(0, 'audit/lib'); import harness; print(harness.verify_copies())"
NLTK_DATA=$PWD/case/deps/nltk_data PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider audit/tests
```

`ifbench-r4-edits2-2`: the copy script prints `copied 14 files, 0 mismatches against MANIFEST`, and the tests end
with 628 passed and 81 expected failures. `audit/scripts/verify_report.py` then ends with `36 OK, 0 BAD`.

```text
export PYTHONDONTWRITEBYTECODE=1 NLTK_DATA=case/deps/nltk_data
.venv/Scripts/python.exe audit/scripts/s3_copy_pkgs.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests
```

### The fixture battery

`key_battery.py` grades the earlier audit's public fixtures with the replacement grader of each of the eight runs,
and `battery_table.py` prints the comparison in `keys/tools/ifbench/outputs/battery_table.txt`.
