# Audit of the IFBench grader (Marin's vendored Evalchemy copy)

This file stands in for the issue that the audit-grader skill keeps its record in.
Entries are appended in order; times are UTC, read from `date -u` in the same step.

## Progress

- [x] Step 1 (pre-contract part): manifest, lockfile, dataset rows, run records pinned (2026-11-10 05:50 UTC).
- [x] Step 2: contracts (audit/contracts.md), sha256 fcbfcf62... recorded 05:55:05 UTC before any grader code was read.
- [x] Step 1 (post-contract part): recorded 06:03 UTC (section below).
- [x] Step 3: 208 fixtures in audit/tests/fixtures.py; replacement grader audit/lib/replacement.py; pytest audit/tests: 540 passed, 76 xfailed (06:29 UTC).
- [x] Step 4: reference comparison, reference unit tests on R/G/X/XP, metamorphic tests, fuzzing, loose transform, content-free responses (06:27 UTC; records below).
- [x] Step 5: all 228 run files graded (regraded 06:25 UTC after the replacement change); aggregates in audit/panel_tables.md, audit/frozen/panel_summary.json, panel_extra.json.
- [x] Step 6: not run in this exercise (no reviewers); decision rule and sampling plan recorded below.
- [x] Step 7: audit/AUDIT.md written 06:30 UTC.

Next: nothing in this session. A continuation would run step 6 on the held-out files with the recorded decision rule, then update AUDIT.md.
Commands: fixtures `python audit/scripts/run_fixtures.py`; one fixture `python audit/repro.py <id>`; tests `python -m pytest -q -p no:cacheprovider audit/tests`; panel `python audit/scripts/grade_panel.py` (skips graded files). Always with `.venv/Scripts/python.exe -I -X utf8` from W.

## Step 1. Pinned inputs (from run records, configuration and lockfiles only)

Recorded 2026-11-10 05:50 UTC.

| Input | Value | Source |
|---|---|---|
| Case manifest | `case/MANIFEST.sha256`, 424 entries; every file matches, no unlisted file (`python audit/scripts/verify_manifest.py` prints `OK`) | manifest |
| Grader under audit | `case/grader/IFBench/` (Marin's vendored copy of Evalchemy's IFBench task); file hashes: `instructions.py` fe169405..., `instructions_registry.py` 58a47974..., `instructions_util.py` b7d60e07..., `eval_instruct.py` d4228b13..., `grader.py` 3e49aff4..., `__init__.py` e3b0c442 (empty) | manifest |
| Grader commit | **unverified**: the case has no git metadata, so neither the Marin commit that vendored the copy nor the Evalchemy commit it came from is known. Location: the Marin repository path of the vendored copy; command that would verify: `git log -1 --format=%H -- <vendored path>` in Marin and `git diff <evalchemy-commit> -- eval/chat_benchmarks/IFBench` against Evalchemy | TASK.md |
| Reference implementation | github.com/allenai/IFBench at 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d, `case/reference/IFBench/` (hashes in the manifest; checker code in `ifbench/`) | TASK.md, manifest |
| Dataset | allenai/IFBench_test at revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2, `data/train-00000-of-00001.parquet` sha256 80037e4d...; 300 rows, 344 instruction instances (256 rows with one instruction, 44 with two), 58 instruction ids | TASK.md, parquet |
| Dataset rows | one sha256 per row (canonical JSON, sorted keys) in `audit/frozen/dataset_rows.tsv` (sha256 e0f78ed49530c74de8b02374307bfa3895b323a363c5a744296b784f3982dcb2); rows as JSON in `audit/frozen/dataset_rows.jsonl` (sha256 a5e39b588692b18757f1edf9d2779aea6e199eba84fcb1ad3aac8689b729fc57) | `audit/scripts/dataset_pin.py` |
| Prompt rendering | one user message whose content is the dataset `prompt`, no system message, the model's own chat template at the recorded revision (vLLM `LLM.chat` defaults); Qwen3: `enable_thinking=False` or `True`; other models: no template arguments | panel/CONFIGS.md |
| Response extraction (as stored) | `response` = text after the last `</think>` in the completion, leading whitespace removed, or the whole completion when it has no `</think>`. Checked on all 68,400 records: `response` equals this rule applied to `raw_response` in every record | CONFIGS.md, `audit/scripts/panel_records.py` |
| Generation | vLLM offline `LLM.chat`, engine seed 10060, max new tokens 1,024 (thinking configurations 8,192), context = max new tokens + 1,024; greedy runs temperature 0; sample runs temperature 0.7, per-request seed 10060+i; no top-p/top-k/penalties; `bi_` runs with `VLLM_BATCH_INVARIANT=1` | CONFIGS.md |
| Stop sequences | none recorded beyond vLLM defaults (model EOS); `finish_reason` is stored per record | CONFIGS.md |
| Reasoning parser / merge policy | none: offline `LLM.chat`, reasoning stays in the completion and the stored `response` is cut at the last `</think>` | CONFIGS.md |
| vLLM version | 0.30.0 for 14 configurations; **not recorded** for `Qwen__Qwen3-8B__thinking` and `Qwen__Qwen3-14B__thinking` | CONFIGS.md |
| Model revisions | the `revision` field matches CONFIGS.md in every record (one revision per configuration) | records |
| Panel files | 16 configurations, 228 run files, 68,400 records; sha256 per run file in `audit/frozen/panel_files.sha256` (sha256 232d43a139fdc6f1519ff960b97b1d4d5acf6821433558a1eb4c935a3f23f682); every file has 300 lines; `prompt` and `key` equal the dataset row in every record | records |
| Python | CPython 3.12.10 at `.venv/Scripts/python.exe` | interpreter |
| Packages | `pip freeze` equals `case/deps/requirements.lock.txt` line for line (after CRLF normalization); notable: nltk 3.10.0, langdetect 1.0.9, emoji 2.15.0, syllapy 0.8.0, spacy absent | lockfile |
| NLTK data | `case/deps/nltk_data/` (corpora/stopwords, taggers/averaged_perceptron_tagger_eng, tokenizers/punkt, tokenizers/punkt_tab), hashes in the manifest; which of these the grader loads is recorded after step 2 | manifest |
| Reference copies of the test set | `reference/IFBench/data/IFBench_test.jsonl` (d2ada7da...) and `reference/IFBench/ifbench/data/IFBench_test.jsonl` (a2bf7b8e...) differ from each other; compared with the parquet in step 4 | manifest |

What the stored records already show (step 5, first paragraph; `audit/scripts/panel_records.py`):

- Truncated responses (`finish_reason == "length"`): 4,165 of 68,400 (6.1%); per configuration from 78/3,900 (OLMo-2 32B) to 695/5,100 (Qwen3-8B, thinking off).
- Thinking configurations: all 1,800 completions open `<think>`; 136 never close it (Qwen3-8B 104/900, Qwen3-14B 32/900), all with `finish_reason == "length"`. For these the stored `response` is the whole completion, reasoning included.
- Empty graded text: 37 records (Qwen3-14B off 28, Qwen3-8B off 5, marin-8b 4).
- One Qwen3-32B (thinking off) completion contains a literal `</think>`; its `response` is cut there.

## Step 2. Contracts

- 2026-11-10 05:55:05 UTC: `audit/contracts.md` written from the prompt texts and the README only; sha256 `fcbfcf6299f785d7bb99e55691186f3de8d5973917d23f29a7e0e28b9cfe554e`. No grader or reference code had been read at this time. 58 check contracts, general rules G1-G11, 62 decision entries.
- Later contract changes are listed below with their reason; `audit/contracts.md` itself keeps the hashed text, and changes go in `audit/contracts_changes.md`.

## Step 5. Held-out responses (declared 2026-11-10 06:18 UTC, before any panel aggregate was read)

Held out from any change to the replacement grader: `sample7.jsonl` of each of the 14 configurations that have sampled runs, and `greedy_repeat.jsonl` of the two thinking configurations (16 files, 4,800 responses). The replacement grader as of 06:18 UTC (fixture-driven only) graded them; any later change to `audit/lib/replacement.py` must be validated on these files only after it is made, and examples quoted in the report come from other files.

## Step 1 (continued). Inputs that only the code shows

Recorded 2026-11-10 06:03 UTC, after the contract hash.

| Input | Value | Source |
|---|---|---|
| Harness entry | `eval_instruct.py` `IFBenchBenchmark`: `PRIMARY_METRIC = "strict_prompt_accuracy"`; metrics strict/loose x prompt/instruction; `generation_kwargs={"do_sample": False, "temperature": 0, "max_gen_toks": 1024}` (default `max_tokens=1024`); no system instruction by default | eval_instruct.py |
| Dataset revision in the harness | **unpinned**: `load_dataset("allenai/IFBench_test", split="train")` has no `revision=`; `SourceRef("allenai/IFBench_test", "train")` has none either (finding F-pin-dataset) | eval_instruct.py:26,61 |
| Graded-text extraction | **unverified**: `iter_specs` hands rows to Evalchemy's `text_specs(..., grader="instructions", reference={"protocol": "ifbench"})`; the modules that generate, extract the graded text and call `grader.py` (`eval.sources.common`, `eval.contracts.eval_spec`, `eval.task`) are not in the case. Location: Marin's Evalchemy fork, `eval/sources/common.py` and the `instructions` grader registration; command that would verify: `grep -rn "protocol.*ifbench\|test_instruction_following" eval/` in that checkout. The panel's stored `response` (CONFIGS.md rule) is used as the graded text in this audit. | eval_instruct.py:1-2,93 |
| Per-prompt grading | `grader.py`: strict = `response and response.strip() and check_following(response)`; loose = same over 8 variants (as is, `*` removed, first line removed, last line removed, both, and the `*`-removed versions of the three); responses looked up by exact prompt text (no duplicate prompts in the 300 rows) | grader.py |
| NLTK resources the grader loads | `punkt_tab` (via `nltk.sent_tokenize` / `word_tokenize`), `stopwords` (english), `averaged_perceptron_tagger_eng` (`nltk.pos_tag`); `instructions_util.download_nltk_resources()` runs at import and calls `nltk.download(...)` for any of punkt, punkt_tab, stopwords, averaged_perceptron_tagger_eng that it cannot find, with no version pin (finding F-pin-nltk). `instructions.py` also creates `<package>/.nltk_data` and puts it first on `nltk.data.path`; `NLTK_DATA` wins only when set before import | instructions.py:25-32, instructions_util.py:1551-1571 |
| Other libraries that change verdicts | emoji 2.15.0 (`emoji.is_emoji`), syllapy 0.8.0 (`syllapy.count`), nltk 3.10.0 tokenizers and tagger, Python `csv`, `unicodedata` (Python 3.12.10) | instructions.py imports, lockfile |
| Grader vs reference code | the grader is an older state of the reference's checker code: `diff` shows six checker differences (ratio:overlap tokenization, ratio:sentence_words different-words test, custom:sentence_alphabet first-letter rule, count:keywords_multiple counting, words:words_position tokenization, repeat:repeat_span index unit) and the reference's added classic IFEval registry entries; `instructions_util.py` differs only by the reference's added language table and `count_sentences` | `diff` of the two trees |
| Reference test-set copies | `reference/IFBench/ifbench/data/IFBench_test.jsonl` equals the parquet in every prompt, id list and non-null kwarg; `reference/IFBench/data/IFBench_test.jsonl` differs in 2 prompts by whitespace only (keys 13 and 19). Numeric kwargs (`N`, `small_n`, `min_words`, `max_words`, `percentage`) are floats in all three copies; the checkers accept floats (`audit/scripts/compare_datasets.py`) | data files |
| Work copies | the audit imports byte-identical copies in `audit/work/` (importing creates `.nltk_data` and would write `__pycache__` next to the modules); `python audit/scripts/make_work_copy.py` verifies them against the manifest before and after each run | audit/scripts/make_work_copy.py |

## Step 3. Fixtures and replacement grader (06:29 UTC)

- `audit/tests/fixtures.py` (sha256 ca6f2dce9d8ebee1cda2c13e6b5d4d804395f733fe8021b4e139bfc418c724a1): 208 fixtures, every check has pass and fail fixtures; ids = check + 8 hex of sha256(check, kwargs, row, text). Verdict table `audit/frozen/fixture_verdicts.json`.
- Tests: `audit/tests/test_fixtures.py` (grader vs label, xfail(strict=True) for the fixtures the grader gets wrong; replacement under PROPOSED and AS_IS), `audit/tests/test_stress.py` (loose, metamorphic, content-free). Result: 540 passed, 76 xfailed.
- Replacement grader `audit/lib/replacement.py` (sha256 62bc0eae... at 06:32 UTC): fixes every checker finding; 16 working decision switches; AS_IS = grader's readings, PROPOSED = contract readings. Changed after the first panel pass (06:18-06:25) on non-held-out evidence: list markers, curly apostrophes, Congo aliases, plural-noun starts, D-section and D-template-repeat switches; each change has a fixture. Later: csv checks return fail instead of raising.

## Step 4. Reference comparison and stress tests (06:27 UTC)

- Fixtures: G and R differ on 9, all from the six code differences; R matches the label on each.
- Panel: G and R differ on 257 verdicts (ratio:overlap 227, custom:sentence_alphabet 23, words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1).
- Reference unit tests (`audit/scripts/run_reference_tests.py`): R all pass; G fails 5 (the tests added with the reference's fixes); X fails 3 assertions that the contract contradicts (TEST_EUROPE without Kyiv; TEST_NEWLINE_COUNTRIES without Ethiopia and The Gambia; empty string expected to pass = D-empty); XP adds 5 assertions that encode non-proposed decision readings (TEST_OPTIONS, TEST_PALINDROME2, TEST_PUNCTUATION2, TEST_QUOTE_EXPLANATION, TEST_THREE_VOWEL_FALSE).
- Fuzz: 412,800 calls (400 random texts per instance, seed 10060), 0 exceptions in G, R, X. Hand-written input raises IndexError in csv_quotes (F-csv-quotes-exception); grader.py does not catch it.
- Metamorphic flips under G: CRLF 1, curly apostrophes 4, trailing newline 6.
- Content-free under G strict: empty/whitespace fail all; "the" x200 passes sub-bullets 12/12, sentence_balance 7/7, sentence_type 6/6 (findings) and vacuous checks; the restated prompt passes output_template 4/4 and person_names 6/6.
- Loose: 3,666 loose rescues on the panel (1,798 by `*` removal, 1,814 by first/last line removal, 54 both); content-removal counterexamples in test_stress.py.

## Step 5 summary (06:25 UTC)

- Coverage 78,432/78,432 verdicts for every grader, 0 exceptions.
- Pooled strict prompt-level accuracy: G 24.92, R 25.00, X 25.97, XP 25.36, G loose 28.95, R loose 29.02.
- G vs X: 2,805 verdicts differ (2,760 checker fixes, 45 extraction failures); per configuration X-G from -1.14 to +5.00 points; identical-settings rerun (greedy_repeat - greedy) from -1.33 to +1.00; held-out X-G +1.19 vs +1.04 elsewhere.
- Extraction failures: 136 responses, 157 verdicts, G passes 45 verdicts and 35 whole prompts.

## Findings (43)

Pipeline and pinning: F-extract-unclosed, F-pin-dataset, F-pin-nltk, F-csv-quotes-exception.
Checkers: F-conj-variants, F-keywords-substring (fixed in R), F-numbers-joined, F-word-count-split, F-japanese-skip, F-charrev-partial, F-capitals-key, F-mcq-label, F-africa-incomplete, F-alphabet-quote (fixed in R), F-emoji-sequence, F-indent-tabs, F-indent-blank-lines, F-list-anywhere, F-nbb-blank-lines, F-nbb-period, F-template-check, F-quote-unquote-curly, F-quotes-curly, F-subbullets-check, F-thesis-each, F-titlecase-minor, F-titlecase-contraction, F-overlap-char (fixed in R), F-balance-zero, F-ratio-zero, F-sentence-words-unique (fixed in R), F-repeat-change-same, F-span-char (fixed in R), F-alliteration-sum, F-word-tokenize-contractions, F-attached-punct, F-startverb-tagger, F-startverb-markup, F-words-position-punct (fixed in R), F-date-invalid, F-loose-content, F-crlf, F-curly-apostrophe.
Details, fixtures, shares and commands: audit/AUDIT.md.

## Decision entries

Measured by a replacement switch: D-options-exact, D-explanation, D-palindrome-distinct, D-csv-wrapper, D-section, D-nbb-order, D-punct-set, D-sentence, D-template-repeat, D-list-sep, D-this-sentence, D-trim, D-verb, D-vowel-paragraph, D-japanese-digits, D-word. Not measured: D-keyword-form, D-empty, D-vacuous, D-preamble, D-markdown, D-loose and the remaining entries of audit/contracts.md. Table with readings and effects: audit/AUDIT.md.

## Step 6. Decision rule recorded before any review (06:32 UTC; no review was run)

Recommend replacing the grader with the replacement if the replacement passes every fixture, scored coverage is complete, and its error rate is lower than the current grader's with a 95% paired bootstrap interval (resampling within strata) that excludes zero. Sample from the held-out files only (5,504 verdicts; G and X disagree on 194): all disagreements plus at least 130 consensus cases from the agreement stratum (5,310 verdicts); seed and case-list sha256 to be written here before the review. Extraction failures are counted under their own label.

## Frozen files (06:32 UTC)

`audit/frozen/FROZEN.sha256` lists the sha256 of every file under audit/frozen/ (239 files, including the 228 panel verdict files); its own sha256 is recorded in the final entry below. Key files: dataset_rows.jsonl a5e39b58..., dataset_rows.tsv e0f78ed4..., panel_files.sha256 232d43a1..., fixture_verdicts.json 7cdc916d..., panel_summary.json 0a818c59..., panel_extra.json e41338ea..., stress.json 6d8e5e9a....

## Final check (2026-11-10 06:37 UTC)

- Reference whole pipeline (`run_eval.py`) on the 16 greedy runs: per-prompt strict and loose verdicts equal the per-check R/RL verdicts in all 4,800 prompts (`audit/scripts/run_reference_pipeline.py`).
- `pytest audit/tests`: 540 passed, 76 xfailed. `audit/scripts/verify_report.py`: every fixture id in AUDIT.md exists, all 45 G/R/label triples match, all 19 decision fixtures disagree with the grader as stated, and the 3 example commands print what the report says: OK.
- `audit/scripts/verify_manifest.py`: case/ unchanged (424 files, no unlisted file). Work copies match the manifest.
- `audit/frozen/FROZEN.sha256` sha256 b6d96f49f2102a8984ff3f37d66ec03ca132743acd6199a3375c29935801187e (239 files). `audit/AUDIT.md` sha256 8629d7ba...; `audit/lib/replacement.py` 62bc0eae...; `audit/tests/fixtures.py` ca6f2dce....
- Not done: step 6 (no reviewers). Open: the grader commit and the pipeline's graded-text extraction are unverified (no Evalchemy/Marin checkout in the case).
