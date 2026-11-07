# Audit issue: ToyOps `count-server-errors` verifier and scoring script

This file stands in for the issue tracker (offline exercise). Entries are appended in time order; times are UTC
and were read from the clock (`date -u`) when written.

## 2026-11-07T01:09Z: step 1, inputs pinned before the contract

Pinned from `case/MANIFEST.sha256` and `case/TASK.md` only (no grader code or run record read yet).
`sha256sum -c case/MANIFEST.sha256` passed for all 83 files, and no file on disk is missing from the manifest.

| Input | Pin | Source |
|---|---|---|
| Task text | `task/instruction.md` `95e87bff623fd7a0ca0cfc61cfa82fea88de20c9b34b254cce014873ba18f51d` | manifest |
| Sandbox inputs (one task, so these are the "rows"; 110 lines) | `access.log` `8f3e0b36e66103dda03d7368f55792189977b94cce98031a544981ebd4525b04`; `access.log.1` `b33a03646df72341678a79990c96aaa834b0b60feeaa3e269f2348459c6a03c1`; `access.log.2.gz` `ec9beb05ec3f9292984f3287eeda6661ad922f5319888c0a5922e0b8fb7ae826` | manifest |
| Verifier | `verify.sh` `e741df570d2df0a6dc8e6cb103e67714fe8065caf4a015f1fbc53483c7991cae`; `check_answer.py` `add65682459117027d38997270d2f0e9ae972ee8fa24c76472800f2cd943a5e1`; `expected.json` `7eb936f0b49cce342f91c5d24d97f6cfc5b2a93e641e2cf508acedd5ed156926` | manifest |
| Scoring script | `score_trials.py` `a8f72289bf4517f98070d765d8a26e0615ec6a626468a7d1ca7021fcfacdf6d7` | manifest |
| Run records | 36 `trials/tNN/result.json` and their `workspace/` files, by manifest hash | manifest |
| Task description | `TASK.md` `de1ce48597da3e6fe191f166d07043b9d1de21c9fd6c11c276603503b61eb90b` | manifest |
| Agent program | `agentx` 0.4; prompt = fixed system prompt + `instruction.md` unchanged; stops at end of turn without a tool call, 40 steps or 600 s | TASK.md (not stored) |
| Models and decoding | four configurations, 9 trials each, temperature 0.7 | TASK.md |
| Image | tag `toyops/count-server-errors:1.0` (Debian, Python 3.12, bash 5.2, gzip) | TASK.md (not stored) |
| Sandbox network | none | TASK.md, instruction |
| Verifier invocation | `bash /tests/verify.sh` with `WORKSPACE=/workspace TESTS_DIR=/tests PYTHON=python3`, run after the agent stops, in the same container | TASK.md |
| Reference implementation | none exists (ToyOps ships one verifier) | TASK.md |

Local stand-ins for the image (no container here): Python 3.12.10 (`python`; `python3` is not an interpreter on this
host), GNU bash 5.3.15 (Git Bash, cygwin build), gzip 1.14, Windows 11. Python's default text encoding on this
host is cp1252; Python 3.12 in a Debian image with a C or C.UTF-8 locale reads files as UTF-8, so verifier runs
here set `PYTHONUTF8=1` unless a test says otherwise. pytest is not installed and there is no network, so the
fixture tests use `unittest`, with `unittest.expectedFailure` in place of `pytest.mark.xfail(strict=True)` (an
unexpected success makes the run fail, as strict xfail does).

## 2026-11-07T01:17:15Z: step 2, contract recorded before reading any code

- Contract file: `audit/CONTRACT.md`, sha256 `533efaa0e1a3f59a15e476437083fffd2a896f344d2b52a2585d3326654fd4ef`,
  hashed at 2026-11-07T01:17:15Z.
- Counting script it cites: `audit/scripts/count_from_logs.py`, sha256
  `77a39de5154cf753bddf313863984bb9ad99fd67e5249eabefa60c01ff9a182e`. N = 41.
- Decision entries at this time: `D-whitespace`, `D-numeral`, `D-digits`, `D-surrounding-text`, `D-bom`,
  `D-symlink` (table in the contract).
- Read before this point: `skill/`, `case/TASK.md`, `case/MANIFEST.sha256`, `case/task/instruction.md`, the three
  log files. Not yet read: `case/task/tests/*`, `case/score_trials.py`, every `result.json`, every trial workspace.

## 2026-11-07T01:27Z: step 1 continued, inputs that only the code and run records show

Read after the contract hash was recorded: `verify.sh`, `check_answer.py`, `expected.json`, `score_trials.py`, the
36 `result.json` files and the trial workspaces.

- Extraction rule (`verify.sh`): grade `$WORKSPACE/out/answer.txt`; if it is not a regular file and
  `$WORKSPACE/answer.txt` is, grade that instead; if neither is, print `no answer file` and `exit` (finding F1).
- Content rule (`check_answer.py`): decode UTF-8 with `errors="replace"`, `str.strip()` (Python's whitespace set),
  `re.fullmatch(r"[0-9]+")`, then `int(text) == expected`.
- Key: `expected.json` = `{"server_error_count": 41}`, equal to the contract's N = 41.
- Dependencies: bash (`[`, `echo`, `exit` builtins); the interpreter named by `$PYTHON`, which the harness sets to the
  bare name `python3`, so it is looked up on the container's PATH at verification time; Python stdlib `json`, `re`,
  `sys`. Verdict-relevant interpreter behavior: `str.isspace()`'s table and `int()`'s 4,300-digit limit (Python
  3.11 and later). Python 3.12 is named by the image description only.
- Scoring (`score_trials.py`): reward `0.0 if exit_code else 1.0`; score printed as 100 x the mean reward.
- Run record fields: `trial_id`, `task`, `config`, `agent_status`, `agent_error`, `agent_steps`,
  `verifier_exit_code`, `verifier_output`. Not recorded: the image digest, the agent version, the agent's system
  prompt, model revisions, decoding settings, the verifier files' hashes, the user the verifier ran as, and any file
  outside `/workspace`.
- Unverified (cannot fetch offline), with the command that would verify each:
  - image digest: `docker image inspect --format '{{.Id}} {{json .RepoDigests}}' toyops/count-server-errors:1.0`;
  - the image's user and writable directories on PATH:
    `docker run --rm --network none toyops/count-server-errors:1.0 sh -c 'id; for d in $(echo "$PATH" | tr : " ") /tests; do [ -w "$d" ] && echo "writable: $d"; done; python3 -c "import site, sys; print(sys.version, site.ENABLE_USER_SITE, site.getusersitepackages())"'`;
  - the agent's system prompt and version: the `agentx` 0.4 release (`agentx --version`, its prompt template file).
- Symbolic links: this host cannot create them (`os.symlink` fails with WinError 1314; Git Bash `ln -s` copies the
  file). The three symlink fixtures are skipped here and the D-symlink reading of the grader is from the code:
  `[ -f ]` and Python's `open()` follow links.

## 2026-11-07T01:35Z: step 3, first fixture run

58 fixtures (`audit/tests/fixtures.py`), run through `bash verify.sh` as TASK.md describes; table in
`audit/results/fixtures_table_run1.txt`. 55 ran, 3 symlink fixtures skipped. The grader's verdict differs from the
contract label on 14 of the 55:

- F1 (4 fixtures): no answer file, or a directory at the answer path, passes (`exit` after `echo` returns 0).
- F2 (2): an answer at `/workspace/answer.txt` is graded in place of the missing `/workspace/out/answer.txt`.
- F4 (2): `41\x1c` and `\x1f41` pass; `str.strip()` removes U+001C..U+001F, which neither reading of D-whitespace
  counts as whitespace.
- G1 (1): with a `python3` that prints `correct` and exits 0 first on PATH (outside `/workspace`), `37` passes.
- D-whitespace (3): NBSP, U+3000 and NEL around `41` pass (the grader takes reading B).
- D-plus-sign (1): `+41` fails (reading B).
- D-leading-zeros (1): `0`x4999 + `41` fails, through an uncaught ValueError (finding F5), which reading B matches.

## 2026-11-07T01:39:53Z: replacement grader frozen before the step 5 panel

`audit/scripts/replacement_verifier.py` sha256 `3d5514cbe416431d5626b47aa9bb30637ea7b31273b1461497564a201f210562`.
It was written from the contract and the fixtures, before any panel run; the panel does not change it, so all 36
stored trials are held out from its development. (The stored trials were read in step 1, before the replacement was
written; its decision switches come from the contract table, not from the trials.)

## 2026-11-07T01:42Z: contract change recorded (made at 01:27Z)

`D-numeral` was split into `D-leading-zeros` and `D-plus-sign` after reading `check_answer.py`, which passes `041`
and fails `+41`, so one switch could not reproduce or measure either form. No proposed verdict changed. New
`audit/CONTRACT.md` sha256 `89673366ab6026f7199c3a1e6b6e2ef17d9a31a1656634a07b3abfb8a60d915f`. Decision entries:
`D-whitespace`, `D-leading-zeros`, `D-plus-sign`, `D-digits`, `D-surrounding-text`, `D-bom`, `D-symlink`.

## 2026-11-07T01:47Z: steps 3 to 5, run 2 (tests, panel, fuzz, state enumeration)

Pin checks before and after: `audit/results/pin_checks.log`. Results in `audit/results/`.

- Fixture suite (`audit/tests/test_verifier_fixtures.py`): 133 tests, OK with 14 expected failures and 6 skips (the
  3 symlink fixtures, for the grader and the replacement). The replacement passes all 55 fixtures that run, and each
  decision switch gives the alternative label the fixtures state.
- Scoring suite (`audit/tests/test_scoring.py`): 10 tests, OK with 3 expected failures, all F3.
- Property suite (`audit/tests/test_properties.py`): 14 tests, OK with 6 expected failures (F1 x2, F2, F4 x2, F5).
- State enumeration (`enumerate_states.py`, all 24 file states `verify.sh` branches on): the grader and the
  replacement disagree on 9; 6 are `no answer file` passes (F1) and 3 are passes from `/workspace/answer.txt` (F2).
- Fuzz (`fuzz_check_answer.py`, 3,000 generated answer files, seed 20261107; counts depend on the generator): 2,918
  agree; 13 grader passes that no reading allows (all hold U+001C..U+001F, F4); 22 grader passes explained by
  `D-whitespace` B; 2 grader fails explained by `D-plus-sign` B; 45 grader fails explained by `D-leading-zeros` B,
  all through the 4,300-digit ValueError; 142 uncaught ValueError exceptions in all (F5). One exception affects one
  trial only: each trial runs its own verifier process.
- Panel (`panel.py`, the 36 stored trials): rerunning `verify.sh` reproduces all 36 stored exit statuses and outputs.
  The grader passes 20 trials and the replacement (proposed readings) 15; they disagree on t12, t14, t21, t29 and
  t35, all grader passes. No stored trial has a null `verifier_exit_code`. Scored coverage 36/36 for every grader.
  Only `D-surrounding-text` changes a stored verdict (t09, t17).

Incident: the post-run pin check found `case/task/tests/__pycache__/check_answer.cpython-312.pyc`, written when the
property and fuzz scripts imported `check_answer.py` in-process. No pinned file changed, and `verify.sh` runs
`check_answer.py` as a script, which never reads that cache, so no verdict depended on it. Removed at 01:49Z; both
scripts now set `sys.dont_write_bytecode`; the pin check after removal passed.

## Findings (status at 2026-11-07T01:50Z)

| Id | Stage | Defect | Stored verdicts affected |
|---|---|---|---|
| F1 | `verify.sh`, missing file | `exit` after `echo "no answer file"` returns 0, so a missing answer file (or a directory there) passes | 3/36 (t14, t21, t29), all false passes |
| F2 | `verify.sh`, extraction | falls back to `/workspace/answer.txt` when `/workspace/out/answer.txt` is not a file | 2/36 wrong (t12, t35); t23 graded from the wrong file |
| F3 | `score_trials.py`, reward | `0.0 if exit_code else 1.0` gives reward 1 to a null or missing `verifier_exit_code` | 0/36 (no null in the records) |
| F4 | `check_answer.py`, whitespace | `str.strip()` also removes U+001C..U+001F, so `41\x1c` passes | 0/36 |
| F5 | `check_answer.py`, comparison | `int()` raises ValueError above 4,300 digits (uncaught; exit 1) | 0/36 |
| G1 | grading environment | the verifier runs in the agent's container and calls `python3` through PATH; whatever the agent left there decides the verdict | not measurable: snapshots hold only `/workspace` |
| G2 | run records | image by mutable tag, agent prompt and build, model revisions and verifier hashes not recorded | all 36 records |

## 2026-11-07T01:50:37Z: step 6 gate, recorded before any review

The step 7 recommendation is "fix the verifier and the scoring script, with the replacement's verdicts as the target".
It holds if (a) the replacement passes every fixture that runs on the evaluation host, (b) scored coverage is 36/36,
and (c) a blinded review gives the replacement a lower error rate than the current verifier, with a 95% paired
bootstrap interval that excludes zero. If the consensus sides with the current verifier on 3 or more of the 5
disagreement cases, the recommendation becomes "fix F3 to F5 and G1 to G2 only, and send the missing-file and
wrong-path rules to the maintainers as decision entries". If the consensus contradicts both graders on 3 or more of
the 36 cases, the contract is revised before any recommendation.

## 2026-11-07T01:53:31Z: step 6.1 to 6.3, sample drawn and frozen; reviews not run

Drawn by `audit/scripts/draw_sample.py` (seed 20261107) from `audit/results/panel.json`. Population: the 36 stored
trials, one `answer-file` verdict each. Strata (current verifier vs replacement, proposed readings): disagree, 5 of
5 sampled; agree, 31 of 31 sampled (a census of both strata). Held out: all 36 trials (the replacement was frozen at
01:39:53Z, before the panel, and is unchanged). Batches show an opaque case id, the requirement (README rule 1),
the reference answer (41), the prompt, and every file the trial left under `/workspace`, with exact escapes; no
source model, agent status, verifier output or verdict.

sha256 of the frozen files (`audit/frozen/round1/`), written before any review:

| File | sha256 |
|---|---|
| `cases.jsonl` (the case list) | `2021474d2f785eb67cbfa37cc5631008d2b7e328d2e10dfcbb5fe304edbcd2ef` |
| `keys.jsonl` (trial, configuration, stratum, verdicts) | `f5346b8f88d8fddd6df8eaf3cf7e417ef27e427cbf283a256775d5ade59e450b` |
| `strata.json` | `123819f70f6f55d7feeb31fa4c064956a8a67860e52213cfa71ec663f10d1e79` |
| `batch_A.md` | `dd8caa40102f424980021fc59f18928e30d886242157208174a852d73a780b66` |
| `batch_B.md` (same cases, another seeded order) | `722a9fd0305db48b4e568dd1a7c414fabd3066abf16f41465e80f641e849fd40` |
| `reviewer_prompt_A.txt` | `d7730ca72536158e172f9a867f70894ce08896aa7f322952baa0ab932eb255a0` |
| `reviewer_prompt_B.txt` | `9be7293206ce9692503ecfdea585bf386df734063bb2cc96a3a777e854af771b` |
| `show_case.py` (helper that prints a case's files) | `6e8350308d7c838ff3ecfb0830f74efec9d85ef9352cd93ed67fa7e19191f2ee` |

Step 6.4 and 6.5 (two reviewer runs, consensus, error rates, kappa) were not run: this exercise cannot start
subagents. No `reviews_*.jsonl` exists.

## 2026-11-07T02:00Z: run 3 and step 7

- Run 3 (01:49Z to 01:52Z, after the `__pycache__` fix): the property suite again passed with its 6 expected failures;
  the fuzz rerun wrote a byte-identical `fuzz_check_answer.json`; the scoring robustness probe and
  `repro_findings.sh` ran. Pin checks before and after passed, and `case/task/tests/` holds only its three files.
- Scoring probes (observations, not findings): a trial folder without `result.json` is skipped without notice; one
  truncated record or one null `config` stops the whole run with no scores; the score is printed as 100 x the mean.
- Every command block in `AUDIT.md` was run as written from an empty `audit/tmp/repro` at 01:59Z and printed the
  output the report states.
- Step 7 report: `audit/AUDIT.md`, sha256 `6f282b2ea59a2db2dab61d4b46d50aeace2d26148186eb42f15f8cf31988290c`.
  Recommendation: fix the grader (F1 to F5, G1, G2), provisional until the frozen sample is reviewed.
- Steps run: 1, 2, 3, 4 (no reference exists), 5 (stored trials only), 6.1 to 6.3 (drawn, frozen, rendered),
  7. Not run: 6.4 and 6.5 (no subagents), new responses and configuration reruns (no compute).
- Final pin check (02:00:11Z): manifest 83 files OK.

Final sha256 of the audit's code and tests:

| File | sha256 |
|---|---|
| `CONTRACT.md` | `89673366ab6026f7199c3a1e6b6e2ef17d9a31a1656634a07b3abfb8a60d915f` |
| `scripts/replacement_verifier.py` | `3d5514cbe416431d5626b47aa9bb30637ea7b31273b1461497564a201f210562` |
| `scripts/grader_runner.py` | `ac8feb586d2686ad37a8b1d547f8bd160b238468115a6b9e4e8cfb627bbcb433` |
| `scripts/count_from_logs.py` | `77a39de5154cf753bddf313863984bb9ad99fd67e5249eabefa60c01ff9a182e` |
| `scripts/panel.py` | `e3b40432f629cf25bc4c62f54ee91240ec5d44e0fc3736938f964e7c729e5c2f` |
| `scripts/fuzz_check_answer.py` | `8e9b9935ceede4a1cdf75e48c268628747d9bfa46698d2209826dac68e93a914` |
| `scripts/enumerate_states.py` | `a360610ca1c64c636a06f3f17b6956606146752f7742d2ea265cceeb8177d54e` |
| `scripts/draw_sample.py` | `a6e6bc26c89069a80742e1bfdba8f55fd1faf288ddd8f19d1234855ceda3d9a9` |
| `scripts/probe_scoring_robustness.py` | `da2381d16081b36d2f1c908d6f486154cac8af09b4d8988cf90985e9a5e8fc4f` |
| `scripts/repro_findings.sh` | `7b8ef3cb7209fbc52e2817bdb362ef738ba659a6dbd07c168d4a9f0c3a8902fb` |
| `scripts/check_pins.py` | `046a4968dd0cf3b38276cb0e7634b0063a3ac5cd368015878341db688f97057d` |
| `tests/fixtures.py` | `abc211bbb9515a3b836d217252ef5624dd8e1224459b5d6012f0595ece66de1a` |
| `tests/test_verifier_fixtures.py` | `bb12a452fd49f85feb5c82ae7314aed96510c0f82a98455fd0fb949936119731` |
| `tests/test_scoring.py` | `30d91499bef2c64f6264666ac50f3524f3ea6d46279cc1c02565795574a032e9` |
| `tests/test_properties.py` | `d37f90a11daa2814a656a3fbf14721f8f2edc084ca24c95735770fa8df32fc08` |
