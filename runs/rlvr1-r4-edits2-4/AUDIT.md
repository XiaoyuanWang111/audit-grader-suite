# Audit: RLVR1 instruction-following graders

Written 2026-11-12T11:11Z. The two graders under audit score the 11,817 instruction-following rows of Marin's Nemotron RLVR1 data (28,219 constraints, 47 instruction ids):

- **SkyRL reward** ("skyrl"): `final_answer_text`, then `grade_instruction_following`, which runs NVIDIA's verifiable-instructions checkers; reward 1.0 when every constraint passes. NVIDIA's checkers are also the reference implementation.
- **Task-curation gate** ("gate"): `grade_judge._answer_text`, then verifyit's `ifeval` check for every constraint outside `SEMANTIC_INSTRUCTION_CONSTRAINTS`; any failure gives reward 0.0, otherwise the LLM judge decides. The judge is out of scope.

The replacement grader (`audit/lib/contract_grader.py`, v3) implements the contracts with one switch per decision entry. "Proposed" runs every entry at its proposed reading. "Fixes only" runs every entry at the reading NVIDIA's checker follows, so its difference from the SkyRL reward comes from defects alone.

## Error rate and effect on scores

**The error rate is not estimated.** Step 6 (blinded review) was not run, so no grader verdict has been checked against a reviewer consensus, the replacement included. The numbers below are disagreements with the replacement, which inspection shows to be wrong in some cells (section 5). They bound the problem; they are not error rates.

| Panel run | Responses | SkyRL score | Fixes only | Fixes only − SkyRL, points [95% CI] | Proposed − SkyRL, points | Gate pass (rows that reach the judge) | Proposed, gate constraints only − gate, points |
|---|---|---|---|---|---|---|---|
| Qwen3-4B-Instruct-2507, sample0 | 11,817 | 29.5 | 35.3 | +5.8 [+5.2, +6.3] | +4.4 [+3.8, +5.1] | 47.8 | −5.0 [−5.9, −4.2] |
| Qwen3-4B-Instruct-2507, greedy | 1,000 | 29.3 | 35.1 | +5.8 [+4.0, +7.7] | +5.1 [+3.3, +7.1] | 49.9 | −7.1 [−10.0, −4.2] |
| Qwen3-4B-Instruct-2507, greedy rerun | 1,000 | 29.5 | 35.7 | +6.2 [+4.4, +8.0] | +5.2 [+3.4, +7.1] | 50.0 | −6.7 [−9.7, −3.7] |
| Qwen3-4B-Thinking-2507, sample0 | 1,500 | 55.3 | 63.6 | +8.3 [+6.4, +10.1] | +8.8 [+6.8, +10.9] | 63.4 | +3.9 [+1.8, +6.2] |
| Qwen2.5-7B-Instruct, sample0 (held out) | 4,000 | 20.0 | 21.5 | +1.5 [+0.5, +2.4] | +0.7 [−0.4, +1.7] | 33.0 | −6.9 [−8.2, −5.6] |
| OLMo-2-1124-7B-Instruct, sample0 (held out) | 3,998 | 19.1 | 21.0 | +1.9 [+1.2, +2.7] | −0.8 [−1.6, +0.1] | 32.0 | −7.9 [−9.1, −6.6] |

Scores are row-level pass rates in percent; intervals are paired percentile bootstraps over rows (2,000 resamples). Rerunning the greedy decode with identical settings changed the SkyRL score by +0.2 points (16 of 1,000 row verdicts; 506 of 1,000 responses were byte-identical), so every fixes-only change exceeds the rerun difference and has an interval that excludes zero; the proposed changes for the two held-out runs have intervals that include zero. "Held out": the replacement was changed (v2 to v3) after inspecting Qwen3-4B responses; the Qwen2.5-7B and OLMo-2 responses were never inspected.

- **False rewards (RL).** Over the five main runs (22,315 responses, without the rerun), the SkyRL reward is 1.0 on 6,178 responses. The fixes-only replacement fails 566 of them (9.2%); the proposed replacement fails 938 (15.2%), 924 when the three language checks are left to the SkyRL verdict.
- **Gate.** The gate passes 9,692 of the 22,315 responses to the judge; on the gate's own constraints the proposed replacement fails 2,934 of them (30.3%).
- **Constraint level.** Over the five main runs, SkyRL disagrees with the proposed replacement on 5,501 of 53,375 constraint verdicts (10.3%) and the gate on 8,249 of 48,526 (17.0%); the gate and SkyRL disagree with each other on 7,515. Over all six runs, each disagreement was replayed with the non-proposed reading of every decision entry the check reads, alone and in pairs: SkyRL 2,601 disagreements stay (1,057 false passes, 1,544 false fails), 3,023 are explained by decisions, 84 are extraction failures; gate 5,994 stay (4,383 false passes, 1,611 false fails), 2,494 decisions, 113 extraction failures.
- **Content-free answers.** An empty answer gets SkyRL reward 1.0 on 1,702 of 11,817 rows (14.4%) and passes the gate on 810 (6.9%); under `D-empty-response`'s proposed reading it fails every check. The prompt restated verbatim gets SkyRL 1.0 on 746 rows and passes the gate on 1,365.

**Recommendation: fix both graders**, and run step 6 before relying on any of the score changes above. The gate's verifyit checks implement a different requirement than the prompt states for at least nine instruction ids (F6, F9 to F14, F16, F17), and the gate has 26 checker findings in all; NVIDIA's checkers, which are both the SkyRL reward and the reference, have 32 (10 of them shared with the gate). Both pipelines also grade unclosed reasoning as the answer (G1). A fix should start from the replacement and its fixtures, with each decision entry set by the maintainers. What step 6 must still show is recorded in section 6.

## Scope and what was not done

- Offline exercise. No issue tracker (the record is `audit/ISSUE.md`), no repository or research branch, no Hugging Face dataset, no job launcher, no network; fixtures are runnable tests under `audit/tests/`, frozen files under `audit/frozen/`.
- Step 5 used only the stored panel (`case/panel/`, 23,315 responses); nothing was generated.
- Step 6 was not run (no reviewers): no sample was drawn, frozen or rendered.
- The LLM judge (task curation) was not audited; for the four judged instruction ids the gate has no deterministic verdict. `grade_nemotron_instructions` (the SkyRL path when `verifyit_enabled` is set) was read but not run on the panel.
- `nemotron_tasks.py`, `answer_extraction.py` and `grade_judge.py` cannot be imported here. The audit runs the real `final_answer_text` (its `aime/utils.py` import is satisfied by a stub that `final_answer_text` never calls) and compiles `_answer_text` and `_passes` from the pinned `grade_judge.py` (sha256 `fcc96631…`), see `audit/lib/harness.py`.

## 1. Pinned inputs

Full record in `audit/ISSUE.md`. All 176 files of `case/MANIFEST.sha256` matched. Pinned: Marin `af9c6789`, NVIDIA verifiable-instructions `f46a5ac8` (reference), dataset revision `600262dd` with one sha256 per row (`audit/work/row_hashes.tsv`, file sha256 `5e91ee6a…`), the Python lockfile (nltk 3.10.3, langdetect 1.0.9 with seed 0), `punkt_tab` by hash, the panel's models, revisions, token limits and vLLM version. Unpinned or unverified: NLTK data is downloaded at run time when missing (G4); the session's routing of these rows (G5) and the run's `verifyit_enabled` value are not in the case.

## 2. Contracts and decision entries

`audit/CONTRACTS.md` (sha256 `cbbfdcae…`, recorded 2026-11-12T10:30:49Z before any grader code was read) states each check's pass and fail conditions from the prompt text. It proposed 39 decision entries; 7 more were added after reading the code or the step 4 results, each with its reason in `audit/ISSUE.md`: 46 in all. The table gives, for each entry, the panel verdicts (all six runs) whose disagreement with the proposed replacement the entry's other reading explains, alone or with one other entry; a verdict can count under several entries.

| Entry | Reading A | Reading B | Example (A / B) | Proposed | NVIDIA reads | SkyRL verdicts | Gate verdicts |
|---|---|---|---|---|---|---|---|
| D-empty-response | empty answer fails every check | empty answer passes checks that only forbid | `""` on no_comma: fail / pass | A | B | 1 | 0 |
| D-word-units | hyphenated words and contractions are one word | split at `-` and `'` | `well-known don't`: 2 / 4 words | A | B | 188 | 137 |
| D-word-cjk | each CJK character is a word | a run between spaces is a word | `我喜欢猫`: 4 / 1 | open (B used) | B | 45 | 52 |
| D-word-case | word comparisons ignore case | exact case | `Development is…` for development: pass / fail | A | mostly A | 250 | 138 |
| D-keyword-inflection | only the exact word | inflected forms count | `cats` for cat: fail / pass | A | B (substring) | 97 | 39 |
| D-sentence-split | a line end ends a sentence | only `.!?` do | `Title\nOne. Two.`: 3 / 2 | A | B | 120 | 133 |
| D-capital-word | `I`, `A` are all-capital words | only 2+ letters | `I am OK`: 2 / 1 | A | A | 5 | 80 |
| D-language-mixed | the response is in the language (names, code allowed) | every sentence is | French answer with a line `Steps: 20, Sampler: Euler a`: pass / fail | A | A | 15 | 14 |
| D-two-different | parts differ after stripping | parts differ in substance | `Yes ****** Yes.`: pass / fail | A | A | 0 | 0 |
| D-repeat-center | only a middle word may change | any inner word | `Laughter is the finest medicine`: fail / pass | A | B | 14 | 12 |
| D-repeat-original | an unchanged copy breaks the rule | unchanged copies are ignored | 2 variants + 1 copy: fail / pass | A | A | 0 | 21 |
| D-lowercase-count | lowercase occurrences only | case-insensitive counts | `The the the`, N 2: pass / fail | A | — | 13 | 5 |
| D-lowercase-scope | each lowercase word ≤ N times | all lowercase words together ≤ N | `The cat sat on a mat.`, N 2: pass / fail | A | B | 279 | 24 |
| D-placeholder | any non-empty `[text]` | fill-in slots only | `[1]`: counts / not | A | A | 0 | 0 |
| D-postscript-case | marker case as given | case-insensitive | `p.s. hi`: fail / pass | A | B | 60 | 60 |
| D-postscript-position | the postscript is the last paragraph | anywhere | `P.S. hi\n\nMore.`: fail / pass | A | B | 66 | 61 |
| D-bigram-odd | odd word count may end with a one-word group | all groups two words | `<<I am>> <<here>>`: pass / fail | A | A | 32 | — |
| D-constrained-extra | other text may accompany one option | the answer is exactly one option | `My answer is yes. Because…`: pass / fail | A | A | 0 | 75 |
| D-json-value | object or array only | any JSON value | `"hello"`: fail / pass | A | B | 0 | 0 |
| D-section-case | splitter ignores case | exact case | `Section 1` for SECTION: pass / fail | A | B | 22 | 1 |
| D-section-label | label may be a number, numeral or letter | digits only | `SECTION A`: pass / fail | A | B | 0 | 0 |
| D-sections-preamble | a title line may precede the first marker | any text may | intro paragraph, then markers: fail / pass | A | B | 6 | 6 |
| D-bullet-markers | `*`, `-`, `+` and nested bullets count | top-level `*` only | `+ a\n+ b` for 2: pass / fail | A | B | 0 | 0 |
| D-highlight-bold | `**bold**` is a highlight | italics only | `**a** **b**` for 2: pass / fail | A | A | 0 | 0 |
| D-hyphens-single | one sentence fails | one sentence passes | `The sun rose.`: fail / pass | B | B | 765 | 774 |
| D-hyphens-spaces | spaces inside sentences allowed | no whitespace at all | `The sun rose.-Birds sang.`: pass / fail | A | A | 524 | 738 |
| D-brackets-each | each word in its own brackets | one pair around everything | `[The sun is bright]`: fail / pass | A | A | 21 | 169 |
| D-title-position | title anywhere | title opens the response | `Intro.\n<<T>>`: pass / fail | A | A | 0 | 0 |
| D-consecutive-order | neighbours in either order | ascending only | `Big apples`: fail / pass | A | B | 45 | 40 |
| D-consecutive-script | Latin letters only | any alphabet (code-point order) | Cyrillic `в г`: pass / fail | A | B | 109 | 38 |
| D-palindrome-unit | a whole word or phrase | a palindromic run inside a word | `never`: fail / pass | A | A | 202 | 9 |
| D-palindrome-length | at least 3 letters | any length (`a`, `I`) | `I saw the sea.`: fail / pass | A | B | 211 | 7 |
| D-word-count-exact | exactly N times | at least N times | 3 occurrences for 2: fail / pass | A | B | 159 | 159 |
| D-paragraph-blank-lines | any run of blank lines separates | `\n\n\n\n` makes an empty paragraph | `a\n\n\n\nb` for 2: pass / fail | A | B | 6 | 2 |
| D-divider-form | the given divider line only | any thematic break | `---` for `***`: fail / pass | A | A | 2 | 5 |
| D-divider-edges | no divider or separator at the start or end | edge ones ignored | `a\n***\nb\n***`: fail / pass | A | B | 140 (+30 two_responses) | 65 (+30) |
| D-divider-blank-lines | blank lines inside a divided part do not split it | they do | `a\n\nb\n***\nc` for 2: pass / fail | A | A | 95 | 357 |
| D-letter-case | letter counts ignore case | exact case | `A a` for a: 2 / 1 | A | A | 0 | 0 |
| D-letter-script | any Unicode letter counts | Latin letters only | `你好吗`, at least 3: pass / fail | A | B | 96 | — |
| D-comma-chars | `,，、،﹐` | ASCII `,` | `你好，世界`: fail / pass | A | B | 27 | 27 |
| D-dot-chars | `.．。…` | ASCII `.` | `你好。`: fail / pass | A | B | 55 | 55 |
| D-exclamation-chars | `!！¡‼❗❕` | ASCII `!` | `好！`: fail / pass | A | B | 9 | 9 |
| D-end-markup | closing markup after the phrase allowed | nothing may follow | `**Any other questions?**`: pass / fail | A | B | 2 | 30 |
| D-end-case | the phrase's case must match | case-insensitive | `any other questions?`: fail / pass | A | B | 162 | 0 |
| D-quote-chars | `"…"` or `“…”` | ASCII `"` only | `“Hi”`: pass / fail | A | B | 1 | 0 |
| D-start-end-single | a one-word answer passes | two words needed | `Hello`: pass / fail | A | B | 42 | 13 |

`D-divider-edges` also covers a `******` separator at the start or end of a two-response answer: all 30 SkyRL and gate passes of `combination:two_responses` that the replacement fails have one (the replacement has no switch for this case; counted by inspection). The largest decisions for the maintainers are `D-hyphens-single` and `D-hyphens-spaces` (most `sentence_hyphens` answers are one long hyphenated sentence), `D-lowercase-scope`, `D-word-case`, the two palindrome entries and `D-word-count-exact`.

## 3. Fixtures

`audit/fixtures.jsonl` has 853 labeled responses (fields `instruction_id`, `kwargs`, `response`, `label`, plus `id`, `source`, `label_source`, `thinking`, `note`): 214 hand-written from the contracts (`audit/lib/fixtures_src.py`), 460 metamorphic (46 checks: bases, 375 ignored edits and 46 forbidden edits, after removing responses already in the set), 71 content-free and 108 minimal fuzz reproducers. Hand-written and metamorphic labels come from the contracts; content-free and fuzz labels come from the replacement (`label_source: replacement`), except one hand label (repeated lowercase "answer" is English, which langdetect calls Afrikaans).

`audit/tests/test_fixtures.py` runs every fixture on all three graders and marks each verdict that differs from the label today as `xfail(strict=True)` with its finding or decision id (`audit/tests/expected_wrong.json`), so a fix must remove the mark. Run from `audit/`:

```
../.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q tests
```

Result: 2,886 passed, 77 skipped (judged constraints have no gate verdict), 450 xfailed. The replacement has 3 expected failures, each recorded with its reason: an HTML tag just before a closing `>>` on bigram_wrapping, the whole-text language check that misses one English sentence in a French answer, and the Afrikaans case above. Five grader verdicts on fuzz lines whose label is only the replacement's (a title made of an HTML tag; `İ` read as the letter i) are marked "unattributed"; their labels are uncertain.

## 4. Reference comparison and stress tests

- **Gate against the reference.** On the panel, the gate and NVIDIA's checkers disagree on 7,515 of 48,526 gate verdicts (five main runs). The largest cells, over all six runs: `count:lowercase_counting` 1,623 (F10), `keywords:no_adjacent_consecutive` 915 (F11), `detectable_format:square_brackets` 856 (F13), `copy:repeat_phrase` 577 (F6), `length_constraints:number_paragraphs` 561 (F16), `detectable_format:sentence_hyphens` 500 (decisions), `paragraphs:paragraphs2` 443 (F17). The per-check table in section 5 classifies each grader's disagreements with the contract as defect or decision. The reference has no unit tests, and Marin's verifyit tests are not in the case, so no test assertions could be listed.
- **Metamorphic tests** (`audit/scripts/run_metamorphic.py`, 46 checks, 375 ignored edits: numbered label, bullet, bold, italics, HTML tag, typographic quotes, typographic apostrophe, punctuation after a word, blank line, trailing newline). SkyRL flipped a passing answer to fail 57 times on 14 checks (F5, F7, F34, F36, F38, F39, F40, F45, F46, and `D-paragraph-blank-lines`); the gate 18 times on 8 checks (F29, and its tokenizer F42 and sentence splitter F43: a `- ` bullet or an HTML tag becomes the first word, a `1.` label becomes a sentence). Forbidden edits that still passed: gate on lowercase_counting, square_brackets, no_adjacent_consecutive, start_end, number_paragraphs and paragraphs (F10, F13, F11, F44, F16, F17); both on word_count_different_numbers (`D-word-count-exact`); SkyRL on count_unique (`D-word-case`) and response_language (F47).
- **Fuzzing** (`audit/scripts/run_fuzz.py`, 1,000 random token strings per check, kwargs drawn from the data; counts, not rates): the only exception is `IndexError` in NVIDIA's `last_word:last_word_answer`, 48 times, always on text with no whitespace-separated token (G2). No exception stops a run: SkyRL turns it into an infrastructure error for the row, the gate's `_passes` into a failed check. The fuzzer's verdict disagreements confirmed F1, F27, F31, F36, F42 and found the lone-quote case of F32.
- **Score-level transforms.** Both graders are all-or-nothing per row (`grading_mode` binary on every row); there is no loose-grading transform.
- **Content-free responses** (`audit/scripts/run_content_free.py`, every row). Empty answer: SkyRL passes `count_unique`, `lowercase_counting`, `bigram_wrapping`, `sentence_hyphens`, `square_brackets`, `first_word_sent`, `last_word_sent`, `forbidden_words`, `no_adjacent_consecutive`, the three punctuation checks and `response_language` (F41) on every row, and the relation checks with "less than"; `last_word_answer` raises on all 625 rows (G2). Gate: the forbidding checks and "less than" relations. The verbatim prompt passes SkyRL's `constrained_response` on all 120 rows (it contains all three options, F24), `postscript` on 497 of 644 (F28), `palindrome` on all 618 (one-letter tokens), `paragraphs` on 463 of 576 (an inline `***`, F18); and the gate's `lowercase_counting` on 869 of 869 (F10), `no_adjacent_consecutive` on 624 (F11), `paragraphs`/`paragraphs2` on 538/453 (F17).

## 5. Model panel

Stored records (`case/panel/`, six runs, 23,315 responses):

| Run | Responses | Stopped at the token limit | Thinking: `</think>` present | Extraction failures | Empty SkyRL graded text | SkyRL infra errors |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct sample0 | 4,000 | 65 | — | — | 3 | 0 |
| Qwen3-4B-Instruct greedy | 1,000 | 92 | — | — | 1 | 0 |
| Qwen3-4B-Instruct greedy rerun | 1,000 | 81 | — | — | 2 | 0 |
| Qwen3-4B-Instruct sample0 | 11,817 | 620 | — | — | 16 | 1 |
| Qwen3-4B-Thinking sample0 | 1,500 | 166 | 1,361 | 139 (all at the token limit) | 1 | 0 |
| OLMo-2-7B-Instruct sample0 | 3,998 | 39 | — | — | 1 | 0 |

The 139 thinking responses whose reasoning never closed are graded by both pipelines as if the reasoning were the answer (G1): SkyRL rewards 1 of them and the gate passes 18 to the judge. Scored coverage: the SkyRL reward scores every response except the 1 infrastructure error; the gate scores every deterministic constraint; the replacement scores everything (its language verdicts are langdetect approximations).

Per check, all six runs (55,783 constraint verdicts; 50,724 gate verdicts). "Defect FP / FF": grader passes / fails that the contract contradicts under every decision reading the replacement can switch (alone or in pairs); "decision": disagreements that some non-proposed reading explains.

| Check | Data constraints | Panel verdicts | SkyRL pass | Gate pass | Proposed pass | SkyRL defect FP / FF | SkyRL decision | Gate defect FP / FF | Gate decision |
|---|---|---|---|---|---|---|---|---|---|
| change_case:capital_word_frequency | 601 | 1,207 | 76.2% | 79.5% | 75.5% | 2 / 3 | 16 | 1 / 19 | 81 |
| change_case:english_capital | 772 | 1,534 | 45.1% | 55.0% | 49.3% | 20 / 70 | 14 | 99 / 7 | 4 |
| change_case:english_lowercase | 604 | 1,208 | 69.0% | 77.4% | 69.0% | 1 / 1 | 1 | 122 / 11 | 10 |
| combination:two_responses | 253 | 557 | 81.5% | 81.5% | 76.1% | 30 / 1 | 0 | 30 / 1 | 0 |
| copy:repeat_phrase | 554 | 1,059 | 8.9% | 45.6% | 3.0% | 53 / 4 | 15 | 456 / 31 | 22 |
| count:count_unique | 687 | 1,341 | 15.0% | judged | 22.3% | 6 / 88 | 20 | — | — |
| count:counting_composition | 1 | 1 | 0.0% | 0.0% | 0.0% | 0 / 0 | 0 | 0 / 0 | 0 |
| count:lowercase_counting | 869 | 1,712 | 15.2% | 88.4% | 29.5% | 41 / 0 | 285 | 1,167 / 133 | 39 |
| detectable_content:number_placeholders | 585 | 1,201 | 91.5% | 91.4% | 90.9% | 1 / 1 | 0 | 0 / 1 | 0 |
| detectable_content:postscript | 644 | 1,277 | 83.3% | 72.4% | 57.6% | 198 / 1 | 123 | 68 / 5 | 118 |
| detectable_format:bigram_wrapping | 575 | 1,157 | 19.4% | judged | 3.4% | 184 / 0 | 1 | — | — |
| detectable_format:constrained_response | 120 | 243 | 89.7% | 57.6% | 88.5% | 3 / 0 | 0 | 0 / 0 | 75 |
| detectable_format:json_format | 133 | 266 | 82.0% | 82.0% | 82.0% | 0 / 0 | 0 | 0 / 0 | 0 |
| detectable_format:multiple_sections | 453 | 917 | 86.9% | 85.1% | 81.0% | 66 / 2 | 28 | 36 / 4 | 7 |
| detectable_format:number_bullet_lists | 512 | 1,019 | 80.1% | 81.6% | 81.6% | 3 / 18 | 0 | 0 / 0 | 0 |
| detectable_format:number_highlighted_sections | 555 | 1,070 | 93.4% | 93.4% | 92.7% | 6 / 1 | 0 | 5 / 0 | 0 |
| detectable_format:sentence_hyphens | 669 | 1,300 | 19.6% | 19.5% | 79.0% | 0 / 5 | 767 | 0 / 0 | 778 |
| detectable_format:square_brackets | 553 | 1,079 | 16.2% | 95.2% | 18.3% | 12 / 44 | 32 | 655 / 2 | 169 |
| detectable_format:title | 589 | 1,189 | 97.1% | 97.1% | 96.6% | 0 / 2 | 0 | 0 / 2 | 0 |
| first_word:first_word_answer | 557 | 1,089 | 72.2% | 85.1% | 84.7% | 0 / 74 | 62 | 5 / 1 | 1 |
| first_word:first_word_sent | 540 | 1,024 | 32.3% | 43.3% | 41.3% | 2 / 64 | 52 | 13 / 3 | 22 |
| keywords:existence | 932 | 1,856 | 75.6% | 72.1% | 68.8% | 33 / 0 | 91 | 0 / 1 | 59 |
| keywords:forbidden_words | 836 | 1,687 | 96.6% | 96.6% | 96.7% | 1 / 0 | 3 | 1 / 0 | 3 |
| keywords:frequency | 607 | 1,200 | 81.0% | 80.9% | 79.8% | 13 / 16 | 31 | 0 / 0 | 15 |
| keywords:keyword_specific_position | 676 | 1,341 | 2.8% | 3.7% | 3.7% | 3 / 8 | 13 | 5 / 5 | 8 |
| keywords:letter_frequency | 783 | 1,507 | 56.9% | 56.9% | 56.5% | 0 / 0 | 0 | 0 / 0 | 0 |
| keywords:no_adjacent_consecutive | 818 | 1,499 | 23.7% | 76.8% | 23.8% | 65 / 2 | 154 | 818 / 18 | 86 |
| keywords:palindrome | 618 | 1,165 | 90.3% | 63.4% | 74.4% | 0 / 34 | 221 | 0 / 137 | 13 |
| keywords:start_end | 499 | 989 | 29.6% | 37.2% | 34.2% | 4 / 5 | 45 | 55 / 7 | 21 |
| keywords:word_count_different_numbers | 526 | 1,015 | 54.2% | 54.2% | 36.3% | 162 / 121 | 211 | 159 / 120 | 213 |
| keywords:word_once | 917 | 1,808 | 25.5% | 25.9% | 72.3% | 23 / 803 | 117 | 1 / 766 | 100 |
| language:response_language | 780 | 1,600 | 88.3% | judged | 88.1% | 2 / 0 | 0 | — | — |
| last_word:last_word_answer | 625 | 1,285 | 69.7% | 76.0% | 75.0% | 0 / 63 | 5 | 14 / 2 | 0 |
| last_word:last_word_sent | 600 | 1,203 | 27.8% | 33.3% | 26.9% | 12 / 33 | 31 | 46 / 7 | 38 |
| length_constraints:nth_paragraph_first_word | 515 | 1,048 | 38.9% | 38.4% | 38.0% | 14 / 4 | 2 | 4 / 0 | 0 |
| length_constraints:number_paragraphs | 690 | 1,345 | 74.1% | 42.4% | 63.5% | 22 / 8 | 159 | 26 / 201 | 265 |
| length_constraints:number_sentences | 562 | 1,131 | 70.5% | 69.7% | 72.9% | 15 / 59 | 71 | 19 / 71 | 70 |
| length_constraints:number_words | 729 | 1,443 | 73.6% | 70.5% | 73.5% | 2 / 6 | 17 | 7 / 56 | 7 |
| letters:letter_counting | 497 | 961 | 61.7% | judged | 66.1% | 0 / 0 | 97 | — | — |
| letters:letter_counting2 | 705 | 1,346 | 54.5% | 54.5% | 53.8% | 1 / 0 | 0 | 1 / 0 | 0 |
| paragraphs:paragraphs | 576 | 1,150 | 83.5% | 97.1% | 72.4% | 54 / 3 | 78 | 132 / 0 | 147 |
| paragraphs:paragraphs2 | 744 | 1,391 | 62.5% | 94.3% | 62.5% | 0 / 0 | 5 | 435 / 0 | 2 |
| punctuation:no_comma | 730 | 1,523 | 88.7% | 88.7% | 86.9% | 0 / 0 | 27 | 0 / 0 | 27 |
| punctuation:punctuation_dot | 847 | 1,749 | 51.6% | 51.6% | 48.5% | 0 / 0 | 55 | 0 / 0 | 55 |
| punctuation:punctuation_exclamation | 627 | 1,284 | 95.3% | 95.3% | 94.6% | 0 / 0 | 9 | 0 / 0 | 9 |
| startend:end_checker | 537 | 997 | 87.4% | 68.3% | 71.0% | 3 / 0 | 164 | 3 / 0 | 30 |
| startend:quotation | 417 | 810 | 85.9% | 86.0% | 86.0% | 0 / 0 | 1 | 0 / 0 | 0 |

Checked by inspection (Qwen3-4B runs only, excerpts of the graded text): the SkyRL `postscript` false passes were "P.S." in the middle of the text (F28, replacement right); the SkyRL `english_capital` false fails were plain upper-case English such as "SCHOOL OF REALISM" (F47; 84 of the 192 all-capital answers that SkyRL fails detect as English once lower-cased); the gate's `palindrome` false fails were Arabic or Cyrillic palindromes and "A man, a plan, a canal: Panama" (F42); SkyRL's `number_sentences` false fails include Chinese answers whose `。` sentences count as one (F48). The replacement itself was wrong on per-sentence language detection (v2; v3 detects on the whole text only), on `<<word>>` groups read as HTML tags (v2, fixed in v3), and on letter counts inside HTML (fixed in v3). Its remaining weak cells, where the defect counts above need step 6: the language checks, phrase palindromes found by chance across words, `sentence_hyphens` answers without terminal punctuation, and the gate `postscript` false passes (68), which were not inspected.

Three nondeterminism facts: the greedy rerun (above); the 77 rows with `nth_paragraph > num_paragraphs` (161 panel responses), where SkyRL redraws the paragraph index and two seeds gave different rewards on 6 responses and reward 1.0 on 9 (G3); langdetect is seeded (0) in both the reference and the replacement.

## 6. Blinded review: not run

No reviewers were available, so no sample was drawn, frozen or rendered, and no error rate or interval exists. The result recorded before any review (also in `audit/ISSUE.md`) that would change the recommendation: the recommendation to fix both graders stands unless a review of held-out responses finds that the replacement (at the maintainers' readings) is not more accurate than each grader, with a paired interval for the difference that excludes zero, or that a grader's error rate has an upper bound below 2%. What the review needs: a seeded sample stratified by grader–replacement disagreement, drawn from held-out responses (the Qwen2.5-7B and OLMo-2 runs, which no one has inspected), with all disagreements of the cells marked weak in section 5 included; two reviewers per case with `skill/references/reviewer-prompt.md`; per-stratum error rates weighted by stratum size, bootstrap intervals, the zero-error correction of step 6.5, Cohen's kappa, and the paired SkyRL − replacement and gate − replacement differences.

## 7. Findings

Every counterexample is run by `repro.py` (exact input inside it). Command, from `<W>/audit`: `../.venv/Scripts/python.exe repro.py <id>` (or `repro.py all`); each output line is `finding grader check grader=<verdict> contract=<label>`. Inputs are written as JSON strings (`\n` is a line break). "Share" is the check's defect cell from section 5 (panel verdicts, all six runs), shared between findings on the same check where noted. "Reference" is the status in NVIDIA's checker; for SkyRL findings NVIDIA's checker is the grader itself, so the column gives the gate's status instead.

| Id | Grader | Check | Counterexample (instruction id, kwargs, response) → grader verdict; contract | Contract broken | Share | Reference / other grader |
|---|---|---|---|---|---|---|
| F1 | SkyRL | keywords:existence, frequency, word_once, word_count_different_numbers | existence `{"keywords": ["art", "home"]}` `"We start at home."` → pass; fail | a keyword is a whole word, never part of another word | existence 33 FP; frequency 13 / 16 | gate correct (word boundary) |
| F2 | both | keywords:word_once | `{"keyword": "river"}` `"The river flows into another river."` → fail, fail; pass | "Include keyword X" sets no upper bound | SkyRL 803 FF, gate 766 FF of 1,808 (44%) | in reference |
| F3 | both | keywords:word_count_different_numbers | `{"keyword": "tree", "relation": "less than", "frequency": 2}` `"A tree and a tree."` → fail, fail; pass. Same kwargs, `"Nothing here."` → pass, pass; fail | the text says "should appear 2 times"; the relation is not shown | SkyRL 162 / 121, gate 159 / 120 of 1,015 | in reference |
| F4 | SkyRL | copy:repeat_phrase | `{"phrase": "Laughter is the best medicine", "small_n": 2}` `"Laughter is the best medicine. Laughter is our best medicine."` → pass; fail | every repetition must be transformed | 53 FP / 4 FF of 1,059 (with F5) | gate has F6 |
| F5 | SkyRL | copy:repeat_phrase | `{"phrase": "Don't judge a book by cover", "small_n": 2}` `"Don’t judge the book by cover. Don’t judge one book by cover."` → fail; pass | markup, quotes and apostrophe style do not change the words | shared with F4 | gate has F6 |
| F6 | gate | copy:repeat_phrase | same kwargs as F4, `"Laughter is our best medicine. Laughter is my best medicine."` → fail; pass. `"Laughter is the best medicine. Laughter is the best medicine."` → pass; fail | repetitions must be transformed, not copied | 456 FP / 31 FF of 1,059 | reference has F4, F5 |
| F7 | SkyRL | count:count_unique | `{}` `"Apples, pears, plums."` → fail; pass | punctuation is not a word | 6 / 88 of 1,341 | judged in task curation |
| F8 | SkyRL | count:counting_composition | `{"n_sent": 3, "n_words": 2}` `"Birds sing. Cats sleep. Dogs bark.\n* * *\nFish swim. Bees buzz. Cows moo.\n* * *\nKids play. Moms cook. Dads read."` → fail; pass | the instructed `* * *` divider and 2-word sentences | 1 constraint in the data | gate has F9 |
| F9 | gate | count:counting_composition | same kwargs, the nine sentences without dividers → pass; fail | 3 paragraphs, exact counts | 1 constraint | reference has F8 |
| F10 | gate | count:lowercase_counting | `{"N": 2}` `"the the the end"` → pass; fail. `"I AM OK."` → fail; pass | "at most N times" | 1,167 / 133 of 1,712 | reference reads `D-lowercase-scope` B |
| F11 | gate | keywords:no_adjacent_consecutive | `{}` `"A big dog."` → pass; fail. `"The the end."` → fail; pass | consecutive first letters, not repeated words | 818 / 18 of 1,499 | reference checks letters (F37) |
| F12 | gate | change_case:english_capital, english_lowercase | `{}` `"LE TEMPS EST TRÈS BEAU AUJOURD'HUI ET NOUS ALLONS AU PARC AVEC NOS AMIS."` → pass; fail | "in English" | capital 99 FP, lowercase 122 FP | reference checks the language (F41, F47) |
| F13 | gate | detectable_format:square_brackets | `{}` `"[The] sun is bright."` → pass; fail | every word bracketed | 655 / 2 of 1,079 | reference has F39 |
| F14 | gate | detectable_format:sentence_hyphens | `{}` `"Well-known. Fine-tuned."` → pass; fail | no space between sentences | 0 on the panel (decisions dominate) | reference correct here |
| F15 | SkyRL | detectable_format:sentence_hyphens | `{}` `"The well-known poet arrived.-We listened."` → fail; pass | a hyphen inside a sentence is allowed | 0 / 5 of 1,300 | gate: `D-hyphens-spaces` B |
| F16 | gate | length_constraints:number_paragraphs | `{"num_paragraphs": 2}` `"First paragraph.\n***\nSecond paragraph."` → fail; pass | paragraphs are separated by `***` | 26 / 201 of 1,345 | reference has F18 |
| F17 | gate | paragraphs:paragraphs, paragraphs2 | paragraphs2 `{}` `"First part.\n\nSecond part.\n\nThird part."` → pass; fail. paragraphs `{}` `"First part.\n\nSecond part."` → pass; fail | exactly 2 paragraphs; the divider for paragraphs | 132 FP of 1,150; 435 FP of 1,391 | reference correct |
| F18 | SkyRL | length_constraints:number_paragraphs, paragraphs:paragraphs | `{"num_paragraphs": 2}` `"***Note*** first part.\n***\nSecond part."` → fail; pass | the divider is a line, not `***` inside text | 22 / 8 of 1,345; 54 / 3 of 1,150 | gate has F16, F17 |
| F19 | SkyRL | detectable_format:multiple_sections | `{"num_sections": 2, "section_spliter": "SECTION"}` `"SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text."` → pass; fail | "must have 2 sections" | 66 / 2 of 917 (with F20) | gate exact (correct) |
| F20 | both | detectable_format:multiple_sections | same kwargs, `"SECTION 1\nSee SECTION 2 below for details."` → pass, pass; fail | a mention is not a section marker | gate 36 / 4 of 917 | in reference |
| F21 | SkyRL | detectable_format:number_bullet_lists | `{"num_bullets": 2}` `"* Apples\n* Pears\n---\nThat is all."` → fail; pass | a rule, an italic line or `-5` is not a bullet | 3 / 18 of 1,019 (with F22) | gate correct |
| F22 | both | detectable_format:number_bullet_lists | same kwargs, `"* Apples\n* Pears\n* * *\nDone."` → fail, fail; pass | a divider is not a bullet | gate 0 on the panel | in reference |
| F23 | both | detectable_format:number_highlighted_sections | `{"num_highlights": 2}` `"Compute 2 * 3 * 4 and *done*."` → pass, pass; fail | multiplication signs are not markup | SkyRL 6 / 1, gate 5 / 0 of 1,070 | in reference |
| F24 | SkyRL | detectable_format:constrained_response | `{}` `"My answer is yes. My answer is no."` → pass; fail | one of the options | 3 FP of 243; 120 of 120 restated prompts | gate correct |
| F25 | both | detectable_format:json_format | `{}` `"NaN"` → pass, pass; fail | JSON | 0 on the panel | in reference |
| F26 | gate | detectable_format:json_format | `{}` "```JSON\n{\"a\": 1}\n```" → fail; pass | markdown ticks allowed | 0 on the panel | reference correct |
| F27 | both | detectable_content:number_placeholders | `{"num_placeholders": 2}` `"Dear [], meet me at []."` → SkyRL pass; fail. `"Dear [ ], meet me at [ ]."` → pass, pass; fail | a placeholder has content | 1 / 1 and 0 / 1 of 1,201 | whitespace case in reference |
| F28 | SkyRL | detectable_content:postscript | `{"postscript_marker": "P.S."}` `"Remember to read the P.S. section of the letter.\n\nThanks."` → pass; fail. `"Here is my answer.\n\nP.P.S. One more note."` → pass; fail | a postscript starts with the marker | 198 / 1 of 1,277; 497 of 644 restated prompts | gate correct here (F29) |
| F29 | gate | detectable_content:postscript | `{"postscript_marker": "P.S."}` `"Here is my answer.\n\n**P.S.** Thanks for asking."` → fail; pass | markup is not part of the marker | 5 FF of 1,277 | reference correct |
| F30 | gate | detectable_format:title | `{}` `"<< >>\nThe rain falls softly."` → pass; fail | a title has text | 0 on the panel | reference correct |
| F31 | both | startend:end_checker | `{"end_phrase": "Any other questions?"}` `"Here is the plan. Many other questions?"` → SkyRL pass; fail. Gate: `{"end_phrase": "Is there anything else I can help with?"}` `"SectionIs there anything else I can help with?"` → pass; fail | the phrase, not the end of a longer word | SkyRL 3 FP, gate 3 FP of 997 | in reference (more often: it ignores case) |
| F32 | gate | startend:quotation | `{}` `"'Hello there.'"` → pass; fail | double quotation marks | 0 on the panel | reference correct |
| F33 | both | combination:two_responses | `{}` `"A cat.\n*******\nA dog."` → pass, pass; fail | six asterisks | 0 on the panel (the 30 FP are `D-divider-edges`) | in reference |
| F34 | SkyRL | first_word_answer, first_word_sent, nth_paragraph_first_word, start_end | first_word_answer `{"first_word": "development"}` `"Development, in short, matters."` → fail; pass. nth_paragraph `{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}` `"Clouds gathered.\n\n**Rain** fell all night."` → fail; pass | punctuation and markup are not part of a word | 74 FF of 1,089; 64 FF of 1,024; 4 FF of 1,048 | gate correct (F42 aside) |
| F35 | SkyRL | keywords:start_end | `{}` `"! !"` → pass; fail | an answer with no words does not start with a word | 4 FP of 989 | gate correct |
| F36 | SkyRL | keywords:palindrome | `{}` `"* Apples\n* Pears"` → pass; fail. `"Paddle the kayak."` → fail; pass | `*` is not a palindrome; punctuation is not part of the word | 0 / 34 of 1,165 (+221 `D-palindrome-length`); 618 of 618 restated prompts | gate F42 |
| F37 | SkyRL | keywords:no_adjacent_consecutive | `{}` `"\"apple\" \"banana\" were eaten."` → pass; fail | first letters of words, not of tokens | 65 / 2 of 1,499 | gate F11 |
| F38 | SkyRL | keywords:keyword_specific_position | `{"keyword": "river", "n": 2, "m": 3}` `"We walked far. Then, the river appeared."` → fail; pass | a comma is not a word | 3 / 8 of 1,341 | gate correct here (F43) |
| F39 | SkyRL | detectable_format:square_brackets | `{}` `"[The] [sun] [is] [bright]."` → fail; pass | punctuation outside a bracketed word | 12 / 44 of 1,079 | gate F13 |
| F40 | SkyRL | detectable_format:bigram_wrapping | `{}` `"<<I am>> <<at home>> today"` → pass; fail | every word wrapped | 184 FP of 1,157 | judged in task curation |
| F41 | SkyRL | response_language, english_capital, english_lowercase | `{"language": "fr"}` `"12345"` → pass; fail | an answer without language is not in French | response_language 2 FP; all 780 rows on an empty answer | judged / gate F12 |
| F42 | gate | number_words, first/last word, start_end, keyword position, palindrome, capital_word_frequency | number_words `{"relation": "at least", "num_words": 3}` `"Мы пошли домой сегодня."` → fail; pass. first_word_answer `{"first_word": "rain"}` `"- Rain falls softly today.\n- Clouds gather."` → fail; pass | words in any script; `-` and tag names are not words | number_words 56 FF; palindrome 137 FF; last_word_answer 14 FP | reference correct (Unicode `\w`, nltk) |
| F43 | gate | number_sentences, first/last_word_sent, keyword position | `{"relation": "at least", "num_sentences": 2}` `"We met Dr. Smith today."` → pass; fail | an abbreviation or `1.` label does not end a sentence | number_sentences 19 / 71 (with F48) | reference correct (punkt) |
| F44 | gate | keywords:start_end | `{}` `"Hello there my friend hello."` → pass; fail | "not even punctuation" | 55 FP of 989 | reference correct |
| F45 | SkyRL | last_word:last_word_answer | `{"last_word": "language"}` `"We speak one language —"` → fail; pass | a trailing dash is not the last word | 63 FF of 1,285 | gate correct |
| F46 | SkyRL | count:lowercase_counting | `{"N": 2}` `"мы мы мы идём"` → pass; fail | lowercase words in any script; tags are not words | 41 FP of 1,712 | gate F10 |
| F47 | SkyRL | english_capital, response_language, english_lowercase | english_capital `{}` `"SCHOOL OF REALISM"` → fail; pass. response_language `{"language": "fr"}` French sentence + `"\nWe play with our friends all day long in the park."` (full text in repro.py) → pass; fail | the text's language, judged per text | english_capital 70 FF (84 of 192 by direct count) | judged / gate F12 |
| F48 | both | number_sentences (and sentence-based checks) | `{"relation": "at least", "num_sentences": 3}` `"今天下雨了。我们待在家里。我们看书。"` → fail, fail; pass | `。` ends a sentence | shared with F43 | in reference |
| G1 | both | graded text | `keywords:word_once` `{"keyword": "river"}`, raw thinking response without `</think>`: `"The user wants the word river once, so I will plan a short answer about a"` → pass, pass; extraction failure (fail) | unclosed reasoning is not an answer | 139 of 1,500 thinking responses; 84 SkyRL / 113 gate verdicts | both pipelines |
| G2 | SkyRL | session | `last_word:last_word_answer` `{"last_word": "limit"}` on `""` → `IndexError`, row becomes INFRA_ERROR "Verifier configuration failed", reward 0 | a model's empty answer is a graded failure, not an infrastructure error | 1 panel response; 625 rows on an empty answer | gate: plain fail |
| G3 | SkyRL | nth_paragraph_first_word | `{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "rain"}` `"Rain fell.\n\nRain stopped."` over 40 seeds → 24 pass, 16 fail; contract fail (no answer can pass) | deterministic verdicts; unsatisfiable rows never rewarded | 77 rows, 161 panel responses, reward 1.0 on 9 | gate: always fail |
| G4 | SkyRL | dependencies | `instruction_following.py` line 33 downloads `punkt_tab` when missing (repro.py prints it) | NLTK data pinned by hash | — | — |
| G5 | SkyRL | session (unverified) | all rows `route = skyrl_gym`; `nemotron_tasks.py` line 106 raises unless `task_session` (repro.py prints both) | rows must reach the reward | unknown | — |

## Files

- `audit/ISSUE.md`: the issue record (pins, contract hash and time, decision changes, findings, frozen hashes, progress).
- `audit/CONTRACTS.md`: contracts (hash-pinned) and the first 39 decision entries.
- `audit/lib/`: `harness.py` (both graders as their pipelines run them), `contract_grader.py` (replacement v3; frozen copies v1–v3 in `audit/frozen/`), `fixtures_src.py`, `metamorphic_specs.py`, `findings.py`, `relevance.py`, `verdicts.py`.
- `audit/fixtures.jsonl`, `audit/tests/`: fixtures and regression tests.
- `audit/repro.py`: one counterexample per finding.
- `audit/scripts/`: every step's script; `audit/work/`: their outputs (`panel_verdicts.jsonl`, `panel_summary.json`, `fixes_only.json`, `report_stats.json`, `content_free.json`, `fuzz.json`).
