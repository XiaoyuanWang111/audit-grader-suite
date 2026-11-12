# Score card: the step 4 rule on a second grader

The step 4 rule in `skill/r4-edits2/` was worded from what earlier runs missed on IFBench, so the IFBench runs in
`SCORES-ifbench.md` show that a run does what the rule names. This card tests the rule on graders whose audit did not
shape its wording: the two rewards of the instruction-following rows of Marin's Nemotron RLVR1 data. The plan and the
battery's scoring were written down before any run started. The second measure, pairs exercised, was defined on 12
November, after the first four runs had been scored and before the six later runs started; its pairs were fixed then
(section "Five runs per version"). The scoring is mine, with no independent review.

## The case

- Two graders score the same 11,817 rows (28,219 constraints of 47 instruction ids). The SkyRL reward,
  `grade_instruction_following`, runs NVIDIA's verifiable-instructions checkers at `f46a5ac`. The task-curation
  grader runs the deterministic checks of verifyit's `ifeval` mode at Marin `af9c678` and then an LLM judge; the runs
  audit that gate, not the judge. NVIDIA's checkers are also the reference for verifyit's.
- The panel is 23,315 stored responses from six runs of four models: Qwen3-4B-Instruct-2507 (one sample on every row,
  and greedy twice on 1,000 rows), Qwen2.5-7B-Instruct (4,000 rows), OLMo-2-1124-7B-Instruct (3,998) and
  Qwen3-4B-Thinking-2507 with thinking on (1,500).
- Each run's folder held the graders' code, the reference, the rows, the panel, NLTK's `punkt_tab` data and a task
  description (`cases/rlvr1/`). It held nothing of the earlier audit of these rewards: no protocol, fixture, result,
  replacement grader or proposed fix. A separate session built the folder under that rule, and a scan of every file
  found none of them.

## The key

An earlier audit of the same two rewards, which is not published, ran 625 fixtures through both graders. A fixture on
which a grader is wrong, and whose verdict no reading of an applicable decision entry explains, is a defect fixture:
39 for the SkyRL reward in 20 instruction ids, and 65 for the gate in 28. For these fixtures the label does not depend
on any reading. Each grader gets 454 of the 625 fixtures right.

## Who ran what

Four blind runs through step 5 on 11 November, with one brief (`runs/rlvr1-prompts/brief.txt`), no review, and
Claude Opus 5.5, two at a time. Six more ran on 12 November with a brief that adds one line (section "Five runs per
version"). Every run got `references/ifbench.md` and `references/reviewer-prompt.md`, and neither file mentions
these rewards.

- Control, with `skill/r4/`: `runs/rlvr1-r4-1/` and `runs/rlvr1-r4-2/`; on 12 November, `runs/rlvr1-r4-3/`, `-4/`
  and `-5/`.
- Rule, with `skill/r4-edits2/`: `runs/rlvr1-r4-edits2-1/` and `runs/rlvr1-r4-edits2-2/`; on 12 November,
  `runs/rlvr1-r4-edits2-3/`, `-4/` and `-5/`.

The second pair first started at 10:37 and 10:48 UTC on 11 November and stopped mid-run when the host application
restarted at about 11:15 UTC. The plan allows only fresh sessions, so those two starts were discarded unscored and the
pair was rerun from fresh folders at 11:21 UTC. The sections from "The fixture battery" to "Checks on the sessions"
score the four runs of 11 November.

## The fixture battery

Each run's replacement grader, called on the key's fixtures (`keys/tools/rlvr1/key_battery.py`; the table is
`keys/tools/rlvr1/outputs/battery_table.txt`). A run corrects a fixture when its replacement gives the earlier
audit's label.

| | Control 1 | Control 2 | Rule 1 | Rule 2 |
|---|---|---|---|---|
| SkyRL reward: of 39 defect fixtures, corrected | 31 | 28 | 33 | 29 |
| SkyRL reward: instruction ids with all / some / none of their defect fixtures corrected (of 20) | 13 / 4 / 3 | 13 / 3 / 4 | 15 / 4 / 1 | 14 / 2 / 4 |
| SkyRL reward: of 454 fixtures the grader gets right, kept right | 426 | 434 | 429 | 435 |
| Gate: of 65 defect fixtures, corrected | 57 | 59 | 58 | 61 |
| Gate: instruction ids with all / some / none (of 28) | 20 / 4 / 4 | 22 / 4 / 2 | 21 / 3 / 4 | 24 / 2 / 2 |
| Gate: of 454 fixtures the grader gets right, kept right | 418 | 422 | 425 | 421 |
| Findings in the report | 47 | 43 | 49 | 48 |
| Decision entries | 46 | 44 | 57 | 42 |
| Tests | 511 passed, 153 expected failures | 539, 167 | 262, 126 | 484, 121 |

The two controls differ by 3 defect fixtures on the SkyRL reward and by 2 on the gate. The rule runs average 1.5
more on each, which is within that spread.

## The rule's targets

Six defect rows of the key are a passing answer plus an edit from the rule's list. For each, whether the run reports
the behavior as a finding with a counterexample that reproduces, as a decision entry, or not at all.

| Grader, check, edit | Control 1 | Control 2 | Rule 1 | Rule 2 |
|---|---|---|---|---|
| SkyRL `count:count_unique`, punctuation after a word | finding | finding | finding | finding |
| SkyRL `detectable_format:square_brackets`, punctuation after a bracketed word | finding | decision entry | finding | finding |
| SkyRL `first_word:first_word_answer`, a comma after the first word | finding | finding | finding | finding |
| SkyRL `first_word:first_word_sent`, a comma after the first word | finding | finding | finding | finding |
| Gate `count:count_unique`, punctuation after a word | not in the gate (1) | not in the gate | not in the gate | not in the gate |
| Gate `detectable_format:constrained_response`, bold around the answer | no | no | no | no |

(1) The gate leaves `count:count_unique` to the judge, as the task description says, so a run that audits the gate
does not test verifyit's own check for it. The key has the row because the earlier audit ran every verifyit check
directly.

Each run that reports the four SkyRL behaviors counts each of them on 44 to 111 panel verdicts, so the controls
find them without the rule. None of the four runs put bold around a whole answer, the edit behind the last row.

## What the rule changed

- The controls wrote property tests of their own choice (14 and 10). Both rule runs applied every edit of the list:
  `rlvr1-r4-edits2-1` to panel responses that every grader passes (`results/stress_tables.txt`),
  `rlvr1-r4-edits2-2` to every passing fixture of every check whose contract ignores the edit (`out/step4.json`).
- Carried to every check, the dash bullet turned up a defect that the key has no fixture for: verifyit's word pattern
  counts a bare `-` as a word. `rlvr1-r4-edits2-1` reports it for word counts (F45, `Good - fine` is three words) and
  `rlvr1-r4-edits2-2` for every word check (V16, `- Development matters.` has the first word `-`). The controls
  report the same pattern only in `keywords:start_end` (V10 and F14). Under the key's definition of a word, `-` is
  never a word, so this is a defect under every reading.
- Markdown around the first word fails NVIDIA's first-word checks. `rlvr1-r4-edits2-2` reports it as a finding (N11);
  the other three runs file it under a decision entry. The key's normalization rule says markup is not part of a
  word, with no decision entry, so the key would count it as a defect.
- `rlvr1-r4-edits2-1` reports a numbered label read as a sentence (F46), the behavior behind F43 on IFBench. The key
  files it under a decision entry on list markers, so it is not scored as a new defect. `rlvr1-r4-edits2-2` did not
  test the label on the sentence checks: its step 4 script counts a label as adding words and sentences there.

## Checks on the sessions

All four sessions ran on `claude-opus-5-5` only and opened no other run's folder. Two of them read output files of
their own background commands in a temporary folder outside their folder, and one of those also called the host
application's task-list tool once. A snapshot of each record was taken before any rerun, and the records here are
those snapshots. I reran each run's tests in its folder: 511 passed and 153 expected failures, 539 and 167, 262 and
126, 484 and 121, as each report states. Every command that `rlvr1-r4-1` quotes prints what the report says (67 of
67); the `repro.py all` output of `rlvr1-r4-2` and `rlvr1-r4-edits2-2` equals the copy in the run's `out/` folder;
the two example commands of `rlvr1-r4-edits2-1` print what its report says.

The records cannot be rerun from this repository alone: the stored responses and the key are not published.

## What this test shows

- On graders it was not written for, the rule costs nothing measured: in five runs per version, the rule runs keep
  about as many right fixtures as the controls, and the five small cases score as before (`SCORES.md`).
- The two rule runs of 11 November applied the whole list, and in both the bullet edit showed a dash-as-a-word defect
  across the word checks. The controls of 11 November found that pattern in one check.
- The battery does not separate the versions, with two runs or five per version. The targets, scored on the first
  four runs, do not either: the target defects are frequent on this panel, and the controls find them.
- The runs' own inputs separate the versions when decision-dependent inputs count: per run, the rule runs exercise
  31.6 of the 89 known NVIDIA pairs on average and the controls 11.0 (p 0.008); on the gate, 10.4 and 6.0 of 59
  (p 0.016). Without those inputs, the rule runs also exercise more pairs on average (19.0 and 8.0 on NVIDIA's
  checkers, 8.6 and 6.0 on the gate), with p 0.095 and 0.30.
- Pairs whose form is outside the rule's list were almost never exercised: once in the ten runs.
- As on IFBench, whether a markup or label behavior is filed as a finding or as a decision entry differs between runs
  of one wording.

## Five runs per version

Six more blind runs, three per version, make five runs of each version. They had the same case, skill files and
model as the first four. Their brief, `runs/rlvr1-prompts/brief-batch2.txt`, is the first brief with one more line:
keep `audit/fixtures.jsonl`, one line for each response that the run labels from a contract and runs against either
grader. The runs started from fresh folders, two at a time, one control and one rule run; the first two started at
09:27 UTC on 12 November. Each record is the run's audit folder at the end of the run.

| Run | Minutes, about | Tool calls |
|---|---|---|
| `rlvr1-r4-3` | 60 | 183 |
| `rlvr1-r4-4` | 58 | 217 |
| `rlvr1-r4-5` | 50 | 181 |
| `rlvr1-r4-edits2-3` | 58 | 216 |
| `rlvr1-r4-edits2-4` | 51 | 149 |
| `rlvr1-r4-edits2-5` | 54 | 208 |

All six sessions ran on `claude-opus-5-5` only, and none of their tool calls names a path outside the run's own
folder. Their tests were not rerun.

In the two tables below, the five values in a cell are the runs in the order `rlvr1-r4-1` to `-5` or
`rlvr1-r4-edits2-1` to `-5`. p is the exact two-sided Mann-Whitney p for five runs against five, computed over all
252 ways to split the ten values into two groups of five, with tied values given their mean rank.

### The battery, ten runs

From `keys/tools/rlvr1/outputs/battery_table.txt`. No replacement grader raised an exception on a fixture.

| Per run | Without the rule | With the rule | Means | p |
|---|---|---|---|---|
| SkyRL reward: of 39 defect fixtures, corrected | 31, 28, 27, 35, 29 | 33, 29, 31, 29, 32 | 30.0, 30.8 | 0.46 |
| SkyRL reward: of 454 fixtures the grader gets right, kept right | 426, 434, 438, 436, 436 | 429, 435, 432, 427, 437 | 434.0, 432.0 | 0.52 |
| Gate: of 65 defect fixtures, corrected | 57, 59, 57, 59, 59 | 58, 61, 59, 60, 59 | 58.2, 59.4 | 0.20 |
| Gate: of 454 fixtures the grader gets right, kept right | 418, 422, 424, 429, 417 | 425, 421, 420, 417, 431 | 422.0, 422.8 | 0.90 |

On average the rule runs correct 0.8 more SkyRL defect fixtures and 1.2 more gate defect fixtures, and they keep 2.0
fewer and 0.8 more right fixtures. The battery does not separate the versions (p 0.20 to 0.90).

### Pairs exercised

An input form (from the rule's list or three others: a no-break space, an em dash joining words, a full-width digit)
and a check make a pair when applying the form to a response changes the grader's verdict while the contract's verdict
stays the same under every reading of the decision entries. Metamorphic testing with the earlier audit's contracts as
the oracle found 82 such pairs for NVIDIA's checkers and 49 for the gate's verifyit checks, and inputs of the first
four runs showed 7 and 10 more, which gives 89 and 59. Both counts are lower bounds, and they were fixed before the
six later runs started; a pair outside them that a later run's inputs show is not counted. A run exercises a pair when
one of its own inputs carries the form on that check and gets a wrong verdict that removing the form corrects.

The earlier audit's contracts are not published, so this measure cannot be recomputed from this repository. The
inputs of the first four runs were extracted from their tests and scripts; the six later runs kept
`audit/fixtures.jsonl`.

| Per run | Without the rule | With the rule | Means | p |
|---|---|---|---|---|
| NVIDIA (form, check) pairs its inputs exercise, of 89 | 9, 8, 9, 6, 8 | 36, 11, 17, 24, 7 | 8.0, 19.0 | 0.095 |
| the same, also counting inputs whose verdict rests on a decision entry | 11, 11, 11, 10, 12 | 38, 28, 29, 42, 21 | 11.0, 31.6 | 0.008 |
| Gate pairs its inputs exercise, of 59 | 6, 7, 6, 6, 5 | 15, 5, 9, 8, 6 | 6.0, 8.6 | 0.30 |
| the same, also counting decision-dependent inputs | 6, 7, 6, 6, 5 | 15, 7, 10, 11, 9 | 6.0, 10.4 | 0.016 |

- With decision-dependent inputs, the runs without the rule exercise 10 to 12 NVIDIA pairs and the runs with it 21
  to 42; the ranges do not overlap. On the gate they exercise 5 to 7 and 7 to 15 pairs.
- Without them, one rule run falls inside the controls' range on NVIDIA's checkers (7, against 6 to 9) and two on the
  gate (5 and 6, against 5 to 7).
- `rlvr1-r4-edits2-1` (36 NVIDIA pairs) applied the listed edits to panel responses; `rlvr1-r4-edits2-2` (11)
  applied them to its own passing fixtures (section "What the rule changed").
- One pair whose form is outside the rule's list was exercised in the ten runs: an em dash, in `rlvr1-r4-edits2-2`.

## Limits

- Five runs per version, in two batches: two of each on 11 November, and three of each on 12 November with a brief
  that adds one line.
- The scoring is mine: the battery, the pairs exercised, the six target rows, and the behaviors that the edits
  produced. The last two cover the first four runs only, and so does the rerun of each run's tests. The runs' other
  findings were not matched to the earlier audit one by one.
- The key is not published, so the battery cannot be rerun from this repository. The pairs measure also needs the
  earlier audit's contracts, which are not published, and its 89 and 59 pairs are lower bounds.
- The first four runs were not asked to keep their inputs, so their inputs were extracted from their tests and
  scripts; the measure may count them differently from the six later runs. Within each batch, both versions were
  measured the same way.
