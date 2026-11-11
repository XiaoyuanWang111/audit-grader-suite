# Audit: IFBench grader in Marin's evaluation policy (Evalchemy vendored copy)

Offline stand-in for the task issue. Entries are appended in time order; times are UTC from `date -u`.

## Progress

- [x] Step 1: pin inputs -- 2026-11-11 00:02 (code-derived pins 00:18)
- [x] Step 2: contracts v1 hashed 00:07, before any grader or reference code was read; v2 00:22, v3 00:32, v4 00:44 (reasons in CONTRACTS.md change log)
- [x] Step 3: 354 fixtures; grader 81 wrong (strict xfail, classified: 55 findings, 26 decisions); replacement grader 354/354
- [x] Step 4: reference unit tests vs replacement (6 assertions contradicted), metamorphic (grader 152 wrong of 1,376), fuzz (0 exceptions in 20,640), content-free, loose
- [x] Step 5: panel graded (68,400 responses, 78,432 verdicts); held-out = greedy_repeat runs; replacement frozen sha256 8de19f99b9ee...
- [ ] Step 6: NOT RUN in this exercise (no reviewers); AUDIT.md section 7 says what the recommendation needs from it
- [x] Step 7: audit/AUDIT.md written 2026-11-11 00:59 UTC (first full version); final checks: rerun tests, verify every report command (audit/scripts/verify_report.py)

Next action for a resumed session: run `audit/scripts/verify_report.py` and the pytest suite; then optional improvements only.

## Step 1: pinned inputs (from run records, configuration and lockfiles only)

Recorded 2026-11-11 00:02 UTC.

- Case folder integrity: `case/MANIFEST.sha256` (sha256 `f03178d6e4769e119d58cb33178764e79512d5205040b4c67e5a112d3616b1b3`) lists 424 files; all 424 match, no unlisted files (`audit/scripts/s1_pin.py`).
- Grader under audit: `case/grader/IFBench/` (Marin's vendored Evalchemy IFBench). No commit hash is given for the vendored copy or for Evalchemy; files are pinned only by the manifest hashes. UNVERIFIED: the Evalchemy/Marin commit that the copy came from (would be verified with `git -C <marin checkout> log -1 -- <vendored path>` and a diff against Evalchemy at that commit). -> finding candidate F-pin (grader commit unpinned).
- Reference implementation: `case/reference/IFBench/` = github.com/allenai/IFBench at commit 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d (stated in case/TASK.md; not verifiable offline: no `.git`; would be verified with `git clone https://github.com/allenai/IFBench && git -C IFBench diff 1c40f0c --stat` against the folder).
- Dataset: `case/data/train-00000-of-00001.parquet` sha256 `80037e4d99c39a55c1e2e7d5a863d8d9edeb5ebe136ba8c1e849f8c015027c6a`, stated as allenai/IFBench_test revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2 (UNVERIFIED offline: `huggingface-cli download allenai/IFBench_test --repo-type dataset --revision 2e8a48de... ` then sha256). 300 rows, columns key, prompt, instruction_id_list, kwargs; 256 rows with one instruction, 44 with two; 58 instruction ids, 344 instruction instances.
  - One hash per row: `audit/frozen/dataset_row_hashes.tsv`; row hash = sha256 of canonical JSON of {key, prompt, instruction_id_list, kwargs without null fields}. CORRECTED 2026-11-11 00:17 UTC: the first version (sha256 `2ea6504c...`) read the parquet through pandas, which turned the int64 kwargs `m`, `n`, `n_start`, `n_end` into floats because of nulls. Recomputed from pyarrow (`to_pylist`, the types `datasets` returns): sha256 `541e49209ca68f7697ba7835a5e54bc572534d8a35956d947221f1cc4384b6d5`.
  - Parquet kwarg types (schema): `m`, `n`, `n_start`, `n_end` int64; `N`, `small_n`, `percentage`, `min_words`, `max_words` double (so `N` arrives as `13.0`); strings otherwise. With these types the reference repository's own copy `reference/IFBench/data/IFBench_test.jsonl` matches the parquet in every row's ids and kwargs; two prompts differ by trailing whitespace only (rows 13 and 19). The 00:02 entry that said the parquet stores every numeric kwarg as a float was a pandas artifact and is withdrawn.
- Prompt rendering (from panel/CONFIGS.md): one user message = dataset `prompt`, no system message, model's own chat template at the listed revision (vLLM `LLM.chat` defaults); Qwen3 with `enable_thinking=False/True`.
- Response extraction recorded by the panel: `response` = text after the last `</think>` in `raw_response`, leading whitespace stripped, or the whole completion when there is no `</think>`. Verified on all 68,400 lines (0 mismatches). Whether Marin's harness applies the same rule is a code question, recorded after the contract hash.
- Generation settings that change graded text (panel/CONFIGS.md): max new tokens 1,024 (thinking off) and 8,192 (thinking on); context = max new tokens + 1,024; vLLM 0.30.0 except the two thinking configurations (not recorded -> unpinned); no stop sequences recorded beyond defaults (UNVERIFIED: vLLM default stop = model EOS); reasoning parser: none (raw completion stored; extraction done by the rule above); no reasoning field merged.
- Panel: 16 configurations, 228 run files, 68,400 responses (`audit/frozen/panel_summary.json`, sha256 `aa613580450e311c846b4dd231191191b2da174269d7f0e4d83f7e1e14bd2103`). Every line's key and prompt match the dataset row order.
  - finish_reason `length` (truncated): 4,165 of 68,400.
  - empty `response`: 37 (Qwen3-14B 28, Qwen3-8B 5, marin-8b-instruct 4).
  - thinking configurations: 136 responses whose reasoning never closes (`<think>` without `</think>`): Qwen3-8B thinking 104 of 900, Qwen3-14B thinking 32 of 900. Their `response` field is the whole completion including the open reasoning.
  - Qwen3-32B (thinking off): 1 response contains a `</think>` in its completion.
- Dependencies (lockfile `case/deps/requirements.lock.txt`, sha256 `5ae01214d54ea3e79ba3afd4ec75f8311bf7e84a3392b8cc27c28faca6161bde`): Python 3.12.10 (uv venv), nltk 3.10.0, langdetect 1.0.9, emoji 2.15.0, syllapy 0.8.0, immutabledict 4.3.1, absl-py 2.5.1, regex 2026.11.9, datasets 5.1.0, pytest 9.2.0, hypothesis 6.170.15, and the rest of the file. NLTK data: `case/deps/nltk_data/` (stopwords, punkt, punkt_tab, averaged_perceptron_tagger_eng), hashed in the manifest. The lockfile is the audit environment, not a record of the environment Marin's evaluation runs in (UNVERIFIED: Marin's/Evalchemy's lockfile at the evaluation commit).
- Interpreter: `.venv/Scripts/python.exe` sha256 `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`.
- langdetect is nondeterministic unless `DetectorFactory.seed` is set; whether any checker uses it is a code question (after the contract hash).

## Step 2: contract hash

- 2026-11-11 00:07:43 UTC: `audit/CONTRACTS.md` v1, sha256 `5419289271db5dae4ce579d442436407aca712dd9fac363c72ed092cfcd71127` (370 lines). Frozen copy `audit/frozen/CONTRACTS_v1_2026-11-11T0007Z.md` (same hash). Written from the dataset prompt text only; no file under `case/grader/` or `case/reference/` had been opened (only directory listings, and the reference's `data/IFBench_test.jsonl` for the dataset comparison in step 1).
- Later contract changes are logged at the end of CONTRACTS.md with reasons, and each new hash is appended here.

## Step 1 (continued): inputs that only the code shows (recorded after the contract hash)

Recorded 2026-11-11 00:18 UTC, after reading `case/grader/IFBench/*.py` and the reference's `evaluation_lib.py`, `run_eval.py`.

- Marin harness `eval_instruct.py`: loads `load_dataset("allenai/IFBench_test", split="train")` with NO revision -> the dataset revision is unpinned in the evaluation (finding F-01). Generation kwargs `do_sample=False, temperature=0, max_gen_toks=1024`. Primary metric `strict_prompt_accuracy`; also reports strict instruction accuracy and both loose metrics. Grader name "instructions", protocol "ifbench".
- The module that turns a completion into the graded text and calls `grader.py` (`eval.sources.common.text_specs`, `eval.contracts.eval_spec`, the "instructions" grader) is not in the case folder. UNVERIFIED: the extraction rule for reasoning models (whether text after the last `</think>` is graded, and what happens when `</think>` is missing), and whether an exception raised by a checker is caught per item or stops the run. Would be verified by reading those modules at the evaluation commit (`grep -rn "def text_specs\|protocol.*ifbench" <marin checkout>`).
- `grader.py`: strict = `response.strip()` non-empty and `check_following(response)`; loose = any of 8 variants (first line removed, last line removed, both, `*` removed) passes. None-valued kwargs are dropped. No try/except around `check_following`.
- Grader dependencies used by the code: nltk (`sent_tokenize` with punkt/punkt_tab, `word_tokenize`, `pos_tag` with averaged_perceptron_tagger_eng, English stopwords), emoji (`is_emoji`), syllapy (`count`), unicodedata, csv, re. langdetect is not used by the 58 IFBench checkers (only by the reference's classic IFEval checkers).
- NLTK data: `instructions.py` creates `<package>/.nltk_data` at import and sets `NLTK_DATA` only if unset; `instructions_util.download_nltk_resources()` downloads punkt, punkt_tab, stopwords and the tagger from the network at import when they are missing. The grader therefore does not pin its NLTK data; a fresh environment gets whatever the NLTK index serves (finding F-02). In this audit `NLTK_DATA` points at the hashed `case/deps/nltk_data`, so nothing is downloaded.
- To avoid writing into `case/` (the `.nltk_data` mkdir and `__pycache__`), the audit imports verbatim copies of the grader and the reference made by `audit/scripts/s3_copy_pkgs.py`, which checks each copy against `case/MANIFEST.sha256`, and runs Python with `PYTHONDONTWRITEBYTECODE=1`.
- Through `datasets`/pyarrow the kwargs keep their parquet types, so the int64 index kwargs reach the checkers as ints; no float-index crash on the dataset as loaded.
- (Step 2 record) 2026-11-11 00:22 UTC: `audit/CONTRACTS.md` v2 (change log entry v2: D-typographic narrowed to quotation delimiters; new D-japanese-digits and D-change-case; emoji forms clarified). Frozen copy `audit/frozen/CONTRACTS_v2_2026-11-11T0021Z.md`; sha256 in the line below.
  - v2 sha256: cd222e61d4264d089839c10afd4f6829f112f6edd0ca45eb33147ddec0f6fcb2
- (Step 2 record) 2026-11-11 00:32 UTC: CONTRACTS.md v3 (new D-paren-closed), frozen copy audit/frozen/CONTRACTS_v3_2026-11-11T0032Z.md, sha256 555514384328daebf3d5e8f1de0956e6abb0f2427ca2b9fbd0cdf040cac0d4c9

## Step 3: fixtures and replacement grader (recorded 2026-11-11 00:39 UTC)

- Fixtures: `audit/tests/fixtures.py`, 349 fixtures over all 58 checks (pass, fail and near-miss per check, plus 52 probes added after reading the code; every label from CONTRACTS.md alone). Stable id = check + sha256(kwargs, response)[:8].
- `audit/tests/test_grader_fixtures.py`: the grader passes 271 and gets 78 wrong; the 78 carry `xfail(strict=True)`. `audit/tests/classification.py` classifies each: 52 findings, 26 decisions (named D-entries).
- Replacement grader: `audit/replacement/ifb_replacement.py`, all 58 checks from the contracts, one switch per decision entry (`SWITCHES`); alternatives needing human judgment are marked NOT_IMPLEMENTED (D-content-history, D-sentence-type grammar, D-simple-which, D-alliteration sound, D-syllable dictionary). `audit/tests/test_replacement_fixtures.py`: 349/349 pass.
- Findings so far (details in AUDIT.md): F-04..F-32 (check defects), F-33 (sentence splitter treats list labels as sentences, from step 4), F-20 withdrawn into decision D-paren-closed (contract v3).

## Step 4: reference comparison and stress tests (recorded 2026-11-11 00:39 UTC)

- Grader vs reference code: the reference at 1c40f0c differs from the grader in 7 places, each a fix in the reference: word trigrams for ratio:overlap, the "all different words" test in ratio:sentence_words, punctuation stripping in custom:sentence_alphabet, whole-word counting in count:keywords_multiple, punctuation-free tokens in words:words_position, word (not character) indices in repeat:repeat_span (`audit/work/instructions_ref_vs_grader.diff`).
- Reference unit tests vs replacement (`audit/scripts/s4_reference_tests_vs_replacement.py`): 71 tests run, 6 classic-IFEval tests skipped, 6 failing assertions, each contradicted by the contract's proposal: line 1007 TEST_EUROPE (D-capitals-set), line 275 TEST_NESTED_PARENTHESES_TRUE2 (D-paren-closed), line 235 TEST_PALINDROME2 (D-palindrome-distinct), line 252 TEST_PUNCTUATION2 (contradicted under every reading: only `. , ! ? ; :` and `!?`; encodes F-08), line 1163 quote_unquote "123..." (D-vacuous), line 942 TEST_NEWLINE_COUNTRIES (52 of 54 countries; D-africa-set).
- Metamorphic tests (`audit/scripts/s4_metamorphic.py`, 1,375 edited responses from passing fixtures): grader wrong on 152, reference 152, replacement 0.
- Fuzz (`audit/scripts/s4_fuzz_contentfree.py`, 60 generated strings per instance x 344 instances): 0 exceptions in all three graders; the only exception found is the fixture `custom:csv_quotes#fa168408` (IndexError, F-11), in grader and reference. Neither harness catches exceptions: grader.py has no try/except, and the reference's run_eval.py loop stops at the first exception.
- Content-free responses: empty and whitespace pass nothing (harness guard). Repeated words pass 102 of 344 instances under the grader (13 checks), 45 under the replacement (5 checks, each a genuine contract pass such as a 0% stop-word ratio).

## Step 5 setup: held-out responses (recorded 2026-11-11 00:39 UTC, before any panel grading)

- Held out from any replacement change: the `greedy_repeat` run of every configuration (16 run files, 4,800 responses). List: `audit/frozen/heldout_runs.txt`, sha256 `d8d5cd111d66bdd1fa5c999cd13a78e876b0c7ccb7be31eced3ddf188dbabd38`. Disagreements in these files are not inspected until the replacement is frozen.
- (Step 2 record) 2026-11-11 00:44 UTC: CONTRACTS.md v4 (new D-japanese-segmentation, from non-held-out panel responses), frozen copy audit/frozen/CONTRACTS_v4_2026-11-11T0044Z.md, sha256 87e75878647519a3891e819247a65717cd52aaabc5bcc27404f3ecc87d7a4013
- 2026-11-11 00:44 UTC replacement changes from non-held-out panel inspection: custom:word_reverse now fails forward English text (scored by English bigrams), as the contract requires (bug fix, not a reading change); count:words_japanese implements D-japanese-segmentation (contract v4).
- 2026-11-11 00:47 UTC: replacement FROZEN for step 5: audit/replacement/ifb_replacement.py = audit/frozen/ifb_replacement_frozen.py, sha256 79b7f480380f06d97c008788b138d708c569c8b1071b3f4f3f0ad9759da754d5. Changes made from non-held-out panel inspection before freezing: word_reverse forward-English test, D-japanese-segmentation (contract v4), Markdown emphasis removed inside words, inline separators for format:list. Held-out runs were not inspected.
- 2026-11-11 00:49 UTC: post-freeze crash fix (no reading change): words:odd_even_syllables counted syllables of a hyphenated compound by passing it whole to syllapy, which recursed past Python's limit on one panel response (Qwen2.5-32B sample6 key 233, not held out). Now sums the parts. Re-frozen: sha256 8de19f99b9ee3a9c674dae5673011602014290ffdd2563aa24bc37be74e05b10 (audit/frozen/ifb_replacement_frozen.py). Panel regraded; replacement coverage 100%.

## Findings and decision entries (summary; full text in AUDIT.md sections 5 and 6)

Recorded 2026-11-11 00:59 UTC.

- Findings (35): F-01 dataset revision unpinned in eval_instruct.py; F-02 NLTK data downloaded at import (unpinned); F-03 vendored grader has no recorded source commit; F-04 conjunctions counts case variants as different; F-05 keywords_multiple substring counting; F-06 numbers merges 10-20; F-07 pronouns counts determiners; F-08 punctuation checks only 6 marks; F-09 typographic punctuation and HTML stay in words; F-10 character_reverse substring test; F-11 csv_quotes IndexError; F-12 capitals key omits Kyiv; F-13 mcq parser; F-14 flag/keycap emoji; F-15 list marker counted anywhere; F-16 newline whitespace-only line; F-17 no_bullets_bullets (period not checked, blank lines, bold); F-18 options typographic apostrophe; F-19 output_template presence only; F-20 withdrawn (D-paren-closed); F-21 quotes counts apostrophes; F-22 quote_unquote comma passes; F-23 sub-bullets split on every *; F-24 thesis any italic anywhere; F-25 title_case minor words and contractions; F-26 sentence_words no different-words test; F-27 repeat_change trailing newline; F-28 repeat_span character indices; F-29 alliteration sums runs; F-30 paragraph_last_first inner punctuation; F-31 start_verb tagger misses imperatives and markup; F-32 words_position punctuation tokens; F-33 nltk list labels as sentences; F-34 sentence_alphabet first char; F-35 unclosed reasoning graded as answer (stored rule); F-36 loose grading removes every * and first/last lines.
- Decision entries (66): see AUDIT.md section 6 (table with readings, examples and panel effect of each).
- Panel: grader vs replacement disagree on 6,506 of 78,432 verdicts (8.3%), held-out 482 of 5,504 (8.8%); strict prompt accuracy changes -3.94 to +3.22 points per configuration; 8 of 120 configuration pairs flip.
- Recommendation (provisional, needs step 6): fix the grader by replacing the checkers with a contract implementation.
- 2026-11-11 01:03 UTC: reference whole pipeline (`run_eval.py`, verbatim copy) run on 3 stored runs (`audit/scripts/s4_reference_pipeline.py`): strict and loose prompt-level accuracies equal the step-5 per-response reference verdicts exactly. Needs PYTHONUTF8=1 on Windows (locale-encoded file reads).
- 2026-11-11 01:03 UTC: AUDIT.md appendix A (pass rate per check) added; every command in AUDIT.md section 5 verified by `audit/scripts/verify_report.py` (36 OK, 0 BAD).

## Frozen files and sha256 (recorded 2026-11-11 01:04 UTC, final check)

- 5419289271db5dae4ce579d442436407aca712dd9fac363c72ed092cfcd71127  audit/frozen/CONTRACTS_v1_2026-11-11T0007Z.md
- cd222e61d4264d089839c10afd4f6829f112f6edd0ca45eb33147ddec0f6fcb2  audit/frozen/CONTRACTS_v2_2026-11-11T0021Z.md
- 555514384328daebf3d5e8f1de0956e6abb0f2427ca2b9fbd0cdf040cac0d4c9  audit/frozen/CONTRACTS_v3_2026-11-11T0032Z.md
- 87e75878647519a3891e819247a65717cd52aaabc5bcc27404f3ecc87d7a4013  audit/frozen/CONTRACTS_v4_2026-11-11T0044Z.md
- 541e49209ca68f7697ba7835a5e54bc572534d8a35956d947221f1cc4384b6d5  audit/frozen/dataset_row_hashes.tsv
- d8d5cd111d66bdd1fa5c999cd13a78e876b0c7ccb7be31eced3ddf188dbabd38  audit/frozen/heldout_runs.txt
- 8de19f99b9ee3a9c674dae5673011602014290ffdd2563aa24bc37be74e05b10  audit/frozen/ifb_replacement_frozen.py
- aa613580450e311c846b4dd231191191b2da174269d7f0e4d83f7e1e14bd2103  audit/frozen/panel_summary.json
- 404f97bd692c6e1427555a90d47999c85b74037c9ddf28e3a39130612b3f2a14  audit/tests/fixtures.py
- 27f6d8ac74842bb4eb71cd4c48420a88f7b1358246293464fee31d4f5957d7a6  audit/tests/classification.py
- Final checks: case/MANIFEST.sha256 424/424 match after all runs, no unlisted files; verbatim package copies 14/14 match; pytest audit/tests: 628 passed, 81 xfailed.
