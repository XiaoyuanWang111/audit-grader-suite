# Audit of the IFBench grader in Marin's evaluation policy

Grader: Marin's vendored copy of Evalchemy's IFBench (`case/grader/IFBench/`), 58
instruction checkers, strict and loose harness. Audited 2026-11-11 (UTC) with the
`audit-grader` skill, offline. Record of the audit (pins, contract hashes, decisions,
progress): `audit/ISSUE.md`. Contracts: `audit/CONTRACTS.md` (v4).

## 1. Result

**Error rate: not estimated.** Step 6 (blinded review) was not run in this exercise, so
neither the grader's nor the replacement's error rate has an estimate or an interval.
What the stored panel measures instead:

- **Disagreement with the contracts.** On the 78,432 instruction verdicts of the panel
  (68,400 stored responses, 16 configurations, 228 runs), the grader and the replacement
  grader built from the contracts disagree on **6,506 (8.3%)**. On the held-out runs
  (`greedy_repeat` of every configuration, 5,504 verdicts, never inspected while the
  replacement was built) they disagree on **482 (8.8%)**. 3,916 of the grader's 21,708
  passes (18.0%) are fails under the contracts; 2,590 grader fails are passes.
- **Effect on scores.** Strict prompt-level accuracy (Marin's primary metric,
  `strict_prompt_accuracy`) changes by **-3.94 to +3.22 points per configuration**
  (table in section 4). For 15 of 16 configurations the paired interval over runs
  excludes zero, and for 12 of 16 the change is larger than every rerun difference of
  that configuration (greedy vs `greedy_repeat`, `greedy_shuffled`, `bi_greedy`: at most
  1.7 points). 8 of the 120 configuration pairs change order (Kendall tau 0.87);
  marin-8b-instruct moves from 17.4 to 16.7 and falls below Mistral-7B-Instruct-v0.3.
- **Findings: 35** (3 unpinned inputs, 30 checker or harness defects, 1 extraction
  defect, 1 score-level transform defect). **Decision entries: 66**, listed in section 6
  for the evaluation's maintainers. Of the 81 fixtures the grader gets wrong, 55 are
  findings and 26 are decisions.
- **Scored coverage** on the panel is 100% for the grader, the reference and the
  replacement. One fixture raises `IndexError` in the grader and the reference (F-11);
  neither harness catches checker exceptions.
- **Reference implementation** (allenai/IFBench at 1c40f0c): it disagrees with the grader
  on 257 panel verdicts (0.33%). It contains fixes for 5 of the 30 checker findings (F-05,
  F-26, F-28, F-32, F-34) and uses word trigrams for ratio:overlap; it shares the other 25.
- **Extraction.** 136 thinking-mode responses never close their reasoning. Under the
  panel's stored extraction rule they are graded as answers, and the grader passes 45 of
  their 157 checks (F-35). Marin's own extraction code is not in the case (unverified).

**Recommendation: fix the grader**, by replacing the 58 checkers with an implementation of
the contracts (the replacement in `audit/replacement/`, after the maintainers settle the
decision entries), not by syncing to upstream, which fixes 5 of the 30 checker findings.
This recommendation is provisional: it needs step 6 (section 7) to show that the
replacement's error rate is lower than the grader's with a paired interval that excludes
zero. Admitting the grader is ruled out by findings that each move more than 10% of a
check's verdicts after the decision entries are accounted for (F-04, F-08, F-13, F-17,
F-23, F-24, F-29, F-34), with F-07, F-21 and F-31 above 10% as well but pending step 6.
Replacing the benchmark is not indicated: every finding is a code or configuration
defect, and the prompts are usable once the decision entries are settled.

## 2. What was run

| Step | Status |
|---|---|
| 1 Pin inputs | Done. Manifest verified (424 files), one hash per dataset row, panel records summarized. Unverifiable offline items listed in section 3. |
| 2 Contracts | Done before any grader or reference code was read (v1 at 2026-11-11 00:07 UTC, sha256 `5419289271db...`). Later versions v2-v4 add decision entries, each with its reason (CONTRACTS.md change log). |
| 3 Fixtures | 354 fixtures over all 58 checks (`audit/tests/fixtures.py`); grader: 273 right, 81 wrong, marked `xfail(strict=True)`; replacement: 354 right. |
| 3 Replacement | `audit/replacement/ifb_replacement.py`, one switch per decision entry; frozen for step 5 (sha256 `8de19f99b9ee...`). |
| 4 Reference, stress | Reference's unit tests run against the replacement; 1,376 metamorphic edits; 20,640 fuzz strings; content-free responses; loose transform. |
| 5 Panel | All 68,400 stored responses graded by grader (strict, loose), reference (strict, loose) and replacement. No new responses were generated (no compute in this exercise). |
| 6 Blinded review | **Not run** (no reviewers in this exercise). See section 7. |

The reference's whole pipeline (`run_eval.py`: reading, strict, loose, aggregation) was
also run on three stored runs (`$PY audit/scripts/s4_reference_pipeline.py`); its strict
and loose prompt-level accuracies equal the step-5 per-response reference verdicts
exactly. It needs `PYTHONUTF8=1` on Windows because it opens files with the locale
encoding. Marin's harness (`eval_instruct.py`) cannot run here: the Evalchemy modules it
imports are not in the case, so the grader was run through `grader.py`'s strict and loose
functions, which `eval_instruct.py` reaches through code that is not available.

Skipped because this exercise has no repository, branch, dataset hub or job launcher:
opening an issue (`audit/ISSUE.md` stands in), landing fixture tests and fixes through
`manage-pr`, a research branch, a pinned Hugging Face dataset for frozen samples, and
launching generation through `use-iris`.

All commands below run from `<W>` in Git Bash, with this
prefix (written `$PY` below):

    PYTHONDONTWRITEBYTECODE=1 NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe

The grader and the reference are imported from verbatim copies under `audit/work/pkgs/`
(`$PY audit/scripts/s3_copy_pkgs.py` checks them against the manifest), because importing
the originals writes `.nltk_data/` and `__pycache__/` into `case/`.

## 3. Pinned inputs

- Grader: `case/grader/IFBench/*.py`, pinned by `case/MANIFEST.sha256` only.
- Reference: `case/reference/IFBench/`, stated as allenai/IFBench at
  1c40f0c10d9b5c5c2f10a175a28007ebb64f7f4d.
- Dataset: `case/data/train-00000-of-00001.parquet` (sha256 `80037e4d...`), stated as
  allenai/IFBench_test revision 2e8a48de; per-row hashes in
  `audit/frozen/dataset_row_hashes.tsv` (sha256 `541e4920...`). 300 prompts, 344
  instruction instances, 58 checks. Index kwargs (`m`, `n`, `n_start`, `n_end`) are int64,
  counts are double.
- Prompt rendering: one user turn, model chat template; Qwen3 `enable_thinking` on/off.
- Graded text in the panel: text after the last `</think>`, or the whole completion.
- Generation: max new tokens 1,024 (8,192 thinking), vLLM 0.30.0 (not recorded for the two
  thinking configurations), greedy and temperature-0.7 sampling. Marin's harness asks for
  `temperature 0, max_gen_toks 1024`.
- Dependencies: `case/deps/requirements.lock.txt` (nltk 3.10.0, emoji 2.15.0, syllapy
  0.8.0, ...), NLTK data `case/deps/nltk_data`.

Unverified (location and the command that would verify it):

- Grader provenance: which Evalchemy commit the vendored copy came from. `git -C <marin> log -1 -- <vendored path>` and a diff against Evalchemy at that commit.
- Reference commit: no `.git` in the case. `git clone https://github.com/allenai/IFBench && git -C IFBench checkout 1c40f0c && diff -r IFBench case/reference/IFBench`.
- Dataset revision: `huggingface-cli download allenai/IFBench_test --repo-type dataset --revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2` and compare sha256.
- Marin's extraction rule and exception handling: `eval.sources.common.text_specs`, `eval.contracts.eval_spec` and the "instructions" grader, not in the case. `grep -rn "def text_specs" <marin checkout>`.
- The evaluation environment's package versions (emoji, nltk, syllapy and NLTK data change verdicts): Marin's lockfile at the evaluation commit.

## 4. Effect on scores

Strict prompt-level accuracy (%), mean over each configuration's runs. "Change" is
replacement minus grader, with a 95% interval from the per-run paired changes (it reflects
decoding variation only; all runs share the same 300 prompts). "Rerun" columns: grader
score of `greedy_repeat`, `greedy_shuffled`, `bi_greedy` minus `greedy`. From
`audit/work/panel_tables_all.md` and `audit/work/config_deltas.json`.

| Configuration | Runs | Grader | Replacement | Change [95% CI] | Reference | Grader loose | Rerun diffs |
|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.1 | 30.1 | -3.94 [-4.47, -3.41] | 34.1 | 37.8 | -1.0 / -0.3 / -0.7 |
| Qwen2.5-32B-Instruct | 13 | 35.2 | 33.5 | -1.69 [-2.43, -0.95] | 35.2 | 38.3 | -1.3 / -0.3 / -1.0 |
| Qwen2.5-7B-Instruct | 17 | 27.4 | 25.0 | -2.37 [-3.03, -1.72] | 27.5 | 30.4 | -0.3 / +0.3 / -0.3 |
| Qwen3-14B | 17 | 27.7 | 27.8 | +0.04 [-0.47, +0.55] | 27.8 | 31.3 | -0.3 / +0.3 / -1.3 |
| Qwen3-14B thinking | 3 | 34.3 | 37.6 | +3.22 [+3.00, +3.44] | 34.7 | 39.3 | +1.0 / +0.0 / - |
| Qwen3-32B | 13 | 25.1 | 25.8 | +0.67 [+0.01, +1.33] | 25.2 | 29.4 | -0.7 / -1.7 / +0.3 |
| Qwen3-8B | 17 | 25.2 | 23.7 | -1.45 [-1.81, -1.09] | 25.1 | 29.5 | +0.0 / +0.3 / -1.0 |
| Qwen3-8B thinking | 3 | 32.4 | 30.1 | -2.33 [-2.71, -1.96] | 32.4 | 36.3 | +0.0 / +0.3 / - |
| Llama-3.1-Tulu-3-8B | 17 | 22.7 | 23.4 | +0.76 [+0.25, +1.28] | 22.7 | 26.3 | +0.3 / +1.0 / +1.3 |
| OLMo-2-0325-32B-Instruct | 13 | 33.3 | 30.6 | -2.67 [-3.21, -2.13] | 33.3 | 37.0 | +0.0 / -1.0 / -1.3 |
| OLMo-2-1124-13B-Instruct | 17 | 22.6 | 18.8 | -3.86 [-4.30, -3.42] | 22.7 | 26.8 | +0.0 / +0.0 / +1.0 |
| OLMo-2-1124-7B-Instruct | 17 | 20.4 | 18.3 | -2.12 [-2.60, -1.63] | 20.4 | 24.9 | +0.7 / +0.7 / +1.0 |
| marin-8b-instruct | 17 | 17.4 | 16.7 | -0.69 [-1.22, -0.15] | 17.4 | 21.5 | -1.0 / -0.3 / +0.3 |
| phi-4 | 17 | 19.1 | 20.3 | +1.22 [+0.68, +1.75] | 19.3 | 24.3 | +0.0 / +0.0 / +0.0 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.6 | 16.3 | -1.33 [-1.75, -0.92] | 17.6 | 20.8 | +0.3 / +1.3 / +0.3 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.8 | 23.3 | +1.44 [+0.81, +2.06] | 22.3 | 27.9 | -0.3 / +0.0 / +1.3 |

Configuration pairs that change order (grader gap, replacement gap, points):
Qwen2.5-14B vs OLMo-2-0325-32B (+0.8, -0.5); Qwen2.5-32B vs Qwen3-14B thinking (+0.8,
-4.1); Qwen2.5-7B vs Qwen3-32B (+2.3, -0.7); Qwen3-32B vs Qwen3-8B (-0.1, +2.0);
OLMo-2-13B vs phi-4 (+3.6, -1.5); OLMo-2-13B vs Mistral-Small-24B (+0.8, -4.5); OLMo-2-7B
vs phi-4 (+1.3, -2.0); marin-8b vs Mistral-7B (-0.2, +0.4).

How much of the change the decision entries could move: each decision entry's switch,
flipped alone, changes a configuration's mean score by at most 0.69 points on average
(D-sentence; section 6). With every decision set to the reading closest to the grader's
behavior, 4,726 of the 6,506 disagreements remain (`audit/work/switch_effects.json`); the
replacement's alternative readings only approximate the grader's code, so this is an
estimate, not a split.

## 5. Findings

Shares are measured on the panel (78,432 verdicts) unless the finding is shown only by a
fixture. "Repro" commands print the exact input, the grader's strict and loose verdicts,
the reference's verdicts and the replacement's verdict. Fixture ids are stable
(`audit/tests/fixtures.py`).

### Unpinned inputs

| Id | Stage | Evidence | Contract / rule broken | Status in reference |
|---|---|---|---|---|
| F-01 | dataset loading | `eval_instruct.py` line 61: `load_dataset("allenai/IFBench_test", split="train")` with no `revision=` | every input that changes a verdict must be pinned; a new dataset revision changes scores silently | reference reads its own bundled `data/IFBench_test.jsonl` (pinned by its commit) |
| F-02 | grader dependencies | `instructions_util.py` lines 1551-1571 download punkt, punkt_tab, stopwords and the tagger from the network at import when missing; `instructions.py` lines 26-28 create `<package>/.nltk_data` | NLTK data changes sentence splits, stop words and verb tags; the grader does not pin it | same code in the reference |
| F-03 | grader provenance | the vendored copy records no source commit; it differs from the reference at 1c40f0c in 7 places, all of them fixes present upstream (`audit/work/instructions_ref_vs_grader.diff`) | the grader commit must be recorded | n/a |

### Checker and harness defects

| Id | Check | Fixture or case | Contract broken | Panel share | Reference |
|---|---|---|---|---|---|
| F-04 | count:conjunctions | `count:conjunctions#dcd04ba5` | counts `and`, `And` and `and,` as different conjunctions (set of raw tokens) | 195 of 1,596 verdicts (12.2%) are grader passes the contract fails | same |
| F-05 | count:keywords_multiple | `#e1ec9671`, `#a30082f0` | substring counting: `doorway`, `indoors` count as the keyword `door` | 1 of 1,140 | fixed (whole-word regex) |
| F-06 | count:numbers | `count:numbers#f00b6a23`, `#a5347399` | deletes ASCII punctuation before `\d+`, so `10-20`, `10:30`, `2/3` are one number | at most 5 of 1,824 | same |
| F-07 | count:pronouns | `count:pronouns#2b05f35c` | counts `that`, `all`, `some`, `any`, `each`, `which`, `what` ... in every use, also as determiners and conjunctions | 435 of 1,824 grader passes the contract fails (23.8%); split with D-pronoun-set needs step 6 | same |
| F-08 | count:punctuation | `count:punctuation#b1b8298b`; reference test line 252 | "every standard punctuation mark" checked as only `. , ! ? ; :` plus the interrobang; apostrophes, quotation marks, parentheses, hyphens and dashes are standard under every reading | 267 of 1,368 (19.5%); 191 (14.0%) remain under the narrowest reading of D-punct-set | same (its unit test encodes it) |
| F-09 | word-level checks (unique_word_count, words:alphabet, no_consecutive, prime_lengths, repeats, palindrome, conjunctions, word_count_range, title_case) | `count:unique_word_count#2b002c1c`, `words:alphabet#e46e3fa9`, `words:no_consecutive#a18d9f8b`, `words:prime_lengths#32da9317`, `words:repeats#d2204dd6`; metamorphic `typo_quotes_*`, `html_*` | words are stripped of ASCII punctuation only, so typographic quotes and apostrophes and HTML tags stay part of words (`“The”` is not `the`; `don’t` has 5 letters; `<b>One</b>` adds words `b`); punctuation-only tokens (`-`, `---`) count as words | at most 92 panel verdicts on these checks (an upper bound: unique_word_count 62, no_consecutive 14, alphabet 6, palindrome 6, prime_lengths 2, repeats 2 disagreements); 24 of the 152 metamorphic flips | same |
| F-10 | custom:character_reverse | `custom:character_reverse#1d3496c0` | passes any response containing `elgae dlab`, including a forward sentence | 5 of 228 | same |
| F-11 | custom:csv_quotes | `custom:csv_quotes#fa168408` | raises `IndexError` on an empty field (`field.strip()[0]`); no harness catches it, so the item (or the whole run) fails | 0 on the panel | same |
| F-12 | custom:european_capitals_sort | `custom:european_capitals_sort#35beb628` | the answer key omits Kyiv (50.45 N), so the complete, correctly sorted list fails and only the list without Kyiv passes | 0 on the panel (no model listed all capitals) | same |
| F-13 | custom:mcq_count_length | `custom:mcq_count_length#d79971b5`; case `--panel Qwen__Qwen2.5-7B-Instruct sample7 279` | parses questions only by `Question <number>`: a label without a number fails, and any text after the options (an explanation) is ignored | 36 of 228 (15.8%) grader fails the contract passes | same |
| F-14 | format:emoji | `format:emoji#17317ce5`, `#62a7b39c` | flags (regional-indicator pairs) and keycaps are not recognized as emoji (`emoji.is_emoji` on single code points) | part of the 154 grader fails the contract passes (not separable from F-33) | same |
| F-15 | format:list | `format:list#ceca4d40`, `#40838dbc` | passes when the marker occurs twice anywhere: hyphens inside words for `-`, mixed `*` bullets | 58 of 2,052 (2.8%) | same |
| F-16 | format:newline | `format:newline#9b6ea985` | a whitespace-only line is counted as a line, so a blank line with spaces fails | at most 11 of 1,368 | same |
| F-17 | format:no_bullets_bullets | `format:no_bullets_bullets#7f0516df`, `#97c404e3`, `#029e7b42`; metamorphic `trailing_newline` | does not check that the sentences end in a period; a blank line between sentence lines, a trailing newline, or a line starting with bold `**` makes it fail | 359 of 1,140 (31.5%); at least 257 (22.5%) after D-bullets-after | same |
| F-18 | format:options | `format:options#6d7c8399` | `I don’t know` (typographic apostrophe) is not the option `I don't know` | 0 on the panel | same |
| F-19 | format:output_template | `format:output_template#ad007192`, `#0b09f521`, `#0385cbc5` | only checks that the three labels occur somewhere: text before the template, unfilled `[answer]` placeholders and the wrong order pass; restating the prompt passes | 36 of 912 (3.9%) | same |
| F-21 | format:quotes | `format:quotes#6a418965` | apostrophes are counted as single quotes, so two quoted sentences with contractions reach "3 levels" | 233 of 1,824 (12.8%) grader passes the contract fails (the replacement's apostrophe rule is a heuristic; step 6) | same |
| F-22 | format:quote_unquote | `format:quote_unquote#3e8eecb5` | only rejects two adjacent quotes or a final quote: a comma alone between quoted phrases passes | 59 of 1,140 (5.2%) beyond the 291 grader passes on responses without any quoted phrase (D-vacuous) | same |
| F-23 | format:sub-bullets | `format:sub-bullets#3a8cf170`, `#d319d0a2`; metamorphic `bold_*`; case `--panel microsoft__phi-4 sample9 128` | splits on every `*` and looks for `-` anywhere: no bullet at all passes, a hyphenated word satisfies a bullet, and bold or italic text inside a bullet fails it | 1,113 of 2,736 (40.7%); at least 754 (27.6%) after D-subbullet-indent | same |
| F-24 | format:thesis | `format:thesis#7c919c18` | passes if any `<i>`/`<em>` element anywhere is followed by text; does not check that each section begins with one | 540 of 2,052 (26.3%); at least 253 (12.3%) after D-section | same |
| F-25 | format:title_case | `format:title_case#774b775a`, `#746c2647`, `#6f0636ed` | fails lower-case minor words (`a`, `of`, `the`) although the text asks only for major words, and every contraction (`Don't` tokenizes to `n't`) | 18 of 912 (2.0%) | same |
| F-26 | ratio:sentence_words | `ratio:sentence_words#e678cff6` | does not check "all different words" | 1 of 1,596 | fixed |
| F-27 | repeat:repeat_change | `repeat:repeat_change#6610eec4` | the unchanged request plus a trailing newline passes (string inequality, then whitespace-split comparison) | 0 on the panel | same |
| F-28 | repeat:repeat_span | `repeat:repeat_span#9f2e4789` | uses character indices; the prompt says word indices, so the only passing answer to key 284 is `lain` | 0 on the panel (no response passes either way) | fixed |
| F-29 | sentence:alliteration_increment | `sentence:alliteration_increment#148924a2` | sums every alliterative run in a sentence instead of taking the longest sequence | 121 of 1,140 (10.6%) | same |
| F-30 | words:paragraph_last_first | `words:paragraph_last_first#9640a1cc`; case `--panel Qwen__Qwen3-14B sample0 241` | punctuation after the first word or before the last word stays attached (`indeed,` is not `indeed`) | 29 of 1,368 (2.1%) | same |
| F-31 | words:start_verb | `words:start_verb#b4ab5ac5` (and 7 more imperatives), `#9b0e1f25`; case `--panel microsoft__phi-4 sample1 257` | the POS tagger tags sentence-initial imperatives (`Explore`, `Describe`, `Picture`, `Discover`, `Design`, `Start`, `Show`) as nouns or prepositions, and Markdown or a bullet before the first word fails | 502 of 1,368 (36.7%); the replacement uses a tagger heuristic too, so step 6 must measure it | same |
| F-32 | words:words_position | `words:words_position#88c49983`, `#59af5df2` | punctuation tokens count as words (`Yes,` makes `,` the second word; a closing quote shifts the second-to-last word) | 4 of 684 | fixed |
| F-33 | sentence splitting (emoji, sentence_type, sentence_balance, sentence:keyword, increment, alliteration, last_first, keywords_specific_position) | `ratio:sentence_type#b8f3c20a`, `format:emoji#2e91dae8`; metamorphic `numbered_label` | `nltk.sent_tokenize` makes each numbered-list label (`1.`) a sentence of its own, which shifts sentence positions, adds "declarative sentences", and fails emoji and increment checks | part of the 788 verdicts that D-sentence moves; not separable without step 6 | same |
| F-34 | custom:sentence_alphabet | `custom:sentence_alphabet#0c11d252` | reads the first character of the first token, so a sentence opening with `**` or a quote fails | 28 of 228 (12.3%) | fixed |

F-20 was withdrawn: the nesting depth of unclosed brackets is decision D-paren-closed
(contract v3).

### Extraction and score-level transform

| Id | Stage | Case | Rule broken | Share | Reference |
|---|---|---|---|---|---|
| F-35 | graded-text extraction | `--panel Qwen__Qwen3-14B__thinking greedy 52` (count:unique_word_count passes on unclosed reasoning) | a response whose reasoning never closes is an extraction failure and fails every check; under the stored rule (whole completion when no `</think>`) it is graded as an answer | 136 responses, 157 verdicts, 45 grader passes; whether Marin's harness does the same is unverified | the reference grades whatever response it is given |
| F-36 | loose grading | `--adhoc format:sub-bullets '{}' '* Point one\n* Point two'`; `--adhoc words:start_verb '{}' 'Sure, here is an idea.\nImagine a world without pain.'` | the loose variants delete every `*`, so format:sub-bullets passes every non-empty response (100.0% loose pass rate on the panel), and dropping the first or last line turns contract failures into passes | 3,666 verdicts pass loose but not strict; the contract fails 2,591 of them; Marin reports both loose metrics | same (benchmark's own loose metric) |

### Exact inputs and commands

Each command prints the verdict the table states. Fixture inputs are printed by the
command; the main ones:

| Id | Command | Exact input | Grader says |
|---|---|---|---|
| F-04 | `$PY audit/scripts/repro.py count:conjunctions#dcd04ba5` | `small_n=2`, `'Tea and cake. And milk, and juice.'` | pass (contract: fail) |
| F-05 | `$PY audit/scripts/repro.py count:keywords_multiple#a30082f0` | door/bread/blue/lamp/river, `'The door. Bread, bread. Blue blue blue. Lamp lamp lamp lamp lamp. River river river river river river river. We stayed indoors.'` | fail (pass) |
| F-06 | `$PY audit/scripts/repro.py count:numbers#f00b6a23` | `N=3`, `'Pages 10-20 and 30.'` | fail (pass) |
| F-07 | `$PY audit/scripts/repro.py count:pronouns#2b05f35c` | `N=3`, `'I think that all cats like some milk.'` | pass (fail) |
| F-08 | `$PY audit/scripts/repro.py count:punctuation#b1b8298b` | `'Wait?! Really: yes; ok. Is it? Yes! Done, end.'` | pass (fail) |
| F-09 | `$PY audit/scripts/repro.py words:repeats#d2204dd6` | `small_n=2`, `'“The” cat saw the dog near the tree.'` | pass (fail) |
| F-10 | `$PY audit/scripts/repro.py custom:character_reverse#1d3496c0` | `"The bald eagle, or 'elgae dlab' backwards."` | pass (fail) |
| F-11 | `$PY audit/scripts/repro.py custom:csv_quotes#fa168408` | header row then `"1"\t"Math"\t\t"Fall"\t"95"` and two full rows | EXCEPTION IndexError (fail) |
| F-12 | `$PY audit/scripts/repro.py custom:european_capitals_sort#35beb628` | the 28 capitals above 45 N, Kyiv included, in latitude order | fail (pass) |
| F-13 | `$PY audit/scripts/repro.py custom:mcq_count_length#d79971b5` | 4 valid questions plus `Explanation: Picasso painted Guernica in 1937 after the bombing.` | pass (fail) |
| F-14 | `$PY audit/scripts/repro.py format:emoji#17317ce5` | `'We won 🇺🇸. Great job 🇺🇸.'` | fail (pass) |
| F-15 | `$PY audit/scripts/repro.py format:list#40838dbc` | `sep='-'`, `'This is a well-known, state-of-the-art idea.'` | pass (fail) |
| F-16 | `$PY audit/scripts/repro.py format:newline#9b6ea985` | `'Each\n \nword'` | fail (pass) |
| F-17 | `$PY audit/scripts/repro.py format:no_bullets_bullets#7f0516df` | `'This is the first sentence! This is the second sentence!\n* Point one\n* Point two'` | pass (fail) |
| F-18 | `$PY audit/scripts/repro.py format:options#6d7c8399` | options `I know or I don't know`, `'I don’t know'` | fail (pass) |
| F-19 | `$PY audit/scripts/repro.py format:output_template#0b09f521` | `'My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]'` | pass (fail) |
| F-21 | `$PY audit/scripts/repro.py format:quotes#6a418965` | `'"Don\'t do it," he said. "It\'s fine," she said.'` | pass (fail) |
| F-22 | `$PY audit/scripts/repro.py format:quote_unquote#3e8eecb5` | `'"Carpe diem", "veni vidi vici" are mottos.'` | pass (fail) |
| F-23 | `$PY audit/scripts/repro.py format:sub-bullets#d319d0a2` | `'No bullets here, just a well-known fact.'` | pass (fail) |
| F-24 | `$PY audit/scripts/repro.py format:thesis#7c919c18` | `'Intro paragraph without italics.\n\n<i>Thesis in second section.</i> Body.'` | pass (fail) |
| F-25 | `$PY audit/scripts/repro.py format:title_case#746c2647` | `"Don't Stop The Music"` | fail (pass) |
| F-26 | `$PY audit/scripts/repro.py ratio:sentence_words#e678cff6` | `'Cats nap. Dogs nap. Owls nap.'` | pass (fail) |
| F-27 | `$PY audit/scripts/repro.py repeat:repeat_change#6610eec4` | the request of key 60 unchanged, plus `'\n'` | pass (fail) |
| F-28 | `$PY audit/scripts/repro.py repeat:repeat_span#9f2e4789` | request of key 284, `n_start=3, n_end=6`, response `'lain'` | pass (fail) |
| F-29 | `$PY audit/scripts/repro.py sentence:alliteration_increment#148924a2` | `'Big bears ate apples. Silly snakes slither.'` | fail (pass) |
| F-30 | `$PY audit/scripts/repro.py words:paragraph_last_first#9640a1cc` | `'Indeed, this is true, indeed.'` | fail (pass) |
| F-31 | `$PY audit/scripts/repro.py words:start_verb#b4ab5ac5` | `'Explore the ruins.'` | fail (pass) |
| F-32 | `$PY audit/scripts/repro.py words:words_position#88c49983` | `keyword='despite'`, `'Yes, despite the rain, we went, despite it.'` | fail (pass) |
| F-33 | `$PY audit/scripts/repro.py ratio:sentence_type#b8f3c20a` | `'1. It is sunny.\n2. It is warm.\n3. Is it hot?'` | fail (pass) |
| F-34 | `$PY audit/scripts/repro.py custom:sentence_alphabet#0c11d252` | the 26-sentence A-Z story with `**A**` as the first word | fail (pass) |
| F-35 | `$PY audit/scripts/repro.py --panel Qwen__Qwen3-14B__thinking greedy 52` | stored response with unclosed reasoning (not printed) | pass (fail: extraction failure) |
| F-36 | `$PY audit/scripts/repro.py --adhoc format:sub-bullets '{}' '* Point one\n* Point two'` | two bullets, no sub-bullet | strict fail, loose pass (fail) |

All fixtures together: `$PY -m pytest -q -p no:cacheprovider audit/tests` (628 passed,
81 xfailed: the 81 grader errors, each marked with its finding or decision in
`audit/tests/classification.py`).

### Content-free responses

Graded for all 344 instruction instances with each instance's real kwargs and prompt
(`$PY audit/scripts/s4_fuzz_contentfree.py`, output `audit/work/contentfree.json`). Empty
and whitespace-only responses pass nothing under any grader (harness guard). Checks the
grader passes:

- 60 repetitions of `word` (102 of 344 instances): count:word_count_range,
  format:line_indent, format:quote_unquote, format:sub-bullets, ratio:sentence_balance,
  ratio:sentence_type, ratio:stop_words, sentence:alliteration_increment,
  sentence:increment, words:consonants, words:last_first, words:paragraph_last_first,
  words:vowel. Under the contracts only 5 of these remain (45 instances: word_count_range,
  stop_words, consonants, paragraph_last_first, vowel), each a genuine pass because the
  instruction does not ask for content.
- 20 repetitions of `This is a sentence.` (51): count:pronouns, count:word_count_range,
  format:line_indent, format:quote_unquote, format:sub-bullets, ratio:overlap,
  words:no_consecutive, words:vowel (replacement: 19 instances, 3 checks).
- The prompt itself restated (50): count:conjunctions, count:person_names, count:pronouns,
  count:unique_word_count, format:line_indent, format:list, format:output_template (F-19:
  the template's labels are in the prompt), format:quote_unquote, format:sub-bullets,
  ratio:overlap, ratio:stop_words, sentence:alliteration_increment, sentence:increment,
  words:repeats, words:start_verb (replacement: 20 instances, 10 checks).
- The prompt's last sentence, which restates the instruction (59): count:person_names,
  count:words_japanese, format:line_indent, format:output_template, format:quote_unquote,
  format:sub-bullets, ratio:overlap, ratio:stop_words, repeat:repeat_simple (a genuine
  pass: the instruction sentence is the requested output), sentence:alliteration_increment,
  sentence:increment, words:last_first, words:no_consecutive, words:repeats (replacement:
  19 instances, 9 checks).

## 6. Decision entries

The text allows two verdicts for each entry below; the maintainers choose. "Proposal" is
the contract's reading and the replacement's default. "Panel effect": verdicts that change
when the replacement switches this entry alone to the alternative, and the mean change in
strict prompt accuracy over the 228 runs (points). Examples are fixture ids whose label
depends on the entry.

| Entry | Check(s) | Proposal | Alternative | Example | Panel effect |
|---|---|---|---|---|---|
| D-sentence | all sentence-based checks | sentences end at `. ! ? …` runs and at line breaks; list labels and abbreviations do not end one | only terminal punctuation ends a sentence (lines run together) | `format:emoji#31be7d44` | 788; -0.69 |
| D-vacuous | every "each/every" check, ratios, increment checks | no instance (no quotes, one sentence, zero denominator) fails | vacuous truth passes | `sentence:increment#7d420a76` | 533; +0.58 |
| D-conj-usage | count:conjunctions | every `for/so/yet` counts | only conjunction uses count | `For example, tea and cake.` (N=2) | 439; -0.44 |
| D-list-intro | format:list, custom:reverse_newline | an intro sentence before the list is allowed | the answer is only the list | - | 433; -0.45 |
| D-list-sep | format:list | the marker between items on one line also counts | only at the start of each item line | `format:list` `Apples !?!? Pears !?!? Plums` | 418; -0.39 |
| D-pronoun-set | count:pronouns | personal, possessive, reflexive, reciprocal, -one/-body/-thing | also demonstrative, relative, interrogative pronouns (the replacement counts them always, an upper bound) | `count:pronouns#2b05f35c` | 413; +0.40 |
| D-case | keyword and word matches | case-insensitive | case-sensitive | `count:conjunctions` `AND then BUT also OR.` | 382; -0.13 |
| D-csv-rows | custom:csv_* | N rows are data rows plus the header | N rows include the header | - | 376; -0.55 |
| D-subbullet-indent | format:sub-bullets | the `-` lines need no indentation | sub-bullets must be indented | `format:sub-bullets` `* Point one\n- detail\n* Point two\n- detail` | 359; -0.31 |
| D-palindrome-distinct | words:palindrome | 10 distinct palindromes | 10 occurrences | `words:palindrome#38f080fb`; reference test line 235 | 320; +0.47 |
| D-keyword-count | count:keywords_multiple | exactly once/twice/... | at least | `count:keywords_multiple` door twice | 307; +0.45 |
| D-section | format:thesis | sections are heading blocks, else blank-line paragraphs | a response without headings is one section | `format:thesis#212ce5b0` | 287; +0.30 |
| D-emoji-pos | format:emoji | emoji before or after the terminal punctuation | only after | `I love the sun 🌞. The sea is calm 🌊!` | 267; -0.24 |
| D-paren-closed | format:parentheses | the whole nest must close properly | a group closing at depth 5 suffices | `format:parentheses#3ae933db`; reference test line 275 | 260; +0.35 |
| D-csv-wrapper | custom:csv_* | a code fence is allowed, prose outside it ignored | the whole response is the CSV | `custom:csv_city#8b7fd8ed` | 230; -0.34 |
| D-trigram-def | ratio:overlap | word trigrams, share of the response's trigrams | reference-side share, Jaccard, or character trigrams (the grader) | `ratio:overlap#9983d8e6` | 201 (char); -0.01 |
| D-number-def | count:numbers | digit groups (with internal `.`/`,`) anywhere, number words not | number words count; list labels skipped | `count:numbers` `One, two and three...` | 192; -0.18 |
| D-word | all word checks | runs of letters/digits with internal `'`/`-`; markup and list markers are not words | whitespace tokens with edge punctuation stripped | `red, red. red! blue?` (unique words, N=3) | 124; +0.00 |
| D-options-exact | format:options | the answer is exactly one option | the option may be embedded in a sentence | `I would say no.` | 112; +0.14 |
| D-reverse-content | custom:*_reverse | the reversed text must answer (name the eagle) | form only | `custom:character_reverse` `.nosib ehT` | 110; +0.16 |
| D-bullets-after | format:no_bullets_bullets | text may follow the bullets | nothing after the bullets | - | 102; -0.15 |
| D-paren-mix | format:parentheses | any mix of bracket types | all three types used | `((((( x )))))` | 90; -0.13 |
| D-between | count:word_count_range | inclusive | exclusive | `count:word_count_range` 5 words, range 5-7 | 89; -0.10 |
| D-japanese-segmentation | count:words_japanese | an all-Japanese response passes | whitespace tokens always | `count:words_japanese#77cece42` | 79; -0.12 |
| D-punct-set | count:punctuation | 14 standard marks | without braces, brackets, ellipsis | `count:punctuation#f1ba574d` | 76; +0.11 |
| D-repeat-count | words:repeats | at most N occurrences | at most N repetitions (N+1 occurrences) | `The cat saw the dog.` | 76; +0.11 |
| D-csv-one-field | custom:csv_special_character | at least one quoted special field | exactly one | - | 75; -0.11 |
| D-vowel-reading | words:vowel | at most three vowel letters in the paragraph | exactly three; per word | `I see a red cat.` | 63; -0.08 |
| D-verb | words:start_verb | the first word functions as a verb in context (a gerund subject does not) | any verb form | `Understanding requires care.` | 39; +0.06 |
| D-balanced | ratio:sentence_balance | equal counts | within one | `ratio:sentence_balance` 2/2/1 | 37; +0.04 |
| D-mcq-length | custom:mcq_count_length | stem length in characters | in words; stem plus options | - | 36; -0.04 |
| D-indent | format:line_indent | blank lines ignored, tab = 4 columns | blank lines count as unindented lines | `format:line_indent#8416c808` | 30; -0.04 |
| D-capitals-set | custom:european_capitals_sort | all 28 capitals of European UN states above 45 N | any correctly sorted subset | `custom:european_capitals_sort#fe216477`; reference test line 1007 | 23; +0.03 |
| D-options-label | format:options | `c)` or `c)` plus that option's own text | the label alone | `format:options#9a501bf7` | 20; -0.03 |
| D-typographic | format:quotes, quote_unquote | typographic quotes delimit quotations | only ASCII quotes | `format:quotes#8240a6da` | 16; -0.01 |
| D-strip | all | leading/trailing whitespace ignored | raw text graded | `format:no_whitespace#3b8bd8af` | 15; -0.02 |
| D-newline-punct | format:newline | punctuation-only lines contain no word | they count as words | `Hello\n-\nworld` | 10; -0.00 |
| D-y | words:consonants | `y` is a consonant | `y` is a vowel | `Strong byte.` | 10; -0.01 |
| D-template-markup | format:output_template | line breaks and bold labels allowed | plain labels only | `**My Answer:** ...` | 9; -0.01 |
| D-titlecase-minor | format:title_case | minor words either case | every word capitalized | - | 6; -0.01 |
| D-span-index | repeat:repeat_span | 0-based word indices | 1-based | `repeat:repeat_span#9cafe16f` | 5; +0.01 |
| D-title | custom:sentence_alphabet | an unpunctuated first line is a title, not a sentence | it is a sentence | - | 3; -0.00 |
| D-japanese-digits | count:words_japanese | a numeral is not a Japanese word | it is | `count:words_japanese#8d075f0b` | 2; +0.00 |
| D-keyword-match | count:keywords_multiple | whole word only | inflected forms count | `count:keywords_multiple#6544b7bb` | 1; +0.00 |
| D-name-case | count:person_names | capitalized name | any case | - | 1; +0.00 |
| D-africa-set | custom:reverse_newline | all 54 UN member states, variants accepted | order only | reference test line 942 | 0 |
| D-change-case | repeat:repeat_change | a case-only change is not a change | it is | `repeat:repeat_change#8017d55e` | 0 |
| D-repeat-exact | repeat:* | compare after collapsing whitespace | exact | `repeat:repeat_simple` with quotes | 0 |
| D-csv-header-quoted | custom:csv_quotes | header fields quoted too | data only | `custom:csv_quotes` unquoted header | 0 |
| D-mcq-answer | custom:mcq_count_length | an answer key line is not an explanation | it is | - | 0 |
| D-multiples-prose | custom:multiples | prose without numerals allowed | only the numbers | `Multiples of 7 between 10 and 50: ...` | 0 |
| D-char-count, D-different-words | ratio:sentence_words | every character of the sentence; no word twice in the response | no spaces; no word shared between sentences | - | 0 |
| D-quote-chars | format:quote_unquote | double-quoted phrases only | single-quoted phrases too | - | not measured separately |
| D-ratio-exact | ratio:sentence_type | exactly 2:1 | approximately 2:1 (no tolerance stated) | - | alternative not specified |
| D-reverse-punct | custom:word_reverse | punctuation position and capitals ignored | punctuation must also be reversed | `eagle. bald the is ...` | no alternative implemented |
| D-stopword-list | ratio:stop_words | NLTK English list | another stop-word list | `The cat chased mice.` at 25% | only NLTK's list is available offline |
| D-whitespace-set | format:no_whitespace | U+200B is not whitespace | it is | `Yes\u200bno` | 0 |
| D-japanese-kanji, D-alphabet-start, D-overlap-reference | words_japanese, alphabet, overlap | kanji-only words count; any start letter; reference = kwargs reference_text | no; start at A; prompt minus instructions | - | 0 |
| D-sentence-type, D-alliteration, D-syllable, D-simple-which, D-content-history | sentence_balance/type, alliteration, syllables, repeat_simple, date_format_list | punctuation type; first letter; syllapy counts; the instruction sentence; format only | grammatical type; initial sound; dictionary; the preceding request; historically correct dates | - | alternative needs judgment, not implemented |
| D-loose | score level | strict is the score of record (Marin's primary metric is strict) | loose reported as a score | F-36 | 3,666 loose-only passes |

## 7. Step 6: not run, and what the recommendation still needs from it

Result that would change the recommendation (to be recorded in the issue before any
review): **the replacement passes every fixture (true now), its scored coverage is complete
(true now), and its error rate is lower than the grader's with a paired 95% interval that
excludes zero.** If instead the replacement's interval overlaps the grader's, the
recommendation becomes "fix the grader's specific findings" (F-04 to F-36) rather than
replace the checkers; if both upper bounds are below 2% the grader could be admitted with
the findings filed.

What step 6 must supply:

- A frozen sample drawn with a recorded seed from the held-out responses (or the whole
  panel), stratified by grader-vs-replacement disagreement: all or most of the 482
  held-out disagreements (6,506 on the whole panel) and about 130 agreement cases per
  large stratum for an upper end below 2%.
- Two blinded reviewers per case with `skill/references/reviewer-prompt.md`; consensus by
  lean; per-stratum error rates weighted by stratum size, bootstrap intervals, the
  zero-error adjustment of step 6.5, kappa, and the disputed cases.
- Specific questions only the review can settle: the split of count:pronouns between
  F-07 and D-pronoun-set; the replacement's verb test for words:start_verb (F-31) and its
  apostrophe rule for format:quotes (F-21), both heuristics; sentence segmentation (F-33
  versus D-sentence) on emoji, sentence:keyword and the ratio checks.

## 8. Files

- `audit/ISSUE.md`: progress, pins, contract hashes and times, held-out set, replacement freeze.
- `audit/CONTRACTS.md` (v4) and frozen versions `audit/frozen/CONTRACTS_v1..v4_*.md`.
- `audit/tests/`: `fixtures.py`, `classification.py`, `test_grader_fixtures.py`, `test_replacement_fixtures.py`.
- `audit/replacement/ifb_replacement.py` (frozen copy `audit/frozen/ifb_replacement_frozen.py`).
- `audit/scripts/`: `s1_pin.py`, `s2_dump_texts.py`, `s3_copy_pkgs.py`, `s3_run_fixtures.py`, `s4_reference_tests_vs_replacement.py`, `s4_metamorphic.py`, `s4_fuzz_contentfree.py`, `s5_grade_panel.py`, `s5_analyze.py`, `s5_switch_effects.py`, `s5_inspect.py`, `repro.py`.
- `audit/work/`: panel verdicts (`panel_verdicts/`), `panel_tables_*.md`, `panel_stats_*.json`, `switch_effects.json`, `config_deltas.json`, `metamorphic.json`, `fuzz.json`, `contentfree.json`, `reference_tests_vs_replacement.json`, `fixture_results.json`.
- `audit/frozen/`: `dataset_row_hashes.tsv`, `panel_summary.json`, `heldout_runs.txt`, contract versions, frozen replacement (sha256 in ISSUE.md).

## Appendix A. Pass rate per check on the panel

All 78,432 verdicts (228 runs). Pass rates in %; "G pass / R fail" counts grader passes the replacement fails, "G fail / R pass" the reverse; "G vs ref" counts grader-reference disagreements. Source: `audit/work/panel_stats_all.json` (`$PY audit/scripts/s5_analyze.py`).

| Check | Verdicts | Grader | Replacement | Reference | Grader loose | G pass / R fail | G fail / R pass | G vs ref |
|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1,596 | 64.3 | 52.1 | 64.3 | 64.3 | 195 | 0 | 0 |
| count:keywords_multiple | 1,140 | 0.3 | 0.2 | 0.2 | 0.4 | 1 | 0 | 1 |
| count:numbers | 1,824 | 38.0 | 37.9 | 38.0 | 45.6 | 4 | 1 | 0 |
| count:person_names | 1,368 | 87.2 | 87.2 | 87.2 | 87.2 | 0 | 0 | 0 |
| count:pronouns | 1,824 | 82.0 | 58.3 | 82.0 | 82.0 | 435 | 2 | 0 |
| count:punctuation | 1,368 | 19.5 | 0.0 | 19.5 | 19.5 | 267 | 0 | 0 |
| count:unique_word_count | 2,052 | 79.6 | 76.8 | 79.6 | 79.6 | 60 | 2 | 0 |
| count:word_count_range | 2,508 | 21.7 | 22.6 | 21.7 | 27.9 | 58 | 80 | 0 |
| count:words_japanese | 1,140 | 17.7 | 9.8 | 17.7 | 19.6 | 90 | 0 | 0 |
| custom:character_reverse | 228 | 2.2 | 0.0 | 2.2 | 2.2 | 5 | 0 | 0 |
| custom:csv_city | 228 | 50.4 | 90.4 | 50.4 | 50.4 | 0 | 91 | 0 |
| custom:csv_quotes | 228 | 6.6 | 25.4 | 6.6 | 6.6 | 0 | 43 | 0 |
| custom:csv_special_character | 228 | 7.5 | 49.1 | 7.5 | 13.2 | 1 | 96 | 0 |
| custom:date_format_list | 228 | 68.9 | 68.9 | 68.9 | 68.9 | 0 | 0 | 0 |
| custom:european_capitals_sort | 228 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| custom:mcq_count_length | 228 | 25.0 | 40.8 | 25.0 | 28.9 | 0 | 36 | 0 |
| custom:multiples | 228 | 0.4 | 0.4 | 0.4 | 53.9 | 0 | 0 | 0 |
| custom:reverse_newline | 228 | 3.9 | 1.3 | 3.9 | 3.9 | 6 | 0 | 0 |
| custom:sentence_alphabet | 228 | 21.1 | 33.3 | 31.1 | 30.7 | 0 | 28 | 23 |
| custom:word_reverse | 228 | 7.0 | 13.6 | 7.0 | 7.0 | 8 | 23 | 0 |
| format:emoji | 2,052 | 34.4 | 41.1 | 34.4 | 39.4 | 15 | 154 | 0 |
| format:line_indent | 2,052 | 12.1 | 6.0 | 12.1 | 23.5 | 126 | 1 | 0 |
| format:list | 2,052 | 64.9 | 62.1 | 64.9 | 64.9 | 58 | 0 | 0 |
| format:newline | 1,368 | 34.1 | 34.6 | 34.1 | 41.0 | 4 | 11 | 0 |
| format:no_bullets_bullets | 1,140 | 27.9 | 52.7 | 27.9 | 33.1 | 38 | 321 | 0 |
| format:no_whitespace | 912 | 51.9 | 53.5 | 51.9 | 51.9 | 0 | 15 | 0 |
| format:options | 1,368 | 60.0 | 61.5 | 60.0 | 63.2 | 0 | 20 | 0 |
| format:output_template | 912 | 97.6 | 93.6 | 97.6 | 97.6 | 36 | 0 | 0 |
| format:parentheses | 1,824 | 29.7 | 15.4 | 29.7 | 29.7 | 261 | 0 | 0 |
| format:quote_unquote | 1,140 | 90.4 | 60.0 | 90.4 | 92.5 | 350 | 4 | 0 |
| format:quotes | 1,824 | 23.8 | 14.8 | 23.8 | 24.3 | 233 | 69 | 0 |
| format:sub-bullets | 2,736 | 36.5 | 61.9 | 36.5 | 100.0 | 209 | 904 | 0 |
| format:thesis | 2,052 | 33.1 | 6.8 | 33.1 | 33.1 | 540 | 0 | 0 |
| format:title_case | 912 | 50.7 | 52.6 | 50.7 | 51.3 | 0 | 18 | 0 |
| ratio:overlap | 2,736 | 5.9 | 1.4 | 2.4 | 7.3 | 162 | 39 | 227 |
| ratio:sentence_balance | 1,596 | 3.5 | 3.3 | 3.5 | 8.4 | 12 | 8 | 0 |
| ratio:sentence_type | 1,368 | 4.4 | 4.0 | 4.4 | 9.4 | 17 | 12 | 0 |
| ratio:sentence_words | 1,596 | 0.1 | 0.1 | 0.1 | 0.1 | 1 | 0 | 1 |
| ratio:stop_words | 2,736 | 47.8 | 47.9 | 47.8 | 53.8 | 17 | 18 | 0 |
| repeat:repeat_change | 684 | 6.1 | 6.1 | 6.1 | 7.6 | 0 | 0 | 0 |
| repeat:repeat_simple | 456 | 7.0 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 |
| repeat:repeat_span | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1,140 | 19.0 | 8.9 | 19.0 | 28.3 | 121 | 6 | 0 |
| sentence:increment | 1,824 | 3.1 | 0.1 | 3.1 | 7.2 | 56 | 0 | 0 |
| sentence:keyword | 3,420 | 25.6 | 24.2 | 25.6 | 28.1 | 105 | 56 | 0 |
| words:alphabet | 1,368 | 10.4 | 10.2 | 10.4 | 11.6 | 4 | 2 | 0 |
| words:consonants | 3,420 | 6.0 | 5.7 | 6.0 | 6.1 | 9 | 0 | 0 |
| words:keywords_specific_position | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| words:last_first | 1,140 | 7.0 | 8.1 | 7.0 | 8.1 | 25 | 37 | 0 |
| words:no_consecutive | 1,824 | 4.2 | 3.4 | 4.2 | 6.4 | 14 | 0 | 0 |
| words:odd_even_syllables | 2,052 | 0.8 | 0.8 | 0.8 | 1.0 | 0 | 0 | 0 |
| words:palindrome | 1,596 | 30.3 | 9.9 | 30.3 | 30.3 | 326 | 0 | 0 |
| words:paragraph_last_first | 1,368 | 7.8 | 9.9 | 7.8 | 11.5 | 0 | 29 | 0 |
| words:prime_lengths | 1,140 | 4.6 | 4.6 | 4.6 | 4.6 | 1 | 1 | 0 |
| words:repeats | 1,140 | 17.5 | 17.3 | 17.5 | 18.9 | 2 | 0 | 0 |
| words:start_verb | 1,368 | 39.5 | 70.0 | 39.5 | 45.3 | 43 | 459 | 0 |
| words:vowel | 2,280 | 4.1 | 4.0 | 4.1 | 5.3 | 1 | 0 | 0 |
| words:words_position | 684 | 0.3 | 0.9 | 1.0 | 0.4 | 0 | 4 | 5 |
