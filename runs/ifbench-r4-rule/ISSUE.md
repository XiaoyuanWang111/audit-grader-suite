# Audit: IFBench grader (Marin's vendored Evalchemy copy)

Offline stand-in for the audit issue. Workspace W = `<W>`.
Times are UTC, read with `date -u` in the same step.

## Progress

- [x] Step 1 (pre-contract part): pinned what run records, configuration and lockfiles show.
- [x] Step 2: contracts written from task text, hashed 2026-11-10 05:47:39 UTC, before any grader or
      reference code was read.
- [x] Step 1 (post-contract part, 2026-11-10 ~06:00 UTC): code-only pins recorded below.
- [x] Step 3 (06:03 UTC): 215 fixtures over 58 checks in `audit/tests/fixtures_data.py`;
      grader wrong on 88 (strict xfail). Results `audit/out/fixture_results.tsv`.
- [x] Step 3b (06:20 UTC): replacement grader `audit/replacement/grader.py` built from the contracts,
      one switch per decision entry; matches every fixture except F38 (syllables).
- [x] Step 4 (06:10-06:25 UTC): reference pipeline run (`run_eval.py`, equivalence 0/300 rows differ);
      reference unit tests run against grader, reference and replacement (`audit/scripts/run_ref_tests.py`);
      property tests (`audit/tests/test_properties.py`), fuzz and content-free responses
      (`audit/scripts/step4_fuzz_contentfree.py`), loose transform (`audit/tests/test_loose.py`).
- [x] Step 5 (06:10-06:35 UTC): all 68,400 stored responses graded by G, Gi, R (strict and loose),
      X and XG (`audit/scripts/step5_grade_panel.py`, `step5_add_replacement.py`, `step5_aggregate.py`;
      summary `audit/out/step5_summary.md`).
- [ ] Step 6: not run in this exercise (no reviewers). Pre-registered criterion below.
- [x] Step 7 (06:38 UTC): `audit/AUDIT.md` written. Recommendation: fix the grader; step 6 still needed
      to show the replacement's error rate is lower.

Final checks at 2026-11-10 06:38 UTC: `pytest audit/tests` = 474 passed, 110 xfailed (strict);
`audit/repro.py all` prints exactly what AUDIT.md reports (`audit/out/repro_all.txt`); `case/` still
matches its manifest (425 files, none changed); `audit/work/` copies match the manifest.

Full test run: `NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests -q -p no:cacheprovider`

What is left: step 6 (blinded review from the held-out runs); maintainers' choices on the decision
entries; F38 (syllables) needs a pronunciation dictionary the environment does not have; U1-U5.

How to resume: working copies of grader and reference are in `audit/work/` (verify with
`cd audit/work && sha256sum -c --quiet ../out/work_manifest.sha256`); `audit/lib/harness.py` grades one
response; `audit/scripts/run_fixtures.py` then `make_xfail.py` regenerate fixture results.

## Pinned inputs (step 1)

All files under `case/` match `case/MANIFEST.sha256` (424 entries; `sha256sum -c --quiet` passed
2026-11-10 ~05:40 UTC). sha256 of `MANIFEST.sha256` itself:
`577f586d785f170225a4247b635348ee0db3e606c67afd652f76756c510b160f`.

| Input | Pin | Source |
|---|---|---|
| Grader under audit | `case/grader/IFBench/` files: `instructions.py` fe169405..., `instructions_registry.py` 58a47974..., `instructions_util.py` b7d60e07..., `eval_instruct.py` d4228b13..., `grader.py` 3e49aff4..., `__init__.py` e3b0c442 (empty) | MANIFEST; **no commit recorded** (unverified, see U1) |
| Reference implementation | allenai/IFBench commit 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d; checker files `reference/IFBench/ifbench/instructions.py` a76a3b30..., `instructions_registry.py` 5119f291..., `instructions_util.py` 6996a6ef... | TASK.md, MANIFEST |
| Dataset | allenai/IFBench_test revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2; parquet sha256 80037e4d99c39a55c1e2e7d5a863d8d9edeb5ebe136ba8c1e849f8c015027c6a; 300 rows, 344 (prompt, check) pairs, 58 instruction ids | TASK.md; per-row hashes in `audit/frozen/dataset_row_hashes.tsv` (sha256 ffb4089221732cdec33e72fe40ab5729f19341157ec3f4db29b6b4ffba1ccbc9) |
| Prompt rendering | one user message = dataset `prompt`, no system message, model's own chat template at the listed revision via vLLM `LLM.chat` defaults; Qwen3 `enable_thinking` False/True | `case/panel/CONFIGS.md` |
| Response extraction (generation side) | `response` = text after the last `</think>` in the completion, leading whitespace removed; whole completion if no `</think>`. Verified: `response` equals this rule on all 68,400 lines | CONFIGS.md; `audit/scripts/panel_stats.py` |
| Generation settings | max new tokens 1,024 (thinking off) / 8,192 (thinking on); context = max new tokens + 1,024; temperature 0 or 0.7 with per-request seed 10060+i; engine seed 10060; no top-p/top-k/penalties; stop sequences: none recorded beyond model defaults; reasoning parser: none (offline `LLM.chat`, split by post-processing); vLLM 0.30.0 except thinking configs (not recorded, U2) | CONFIGS.md |
| Model revisions | per configuration in CONFIGS.md and in every line's `revision` field | CONFIGS.md |
| Python environment | Python 3.12.10; `pip freeze` equals `case/deps/requirements.lock.txt` (sha256 5ae01214...) line for line (nltk 3.10.0, emoji 2.15.0, syllapy 0.8.0, langdetect 1.0.9, immutabledict 4.3.1, absl-py 2.5.1); no spaCy installed | lockfile |
| NLTK data | `case/deps/nltk_data/`: corpora/stopwords, taggers/averaged_perceptron_tagger_eng, tokenizers/punkt, tokenizers/punkt_tab; 155 files, each in MANIFEST; sha256 of the sorted per-file `sha256sum` list: 793c7d64a0536b5f67aa56e7328fa04522ee505f7c2591530ee7c7498691ff6c. No NLTK data package version recorded (U3) | MANIFEST |

Unverified inputs:

- U1: the grader's source commit (Marin repository path of the vendored Evalchemy copy, and the
  Evalchemy commit it was copied from). Location: Marin's evaluation config / vendoring commit.
  Verify with `git -C <marin> log -1 --format=%H -- <path to vendored IFBench>` and compare the
  five files' sha256 with the pins above.
- U2: vLLM version for `Qwen__Qwen3-8B__thinking` and `Qwen__Qwen3-14B__thinking`. Location: those
  runs' job records (CONFIGS.md says "not recorded").
- U3: NLTK data package versions (punkt, punkt_tab, averaged_perceptron_tagger_eng, stopwords).
  Location: the nltk_data index used to build `deps/nltk_data`; verify with
  `python -c "import nltk; nltk.download('punkt_tab', download_dir=X)"` into an empty dir and
  compare file hashes (needs network).
- U4: the evaluation run's own grading records (Evalchemy output files and the scores Marin
  reported) are not in the case folder, so the audit cannot check which grading mode (strict or
  loose) and which aggregation produced reported scores.

### Code-only pins (recorded after the contract hash)

- Harness `eval_instruct.py`: imports `eval.sources.common`, `eval.contracts.eval_spec`, `eval.task`
  (not in the case folder). Loads `load_dataset("allenai/IFBench_test", split="train")` with **no
  revision** (F39). Generation kwargs `do_sample=False, temperature=0, max_gen_toks=1024`.
  `PRIMARY_METRIC = "strict_prompt_accuracy"`; METRICS also report loose prompt/instruction accuracy.
  kwargs reach the grader as `dict(kw)` of the HF struct: every key present, unset keys `None`,
  numbers as `float` (the parquet stores `N`, `n`, `m`, `n_start`, `n_end`, `small_n`, ... as float64).
- Extraction rule used by the evaluation: not visible. `text_specs(...)` and the `"instructions"`
  grader with `reference={"protocol": "ifbench"}` live in Evalchemy/Marin code that is not here (U5).
  `grader.py` grades the string it is given; it strips nothing and has no `</think>` handling.
- `grader.py` strict: a check fails when the response is empty or whitespace-only; exceptions from
  `check_following` are not caught (propagate to the unseen caller). Loose: 8 variants (remove
  first line, last line, both; delete every `*`), pass if any variant passes.
- Responses are looked up by prompt text (`prompt_to_response[inp.prompt]`); the 300 prompts are
  distinct, so no collision.
- Checker dependencies: nltk 3.10.0 (`sent_tokenize` = punkt_tab, `word_tokenize`, `pos_tag` =
  averaged_perceptron_tagger_eng, stopwords english, `RegexpTokenizer(r"\w+")`), emoji 2.15.0
  (`is_emoji` per code point), syllapy 0.8.0, Python `csv`, `unicodedata`.
- NLTK data resolution: `instructions.py` creates `<package>/.nltk_data` at import, inserts it first
  on `nltk.data.path`, and sets `NLTK_DATA` only if unset; `instructions_util.py` calls
  `nltk.download(...)` at import for any missing resource (latest version, network) (F40).
- Reference pipeline (`run_eval.py` + `evaluation_lib.py`, commit 1c40f0c) reads its own JSONL
  (`data/IFBench_test.jsonl`): there `n`, `m`, `n_start`, `n_end` are ints; prompts of keys 13 and 19
  lack the trailing whitespace the HF parquet has; `ifbench/data/IFBench_test.jsonl` matches the parquet
  except for those int types. Reference README: the paper reports **prompt-level loose** accuracy.
- U5: the Evalchemy/Marin code between generation and `grader.py` (`text_specs`, the
  `"instructions"` grader, the reducer): extraction rule, kwargs types, exception handling.
  Location: Marin's vendored Evalchemy `eval/sources/common.py` and the grader registry. Verify by
  reading those files at the commit that produced the reported scores.

### Held-out panel responses (recorded 2026-11-10 06:10 UTC, before any replacement-grader work)

Held out from any tuning of a replacement grader: run `sample7` of each of the 14 configurations that
have sampled runs, and run `greedy_repeat` of `Qwen__Qwen3-8B__thinking` and
`Qwen__Qwen3-14B__thinking` (16 files, 4,800 responses). Nothing has been fitted to the panel yet.

## Contract

`audit/CONTRACTS.md` v1 written from the 300 prompts and CONFIGS.md only.
sha256 `f2ed95e9ebd43209d32bfeb99d312eb2c422fe6b4fdc63c46252bd6782f3d900`, recorded
2026-11-10 05:47:39 UTC, before any grader or reference code was read. Frozen copy
`audit/frozen/CONTRACTS_v1.md` (same hash).

### Step 6 criterion (recorded 2026-11-10 06:29 UTC, before any review; the review was not run)

The recommendation "fix the grader by adopting the replacement" holds if: the replacement passes every
fixture (all but F38 today), its scored coverage is complete (100% on the panel), and on a blinded
review drawn from the held-out runs, stratified by whether G and X disagree, its error rate is lower
than the grader's with a paired 95% bootstrap interval that excludes zero. If the interval includes
zero, the recommendation falls back to "fix the defects in place" (F01-F38 patches) without claiming a
lower error rate. If the grader's error-rate upper bound were below 2%, the recommendation would be
"admit"; nothing in steps 3-5 suggests that.

## Decision entries

Named in the contract and exercised by fixtures; the full table with readings, examples, proposals
and the grader's reading is in `audit/AUDIT.md`. Entries: D-empty, D-word, D-sentence, D-paragraph,
D-keyword-match, D-vacuous, D-markup, D-conj-usage, D-count-exact, D-number, D-name-usage,
D-pronoun-set, D-punct-set, D-unique, D-between, D-japanese-script, D-reverse-extra, D-csv-payload,
D-csv-rowcount, D-csv-header-quotes, D-csv-special, D-custom-content, D-list-extra, D-list-labels,
D-capitals-set, D-mcq-length, D-mcq-answer, D-africa-set, D-emoji-def, D-indent, D-list-sep,
D-nobullets-order, D-trailing-ws, D-options-extra, D-template-brackets, D-paren-closed (added 06:18 UTC:
the reference's own unit test asserts a pass for a string whose outer brackets never close, which shows
a second reading; the fixture `((((( x )` moved from finding F30 to this entry), D-quote-chars,
D-subbullet-indent, D-section, D-title-minor, D-overlap-reference, D-overlap-measure, D-balance,
D-ratio-exact, D-char-count, D-different-words, D-stopword-list, D-repeat-trailing, D-change-case
(added 06:00 UTC: contract v1 states "a change of letter case only is not a change" without an entry;
recorded as a decision because the text does not define "change"), D-copy-case (added 06:00 UTC, same
reason for exact copies), D-repeat-simple-target, D-span-extra, D-alliteration, D-consonant-y,
D-syllable, D-palindrome-distinct, D-repeat-count, D-vowel.

## Findings

F01-F38 (F30 withdrawn, now D-paren-closed) and F39-F43; table with counterexamples, commands,
contracts, panel shares and reference status in `audit/AUDIT.md`. Each counterexample reproduces with
`NLTK_DATA=case/deps/nltk_data PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe audit/repro.py <id>`
(output of `repro.py all` in `audit/out/repro_all.txt`).

## Frozen files

| File | sha256 |
|---|---|
| `audit/frozen/CONTRACTS_v1.md` | f2ed95e9ebd43209d32bfeb99d312eb2c422fe6b4fdc63c46252bd6782f3d900 |
| `audit/frozen/dataset_row_hashes.tsv` | ffb4089221732cdec33e72fe40ab5729f19341157ec3f4db29b6b4ffba1ccbc9 |
