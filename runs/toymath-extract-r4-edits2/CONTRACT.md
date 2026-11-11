# Contract: ToyMath 1.0 final-answer check

Written from `case/TASK.md` (the prompt the model sees and the scoring rule
from the ToyMath benchmark card) before any grader code was read. Quoted
phrases are from TASK.md. Later changes are appended at the end with a reason
and do not rewrite this text.

## Scope

ToyMath has one check, applied to each of the 12 problems: is the final answer
within 0.01 of the reference answer. The grader's labels are `correct`,
`incorrect` and `no_answer`. The score counts only `correct`.

## Graded text

The whole `response` field, as stored. None of the models emits a reasoning
block and the serving stack has no reasoning parser, so there is no extraction
step before the answer-line rule, and no extraction-failure label. Text such as
`<think>` inside a response is ordinary text. A response cut off by the output
budget (`finish_reason` = `length`) is graded on its stored text like any
other.

## C1. Answer line

- Split the graded text into lines exactly as Python's `str.splitlines()` does
  (so `\n`, `\r\n`, `\r`, `\v`, `\f`, `\x1c`, `\x1d`, `\x1e`, `\x85`,
  ` `, ` ` all end a line).
- A line is a candidate when it begins with the exact, case-sensitive string
  `Answer:`, after optional leading whitespace (which characters are
  whitespace: `D-leading-whitespace`).
- The answer line is the last candidate. Lines after it are ignored, whatever
  they contain.
- Not candidates (unambiguous): `answer: 5`, `ANSWER: 5`, `Answer : 5`,
  `Answers: 5`, `Final Answer: 5`, `**Answer:** 5`, `- Answer: 5`,
  `The answer is 5`, and `Answer:` occurring mid-line.
- Nothing is required after the colon: `Answer:5` and `Answer:-7` are answer
  lines.

## C2. The number on the answer line

- Search the text of the answer line after `Answer:`.
- A number is an optional `-` (U+002D hyphen-minus) directly followed by
  digits, then optionally a decimal point `.` directly followed by more digits
  (which characters are digits: `D-digits`). No whitespace inside a number.
  Other minus signs (U+2212, en dash, em dash) are not part of the number:
  `Answer: −7` has the number 7. `+` is not part of the number.
- Commas inside the number are ignored: a comma that sits between digits of a
  number joins them, so `12,500` = `12500`, `2,250` = `2250`, `1,5` = `15`.
  A comma not between digits (for example `486,` at the end of a sentence) is
  not part of the number.
- A decimal point with no digit after it is not part of the number: in
  `Answer: 3.` the number is 3. A period after the number is punctuation:
  `Answer: 3.5.` has the number 3.5.
- `2.250` is the number 2.25, not 2250 (only commas are ignored).
- `1.5e4` contains the number 1.5 (exponents are not part of a number).
- Text around the number on the answer line (units, currency signs, markup,
  words): `D-surrounding-text`.
- Several numbers on the answer line: `D-multiple-numbers`.

## C3. Labels

- `no_answer`: the response has no answer line, or the answer line has no
  number (`D-no-number-label` covers whether the second case is `no_answer` or
  `incorrect`; the score is the same either way).
- `incorrect`: the answer line has a number, and it differs from the reference
  answer by more than 0.01.
- `correct`: the answer line has a number within 0.01 of the reference answer
  (`D-tolerance-boundary` covers a difference of exactly 0.01).
- The comparison is between the two decimal values written in the response
  and in `problems.jsonl`, compared exactly. `3.50` = `3.5`, `03.5` = `3.5`,
  `-0` = `0`. A verdict that depends on binary floating-point rounding, and
  differs from the exact decimal comparison under every reading of
  `D-tolerance-boundary`, breaks this contract.
- Rule 3: `no_answer` and `incorrect` both count as not correct.

## C4. Score and denominator

- A model's score is 100 x (number of the 12 problems whose response is
  `correct`) / 12. The denominator is always 12 per model.
- A problem with no response from a model counts as not correct for that model
  (it stays in the denominator).
- A response whose `problem_id` is not one of the 12 problems does not enter
  any score.
- "A model answers each problem once." Two responses from one model to one
  problem break the protocol. The grader must not count that problem twice,
  and a score above 100% or a denominator other than 12 breaks this contract.
- An exception while grading one response is a grading failure for that
  response. It must not decide other responses' verdicts.

## C5. Content-free responses

Each of these must be `no_answer` (or `incorrect`), never `correct`, unless
the text literally carries an answer line with a correct number:

- empty text; whitespace only;
- the prompt restated (its only `Answer:` line is `Answer: <number>`, which
  has no number);
- the problem text restated;
- repeated filler text.

## Decision entries (both readings, an example of each, the proposal)

| Entry | Reading A | Reading B | Example | Proposed |
|---|---|---|---|---|
| `D-leading-whitespace` | any character that Python's `str.isspace()` accepts (space, tab, U+00A0, U+3000, ...) | ASCII space and tab only | ` Answer: 72` for p05: A correct, B no answer line | A: the rule already defers to Python for line splitting, and "whitespace" is unqualified |
| `D-digits` | ASCII `0`-`9` only | any Unicode decimal digit (category Nd), by its value | `Answer: ７２` (fullwidth) for p05: A no number, B 72, correct | A: the number syntax names characters exactly (hyphen-minus), and the prompt asks for "digits only" with ASCII examples |
| `D-surrounding-text` | other text may surround the number on the answer line; the number is found within it | the answer line must be `Answer:` then the number alone (optional whitespace, optional final period); anything else has no number | `Answer: $3.50` for p01: A correct, B no number | A: rules 2 and 3 speak of "the number given on the answer line" and "no number on its answer line", and no rule makes a format slip incorrect |
| `D-multiple-numbers` | the first number on the answer line | the last number on the answer line (or C: no single number, so incorrect) | `Answer: 6 muffins, so 3.5` for p01: A 6 incorrect, B 3.5 correct, C incorrect | A: the format `Answer: <number>` puts the number first |
| `D-tolerance-boundary` | "within 0.01" includes a difference of exactly 0.01 | excludes it | `Answer: 3.51` for p01: A correct, B incorrect | A: the usual meaning of "within" |
| `D-no-number-label` | an answer line without a number gets `no_answer` | it gets `incorrect` | `Answer: unknown`: A `no_answer`, B `incorrect` | A: rule 2 defines the answer as the number, so there is no answer. Score-neutral |

## Change log

- 2026-11-11 01:01 UTC, after reading the grader and the reference.
  `D-surrounding-text` reading B is restated as: the rest of the answer line,
  with surrounding whitespace removed, must be one number and nothing else
  (commas between digits allowed); any other character, a final period
  included, means no number. Reason: the first wording ("optional final
  period") was an arbitrary midpoint; "a final line of the form
  `Answer: <number>`" read strictly allows nothing but the number, and the
  reference implements exactly that. The proposal (reading A) is unchanged.
- 2026-11-11 01:01 UTC. `D-multiple-numbers` reading C ("no single number")
  gets the label `no_answer` (no answer is identified), score-neutral against
  `incorrect`. Reason: the first version left C's label open.
