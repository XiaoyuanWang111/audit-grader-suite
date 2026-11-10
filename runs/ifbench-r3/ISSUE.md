# Audit: IFBench grader (Marin's vendored Evalchemy copy)

This file stands in for the audit issue (offline exercise, no tracker). It holds the pinned
inputs, the contract hash and time, the decision entries, the findings, and the hashes of the
frozen samples. Paths are relative to `W = <W>`.

## Progress

| Step | State | Where |
|---|---|---|
| 1. Pin the inputs | done (record-level 22:10 UTC, code-level 22:30 UTC) | this file, "Step 1" |
| 2. Contracts | done 2026-11-09 22:16 UTC (v1 hash recorded) | `audit/CONTRACT.md` |
| 3. Fixtures | done 2026-11-09 22:47 UTC: 277 fixtures, grader wrong on 84 (52 finding, 32 decision) | `audit/tests/fixtures_data.py`, `test_fixtures_grader.py` |
| 4. Reference comparison and stress | done 2026-11-09 23:30 UTC | this file, "Step 4"; `audit/tests/test_properties.py` |
| 5. Panel | done 2026-11-09 23:45 UTC (stored responses only) | this file, "Step 5"; `audit/work/panel_verdicts.jsonl` |
| 6. Blinded review | done: 6.1-6.3 2026-11-09 23:48 UTC; 6.4 labels received (both reviewers 458 of 458) and checked 2026-11-10 07:17 UTC; 6.5 analysis 2026-11-10 07:18 UTC | this file, "Step 6"; `audit/frozen/review_round1/`, `audit/frozen/reviews/`, `audit/work/analyze_review.log` |
| 7. Report | done: first complete version 2026-11-10 07:31 UTC; post-label analysis added 07:43 UTC (AUDIT.md sections 5.4 and 8); every command rerun and checked 07:51 UTC (AUDIT.md section 10) | `audit/AUDIT.md` |

Recommendation (AUDIT.md section 2): fix the grader, with the replacement grader as the fix and the
47 decision entries left to the maintainers.

Open: a second review round, needed once the replacement is repaired for REPL-emoji-flag or set
to readings other than the proposed ones; it must use held-out responses that round 1 did not use.
The 14 disputed cases and the 11 unclassified panel disagreements (AUDIT.md sections 3.7 and 5)
are not resolved.

## Step 1. Pinned inputs

Checked with `audit/scripts/pin_inputs.py` (re-run before and after every grading run; exit 0
means every file matches `case/MANIFEST.sha256` and every installed package matches the lock).

| Input | Pin | Source | Verified |
|---|---|---|---|
| Grader under audit | `case/grader/IFBench/` (Marin's vendored copy of Evalchemy's IFBench), files: `instructions.py` fe169405…6d302, `instructions_registry.py` 58a47974…43aed, `instructions_util.py` b7d60e07…0b8, `eval_instruct.py` d4228b13…f9ea, `grader.py` 3e49aff4…285c, `__init__.py` (empty) | `case/MANIFEST.sha256` | hashes match the manifest; the Marin and Evalchemy commits of this copy are not recorded in the case (see F-pin-1) |
| Reference implementation | allenai/IFBench at 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d; checker files `ifbench/instructions.py` a76a3b30…4cf, `ifbench/instructions_registry.py` 5119f291…aed, `ifbench/instructions_util.py` 6996a6ef…930, `evaluation_lib.py` e681a4b0…6cfa, `run_eval.py` 08423254…bf75, tests `instructions_test.py` e312bb40…ed | `case/TASK.md`, manifest | hashes match the manifest; commit not checked against GitHub (no network). Verify: `git clone https://github.com/allenai/IFBench && git -C IFBench checkout 1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d && sha256sum IFBench/ifbench/*.py IFBench/*.py` |
| Dataset | allenai/IFBench_test at 2e8a48de45ff3bf41242f927254ca81b59ca3ae2, `data/train-00000-of-00001.parquet` sha256 80037e4d99c39a55c1e2e7d5a863d8d9edeb5ebe136ba8c1e849f8c015027c6a; 300 rows, 344 instruction instances, 58 instruction ids, 44 rows with two instructions; one hash per row in `audit/frozen/dataset_row_hashes.tsv` (sha256 dead3343c495ada3bba42201f71851f9ec69d5c8ffbd5233e29b323460fe7ad7; row hash = sha256 of the sorted-key compact JSON of key, prompt, instruction_id_list, non-null kwargs, read with pyarrow `to_pylist()` so int64 kwargs stay integers as `datasets.load_dataset` returns them; the first version of this file, b7e4d7df…8b56, was computed from the pandas view in which those kwargs are floats and is superseded) | `case/TASK.md`, manifest | parquet matches the manifest; revision not checked against the Hub (no network). Verify: `huggingface-cli download allenai/IFBench_test --repo-type dataset --revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2 --local-dir x && sha256sum x/data/train-00000-of-00001.parquet`. The reference's `ifbench/data/IFBench_test.jsonl` equals the parquet row for row; its `data/IFBench_test.jsonl` differs only by trailing spaces in prompts 13 and 19 |
| Prompt rendering | one user message = dataset `prompt`, no system message, model's own chat template at the pinned model revision (vLLM `LLM.chat` defaults); Qwen3 `enable_thinking` False or True as listed | `case/panel/CONFIGS.md` | all 228 run files: 300 lines in dataset order, `key` and `prompt` equal the dataset row (`audit/scripts/scan_panel.py`) |
| Response extraction (panel records) | `response` = text after the last `</think>` of the completion with leading whitespace removed, or the whole completion when it has no `</think>` | `case/panel/CONFIGS.md` | holds for all 68,400 lines. 136 thinking-on completions open `<think>` and never close it, so their `response` field is the unclosed reasoning (contract: extraction failure) |
| Generation settings | per configuration in `case/panel/CONFIGS.md`: max new tokens 1,024 (8,192 for the two thinking configurations), context = max new tokens + 1,024, engine seed 10060, temperature 0 or 0.7 with per-request seed 10060+i, no other sampling parameter, vLLM 0.30.0 (not recorded for the thinking configurations) | `case/panel/CONFIGS.md` | stop sequences and the server reasoning parser are not recorded (vLLM offline `LLM.chat` returns the completion text only, so no reasoning field is merged); vLLM version missing for the thinking runs (see F-pin-2) |
| Python and packages | Python 3.12.10; 60 packages pinned in `case/deps/requirements.lock.txt` (sha256 5ae01214…161bde), including nltk 3.10.0, langdetect 1.0.9, emoji 2.15.0, syllapy 0.8.0, pandas 3.1.1 | lock file | installed versions equal the lock, nothing unlocked installed |
| NLTK data | `case/deps/nltk_data/`: `tokenizers/punkt` (pickles), `tokenizers/punkt_tab`, `corpora/stopwords`, `taggers/averaged_perceptron_tagger_eng`; 155 files hashed in the manifest | manifest | hashes match; the NLTK data packages carry no version, so the hashes are the only pin |

Which of these the grader actually loads (and any extraction rule it applies itself) is read from
the code only after the contract hash is recorded; see "Step 1, code-level pins" below.

### Step 1, code-level pins (recorded 2026-11-09 22:30 UTC, after the contract hash)

- What the grader loads: `instructions.py` imports nltk 3.10.0 (`sent_tokenize` and
  `word_tokenize` use `tokenizers/punkt_tab/english`; `pos_tag` uses
  `taggers/averaged_perceptron_tagger_eng`; `count_stopwords` uses `corpora/stopwords/english`;
  `RegexpTokenizer(r"\w+")` counts words), emoji 2.15.0 (`emoji.is_emoji`), syllapy 0.8.0
  (`syllapy.count`), and the standard library `csv`, `unicodedata` (Python 3.12.10, Unicode
  15.0), `re`, `string`. The pickled `tokenizers/punkt/english.pickle` is referenced only by an
  unused helper.
- Import-time side effects: `instructions.py` creates a `.nltk_data` folder next to itself, puts
  it first on `nltk.data.path`, and sets `NLTK_DATA` to it when the variable is unset;
  `instructions_util.download_nltk_resources()` then downloads `punkt`, `punkt_tab`, `stopwords`
  and `averaged_perceptron_tagger_eng` from the network when they are missing (F-pin-3).
- Dataset loading: `eval_instruct.py` calls `load_dataset("allenai/IFBench_test", split="train")`
  with no revision (F-pin-4).
- Extraction: neither `eval_instruct.py` nor `grader.py` removes reasoning or `</think>`; the
  graded text is whatever Evalchemy's generation step stores, which is not in the case.
  Unverified; location: Evalchemy `eval/sources/common.py` (`text_specs`) and the `instructions`
  grader it dispatches to. Verify by reading those files at the commit Marin pins.
- Generation settings in code: `generation_kwargs={"do_sample": False, "temperature": 0,
  "max_gen_toks": max_tokens}` with `max_tokens=1024` by default (matches the panel's thinking-off
  configurations; the thinking configurations used 8,192).
- Strict grading (`grader.py`): an empty or whitespace-only response fails every instruction;
  otherwise `check_following(response)` on the unstripped response. Loose grading tries eight
  variants (the response, without its first line, without its last line, without both, and
  each of these with every `*` removed) and passes if any passes. The reference
  (`evaluation_lib.py`) applies the same two transforms.
- Responses are looked up by prompt text; the 300 prompts are distinct, so no collisions.
- How the audit runs the code: byte-identical copies in `audit/work/pkgs/grader/IFBench` and
  `audit/work/pkgs/reference/ifbench` (+ `evaluation_lib.py`, `instructions_test.py`), imported
  with bytecode writing off, so that importing does not create folders under `case/`.
  `audit/lib/ifb.py` (`verify_pins`) checks every copy, the parquet and the lock file against the
  manifest before each run. Its per-instruction wrapper reproduces `grader.py`'s strict and loose
  functions exactly (344 of 344 verdicts on one stored run, `audit/scripts/smoke_grader.py`).

### Stored-record counts (from `audit/scripts/scan_panel.py`, `audit/work/panel_scan.csv`)

- 68,400 responses in 228 run files of 16 configurations.
- 4,165 responses stopped at the token limit (`finish_reason == "length"`), 6.1%.
- Thinking on: 1,800 completions, all open `<think>`; 136 never close it (Qwen3-8B 104 of 900,
  Qwen3-14B 32 of 900). Thinking off: one Qwen3-32B completion contains a `</think>`.
- 37 responses are empty after extraction (Qwen3-14B 28, Qwen3-8B 5, marin-8b-instruct 4).

## Held-out runs (step 5)

Chosen before the panel is graded by any replacement, with `audit/scripts/choose_heldout.py`
(seed 20261109): one sampled run per configuration, or one of the three greedy runs for the two
thinking configurations. List: `audit/frozen/heldout_runs.tsv`, sha256
f0b61346260e4a08563f02478830864589ae528b267d8b463ade7c9bb175f848. These runs are never used to
change the replacement grader; the review sample is drawn from them.

## Step 2. Contract

- `audit/CONTRACT.md` version 1: sha256 b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95,
  recorded 2026-11-09 22:16 UTC, before any grader or reference code was opened (only the dataset
  prompts, `case/panel/CONFIGS.md`, the manifest, the lock file and the panel records had been
  read). A byte-identical copy is `audit/frozen/CONTRACT_v1.md`.
- 58 check contracts, shared rules G1 to G6, 47 decision entries (table at the end of the file).
- Later changes to the contract are listed here with their reason.
- Version 2, 2026-11-09 22:43 UTC, sha256 5175ec90cbced57cadf39c59e9976731a73ef803e231b06f56df5adc0b0bb813
  (copy `audit/frozen/CONTRACT_v2.md`), written after the grader code was read; no proposed
  reading changed. D-paragraph gains reading C (every line break starts a paragraph) and
  D-options gains reading D (only the bare option string counts). Reason: both are readings a
  careful reader could defend that version 1 omitted (details at the top of the decision table).
  Effect: two fixtures that the grader fails (`words:vowel-f01e48fd`, `format:options-ff170446`)
  count as decisions, not findings.

## Decision entries

47 entries, each with both readings, an example of each and the proposed reading, in the table at
the end of `audit/CONTRACT.md` (version 2): D-vacuous, D-word, D-word-numbers, D-sentence,
D-paragraph, D-match, D-keyword-count, D-conj, D-number, D-names-case, D-pronoun, D-punct-set,
D-unique, D-between, D-japanese, D-emoji-position, D-indent, D-list, D-options, D-template,
D-paren, D-subbullet, D-section, D-title, D-overlap, D-balance, D-char-count, D-different-words,
D-stopwords, D-repeat-change, D-repeat-simple, D-span, D-alliteration, D-alphabet-start, D-y,
D-syllables, D-palindrome, D-prime-length, D-repeat-count, D-verb, D-vowel, D-custom-facts,
D-custom-extra-text, D-csv, D-char-reverse, D-mcq, D-trailing-ws.

Where the grader takes a non-proposed reading (from the step 3 fixtures and the step 5 switch
counts): D-vacuous B (a lone period passes 14 checks that the contract fails, step 4), D-word C (standalone punctuation tokens are
words), D-sentence B (line breaks do not end sentences), D-match B (substring keyword counts),
D-conj B, D-punct-set below B (see F-punct-six-marks), D-overlap D (character trigrams), D-paren C,
D-subbullet B, D-section B, D-title B, D-template C, D-csv C and E, D-custom-facts B and C,
D-palindrome B and C, D-repeat-change C, D-paragraph C, D-options D, D-indent C. Counts of the
panel verdicts each switch changes are in `audit/work/analyze_panel.log`.

## Step 3. Fixtures

- `audit/tests/fixtures_data.py`: 277 fixtures, at least a pass, a fail and a near-miss for every
  one of the 58 checks (68 pass, 57 fail, 62 near-miss, 47 defect reproductions, 43 decision
  probes). Labels come from the contract's proposed readings; `decisions` lists the entries
  whose other readings would flip a label. Id = check + first 8 hex of sha256(kwargs, response).
- `audit/tests/test_fixtures_grader.py` runs them against the grader (strict); the 84 the grader
  gets wrong carry `pytest.mark.xfail(strict=True)` with the finding or decision id as reason.
  `test_fixtures_reference.py` does the same for the reference (75 wrong: 46 finding, 29
  decision). Run: `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider audit/tests`
  (run at about 22:44 UTC: 395 passed, 159 xfailed).
- Grader-wrong fixtures that are decisions (a non-proposed reading makes the grader right):
  D-vacuous 7, D-word 3, D-custom-facts 3, D-csv 2, D-match 2, D-palindrome 2, and one each for
  D-conj, D-indent, D-options, D-overlap, D-paragraph, D-paren, D-punct-set, D-repeat-change,
  D-section, D-sentence, D-subbullet, D-template, D-title.

## Step 4. Reference comparison and stress (2026-11-09, 23:00 to 23:30 UTC)

- Code diff, reference 1c40f0c against the grader: the reference changes 7 checkers. It counts
  word trigrams in ratio:overlap (the grader counts character trigrams), checks "all different
  words" in ratio:sentence_words, counts whole words in count:keywords_multiple (the grader
  counts substrings), strips leading punctuation in custom:sentence_alphabet, drops punctuation
  tokens in words:words_position, cuts repeat:repeat_span by word indices (the grader by
  character indices), and refactors words:repeats and words:no_consecutive without changing
  behavior. Everything else, including the strict and loose functions, is the same.
- Fixtures against the reference: wrong on 75 of 277 (46 finding, 29 decision). Fixed relative
  to the grader: F-alphabet-story-quote, F-sentwords-no-word-check, F-span-characters,
  F-wordspos-comma; the reference also takes the proposed reading of D-match and D-overlap.
- Reference pipeline defect (R-loose-order, minor): `evaluation_lib.test_instruction_following_loose`
  passes the unfiltered kwargs to `build_description`; it works only because the strict
  function, which `run_eval.py` calls first, replaces `inp.kwargs[index]` with the filtered dict.
  Run alone, every instruction raises `TypeError` (unexpected keyword argument).
- Reference unit tests against the replacement (`audit/scripts/reftests_vs_replacement.py`, shim
  in `audit/work/shim/`, records in `audit/work/reftests_vs_replacement.json`): 65 tests, 177
  assertions on the 58 IFBench checks. The replacement contradicts 9 assertions. One contradicts
  every reading: `test_punctuation` line 252 expects 'All the punctuation marks: . , ! ? ; : !?'
  to pass (F-punct-six-marks). Eight encode a decision: `test_csv_special_character` line 1073
  (D-csv E, two special-character fields), `test_europe_capitals` line 1007 (D-custom-facts B,
  the 27-city list without Kyiv), `test_nested_parentheses` line 275 (D-paren C, the brackets do
  not close), `test_palindrome` line 235 (D-palindrome B and C, "abcba" ten times),
  `test_quote_explanation__handles_empty_string_after_stripping` lines 1163 and 1164 (D-vacuous
  B, '123...' and ''), `test_reverse_newline` line 942 (D-custom-extra-text B and D-custom-facts
  B: a lead-in line, and the list misses Ethiopia and Gambia), `test_three_vowels` line 193
  (D-paragraph C). Two further mismatches were replacement errors and were fixed (the
  conjunction heuristic missed "yet" before a clause; a single quoted character was taken as a
  quoted phrase).
- Fuzzing (`audit/scripts/step4_stress.py`, seed 20261109): 400 random texts per check, 58
  checks: no exception in the grader or the reference. A targeted input finds one:
  custom:csv_quotes raises `IndexError` on any empty field (`field.strip()[0]`), in the grader
  and the reference, and the exception leaves `test_instruction_following_strict`, so a run
  stops on that response unless the caller catches it (F-csvquotes-indexerror; the caller is in
  Evalchemy and not in the case). The exception needs the header, exactly 3 data rows and 5
  fields in every row, so that the field check is reached (corrected 2026-11-10; the earlier
  note "a data row ending in a tab" alone returns fail before that check). Reproduce:
  `.venv/Scripts/python.exe -B audit/scripts/repro.py F-csvquotes-indexerror`.
- Content-free responses, grader strict, instruction instances passed (of the check's total):
  - empty or whitespace: none (the strict function fails them first).
  - a single period ".": 106 in 16 checks, every instance of count:words_japanese,
    format:line_indent, format:newline, format:quote_unquote, format:sub-bullets,
    format:title_case, sentence:alliteration_increment, sentence:increment, words:last_first,
    words:no_consecutive, words:odd_even_syllables, words:prime_lengths, words:repeats,
    words:vowel, plus format:no_whitespace and words:paragraph_last_first (which the contract
    also passes); the replacement passes 10.
  - "word" repeated 100 times: 101 in 13 checks (adds ratio:sentence_balance 7/7,
    ratio:sentence_type 6/6, ratio:stop_words 12/12, words:consonants 15/15); the replacement
    passes 44 (stop words, consonants, vowel and paragraph checks, which "word word ..." does
    satisfy).
  - "This is a sentence." repeated 30 times: 52 in 7 checks.
  - the prompt itself restated: 50 in 15 checks, including format:output_template 4/4 (the
    labels appear in the prompt) and format:sub-bullets 11/12.
- Metamorphic edits on the 16 greedy runs (verdict flips, grader / replacement): appending a
  newline flips format:options 58 of 96 / 0, format:no_bullets_bullets 28 of 80 / 0,
  repeat:repeat_change 7 of 48 / 0 (format:no_whitespace 37 of 64 / 37, as the contract wants);
  turning straight double quotes into curly ones flips format:quotes 27 of 114,
  format:quote_unquote 11 of 59, count:conjunctions 6 of 29, ratio:overlap 3 of 57,
  words:palindrome 3 of 45, sentence:keyword 1 of 59 (CSV checks flip under both, as they
  should).
- Property tests (`audit/tests/test_properties.py`): 18 cases, 14 grader violations marked
  `xfail(strict=True)`: verdict changes under a trailing newline (F-options-whitespace,
  F-nbb-blank-line), under a second blank line (F-indent-blank-lines: one blank line between
  stairs passes, two fail, because `IndentStairsChecker` removes items from the list it is
  iterating), under tabs for spaces (F-indent-tabs), under bold on the first word
  (F-startverb-markup), under a repeated "And" (F-conj-surface-forms); forbidden edits that keep a
  pass (F-subbullets-none, F-template-presence-only, F-sentwords-no-word-check,
  F-punct-six-marks); and loose passes obtained by deleting constrained text
  (F-loose-deletes-constrained: removing every `*` makes any `*`-bullet response pass
  format:sub-bullets; dropping the first line rescues words:start_verb; dropping the last line
  rescues count:keywords_multiple and count:numbers).

## Step 5. Panel (stored responses only; no generation)

Every stored response was graded by the grader (strict and loose), the reference (strict and
loose) and the replacement (`audit/replacement/ifbench_contract.py`, proposed readings, plus one
switched decision at a time): `audit/scripts/grade_panel.py` -> `audit/work/panel_verdicts.jsonl`
(78,432 instruction verdicts), summarized by `audit/scripts/analyze_panel.py` ->
`audit/work/analyze_panel.log`, `audit/work/panel_summary.json`. Pins checked before and after
the run (`ifb.verify_pins`).

- Scored coverage: 100% for every grader on the stored panel (no exception on any stored
  response; the csv_quotes crash of step 4 needs an empty field, which no stored response has).
- Pass rates over all 78,432 verdicts: grader strict 27.7%, grader loose 32.4%, reference strict
  27.6%, replacement 25.4%.
- Grader vs reference: 257 verdicts differ (ratio:overlap 227, custom:sentence_alphabet 23,
  words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1).
- Grader vs replacement: 6,226 verdicts differ (7.9%): grader pass and replacement fail 3,992,
  grader fail and replacement pass 2,234. A single switched decision reproduces the grader's
  verdict in 2,718 of them (largest: D-vacuous B 440, D-section B 360, D-palindrome B or C 317,
  D-subbullet B 245, D-sentence B 230, D-conj B 221, D-overlap D 205, D-paren C 201, D-csv B or C
  146 each, D-word B 87, D-punct-set B 76). Largest per-check differences: format:sub-bullets
  1,216, format:thesis 507, count:conjunctions 416, format:quote_unquote 332, words:palindrome
  326, format:no_bullets_bullets 358, words:start_verb 309, format:quotes 306, count:punctuation
  267, ratio:overlap 205, format:parentheses 202, count:words_japanese 169, count:pronouns 170.
- Extraction failures (G1): 136 thinking-on responses never close `<think>`; their stored
  `response` is the reasoning itself. The grader passes 45 of their 157 instruction verdicts,
  all of which the contract fails (F-extract-unclosed).
- Truncated responses (finish_reason length): 4,588 instruction verdicts; the grader passes
  1,013 of them, the replacement 793.
- Loose transform: 3,666 verdicts (4.7%) pass only under loose grading; the contract fails the
  full response in 2,762 of them (F-loose-deletes-constrained). format:sub-bullets passes 100% of
  2,736 verdicts under loose grading, because deleting every `*` leaves a response with no
  bullets, which the grader passes (F-subbullets-none). Winning variants: no asterisks 1,798, no
  first line 956, no last line 379, no first and last line 479, combinations 54.
- Score change per configuration (prompt-level strict accuracy, mean over runs; replacement minus
  grader, range over runs in brackets; rerun = |greedy - greedy_repeat| under the grader):
  Qwen2.5-14B -4.9 [-7.7, -2.7] rerun 1.0; Qwen2.5-32B -2.3 [-4.0, -0.3] rerun 1.3; Qwen2.5-7B
  -3.4 [-7.3, -1.0] rerun 0.3; Qwen3-14B -1.7 [-3.0, +0.3] rerun 0.3; Qwen3-14B thinking +1.0
  [+0.7, +1.3] rerun 1.0; Qwen3-32B +0.4 [-1.7, +2.3] rerun 0.7; Qwen3-8B -1.5 [-3.3, +0.3] rerun 0;
  Qwen3-8B thinking -1.6 [-2.0, -0.7] rerun 0; Tulu-3-8B +0.6 [-1.7, +2.3] rerun 0.3;
  OLMo-2-32B -2.9 [-4.3, -1.0] rerun 0; OLMo-2-13B -3.9 [-6.0, -2.0] rerun 0; OLMo-2-7B -3.1
  [-6.0, -1.7] rerun 0.7; marin-8b -0.5 [-3.3, +1.7] rerun 1.0; phi-4 +1.2 [-1.3, +3.0] rerun 0;
  Mistral-7B -1.8 [-3.7, -0.3] rerun 0.3; Mistral-Small-24B +1.6 [-0.3, +3.0] rerun 0.3 (points).
  The ranking of the 16 configurations changes (for example Qwen3-14B thinking moves from second
  to first and Qwen2.5-14B from third to fifth). These differences are measured against the
  replacement, whose own error rate step 6 estimates.
- Replacement changes after the panel run, all from non-held-out examples
  (`audit/scripts/inspect_disagreements.py` reads only non-held-out runs) or from crashes:
  count:pronouns reading C crashed (fixed, rows recomputed); words:start_verb (third-person verbs,
  "Here's" removed from the verb list), format:thesis (HTML wrappers such as `<p>` before the
  italics), format:quote_unquote (guillemets as quotation marks), format:list (numbers are not
  bullet symbols in the contract). Rows of these checks were recomputed with
  `audit/scripts/regrade_replacement_rows.py`; the replacement still passes all 277 fixtures.

## Step 6. Blinded review (round 1)

Recorded 2026-11-09 23:48 UTC, before any review started.

Result that would change the step 7 recommendation. Planned recommendation if the review
confirms steps 3 to 5: fix the grader. It changes to:
- admit, if the grader's weighted error rate against the consensus is at most 2% with an upper
  95% bound of at most 3%, and no finding affects more than 1% of verdicts;
- replace the benchmark, if Cohen's kappa between the reviewers' leans is below 0.40 overall, or
  more than 25% of the reviewed cases get an `ambiguous` verdict from either reviewer (the texts
  then do not support reliable grading by any implementation).
The replacement is proposed as the fix only if it passes every fixture (it does, 277 of 277),
scored coverage is complete (it is), and its weighted error rate is lower than the grader's with
a paired 95% bootstrap interval that excludes zero; otherwise the fix is the per-finding repair
list, with the decision entries left to the maintainers.

6.1 Sample (`audit/scripts/draw_review_sample.py`, seed 61109). Population: the held-out run of
every configuration, all instruction instances except the 52 extraction failures (counted under
G1): 5,452 verdicts. Strata and sample sizes:

| Stratum | Definition | Population | Sample |
|---|---|---|---|
| S1a | grader pass, replacement fail | 250 | 170 |
| S1b | grader fail, replacement pass | 180 | 125 |
| S2 | grader = replacement, reference differs | 3 | 3 |
| S3 | grader = replacement = reference | 5,019 | 160 |

6.2 Frozen before any review (files under `audit/frozen/review_round1/`):

| File | sha256 |
|---|---|
| `cases.jsonl` (the case list: id, stratum, check, prompt key, instruction index, response sha256) | f360e3596f16f22c7c53fb117d6096b9784c4849f8406f4ef3a6292c8ad24f4d |
| `key.jsonl` (source configuration and run, every grader verdict; not for reviewers) | f39322475638d564e86a7b2bb63cb6bfccd621e59556c033a93168395634675f |
| `review_cases.jsonl` (what the helper prints from) | 491371ce7905dae83cd492b5dfaaea96497f7b3074eba41ceabdc16da61e6148 |
| `strata.json` | 87f5ac13cd36f426916c6db4c4f543b07584dd771cd11719658562afbee274d0 |
| `show_case.py` (helper) | bd1c6d68d3863110503d6ae732bc26f0da56105f7c857a5f4012ff178c89b80c |
| `prompt_reviewer_A.md` | 8859795100204309c37bb1e5b25efb145524ecc71cac9b0b9373a09c6927a348 |
| `prompt_reviewer_B.md` | feb112b88ac30114f8876c6fd22de6af1e45fd457366a58c6a54ae37ea9e2e74 |
| `MANIFEST.sha256` (every file in the folder: batches, responses, the above) | 5ec4828648954952a495b4b2eeadd015c70627c509f0539d9b44662201a30f3c |

6.3 Rendering. 458 cases, 19 batch files per reviewer (25 cases each, the last 8), in
`audit/frozen/review_round1/batches_A/` and `batches_B/`; the two reviewers get the cases in
different random orders (seeds 61110 and 61111). Each case shows an opaque id (`R1-xxxxx`), the
check name, the requirement text as the prompt renders it (the whole prompt for the 11 custom
checks), the prompt, and the response between BEGIN and END marker lines; no source model,
grader verdict or other reviewer's label. 20 responses longer than 6,000 characters are cut in
the batch and point to `audit/frozen/review_round1/responses/<id>.txt`. Helper:
`W/.venv/Scripts/python.exe W/audit/frozen/review_round1/show_case.py <id>` (`--repr` shows
whitespace, `--json` the whole case). One sampled response introduces itself as Qwen; that is
response text and stays.

How a reviewer returns labels: give reviewer A the text of
`audit/frozen/review_round1/prompt_reviewer_A.md` (the reviewer prompt of
`skill/references/reviewer-prompt.md` with its placeholders filled) and reviewer B
`prompt_reviewer_B.md`, in separate runs. Each writes one JSON object per line, in its batches'
case order, to its own file: reviewer A `audit/frozen/reviews/review_A.jsonl`, reviewer B
`audit/frozen/reviews/review_B.jsonl`, with exactly the fields `case_id`, `verdict` (pass, fail,
ambiguous), `lean` (pass, fail), `confidence` (high, medium, low), `reason` (at most 40 words).
Every case must appear exactly once. Record who or which model ran each reviewer next to the
file (for example in `audit/frozen/reviews/README.md`), since two runs of one model can share
blind spots.

6.4 Labels (checked 2026-11-10 07:17 UTC with `audit/scripts/check_reviews.py`, which reads only).

- Who: both reviewers are runs of one language model, Claude Opus 5.5 (`claude-opus-5-5`); no
  person labeled a case. Two runs of one model can share blind spots, so the agreement below is
  likely higher than two independent reviewers would reach, and shared errors do not show as
  disputes.
- Separation (from `audit/frozen/reviews/README.md`): two separate agents started 2026-11-09
  23:55 UTC, each with only its prompt; each worked in its own folder outside the workspace
  holding copies of its own batches, the full-response files, `show_case.py` and
  `review_cases.jsonl`. A script read every tool call of both runs afterwards: neither opened the
  key, the case list, `strata.json`, the other reviewer's files or any grader, and neither used
  the network. The operator copied the label files unchanged. The audit cannot verify this
  record; it relies on it.
- Files: `review_A.jsonl` sha256 5eec6b187962afa8847f9341f55f8bc7ca627c6ee1bdeaa0f1f31e752e2321fc,
  `review_B.jsonl` sha256 d809a126270b878b5dd43c07989d9a81b10600ef24b25a702006bf54ea3cb0a3, both
  equal to the hashes in the README. Each has 458 lines, every case once, exactly the five
  fields, valid values, lines in its own batch order, no reason over 40 words, and every definite
  verdict equal to its lean. The review-round folder still matches its `MANIFEST.sha256`.
- Verdicts: A pass 197, fail 207, ambiguous 54 (leans pass 225, fail 233); B pass 192, fail 195,
  ambiguous 71 (leans pass 231, fail 227). Confidence: A high 298, medium 127, low 33; B high
  302, medium 86, low 70.

6.5 Results (2026-11-10 07:18 UTC, `audit/scripts/analyze_review.py` as written before the
review, 10,000 bootstrap draws within strata, seed 20261110; output `audit/work/analyze_review.log`
and `audit/work/review_summary.json`). The population is 5,452 verdicts; stratum weights
S1a 4.59%, S1b 3.30%, S2 0.06%, S3 92.06%.

- Agreement: the leans agree on 444 of 458 cases (96.9%); Cohen's kappa on the leans 0.939.
  `ambiguous` from A 54, from B 71, from either 88 of 458 (19.2%).
- Weighted error rate against the consensus (444 cases), with 95% intervals:

  | Grader | Error rate | 95% interval |
  |---|---|---|
  | grader strict | 7.22% | 5.87% to 9.15% |
  | grader loose | 7.77% | 5.44% to 10.70% |
  | reference strict | 6.97% | 5.62% to 8.89% |
  | reference loose | 7.55% | 5.22% to 10.47% |
  | replacement | 3.02% | 1.68% to 4.93% |

  Paired difference, grader strict minus replacement: +4.20 points (95% interval +3.47 to +4.91).
- Over the 370 cases where both verdicts are definite and agree: grader strict 6.94% (6.01% to
  8.45%), grader loose 7.45%, reference strict 6.75%, reference loose 7.32%, replacement 2.15%
  (1.24% to 3.63%); paired difference +4.79 points (+3.93 to +5.62).
- Per stratum (errors / consensus cases): S1a grader 100/161, reference 93/161, replacement
  61/161; S1b grader 120/124, reference 116/124, replacement 4/124; S2 grader 0/3, reference 3/3,
  replacement 0/3; S3 grader, reference and replacement 2/156 each (the same two cases).
- Disputed cases (leans differ): 14, listed in `audit/work/review_summary.json` under
  `disputed` and in `audit/AUDIT.md`; not resolved by the audit.
- Against the rule recorded above: not admit (7.22% > 2%, upper bound 9.15% > 3%); not replace
  the benchmark (kappa 0.939 >= 0.40, ambiguous 19.2% <= 25%); so fix the grader. The
  replacement passes 277 of 277 fixtures, has complete scored coverage, and its error rate is
  lower with a paired interval that excludes zero, so it is proposed as the fix.
- Computed after the labels were read (`audit/scripts/analyze_review_post.py`, output
  `audit/work/analyze_review_post.log`, `audit/work/review_post.json`): grader strict minus
  reference strict +0.25 points (+0.08 to +0.44); grader strict minus grader loose -0.55 points
  (-3.36 to +1.86); the grader's 7.22% splits into false passes 3.44% and false fails 3.79%; the
  52 held-out extraction-failure verdicts excluded from the population get 15 grader passes, all
  errors under G1; the two S3 cases that all three graders get wrong are R1-bd01c
  (custom:date_format_list, graders pass, consensus fail) and R1-cab3d (format:emoji, graders
  fail, consensus pass).

## Findings

| Id | Check or stage | Summary | Evidence |
|---|---|---|---|
| F-pin-1 | grader provenance | The case records no Marin or Evalchemy commit for the vendored grader; only file hashes pin it. | `case/TASK.md`; verify with `git -C <marin> log -1 --format=%H -- <vendored IFBench path>` |
| F-pin-2 | generation settings | Stop sequences are not recorded for any configuration, and the vLLM version is not recorded for the two thinking configurations. | `case/panel/CONFIGS.md` |
| F-pin-3 | grader dependencies | At import the grader downloads any missing NLTK package (latest version, from the network) into a folder it creates next to its own code; the NLTK data it grades with is therefore pinned only when the caller provides it. | `instructions.py` lines 25-32, `instructions_util.py` lines 1551-1571 |
| F-pin-4 | dataset | `eval_instruct.py` loads `allenai/IFBench_test` without a revision, so a dataset update changes prompts and kwargs silently. | `eval_instruct.py` `load_questions` |

Checker findings from step 3 (verdict wrong under every reading the text allows). Fixture ids
are in `audit/tests/fixtures_data.py`; "Ref" gives the reference's status at 1c40f0c. The panel
bound on the verdicts each finding affects (`audit/scripts/finding_bounds.py`) and every
counterexample with its reproducing command (`audit/scripts/repro.py <finding id>`) are in
`audit/AUDIT.md`, sections 5 and Appendix A.

| Id | Check | Defect | Fixture | Ref |
|---|---|---|---|---|
| F-conj-surface-forms | count:conjunctions | Distinct conjunctions are counted by raw token, so "and", "And" and "and," are three different conjunctions. | count:conjunctions-81617dea | same |
| F-numbers-joined | count:numbers | Punctuation is deleted before counting digit runs, so numbers joined by "-", "/" or ":" ("9-11") count as one. | count:numbers-18e30b2e | same |
| F-pronouns-determiners | count:pronouns | this, that, these, those, all, some, any, each, both count as pronouns when they are determiners. | count:pronouns-776a2e0f | same |
| F-punct-six-marks | count:punctuation | Only . , ? ! ; : and the interrobang are required; apostrophe, quotation marks, hyphen or dash, parentheses are not. | count:punctuation-601839ea | same |
| F-wordcount-contractions | count:word_count_range | Words are `\w+` runs, so every contraction (and decimal) counts as two words. | count:word_count_range-1cde9d43 | same |
| F-japanese-skip-tokens | count:words_japanese | Punctuation-only tokens count toward positions but are exempt when they land on an Nth position. | count:words_japanese-b951151d | same |
| F-charrev-substring | custom:character_reverse | Any response containing "elgae dlab" passes, including a normal-order answer with a reversed copy. | custom:character_reverse-20633f9c | same |
| F-wordrev-mixed | custom:word_reverse | A normal-order answer followed by a reversed copy passes (only "bald eagle" in the reversed text is checked). | custom:word_reverse-babe3eb6 | same |
| F-csvspecial-early-return | custom:csv_special_character | The row loop returns at the first quoted special field, so later rows are never checked for 5 fields. | custom:csv_special_character-5af2501d | same |
| F-dates-invalid | custom:date_format_list | Month 00 and day 00 are accepted. | custom:date_format_list-8e75a21f | same |
| F-capitals-kyiv | custom:european_capitals_sort | The expected list omits Kyiv (50.45 N), so the complete answer fails and the answer without Kyiv passes. | custom:european_capitals_sort-75101278 | same |
| F-mcq-label-number | custom:mcq_count_length | Questions are split on "Question <digit>", so the label "Question:" fails. | custom:mcq_count_length-05811cfb | same |
| F-africa-numbering | custom:reverse_newline | List numbers stay in the sorted strings, so a numbered list in correct order fails. | custom:reverse_newline-a8b76fa4 | same |
| F-alphabet-story-quote | custom:sentence_alphabet | The first character, not the first letter, is compared, so a sentence opening with a quotation mark fails. | custom:sentence_alphabet-bfdf2432 | fixed |
| F-indent-tabs | format:line_indent | Only spaces count as indentation; tab-indented stairs fail. | format:line_indent-66b6dfe6 | same |
| F-list-anywhere | format:list | Two occurrences of the separator anywhere pass; with "-" two hyphenated words pass without a list. | format:list-ba07ac37 | same |
| F-newline-blank-offset | format:newline | Space-only lines count as lines, offsetting lines with two words. | format:newline-70967df1 | same |
| F-nbb-blank-line | format:no_bullets_bullets | Any blank line after the first bullet fails the response. | format:no_bullets_bullets-f3697474 | same |
| F-nbb-period | format:no_bullets_bullets | The sentences before the bullets need not end in a period. | format:no_bullets_bullets-371f2417 | same |
| F-nbb-trailing-text | format:no_bullets_bullets | Any text after the bullets fails the response. | format:no_bullets_bullets-1e4e8bf9 | same |
| F-options-case | format:options | The a)-d) options need an exact, case-sensitive match ("D)" fails). | format:options-e705e191 | same |
| F-options-whitespace | format:options | A trailing newline, or line breaks between the words of an option, fail it. | format:options-db41d773 (+2) | same |
| F-template-presence-only | format:output_template | Only the presence of the three labels is checked: order, placeholders and content are not. | format:output_template-c1479850 (+1) | same |
| F-quote-curly | format:quote_unquote | Curly quotes are never examined (the intended replacement is a no-op), so a curly-quoted phrase may end the response. | format:quote_unquote-09271858 | same |
| F-quotes-apostrophe | format:quotes | Apostrophes are taken as quote marks, so two quoted contractions make "3 levels". | format:quotes-986acc3a | same |
| F-quotes-curly | format:quotes | Curly quotes are ignored, so a correct three-level nest written with them fails. | format:quotes-ba7df411 | same |
| F-subbullets-none | format:sub-bullets | A response without any `*` passes. | format:sub-bullets-68bc3978 | same |
| F-subbullets-any-hyphen | format:sub-bullets | Any hyphen after a `*` counts as a sub-bullet. | format:sub-bullets-eac31626 | same |
| F-subbullets-bold | format:sub-bullets | Bold markup (`**`) makes empty segments, so any bold text fails. | format:sub-bullets-e7564723 | same |
| F-thesis-anywhere | format:thesis | One italic span anywhere passes; nothing checks that sections begin with it. | format:thesis-0be7ab4a | same |
| F-title-contraction | format:title_case | The tokenizer splits "Don't" into "Do" + "n't", and "n't" fails as a lower-case word. | format:title_case-66236ed6 | same |
| F-ratio-quote-endings | ratio:sentence_balance, ratio:sentence_type | Sentences ending in a closing quote get no type, so 0:0 counts as balanced or 2:1. | ratio:sentence_balance-06d14a8d, ratio:sentence_type-7d8c6c99 | same |
| F-sentwords-no-word-check | ratio:sentence_words | "Using all different words" is not checked. | ratio:sentence_words-65a6de4b | fixed |
| F-stopwords-contractions | ratio:stop_words | `\w+` splits contractions into stop-word fragments ("doesn", "t"). | ratio:stop_words-796f0c51 | same |
| F-repeatchange-whitespace | repeat:repeat_change | An unchanged repetition passes when its whitespace differs from the request (a trailing newline). | repeat:repeat_change-14044665 | same |
| F-span-characters | repeat:repeat_span | The expected span is cut by character indices, while the prompt says word indices. | repeat:repeat_span-f5668efe (+2) | fixed |
| F-alliteration-sum | sentence:alliteration_increment | All alliterative words of a sentence are summed instead of taking the longest run. | sentence:alliteration_increment-f060bd4c | same |
| F-position-contractions | words:keywords_specific_position | The tokenizer splits contractions, shifting word positions. | words:keywords_specific_position-5d6232b7 | same |
| F-lastfirst-quotes | words:last_first | A closing quote stays on the last word. | words:last_first-b94487b1 | same |
| F-noconsec-digits | words:no_consecutive | Adjacent numbers starting with the same digit fail. | words:no_consecutive-3f7dfb90 | same |
| F-paralastfirst-comma | words:paragraph_last_first | Punctuation after the first word breaks the comparison. | words:paragraph_last_first-9ba4900d | same |
| F-startverb-tagger | words:start_verb | The NLTK tagger reads sentence-initial imperatives (Imagine, Build, Explore) as nouns or prepositions. | words:start_verb-4239f418 (+2) | same |
| F-startverb-markup | words:start_verb | Markup before the first word ("**Imagine**") is tagged instead of the word. | words:start_verb-f0af03a0 | same |
| F-wordspos-comma | words:words_position | Punctuation tokens count as words except one at the very end. | words:words_position-bd6267af | fixed |
| F-indent-blank-lines | format:line_indent | One blank line between stairs is ignored, two consecutive blank lines fail the response (list mutated while iterated). | test_properties.py::indent-second-blank-line | same |
| F-csvquotes-indexerror | custom:csv_quotes | An empty field in a response with the header, 3 data rows and 5 fields per row raises IndexError, which stops the per-prompt function. | step 4 targeted input (`repro.py F-csvquotes-indexerror`) | same |
| F-loose-deletes-constrained | loose transform (all checks) | Loose grading passes responses by deleting the first or last line or every `*`, text the instructions constrain. | test_properties.py::loose-* | same |
| F-extract-unclosed | response extraction | A thinking-on completion that never closes `<think>` is stored (and graded) as its whole reasoning; the grader passes 45 of those 157 verdicts. | 136 stored responses (`audit/work/panel_scan.csv`) | n/a (pipeline) |

Found after the review labels were read (2026-11-10, 07:31 to 07:43 UTC), while explaining review
case R1-cab3d and the panel disagreements that no decision reading explains. Fixtures in
`audit/tests/fixtures_post_label.py` (run by `test_post_label.py`), not counted among the 277
step 3 fixtures that the pre-registered rule refers to.

| Id | Check | Defect | Fixture | Ref |
|---|---|---|---|---|
| F-sentence-html-tags | sentence-based checks | A period followed by an HTML closing tag does not end a sentence (NLTK splitter); a merged single sentence passes sentence:increment under D-vacuous B. Tag removal changes 26 of 1,820 sentence:increment panel verdicts. | sentence:increment-42d871c8 | same |
| F-wordcount-html-tags | count:word_count_range | `\w+` counts HTML tag names as words; tag removal changes 2 of 2,508 panel verdicts. | count:word_count_range-cc95e9c6 | same |
| F-emoji-flag | format:emoji | A flag emoji (two regional-indicator characters) is not an emoji to `emoji.is_emoji` on single characters; replacing flags changes 27 of 2,049 panel verdicts. Explains review case R1-cab3d. | format:emoji-12dd4be2 | same |
| F-quote-separator | format:quote_unquote | Only adjacency of quotation marks and a final quote are checked, so any symbol between two quoted phrases counts as an explanation; bound 83 of 1,140 panel verdicts. | format:quote_unquote-9b7688e5 | same |

Replacement error found after the labels: REPL-emoji-flag (the replacement also rejects flag emoji;
35 of its panel verdicts change when flags are replaced). The replacement is not changed in this
round; the fix needs a new review round on held-out responses that round 1 did not use.

## Frozen artifacts

| File | sha256 | Written |
|---|---|---|
| `audit/frozen/dataset_row_hashes.tsv` | dead3343c495ada3bba42201f71851f9ec69d5c8ffbd5233e29b323460fe7ad7 | 2026-11-09 22:29 UTC (supersedes b7e4d7df…8b56 of 22:05, see Step 1) |
| `audit/frozen/CONTRACT_v1.md` | b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95 | 2026-11-09 22:16 UTC |
| `audit/frozen/CONTRACT_v2.md` | 5175ec90cbced57cadf39c59e9976731a73ef803e231b06f56df5adc0b0bb813 | 2026-11-09 22:43 UTC |
| `audit/frozen/review_round1/cases.jsonl` (review case list) | f360e3596f16f22c7c53fb117d6096b9784c4849f8406f4ef3a6292c8ad24f4d | 2026-11-09 23:47 UTC |
| `audit/frozen/review_round1/MANIFEST.sha256` (whole review folder) | 5ec4828648954952a495b4b2eeadd015c70627c509f0539d9b44662201a30f3c | 2026-11-09 23:48 UTC |
| `audit/frozen/heldout_runs.tsv` | f0b61346260e4a08563f02478830864589ae528b267d8b463ade7c9bb175f848 | 2026-11-09 22:09 UTC |
| `audit/frozen/reviews/review_A.jsonl` | 5eec6b187962afa8847f9341f55f8bc7ca627c6ee1bdeaa0f1f31e752e2321fc | returned 2026-11-10 00:14 UTC (README) |
| `audit/frozen/reviews/review_B.jsonl` | d809a126270b878b5dd43c07989d9a81b10600ef24b25a702006bf54ea3cb0a3 | returned 2026-11-10 00:20 UTC (README) |
| `audit/frozen/reviews/README.md` | 433496dba916743319b143b91c63575e9d88254e913074fcee5a5ca5432d9a04 | 2026-11-10 (operator) |

## Log

- 2026-11-09 21:55 UTC: audit started; read `case/TASK.md`, `skill/SKILL.md`,
  `skill/references/reviewer-prompt.md`. `skill/references/ifbench.md` and `validation.md` are
  not provided in this run.
- 2026-11-09 22:10 UTC: step 1 record-level pins written; held-out runs chosen.
- 2026-11-09 22:16 UTC: contract v1 hashed and recorded; grader code not yet opened.
- 2026-11-09 22:30 UTC: read the grader and the reference code (diff: the reference commit fixes 7 checkers); code-level pins recorded.
- 2026-11-09 22:43 UTC: contract version 2 (two readings added, reasons above).
- 2026-11-09 22:47 UTC: step 3 done, 277 fixtures; findings table added.
- 2026-11-09 23:30 UTC: step 4 done (reference tests against the replacement, fuzzing, content-free, metamorphic, loose).
- 2026-11-09 23:45 UTC: step 5 panel graded and analyzed.
- 2026-11-09 23:48 UTC: step 6.1-6.3: review sample drawn, frozen and rendered; stopped for the reviewers.
- 2026-11-10 07:15 UTC: audit resumed in a new session; both label files present (458 lines each).
- 2026-11-10 07:17 UTC: step 6.4 label files checked; frozen hashes verified unchanged.
- 2026-11-10 07:18 UTC: step 6.5 pre-registered analysis run; post-label analysis added (marked as such).
- 2026-11-10 07:20 UTC: tests rerun: 676 passed, 173 xfailed (grader 84, reference 75, properties 14); replacement 277 of 277.
- 2026-11-10 07:31 UTC: step 7 report `audit/AUDIT.md` written (recommendation: fix the grader, with the replacement as the fix); `audit/scripts/repro.py` reproduces every finding.
- 2026-11-10 07:43 UTC: post-label analysis: disagreements regraded with every decision reading (`regrade_disagreements.py`), edit-based shares for ten findings (`metamorphic_shares.py`), tag and flag tests (`metamorphic_post.py`); four findings and one replacement error added (above); AUDIT.md sections 5 and 8 updated.
- 2026-11-10 07:51 UTC: `audit/scripts/verify_all.sh` reran every report command (outputs in `audit/work/verify/`): pins match; pytest 679 passed, 182 xfailed; every analysis output equals its quoted log; all 56 Appendix A commands print exactly what the report shows; frozen files unchanged.
