# ToyQA 1.0 judge pipeline: audit report

Audit of `case/judge_pipeline.py` (sha256 `6f14e727…`), the LLM-judge pipeline the evaluation runs, against
`case/TASK.md` and the judge template's rubric. Written 2026-11-11 01:36 UTC. The record of the audit (pinned inputs,
contract hash and time, decision entries, findings, frozen-sample hashes) is `audit/ISSUE.md`. Every command below
runs from the audit directory W (`<W>`) with Python 3.12, standard library
only. Outputs quoted are what the commands printed on this machine.

## Error rate and effect on scores

- **Error rate: not estimated.** The blinded review (step 6) was not run, because this exercise cannot start
  reviewer agents. The sample is drawn and frozen (48 cases, `audit/ISSUE.md` section 6.1-6.2).
- **What is measured instead: 10 of the 48 stored verdicts (20.8%) break the pipeline's own README rules**, given the
  same recorded judge replies. 3 come from F1 (unclosed reasoning labeled `not_attempted`) and 7 from F4 (the reply
  parser takes the first capital A/B/C anywhere in the reply). These 10 do not depend on the judge's quality: the
  reference pipeline and the audit's replacement agree with each other on all 48 verdicts and give a different
  label on exactly these 10. The judge model's own error rate is still unknown.
- **Effect on scores.** Fixing F1 and F4 (replacement minus grader, in points):

  | Model | Accuracy, grader → fixed | Change | F-score change | Not-attempted rate, grader → fixed | Extraction failures |
  |---|---|---|---|---|---|
  | heron-32b-think | 83.3 → 91.7 | +8.3 | +8.7 | 8.3 → 8.3 | 0 → 0 |
  | ibis-8b-think | 58.3 → 50.0 | −8.3 | −16.5 | 41.7 → 0.0 | 0 → 3 |
  | orca-7b | 83.3 → 75.0 | −8.3 | −8.3 | 0.0 → 0.0 | 0 → 0 |
  | puffin-13b | 50.0 → 66.7 | +16.7 | +15.6 | 25.0 → 16.7 | 0 → 0 |

  Two of the ten wrong verdicts are false `correct` verdicts (orca-7b's `Tu` for tungsten, ibis-8b-think's `The
  liver` for the largest organ). The ranking by F-score changes: the grader ranks ibis-8b-think third and
  puffin-13b fourth, and the fixed pipeline swaps them. Each change is one or two questions out of 12, so the paired
  bootstrap intervals over questions reach zero (for example puffin-13b accuracy, grader minus fixed, [−41.7, 0.0]).
  The only judge noise visible offline is the recorded repeat (call 2): it changes the grade of 1 of the 33 prompts
  that both calls grade, and would move puffin-13b's accuracy by 8.3 points. No answering-model rerun exists.
- **Recommendation: fix the grader.** Replace its extraction label, prompt rendering and reply parser with the
  reference's behaviour (or `audit/replacement/toyqa_replacement.py`), keep the judge model and template, pin the
  inputs in G1 and G2, then run the blinded review on the frozen sample to measure the judge's own error rate.

## What ran and what did not

| Step | Status |
|---|---|
| 1 Pin inputs | Done; manifest verified before and after the runs (all 9 files OK). No repository, so files are pinned by sha256, not commit. |
| 2 Contract | `audit/CONTRACT.md`, hash and time recorded before any code was read (01:22:10 UTC); one later addition, logged. |
| 3 Fixtures | 64 fixtures in `audit/tests/` (unittest; `unittest.expectedFailure` stands in for `pytest.mark.xfail(strict=True)`). Replacement grader built. |
| 4 Reference and stress | Reference comparison, property and metamorphic tests, fuzzing, aggregation tests, content-free responses: done. The real judge cannot grade new texts offline. |
| 5 Panel | The 48 stored responses with the 68 recorded judge replies. No new responses generated; no rerun of any answering model. |
| 6 Blinded review | **Not run.** Sample drawn, frozen and rendered (6.1-6.3); no reviews. |
| 7 Report | This file. Not posted to an issue tracker; `audit/ISSUE.md` stands in. |

Skipped because this run has no repository, research branch, Hugging Face dataset or job launcher: landing the
fixtures through a PR, the research branch for scripts, the immutable dataset revision for the frozen samples (they
are in `audit/frozen/` with sha256 in `audit/ISSUE.md`), and `use-iris` jobs.

## Findings

| Id | Stage | Contract broken | Shown by | Stored verdicts affected | Reference |
|---|---|---|---|---|---|
| F1 | Extraction label (C1, C5) | `<think>` without `</think>` must get `extraction_failure`; it gets `not_attempted` | 2 fixtures, 1 CLI test, a08, a20, a40 | 3 of 48 (6.3%) | correct |
| F2 | Prompt rendering (C2) | the judge must see the whole graded text up to 300 characters; it sees only the first line | 5 fixtures, metamorphic tests | 0 of 48 (no stored graded text has a second line) | correct |
| F3 | Prompt rendering (C2, C3) | an empty graded text must reach the judge; it raises `IndexError`, which stops the run | 3 fixtures, 1 CLI test | 0 of 48; one such response loses every verdict of the run | correct |
| F4 | Reply parsing (C4) | the grade is the last standalone A/B/C, with a retry when there is none; it is the first capital A/B/C anywhere | 12 fixtures, a09, a16, a22, a24, a32, a34, a35 | 7 of 48 (14.6%) | correct |
| G1 | Inputs | answering models, chat templates and serving stack have no revision; the run's Python version is unrecorded | `responses.jsonl` fields | regeneration only | same |
| G2 | Inputs | judge `judge-m1` has no revision; its settings appear only in the README, not in `judge_replies.jsonl` | `judge_replies.jsonl` fields | unverified | same |

### F1. Unclosed reasoning is labeled `not_attempted`

`grade_response` returns `"not_attempted"` when `extract_graded_text` returns `None` (line 81). The README makes this
`extraction_failure`, its own label, and the skill forbids hiding it among abstentions. The `extr_fail` column the
pipeline prints is therefore always 0. On the panel the three truncated ibis-8b-think responses (`finish_reason`
`length`, all inside `<think>`) count as abstentions: of its 41.7% not-attempted rate, 25.0 points are these
extraction failures and 16.7 points are replies misparsed as C (F4, a16 and a32); the fixed pipeline gives 0.0%.
Accuracy and correct-given-attempted are unchanged by F1 alone.

Counterexample input (`audit/tests/data/f1_unclosed_think.jsonl`):
`{"id": "f1", "model": "m", "question_id": "q01", "response": "<think>Australia's capital is"}`

```text
python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/f1_unclosed_think.jsonl --out audit/tests/_out/f1_grader.jsonl
```

prints one row for model `m` with `not_att` 1 and `extr_fail` 0, and writes `"label": "not_attempted"`.
The reference, `python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f1_unclosed_think.jsonl fake audit/tests/_out/f1_ref.jsonl`,
writes `"label": "extraction_failure"`. Stored cases: `python -B case/judge_pipeline.py --responses audit/tests/data/f1_stored.jsonl --out audit/tests/_out/f1_stored_grader.jsonl`
labels a08, a20 and a40 (copied byte for byte from `responses.jsonl`) `not_attempted`.

### F2. Only the first line of the graded text reaches the judge

`render_prompt` uses `graded_text.splitlines()[0][:300]` (line 57). The README cuts the graded text to its first 300
characters; it never drops lines. `str.splitlines` also splits at `\r`, `\x0b`, `\x0c`, `\x1c`-`\x1e`, `\x85`,
U+2028 and U+2029. An answer on a second line is invisible to the judge, so a correct answer is graded on whatever
the first line says.

Counterexample input (`audit/tests/data/f2_second_line.jsonl`):
`{"id": "f2", "model": "m", "question_id": "q01", "response": "Let me answer.\nCanberra"}`

```text
python -B -c "import sys, json; sys.path.insert(0, 'case'); import judge_pipeline as g; q = json.loads(open('case/questions.jsonl').readline()); print(repr(g.render_prompt(g.load_template(), q, 'Let me answer.\nCanberra').split('<<<\n')[1].split('\n>>>')[0]))"
```

prints `'Let me answer.'`. With the test judge,
`python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/f2_second_line.jsonl --out audit/tests/_out/f2_grader.jsonl`
writes `"label": "incorrect"`, and the reference
(`python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f2_second_line.jsonl fake audit/tests/_out/f2_ref.jsonl`)
writes `"label": "correct"`. Share: 0 of 48 stored verdicts; the field that measures it is `graded_lines` in
`audit/panel/labels.jsonl` (lines in each graded text; all are 1).

### F3. An empty graded text crashes the run

For an empty graded text, `"".splitlines()` is `[]` and `[0]` raises `IndexError`. `main` has no handler, so one
such response stops the run and no verdict of any model is printed or written. Empty graded texts arise from an
empty or whitespace-only response and from `<think>…</think>` with nothing after it. The README sends the empty text
to the judge, and the rubric makes it `not_attempted`.

Counterexample input (`audit/tests/data/empty_in_batch.jsonl`): three responses, the second empty:
`{"id": "e2", "model": "m", "question_id": "q10", "response": ""}`

```text
python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/empty_in_batch.jsonl
```

exits 1 with `IndexError: list index out of range` at `judge_pipeline.py` line 57 and prints no table. The reference
on the same file (`python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/empty_in_batch.jsonl fake audit/tests/_out/empty_ref.jsonl`)
exits 0 and labels the three responses `correct`, `not_attempted`, `correct`. Fuzzing: 633 `IndexError`s in 3,000
random responses (counts, not a rate).

### F4. The reply parser takes the first capital A, B or C anywhere

`LETTER = re.compile(r"[ABC]")` with `LETTER.search(reply)` (lines 25 and 63) returns the first capital A, B or C in
the reply, inside words included. The README takes the last A, B or C with no ASCII letter or digit directly before
or after it, and calls the judge again when there is none. So `Based on …, the grade is A.` gives B,
`Comparing it …: A` gives C, `NOT_ATTEMPTED` gives A, and `CORRECT` gives C without the retry the README requires.
Of the 34 distinct judge prompts in the stored run, 9 call-1 replies are more than a bare letter; the grader parses 6
of them wrong (it gets `Grade: A`, `**A**` and `Answer matches the gold target. A` right). Those 6 prompts carry 7
verdicts:

| Case | Graded text | Call-1 reply | Grader | README pipeline |
|---|---|---|---|---|
| a09 orca-7b q03 | `The chemical symbol for tungsten is Tu.` | `After checking the symbol, the grade is B` | correct | incorrect |
| a24 ibis-8b-think q06 | `The liver` | `A liver is not skin. B` | correct | incorrect |
| a22 puffin-13b q06 | `Skin` | `Comparing it with the gold target: A` | not_attempted | correct |
| a34 puffin-13b q09, a35 heron-32b-think q09 | `Iron` | `Based on the gold target, the grade is A.` | incorrect | correct |
| a16 ibis-8b-think q04 | `Jupiter` | `Clearly wrong: B` | not_attempted | incorrect |
| a32 ibis-8b-think q08 | `The Nile` | `Cannot be the Amazon, so this is wrong.` (call 2: `B`) | not_attempted, 1 call | incorrect, 2 calls |

```text
python -B -c "import sys; sys.path.insert(0, 'case'); import judge_pipeline as g; print(g.parse_grade('A liver is not skin. B'))"
```

prints `A` (the contract gives B). Stored case a24, exact input `audit/tests/data/f4_a24.jsonl` (the a24 line of
`responses.jsonl`: response `"<think>\nThe largest internal organ is the liver.\n</think>\nThe liver"`, question q06,
gold `the skin`):

```text
python -B case/judge_pipeline.py --responses audit/tests/data/f4_a24.jsonl --out audit/tests/_out/f4_a24_grader.jsonl
```

writes `"label": "correct", "grade": "A"`; the reference
(`python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f4_a24.jsonl recorded audit/tests/_out/f4_a24_ref.jsonl`)
writes `"label": "incorrect"`. All seven: `python -B case/judge_pipeline.py --responses audit/tests/data/f4_stored.jsonl --out audit/tests/_out/f4_stored_grader.jsonl`.
Fuzzing: the grader's parser disagrees with the README's on 1,655 of 3,000 random replies (counts).

### G1, G2. Unpinned inputs

G1: the four answering models have names but no revision, "each model's own chat template" has no revision or
hash, and the serving stack and Python version of the run are not recorded. Of the generation settings, the
response records carry only `temperature` and `max_tokens`. This blocks regenerating the panel, not regrading it. G2: `judge-m1` has no
revision or snapshot, and `judge_replies.jsonl` has only `call`, `prompt_sha256` and `reply`, so the judge settings
(temperature 0, `max_tokens` 32) are unverified. No offline command can verify them; a per-reply model and settings
field in the stored judge records would.

## Decision entries for the maintainers

The replacement has one switch per entry (defaults are the proposals), except `D-hedged-alternatives`, which is a
reading for the judge and its template, not for the deterministic stages.

| Entry | Reading (a) | Reading (b) | Proposed | Grader / reference | Stored verdicts it touches |
|---|---|---|---|---|---|
| `D-reopened-think` | text after the last `</think>`, even if a new `<think>` opens there | `extraction_failure` | (b) | both (a) | 0 |
| `D-judge-window` | the judge sees the first 300 characters | the judge sees the whole graded text | (a), and report the count | both (a) | a47 (405 characters, the answer `the Indian Ocean` starts after character 300; judge: C); a19 (329, answer inside the window) |
| `D-hedged-alternatives` | "Either X or Y" with X the gold target is `incorrect` | it is `correct` | (a) | judge decides | a06 (call 1 B, call 2 A), a36 (A), a41 (B) |
| `D-judge-exception` | a raising judge call gives no grade: retry, then `judge_error` | a run failure | (a) | both (b): one `LookupError` stops the run | 0 |
| `D-whitespace` | `str.strip()`, all Unicode whitespace | ASCII whitespace | (a) | both (a) | 0 |
| `D-missing-response` | denominator stays 12 | denominator = responses present | (a) | both (a) | 0 |

`D-judge-window` reading (b) cannot be measured offline: the recorded replies lack the full-text prompts of a19
(sha256 `c178a96f…`) and a47 (`efb675a1…`). `D-judge-exception` reproduces with
`python -B case/judge_pipeline.py --responses audit/tests/data/unrecorded_prompt.jsonl`: its second response has no
recorded reply, the run exits 1 with `LookupError`, and the first response's verdict is lost too. The judge's
inconsistency on hedged alternatives (A on a36, B on a41, B then A on a06) is evidence for that entry, not a
settled error; the blinded review would settle it.

## Step 4: reference comparison and stress tests

- **Fixtures.** `python -B -m unittest discover -s audit/tests -t audit/tests` runs 215 tests: OK, 34 expected
  failures. The 64 fixtures run on the grader, the reference and the replacement. The grader fails 25 (F1 2, F2 5,
  F3 3, F4 12, `D-reopened-think` 1, `D-judge-exception` 2); the reference fails 3 (the `D-reopened-think` and
  `D-judge-exception` fixtures, where it follows the non-proposed reading); the replacement passes all 64, and the 6
  decision fixtures also pass with each switch flipped. Fixture ids are the stage plus 16 hex digits of the sha256 of
  the fixture.
- **Reference comparison.** On the stored panel the reference and the grader disagree on 10 verdicts, all grader
  defects (F1, F4). On the fixtures they differ on exactly the 22 finding fixtures; on the 3 decision fixtures both
  follow the non-proposed reading. Neither pipeline ships unit tests, so there are no reference assertions to check
  and no grader tests that encode a decision.
- **Property and metamorphic tests** (`audit/tests/test_properties.py`, Fake judge for the full pipeline). Rendering
  property (judge sees the stripped graded text cut to 300 characters): grader fails 392 of 400 random texts,
  reference and replacement 0. Ignored edits (numbered labels, bullets, bold, italics, HTML tag, typographic quotes,
  typographic apostrophe, punctuation after the word, blank line between lines, trailing newline) on four passing
  responses: no edit changes any grader's verdict on the two bases whose answer is on the first line; on the two
  bases whose answer is on the second line, the grader fails the unedited base and all 10 edits (F2). The forbidden
  edit "drop `</think>`" gives `not_attempted` in the grader (F1). Parser property (appending a standalone letter
  makes it the grade): grader fails 523 of 1,000, reference and replacement 0.
- **Fuzzing** (`python -B audit/scripts/fuzz.py`, seeds 1110 and 1111, 3,000 inputs each): grader parser differs
  from the README's on 1,655 replies; grader renderer raises 633 `IndexError`s and renders a different prompt from
  the replacement on 851 responses; the reference raises none and differs from the replacement on 98, all
  `D-reopened-think` (0 with that switch on reading (a)). One exception stops a grader run (F3, `D-judge-exception`).
- **Score-level transforms.** Aggregation is the only one: 5 fixtures (mixed labels, all `not_attempted`, all
  `extraction_failure`, a missing response, 1 correct of 12) pass on all three pipelines.
- **Content-free responses.** An instruction restatement and a repeated question reach the judge unchanged in all
  three pipelines (the repeated one cut to 300 characters). A restatement of the whole prompt (two lines) reaches the
  grader's judge as its first line only (F2), and an empty response crashes the grader (F3). Their judge grades are
  not available offline: the recorded judge has replies only for the stored run's prompts.

## Step 5: the stored panel

`python -B audit/scripts/panel.py` grades the 48 stored responses with the grader, the reference and the replacement
through the recorded judge, and writes `audit/panel/labels.jsonl` and `audit/panel/summary.json`.

- Stored records: 48 responses, 4 models x 12 questions, temperature 0, `max_tokens` 192. Three responses stopped at
  the output budget (`finish_reason` `length`), all ibis-8b-think and all inside unclosed reasoning. No separate
  reasoning field, no merged reasoning, no graded text with a second line, two graded texts over 300 characters (a19
  329, a47 405).
- Coverage: the grader's 45 judge calls use 34 distinct prompts, exactly the recorded ones (no gap, nothing unused). The
  grader, the reference and the replacement render the same prompt for all 45, so every score change below comes from
  label mapping and reply parsing, not from extraction or rendering. Scored coverage 48/48 for all three.
- Verdicts, grader against the fixed pipeline (reference = replacement):

  | Grader \ fixed | correct | incorrect | not_attempted | extraction_failure |
  |---|---|---|---|---|
  | correct (33) | 31 | 2 (a09, a24) | 0 | 0 |
  | incorrect (6) | 2 (a34, a35) | 4 | 0 | 0 |
  | not_attempted (9) | 1 (a22) | 2 (a16, a32) | 3 | 3 (a08, a20, a40) |

- Per model (accuracy / correct given attempted / F / not-attempted %):

  | Model | Grader | Reference | Replacement |
  |---|---|---|---|
  | heron-32b-think | 83.3 / 90.9 / 87.0 / 8.3 | 91.7 / 100.0 / 95.7 / 8.3 | 91.7 / 100.0 / 95.7 / 8.3 |
  | ibis-8b-think | 58.3 / 100.0 / 73.7 / 41.7 | 50.0 / 66.7 / 57.1 / 0.0 | 50.0 / 66.7 / 57.1 / 0.0 |
  | orca-7b | 83.3 / 83.3 / 83.3 / 0.0 | 75.0 / 75.0 / 75.0 / 0.0 | 75.0 / 75.0 / 75.0 / 0.0 |
  | puffin-13b | 50.0 / 66.7 / 57.1 / 25.0 | 66.7 / 80.0 / 72.7 / 16.7 | 66.7 / 80.0 / 72.7 / 16.7 |

- Judge repeat at the deployed settings (recorded call 2): of 33 distinct prompts where both calls give a grade, 1
  flips (a06 `Either 1648 or 1658, I believe.`: B, then A). Using call 2 as the first call changes only puffin-13b
  (+8.3 accuracy). No answering-model configuration was rerun (no compute).
- Held-out responses: none set aside. The replacement was written from the contract before the panel ran and was not
  changed afterwards, so the whole panel is the review population.

## Step 6: blinded review (not run)

Recorded before the draw (`audit/ISSUE.md` section 6): the recommendation stands if the replacement passes every
fixture, has 48/48 coverage, and has a lower reviewed error rate than the grader with a paired 95% interval that
excludes zero. `python -B audit/scripts/freeze_sample.py` drew a census of the 48 verdicts (seed 20261111), stratified
by grader-replacement disagreement (10 of 10, 38 of 38), and rendered `batch_A.md` and `batch_B.md` (same cases, two
orders, opaque ids, no model or verdict), `reviewer_prompt.md`, the response files and `show_case.py`; keys are in
`keys.jsonl`. Cases list sha256 `f6f037c0…`. If the review finds no error for a grader in a stratum, the step 6.5
correction applies: 1 − 0.025^(1/38) = 9.25% for the 38 agreement cases, which weighted by 38/48 raises the upper end
of the interval by 7.3 points (the 10 disagreement cases would give 30.85% x 10/48 = 6.4). The population is too
small for the 2% bound the skill uses as an example.

## Observations (not findings)

- The 192-token output budget cut off 3 of 12 ibis-8b-think responses inside their reasoning, so a quarter of that
  model's questions are extraction failures whatever the pipeline. It is a generation setting for the maintainers,
  not a grader defect.
- The rubric has no rule for answers that list the gold target with another candidate; see `D-hedged-alternatives`.

## Files

- `audit/ISSUE.md` (record), `audit/CONTRACT.md` (contracts), `audit/pins.json` (row hashes)
- `audit/replacement/toyqa_replacement.py` (replacement grader)
- `audit/tests/` (fixtures, `test_fixtures.py`, `test_cli.py`, `test_properties.py`, `make_data.py`, `data/`)
- `audit/scripts/` (`pin_inputs.py`, `panel.py`, `fuzz.py`, `freeze_sample.py`, `common.py`)
- `audit/panel/` (stored-panel verdicts), `audit/frozen/` (frozen sample, keys, batches, `SHA256SUMS`)
