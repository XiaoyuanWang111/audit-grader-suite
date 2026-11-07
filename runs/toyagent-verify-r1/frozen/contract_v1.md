# Contract: ToyOps `count-server-errors` verifier and scoring

Version 1. Written from the task text only, before reading any grader file
(`task/tests/verify.sh`, `task/tests/check_answer.py`, `task/tests/expected.json`,
`score_trials.py`) and before reading any stored verifier field
(`verifier_exit_code`, `verifier_output`).

Sources: `case/task/instruction.md` (the text the agent sees, identical to the
quote in `case/TASK.md`), the sections "Sandbox and verifier" and "Scoring rule
(from the ToyOps README)" of `case/TASK.md`, and the three input files in
`case/task/environment/logs/`, which the agent also sees.

## Terms

- Trial: one `agentx` run on the task, with its final sandbox.
- Answer file: the path `/workspace/out/answer.txt` in the final sandbox. In
  the stored trials it is `trials/tNN/workspace/out/answer.txt`.
- Content: the answer file's bytes decoded as text.
- Trimmed content: the content with whitespace removed at both ends.
- N: the correct count, defined below.

## The correct count N

The instruction defines the count: the requests (one per line) in
`access.log`, `access.log.1` and `access.log.2.gz` (gzip, so its decompressed
lines) whose status code, "the field right after the quoted request", is a
server error, 500 to 599.

Computed from the pinned log files (sha256 in `case/MANIFEST.sha256`) by
parsing each line as `host ident user [time] "request" status bytes`:

| File | Lines | Status 500-599 |
|---|---|---|
| `access.log` | 40 | 20 |
| `access.log.1` | 40 | 17 |
| `access.log.2.gz` (decompressed) | 30 | 4 |
| Total | 110 | **N = 41** |

All 110 lines parse, all statuses are three digits (500: 10, 502: 15, 503: 7,
504: 9), and no line repeats. Wrong counts a careless method gives, used as
near-miss fixtures:

- 40: whitespace field 9 as the status. Line 31 of `access.log.1` has a space
  inside its quoted request (`q=red shoes`), so its status 503 is field 10.
- 45: any ` 5dd` in the line. Four status-200 lines have a byte count that
  starts with 5 (512 and 5120 in `access.log`, 580 and 59000 in
  `access.log.2.gz`).
- 37: the gzip file left out. 20: `access.log` alone.

## Check `answer` (the verifier, one verdict per trial)

Graded state: the answer file only. Nothing else under `/workspace` changes the
verdict, including `/workspace/answer.txt`, other files in `/workspace/out`,
and files in `/workspace/tmp`. The agent's status (`completed`, `error`,
`timeout`) does not change the verdict of a given final sandbox.

Pass when all hold:

1. The answer file exists and is a file whose content can be read.
2. The trimmed content is a decimal integer whose value is N = 41.

Whitespace (TASK.md rule 1): "Whitespace around the content, including a final
newline, is ignored." Whitespace inside the content is not ignored.

Fail otherwise. In particular:

- The answer file is missing, or is a directory (README rule 1: missing fails).
- The content is empty or only whitespace (README rule 1: empty fails).
- The trimmed content is another integer: `40`, `45`, `37`, `20`, `-41`, `0`.
- The trimmed content has other text: `41 server errors`, `count=41`,
  `Total: 41`, `{"count": 41}`, `41\n41`, `4 1`, `forty-one`.
- The trimmed content is not an integer numeral: `41.0`, `4.1e1`, `0x29`,
  `4_1`, `41,`, `1e1`.

Pass examples: `41`, `41\n`, ` 41 \n`, `\t41\r\n`, `\n\n41\n\n`.

Verifier interface (TASK.md "Sandbox and verifier" and rule 2): the harness
runs `bash /tests/verify.sh` with `WORKSPACE=/workspace`, `TESTS_DIR=/tests`,
`PYTHON=python3`; exit status 0 means pass, any other status means fail. So the
verifier must exit 0 exactly on the pass cases above, and non-zero on every
fail case, whatever the answer file holds (no input may make it exit 0 for a
fail case, and an internal error on a pass case is a wrong verdict).

## Check `reward` (scoring, one reward per trial)

From TASK.md rules 2 and 3:

- Reward 1 when the stored `verifier_exit_code` is the integer 0; reward 0 for
  any other value, for `null`, and when the field is absent.
- `verifier_output` and `agent_status` never change the reward.

## Check `score` (scoring, one score per configuration)

- A configuration's trials are the records whose `config` field names it.
- Score = (sum of rewards) / (number of its trials). Every trial is in the
  denominator: agent status `completed`, `error` or `timeout`, and verifier
  not run (`null`).
- The script prints, per configuration, the number of trials, the passes and
  the score.

## Network

The sandbox has no network. The verifier must not need the network.

## Decision entries (the text allows two verdicts)

### D-integer-form: a sign or leading zeros

Is `+41` or `041` "the count as a decimal integer"?

| Reading | `041\n` | `+41\n` | `41\n` |
|---|---|---|---|
| Canonical: ASCII digits, no sign, no leading zero | fail | fail | pass |
| Base-10 numeral: optional `+`, leading zeros allowed | pass | pass | pass |

Proposed: base-10 numeral. Both strings denote 41 in base 10 and every
standard decimal integer parser (C `strtol(s, 10)`, Python `int`, `test -eq`)
reads them as 41, so the format deviation does not hide a wrong count.

### D-digit-script: decimal digits outside ASCII

Is `٤١` (Arabic-Indic digits) or `４１` (fullwidth digits) a decimal integer?

| Reading | `٤١\n` | `４１\n` |
|---|---|---|
| ASCII digits 0-9 only | fail | fail |
| Any Unicode decimal digit (category Nd) | pass | pass |

Proposed: ASCII only. The task, its file names and its log fields are ASCII,
the sandbox is a Debian shell, and shell tools and `strtol` do not read these
digits.

### D-whitespace-set: which characters are "whitespace"

| Reading | `41 \n` (no-break space) | `　41` (ideographic space) |
|---|---|---|
| ASCII whitespace only (space, `\t`, `\n`, `\v`, `\f`, `\r`) | fail | fail |
| Unicode White_Space characters too | pass | pass |

Proposed: ASCII whitespace, for the same reason as D-digit-script: the rule
exists for final newlines and padding that shell tools add.

### D-encoding: a byte-order mark or UTF-16

| Reading | `EF BB BF` + `41\n` (UTF-8 BOM) | UTF-16LE with BOM `FF FE 34 00 31 00` |
|---|---|---|
| Bytes read as UTF-8 text; a BOM is content | fail | fail |
| Text decoded by its BOM; the BOM is not content | pass | pass |

Proposed: bytes read as UTF-8 text, so both fail. No tool in the Debian sandbox
writes a BOM by default, and the instruction asks for the count as text in a
file that other shell tools read.

## Open questions with no proposal

None at version 1. Later changes are listed below with their reasons.

## Changes

(none yet)
