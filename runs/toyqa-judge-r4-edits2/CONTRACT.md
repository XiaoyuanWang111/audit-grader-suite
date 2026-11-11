# ToyQA judge pipeline: contracts

Written from the text the answering model sees (`case/prompt_template.txt`), the text the judge sees
(`case/judge_template.txt`, its rubric), the questions with their gold targets and aliases
(`case/questions.jsonl`), and the pipeline description that `case/TASK.md` quotes from the ToyQA README.
Written before reading any code (`case/judge_pipeline.py`, `case/judges.py`, `case/reference/pipeline_ref.py`).
Every later change is listed at the end with its reason.

The grader has one check: the label of one response to one question. It is a pipeline, so the contract has one part
per stage (C1 to C6) and one part for the label itself (C0).

## C0. The label a graded text must get (the rubric)

Labels: `correct` (judge grade A), `incorrect` (B), `not_attempted` (C), and the pipeline labels
`extraction_failure` and `judge_error`.

- `correct`: the predicted answer gives the gold target, or an answer the question lists as also accepted (an
  alias), and nothing in it contradicts the gold target. Differences in capitalization, punctuation, accents and
  the articles a, an, the do not matter (so `skin`, `The Skin`, `Gabriel Garcia Marquez`, `w` and `Amazon` match
  `the skin`, `Gabriel García Márquez`, `W` and `the Amazon`). Repeating the question is not needed. Extra words
  around the answer are allowed as long as nothing contradicts the gold target. A hedged answer that names only
  the gold target ("I think it is Canberra") is `correct`: it gives the target and contradicts nothing.
- `incorrect`: the predicted answer gives an answer that is not the gold target or an alias, or says something
  that contradicts the gold target. A guess counts as an answer: "I am not sure, maybe Sydney" is `incorrect`.
- `not_attempted`: the predicted answer gives no answer, for example it says it does not know, and it does not
  guess. An empty predicted answer, a restatement of the question, or a restatement of the instructions gives no
  answer, so it is `not_attempted`.
- The judge is told to grade against the gold target as given, not against outside knowledge.

## C1. Graded text (extraction)

- If the response contains `</think>`, the graded text is the text after the last `</think>`; otherwise it is the
  whole response.
- Leading and trailing whitespace of the graded text is removed (see `D-whitespace`).
- A response that contains `<think>` and no `</think>` gets `extraction_failure` and is not sent to the judge.
  It is in the accuracy denominator, never correct, not an attempt, and is reported as a count.
- A response with `</think>` and no `<think>` (a template that opens the reasoning in the prompt) is graded on the
  text after the last `</think>`.
- A `<think>` that opens after the last `</think>` and never closes: see `D-reopened-think`.
- An empty graded text after a closed `</think>` is not an extraction failure. It goes to the judge and should be
  `not_attempted` (C0).
- `finish_reason` does not enter the label. A truncated response is graded by the rules above.

## C2. Judge prompt (rendering)

- The predicted answer is the graded text cut to its first 300 Python string characters (code points). A graded
  text of 300 characters or fewer is used unchanged.
- `{target}` is the gold target, followed by ` (also accepted: X, Y)` when the question has aliases: the aliases in
  their order, joined by `, `. A question with no aliases gets the gold target alone.
- `{question}` is the question.
- Substitution is literal and happens once: braces or placeholder names inside the question, the target or the
  graded text are copied as they are and are never substituted again. Every other character of the template is
  kept, including its trailing newline.
- The rendered prompt is the only user message of the judge call.
- The 300-character window: see `D-judge-window`.

## C3. Judge call

- Judge model `judge-m1`, temperature 0, `max_tokens` 32, the prompt as one user message.
- Call 1 always. Call 2, with the same prompt, only when call 1 gives no grade (C4). No call 3.
- Replies are cached by prompt and call number, so identical prompts get identical replies.
- A judge back end that raises is a grading failure, counted apart from model accuracy; it must not stop the
  grading of other responses (see `D-judge-exception`).

## C4. Reply parsing

- The grade is the last capital letter A, B or C in the reply that stands alone: no ASCII letter or digit
  (A-Z, a-z, 0-9) directly before or after it. Start and end of the reply count as not a letter or digit.
- Non-ASCII characters, underscores, punctuation, markup and whitespace next to the letter do not stop it from
  standing alone (`*A*`, `(B)`, `_C_`, `éA` all give a grade). Lowercase `a`, `b`, `c` and non-ASCII look-alikes
  such as full-width `Ａ` are not grades.
- Examples: `A` gives A; `A.` gives A; `Grade: B` gives B; `B: INCORRECT` gives B; `C: NOT_ATTEMPTED` gives C;
  `CORRECT` gives none; `A1` gives none; `The grade is A, not B` gives B (the last standalone letter).
- No grade in call 1: call 2. No grade in either call: `judge_error`.

## C5. Label mapping

- A is `correct`, B is `incorrect`, C is `not_attempted`. `extraction_failure` and `judge_error` are their own
  labels and are never mapped to `not_attempted`, `incorrect` or `correct`.

## C6. Aggregation, per model

- Denominator: 12, the number of ToyQA questions, for accuracy and the not-attempted rate. Every response of the
  model counts once whatever its label, including `extraction_failure` and `judge_error`.
- accuracy = correct / 12; attempted = correct + incorrect; cga = correct / attempted, or 0 when attempted is 0;
  F-score = 2 * accuracy * cga / (accuracy + cga), or 0 when both are 0; not-attempted rate = not_attempted / 12.
- `extraction_failure` and `judge_error` are never correct, never attempts, and are reported as counts.
- A model with a missing response: see `D-missing-response`.

## Decision entries opened while writing the contract

Each lists both readings and the proposal; the evaluation's maintainers decide.

- `D-whitespace`: which characters are the leading and trailing whitespace removed in C1. (a) Python `str.strip()`,
  all Unicode whitespace, including U+00A0 and U+3000. (b) ASCII whitespace only. Proposed: (a), the usual meaning
  in a Python pipeline. Affects the judge prompt bytes, so the recorded judge cache key, but rarely the label.
- `D-reopened-think`: a response whose last `</think>` is followed by a `<think>` that never closes. (a) README
  literal: it contains `</think>`, so the graded text is everything after the last `</think>`, including the open
  reasoning. (b) The reasoning never closed, so `extraction_failure`. Example: `<think>x</think>Canberra<think>more`
  is graded on `Canberra<think>more` under (a) and is `extraction_failure` under (b). Proposed: (b), because the
  graded text then holds unfinished reasoning, which the README's extraction rule is meant to keep from the judge.
- `D-judge-window`: an answer whose deciding words lie past character 300 of the graded text. (a) README: the judge
  sees only the first 300 characters, and the label follows them. (b) The label should follow the whole graded
  text. Example: 290 characters of discussion, then `so the answer is Canberra`: (a) the judge cannot see the
  answer and should grade C; (b) `correct`. Proposed: (a), as the README states it, with the count of graded texts
  longer than 300 characters reported, since the model is asked for a short answer.
- `D-judge-exception`: a judge back end that raises for a prompt. (a) A call that gives no grade: retry, then
  `judge_error`. (b) A run failure. Proposed: (a); one judge failure must not stop the run or drop other verdicts.
- `D-missing-response`: a model with fewer than 12 responses. (a) Denominator stays 12; a missing response counts
  like an extraction failure. (b) Denominator is the number of responses. Proposed: (a), README says "/ 12".

## Changes

- 2026-11-11, after grading the stored panel (step 5): added `D-hedged-alternatives`. Reason: three stored answers
  name the gold target together with another answer (`Either 1648 or 1658, I believe.`, `Either iron or cobalt.`,
  `It is either 1 or 2.`), and C0 does not settle them: such an answer "gives the gold target" (A) and also "gives
  an answer that is not the gold target" (B). No contract rule above changed.

## Decision entries added later

- `D-hedged-alternatives`: an answer that offers the gold target and another answer as alternatives.
  (a) `incorrect`: it gives an answer that is not the gold target, and the alternative contradicts it.
  (b) `correct`: it gives the gold target, and offering an alternative is not a contradiction.
  Example: `Either iron or cobalt.` for atomic number 26 is `incorrect` under (a) and `correct` under (b).
  Proposed: (a), because otherwise listing every candidate would always score as correct.
