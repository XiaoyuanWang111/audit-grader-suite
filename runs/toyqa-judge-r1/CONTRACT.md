# Contract: ToyQA 1.0 judge pipeline

Written from `case/TASK.md` (sections "What the judge sees", "Pipeline", "How the pipeline is run"), the rubric in
`case/judge_template.txt` and the gold targets in `case/questions.jsonl`, before reading `case/judge_pipeline.py`,
`case/judges.py`, `case/reference/pipeline_ref.py` or any stored response text. Clause ids are cited by the fixtures in
`audit/tests/` and by the findings.

A response row has `id`, `model`, `question_id` and `response`. The pipeline gives each row exactly one of five
labels: `correct`, `incorrect`, `not_attempted`, `extraction_failure`, `judge_error`.

## E. Graded text (pipeline step 1)

- E1. If the response contains the substring `</think>`, the graded text is everything after the last occurrence of
  `</think>`, with leading and trailing whitespace removed. This holds whether or not the response contains `<think>`
  and wherever `<think>` appears; for example, `<think>x</think>Paris<think>y` has the graded text `Paris<think>y`.
- E2. Otherwise, if the response contains `<think>`, its reasoning never closed: the label is `extraction_failure`,
  the judge is not called (0 calls) and there is no grade. It is never labeled `not_attempted`.
- E3. Otherwise the graded text is the whole response with leading and trailing whitespace removed.
- E4. The markers are the literal, case-sensitive strings `<think>` and `</think>`. `finish_reason` does not change
  the rule: a `length` response follows E1 to E3 like any other.
- E5. An empty graded text is not an extraction failure. It goes to the judge as an empty predicted answer.
- Whitespace means what Python's `str.strip()` removes; the README counts characters as Python string characters, and
  the same convention is taken here. No verdict in this audit depends on non-ASCII whitespace.

## R. Judge prompt (pipeline step 2, "What the judge sees")

- R1. `{predicted_answer}` is `graded_text[:300]`: the first 300 Python string characters (code points) of the graded
  text, with nothing removed or added after the cut.
- R2. `{target}` is the gold target when the question has no aliases, and otherwise
  `gold + " (also accepted: " + ", ".join(aliases) + ")"`, aliases in file order. For q05 that is
  `Gabriel García Márquez (also accepted: García Márquez)`.
- R3. `{question}` is the question text, unchanged.
- R4. The prompt is the text of `judge_template.txt` with each of the three placeholders replaced by its value. A value
  is inserted as text: braces or placeholder names inside a graded text (such as `{target}`) appear in the prompt
  unchanged and are not filled in. The prompt is the only user message; nothing else is sent.
- R5. The prompt's sha256 is taken over its UTF-8 encoding.

## J. Judge call (pipeline step 3)

- J1. Model `judge-m1`, temperature 0, `max_tokens` 32, the prompt as one user message.
- J2. Call 1 is made for every row that is not an extraction failure. Call 2 is made only when call 1 gives no grade
  (P1), with the same prompt, and is requested as call 2: the client caches replies by prompt and call number, so a
  retry requested as call 1 would get the cached call-1 reply back. There is never a third call.
- J3. A response labeled `extraction_failure` gets no judge call.

## P. Reply parsing (pipeline step 4)

- P1. The grade of a reply is the last character in it that is `A`, `B` or `C` (ASCII capitals) and has no ASCII
  letter or digit (`A-Z`, `a-z`, `0-9`) directly before it and none directly after it. The start and the end of the
  reply count as non-letters. Any other neighbour, such as whitespace, punctuation, `_`, `*`, a non-ASCII letter such as
  `é` or a non-ASCII digit, does not stop a letter from standing alone.
- P2. A reply with no such character gives no grade.
- P3. If call 1 gives no grade, the grade is that of call 2; if call 2 gives none either, the label is `judge_error`.
  The row's call count is 1 when call 1 gave a grade and 2 otherwise.

Parser examples, from P1 alone:

| Reply | Grade |
|---|---|
| `A` | A |
| `B.` | B |
| `**C**` | C |
| `Grade: B` | B |
| `A: CORRECT` | A |
| `B (INCORRECT)` | B |
| `C. NOT_ATTEMPTED` | C |
| `The answer is A.` | A |
| `A or B` | B |
| `B` then a new line, then `A` | A |
| `éA` | A |
| `A_` | A |
| `CORRECT`, `INCORRECT`, `NOT_ATTEMPTED` | none |
| empty reply | none |
| `a`, `A1`, `1A`, `AB` | none |

## L. Labels (pipeline step 5)

- L1. Grade A is `correct`, B is `incorrect`, C is `not_attempted`. A row without a graded text (E2) is
  `extraction_failure`, and a row with no grade after call 2 (P3) is `judge_error`. No other label exists.

## G. Aggregation (pipeline step 6)

Per model, over the benchmark's 12 questions:

- G1. `accuracy = correct / 12`. The denominator is the number of questions, 12, and does not shrink for extraction
  failures, judge errors or a missing row.
- G2. `attempted = correct + incorrect`; `cga = correct / attempted`, or 0 when `attempted` is 0.
- G3. `F = 2 * accuracy * cga / (accuracy + cga)`, or 0 when both are 0.
- G4. `not_attempted_rate = not_attempted / 12`. Extraction failures and judge errors are not in `not_attempted`.
- G5. Extraction failures and judge errors are never correct and never attempts, and are reported as counts.
- G6. With `--out`, one JSON line per response row with its label, its grade (A, B, C or none), its number of judge
  calls (0, 1 or 2) and its prompt's sha256.

Not specified by the text, so no fixture asserts a verdict, and step 4 only reports the behaviour: a response file
with two rows for one model and question, a row whose `question_id` is not in `questions.jsonl`, a non-string
`response`, and an exception raised by the judge back end.

## K. Grades: what the judge should return (the rubric)

From `judge_template.txt`, judged against the gold target and aliases as given, not against world knowledge:

- K1. A, CORRECT: the predicted answer gives the gold target or a listed alias, and nothing in it contradicts the gold
  target. Differences in capitalization, punctuation, accents and the articles a, an, the do not matter, and the answer
  need not repeat the question.
- K2. B, INCORRECT: the predicted answer gives an answer that is not the gold target or an alias, or says something that
  contradicts the gold target.
- K3. C, NOT_ATTEMPTED: the predicted answer gives no answer, for example because it says it does not know, and does not
  guess. An empty predicted answer gives no answer. A hedged guess ("maybe X") is a guess, so it is A or B, not C.

Examples: q01 `canberra.` is A, `Sydney` is B, `I don't know.` is C; q05 `Gabriel Garcia Marquez` and `Garcia Marquez`
are A (accents); q06 `Skin` and q08 `Amazon` are A (articles); q09 `Fe` and q11 `two` are A (aliases).

## Decision entries

The text allows two verdicts in these cases. The evaluation's maintainers choose the reading.

| Entry | Reading 1 | Reading 2 | Example | Proposed |
|---|---|---|---|---|
| `D-multiple-candidates` | A: the gold is given and no sentence says it is wrong | B: the predicted answer also gives an answer that is not the gold target (K2) | q01 `Canberra or Sydney` | Reading 2: accepting a list of candidates rewards guessing several answers |
| `D-unlisted-equivalent` | B: only the gold, the listed aliases and the four named differences (capitalization, punctuation, accents, articles) count | A: any form that names the gold target's referent counts | q05 `Márquez`; q07 `two hundred and six` | Reading 1: the aliases list the forms the authors accept (`two` for `2`, `Fe` for `iron`), and the rubric names the differences that do not matter |
| `D-cut-off-answer` | C: a predicted answer cut before it names anything gives no answer | B: it is an attempt whose answer is not the gold target | q01 `The capital of Australia is Canb` (output budget or 300-character cut) | Reading 1: C's own words, "gives no answer", fit a cut-off text |

Each decision entry concerns the judge's grade (K), so it is measured only by the judge itself (step 5) and the blinded
review (step 6); the deterministic stages (E, R, J, P, L, G) have no decision entry.
