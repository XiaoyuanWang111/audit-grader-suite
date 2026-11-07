# Audit of the ToyOrders reward (`case/reward.py`)

This file stands in for the task's issue: the exercise has no issue tracker. It keeps the
pinned inputs, the contract file's hash and time, the decision entries, the findings, and the
frozen-sample hashes. Entries are appended in time order, and every time is UTC, read from the
clock (`date -u`) when the entry was written.

## Step 1. Pinned inputs (2026-11-06T23:53:32Z)

Pinned from the run records, configuration and lockfiles only (`case/TASK.md`,
`case/MANIFEST.sha256`, the fields of `case/responses.jsonl`). `case/reward.py` has not been
opened; it is pinned here by hash only.

`python -I audit/scripts/pin_inputs.py --check` verifies every pin below. It passed at
2026-11-06T23:53Z.

| Input | Pin |
|---|---|
| Grader under audit | `case/reward.py`, sha256 `e8cbb5566d04077449430f4bd3ef184f9f509afc34762fc89b8e46e0988f2362` (there is no repository, so the hash stands in for the commit) |
| Reference implementation | none exists (`case/TASK.md`: "There is no reference implementation of the reward.") |
| Task text and reward specification | `case/TASK.md`, sha256 `ee70972e4cbaedcd05be184ee761d7a6f4432edd212acd24ff5ef2d94593bf34` |
| Prompt template | `case/prompt_template.txt`, sha256 `11d2c94c0b96d8461b6106e6ad793f9e8822ef0b4c7797fef044581bba2fc02e` |
| Dataset | `case/orders.jsonl`, 12 rows, sha256 `f6a5d0a2a4d72fa8658b6160679d757bddda7105449b18757029e9e1e92e20bf`; one hash per row below |
| Stored rollouts (the panel) | `case/responses.jsonl`, 48 rows, sha256 `d343e478c3a61d5e1b0c57919e2ed30672fcae620e97c9dcf82383e0f77e5753` |
| Manifest | `case/MANIFEST.sha256`, sha256 `f190138bf83efd5887ebb7ec749bd86e93eae8916b207bbb8fc158b4e96c2142`; its five entries equal the hashes above |
| Prompt rendering | `prompt_template.txt` with the literal `{email}` replaced by the row's `email`, sent as the only user message (`case/TASK.md`). The template keeps its final newline. The template contains other braces (`{"sku": ...}`), so the rendering is a plain replacement, not `str.format` |
| Reference loading | `json.loads(line, parse_float=Decimal)` on each `orders.jsonl` line (`case/TASK.md`) |
| Response extraction rule | `case/TASK.md`, reward specification item 1: strip whitespace at both ends; if what remains is one fenced block (opening line ```` ```json ```` or ```` ``` ```` with optional trailing spaces, content, closing line ```` ``` ````), the answer is the block's content, otherwise all of what remains |
| Generation settings in the records | every one of the 48 rows: `temperature` 1.0, `max_tokens` 256 |
| Grader dependencies | the Python 3 standard library only (`case/TASK.md`); this audit runs CPython 3.12.10 (`python`, Windows, 64-bit) |

Dataset rows: the sha256 of each `orders.jsonl` line without its newline, and of the rendered
prompt (UTF-8).

| order_id | row sha256 | rendered prompt sha256 |
|---|---|---|
| o01 | `32abe6f65ab43b38f7fba1d22d6323fea3d9335219e569388d208e950e6b63ae` | `013d2f649024285ca1cbbaf35f4ee38fccd2560b3fb8f2777d159c4c1302162b` |
| o02 | `4f8b7b79b1542dd044dfbe3a84bb87089889b4f1e02d9e049ae129339b940b2e` | `585fb29647c49809065358c6390f8d8e244035c4ada8908632735c1fdd8d820a` |
| o03 | `9872ccb03a77bae87fd96359eda3e7677418b86d4c26b2675bfb92e6f5ba63d2` | `bd70533af2ec073d30987f1f20a7113862c93b751c9a0364c54e7522c793bbfa` |
| o04 | `6a6a69076beb0242c50953d1f38b43b2819cd73f0bf02bd45d8b7a2e5a6566a2` | `1f73d1bee7f7fa38fc49f97ec7193fe2e716432b3fd67d49f391fec117514126` |
| o05 | `73874ee1ddc9740ffac14442b8a7b2cc74d0fd0f5cdccbabb00d93c10f87399f` | `581ad6859970e0804b7d7c187b88c8595c37733cd35be1b0349ecbc1bcd77910` |
| o06 | `0113fe55ca65d11a5e8d1e4f86290695e59770befaff35f4dddc8ea1efd6cd9f` | `10e1afd5d02e3dd78ab47e18f20f7c5c7c336140bc742a60865b32ccb91a5c09` |
| o07 | `50abd6a3eb65733a2b5480fd02c90d7e55ac1da472ad7478b2709b008284a0e2` | `df602df886a5d4e0b4330809564000ddbc66bde02a543d889feb1b143af00829` |
| o08 | `cc1fa39c48158032ce066b947882affc630171093c079f4701b1295548919e67` | `d5015293ef76211b472b624128029f6531a4918de12a92298688523ecd683969` |
| o09 | `c49d98a5349762867605746a619a7178f945cb258b13f37332bc93c0bd614975` | `b46bd7c2b42a0a24bcd97114b9de1220466b9f64a7c355c9328d6e4017f76e87` |
| o10 | `6b650a9b5529daea949e25fd116aa547e4c9b487c99a8fb23e0b1ec431b7f716` | `73b1865e51b7927ed12bde2ac26758de58c453fdc3e91123f3b14b109072dffd` |
| o11 | `74c098c097d992fb83f2ba73cba03276979f34ba348cad7fe3cacd3734fee47b` | `61ba5d9d6dc7f69f2ec990c42c17e00e421598176400f341f2cedf17d32b64eb` |
| o12 | `3797653c92c0c42868159cb0f781e0702d1a539408a59ac9fb88d9a81100287d` | `b120492df46d4da597e44ae673e0d5f8329df4e1ddf00230d72a6e0a77d03262` |

I checked each reference against its email by hand (name, date, product codes and
quantities, total); all 12 agree with their emails.

### Inputs the records leave unpinned or unverifiable

| Input | Where it would be recorded | Status |
|---|---|---|
| Policy model, checkpoint weights and tokenizer | a model id and revision per checkpoint in the run records; `responses.jsonl` names only `step-0000` to `step-0600` | unpinned (finding G1) |
| Chat template, system prompt (TASK.md says none), stop sequences, `top_p` and other sampling settings, reasoning parser or reasoning-merge policy | the run's generation configuration; absent from `TASK.md` and from every `responses.jsonl` row | unpinned (finding G1) |
| "None was truncated" | a per-row `finish_reason` or completion-token count; `responses.jsonl` has neither | unverified. Would be verified by `python -c "import json; [print(r['id'], r['finish_reason']) for r in map(json.loads, open('case/responses.jsonl'))]"` on records that keep the field |
| The trainer's Python version | the trainer's environment or lockfile; `TASK.md` says only "Python 3 standard library" | unpinned (finding G2). Unicode tables (`str.casefold`, `str.strip`) and integer-parsing limits differ across Python 3 versions |
| The trainer's call site | the trainer's code that imports `reward.py`; only described in `TASK.md` | unverified; the audit calls `reward(response, reference)` as `TASK.md` describes |

Not applicable in this exercise: there is no repository, research branch, Hugging Face dataset
or job launcher, so there is no grader commit, no dataset revision to pin, and no run to launch.

## Step 2. Contract recorded (2026-11-06T23:57:08Z)

- Contract file: `audit/CONTRACT.md`, sha256
  `8f3b0839348468c2de9767c11d79f42a1a569370da53932e9fbab432cb65ba80`, 10,080 bytes, recorded
  at 2026-11-06T23:57:08Z, before `case/reward.py` was opened. Written from
  `case/prompt_template.txt` and the "Reward specification" and "How the reward is run"
  sections of `case/TASK.md`.
- Checks: `answer` (extraction and parse gate), `customer`, `date`, `items`, `total`,
  `extra_keys` (penalty), `reward` (aggregation), plus the robustness requirement and the
  command line.
- Open points written into the contract, each with a proposed reading: D-fence-newline,
  D-inner-whitespace, D-qty-bool, D-qty-integral, D-total-boundary. They enter the decision
  table below once step 3 has checked the grader against each reading.

## Step 1, continued. Inputs that only the code shows (2026-11-07T00:02Z, after the contract)

`case/reward.py` was opened after the contract hash above was recorded.

- Extraction rule as implemented: `FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*)\n```", re.DOTALL)`
  with `fullmatch` on `response.strip()`; a match's content is `.strip()`ped.
- Reply parser: `json.JSONDecoder(parse_float=Decimal).raw_decode(text)`, catching only
  `json.JSONDecodeError`. `raw_decode` parses one value from the start of `text` and ignores
  whatever follows it. Defaults otherwise: `strict=True`, `NaN` and `Infinity` read as floats,
  last value of a repeated key kept.
- Dependency: the calling thread's `decimal` context. `total_score` computes
  `abs(Decimal(value) - Decimal(expected))` in it, so its precision (28 digits by default) and
  its traps (`Overflow`, `InvalidOperation`, `DivisionByZero` by default) change verdicts and
  exceptions. The trainer process owns that context, and nothing pins it (finding G3).
- Dependency: the interpreter's limits. The `json` scanner's recursion limit and the integer
  digit limit (4,300 digits, CPython 3.11 and later) decide when parsing raises (part of G2).
- Command line: `round(reward(...), 4)` is applied before the per-checkpoint mean, the full-reward
  count and the `--out` lines.

## Step 5 preparation. Held-out rollouts (2026-11-07T00:02:20Z)

Set aside before any response text was read or graded. `python -I audit/scripts/heldout_split.py`,
seed 20261106, 6 of 12 rollouts per checkpoint.

- `audit/frozen/heldout_split.json`, sha256
  `a64cea243a88507800bccbdd54dd6e8dc23b57b1872fd7136a2633f23fa7656f`.
- Held out (24): j01 j02 j03 j04 j05 j07 j08 j09 j11 j12 j13 j15 j18 j19 j20 j22 j24 j26 j38 j40
  j41 j42 j43 j45. Development: the other 24.
- Rule: the replacement grader may be changed only from fixtures and development rollouts; the
  review sample of step 6 is drawn from the held-out rollouts only.

## Steps 3 and 4. Fixtures, properties and fuzzing (2026-11-07T00:12:28Z)

- Fixtures: 125 in `audit/tests/fixtures.py`, labeled from the contract alone (31 pass, 31
  near-miss, 63 fail; checks: answer 45, customer 9, date 5, items 21, total 18, extra_keys 5,
  reward 16, content_free 6). Exported with labels and the grader's verdicts to
  `audit/frozen/fixtures.jsonl`, sha256
  `fb849f997edbccbaba945343e565b89afac6f292551c0a89d51b661651298f3b`. Table:
  `audit/runs/fixture_table.md`.
- The grader agrees with 93 fixtures. The 32 it gets wrong are strict expected failures, named
  by cause: F1 7, F2 6, F3 6, F4 2, F5 2, F6 2, F7 2, D-qty-integral 3, D-fence-newline 2.
  The replacement passes all 125 under the proposed readings, under each decision's other
  reading, and under the official readings.
- Property tests: 25 properties over all 12 orders (`audit/tests/test_properties.py`). The
  grader fails 6 (F1: text after the object, text after it inside the fence, a second copy;
  F2: the answer wrapped in an array; F3: an extra wrong item, a duplicated item). The
  replacement passes all 25 and the fence metamorphic relation.
- Test command: `python -I -B -m unittest discover -s audit/tests -t audit/tests`. Result at
  2026-11-07T00:10Z: 303 tests, OK, 38 expected failures. pytest is not installed here, so
  the strict marks use `unittest.expectedFailure`, which fails the run on an unexpected
  success; with pytest installed, `support.xfail_strict` applies
  `pytest.mark.xfail(strict=True)`.
- Fuzzing: `python -I -B audit/scripts/fuzz.py --n 20000 --seed 7` (summary in
  `audit/runs/fuzz_summary.json`). Counts, not rates: the grader raised on 5,094 of 20,000
  cases (AttributeError 5,085, decimal.Overflow 9); it scored 2,600 cases above the
  fixes-only replacement, 1,120 of them as full rewards, and none below it. The replacement
  raised on none. Harness checks on every case: the patched grader with no fix equals
  `case/reward.py`, and with every fix equals the replacement's official readings (0
  mismatches).
- No reference implementation exists, so the reference comparison and its unit tests are
  skipped; `case/reward.py` has no tests of its own, so none encodes a decision.

## Step 5 preparation. Replacement frozen before the panel (2026-11-07T00:12:28Z)

- `audit/replacement/reward_contract.py`, sha256
  `b814dd47e25cf75b86aa6765c4b5ae759ce583a2783977c20e57c89c85ee57ff` (unchanged since it was
  written at 2026-11-07T00:02Z). Attribution harness `audit/scripts/patched_grader.py`, sha256
  `3269af349eca6b1c56ee54f971f0e273b405afafb049da76a2ee9add8c65bc1a`.

## Decision entries (2026-11-07T00:17Z)

The text allows two verdicts on each of these. The evaluation's maintainers choose; the
replacement has one switch per entry (`audit/replacement/reward_contract.py`). "Official" is
what `case/reward.py` does. All five were written into the contract before the code was read.

| Entry | Reading A | Reading B | Grader | Proposed | Fixtures | Panel rollouts affected |
|---|---|---|---|---|---|---|
| D-fence-newline | lines end at `\n` only: ```` ```json\r\n{...}\r\n``` ```` is not a fenced block, 0.0 | LF, CR or CRLF end a line: the same text is a fenced block, scored normally | A | B | `answer:9770c8d1290b`, `answer:cd2109a50988` | 0 of 48 (no response has a CR) |
| D-inner-whitespace | strip the answer, then parse: U+00A0 before the object is allowed | parse the answer as it is: U+00A0 before the object fails | A | A | `answer:277e2d54cb79` | 0 of 48 |
| D-qty-bool | `true`/`false` are not integers: `{"sku": "CD-220", "qty": true}` matches nothing | `true == 1`: it matches a quantity of 1 | A | A | `items:a4e0bb3abc6b`, `items:e33c398b9213` | 0 of 48 |
| D-qty-integral | only a JSON integer is an integer: `"qty": 2.0` does not match 2 | any integral number: `2.0` and `2e0` match 2 | B | A | `items:9d08be6b7961`, `items:497edfbbcb69`, `items:9e80a744f999` | 2 of 48: j02 (1.0 under B, 0.875 under A), j46 (1.0 under B, 0.75 under A) |
| D-total-boundary | "within 0.005" includes the boundary: 64.505 against 64.50 scores 1 | strictly inside: it scores 0 | A | A | `total:2ccc581ca61b`, `total:5d48891fbccf` | 0 of 48 |

Reasons for the proposals are in `audit/CONTRACT.md` sections 1 and 2.

## Findings (2026-11-07T00:17Z)

"Smallest" is the smallest response kept as a fixture that reproduces the wrong verdict.
There is no reference implementation, so no finding has a reference status.

| Id | Check or stage | Defect | Contract broken | Smallest reproducer (order) | Panel share |
|---|---|---|---|---|---|
| F1 | `answer`: parser | `raw_decode` parses the first JSON value and ignores any text after it, inside or outside the fence | 1.3: nothing but whitespace around the object, else 0.0 | `{"total":24}x` (o10): 0.25, contract 0.0 | 6 of 48 rollouts (12.5%): j05 j08 j20 j37 j40 j47, each 1.0 instead of 0.0 |
| F2 | `answer`: type check | a top-level value that is not an object raises `AttributeError`; that includes any response that starts with a number, a string, `true`, `false`, `NaN` or `[` | 1.3 (0.0) and 5 (always a float); one such response stops the command-line run with no output | `0` (o01): raises | 0 of 48; fuzz 5,085 of 20,000 |
| F3 | `items` | the score divides by the number of reference items, not the larger of reference and answer items, so extra, duplicate, hedged and non-object items cost nothing | 2, `items` | `{"items":[{"sku":"EF-310","qty":3},0]}` (o02): 0.25, contract 0.125 | 5 of 48 (10.4%): j04 j16 j18 j32 j41, each 1.0 instead of 0.875 to 0.9375 |
| F4 | `total` | `Decimal` subtraction raises `decimal.Overflow` on a total beyond the context's exponent limit | 5 | `{"total":1e1000000}` (o01): raises | 0 of 48; fuzz 9 |
| F5 | `answer`: parser | parse errors other than `JSONDecodeError` escape: `RecursionError` from 2,997 nesting levels (CPython 3.12.10, Windows), `ValueError` from a 4,301-digit integer (CPython 3.11 and later) | 1.3 and 5 | `{"a": ` + 2,997 `[` ... (o01): raises | 0 of 48 |
| F6 | `total` | the difference is rounded to the context's 28 digits, so a total just outside the band can score 1 | 2, `total`: numbers read exactly | `{"total":64.4949999999999999999999999999999}` (o01): 0.25, contract 0.0 | 0 of 48 |
| F7 | `answer`: fence | a tab after the fence tag is accepted (`[ \t]*`). The text says "spaces may follow the tag"; the same item says "whitespace" when it means any whitespace | 1.2 | the Python string `'```json\t\n{"total":24}\n```'` (o10): 0.25, contract 0.0 | 0 of 48 |
| G1 | inputs | policy model and revision, tokenizer, chat template, stop sequences, `top_p` and reasoning parser are not recorded; no `finish_reason`, so "None was truncated" cannot be checked | step 1 | see step 1 | all 48 |
| G2 | inputs | the interpreter version is not pinned; F5's integer case raises only on CPython 3.11 and later, and the nesting limit and Unicode tables change with the version | step 1 | `{"total": ` + 4,301 `1`s + `}`: raises on 3.11+, 0.0 before | 0 of 48 |
| G3 | inputs | the reward computes in the caller's `decimal` context, which the trainer owns: with `getcontext().prec = 1`, `"total": 64.5051` for o01 scores 1 (reward 1.0 instead of 0.75); with the `Overflow` trap off, F4's input returns 0.0 | step 1 | see `audit/AUDIT.md` | 0 of 48 at the default context |

## Step 5. Panel results (2026-11-07T00:17Z)

`python -I -B audit/scripts/panel.py` (pins checked before and after: OK). Verdicts in
`audit/runs/panel_verdicts.jsonl`, summary in `audit/runs/panel_summary.json`.

- Scored coverage: 48 of 48 for every grader (no exception on the stored rollouts).
- Mean reward, grader / fixes only / proposed: 0.926 / 0.791 / 0.784. Per checkpoint:
  step-0000 0.756 / 0.584 / 0.584; step-0200 0.971 / 0.960 / 0.929; step-0400 0.979 / 0.896 /
  0.896; step-0600 1.000 / 0.726 / 0.726.
- The grader's verdict differs from fixes only on 11 of 48 rollouts and from proposed on 13,
  always higher. 11 of its 38 full rewards (28.9%) are false under fixes only, 13 (34.2%)
  under proposed; at step-0600, 6 of 12.
- Stored records: 7 of 48 responses fenced, none with a CR or a reasoning block, the longest
  203 characters; 7 end in a sentence after the JSON (6 rewarded by F1; j25's text follows the
  closing fence and both graders give 0.0).
- Not run: no new responses (no compute), so no rerun of a configuration with identical
  settings, and no held-out generation run.

## Step 6 pre-registration (2026-11-07T00:17Z, before any review)

The planned recommendation is to fix the grader. It changes if the blinded review of the
frozen held-out sample shows any of these:

1. On the 7 sampled F1 and F3 disagreements, the two reviewers' leans agree with the grader's
   reward on 4 or more. Then readers of the text do not settle F1 and F3, they become decision
   entries, and the recommendation becomes: reword the specification, then fix.
2. The replacement's error rate is not lower than the grader's with a paired 95% interval
   that excludes zero. Then the recommendation becomes: do not adopt the replacement; audit
   again.
3. Cohen's kappa between the reviewers' leans is below 0.6, or a quarter or more of the
   verdicts are `ambiguous`. Then the specification cannot be graded reliably as written, and
   the recommendation becomes: rewrite the reward specification (replace the benchmark's
   reward text) before fixing the grader.

The fix recommendation stands when the replacement passes every fixture (it does), scored
coverage is complete (48 of 48), and the replacement's error rate is lower than the
grader's with a paired interval that excludes zero.

## Step 6.1 and 6.2. Review sample drawn and frozen (2026-11-07T00:20:15Z, before any review)

`python -I -B audit/scripts/draw_review_sample.py`, seed 20261108. Population: the 24
held-out rollouts. A case is one rollout, labeled with its reward under the specification.
Strata: the grader under audit and the replacement (proposed readings) disagree (population
8: 4 F1, 3 F3, 1 D-qty-integral) or agree (population 16). Sample: all 8 and all 16. Case ids
are opaque (C113 to C963), drawn with the seed.

| File (under `audit/frozen/`) | sha256 |
|---|---|
| `review_r1_cases.jsonl`: the case list (the freeze) | `1a3fcf31dc2b50a6d5129ac0c256547b46783b45273960aa2a583c40b47943dd` |
| `review_r1_keys.jsonl`: rollout id, source checkpoint, stratum, verdicts | `befdbd8d8721c72c3ad2882fde525643c496751db12164241c1349eb213f89e8` |
| `review_r1_material.jsonl`: prompt, reference, response per case | `852b3e92fc6122dc583a8692060873db6a86585542c94e1c7f0d7daf22c4e724` |
| `review_r1_batch_A.md`: cases in case-id order | `cff443b1436cda2ca0c25cac88768ee0aaf75d329b60752ea9fd2e919cf66166` |
| `review_r1_batch_B.md`: the same cases in a seeded shuffled order | `d1f56c057d80f1c1eb232fb80195e5451d5ea323b948d9bd1927cd7d98e21e4d` |
| `review_r1_strata.json`: seed, population and sample sizes, batch orders | `554d720b31fb1f7a7fad700573082b7e47063d1b6f02c95c520e21df1a6f3d17` |
| `review_r1_show.py`: helper that prints a case's exact response | `5608b65352d8f2a518cf5cd084dc758fd68f664364de72a168a36ec0c657fa42` |
| `review_r1_reviewer_prompt.md`: the adapted reviewer prompt | `bbbf86b3287dbd903e13cd856e6b820b0d2fe20daaf20b278a2646dfc978fa9c` |
| `heldout_split.json`: the held-out split (step 5) | `a64cea243a88507800bccbdd54dd6e8dc23b57b1872fd7136a2633f23fa7656f` |
| `fixtures.jsonl`: the fixtures with labels (step 3) | `fb849f997edbccbaba945343e565b89afac6f292551c0a89d51b661651298f3b` |

The batch files show case ids, the specification, the prompt, the reference and the
response; no checkpoint, rollout id or grader verdict (checked by search). Steps 6.4 and 6.5
were not run: this exercise cannot start reviewer runs, so no labels, consensus, error rate,
kappa or intervals exist.

## Step 7. Report (2026-11-07T00:27:08Z)

Report: `audit/AUDIT.md`, sha256
`d35bc9a244fca9be76178e9dbed10a03852fb0721f20d40d2f135cb1bede3d46`.

- Recommendation: fix the grader.
- No blinded review ran, so there is no consensus error rate. Judged by the replacement, the
  grader is wrong on 11 of 48 stored rollouts (13 under the proposed readings), always
  upward; 11 of its 38 full rewards are false. Mean reward 0.926 against 0.791 (fixes only);
  step-0600 1.000 against 0.726. Under fixes only the best checkpoint is step-0200.
- Findings: F1 to F7 (grader), G1 to G3 (inputs). Decision entries: D-fence-newline,
  D-inner-whitespace, D-qty-bool, D-qty-integral, D-total-boundary; the grader takes the
  non-proposed reading of D-fence-newline and D-qty-integral.
- Final checks at 2026-11-07T00:27Z: pins OK; 306 tests OK with 39 strict expected failures;
  `audit/CONTRACT.md` still has its recorded hash; no bytecode cache in `case/`.
