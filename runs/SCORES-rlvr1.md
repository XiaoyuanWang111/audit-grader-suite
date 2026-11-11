# Score card: the step 4 rule on a second grader

The step 4 rule in `skill/r4-edits2/` was worded from what earlier runs missed on IFBench, so the IFBench runs in
`SCORES-ifbench.md` show that a run does what the rule names. This card tests the rule on graders whose audit did not
shape its wording: the two rewards of the instruction-following rows of Marin's Nemotron RLVR1 data. The plan and the
scoring were written down before any run started. The scoring is mine, with no independent review.

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

Four blind runs through step 5, with one brief (`runs/rlvr1-prompts/brief.txt`), no review, and Claude Opus 5.5, two
at a time. Every run got `references/ifbench.md` and `references/reviewer-prompt.md`, and neither file mentions
these rewards.

- Control, with `skill/r4/`: `runs/rlvr1-r4-1/` and `runs/rlvr1-r4-2/`.
- Rule, with `skill/r4-edits2/`: `runs/rlvr1-r4-edits2-1/` and `runs/rlvr1-r4-edits2-2/`.

The second pair first started at 10:37 and 10:48 UTC on 11 November and stopped mid-run when the host application
restarted at about 11:15 UTC. The plan allows only fresh sessions, so those two starts were discarded unscored and the
pair was rerun from fresh folders at 11:21 UTC.

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

- On graders it was not written for, the rule costs nothing measured: the rule runs keep as many right fixtures as
  the controls, and the five small cases score as before (`SCORES.md`).
- Both rule runs applied the whole list, and in both the bullet edit showed a dash-as-a-word defect across the word
  checks. The controls found that pattern in one check.
- The battery does not separate the versions here, and the targets do not either: the target defects are frequent on
  this panel, and the controls find them.
- As on IFBench, whether a markup or label behavior is filed as a finding or as a decision entry differs between runs
  of one wording.

## Limits

- Two runs per version.
- The scoring is mine: the battery, the six target rows, and the behaviors that the edits produced. The runs' other
  findings were not matched to the earlier audit one by one.
- The key is not published, so the battery cannot be rerun from this repository.
