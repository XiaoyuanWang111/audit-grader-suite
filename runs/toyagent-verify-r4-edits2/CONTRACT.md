# Contracts: ToyOps `count-server-errors`

Written from `case/task/instruction.md` (what the agent sees) and the scoring rule in `case/TASK.md` (the ToyOps
README excerpt), before any grader code, `expected.json` or `result.json` was read. The input logs were read,
because the agent sees them too.

## Sources quoted

- Instruction: count the requests in all three files (`access.log`, `access.log.1`, `access.log.2.gz`, the last
  gzip-compressed) whose status code is 500 to 599; the status code is "the field right after the quoted request";
  write the count "as a decimal integer" to `/workspace/out/answer.txt`. No network.
- README rule 1: pass when `/workspace/out/answer.txt` holds the correct count; whitespace around the content,
  including a final newline, is ignored; missing or empty file fails.
- README rule 2: the verifier runs on every trial's final sandbox, whatever the agent's status; its exit status
  alone decides: 0 passes, anything else fails; `verifier_exit_code` null fails.
- README rule 3: reward 1 on pass, 0 otherwise; a configuration's score is the mean reward over all its trials.

## The correct count

Parsing each line as `host ident user [time] "request" status bytes`, with the status taken as the field right
after the closing quote of the request: `access.log` has 40 lines and 20 with status 500 to 599, `access.log.1` 40
and 17, `access.log.2.gz` 30 and 4. The correct count is **41**. Every line parses; no CR bytes; each file ends
with a newline.

Traps in the data that the contract settles (the text is explicit, so these are not decisions):

- `access.log.1` has one request with a space inside the quoted request (`"GET /api/search?q=red shoes HTTP/1.1" 503
  167`). The field right after the quoted request is `503`, so it counts. A whitespace field split (`awk '{print
  $9}'`) reads `HTTP/1.1"` there and misses it: 40.
- The gzip file must be decompressed and counted: omitting it gives 37 (36 with the field-split error).
- Byte counts such as `5120`, `580`, `59000` start with 5 but are not status codes; a pattern such as
  `grep ' 5[0-9][0-9]'` over whole lines also matches them.

## Check V: the verifier verdict for one trial

Graded state: the regular content of the file at exactly `/workspace/out/answer.txt` in the trial's final
sandbox. Nothing else under `/workspace` may change the verdict.

Graded text: the file's content with whitespace around it removed (see `D-whitespace` for which characters).

- Pass: the graded text is a decimal integer whose value is 41 (see `D-leading-zeros`, `D-plus-sign`,
  `D-nonascii-digits` for the forms).
- Fail:
  - the file is missing (including an answer written anywhere else, such as `/workspace/answer.txt` or
    `/workspace/tmp/...`);
  - the file is empty or holds only whitespace;
  - the graded text is a different integer (37, 40, 44, 0, -41, ...);
  - the graded text is not a decimal integer: words (`forty-one`), hexadecimal (`0x29`), a fraction or decimal
    point (`41.0`), scientific notation (`4.1e1`), digit separators (`4_1`, `4,1`), two numbers on separate lines
    (`41\n41`), or other text around the number (see `D-surrounding-text`).
- Independence: adding, removing or changing any file under `/workspace` other than `out/answer.txt` must not
  change the verdict; neither must the agent's status (`completed`, `error`, `timeout`).
- Exit status mapping: pass is exit 0; every fail is a non-zero exit. A verifier exception counts as a fail by
  the README's rule, so an exception on a passing state is a wrong verdict (a grader defect), and an exception on
  a failing state is a correct verdict reached for the wrong reason (reported as a robustness finding only if it
  could flip a verdict).

## Check S: reward and score (`score_trials.py`)

- Trials in the denominator: every stored trial of the configuration, including trials whose agent ended in
  `error` or `timeout` and trials whose `verifier_exit_code` is null. Nothing is dropped.
- Reward: 1 when `verifier_exit_code` is the integer 0, else 0 (null, any non-zero code, a missing field).
- Score: mean reward over all trials of the configuration (here 9 each), so every score is a multiple of 1/9.
- Configuration identity: the `config` field of `result.json`.

## Network

The agent has no network access and the task needs none; nothing in the grader may depend on the network.

## Decision entries (text allows two verdicts)

| Id | Question | Reading A (example, verdict) | Reading B (example, verdict) | Proposed |
|---|---|---|---|---|
| `D-surrounding-text` | May other words surround the integer in the answer file? | The file must hold only the integer: `41 server errors` fails | The count may be embedded in text: `41 server errors` passes | A: "write the count as a decimal integer" names the file's whole content |
| `D-whitespace` | Which characters count as the "whitespace around the content" that is ignored? | ASCII whitespace only (space, tab, LF, CR, VT, FF): `41\r\n` passes, `41` followed by U+00A0 (no-break space) fails | Any Unicode whitespace: `41` + U+00A0 passes, U+3000 ideographic space passes | A: a decimal integer in a text file, written by shell tools; non-ASCII spaces are content |
| `D-leading-zeros` | Does a decimal integer with leading zeros count? | `041` is the decimal integer 41: passes | Only the canonical form counts: `041` fails | A: the value is the count and the notation is decimal |
| `D-plus-sign` | Does an explicit plus sign count? | `+41` is a decimal integer equal to 41: passes | A count is written without a sign: `+41` fails | B, weakly: a count has no sign; either reading is defensible |
| `D-nonascii-digits` | Do non-ASCII decimal digits count? | Only ASCII `0`-`9`: `４１` (full-width) and `٤١` (Arabic-Indic) fail | Any Unicode decimal digit: `４１` passes | A: "decimal integer" in a shell task means ASCII digits |

The BOM (U+FEFF) is not whitespace under either reading of `D-whitespace` (Unicode does not class it as
whitespace), so `﻿41` fails under both readings: a careful reader could still argue it is an encoding marker
rather than content, so it is listed under `D-whitespace` as a variant if a grader passes it.

## Replacement grader switches

A replacement, if step 3 shows a grader defect that a change can fix, takes one switch per decision:
`surrounding_text` (A strict / B embedded), `whitespace` (A ascii / B unicode), `leading_zeros` (A allow / B
forbid), `plus_sign` (A allow / B forbid), `nonascii_digits` (A forbid / B allow). Proposed setting: strict,
ascii, allow, forbid, forbid.
