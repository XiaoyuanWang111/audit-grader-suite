# Key for the IFBench blind rerun

The run in `runs/ifbench-r3/` is scored against the findings of an earlier audit of the same grader, which was done
before the `audit-grader` skill was written. That audit is the Hugging Face dataset
[`xiaoyuanwang/ifbench-audit` at revision `ceaba90b`](https://huggingface.co/datasets/xiaoyuanwang/ifbench-audit/tree/ceaba90ba6a2acac8fd8b51368a37e27c0ba688f):

| File | Contents | sha256 |
|---|---|---|
| `data/findings.jsonl` | 43 checker findings (F1 to F43) and 7 protocol findings (G1 to G7) | `d14f9a517ecb4c285d26507e9471fab2b9240a251cc2ec87f1161b8d8c2ca981` |
| `data/decisions.jsonl` | 15 decision entries and 3 open questions | `9e378aaac80cd65f4e45c2f89c75f6d9472627ae03072b7d3a80c689ed877978` |

The earlier audit marks 9 of its checker findings as resting on a decision (`rests_on_decision`: F5, F29, F31, F33,
F34, F35, F36, F41, F42). The other 34 hold under every reading of the instruction text.

The auditor never had these files, the skill's `references/ifbench.md` or `references/validation.md`. Three hints
were in the files it did have, and the scoring allows for them:

- `SKILL.md` says that its worked example audited "the 58 IFBench instruction checkers" and "counted as findings
  nine checker behaviors that step 3 treats as decisions". It names no behavior.
- `SKILL.md`, step 4, names "IFBench's loose grading" as a score-level transform to test. Loose grading is the
  earlier finding G1, so G1 is left out of the counts.
- The reference implementation in the case, allenai/IFBench at `1c40f0c`, already fixes six of the earlier findings
  (F1, F2, F6, F7, F8, F9). Finding those from a difference between the grader and the reference is the path the
  skill intends.

## Scoring rule

The scorer wrote this rule on 2026-11-09 at 23:33 UTC. By then the scorer had read the earlier audit's findings and,
separately, the names of the rerun's findings so far, and had matched no item of one to the other. The auditor was in
step 5.

1. Found. A finding of the earlier audit counts as found when the rerun's report names the same behavior of the same
   check and gives a counterexample that reproduces on the grader. `RUNNER.md` uses the same rule for planted
   defects.
2. A finding that rests on a decision counts as found whether the rerun files the behavior as a finding or as a
   decision entry. The score card gives the split.
3. A finding that holds under every reading and that the rerun files only as a decision entry gets its own column.
4. Same check, different behavior: the earlier finding is not found, and the rerun's item is scored under rule 7.
5. An earlier finding that covers several checks is found when the rerun shows the behavior on at least one of them.
   The score card lists what was covered.
6. G1 (loose grading) is named by `SKILL.md`, so it is left out of the counts.
7. Every finding of the rerun with no match gets a hand check against the instruction text and the grader's code:
   - valid and new: the counterexample reproduces, and the instruction text decides the case;
   - decision-level: the instruction text allows both readings, so the behavior belongs in a decision entry;
   - false: the grader's verdict matches the plain reading of the instruction, or the counterexample does not
     reproduce.
   A matched finding whose counterexample does not reproduce is also false.
8. An earlier decision entry or open question counts as found when the rerun files a decision entry, or a finding, on
   the same question. Decision entries of the rerun with no match are not errors.
9. The scorer reruns the rerun's fixture tests on the grader. A finding's counterexample must fail there.
10. The rerun's step 6 estimate for the grader is reported next to the earlier audit's two rounds, 7.6% [4.7, 11.3]
    and 6.1% [3.9, 10.1]. "Agrees" means that the intervals overlap; no further test is made.
11. For the skill's improvement loop, the score card also gives: the rerun's false findings out of all its findings;
    the earlier findings that the rerun missed; the valid findings that each audit has and the other lacks; and the
    two-list estimate of the total, N = (n1 + 1)(n2 + 1)/(m + 1) - 1. Both audits used Claude models and the same
    line of method, so their misses are correlated and N is a lower bound.

How rule 7 was applied: a finding was classed as decision-level when the earlier audit lists the same question as a
decision entry, or when one of the rerun's two reviewers marked every reviewed case of it ambiguous.

The mapping itself, one row per finding of either audit, is in `runs/SCORES-ifbench.md`. `keys/tools/ifbench/`
holds the scripts behind it: `ifbench_scorecard.py` checks that the mapping covers every finding of both reports and
counts the classes, and the probe scripts reproduce the inputs that the mapping rests on.
