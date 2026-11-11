# Audit record: ToyOps `count-server-errors` verifier and `score_trials.py`

Offline stand-in for the issue the skill asks for (there is no issue tracker in this exercise). Entries are
appended in order; times are UTC and were read with `date -u` in the step that wrote them.

## Step 1. Pinned inputs (recorded 2026-11-11 01:46 UTC, before any contract or code was read)

Source of every value: `case/TASK.md` (the task's README excerpt and harness description) and
`case/MANIFEST.sha256`. At this point no grader code (`verify.sh`, `check_answer.py`, `score_trials.py`),
no `expected.json` and no `result.json` had been opened.

| Input | Pinned value | Source |
|---|---|---|
| Case manifest | `MANIFEST.sha256`, sha256 `16e509fd04426690b42ef5a8fe037e04100299363b360fafcac77b330d0aaee3`; `sha256sum -c` passes on all 83 listed files | local file |
| Task text the agent sees | `task/instruction.md` (hash below) | manifest |
| Verifier | `task/tests/verify.sh`, `task/tests/check_answer.py`, `task/tests/expected.json` (hashes below); run as `bash /tests/verify.sh` with `WORKSPACE=/workspace`, `TESTS_DIR=/tests`, `PYTHON=python3` | manifest, TASK.md |
| Scoring script | `score_trials.py` (hash below) | manifest |
| Input logs | the three files of `task/environment/logs/` (hashes below), mounted read-only at `/workspace/logs` | manifest, TASK.md |
| Stored trials | 36 `trials/tNN/result.json` and their `workspace/` trees (hashes in the manifest) | manifest |
| Agent program | `agentx` 0.4, fixed system prompt (not stored), instruction sent unchanged as the first user message; stops at end of turn without a tool call, after 40 steps or after 600 s | TASK.md |
| Model configurations | `agentx+falcon-70b`, `agentx+merlin-32b`, `agentx+osprey-14b`, `agentx+kestrel-8b`, 9 trials each, temperature 0.7 | TASK.md |
| Sandbox image | `toyops/count-server-errors:1.0` (Debian, Python 3.12, bash 5.2, gzip), no network; `/workspace/logs` read-only, rest of `/workspace` writable | TASK.md |
| Harness | copies `task/tests/` to `/tests` after the agent stops (any status); stores exit status as `verifier_exit_code` (null if the container was lost) and output as `verifier_output` | TASK.md |

Full hashes of the grader-relevant files, copied from the manifest:

```text
95e87bff623fd7a0ca0cfc61cfa82fea88de20c9b34b254cce014873ba18f51d  task/instruction.md
8f3e0b36e66103dda03d7368f55792189977b94cce98031a544981ebd4525b04  task/environment/logs/access.log
b33a03646df72341678a79990c96aaa834b0b60feeaa3e269f2348459c6a03c1  task/environment/logs/access.log.1
ec9beb05ec3f9292984f3287eeda6661ad922f5319888c0a5922e0b8fb7ae826  task/environment/logs/access.log.2.gz
e741df570d2df0a6dc8e6cb103e67714fe8065caf4a015f1fbc53483c7991cae  task/tests/verify.sh
add65682459117027d38997270d2f0e9ae972ee8fa24c76472800f2cd943a5e1  task/tests/check_answer.py
7eb936f0b49cce342f91c5d24d97f6cfc5b2a93e641e2cf508acedd5ed156926  task/tests/expected.json
a8f72289bf4517f98070d765d8a26e0615ec6a626468a7d1ca7021fcfacdf6d7  score_trials.py
```

Unverified inputs (cannot be fetched offline):

| Input | Location | Command that would verify it |
|---|---|---|
| `agentx` 0.4 program and its system prompt | agent package, version 0.4 (not stored) | `pip download agentx==0.4 --no-deps`, hash the wheel, and record the system prompt template from the package |
| Image `toyops/count-server-errors:1.0` | container registry tag (a tag, not a digest) | `docker pull toyops/count-server-errors:1.0 && docker inspect --format '{{.Id}} {{.RepoDigests}}' toyops/count-server-errors:1.0` |
| Interpreter, shell and locale inside the image | the image | `docker run --rm toyops/count-server-errors:1.0 sh -c 'python3 -VV; bash --version; locale; python3 -c "import sys,locale;print(sys.getfilesystemencoding(), locale.getpreferredencoding())"'` |
| That the stored trials ran this exact `task/tests/` and logs | no such field in `result.json` per TASK.md | none offline; needs a per-trial record of the task files' hash |

Local substitute environment used to run the verifier offline: Windows 11, Git Bash `GNU bash 5.3.15(2)-release
(x86_64-pc-cygwin)`, `Python 3.12.10`, `gzip 1.14`. Differences from the image (bash 5.3 vs 5.2, Cygwin vs
Debian, default text encoding) are noted where they could matter.

Skill files used: `skill/SKILL.md` `f29d849c181c1a06e0ebe3a94437d68ef0bfd11c48c78fbb62cd73ba93f12f95`,
`skill/references/ifbench.md` `4f36a6a5e2b378353b284de848703244553e922e784cbb8c5780f3e0dfc7ac93`,
`skill/references/reviewer-prompt.md` `02776f1776ab118fb5452a7ea2624eee32c76cd80f177031aa64798af3e64752`.
`skill/references/validation.md` is not provided in this run.

## Step 2. Contract recorded (2026-11-11 01:47:50 UTC, before any grader code was read)

`audit/CONTRACT.md` sha256 `bd6b9d96861c58d6c356463c76c2efc4fb4dc4ba69f60c3a0bb65d36f6357b1f`.

Contents in brief: correct count 41 (20 + 17 + 4), with the three data traps (a space inside one quoted request,
the gzip file, byte counts starting with 5); check V (verifier verdict per trial) and check S (reward and score);
five decision entries: `D-surrounding-text`, `D-whitespace`, `D-leading-zeros`, `D-plus-sign`,
`D-nonascii-digits`. Later changes to the contract are logged below with their reason.

## Step 1, continued: inputs that only the code shows (recorded 2026-11-11 01:59 UTC, after the contract hash)

- `verify.sh` grades `$WORKSPACE/out/answer.txt`, and when that is not a regular file but `$WORKSPACE/answer.txt`
  is, grades `$WORKSPACE/answer.txt` instead. It runs `"$PYTHON" "$TESTS_DIR/check_answer.py" ANSWER
  "$TESTS_DIR/expected.json"` without `-I`.
- Extraction rule (`check_answer.py`): read as UTF-8 with `errors="replace"`, Python `str.strip()` (Python's
  whitespace set, which includes U+001C to U+001F, U+0085, U+00A0, U+3000), then `re.fullmatch(r"[0-9]+")`,
  then `int(text) == expected`. `int()` is subject to Python 3.12's 4,300-digit limit for string conversion.
- Expected value: `expected.json` = `{"server_error_count": 41}`, equal to the count recomputed from the logs
  under the contract (test `audit/tests/test_inputs.py`).
- Reward rule (`score_trials.py`): `0.0 if verifier_exit_code else 1.0`; denominator = every `trials/*/result.json`.
- Dependencies: standard library only (`json`, `re`, `sys`, `os`, `collections`); bash; no data files.
- Stored records: all 36 `result.json` hold the 8 fields TASK.md lists; none has `verifier_exit_code` null.
  Agent status: 31 `completed`, 2 `error` (t14, t21), 3 `timeout` (t05, t15, t29). No record stores the image
  digest, the agent's system prompt, or a hash of the task files it ran.

## Step 3. Fixtures (recorded 2026-11-11 01:59 UTC)

Tests: `audit/tests/test_fixtures.py` (verifier and scorer fixtures, current grader and replacement),
`audit/tests/test_properties.py` (step 4 metamorphic tests), `audit/tests/test_inputs.py` (pinned hashes and the
expected count). Run: `python -B -m unittest discover -s audit/tests -p "test_*.py"` from the case's parent
directory. pytest is not installed offline, so the expected failures use `unittest.expectedFailure`, which is
strict (an unexpected success fails the run). Verifier fixtures run `bash verify.sh` with `WORKSPACE`,
`TESTS_DIR`, `PYTHON` set, as the harness does, on Git Bash and Python 3.12 with `PYTHONUTF8=1`.

48 verifier fixtures and 11 scorer fixtures; ids are the check name plus 16 hex digits of the state's sha256.
Wrong verdicts of the current grader:

| Fixture id | State | Contract | Current | Classification |
|---|---|---|---|---|
| `verifier:4f53cda18c2baa0c` | empty sandbox | fail | pass (exit 0, "no answer file") | F1 |
| `verifier:4a6140effe24c8de` | empty `out/` | fail | pass | F1 |
| `verifier:2d4a6990d3419443` | only `tmp/notes.txt` | fail | pass | F1 |
| `verifier:5155d908af56d922` | `tmp/answer.txt` = `41\n` | fail | pass | F1 |
| `verifier:405ef7ce62fe6965` | `out/answer.txt` is a directory | fail | pass | F1 |
| `verifier:64d7e51ce10deb36` | `/workspace/answer.txt` = `41\n` | fail | pass ("correct") | F2 |
| `verifier:61bb4e84a6e4f510` | same, with empty `out/` | fail | pass | F2 |
| `score:766bd63355dc5bd6` | one trial, `verifier_exit_code` null | reward 0 | reward 1 | F3 |
| `score:9e2325ba76fe4090` | one trial, field missing | reward 0 | reward 1 | F3 |
| `score:8729d0b68ca87c05` | exit codes 0, 1, null | 33.3 | 66.7 | F3 |
| `verifier:ac969af12c767179` | 5,000 zeros then `41` | pass | fail (ValueError traceback, exit 1) | decision: `D-leading-zeros` |
| `verifier:556ea5af0f0bc4ce` | `41` + U+00A0 | fail | pass | decision: `D-whitespace` or `D-surrounding-text` |
| `verifier:ae41aadcd7ee7384` | U+3000 + `41` | fail | pass | decision: `D-whitespace` or `D-surrounding-text` |
| `verifier:131d469371aec69c` | `41` + U+0085 | fail | pass | decision: `D-whitespace` or `D-surrounding-text` |
| `verifier:f20550d4ff9fccc4` | `41` + U+001F | fail | pass | decision: `D-surrounding-text` only |
| `verifier:ca11c01c5ebfb258` | U+001C + `41` | fail | pass | decision: `D-surrounding-text` only |

Contract change log: none. Classification change, 01:58 UTC: the two U+001C/U+001F fixtures were first filed as a
finding (no reading of `D-whitespace` makes U+001C..U+001F whitespace); re-filed as decision-dependent because the
other reading of `D-surrounding-text` makes their pass correct, and SKILL.md step 3 counts such a verdict as a
decision. They are reported as observation O1.

### Findings (unambiguous defects)

- **F1** `verify.sh`, missing answer: the branch `echo "no answer file"; exit` exits with echo's status, 0, so a
  trial without `/workspace/out/answer.txt` (and without `/workspace/answer.txt`) passes. Contract: README rule 1,
  "A trial whose `/workspace/out/answer.txt` is missing ... fails".
- **F2** `verify.sh`, answer location: falls back to `/workspace/answer.txt` when `out/answer.txt` is missing.
  Contract: README rule 1 and the instruction name only `/workspace/out/answer.txt`.
- **F3** `score_trials.py`, reward mapping: `0.0 if exit_code else 1.0` gives reward 1 when
  `verifier_exit_code` is null or absent (and for `false`, `0.0`, `[]`). Contract: README rule 2, "A trial whose
  verifier did not run (`verifier_exit_code` null) fails".
- **G1** (protocol, unpinned inputs): the image is pinned by a mutable tag (`toyops/count-server-errors:1.0`), and
  neither the image digest, the `agentx` system prompt nor a hash of the task files is stored per trial.
- **G2** (protocol, unverified): the verifier runs in the container the agent controlled, with `python3` from
  `PATH` and without `-I`. Whether the agent could write outside `/workspace` (interpreter, site-packages, its
  home directory's user site) is not recorded; if it could, it could set the verdict.

### Replacement grader (frozen 2026-11-11 01:59 UTC, before it graded any stored trial)

Written from the contract, one switch per decision entry (environment variables `D_SURROUNDING_TEXT`,
`D_WHITESPACE`, `D_LEADING_ZEROS`, `D_PLUS_SIGN`, `D_NONASCII_DIGITS`; unset = proposed reading).

```text
0c81039c0052ebc5562a1c16e85cc02024b313d214aab83c0b1e13b638bee5ad  audit/replacement/tests/verify.sh
d7b9af47961d3800356fb33ed74a7d05d4dd622d119b940b3f398dc2016d9bb8  audit/replacement/tests/check_answer.py
7eb936f0b49cce342f91c5d24d97f6cfc5b2a93e641e2cf508acedd5ed156926  audit/replacement/tests/expected.json
5858fcc8c1524d44d89f273d9e55c3a832f06a4388606b1b9f969402ce9e5fcf  audit/replacement/score_trials.py
```

It passes all 48 verifier fixtures, all 11 scorer fixtures, every flipped-reading fixture and every metamorphic
test (186 tests, 19 expected failures, all on the current grader).

Disclosure: the trial files were listed and printed (`audit/scripts/dump_trials.py`) after the contract hash and
before the replacement was written, so its author knew that t12, t23 and t35 wrote `/workspace/answer.txt`. The
replacement adds nothing beyond the contract for those cases (only `out/answer.txt` is graded, as the contract
written before that listing says).

Held-out trials, drawn with `random.Random(20261111).choice` per configuration before the panel run: t08, t14,
t24, t30. They are needed only if the panel prompts a change to the replacement; no such change was made (see
step 5), so step 6 draws from the whole panel.

## Step 4. Stress tests (recorded 2026-11-11 02:02 UTC)

- Reference implementation: none exists (TASK.md names none), so the reference comparison and the reference's
  unit tests are skipped. The grader has no tests of its own, so no grader test encodes a decision.
- Metamorphic tests (`audit/tests/test_properties.py`): 7 ignored edits and 16 forbidden edits, each applied to 4
  passing states. The current grader fails 3 forbidden edits: deleting the answer file (F1), moving it to
  `/workspace/answer.txt` (F2) and moving it to `/workspace/tmp/answer.txt` (F1). It passes every ignored edit
  and the 13 text edits of step 4 (numbered label, bullet, bold, italics, HTML tag, typographic quotes,
  typographic apostrophe, punctuation after the number, a word after it, count plus or minus one). The score
  does not depend on `agent_status`.
- Fuzz (`audit/scripts/fuzz.py 5000 20261111`, output `audit/fuzz_output.txt`, sha256
  `12edb79daeacf2a1e9bf09a2b95f7795953ac075eebfbdd2ec1d8d85c10d694c`): 5,000 random answer files. 139
  `ValueError` exceptions (answers of 4,301 or more digits, all of them leading-zero runs before `41`); 874
  disagreements with the replacement, each removed by one decision switch (`D-leading-zeros` 139,
  `D-surrounding-text` 247, `D-surrounding-text` or `D-whitespace` 488); none that no reading explains. A
  verifier exception exits 1 and fails only that trial; it does not stop other trials.
- Sandbox layouts: of 64 combinations of `out/answer.txt`, `/workspace/answer.txt`, `tmp/answer.txt` (absent,
  41, 37, directory), the current grader is wrong on 24 (F1, F2), the replacement on 0.
- Scorer: `verifier_exit_code` null or absent gives reward 1 (F3); so do `false`, `0.0` and `[]`, which the
  harness does not produce. One truncated `result.json`, or one without `config`, stops the whole scoring run
  with a traceback and no table (robustness note R1; no stored record is malformed).
- Content-free states: the empty sandbox passes (F1); an empty file, a whitespace-only file, 50 repeated lines of
  `41` and a restatement of the instruction all fail.

## Step 5. Panel from the stored trials (recorded 2026-11-11 02:02 UTC)

No compute: the 36 stored trials are the panel, and no new trials were generated. Script
`audit/scripts/panel.py` (sha256 `192eb903bafa226db6d9585f121bbdc2c622e550e3264d0b9c2bd652bd13ea82`), output
`audit/panel_output.txt` (`b21d28b3b1554be61850fbe8447f9e9798395e4b6d1bc2fe4e03c9a4b59bd18f`), verdicts
`audit/panel/panel_verdicts.json` (`1c24c3e93f01b5c19e85e7915fedd421bf86acf81d276e9fdbd9b6241e1871ed`). The case
manifest matched before and after the run.

- The offline rerun of `verify.sh` reproduces all 36 stored exit statuses.
- Stored records show: 3 trials with no answer file anywhere (t14 error, t21 error, t29 timeout), all with
  `verifier_exit_code` 0 and output "no answer file"; 3 trials that wrote `/workspace/answer.txt` (t12 and t35
  hold `41`, t23 holds `37`); no null exit code.
- Disagreements between the current grader and the replacement: 5 of 36 (t12, t14, t21, t29, t35), all current
  passes that the contract fails. False rewards: 5 of 20 passes (25%, Clopper-Pearson 95% [8.7, 49.1]).
- Scored coverage: 36 of 36 for both.
- Scores (current, replacement, change, paired bootstrap 95% over trials): falcon-70b 77.8, 77.8, +0.0;
  merlin-32b 77.8, 55.6, -22.2 [-55.6, +0.0]; osprey-14b 33.3, 22.2, -11.1 [-33.3, +0.0]; kestrel-8b 33.3, 11.1,
  -22.2 [-55.6, +0.0]. All trials: 55.6 to 41.7, -13.9 points [-25.0, -2.8] (bootstrap stratified by
  configuration). The current grader ties falcon with merlin and osprey with kestrel; the replacement orders
  them falcon > merlin > osprey > kestrel.
- Decisions on the panel: only `D-surrounding-text` moves a trial (t09 `41 server errors`, t17 `Total 5xx: 41`);
  its other reading raises falcon-70b to 88.9 and merlin-32b to 66.7. The other four decisions move nothing.
- Not run: a rerun of a configuration with identical settings (needs compute); a replacement change from the
  panel (none was made, so the held-out set t08, t14, t24, t30 was not needed).

## Step 6. Pre-registered decision rule (recorded 2026-11-11 02:02 UTC, before the sample was drawn)

The recommendation is "fix the grader" (adopt the replacement's changes: F1, F2, F3). It stands if the blinded
review shows: the replacement passes every fixture (true now), scored coverage is complete (true now), and the
replacement's error rate is lower than the current grader's with a paired 95% interval that excludes zero. If
the consensus instead agrees with the current grader on the disagreement cases, so that the paired interval
includes zero or favors the current grader, the recommendation becomes "admit the grader" for F1 and F2 and the
contract is revisited with the maintainers.

## Step 6.1 to 6.3. Sample drawn, frozen and rendered (recorded 2026-11-11 02:04 UTC; no review has started)

Script `audit/scripts/draw_sample.py 20261111` (sha256
`526b9fddcca6156f35cb11146972b47915a2d820aec7821a1c98001c2d3c357c`), seed 20261111. Population: the 36 stored
trial verdicts of step 5. Strata: current grader and replacement disagree (5) or agree (31). Both strata are
small, so the sample is a census: all 5 and all 31. The whole panel is used because the replacement was frozen
before it graded any trial and was not changed afterwards (held-out set t08, t14, t24, t30 not needed).

Freeze record (sha256 of the case list):

```text
81357f5204bd1c389a68dd4ba5efbddddcb55ed11365a20850114641f6c3e6d9  audit/frozen/keys/round1_case_list.json
```

Other frozen files:

```text
948126056c704f342dff231167b1e89d0ef4a4aac9dc17cec661dce0a6bca18c  audit/frozen/keys/round1_keys.json
202e41bd34987b6a77f85b07cbcb4c6d33f4c74846988069b5563cb7e877f6a2  audit/frozen/round1/batch_A.md
380fae5e8ca912b50f977a554ac453f3fd82aa9c72bc86566dc7e945af797efb  audit/frozen/round1/batch_B.md
cb8ef350dc3347f0e895207d84f9405a4dc59f81cf7f817cb73d3175c60895a4  audit/frozen/round1/cases.json
00942d6fc156c19c24570f98f4981007de5993c84c0ec8c66e387a9766817c6a  audit/frozen/round1/logs_decompressed.txt
84b32471e39041dda15204b9e6f499e8e7124fd4a4a3a8d9091af9db7ef6f241  audit/frozen/round1/reviewer_prompt_A.txt
d61ba60c3e44b644ab2b5194509cbc3e58017fb0c8ff1c8e5d2fc53c39821e99  audit/frozen/round1/reviewer_prompt_B.txt
318da5cc70223746aeeba7501c40fc39467979d832781ed3d56cec1d92a5710f  audit/frozen/round1/show_case.py
```

Each case in a batch shows an opaque id (`C` plus 4 hex digits), the requirement (instruction plus README rule 1
and the reference count 41), the prompt, and every file the trial left under `/workspace`, as a bytes literal and
between begin and end markers. No source model, agent status, grader verdict or stratum appears in the
reviewers' folder `audit/frozen/round1/`; the keys and the case list are in `audit/frozen/keys/`. Batch B holds
the same cases as batch A in a different seeded order.

## Step 6.4 and 6.5. Not run

This exercise allows no subagents, so no reviewer labeled the sample, and no blinded error rate, kappa or
disputed-case list exists. `reviews_A.jsonl` and `reviews_B.jsonl` do not exist.

## Counterexample states cited by the report (recorded 2026-11-11 02:10 UTC)

Created by `audit/scripts/make_repro.py` (sha256 `90c3fd8ae4b0f6153a21e99926881458a2c9a73bb3f700bcebb8e5dc5e87a760`).
`audit/repro/F1_no_answer/` holds only the empty directory `out/`.

```text
040316eca5e77dbb2212c1efe8b81cb23bc67ce0ac8cb5c9d902d98bd45ddfa1  audit/repro/F2_root_answer/answer.txt
58532d4b8f8769b10ff1e5d2a9dade2546023f3bfddee4ac52b2b573c639ffc3  audit/repro/F3_null_trials/t1/result.json
0a8f8bac5b356318f64bfad703100b21a6aed823f5124894eab6a55f83f1b1cf  audit/repro/O1_unit_separator/out/answer.txt
da73200118e9fa06f3b76b33735bc013d7469f85ceca0a61a3edb3ba3accb7a1  audit/repro/O2_nbsp/out/answer.txt
c52364374b0a46cebf45a78713eedaac2033e71eb27590567774f6c62cd324b5  audit/repro/O3_leading_zeros/out/answer.txt
```

## Step 7. Report (recorded 2026-11-11 02:10 UTC)

Report: `audit/AUDIT.md` (sha256 `ae3144e0f4db4841361309d41689f0a87c135180c5d83ac365dc11a4fc5ea816`).
Recommendation: fix the grader (F1, F2, F3; G1 and G2 as protocol changes), provisional on the blinded review
that has not run. Final checks at 02:10 UTC: `python -B -m unittest discover -s audit/tests -p "test_*.py"` ran
186 tests, OK with 19 expected failures; `audit/scripts/fuzz.py 5000 20261111` and `audit/scripts/panel.py`
reproduce their saved outputs byte for byte; `audit/scripts/check_report_commands.sh` (sha256
`56728c15b83d8dc1902480a33f4d57f704975782ec04831bfe47285ecb5ea1ae`) ran every command in the report and each
printed what the report says; the case manifest still matches and no `__pycache__` exists under `case/`.
