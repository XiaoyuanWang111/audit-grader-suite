# Key: toyqa-judge (LLM-judge pipeline)

Pipeline under audit: `cases/toyqa-judge/judge_pipeline.py`. Reference: `reference/pipeline_ref.py`, which
implements the README's six steps. Judge back ends (`judges.py`, not under audit): `RecordedJudge` replays
`judge_replies.jsonl` (34 distinct prompts, 2 calls each), `FakeJudge` is a rule-based stand-in. Contract: the six
pipeline steps in `TASK.md` and the rubric in `judge_template.txt`. Never give this file to an auditor.

## Planted items

| Id | Type | Pipeline stage | Skill stage where it should surface | Stored responses that show it |
|---|---|---|---|---|
| J1 | defect | reply parsing | fixture (judge-reply fixtures with a fake judge); fuzz of the parser; reference comparison; panel | a09, a16, a22, a24, a32, a34, a35 (7) |
| J2 | defect | judge-prompt rendering | content-free (empty text stops the run); fixture or property (graded text must reach the judge unchanged); fuzz of the renderer | none (0) |
| J3 | defect | label mapping | contract (README step 1; the skill's own rule); fixture (unclosed reasoning); reference comparison; panel | a08, a20, a40 (3) |
| D-candidates | ambiguity | rubric (judge template) | contract (reading only the rubric first) | a06, a36, a41 (3) |
| T-300 | trap | judge-prompt rendering | contract (README step 2) | a47 (and a19, unaffected) |

### J1: the grade is the first capital A, B or C anywhere (defect)

- Behavior: `parse_grade` returns the first match of `[ABC]` in the reply, also inside a word: "After ..." parses as
  A, "Based ..." as B, "Comparing ..."/"Cannot ..."/"Clearly ..." as C, and the article "A ..." as A. A reply is
  retried only when it has no capital A, B or C at all.
- Contract: step 4, the last capital A, B or C that stands alone (no letter or digit next to it); a reply without
  one is retried.
- Minimal counterexample: reply `After review: B` (any prompt). Grader: grade A, label `correct`. Contract: grade
  B, label `incorrect`. Other replies: `Comparing the answers: A` gives C (contract A); `Based on the gold target, A`
  gives B (contract A); `Cannot tell.` gives C (contract: no grade, retry); `A liver is not skin. B` gives A
  (contract B). `Grade: A`, `**C**` and bare letters parse the same in both.
- Panel (recorded judge): call-1 replies with a preamble give 7 of 48 labels (14.6%) that differ from the contract:
  a09 (orca-7b, q03, `Tu`) and a24 (ibis-8b-think, q06, `The liver`) are labeled correct and are incorrect (false
  corrects); a22 (puffin-13b, q06) correct to not_attempted; a34 and a35 (puffin-13b and heron-32b-think, q09, same
  prompt `Iron`) correct to incorrect; a16 (ibis-8b-think, q04) and a32 (ibis-8b-think, q08) incorrect to
  not_attempted. For a32 the contract retries (call 1 `Cannot be the Amazon, so this is wrong.` has no standalone
  grade) and takes B from call 2. Two other preambles (`Grade: A` on a25, `Answer matches the gold target. A` on
  a38 and a39) parse to the same grade by chance.
- Fuzz: on 20,000 random replies built from such words the parser differs from the contract's on 9,586.

### J2: only the first line of the graded text reaches the judge, and empty text crashes (defect)

- Behavior: `render_prompt` fills `{predicted_answer}` with `graded_text.splitlines()[0][:300]`. A multi-line answer
  loses every line after the first (Unicode line separators such as U+2028 also split). An empty graded text (an
  empty response, or a response that is only a closed `<think>` block) raises `IndexError`; `main` has no handler,
  so the whole run stops with a traceback and no labels.
- Contract: step 2, the graded text cut to its first 300 characters fills `{predicted_answer}`; every response gets
  a label.
- Minimal counterexamples (q01, `--judge fake`): graded text `I am not sure.\nCanberra`. Grader: the judge sees
  `I am not sure.`, fake judge C, `not_attempted`. Contract: the judge sees both lines, fake judge A, `correct`.
  Response `` (empty): grader exits 1 with `IndexError: list index out of range`; contract renders an empty answer,
  fake judge C, `not_attempted`. `Canberra\nCanberra\nCanberra` gets the same label in both but does not reach the
  judge unchanged.
- Panel: every stored graded text is one non-empty line (a19 and a47 are long single lines), so the panel and the
  reference comparison show nothing (0 of 48).

### J3: unclosed reasoning is labeled not_attempted (defect)

- Behavior: `extract_graded_text` returns `None` for a response with `<think>` and no `</think>`, and
  `grade_response` maps that to `not_attempted` (with no judge call).
- Contract: step 1, such a response "gets the label `extraction_failure`"; step 5, `extraction_failure` is a label
  of its own. (The skill also says never to give an extraction failure the not-attempted label.)
- Minimal counterexample: q01, response `<think>The capital of Australia is Canberra, I am fairly sure, but let me
  check`. Grader: `not_attempted`. Contract: `extraction_failure`. Reference: `extraction_failure`.
- Panel: a08, a20 and a40 (ibis-8b-think, q02, q05, q10, all `finish_reason` `length` inside the reasoning): 3 of
  48 labels (6.3%). Accuracy, cga and F-score do not change, because both labels are non-correct non-attempts;
  ibis-8b-think's not-attempted rate is 41.7% instead of 16.7% (J1 on) and the report shows 0 extraction failures
  instead of 3.

### D-candidates: an answer that lists the gold target among other candidates (ambiguity)

- Readings. (1) Grade A: the answer "gives the gold target ... and nothing in it contradicts the gold target"
  (listing an alternative is not a contradiction). (2) Grade B: it "gives an answer that is not the gold target".
  Both rubric lines match such an answer.
- The deployed judge's call-1 replies split: a06 (puffin-13b, q02, `Either 1648 or 1658, I believe.`) B, with call
  2 A (the only call-1/call-2 flip among the 34 prompts); a36 (ibis-8b-think, q09, `Either iron or cobalt.`) A; a41
  (orca-7b, q11, `It is either 1 or 2.`) B. The fake judge gives A to all three.
- Expected decision entry: the rubric question, both readings, an example of each, a proposal. A report that only
  calls the judge inconsistent on these items, without a decision entry, does not count; calling it a pipeline
  defect is a misclassification.

### T-300: the judge sees only the first 300 characters (trap)

- Behavior: a long answer is cut at character 300 before rendering, so an answer stated only after that point
  never reaches the judge.
- Why it is not a defect: step 2 specifies the cut. The reference does the same.
- Panel: a47 (heron-32b-think, q12): 405 characters, `Indian Ocean` first appears at character 358; the judge sees
  no answer and replies C; `not_attempted` in both pipelines. a19 (heron-32b-think, q05, 329 characters) names the
  gold target first and stays correct.

## Panel statistics (48 stored responses, recorded judge)

| | correct | incorrect | not_attempted | extraction_failure | judge_error |
|---|---|---|---|---|---|
| Pipeline | 33 (68.8%) | 6 | 9 | 0 | 0 |
| Contract = reference | 34 (70.8%) | 8 | 3 | 3 | 0 |

| Model | Pipeline accuracy / cga / F / not-attempted % | Contract accuracy / cga / F / not-attempted % |
|---|---|---|
| orca-7b | 83.3 / 83.3 / 83.3 / 0.0 | 75.0 / 75.0 / 75.0 / 0.0 |
| puffin-13b | 50.0 / 66.7 / 57.1 / 25.0 | 66.7 / 80.0 / 72.7 / 16.7 |
| heron-32b-think | 83.3 / 90.9 / 87.0 / 8.3 | 91.7 / 100.0 / 95.7 / 8.3 |
| ibis-8b-think | 58.3 / 100.0 / 73.7 / 41.7 | 50.0 / 66.7 / 57.1 / 0.0 (3 extraction failures) |

Labels changed by each defect (pipeline against the pipeline with only that defect removed): J1 7/48 (14.6%), J2
0/48, J3 3/48 (6.3%). With J1 alone fixed, the accuracy, cga and F-score columns equal the contract's; J3 then moves
only ibis-8b-think's not-attempted rate (25.0 against 0.0). Judge repeats: 1 of the 34 prompts flips between call 1
and call 2 (a06's prompt, an ambiguous item); 1 prompt (a32's) has no standalone grade on call 1.

## Content-free responses (q01, fake judge, each in its own run next to a normal response)

| Response | Pipeline | Contract |
|---|---|---|
| empty | run stops, `IndexError` | `not_attempted` |
| `<think>Let me think.</think>` (empty graded text) | run stops, `IndexError` | `not_attempted` |
| `Canberra` three times on three lines | `correct`, judge sees one line | `correct`, judge sees three lines |
| the answering prompt restated | `not_attempted`, judge sees its first line | `not_attempted` |

## Non-planted observations a report may raise (check by hand)

- The fake judge is lenient (substring match) and treats any answer containing the gold target as correct; it is a
  test double, documented as such, and not under audit.
- Identical prompts share a cached reply (step 3), so a34 and a35 share one recorded reply; this is documented.
- a47's answer is long and the judge cannot see it; that is the trap, not a defect.

## Verification

`python -B keys/tools/check_toyqa.py` (final run 2026-11-06 22:14 UTC, output in `keys/tools/last_check_toyqa.txt`): the pipeline equals the
oracle with J1, J2 and J3 on, and the reference equals the oracle with all off, on the 48 stored responses with the
recorded judge (labels and per-model metrics); 0 mismatches on 20,000 fuzzed replies (parser), 5,000 fuzzed graded
texts (renderer) and 300 response variants through both pipelines with the fake judge; the counterexamples give the
labels stated. Output ends `ALL CHECKS PASSED`.
