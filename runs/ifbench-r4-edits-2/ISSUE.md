# Audit: IFBench grader (Marin's vendored Evalchemy copy)

This file stands in for the task's issue (offline exercise: no tracker). Entries are appended in time order; times are UTC and were read from `date -u` in the same step.

## Progress

- [x] Step 1: pinned inputs (records part 22:07 UTC; code part 22:24 UTC).
- [x] Step 2: contracts v1 hashed 22:09 UTC before reading code; v2 22:24 UTC (changes logged in CONTRACTS.md section 9).
- [x] Step 3: 332 fixtures in `audit/tests/fixtures.py`, runnable with pytest (`audit/tests/test_fixtures.py`); 74 strict xfails mark the grader's current failures (47 findings, 27 decisions); replacement grader `audit/scripts/replacement.py` passes all 332.
- [x] Step 4: reference comparison (fixtures + panel), reference unit tests vs replacement, metamorphic edits, fuzzing (17,400 inputs), loose grading, content-free responses.
- [x] Step 5: all 68,400 stored responses (78,432 instruction verdicts) graded by grader strict/loose, reference strict/loose, replacement (+ decision switches, + grader readings). Held-out set: run sample7 of each configuration with sampled runs, greedy_repeat of the two thinking configurations.
- [ ] Step 6: NOT RUN in this exercise (no reviewers). No sample drawn or frozen.
- [x] Step 7: `audit/AUDIT.md` written 22:50-22:54 UTC; all 43 quoted commands verified.

Next (if continuing): step 6 when reviewers exist (see AUDIT.md "What step 6 still has to settle"); otherwise polish AUDIT.md. Rerun checks: `pytest audit/tests`, `audit/scripts/repro.py`.

## 2026-11-10 22:07 UTC: pinned inputs (from records, configuration and lockfiles only)

Working directory `W = <W>`. `sha256sum -c case/MANIFEST.sha256` passed for every file at 22:02 UTC.

| Input | Value | Source |
|---|---|---|
| Grader under audit | `case/grader/IFBench/` (Marin's vendored copy of Evalchemy IFBench); no commit recorded, pinned by file hash in `case/MANIFEST.sha256` | TASK.md, MANIFEST |
| Grader file hashes | `instructions.py` fe169405...76302, `instructions_registry.py` 58a47974...3aed, `instructions_util.py` b7d60e07...20b8, `eval_instruct.py` d4228b13...41e0, `grader.py` 3e49aff4...285c, `__init__.py` e3b0c442...b855 (empty) | MANIFEST |
| Reference implementation | `case/reference/IFBench/`, github.com/allenai/IFBench at 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d; checker code in `ifbench/` | TASK.md |
| Dataset | allenai/IFBench_test at revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2, `case/data/train-00000-of-00001.parquet` sha256 80037e4d99c39a55c1e2e7d5a863d8d9edeb5ebe136ba8c1e849f8c015027c6a; 300 rows, 58 instruction ids, 256 rows with 1 instruction, 44 with 2 | TASK.md, parquet |
| Per-row hashes | `audit/frozen/dataset_row_hashes.tsv` (sha256 of canonical JSON per row), file sha256 f170f0bdfd7463b9cb53ec88729e08c74a281098e08687c91aae57fa5e577ff5 | this audit |
| Prompt rendering | one user message = dataset `prompt`, no system message, model's own chat template at the listed revision (vLLM `LLM.chat` defaults); Qwen3 `enable_thinking=False/True` | panel/CONFIGS.md |
| Response extraction (records) | `response` = text after the last `</think>` with leading whitespace removed, or the whole completion when it has no `</think>` | panel/CONFIGS.md |
| Output budget | 1,024 new tokens (thinking off), 8,192 (two thinking configs); context = max new tokens + 1,024 | panel/CONFIGS.md |
| Stop sequences | none recorded (vLLM defaults: model EOS) | panel/CONFIGS.md (absent) |
| Reasoning parser / merge policy | no server reasoning parser recorded; the split is done offline on `</think>` as above; no `reasoning_content` field in the records | panel/CONFIGS.md |
| Decoding | greedy (temperature 0) and sample<i> (temperature 0.7, seed 10060+i); engine seed 10060; no top-p/top-k/penalties | panel/CONFIGS.md |
| vLLM | 0.30.0 for 14 configs; NOT RECORDED for `Qwen__Qwen3-8B__thinking` and `Qwen__Qwen3-14B__thinking` | panel/CONFIGS.md |
| Model revisions | per config in panel/CONFIGS.md and each line's `revision` field | panel/CONFIGS.md |
| Python | 3.12.10 at `W/.venv/Scripts/python.exe` | `python --version` |
| Packages | `case/deps/requirements.lock.txt` sha256 5ae01214...161bde; installed set matches the lock exactly (60 packages) plus `pip 26.3`; relevant: nltk 3.10.0, langdetect 1.0.9, emoji 2.15.0, syllapy 0.8.0, immutabledict 4.3.1, absl-py 2.5.1 | importlib.metadata vs lock |
| NLTK data | `case/deps/nltk_data/`: corpora/stopwords, taggers/averaged_perceptron_tagger_eng, tokenizers/punkt (+PY3), tokenizers/punkt_tab; 155 files, all in MANIFEST | directory listing |

Unverified (cannot fetch offline):

- That `case/grader/IFBench/` equals the copy Marin runs: no Marin/Evalchemy commit is given. Verify with `git -C <marin> log -1 -- <vendored IFBench path>` and `sha256sum` of the five files against the MANIFEST values above.
- That `case/reference/IFBench/` equals allenai/IFBench@1c40f0c: verify with `git clone https://github.com/allenai/IFBench && git -C IFBench checkout 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d && sha256sum` of each file.
- That the parquet equals allenai/IFBench_test@2e8a48d: verify with `huggingface-cli download allenai/IFBench_test --repo-type dataset --revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2` and `sha256sum`.
- vLLM version of the two thinking configurations (record field absent).
- NLTK data package versions (no index file in `deps/nltk_data`); pinned by file hash only.

## 2026-11-10 22:09 UTC: contract hash (before reading any grader or reference code)

`audit/CONTRACTS.md` v1 sha256 `3d0aaccbaa03d1e46ce9aa9d4f9d933a25a8af013888413ee280d4fceb6b04fc`, frozen copy `audit/frozen/CONTRACTS_v1.md` (same hash). Written from the dataset prompts and kwargs only (`audit/scripts/dump_instruction_texts.py` output). No file under `case/grader/` or `case/reference/` had been opened. 58 checks, 10 global rules, 60 decision entries proposed. Later contract changes are logged below with their reason.

## 2026-11-10 22:14 UTC: fixtures labeled before reading code

`audit/tests/fixtures.py` v1: 293 fixtures over all 58 checks (3 to 14 per check, each check has pass and fail labels), labeled from CONTRACTS v1 only. sha256 `03a70e34e6b2a29ef075d1c09881fd5ea67b050cb641547954dbc1150bc11a8e`; frozen copy `audit/frozen/fixtures_v1_prelabel.py`. Each fixture names the decision entries its label depends on. Grader code is read only after this entry.

## 2026-11-10 22:24 UTC: step 1 (code part), contract v2, first fixture run

Inputs that only the code shows (recorded after the contract hash, as step 1 requires):

- `eval_instruct.py` loads `load_dataset("allenai/IFBench_test", split="train")` with no `revision`: the dataset is unpinned in the run (finding F-H1).
- `instructions.py` lines 26-32 create `<package>/.nltk_data` on import and put it first on `nltk.data.path`; `instructions_util.py` lines 1551-1571 call `nltk.download` at import for punkt, punkt_tab, stopwords and averaged_perceptron_tagger_eng when missing. NLTK data versions are therefore not pinned by the grader (finding F-H2). The audit runs byte-identical copies under `audit/run/` (hashes checked against the MANIFEST by `audit/scripts/setup_run_copies.py`) with `nltk.download` blocked, so `case/` is never modified and nothing reaches the network.
- Response extraction is not in the vendored files: `eval_instruct.py` hands grading to Evalchemy's `grader="instructions"` with `reference={"protocol": "ifbench"}`, which is not included. The extraction rule applied by the run is unverified; the audit uses the panel records' rule (CONFIGS.md). Verify with the Evalchemy source of the `instructions` grader at the Marin commit.
- Harness: `grader.py` grades strict (`response.strip()` and `check_following`) and loose (8 variants: first/last line removed, `*` removed); no exception handling, so one checker exception stops the run.
- Dataset copies: the HF parquet and `reference/IFBench/ifbench/data/IFBench_test.jsonl` agree; `reference/IFBench/data/IFBench_test.jsonl` strips trailing spaces from the prompts of keys 13 and 19 (the reference harness looks prompts up with `.strip()` tolerance, so verdicts are unaffected). `datasets` loads `m, n, n_start, n_end` as int and `N, small_n, percentage, min_words, max_words` as float; no checker fails on the float values.
- Grader vs reference code: 7 behavioral differences (`ratio:overlap` character vs word trigrams; `ratio:sentence_words` missing the different-words check; `count:keywords_multiple` substring vs whole-word count; `repeat:repeat_span` character vs word indices; `words:words_position` token handling; `custom:sentence_alphabet` leading punctuation; refactors with equal behavior for `words:repeats`, `words:no_consecutive`). The reference registry adds 25 classic IFEval checkers that IFBench_test does not use.

Contract v2: `audit/CONTRACTS.md` sha256 `71ac928e59788b462068aa2da6e05ed26a9a530a84c25a213fcaccd284d0bafb`, frozen as `audit/frozen/CONTRACTS_v2.md`. Changes and reasons are in its section 9 (D-title-minor narrowed; new D-options-whitespace, D-template-outside, D-vowel-paragraph, D-empty-output, D-punct-separate; D-overlap-def gains character trigrams).

Fixtures: 37 targeted fixtures added after reading the code (from `POST` onward in `fixtures.py`), labeled from the contract; 330 fixtures in all.

## 2026-11-10 22:54 UTC: steps 3-5 results, findings, decisions, frozen files

Correction to the 22:09 entry: contract v1 proposed 59 decision entries, not 60 (v2 added 5, v3 added 1: 65 in all).

Frozen files and hashes (sha256):

| File | sha256 |
|---|---|
| `audit/frozen/CONTRACTS_v1.md` | 3d0aaccbaa03d1e46ce9aa9d4f9d933a25a8af013888413ee280d4fceb6b04fc |
| `audit/frozen/CONTRACTS_v2.md` | 71ac928e59788b462068aa2da6e05ed26a9a530a84c25a213fcaccd284d0bafb |
| `audit/frozen/CONTRACTS_v3.md` (= current `audit/CONTRACTS.md`) | 42dbe1d7ba03afafd47d55117ec5deb26922d1788daec1ebabc1ee024edcb7e2 |
| `audit/frozen/dataset_row_hashes.tsv` | f170f0bdfd7463b9cb53ec88729e08c74a281098e08687c91aae57fa5e577ff5 |
| `audit/frozen/fixtures_v1_prelabel.py` (labels before code was read) | 03a70e34e6b2a29ef075d1c09881fd5ea67b050cb641547954dbc1150bc11a8e |
| `audit/tests/fixtures.py` (332 fixtures, current) | 502da34c8f72b1acbee153676fc503bc32618f7479eacc095536eb3053289a59 |
| `audit/tests/xfail_grader.json` | d1d32134a44f8e7044e1a62f4f5f78e7c3606d2a4f134732f5f8811aacb7844d |
| `audit/scripts/replacement.py` | c973100da0031bc161a4cef497ff33356e4a57246d38d466cf18702b0205899a |

Fixture changes after v1 labeling, each with its reason: one label corrected ("indoors" fixture of count:keywords_multiple, labeled fail by mistake; the contract gives pass because "door" still occurs once as a word); one post-code fixture response replaced (custom:reverse_newline filler lines "Zz.." sort above "Zimbabwe", which made the fixture fail for an unintended reason; now "Y.."); decision tags changed as listed in CONTRACTS.md section 9 plus D-edge-whitespace+D-nbb-after on the trailing-newline fixture of format:no_bullets_bullets; 39 post-code fixtures added in all.

Replacement changes after the panel was graded: (1) `words:odd_even_syllables` counts syllables per letter run, because syllapy recursed on a 4,669-character hyphenated token (Qwen2.5-32B sample6 key 233, not held out); 2 panel verdicts changed and were regraded. (2) Carriage returns are normalized to line breaks (found by fuzzing; no panel response contains one, so no panel verdict changed). Held-out set, fixed before any further change: run `sample7` of the 14 configurations with sampled runs and `greedy_repeat` of the two thinking configurations (5,504 verdicts, 480 grader-vs-replacement disagreements).

Step 5 headline: grader vs replacement disagree on 6,777 of 78,432 verdicts (8.6%); 4,703 (6.0%) remain with the replacement set to the grader's readings of the modelled decisions; grader vs reference 257 (0.33%). Strict prompt-level, pooled: grader 24.92%, reference 25.00%, replacement 24.01%; loose 28.95%. Per-configuration change replacement minus grader: -4.4 to +2.9 points; greedy_repeat minus greedy: at most 1.3 points.

Findings (details, counterexamples and commands in AUDIT.md): F01 repeat_span character indices; F02 sentence_words no different-words check; F03 keywords_multiple substring count; F04 conjunctions raw-token dedupe (188 panel verdicts); F05 sentence_type/sentence_balance pass with zero typed sentences; F06 alliteration sums runs (120); F07 newline whitespace-only lines; F08 line_indent ignores tabs; F09 quote_unquote curly quotes and punctuation (58); F10 list separator anywhere (459); F11 thesis checks only the first span (254); F12 sub-bullets vacuous pass and bold false fail (833); F13 no_bullets_bullets period unchecked and empty-line reset (159); F14 character_reverse substring; F15 reverse_newline ignores lines before Zimbabwe; F16 capitals key omits Kyiv; F17 csv_special early return; F18 csv_quotes IndexError and csv_city _csv.Error; F19 dates with 00; F20 title_case minor words and contractions; F21 output_template placeholders and order (43); F22 repeat_change unchanged first word; F23 options case; F24 parentheses unmatched opens (201); F25 prime_lengths non-ASCII punctuation; F26 last_first/paragraph_last_first attached punctuation (64); F27 emoji sequences (27); F28 start_verb tagger on capitalized imperatives (>=124); F29 sentence_alphabet leading punctuation (23); F30 words_position trailing punctuation (5); F31 no exception handler, one exception stops the run; F32 loose grading passes 2,609 contract-failed verdicts (all 2,736 sub-bullets verdicts pass loose); F33 unclosed reasoning graded as the answer (136 responses, 45 passes); F34 dataset revision unpinned; F35 NLTK data unpinned and downloaded at import; F36 thinking-config vLLM version and grader commit unrecorded, false comparability claim. Reference status: F01, F02, F03, F29, F30 fixed there; the rest present.

Decision entries: 65 (table in AUDIT.md, full text in CONTRACTS.md). Largest panel effects: D-vacuous 602, D-list-inline 480, D-punct-set 434, D-vowel 365, D-palin-distinct 319, D-count-exact 307, D-section 288, D-csv-wrapper 220, D-overlap-def 201/149.

Step 6 (not run). Result that would change the recommendation, recorded before any review: adopt the replacement only if it passes every fixture, has complete scored coverage, and its error rate on a blinded, seeded, stratified sample of the held-out runs is lower than the grader's with a 95% paired bootstrap interval that excludes zero; otherwise fix the grader by moving to the reference and patching F04-F28 and F31-F35.

Report: `audit/AUDIT.md` (sha256 at 22:54 UTC 031406541d0a8745e65b60dff0187876ceaf3d4cb74781f2952e69e21b21730e). `audit/scripts/verify_report.py` checked all 43 commands it quotes (0 failed); pytest: 591 passed, 74 xfailed.
