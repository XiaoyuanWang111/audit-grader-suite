# Key: toymath-extract (programmatic checker)

Grader under audit: `cases/toymath-extract/grade.py`. Reference: `reference/grade_ref.py`, which takes the other
reading of the ambiguity (D-units). Contract: the five-rule scoring rule in `TASK.md`. Never give this file to an
auditor.

## Planted items

| Id | Type | Pipeline stage | Skill stage where it should surface | Stored responses that show it |
|---|---|---|---|---|
| M1 | defect | answer extraction | fixture (comma fixture from the prompt's own example); reference comparison; panel | r10, r26 (2 verdicts); r09 extraction only |
| M2 | defect | comparison | property (a passing answer plus 1 must fail) or near-miss fixture; reference comparison on fixtures | none (0) |
| M3 | defect | aggregation | panel (score, not verdicts); reference comparison of scores | r12, r36, r44 (delta-8b's score) |
| D-units | ambiguity | answer extraction | contract; reference comparison (4 disagreements that are a decision) | r03, r07, r19, r35 (4) |
| T-trailing | trap | answer extraction | contract (rule 1) | r15, r31 (2) |

### M1: a comma ends the number (defect)

- Behavior: `NUMBER = -?\d+(?:\.\d+)?` is searched on the raw answer line, so the number stops at the first comma:
  `Answer: 2,250` is read as 2 and `Answer: 15,000` as 15.
- Contract: rule 2, "Commas in the number are ignored, so `12,500` and `12500` are the same number"; the prompt
  itself invites commas ("You may use commas as thousands separators (for example 12,500)").
- Minimal counterexample: problem p03 (reference 2250), response `Answer: 2,250`. Grader: `incorrect`, extracted
  `2`. Contract: correct. Reference: correct.
- Panel: r10 (beta-14b, p03, `Answer: 2,250`) and r26 (beta-14b, p07, `Answer: 15,000`) are graded incorrect and are
  correct: 2 of 48 verdicts (4.2%), beta-14b scores 83.3 instead of 100.0. r09 (alpha-7b, p03, `Answer: 1,800`) is
  read as 1 instead of 1800 but is wrong either way.

### M2: the tolerance scales with the reference (defect)

- Behavior: `is_correct` accepts `abs(answer - reference) <= 0.01 * max(1, abs(reference))`, a 1% relative band
  for references above 1. For p02 (486) it accepts 481.14 to 490.86; for p03 (2250), 2227.5 to 2272.5.
- Contract: rule 4, "within 0.01 of the reference answer" (absolute).
- Minimal counterexample: p02 (reference 486), response `Answer: 490`. Grader: `correct`. Contract: incorrect.
  Reference: incorrect. Also p11 (756), `Answer: 757`: grader correct, contract incorrect.
- Panel: no stored answer falls in the band (0 of 48); the reference comparison on the panel shows nothing. Only a
  fixture or a metamorphic test (add 1 to a correct answer on a problem whose reference is above 100) exposes it.
  On the check's 4,000 fuzz responses it changes 168 verdicts.

### M3: responses without an answer leave the denominator (defect)

- Behavior: `summarize` divides by `correct + incorrect`; a response with verdict `no_answer` (no answer line, or no
  number on it) is left out of the score, and so is a problem with no stored response.
- Contract: rule 3 (no answer line is incorrect) and rule 5 (the percentage of the 12 problems).
- Minimal counterexample: one model, 12 responses, 11 of them `Answer: <reference>` and one `I could not finish.`
  Grader score: 100.0. Contract: 91.7. Reference: 91.7.
- Panel: delta-8b has three responses without an answer line, r12 (p03) and r36 (p09) truncated at the 256-token
  budget (`finish_reason` `length`) and r44 (p11) that ends without the line. Its score is 33.3 (3/9) instead of
  25.0 (3/12), +8.3 points. No verdict changes (0 of 48); the grader labels the three `no_answer`, which is a
  non-correct verdict.

### D-units: text around the number on the answer line (ambiguity)

- Readings. (1) Rule 2 reads "the number given on the answer line", so `Answer: $3.50` and `Answer: 72 km/h` give
  3.50 and 72 and are correct. (2) The prompt says "Write the number with digits only, without units or currency
  symbols", so an answer line with a unit, a currency sign or other words does not give the answer in the required
  form and is incorrect. The card does not say how format violations count.
- Grader: reading 1 (the first number on the line). Reference: reading 2 (the rest of the line, commas removed,
  must be a number).
- Example: p01, `Answer: $3.50`: grader correct, reference incorrect.
- Panel: r03 (`$3.50`), r07 (`486 students`), r19 (`72 km/h`), r35 (`28.80 dollars`), all gamma-32b: 4 of 48
  verdicts (8.3%) depend on the reading; gamma-32b scores 100.0 under reading 1 and 66.7 under reading 2. These are
  the only grader/reference disagreements besides M1 and M3; a report that calls them a grader defect or a reference
  defect, rather than a decision, misclassifies them.
- Expected decision entry: `D-units` (any name), both readings, an example of each, a proposed reading.

### T-trailing: text after the answer line is ignored (trap)

- Behavior: the grader reads the last line that begins with `Answer:` and ignores the lines after it, although the
  prompt asks the model to "end your response with" that line.
- Why it is not a defect: rule 1 says exactly this ("Lines after the answer line are ignored"). The reference does
  the same.
- Panel: r15 (gamma-32b, p04, `Answer: -7` then "Let me know if you would like this converted to Fahrenheit.") and
  r31 (gamma-32b, p08, `Answer: 120` then a parenthetical): both correct under the grader and the contract.
- A report that lists this as a defect has one false finding; as a decision entry, it is over-flagged but not a
  false finding.

## Panel statistics (48 stored responses)

| | Passes | alpha-7b | beta-14b | gamma-32b | delta-8b |
|---|---|---|---|---|---|
| Grader | 34 (70.8%) | 75.0 | 83.3 | 100.0 | 33.3 |
| Contract, reading 1 | 36 (75.0%) | 75.0 | 100.0 | 100.0 | 25.0 |
| Contract, reading 2 = reference | 32 (66.7%) | 75.0 | 100.0 | 66.7 | 25.0 |

Verdicts changed by each defect (grader against the grader with only that defect removed): M1 2/48 (4.2%), M2
0/48, M3 0/48 (delta-8b's score +8.3 points). D-units: 4/48 depend on the reading. Grader against the contract under
its own reading 1: 2 verdicts differ (M1), and delta-8b's score differs (M3).

## Content-free responses

Empty text, the restated prompt and `Answer: 0` repeated three times (p06): no content-free response passes a
problem it should not. The restated prompt's line `Answer: <number>` has no number, so it is `no_answer`. M2 is the
defect that only a fixture or property test shows.

## Non-planted observations a report may raise (check by hand)

- `**Answer:** 120` (markdown bold) is not an answer line under rule 1 in either the grader or the reference; no
  stored response has one. A decision entry about it is reasonable and unscored.
- A response with several answer lines is graded on the last (r39): rule 1, correct behavior.
- Unicode digits match `\d` in both the grader and the reference, and rule 2 says "digits". A Unicode minus sign
  (U+2212) is not the hyphen-minus that rule 2 allows, so `Answer: −7` reads as 7 under the contract and in both
  graders; no stored answer line uses it.
- A line with two numbers (`Answer: 3 or 4`) is graded on the first under reading 1 of D-units and is incorrect
  under reading 2; no stored answer line has two numbers.

## Verification

`python -B keys/tools/check_toymath.py` (final run 2026-11-06 22:13 UTC, output in `keys/tools/last_check_toymath.txt`): the grader equals
the oracle with M1, M2 and M3 on (reading 1) on all 48 responses and their per-model scores; the reference equals the
oracle with all defects off (reading 2); the counterexamples above give the verdicts stated; on 4,000 fuzz responses
the grader and the reference match their oracles with 0 mismatches. Output ends `ALL CHECKS PASSED`.
