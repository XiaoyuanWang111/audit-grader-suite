# Audit: ToyOps `count-server-errors` verifier and scoring script

This file stands in for the task's issue (offline exercise: no issue tracker,
repository, research branch, Hugging Face dataset or job launcher). Entries are
added in order; times are UTC, read from the clock when written.

Grader under audit: `case/task/tests/verify.sh`, `case/task/tests/check_answer.py`,
`case/task/tests/expected.json` (the verifier) and `case/score_trials.py` (the
scoring script). Reference implementation: none is named in `case/TASK.md`, so
step 4's reference comparison is skipped.

## Step 1. Pinned inputs (from the run records, TASK.md and the manifest only)

Checked right after the first clock read (2026-11-06T23:58:16Z), written at
2026-11-07T00:04Z. Every file in `case/` matches `case/MANIFEST.sha256`:
`sha256sum -c MANIFEST.sha256` (run from `case/`) reports 83 OK and 0 failures,
and `case/` holds exactly the 83 listed files plus the manifest. The manifest's
own sha256, computed at 00:11Z, is
`16e509fd04426690b42ef5a8fe037e04100299363b360fafcac77b330d0aaee3`.

| Input | Pin | Source |
|---|---|---|
| Task text | `task/instruction.md` sha256 `95e87bff…` (identical to the quote in TASK.md, 0 CR bytes) | manifest |
| Input logs | `access.log` `8f3e0b36…`, `access.log.1` `b33a0364…`, `access.log.2.gz` `ec9beb05…` (one gzip member, no trailing bytes; 40 + 40 + 30 lines) | manifest |
| Verifier | `verify.sh` `e741df57…`, `check_answer.py` `add65682…`, `expected.json` `7eb936f0…` | manifest |
| Scoring script | `score_trials.py` `a8f72289…` | manifest |
| Trials | 36 `result.json` + 46 workspace files, sha256 per file | manifest |
| Agent | `agentx` 0.4, fixed system prompt, first user message = `instruction.md` unchanged, stops at end of turn without a tool call, 40 steps or 600 s | TASK.md only; not stored |
| Models | `agentx+falcon-70b`, `agentx+merlin-32b`, `agentx+osprey-14b`, `agentx+kestrel-8b`, 9 trials each, temperature 0.7 | TASK.md and the `config` field; no model revision, no other decoding setting |
| Image | `toyops/count-server-errors:1.0` (Debian, Python 3.12, bash 5.2, gzip), no network | TASK.md only; a tag, no digest |
| Verifier invocation | `bash /tests/verify.sh` with `WORKSPACE=/workspace TESTS_DIR=/tests PYTHON=python3`, same container, after the agent stops | TASK.md |
| Run records | fields `trial_id task config agent_status agent_error agent_steps verifier_exit_code verifier_output` in all 36 files | `result.json` |

Run-record counts (non-verifier fields; verifier fields not read before the
contract hash): 36 trials, 9 per configuration. Agent status: `completed` 31,
`timeout` 3 (t05, t15, t29), `error` 2 (t14 "context length exceeded", t21
"tool call failed: shell exited with status 137"). t05 and t29 are recorded as
"agent exceeded 600 s wall time" at `agent_steps` 40, the step limit.

Local offline environment used in place of the image: Python 3.12.10 (`python`),
GNU bash 5.3.15 (Git Bash, MSYS) on Windows 11. The image's bash is 5.2.

Unverified inputs (cannot be fetched offline):

| Input | Location | Command that would verify it |
|---|---|---|
| Image content and digest | tag `toyops/count-server-errors:1.0` | `docker image inspect toyops/count-server-errors:1.0 --format '{{.Id}} {{.RepoDigests}}'`; `docker run --rm --network none toyops/count-server-errors:1.0 sh -c 'python3 --version; bash --version; command -v python3; echo $PATH; locale'` |
| Agent program and system prompt | `agentx` 0.4 | `agentx --version` and its packaged system prompt file, sha256 |
| Sandbox user and writable paths outside `/workspace` | not in TASK.md or the records | `docker run --rm toyops/count-server-errors:1.0 sh -c 'id; touch /usr/local/bin/x && echo writable; touch /tests_probe && echo root-writable'` |
| Network setting of each trial | not in the records | the harness's container create options (`docker inspect <container> --format '{{.HostConfig.NetworkMode}}'`) |

## Step 2. Contract

2026-11-07T00:05:19Z. Contract version 1 written to `audit/CONTRACT.md`
before reading any grader file or stored verifier field.
sha256 `eaa1e8e70a8d25f94dcfccbdfe2758a91c8e3647ffc97e84193121789f1cfe3f`
(frozen copy `audit/frozen/contract_v1.md`, same hash).
Correct count from the task text and the pinned logs: N = 41 (20 + 17 + 4).
Decision entries at version 1: D-integer-form, D-digit-script,
D-whitespace-set, D-encoding.

Between 2026-11-07T00:05:39Z and 00:11:32Z (clock reads before and after),
after the contract hash above, read the grader files:
`verify.sh`, `check_answer.py`, `expected.json` (`{"server_error_count": 41}`,
which equals N), `score_trials.py`; then the stored verifier fields.
Pins recorded only after the contract hash: the verifier reads the answer with
`open(path, encoding="utf-8", errors="replace").read().strip()` and accepts
`re.fullmatch(r"[0-9]+", text)` with `int(text) == 41`; `verify.sh` resolves
`$PYTHON` (harness value `python3`) through `PATH` and has no `set -e`;
`score_trials.py` uses only the standard library.

2026-11-07T00:20:32Z. Contract version 2: `audit/CONTRACT.md` sha256
`e8ca88c27866b9027a72fa09946dc33900e7a1594d5a1ac643548196961bf9b6` (frozen copy
`audit/frozen/contract_v2.md`). No verdict of version 1 changes. Changes and
their reasons are listed at the end of the contract: D-integer-form split into
D-leading-zeros and D-plus-sign (the grader treats the two differently, so each
needs a switch); D-leading-zeros has no length limit (Python `int()` raises
over 4,300 digits); D-whitespace-set names the Unicode White_Space property,
under which U+001C-U+001F are not whitespace (Python `str.strip()` removes
them).

Replacement grader frozen before it graded any stored trial (so every stored
trial is held out from its development; it was built from the contract and
checked only on fixtures):
`audit/replacement/replacement_verifier.py` sha256
`520916a63b420c48eb9f7fe284a9c9ac597db53cf4e120f8227c38ca48aab942`,
`audit/replacement/replacement_scoring.py` sha256
`ebbe0bdf158d17785bd1464cd39073e47747618eb420e59f540d12fac767c268`
(copies in `audit/frozen/`). Fixture set `audit/tests/fixtures.py` sha256
`aee51dd03a54e304ec0578627d9dd7b682a33da34ed5228d2346582e6642806f`.

## Step 3 to 5 results so far

2026-11-07T00:21Z to 00:23Z (clock reads 00:20:48Z and 00:23:43Z). Panel run
(`audit/scripts/panel.py`, output `audit/panel/panel_results.json`): the replay
of `verify.sh` on all 36 stored workspaces reproduces every stored
`verifier_exit_code` and `verifier_output` (0 mismatches), so the offline
runner stands in for the harness on these trials. Scored coverage 36/36 for
the grader and the replacement. The grader passes 20 trials, the replacement
15; the 5 differences (t12, t14, t21, t29, t35) are all grader passes that the
contract fails. No stored trial's verdict depends on a decision entry: all 32
combinations of readings give the same verdicts.

## Step 6 decision gate (recorded before the sample is drawn)

2026-11-07T00:23:43Z. Current recommendation from steps 1 to 5: fix the
grader. Results of a blinded review that would change it:

- Admit the grader instead: the consensus passes at least 3 of the 5
  disagreement trials (t12, t14, t21, t29, t35), so that the current grader's
  weighted error rate is not higher than the replacement's (the paired 95%
  interval of grader minus replacement includes zero or lies below it).
- Replace the benchmark instead: the reviewers cannot settle the task's own
  verdicts, meaning Cohen's kappa between the two reviewers' leans below 0.6
  on the 36 trial cases, or a consensus that contradicts both the grader and
  the replacement on 2 or more agreement-stratum trials.
- Otherwise the recommendation stays "fix the grader", with the replacement
  (or the three fixes it implies) admitted only if it also passes every
  fixture, keeps scored coverage complete, and its error rate is lower than
  the current grader's with a paired interval that excludes zero.

## Step 6.1-6.2 frozen sample, round 1 (no review has started; none will run in this exercise)

2026-11-07T00:26:37Z. Drawn by `audit/scripts/draw_sample.py` with seed
20261107 from `audit/panel/panel_results.json`. Strata of the 36 stored trial
verdicts, by whether the stored verdict and the replacement (proposed
readings) disagree: disagree 5, agree 31. Round 1 takes all 36 (a census of
both strata), plus 8 calibration fixtures with unambiguous labels and 4
decision fixtures (D-leading-zeros, D-plus-sign, D-whitespace-set,
D-encoding), which stay out of the error rate: 48 cases with opaque ids, in a
different seeded order for each reviewer. Every stored trial is held out: the
replacement was frozen before it graded any of them.

Case list `audit/frozen/round1/cases.json` sha256
`34b9673f16ba3295c476219681e3732c353057cad38c289744f1d8043da66311`.

| Frozen file | sha256 |
|---|---|
| `frozen/round1/key.json` (source model and grader verdicts per case) | `693599d599a0ebe66c29dea641423c892ed7b2b7f798857b2bc2d2a4739a688d` |
| `frozen/round1/packet/batch_A.md` | `8814fb7b325c9ec2a198b63e177871649f1b9914905d64c8d294116b20346600` |
| `frozen/round1/packet/batch_B.md` | `760beb415a79b56ac6d26c413c152dbbc84f7f94f559ebc68f233744f9936210` |
| `frozen/round1/packet/responses.json` (frozen graded state per case) | `b80fc29b1cadc574e8ddc5503ac78aa346abf4846cb2aba167231f0bc0748742` |
| `frozen/round1/packet/show_case.py` (helper) | `f082d0d3d65415e3eeeb96929fa225e1d2a06918a990306f72e5b9bd1d10bc3c` |
| `frozen/round1/packet/reviewer_prompt_A.md` | `f2bb3dfbf89afb83626a496e84ec720d0092967e8a1f013188ba9af411607f18` |
| `frozen/round1/packet/reviewer_prompt_B.md` | `98e45dc7e1558f8cd088972f6dd637e948665d41cb87e856fae3fc7f6fc24b28` |
| `frozen/contract_v1.md`, `frozen/contract_v2.md` | `eaa1e8e7…`, `e8ca88c2…` |
| `frozen/replacement_verifier_v1.py`, `frozen/replacement_scoring_v1.py` | `520916a6…`, `ebbe0bdf…` |

Step 6.3 is rendered (batch files show the case id, the requirement, the
prompt, the reference answer 41 and every stored file under `/workspace`
between begin and end markers; no source model or verdict). Steps 6.4-6.5
(two reviewers, consensus, error rates, kappa) are not run: this exercise
cannot start subagents.

## Findings (defects; recorded 2026-11-07T00:32:07Z)

No reference implementation exists, so every finding's reference status is
"no reference". Reproduce all of them with `bash audit/scripts/repro_findings.sh`
and `bash audit/scripts/repro_g2_path_shadow.sh` (outputs saved next to them).

- F1, check `answer`, `verify.sh` lines 12-15. With no regular file at the
  answer path, the script prints "no answer file" and runs a bare `exit`,
  which returns the status of `echo`: 0, a pass. Contract: README rule 1, a
  missing answer file fails. Stored trials affected: t14, t21, t29 (3 of 36;
  3 of the grader's 20 passes). Fixtures: 7 (empty workspace, `tmp/` only,
  empty `out/`, `out/answer.txt` a directory, `out/answer`,
  `out/answer.txt.txt`, `tmp/answer.txt`).
- F2, check `answer`, `verify.sh` lines 8-10. When `out/answer.txt` is not a
  regular file, the script grades `/workspace/answer.txt` instead. Contract:
  the instruction names `/workspace/out/answer.txt`, and README rule 1 fails a
  trial whose `/workspace/out/answer.txt` is missing. Stored trials graded
  from the wrong file: t12, t23, t35; wrong verdicts: t12 and t35 (41, pass),
  2 of 36. t23 holds 37 and fails anyway.
- F3, check `answer`, `check_answer.py` line 17. `str.strip()` removes
  U+001C-U+001F, which are whitespace under neither reading of
  D-whitespace-set, so `41\x1c` passes. Stored trials affected: 0.
- F4, check `answer`, `check_answer.py` line 21. `int(text)` raises
  `ValueError` on more than 4,300 digits (Python's integer string limit),
  leading zeros included; the uncaught exception exits 1. One exception fails
  only its own trial (one verifier process per trial). The verdict is wrong
  for 41 with 4,299 or more leading zeros (4,301 or more characters) under D-leading-zeros' proposed
  reading. Stored trials affected: 0.
- F5, checks `reward` and `score`, `score_trials.py` line 19.
  `0.0 if exit_code else 1.0` gives reward 1 to `verifier_exit_code` null,
  absent or `false`. Contract: README rule 2, a trial whose verifier did not
  run fails. Stored trials affected: 0 (no stored null); the field that
  measures it is `verifier_exit_code`.
- G1, step 1 inputs. Unpinned by the benchmark: the image is named by tag
  (`toyops/count-server-errors:1.0`) without a digest; the run records hold no
  image digest, `agentx` version or system-prompt hash, model revision,
  decoding setting other than the configuration name, or network mode. All 36
  trials.
- G2, harness. The verifier runs in the container the agent used, after the
  agent, and resolves `bash` and `$PYTHON` (`python3`) through `PATH`. A
  sandbox where a directory ahead on `PATH` holds a `python3` that exits 0
  passes with any answer (`repro_g2_path_shadow.sh`: answer 37, exit 0).
  Whether the agent can write such a path is not stated (unverified input in
  step 1). Share unknown: the snapshots store only `/workspace`; a per-trial
  container diff before the verifier runs would measure it.

## Decision entries (recorded 2026-11-07T00:32:07Z)

Each changes 0 of the 36 stored verdicts (all 32 reading combinations give
the same verdicts).

- D-leading-zeros: `041`. Proposed: pass. Grader: pass (up to 4,300 characters; F4 beyond).
- D-plus-sign: `+41`. Proposed: pass. Grader: fail (non-proposed reading).
- D-digit-script: `٤١`, `４１`. Proposed: fail. Grader: fail.
- D-whitespace-set: `41` + U+00A0. Proposed: fail. Grader: pass (Unicode reading).
- D-encoding: UTF-8 BOM + `41`. Proposed: fail. Grader: fail.

## Steps 3 to 5 evidence (recorded 2026-11-07T00:44:01Z)

- Fixtures and tests: `python -I -m unittest discover -s audit/tests -p "test_*.py" -v`
  (run from the run root): 205 tests, 176 pass, 29 expected failures, 0
  unexpected successes. `unittest.expectedFailure` stands in for
  `pytest.mark.xfail(strict=True)` (pytest is not installed offline).
- Fuzz: `audit/scripts/fuzz_verifier.py`, seed 20261107, 16,000 inputs: 290
  defects (F3; all contain U+001C-U+001F, `check_fuzz_defects.py`), 1,911
  `ValueError` (F4, only among long digit strings), decision classes
  D-whitespace-set 307, D-plus-sign 57, D-leading-zeros 969, D-plus-sign or
  D-leading-zeros 47.
- Score-change table: `audit/panel/score_summary.txt`.

| Evidence file | sha256 |
|---|---|
| `panel/panel_results.json` | `b1b2b6b64eec1fd461a006362deff5a576e47473eb4d0d4fc26716605ab8186a` |
| `panel/score_summary.txt` | `fd31d907452d9f39d45bfd57d6fd7a7c7613a60d9faeb0f7980c39cdd1694000` |
| `fuzz/fuzz_results.json` | `5e071d9a86b22a693504a62df8f016a4ef8fa31d827634a2fafd70354cf8bef7` |
| `fuzz/check_fuzz_defects_output.txt` | `c5a6c4fbfb27293b4db6d88b1ab0f9673bde6145e18691d02090ff3406036d46` |
| `tests/test_run_output.txt` | `9059d0b8d0fd08e05072af0419cf4925e28dd68be918a1b701032c49a6935cdc` |
| `tests/test_fixtures.py` | `5e03a4d365e2f9530bbbcb240d359cf840d8da2f78e021ea8458fcddb629a116` |
| `tests/test_properties.py` | `9c2b66721fc51957f643842e1fb8308da52d468370f6aa49203d441e95daf3ff` |
| `scripts/repro_findings_output.txt` | `0f131ac92cc3216899e9946c0ec7d1b6424583ea214aacac223285b98523c80d` |
| `scripts/repro_g2_output.txt` | `6c4061c1723556a5b32e9ed65dca216f483755245b12717f8f340c975999e0d9` |

Step 6: not run (no subagents in this exercise); the frozen round-1 sample
above is ready for two reviewers. Final pin check of all 83 case files at
2026-11-07T00:44:01Z: no problems.

## Step 7 report

`audit/AUDIT.md`. Recommendation: fix the grader. F1 and F2 change stored
scores; F5 changes the score of any trial whose verifier did not run (none
stored); F3, F4 and the decision entries change no stored verdict; G1 and G2
need harness changes.

## Rerun with temporary directories inside the run (2026-11-07T00:44Z to 00:59Z)

The first runs of the fixture, panel and fuzz scripts made short-lived
sandbox directories in the system temporary folder (deleted after use).
`audit/scripts/common.py` (now sha256 `dc84e8da7d2a1e761db738b9953260bb96525120fccb23ab244764391f09dbc9`)
and the two repro scripts now make them under `audit/tmp/`, and everything
was rerun. Outputs are byte-identical to the first runs (`panel_results.json`
`b1b2b6b6…`, so the frozen sample drawn from it stands; `score_summary.txt`,
`fuzz_results.json`, `check_fuzz_defects_output.txt` and both repro outputs
keep the hashes above), except `tests/test_run_output.txt`, whose timing line
changed: new sha256
`515871f7d4da07062a1b49d89f0828bb7414deba4b349b9de35a1f455cec9ae7`
(205 tests, OK, 29 expected failures). Final pin check of all 83 case files
at 2026-11-07T00:59:07Z: no problems. No bytecode or other file was written
under `case/`.
