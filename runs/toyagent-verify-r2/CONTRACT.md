# Contract: ToyOps `count-server-errors` (verifier and scoring script)

Written from the text the agent sees (`case/task/instruction.md`), the scoring rule quoted from the ToyOps README in
`case/TASK.md`, and the sandbox input files (`case/task/environment/logs/`), before reading `verify.sh`,
`check_answer.py`, `expected.json`, `score_trials.py` or any `result.json`. Later changes are appended in the
"Changes" section at the end, each with its reason.

## C0. The correct count N

- A request is one line of `access.log`, `access.log.1`, or the decompressed `access.log.2.gz` ("Each line is one
  request"). All three files count.
- Its status code is the field right after the quoted request, `"..." <status> <bytes>`. Fields inside the quotes
  never count, even when the request text contains a space (`access.log.1` line 31, `"GET /api/search?q=red shoes
  HTTP/1.1" 503 167`). The response-size field never counts (sizes 512, 5120, 580 and 59000 occur on lines whose
  status is 200).
- A server error is a status code from 500 to 599 inclusive.
- Computed by `audit/scripts/count_from_logs.py`: all 110 lines parse; N = 41 (20 in `access.log`, 17 in
  `access.log.1`, 4 in `access.log.2.gz`). Reference counts of common wrong methods: 37 (the `.gz` file skipped),
  40 (the 9th whitespace field, which misreads the `red shoes` line), 45 (` 5[0-9][0-9]` anywhere in the line).

## C1. Answer check, per trial (the verifier)

Graded state: the file at `/workspace/out/answer.txt` in the trial's final sandbox, and nothing else. The verdict
does not depend on `agent_status`, on the agent's messages, or on any other file the agent left; the verifier does
not execute, source or import anything the agent wrote.

- Missing file: fail. This includes an answer written to any other path, such as `/workspace/answer.txt`, and a
  directory at the answer path.
- Empty file (0 bytes): fail. A file of whitespace only: fail (it holds no count).
- Otherwise remove the whitespace at both ends. Space, tab, LF and CR always count as whitespace, so a final
  newline, several final newlines, a leading newline and a CRLF ending are all ignored. Other characters:
  `D-whitespace`.
- Pass if and only if what remains is a decimal integer whose value is N = 41, written in ASCII digits.
  - Fail: another value (40, 42, 37, 45, 0); hexadecimal (`0x29`); a fraction or exponent (`41.0`, `4.1e1`);
    digit separators or inner whitespace (`4_1`, `4,1`, `4 1`); words (`forty-one`); two lines (`41\n41`); any
    byte that is not whitespace, such as NUL, anywhere in the file (`41\0`, `4\0` `1`).
  - Leading zeros (`041`): `D-leading-zeros`. A plus sign (`+41`): `D-plus-sign`.
  - Non-ASCII decimal digits (`٤١`, full-width `４１`): `D-digits`.
  - Other text around the integer (`41 errors`, `count: 41`): `D-surrounding-text`.
  - A byte-order mark or a UTF-16 encoding of `41`: `D-bom`.
  - A symbolic link at the answer path: `D-symlink`.
- The verifier exits 0 when the trial passes and with a nonzero status when it fails. An error inside the verifier
  (an exception, a missing tool) must end in a nonzero status, never 0.

## C2. Trial verdict (README rule 2)

- The verifier runs on the final sandbox of every trial, whatever `agent_status` is (`completed`, `error`,
  `timeout`). Its exit status alone decides: 0 passes, any other status fails, and `verifier_exit_code: null` (the
  verifier did not run) fails.
- A trial whose agent erred or timed out but left a correct answer file passes.

## C3. Reward and score (README rule 3)

- Reward 1 for a pass and 0 for a fail.
- A configuration's score is its mean reward over all of its trials: every trial with that `config` enters the
  denominator, including trials with `agent_status` `error` or `timeout` and trials with a null
  `verifier_exit_code`. With 9 trials per configuration, score = passes / 9.
- The script prints, per configuration, the number of trials, the number of passes and the score; every stored trial
  gets a reward (scored coverage 36 of 36).
- The agent has no network access (sandbox rule); the score does not test it.

## Decision entries (the text allows two verdicts)

| Id | Question | Reading A | Reading B | Proposed |
|---|---|---|---|---|
| `D-whitespace` | Which characters besides space, tab, LF and CR are "whitespace around the content"? | ASCII whitespace only, adding VT and FF (POSIX `[:space:]`): `41\x0b` passes, `41 ` fails | Unicode whitespace too (NBSP, U+3000, NEL): `41 ` passes | A: a count file is plain ASCII text, and only the README's whitespace is ignored |
| `D-leading-zeros` | Do leading zeros keep the content "a decimal integer" with value N? | Value reading: `041` passes | Canonical reading: `041` fails | A: `041` is a base-10 integer whose value is the count |
| `D-plus-sign` | Does a plus sign keep the content "a decimal integer" with value N? | Value reading: `+41` passes | Canonical reading: `+41` fails | A: `+41` is a base-10 integer whose value is the count |
| `D-digits` | Do non-ASCII decimal digits count as a decimal integer? | No: `٤١` fails | Yes: `٤١` passes (Unicode category Nd) | A: the instruction asks for a decimal integer in a text file read by tools; ASCII digits are the plain reading |
| `D-surrounding-text` | May other text surround the integer? | No: `41 errors` and `count: 41` fail | Yes, if the file holds one integer and it is N | A: the README ignores only whitespace around the content |
| `D-bom` | Does a byte-order mark or UTF-16 encoding change the content? | Yes: the bytes are the content; `﻿41` (UTF-8 BOM) and UTF-16 `41` fail | No: decode by the BOM; both pass | A: a BOM is not whitespace, and the README ignores only whitespace |
| `D-symlink` | Does a symbolic link at the answer path hold the content of its target? | Yes: grade what reading the path returns | No: only a regular file counts | A: the path "holds" what any reader of it gets; a link to a file the agent did not write is examined separately |

## Changes

- 2026-11-07T01:27Z, after reading the verifier code: `D-numeral` split into `D-leading-zeros` and `D-plus-sign`.
  Reason: `check_answer.py` passes `041` and fails `+41`, so one switch could neither reproduce its verdicts nor
  measure each form's effect. No proposed verdict changed.
