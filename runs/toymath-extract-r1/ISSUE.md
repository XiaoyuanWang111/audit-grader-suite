# Audit of the ToyMath 1.0 grader (`case/grade.py`)

This file stands in for the task's issue: the exercise is offline and has no issue tracker. Entries are
appended in time order. Each entry's time is UTC, read from the clock (`date -u`) when the entry was
written. Paths are relative to the run root `<run directory>`.

## 2026-11-06T22:26Z: step 1, pinned inputs

Sources: `case/TASK.md`, `case/MANIFEST.sha256` and the stored run records `case/responses.jsonl`. No code
was read for this entry. `python -I audit/scripts/pin_inputs.py` recomputes every hash below and writes
them, with the 48 response-row hashes, to `audit/out/pins.json`; with `--check` it exits 1 if any case file
differs from the manifest.

Files. All six match `case/MANIFEST.sha256` (`sha256sum -c` and `pin_inputs.py --check`, both OK):

| File | sha256 |
|---|---|
| `case/grade.py` (grader under audit) | `35e8eff6d1cdacf97d8b08aed2d58171466df5174aa1a8b172ceeb0ff5a05a6e` |
| `case/reference/grade_ref.py` (reference, ToyMath 1.0 release) | `46f8a70c5f1eaf886a3ff54bde2cd3271c9c8b6d7ec67f0b3c874eeffa4aa53a` |
| `case/problems.jsonl` (dataset, 12 rows) | `976da248da1f45642778836a7e0a779b821b3366de1e3b6b55055633d03b7f18` |
| `case/prompt_template.txt` (312 bytes, LF, no CR) | `05e1b62f677b071d290b087c2acefa59b7556ae84a71fbd3911b160ac293f71f` |
| `case/responses.jsonl` (48 stored responses) | `f50586804ce1d72e637635472de1c034f10b32fe435eff6aa2ddb76d485b5964` |
| `case/TASK.md` | `bb4e1b0ae1fdee8239d84b1739d85bf9a9ac36b0f92c11d8a95cce133e48af7b` |
| `case/MANIFEST.sha256` | `8cd28ab69c93828970255ce40b5330de3f80436770b4492348ff1a94f22611d1` |

There is no commit for either grader: the manifest hash is the only pin. ToyMath has one version, 1.0.

Dataset rows. Row hash = sha256 of the row's canonical JSON (keys sorted, UTF-8, separators `,` `:`).
Prompt hash = sha256 of the UTF-8 user message: `prompt_template.txt` with `{problem}` replaced by the
`problem` field. For every row, `str.replace` and `str.format` give the same text. I checked the 12
reference answers by hand, and all are right.

| problem_id | answer | row sha256 | rendered prompt sha256 |
|---|---|---|---|
| p01 | 3.5 | `9789e7a3274cff3d7c276d5198e2e961757dd3f2b72163784326b3d8142dc887` | `d5e6c6898875729fac09d6d9dff9fe4a33e127c0d11266195046adce6d520e07` |
| p02 | 486 | `e22d1f3839bfe6cdf85114ca9205636acd770662ee49c003c5491a2563ef9f44` | `fbf9c9d4e843fc45c98a5c8155e003b5639d5b9f86f0c9ffda94b2bbf5ae060a` |
| p03 | 2250 | `7395ad8ac27fca92353da8cfcb929af672cd6ca4b899b9a807e82721639dfbdc` | `cb8f1d5d59267f8776456d28e31e27f087253c1eb8fb1059d48188fd7a083dbf` |
| p04 | -7 | `790986fee2e1ce423f17739ef1e176c0f363122f4b4fbfdeaf7eaf4586ed2835` | `e23fe78cf17a19fb3a3bbbe8f300dbd4186c4bb489816313c6710c2c222151d3` |
| p05 | 72 | `6cfde9f080567d5056d9c3134f95b648067044175e8a9130653dad20f5b584b5` | `5e3cfd64a8ae3d6937354b1fbb05aabbfd3360f751428959cb59dc7486a918f1` |
| p06 | 0 | `d9cd8c6cc42d973308e6a02bd6090784224ddbc5a5e258205e202b011fb94c15` | `4eb528c0f0d84594897bc97586091173e71b17ffa14737ff4447d53d501693a2` |
| p07 | 15000 | `35aa1d8888a8a99d3a3af6b43dd22429323f3e289dc5d2c18f91f980345cd9aa` | `7f482bb11d4f8e6d1b61bb64312bfef6fbbf2fc501211962d997ae80d8723e15` |
| p08 | 120 | `43de7706efe8578798630f11df976a64a2056cbd8672d71946fdf6802beb9423` | `1fefa468cf455a1598f8c32cebb59d2c4abbdd8d8ca529c3bfc0fbf566f1ee2d` |
| p09 | 28.8 | `ace656f4139e7aed398a7d24d5c3d6e0ecc2b8f215dfe1b7e1467755028c4924` | `b54f3bef3f0c8d15415a57c9c4540645c485d000f1edb54697a0343bfec6708c` |
| p10 | 13 | `ff422573de8183754ca6b654b7f77b206b3fec2d50482d8e56b60e98473c51b4` | `5489a64f9b3d8f9b36e5e76e759c1f8099834cae999ebf4ca84c550b998556a2` |
| p11 | 756 | `cfd272ac3a552c32ad1107d42e2ee540797ecda28fab8e0c6f110980e3751348` | `6732485968c424a335bd66fe34a6b60aae3fc59143dc48ca4cea2a7f2c7899d7` |
| p12 | 15 | `2e60524ba3244f5203e94da393f93c1210c567bafd91fd1fec881b2465d9fe0a` | `72f84c99402d00616cc01e1e77f3b8209987e9a969c3a23e75639423f8fa6d56` |

Prompt rendering (TASK.md): the rendered prompt is the only user message, with no system prompt, wrapped
in each model's own chat template.

Generation settings. Each response row has the fields `id`, `model`, `problem_id`, `response`,
`finish_reason`, `temperature` and `max_tokens`:

| Setting | Value | Source |
|---|---|---|
| Models | `alpha-7b`, `beta-14b`, `gamma-32b`, `delta-8b`; 12 responses each, one per problem, ids unique | records |
| Temperature | 0.0 on all 48 rows | records |
| Output budget | `max_tokens` 256 on all 48 rows | records |
| Finish reason | `stop` 46, `length` 2 (both `delta-8b`) | records |
| Stop sequences | none | TASK.md only; no record field |
| Chat template | "each model's own" | TASK.md only; no revision |
| Reasoning block, reasoning parser, merge policy | none: no model emits a reasoning block, the server has no reasoning parser | TASK.md only; no record field |
| Graded text, extraction rule | the benchmark card's scoring rule in TASK.md | TASK.md; the code's rule is recorded after the contract hash |
| Grader dependencies | Python 3 standard library, "3.8 or later", offline | TASK.md; this audit runs Python 3.12.10 |

Inputs that the benchmark leaves unpinned. The records name each model but give no checkpoint or revision,
no chat-template revision, no serving stack or version, and no seed. Stop sequences and the absence of a
reasoning parser are stated in TASK.md, and no record field shows them. I report these as finding G1 below.
The Python version is a range, "3.8 or later". Whether it can change a verdict depends on the code, so I
will record that after the contract hash.

Unverified inputs, which this offline audit cannot fetch:

| Input | Location | Command that would verify it |
|---|---|---|
| The chat-templated input each model received | not stored; the serving request log | add `prompt_sha256` (rendered user message) and `chat_input_sha256` to each record, then compare with this table |
| Stop sequences: none | not stored; the run's sampling parameters | add a `stop` field to each record; `python -c "import json;print({json.dumps(json.loads(l).get('stop')) for l in open('case/responses.jsonl')})"` |
| Model checkpoints | not stored | add `model_revision` to each record and pin it here |

Pin checks: `python -I audit/scripts/pin_inputs.py --check` runs before and after every grading run in this
audit. Each run's log is under `audit/out/`.

### Finding G1 (protocol): generation inputs that the run records leave unpinned

The 48 run records name the model, but not its checkpoint or revision, the chat template, the serving stack
and version, or the seed, and they have no field for stop sequences or reasoning parsing. TASK.md states some
of these values ("no stop sequences", "each model's own chat template", "no reasoning parser"), but nothing
in the records shows which values a given run used. So a rerun cannot be checked against this one.
Affected: all 48 responses. Status in the reference: not applicable, because this is the run protocol and
not the grader.

## 2026-11-06T22:29Z: step 2, contract recorded before any code was read

`audit/CONTRACT.md`, 7,776 bytes, sha256 `6a4b4e9401866fc0678bfe908c8a67f94018b12ae8b7254dba81cca955d95b17`,
hashed at 2026-11-06T22:29:07Z. It was written from `case/prompt_template.txt`, `case/problems.jsonl` and the
scoring rule in `case/TASK.md`. Neither `case/grade.py` nor `case/reference/grade_ref.py` had been opened when
it was hashed. It has one check (`answer`), four stages (S1 answer line, S2 number, S3 comparison, S4 score),
three labels, and five decision entries: `D-multiple-numbers`, `D-comma-grouping`, `D-digits`,
`D-leading-whitespace` and `D-tolerance-boundary`. Each later contract change is listed below with its reason.

## 2026-11-06T22:40Z: step 1 addendum, what only the code shows

I read `case/grade.py` and `case/reference/grade_ref.py` after the contract hash above was recorded.

| Input | `case/grade.py` | `case/reference/grade_ref.py` |
|---|---|---|
| Answer line | last line of `str.splitlines()` that matches `^\s*Answer:(.*)$` | last line whose `strip()` starts with `Answer:` |
| Number | first match of `-?\d+(?:\.\d+)?` in the rest of the line; commas are not handled | rest of the line, stripped, with every comma removed, must fully match `-?\d+(\.\d+)?` |
| Parse and compare | `Decimal`; correct if \|x − r\| ≤ 0.01 × max(1, \|r\|) | `Decimal`; correct if \|x − r\| ≤ 0.01 |
| Labels | `correct`, `incorrect`, `no_answer` | `correct`, `incorrect`; a response with no number gets `incorrect` and `"answer": null` |
| Score | 100 × correct / (correct + incorrect), rounded to 0.1 | 100 × correct / (rows in problems.jsonl) |
| Dependencies | `argparse`, `json`, `os`, `re`, `collections`, `decimal` | `json`, `re`, `sys`, `decimal` |

Python version. In both graders, `\d` and `\s` follow the interpreter's Unicode database: Unicode 15.0.0 in
the Python 3.12.10 used here, and 12.1.0 in Python 3.8. So "3.8 or later" can change a verdict. Under 3.12,
`\d` matches KAWI DIGIT FOUR (U+11F54, added in Unicode 15.0), and `Decimal` reads it as 4. Python 3.8 does not
know the character, so the same response has no number there. This joins finding G1. The `decimal` default
context (28 significant digits, Emax 999999) is the same in 3.8 to 3.12. Unverified, because only Python 3.12
is installed here. Command: `python3.8 -c "import re;print(bool(re.match(r'\d', chr(0x11F54))))"`, expected
`False` (3.12 prints `True`).

## 2026-11-06T22:40Z: contract change 1, decision entry `D-answer-line-form` added

Reason: the reference grader grades the answer line only if all of the text after `Answer:` is one number,
which is a reading of R2 and R3 that the first contract treated as fixed. The proposed reading stays (a):
search for the first number, because R3's "no number on its answer line" presupposes searching the line. The
prompt's "final line of the form `Answer: <number>`" and "without units or currency symbols" support (b).
S2.1 and S2.5 now name the entry, and the decision table has a sixth row. No label under the proposed
readings changed. `audit/CONTRACT.md` sha256 is now
`1b8cfb4dd07e6428abc9f18ccc1fc996a31685ca7cf9e6f31f51de7be130113a` (was `6a4b4e94…5b17`).

## 2026-11-06T22:50Z: replacement grader frozen before the panel is graded

`audit/scripts/grade_contract.py` sha256 `7d58f108aa62b60c36db1b62c959eb7a6b851d4f69a4be8ebb610d75d965cbcc`,
`audit/tests/fixtures.py` sha256 `db5a92323baccedf07f8c62faca6bf7fc6a168f9617c307fdd49f726cd2b093e`. The
replacement was written from the contract, and it passes all 146 fixtures under the proposed readings and
each entry's reading (b). I wrote it after reading the 48 stored responses, but not from grader verdicts on
them. There is one run with one response per model and problem, so no held-out split is possible. Instead,
the replacement stays frozen at this hash for steps 5 and 6. A change prompted by the panel would need a new
review round on new responses, which this offline run cannot generate.

## 2026-11-06T22:51Z: steps 3 to 5, results

Step 3, fixtures. `audit/tests/fixtures.py` has 146 single-response fixtures and 1 isolated one, all labeled
from the contract. 127 were written before any code was read, and 20 after; one of those 20 is the isolated
fixture. 52 fixtures depend on a decision entry, and each stores its label under that entry's reading (b).
`audit/tests/test_score.py` has 7 multi-response score cases (SC1 to SC7). The suite runs with
`python -I -m unittest discover -s audit/tests -p "test_*.py"`: 197 tests, OK, with 40 expected failures, each
marked strict with the finding or decision that explains it. The replacement passes every fixture under the
proposed readings, and under each entry's reading (b) alone (`test_replacement.py`, 0 mismatches).

| Grader | Pass | Wrong only under (a): a decision | Wrong under every reading: a finding |
|---|---|---|---|
| `case/grade.py` | 117 | 5 (`D-comma-grouping` 2, `D-digits` 3) | 24 (F1: 7, F2: 15, F4: 2, one of them also F2) |
| `case/reference/grade_ref.py` | 104 | 40 (`D-answer-line-form` 37, `D-digits` 3) | 2 (F4) |
| replacement, proposed readings | 146 | 0 | 0 |

Step 4. The reference and `grade.py` have no unit tests, so no assertion is checked against the contract.
Property tests (`audit/tests/properties.py`, seed 20261106, 1,248 cases with labels known by construction,
10 properties): `grade.py` fails P1, thousands separators (48 of 240), and P7, more than 0.01 off (21 of 72).
The reference and the replacement fail none. Fuzzing (`audit/scripts/fuzz.py`, seed 20261106, 20,000 random
responses plus 3 whose answers have 1,000,000 or more digits): both graders raise `decimal.Overflow` on the 3 huge answers
and on nothing else. Every disagreement with the replacement is explained by a finding or a decision, with
0 unexplained. For `grade.py` the counts are F2 737, F1 380, `D-digits` 275, F2 with `D-digits` 22, F1 with
`D-digits` 12, F1 with F2 9, and F5 3. For the reference they are `D-answer-line-form` 3,943, `D-digits` 191,
both together 2, and F5 3. Fuzz counts depend on the generator's distribution. On the 20,000 rows that do not
raise, the two command lines agree with the in-process calls on every verdict. Content-free responses (empty,
whitespace, the restated prompt, the bare answer template, a repeated word, number lists) get `no_answer` or
`incorrect` from all three graders, so none passes the check. Under `grade.py`, though, a `no_answer` leaves
the score's denominator (F3), so a model loses nothing by giving a content-free response.

Step 5, the panel is the 48 stored responses; there is no compute, so nothing new was generated. Two runs of
each grader gave identical verdicts and tables. Every grader gives all 48 responses a verdict. `grade.py`'s
score counts 45 of them (delta-8b: 9 of 12). Stored records: 2 responses stop at the output budget (r12, r36,
both delta-8b, neither with an answer line), and 3 responses get `no_answer` (r12, r36, r44). No response has a
reasoning marker.

| Score | alpha-7b | beta-14b | delta-8b | gamma-32b |
|---|---|---|---|---|
| `grade.py` (as printed) | 75.0 | 83.3 | 33.3 | 100.0 |
| reference (as printed) | 75.0 | 100.0 | 25.0 | 66.7 |
| replacement, proposed readings | 75.0 | 100.0 | 25.0 | 100.0 |
| replacement, `D-answer-line-form` (b) | 75.0 | 100.0 | 25.0 | 66.7 |
| `grade.py` minus replacement | 0.0 | −16.7 (F1: r10, r26) | +8.3 (F3) | 0.0 |

No other decision entry changes a panel verdict. The generation rerun that would size these changes against
rerun noise needs compute, so it was not run.

### Finding F1 (`case/grade.py`, S2): commas end the number

`NUMBER = -?\d+(?:\.\d+)?` has no comma, so the number stops at the first comma. Fixture
`number:0e7d92f33bea1048`, p07 `Answer: 15,000`: the contract says 15000, correct. `grade.py` reads 15, incorrect.
In fixture `number:71c714f04005fff5`, p12 `Answer: 15,000` gets `correct`, a false correct. It breaks R2 ("Commas
in the number are ignored, so 12,500 and 12500 are the same number"), and the prompt allows such commas. Panel:
2 of 48 verdicts (r10 `Answer: 2,250`, r26 `Answer: 15,000`, both beta-14b); r09's extracted value is also
wrong (1 for `1,800`), with the verdict right by chance. Reference: correct (it removes commas).

### Finding F2 (`case/grade.py`, S3): the tolerance is 1% of the reference

`is_correct` accepts |x − r| ≤ 0.01 × max(1, |r|). Fixture `compare:6dad715a6cc98cca`, p02 `Answer: 482`:
the distance is 4 and the contract says incorrect; `grade.py` says correct. The band is wider than 0.01 on 11
of the 12 problems (every |r| > 1); on p07 it accepts 14,850 to 15,150. It breaks R4 ("within 0.01 of the
reference answer"). Panel: 0 of 48 verdicts. Reference: correct (absolute 0.01).

### Finding F3 (`case/grade.py`, S4): the score leaves out `no_answer` and missing problems

`summarize` divides by correct + incorrect. Score case SC1 (6 correct, 6 empty responses) scores 100.0, where the
contract gives 50.0. SC2 (11 correct, p12 missing) scores 100.0 for 91.7. SC4: replacing 3 wrong answers with
empty responses raises a model from 75.0 to 100.0. It breaks R3 and R5 (no answer is incorrect, and the score is
the percentage of the 12 problems). Panel: delta-8b 33.3 instead of 25.0 (3 of its 12 responses). Reference:
correct (divides by the 12 problems).

### Finding F4 (both graders, S3): the distance is rounded to 28 significant digits

`abs(x - r)` runs in the default `decimal` context, which rounds to 28 digits. Fixture
`compare:8001e423a0f0f867`, p06 `Answer: 0.010000000000000000000000000001`: the distance exceeds 0.01 by 1e-30,
so the contract says incorrect. Both graders round it to 0.01 and say correct. It breaks S3.3 (exact comparison).
Panel: 0 of 48. Reference: same defect.

### Finding F5 (both graders, S4.4): a huge number raises and stops the run

The subtraction x − r rounds its result to 28 digits in a context whose largest exponent is 999,999. So it
raises `decimal.Overflow` when the rounded result reaches 10^1,000,000: for every answer with 1,000,001 or more
integer digits, and for 1,000,000 digits when the rounding carries, as with 1,000,000 nines. A 1 followed by
999,999 zeros does not raise. Nothing catches the exception, so the run ends with no verdict file and no scores
(`test_robustness.py`). Isolated fixture `robust:8bbb61cc04a86568`, p02, `Answer: ` followed by 1,000,000
nines. It breaks S4.4. Such a response cannot fit in `max_tokens` 256, so it affects 0 of 48 verdicts.
Reference: same defect.

### Finding F6 (both graders, S4): a second response to a problem counts twice

Neither grader checks for one response per model and problem. In SC5 (p01 answered twice, p12 missing), each
grader scores 100.0 where the contract gives 91.7 or a rejection. In SC6 (all 12 right, plus p01 again), the
reference prints 108.3. It breaks S4.3. The stored run has exactly one response per pair, so it affects 0 of 48.
Reference: same defect.

### Decision entries (for the evaluation's maintainers)

| Entry | (a), proposed | (b) | `grade.py` | Reference | Panel verdicts that (b) changes | Example: (a) / (b) |
|---|---|---|---|---|---|---|
| `D-answer-line-form` | first number in the text after `Answer:`; other text allowed | the text after `Answer:`, stripped, commas removed, must be one number | (a) | (b) | 4 of 48: r03 `$3.50`, r07 `486 students`, r19 `72 km/h`, r35 `28.80 dollars` (all gamma-32b: 100.0 / 66.7) | p05 `Answer: 72 km/h`: correct / no_answer |
| `D-multiple-numbers` | first number | last number | (a) | moot, it follows `D-answer-line-form` (b) | 0 | p03 `Answer: 2500 - 700 + 450 = 2250`: incorrect / correct |
| `D-comma-grouping` | a comma between digits is ignored | only valid thousands groups | neither: commas always end its number (F1); it matches (b) on `1,5` | (a) | 0 | p12 `Answer: 1,5`: correct / incorrect |
| `D-digits` | ASCII 0 to 9 | any Unicode decimal digit | (b) | (b) | 0 | p02 `Answer: ４８６`: no_answer / correct |
| `D-leading-whitespace` | any `str.isspace()` character | space and tab only | (a) | (a) | 0 | p02 no-break space then `Answer: 486`: correct / no_answer |
| `D-tolerance-boundary` | a distance of exactly 0.01 is within | it is not | (a) | (a) | 0 | p01 `Answer: 3.51`: correct / incorrect |

## 2026-11-06T22:53Z: step 6, the result that would change the recommendation (recorded before any review)

The recommendation going into the review is to fix `grade.py` (F1 to F6, and G1 for the protocol). No
review result can change that, because F1 to F3 contradict R2, R4 and R5 on fixtures whose labels need no
reading. The review can change three things:

1. If both reviewers lean `no_answer` or `incorrect` on at least 3 of the 4 `D-answer-line-form` panel cases
   (r03, r07, r19, r35), the report proposes reading (b) instead of (a).
2. If the consensus on r10 or r26 is not `correct`, the report withdraws F1's panel share and reopens the R2
   reading.
3. The gate for calling the replacement more reliable than `grade.py`: (a) it passes every fixture, met;
   (b) it passes every property test, met; (c) scored coverage is complete, met (48 of 48 verdicts,
   denominator 12); (d) its review error rate is lower than `grade.py`'s, with a paired 95% bootstrap interval
   that excludes zero. This panel cannot meet (d). The 2 verdicts where the two graders differ (r10, r26) lie in
   a 6-case stratum, and a within-stratum bootstrap draws neither of them in (4/6)^6 = 8.8% of resamples. So the
   interval starts at 0 even if the consensus sides with the replacement on every case. Meeting (d) needs at
   least 3 such verdicts in a 6-case stratum, or a larger panel.

A wrong reference answer found by the review would be a data finding, fixed by correcting its row. It would
not change the recommendation.

## 2026-11-06T22:54Z: step 6.1 and 6.2, review sample drawn and frozen (no review started)

`python -I audit/scripts/draw_sample.py`, seed 61106. Population: the 48 stored-response verdicts. The
`disagree` stratum (`grade.py`, the reference and the replacement do not all give the same label) has 6:
r03, r07, r10, r19, r26, r35. The `agree` stratum has 42. Both are sampled in full. A `fixture` stratum adds
12 calibration fixtures whose labels need no reading (4 that `grade.py` fails, 8 that it passes). It checks the
reviewers and stays out of the error rate. That makes 60 cases, T001 to T060, in a seeded order. Each case
shows the case id, the check name, the benchmark card's rules 1 to 4 with the reference answer, the rendered
prompt and the response. None shows a source model, grader verdict or stratum (checked by script). The
calibration responses are synthetic and short, so a reviewer may tell them from panel responses.

| Frozen file | sha256 |
|---|---|
| `audit/frozen/round1_cases.jsonl` (the case list) | `ef6054425b8b07b8c3d80625b17a7752bc5881feb6e83d84cb3249a4a5491b92` |
| `audit/frozen/round1_keys.jsonl` (stratum, source, model, verdicts of the three graders) | `b40d1746a7ff5fbd391acd5866c7e9482a91a96a010edccd3ed59879f6cb584d` |
| `audit/frozen/round1_orders.json` (reviewer A and B orders) | `0b1aa110c877eb243cbccfde5b3c15d87e851fe8dd7c1c8a6a5b14aa6878ed02` |
| `audit/frozen/round1_manifest.json` | `878a8299fa3f84eba8a415267e5b3ef967e2650cf17a8569213e22b263b6bcc1` |

Steps 6.3 to 6.5 (batch files, the two reviewer runs, the error rates) were not run, because this exercise
cannot start subagents. `audit/frozen/` has no reviews.

## 2026-11-06T23:00Z: step 7, report

The report is `audit/AUDIT.md` (sha256 `58dbf68f15228c0a1783e96d536ca2e9026b4f6b09673fa1a7bdc54243a80fa4`).
It recommends fixing the grader. The record above lists findings F1 to F6 and G1, and six decision entries
for the maintainers. Each finding's exact counterexample is in `audit/tests/counterexamples/`. Housekeeping:
in-process imports by `audit/scripts/fuzz.py` had written `case/__pycache__` and `case/reference/__pycache__`.
I deleted both, and the script no longer writes bytecode. `case/` again holds only its 7 original files, and
all 6 manifest hashes match.
