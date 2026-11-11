# Audit record: ToyCode 1.0 execution grader

Offline stand-in for the task's issue (no tracker in this run). Entries are appended in order; times are UTC and
were read from the clock in the same step as they were written.

## 1. Pinned inputs (recorded 2026-11-11T01:11Z, before the contract hash; from TASK.md, MANIFEST.sha256 and the stored run records only)

All files under `case/` match `case/MANIFEST.sha256` (`sha256sum -c` OK for all 8 entries at 01:07Z).

| Input | Pin | Source |
|---|---|---|
| Grader `grade.py` | sha256 `ea020bdda3314c85bb2c185697bfa640b5939251dce97fdde1a60aeb8ecd9153` | MANIFEST |
| Grader child `runner.py` | sha256 `36953b5beac29ef3e2162551d0e9249226e1ff679b11ae101e847365dd1ecc28` | MANIFEST |
| Reference `reference/harness_ref.py` (authors' harness, ToyCode 1.0) | sha256 `4b502d23f2dad7aa26ba5dd2c7a5f54072265f5908412675de39918075c6e0ec` | MANIFEST; no commit id given |
| Prompt template `prompt_template.txt` | sha256 `e625324a385702293fedc322a5a9d65cbf0e0d8313d912119425b0f53db0a87a` | MANIFEST |
| Tasks `tasks.jsonl` (10 rows) | sha256 `6d7374ece0f947ad2a74ee2358225d399871c38c0fc2822e6858b1e1193e0027` | MANIFEST |
| Tests `tests.json` (45 tests) | sha256 `b68f1b8f193a8a7286da463ba2191d74bda28d7724223dd4b6ce5cd40820218e` | MANIFEST |
| Stored responses `responses.jsonl` (40 rows) | sha256 `dc00ec20a4e86e9743a7d82b271b555a639cd582bb11f0fcc174513689d95535` | MANIFEST |
| Task text `TASK.md` | sha256 `657855f8fda321d84346273a8effb68bdac7e4db1dbb7bccab19e4d70845d70a` | MANIFEST |
| `MANIFEST.sha256` itself | sha256 `1a8b608ad96358348d941de149b04ce4ceaf679a26dcc920f6680052932e14c7` | computed here |
| Prompt rendering | template with `{prompt}` replaced, sole user message, no system prompt, the model's own chat template | TASK.md |
| Generation | temperature 0, `max_tokens` 1024, no stop sequences; stored per row (`temperature`, `max_tokens`, `finish_reason`) | responses.jsonl |
| Reasoning | none of the 4 models emits a reasoning block; no reasoning parser | TASK.md |
| Interpreter | "CPython 3.12" (no patch version, OS, locale or hardware) | TASK.md |
| Grader dependencies | standard library only, offline | TASK.md |
| Audit machine | Windows 11, Python 3.12.10 (`python --version`), Git Bash | this run |

Row hashes (first 16 hex digits of sha256 of each JSON line without its line break; tests: sha256 of the task's
test list as compact sorted JSON):

- tasks: t01 797d5de3a67d993f, t02 5fbc52110c2d5f1d, t03 100ef97624181e40, t04 87a3f76d54af23be,
  t05 5792d06fd756a432, t06 42e9ddd0b480858e, t07 d7b2e848d2858f0b, t08 3592eb1286e9ca2d, t09 ef6727107b2e370f,
  t10 86cd90dc7a8206f3
- tests: t01 66511df85f03d63b (5), t02 394d974a440e9fde (5), t03 b5c6d3f28412ad6a (5), t04 a02c20ee7a78bc6f (4),
  t05 eafaef5655761258 (4), t06 3420349830450db6 (4), t07 7a73ed59a28bc39c (5), t08 8b6274408bd4fdcb (4),
  t09 dd28dd68daacea6a (4), t10 973c756790cbd392 (5)
- responses: c01 5ec811450b986735, c02 c62987c006204fdf, c03 d0cc84155932c371, c04 0e6becca1d1c9fdd,
  c05 ee567b06371b91a4, c06 2aca53f0920f1d77, c07 5ae65ce17239141c, c08 182028d524bae9c9, c09 fb2cb9bb2bad72ba,
  c10 3a980a2f16980679, c11 292b22af09676f40, c12 74edf7cf2029ed40, c13 feae19694be3cf4f, c14 19f77a8a2cde71aa,
  c15 faa32e52154f7fab, c16 002bf23b526e64b1, c17 f3d8ee05520ab6a6, c18 9e27bec85a6c133b, c19 770f8173bff2ddf4,
  c20 050c7ba52e06291f, c21 2d0f1bfa9d20f6e6, c22 3e88f09d756386de, c23 ad1b20cb2cdd656a, c24 15352ae6ff01997e,
  c25 c59e62e5938e10b8, c26 1e0d858c0ea2c6a5, c27 c38e7499bde0d855, c28 6cb7b10b2ba642e8, c29 f93f4eb7e7567715,
  c30 fef14fa857806a17, c31 075effc70455bdeb, c32 7c9cf2f32b525385, c33 6e2f7328ba36e439, c34 6056d77e11335492,
  c35 091340fcf7938711, c36 055744c945330743, c37 9a44edd8d8e33272, c38 8713bd2e8edd8a3e, c39 00f6f5308339b5ee,
  c40 60e6d54f48bab9b7

Unpinned or unverified so far (TASK.md and the records only):

- U1. Model revisions and chat templates: "each model's own chat template", no revision. Unverified; would be
  verified from the generation run's config (not provided). Affects regeneration, not regrading.
- U2. Grader platform: "CPython 3.12" with no patch version, OS, locale (text encoding) or hardware. The 4 s wall
  limit depends on hardware. Checked further after reading the code (see entries below).
- U3. Reference commit: the reference is pinned by file hash only, no upstream commit.

## 2. Contract

- 2026-11-11T01:11:23Z: `audit/CONTRACT.md` written before reading any grader or reference code.
  sha256 `f2f85c9863300eb3b4455bb0a8e7bf4fd2f319c89b07275316d7a59276632b1b`.
- Decision entries at this point: D-crlf, D-dynamic-import, D-eq-object, D-palindrome-normalization (all in
  the contract file, each with both readings and a proposal).

## 1b. Pins that only the code shows (recorded 2026-11-11T01:18Z, after the contract hash)

`grade.py`, `runner.py` and `reference/harness_ref.py` were first opened after the 01:11:23Z contract entry.

- Grader extraction rule: `FENCE = ^```python[ \t]*\n(.*?)^```[ \t]*$` (MULTILINE, DOTALL), first match, else the
  whole response. Only the tag `python` opens a block.
- Grader import check: `ast.parse`, `ast.walk`, top-level name before the first dot against the 9 allowed
  modules; `ImportFrom` checks `node.module` and ignores `node.level`; only `SyntaxError` and `ValueError` from
  `ast.parse` are caught.
- Grader execution: `[sys.executable, runner.py, job.json]`, cwd a temp dir, env = parent env plus
  `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1` (no `PYTHONHASHSEED`), `subprocess.run(timeout=4.0)` over
  the whole child process, stdout decoded as UTF-8 with `errors="replace"`; the verdict is read from the LAST
  stdout line that starts with `@@RESULT@@ `.
- Grader child: `exec` into `{"__name__": "candidate"}`, sharing the child's builtins; candidate stdout
  redirected to a StringIO; each call `fn(*copy.deepcopy(args))` under `except Exception`; return values sent
  as `json.dumps(value, default=repr)` and compared in the parent after `json.loads`; calls that raise on an
  `expected` test go to an `errors` list.
- Reference: same interpreter and timeout; extraction `^```[A-Za-z0-9_+-]*[ \t]*\n(.*?)^```[ \t]*$`; compares
  `out == expected` inside the child and prints `<<toycode-result>>{"ok": ...}`.
- Text encoding: job file written and read as UTF-8 on both sides, child stdout forced to UTF-8, so grading
  does not depend on the locale (U2's encoding part is closed). Still unpinned: OS, interpreter patch version,
  hardware (4 s wall limit) and the hash seed (no `PYTHONHASHSEED`).
- Tests: neither the grader nor the reference ships unit tests.

## 2b. Contract additions after reading the code (each with its reason)

- 2026-11-11T01:20Z, D-main-guard (added to the decision table in AUDIT.md, not to CONTRACT.md, whose hash
  stays as recorded): README step 3 says the code "runs in a fresh Python process"; it does not say whether
  `__name__` is `"__main__"`. Reason: noticed while writing fixtures for top-level code; both graders use
  `"candidate"`. Proposed: the guard does not run (README: "loading the code", then "calls the function").
- 2026-11-11T01:20Z, D-time-origin: the 4 s cover "loading the code and running every test"; the grader and the
  reference measure from process start, so interpreter start-up (about 0.05 s here) counts. Reason: noticed
  while implementing the replacement's timer. Proposed: process start (as both graders do).

## 3. Fixtures (2026-11-11T01:28Z)

- 60 single-response fixtures in `audit/tests/fixtures.py` (36 controls on which all three graders agree with
  the label, 6 decision fixtures, 18 finding fixtures), 2 robustness fixtures, 2 aggregation fixtures and 1
  hash-seed fixture (65 in all), run by `audit/tests/test_fixtures.py`; 330 metamorphic and content-free cases
  (19 ignored edits + 14 forbidden edits x 10 tasks) in `audit/tests/metamorphic.py`, run by
  `audit/tests/test_metamorphic.py`. Runner: `python -B -m unittest discover -s audit/tests -p "test_*.py"`
  (pytest is not installed; `unittest.expectedFailure` is strict: an unexpected success fails the run).
- First full run at 01:27Z: 1192 tests, OK, 121 expected failures (all on the grader or the reference).
- A replacement grader was needed (fixtures showed fixable defects): `audit/replacement/grade_contract.py` and
  `child_contract.py`, one switch per decision. Frozen before the panel run:
  - grade_contract.py `995634419319b74f5783f9933326c5af3e972862459f36b0d99e0add4602c546`
  - child_contract.py `fd5f4d1df7c9ad16f5826782c19e5331bec8f13aac127f8c5044ce212c2c908d`
  - fixtures.py `6e57e4796cdb5d003f92fcd50e7139500c8778632fe4db031536a3f0f9ac4455`,
    metamorphic.py `3186898a774c5d7c89bf3cc2c2d31ca8b07de8c024729867d152c6c1e0c804ad`
- Held-out responses: the replacement was written from the contract and is not changed after seeing panel
  verdicts, so all 40 stored responses stay eligible for the final review round (no split needed).
- Findings opened (details and counterexamples in AUDIT.md): F1 unexpected exceptions and missing function
  ignored; F2 return values compared after a JSON round trip; F3 only ```` ```python ```` opens a block; F4 result
  channel forgeable by candidate code (grader and reference); F5 one response can stop the whole run (grader
  and reference); F6 duplicate rows counted twice (grader and reference); G1 unpinned platform inputs; G2 hash
  seed unpinned. Observation O1: relative `from .math import x` passes the import check (no verdict effect).

## 4. Reference comparison and stress (2026-11-11T01:28Z)

- No unit tests exist in the grader or the reference, so no reference assertions to replay and no grader tests
  that encode a decision.
- Metamorphic suite: the grader misses 86 of 330 cases (I05-I08 tag variants 40, X05 10, X03/X04/X10/X11 32,
  X07 3, X08 1); the reference and the replacement miss none.
- Fuzz (`python -B audit/scripts/fuzz.py 400 20261111`): exceptions that would stop the run: grader 7
  (RecursionError 5, JSONDecodeError 2), reference 20 (RecursionError 14, TypeError 6), replacement 0.
- Content-free: the empty response and the empty block pass 8 of 10 tasks in the grader (every task without a
  `raises` test); restating the signature, the rendered prompt and repeated words fail everywhere.

## 5. Panel (stored responses only; 2026-11-11T01:29Z-01:31Z)

- No compute in this run: the 40 stored responses are the panel (4 models x 10 tasks, temperature 0, 1024
  tokens). All 40 have `finish_reason` `stop`; 39 open with ```` ```python ````, 1 has no fence; none contains
  `</think>` or `\r`.
- `python -B audit/scripts/panel.py` -> `audit/panel/summary.json` and one verdict file per configuration.
  Scored coverage 40/40 for every configuration.
- Scores (percent; kite-7b, lark-13b, wren-34b, finch-8b): grader 90/40/100/30; reference 90/20/90/10;
  replacement with the stored t02 test (`--palindrome normalized`) 90/20/90/10; replacement, proposed readings,
  80/30/80/20.
- Grader vs replacement (stored t02 test): 5 disagreements, all grader passes the contract fails: c02, c22, c40
  (F1) and c16, c31 (F2). The same 5 separate the grader from the reference.
- D-palindrome-normalization moves c05, c06, c07, c08 (kite -10, lark +10, wren -10, finch +10). No other
  decision switch changes a stored verdict.
- Reruns with identical settings: grader vs grader rerun 0 differences, replacement vs rerun 0 (verdict files
  byte-identical, sha256 in summary.json). Every score change above (10 to 20 points) exceeds the rerun
  difference (0).

## 6. Blinded review: gate and frozen sample

Gate, recorded 2026-11-11T01:31:55Z before drawing the sample: the recommendation in step 7 changes from "fix
the grader" to "admit the grader" only if the grader's error rate is not higher than the replacement's (paired
difference interval includes or falls below zero), and to "replace the benchmark" if the consensus contradicts
the replacement on more than 2 of the cases where both reviewers give definite agreeing verdicts. The
replacement must also keep passing every fixture and keep 40/40 coverage.

Frozen sample (drawn and hashed at 2026-11-11T01:32:45Z by `python -B audit/scripts/draw_sample.py 20261111`;
entry written 01:35Z; no review has started, and none will in this run):

- Seed 20261111. Population 40 verdicts (the stored panel). Strata: grader and replacement (proposed readings)
  disagree 9, agree 31. Drawn: all 9 and all 31 (census; the population is too small to subsample).
- `audit/frozen/cases.jsonl` (the case list, with each response's sha256)
  `503809f1192493a9a78c4c2341a514ae6200ed1de5734c203e6ba679f73d4a74`
- `audit/frozen/keys.jsonl` (source model and verdicts; never shown to reviewers)
  `b20bbaaca5f76ba045853fc3c030719f18f823855f8a30d74770f2d341bd9fdf`
- `audit/frozen/batch_A.md` `b5cf593cad8346d46634587d7e67bda9beed8fee710ac23d4988d9534ea231d2`
- `audit/frozen/batch_B.md` (different order) `2e8be4aa372bed405ef1f0eee0dd09d63aa4a204cfdfc1c35dc7224ff71b0387`
- `audit/frozen/show_case.py` `0aef41ab3f70350f559110080189b384dedb29ccca8f5f501aad51a274322418`
- `audit/frozen/reviewer_prompt_A.md` `baa819899722c7b654431746e277a16e8af06ea9533aed112041b6681184d819`
- `audit/frozen/reviewer_prompt_B.md` `d541f74f1ea95660e1a8fb8ae72a1c396e96eb38772500989629fa2ea14fe269`
- `audit/frozen/sample_meta.json` `7ccc05fc5b15ff2a30988864f3add89112b676dbb80819e2a3b63d7f4c6ec600`
- `audit/frozen/responses/` 40 files, each hash in cases.jsonl
- Step 6.4-6.5 (two reviewers, consensus, error rates, kappa) not run: this exercise cannot start subagents.
- 01:38:51Z: re-running the draw with the same seed reproduced every frozen file byte for byte (`diff -r`).

## 7. Report (2026-11-11T01:43Z)

- Report: `audit/AUDIT.md`, sha256 `a3d7261edbaa342bb0db7cf546dd36ec13c4047400714288080a4c86df6e0bd5`.
- Findings: F1 (3 of 40 stored verdicts), F2 (2 of 40), F3, F4, F5, F6, G1, G2 (0 of 40 each); F4, F5, F6, G1, G2
  also hold in the reference. Decision entries: D-palindrome-normalization (4 of 40 stored verdicts),
  D-crlf, D-dynamic-import, D-eq-object, D-main-guard, D-time-origin (0 each). Observation O1.
- Contract-measured grader error on the stored panel: 5 of 40 (12.5%), all false passes; 9 of 40 under the
  proposed D-palindrome-normalization reading. No reviewer-consensus rate (step 6 not run).
- Recommendation: fix the grader.
- Counterexample inputs: `audit/repro/*.jsonl` (written by `audit/scripts/make_repro.py`); sha256: D_crlf
  `eade0939...`, D_palindrome `5b68e4df...`, F1_ignored_exceptions `8701f8b3...`, F1_whole_benchmark
  `7ccb1889...`, F2_json_round_trip `03a5a6f5...`, F3_python_tag_only `f74357ba...`, F4_forged_result
  `1e374495...`, F5_malformed_forge `3a6171a5...`, F5_parse_recursion `ac38ddf9...`, F6_duplicate_rows
  `324da1ce...`, G2_hash_seed `b17d1798...`.
- Final checks, 01:38:57Z-01:43:20Z: `MANIFEST.sha256` OK before and after the test run; unittest `Ran 1192
  tests`, `OK (expected failures=121)`; every command cited in AUDIT.md rerun and printed what the report says
  (F1-F6, G1, G2, fuzz counts, metamorphic misses 86/0/0, panel scores and 40/40 coverage); no bytecode under
  `case/`.
