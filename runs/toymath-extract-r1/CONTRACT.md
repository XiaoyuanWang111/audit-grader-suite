# ToyMath 1.0: grading contract

Written from the text that the model sees (`case/prompt_template.txt`, the 12 rows of `case/problems.jsonl`)
and the benchmark card's scoring rule as quoted in `case/TASK.md`, before reading `case/grade.py` or
`case/reference/grade_ref.py`. Rule numbers (R1 to R5) refer to the card's scoring rule. Each later change to
this file is recorded in `audit/ISSUE.md` with its reason.

ToyMath has one check, `answer`: the response's final answer equals the problem's reference answer within
0.01. Grading has four stages. Every stage is deterministic, and no LLM is involved.

## Labels

| Label | When | Effect on the score |
|---|---|---|
| `correct` | the answer line's number is within 0.01 of the reference answer (R4) | counts as correct |
| `incorrect` | the answer line has a number, and it is not within 0.01 | counts as not correct |
| `no_answer` | no answer line, or no number on the answer line (R3) | counts as not correct (R3 calls it incorrect), stays in the denominator |

`no_answer` is the extraction-failure label. It is never correct, it is not an abstention, and it is never
dropped from the denominator. Giving an R3 response the label `incorrect`, or a response with a number the label
`no_answer`, is a label error that does not change the score. The audit counts label errors separately from
score errors (correct versus not correct).

## Graded text

The graded text is the whole `response` string as stored, with no stripping or normalization. No model in the
run emits a reasoning block, and the server has no reasoning parser, so there is no end-of-reasoning marker to
split at. A response that stopped on the output budget (`finish_reason` `length`) is graded as written,
because the card has no truncation rule. The audit counts these responses separately.

## S1. Answer line (R1)

1. Split the graded text into lines with Python's `str.splitlines()`. Its line boundaries are `\n`, `\r`,
   `\r\n`, `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e`, `\x85`, ` ` and ` `.
2. A line is an answer line when, after its leading whitespace, its next seven characters are exactly
   `Answer:` (case-sensitive, with nothing between `Answer` and `:`). Whitespace is every character for which
   Python's `str.isspace()` is true (decision `D-leading-whitespace`).
3. The answer line is the last answer line of the response. Every line after it is ignored, whatever it
   contains.
4. These lines are not answer lines: `**Answer:** 15`, `answer: 15`, `ANSWER: 15`, `Final Answer: 15`,
   `Answer : 15`, `Answers: 15`, `> Answer: 15`, `- Answer: 15`, `Answer：15` (fullwidth colon),
   `The answer is 15`. A zero-width space (U+200B) or byte-order mark (U+FEFF) before `Answer:` is not
   whitespace.
5. No answer line: `no_answer`.

## S2. The number on the answer line (R2, R3)

1. Search the text that follows the `Answer:` prefix on the answer line (decision `D-answer-line-form`,
   added after the contract hash was first recorded; see the decision table).
2. A number is an optional `-` (U+002D hyphen-minus only), immediately followed by one or more digits,
   then optionally a `.` immediately followed by one or more digits. A comma that stands between two digits is
   part of the number and is ignored: `12,500` and `12500` are the same number, and so are `1,5` and `15`
   (decision `D-comma-grouping`). Digits are the ASCII digits `0` to `9` (decision `D-digits`).
3. The answer is the first number in that text (decision `D-multiple-numbers`).
4. No number in that text: `no_answer`, even when an earlier answer line or a later line has a number.
5. Consequences that the text fixes under `D-answer-line-form` (a). Under its reading (b), every example
   below whose text after `Answer:` holds anything besides one number has no number, and gets `no_answer`.
   - `−7` (U+2212 minus sign) or `– 7` (en dash) gives 7, and `- 7` (space after the hyphen) gives 7. Only a
     hyphen-minus directly before the digits makes a number negative.
   - `+72` gives 72. `486.` gives 486: a point not followed by a digit is not part of the number.
   - `.5` gives 5, and `-.5` gives 5: the grammar has no number without digits before the point.
   - `1.5e4` gives 1.5, `15k` gives 15, `2 250` gives 2, `15.000` gives 15 (the point is a decimal point),
     and `3,5` gives 35.
   - Units, currency symbols and markup around the number do not change it, and no rule fails a response for
     them: `$15,000` gives 15000, `15,000 dollars` gives 15000, `**15**` gives 15, `-7°C` gives -7.
   - Number words are not numbers: `fifteen` gives no number.

## S3. Comparison (R4)

1. The reference answer is the `answer` string of the problem's row in `problems.jsonl`, read as an exact
   decimal.
2. `correct` when |x − r| ≤ 0.01, computed exactly in decimal arithmetic, where x is the answer and r the
   reference (decision `D-tolerance-boundary`). Otherwise `incorrect`.
3. Exact arithmetic means that a value outside the tolerance by any margin is incorrect, and one inside it
   by any margin is correct: for r = 3.5, `3.51000000000000001` is incorrect and `3.4900000000000001` is
   correct, under every reading.

## S4. Score (R5)

1. A model's score is 100 × (the number of the 12 problems whose response is `correct`) / 12.
2. The denominator is always 12. A problem with no response from the model counts as not correct, and so
   does a `no_answer`.
3. The card says that a model answers each problem once, and R5 scores the 12 problems. So a second response
   to the same problem must not make that problem count twice, and a response whose `problem_id` is not one
   of the 12 counts toward no score. Rejecting such a file with an error is allowed.
4. From the audit skill, not the card: grading must not raise an exception on any response string. An
   exception is a grading failure, which the audit counts separately from model accuracy.

## Decision entries

The text allows two verdicts at each of these points. The proposed reading is (a), and the contract above
uses it.

| Entry | (a) Proposed | (b) Alternative | Example, problem: response, verdict under (a) / (b) |
|---|---|---|---|
| `D-multiple-numbers` | the first number after `Answer:` | the last number on the answer line | p12: `Answer: 15 (3 x 5)`, correct / incorrect; p03: `Answer: 2500 - 700 + 450 = 2250`, incorrect / correct |
| `D-comma-grouping` | a comma between two digits is ignored wherever it stands | a comma is ignored only as a thousands separator (groups of three digits); any other comma ends the number | p12: `Answer: 1,5`, correct / incorrect; p07: `Answer: 15,000`, correct / correct |
| `D-digits` | digits are ASCII `0` to `9` | digits are any Unicode decimal digits (category Nd) | p02: `Answer: ４８６` (fullwidth), no_answer / correct |
| `D-leading-whitespace` | whitespace is any `str.isspace()` character | whitespace is ASCII space and tab only | p02: ` Answer: 486` (no-break space first), correct / no_answer |
| `D-tolerance-boundary` | within 0.01 includes a distance of exactly 0.01 | within 0.01 excludes it | p01: `Answer: 3.51`, correct / incorrect; p06: `Answer: 0.01`, correct / incorrect |
| `D-answer-line-form` (added later) | the answer is the first number found in the text after `Answer:`, and other text on the line is allowed | the text after `Answer:`, with surrounding whitespace stripped and commas removed, must be exactly one number; otherwise the line has no number | p05: `Answer: 72 km/h`, correct / no_answer; p07: `Answer: $15,000`, correct / no_answer |

Reasons for the proposals. `D-multiple-numbers`: the prompt asks for the form `Answer: <number>`, which puts
the number right after the label. A third reading, that a line with two numbers gives none, also exists. A
human grader would instead read which number the line states as the result. `D-comma-grouping`: the card says
only that commas in the number are ignored, and states no grouping rule. `D-digits` and
`D-leading-whitespace`: the card describes line splitting in Python's terms, and Python's whitespace includes
the no-break space; but "digits" in an English number grammar most naturally means 0 to 9. `D-tolerance-boundary`:
"within" a distance usually includes that distance.

`D-answer-line-form` was added after the first contract hash, when reading the reference grader showed this
reading: the reference grades the answer line only if the whole text after `Answer:` is one number. The
proposal is (a), because R3 calls a response incorrect when there is "no number on its answer line", which
presupposes searching the line for a number. The prompt's "a final line of the form `Answer: <number>`" and
"without units or currency symbols" support (b). Under (b), `D-multiple-numbers` has no effect, and
`D-comma-grouping` (b) requires the whole text to be a correctly grouped number.

A grader verdict that some combination of (b) readings makes right is a decision, and the report names every
entry involved. A verdict that no combination makes right is a finding.
