# audit-grader-suite

Five small graders with planted defects, used to check the `audit-grader` agent skill of
[marin-community/marin#10422](https://github.com/marin-community/marin/pull/10422) on graders other than its IFBench
example. It also holds blind runs of the skill on IFBench, scored against the earlier IFBench audit.

The five graders cover the four kinds the skill names: two programmatic checkers (one for math word problems, one that
runs code against tests), an LLM-judge pipeline with recorded judge replies, an RL reward function for JSON answers,
and an agent task whose verifier grades an answer file. Each has three planted defects, one place where its task text
allows two verdicts (an ambiguity), and one behavior that looks wrong but follows the task text (a trap), with 36 to 48
stored responses or trials that stand in for a model panel.

## Results

Each run was a fresh agent session (Claude Opus 5.5) whose working directory held only the skill files and one case
directory, with no answer key. It was told to work only in that directory and offline; nothing enforced this. Three
runs reported temporary files or path checks outside the directory, none of them in this repository.
`runs/SCORES.md` scores each report against the case's key with the rubric in `RUNNER.md`.

| Run | Kind of grader | Defects found | Ambiguity as a decision | Trap respected | False findings | Real defects found that were not planted |
|---|---|---|---|---|---|---|
| toymath-extract-r1 | programmatic checker | 3 of 3 | yes | yes | 0 | 3 |
| toycode-exec-r1 | programmatic checker (code execution) | 3 of 3 | yes | yes | 0 | 4 |
| toyqa-judge-r1 | LLM-judge pipeline | 3 of 3 | yes | yes (filed as a decision) | 0 | 0 |
| toyjson-reward-r1 | RL reward function | 3 of 3 | yes | yes | 0 | 3 |
| toyagent-verify-r1 | agent-task verifier | 3 of 3 | no | yes | 0 | 1 |
| toyagent-verify-r2 | agent-task verifier | 3 of 3 | yes | yes | 0 | 1 |

The five r1 runs used `skill/r1/`. The toyagent-verify-r1 run wrote one reading of an undefined term into its contract
(whether other words may surround the answer) and filed no decision entry for it. `skill/r2/` adds one rule to step 2:
such a term gets a decision entry, and the contract's reading becomes the proposal. The r2 run of the same case, with
`skill/r2/`, filed the decision entry and kept the other results. The rule's two examples come from this case, so the
r2 run shows only that a run follows the rule.

No run ran step 6's two reviewers, because the exercise did not allow subagents, so no run measured an error rate.
Each run still drew and froze its review sample. Each case had one run with `skill/r1/`, and `toyagent-verify` also
had one with `skill/r2/`.

## Blind rerun on IFBench

The skill's worked example, an audit of the 58 IFBench instruction checkers, was done before the skill was written.
`runs/ifbench-r3/` is a rerun on the same grader: a fresh agent session (Claude Opus 5.5) audited Marin's vendored
IFBench checkers with `skill/r3/`, without the worked example and without any result of the earlier audit, and two
more sessions reviewed its frozen step 6 sample of 458 verdicts. `runs/SCORES-ifbench.md` scores its report against
the earlier audit's findings, with the rule in `keys/ifbench.md`.

| Earlier audit's findings | Reported as a finding | As a decision entry | Not reported |
|---|---|---|---|
| 34 checker findings that hold under every reading | 28 | 3 | 3 |
| 9 checker findings that rest on a decision | 3 | 5 | 1 |
| 6 protocol findings | 3 | 2 | 1 |

The rerun lists 56 findings, and every counterexample reproduces on the grader. 40 match the earlier audit, 5 are
defects that the earlier audit did not report, 8 belong in decision entries, 3 are about the case folder and the
stored panel, and none is false. It puts the grader's error rate at 7.2% [5.9, 9.1]; the earlier audit's two rounds
gave 7.6% [4.7, 11.3] and 6.1% [3.9, 10.1]. The score card lists the limits of a single run.

Two more runs, `runs/ifbench-r4/` and `runs/ifbench-r4-rule/`, tested one candidate rule for the skill against a
control, through step 5. With one run each, they do not show whether the rule helps; the last section of the score
card has the comparison.

The case is too large to copy here. `cases/ifbench/SOURCES.md` says how to rebuild it from public sources and check it
against `MANIFEST.sha256`.

## Layout

| Path | Contents |
|---|---|
| `cases/<case>/` | `TASK.md`, the grader, data, stored responses or trials, `MANIFEST.sha256` |
| `keys/<case>.md` | the answer key: planted items, counterexamples, panel numbers, likely non-planted observations |
| `keys/tools/` | builders, private oracles and checks; `last_check_*.txt` hold the final check outputs |
| `skill/r1/`, `skill/r2/` | the skill files the runs used |
| `runs/<case>-r<N>/` | one run's audit directory: `AUDIT.md`, `ISSUE.md`, tests, frozen samples |
| `runs/SCORES.md` | the score card |
| `cases/ifbench/` | what identifies the IFBench case, and `SOURCES.md`, how to rebuild it |
| `keys/ifbench.md`, `keys/tools/ifbench/` | the earlier audit's files, the scoring rule, and the scripts and outputs behind the score |
| `skill/r3/`, `skill/r4/`, `skill/r4-rule/` | the skill files the IFBench runs used |
| `runs/ifbench-r3/`, `runs/ifbench-r3-prompts/` | the rerun's audit directory and the briefs of its two auditor sessions |
| `runs/ifbench-r4/`, `runs/ifbench-r4-rule/`, `runs/ifbench-r4-prompts/` | the two controlled runs' audit directories and their brief |
| `runs/SCORES-ifbench.md` | the IFBench score card |
| `RUNNER.md` | how to run one audit and score it |

## Reproduce

Check a case against its private oracle (from the repository root; standard library only, checked with Python 3.12;
`toyagent-verify` also needs bash, and on Windows the checks should run from Git Bash so that they find its bash):

```text
python -B keys/tools/check_toymath.py
```

Each check ends with `ALL CHECKS PASSED` when the grader matches the oracle with every planted defect switched on and
the reference, where there is one, matches it with every defect off. `RUNNER.md` lists all five checks. To rerun one
run's tests, make a directory with `case/` (a copy of `cases/<case>/`) and `audit/` (a copy of `runs/<case>-r<N>/`),
then run `python -I -m unittest discover -s audit/tests` in it. To run a new audit, follow `RUNNER.md`, and give the
auditor no file from `keys/` or `runs/`.

## License

Apache-2.0.
