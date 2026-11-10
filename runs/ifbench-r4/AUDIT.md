# IFBench grader audit (Marin's vendored Evalchemy copy)

Report of the audit-grader skill, step 7. Written 2026-11-10 06:30 UTC; the record of the run is in `audit/ISSUE.md`.
All commands run from `<W>` with `.venv/Scripts/python.exe -I -X utf8`; NLTK data is pinned to `case/deps/nltk_data` by `audit/lib/ifbaudit.py`.

## Result

**Error rate: not estimated.** Step 6 (the blinded review) was not run in this exercise, so no error-rate interval exists for the grader under audit or for the replacement grader.

**Effect on scores.** On the 68,400 stored responses (16 configurations, 228 runs, 78,432 instruction verdicts), the replacement grader built from the contracts, with every decision left at the grader's current reading, changes **2,805 verdicts (3.6%)**: 2,760 from checker fixes and 45 from responses whose reasoning never closes. Strict prompt-level accuracy, the harness's primary metric, moves from **24.92% to 25.97% (+1.05 points)** pooled. Per configuration the change is **-1.14 to +5.00 points** (mean over each configuration's runs). Six configurations move by more than the largest difference between two identical greedy runs (1.33 points): Mistral-Small-24B +4.05, Qwen3-14B with thinking +5.00, Qwen3-32B +2.79, phi-4 +2.73, Qwen3-14B +1.82, Tulu-3-8B +1.69. 14 of the 16 configurations change rank, each by one or two places. On the held-out files the change is +1.19 points, against +1.04 on the rest.

The replacement's own verdicts are checked only by the 208 fixtures and the reference's unit tests; no reviewer has looked at them. The score changes above measure how much the findings move scores. They are not error rates.

**Reference.** The vendored grader is an older state of the benchmark authors' code. The reference at 1c40f0c fixes 6 of the checker defects found here. Those fixes change strict prompt-level accuracy by at most +0.44 points for any configuration (pooled 24.92% to 25.00%), because the six checks rarely pass. Most findings below are in the reference too.

**Recommendation: fix the grader.** The audit has 43 findings: 37 of the 58 checks have at least one, and the rest are the graded-text extraction, the loose score, a checker exception that stops the run, and two unpinned inputs. Each finding has a small fix, and the replacement grader in `audit/lib/replacement.py` implements all of them. The fix does not yet come with a measured difference in error rate, because step 6 has not run. What step 6 still has to show is under "Step 6" below. Until it has run, report IFBench scores from this grader with the caveats below, and do not rank models that differ by less than about 5 points (the largest per-configuration score change).

## Findings

A finding is a verdict that is wrong under every reading the prompt text allows, a grader exception, or an unpinned input. "Share" is measured on the panel: the share of the check's instruction verdicts where the grader (G) and the replacement (X, decisions at the grader's reading) disagree because of this fix. The replacement's verdicts on the panel have not been reviewed. "Ref." gives the finding's status in the reference implementation (R, allenai/IFBench 1c40f0c).

Each counterexample is the exact response of a fixture in `audit/tests/fixtures.py`, graded with the kwargs shown. The command `audit/repro.py <fixture id>` prints the input and the verdicts of G, R and X. Labels come from `audit/contracts.md` (sha256 fcbfcf62..., hashed before any code was read) and its change log `audit/contracts_changes.md`.

### Pipeline and pinning

| Id | Stage | Counterexample / evidence | Contract broken | Share | Ref. |
|---|---|---|---|---|---|
| F-extract-unclosed | graded-text extraction | 136 Qwen3 thinking completions (Qwen3-8B 104/900, Qwen3-14B 32/900) open `<think>`, never close it, and stop at the 8,192-token limit. The stored `response` is then the whole completion, reasoning included, and the grader grades it. G passes 45 of their 157 instruction verdicts, and all checks of 35 prompts. | G1: reasoning that never closes is an extraction failure and fails every check, counted separately | 157 verdicts; Qwen3-8B thinking 104 responses (11.6%) | R grades whatever text it is given; its generator uses the server's `message.content` |
| F-pin-dataset | input pinning | `eval_instruct.py:61` calls `load_dataset("allenai/IFBench_test", split="train")` and `SourceRef("allenai/IFBench_test", "train")`, with no revision | Step 1: every input that can change a verdict is pinned | all verdicts | R reads a local jsonl |
| F-pin-nltk | input pinning | `instructions_util.py:1551-1571` calls `nltk.download()` at import for punkt, punkt_tab, stopwords and averaged_perceptron_tagger_eng when it cannot find them, with no version. `instructions.py:25-32` puts an empty package-local `.nltk_data` first on the path. Sentence splitting, tokenization, the stop-word list and the POS tagger all come from these files. | Step 1 | the 17 checks that load NLTK data (12 split sentences with punkt, 4 use `word_tokenize` or the tagger, 1 uses the stop-word list) | same code in R |
| F-csv-quotes-exception | checker exception | `custom:csv_quotes-54872d9e`: a tab-delimited table with a header and 3 rows, where one data field is empty and unquoted (`"1"\t\t"A"\t"Fall"\t"91"`). `QuotesCSVChecker` raises `IndexError` (`field.strip()[0]`), and `grader.py` does not catch it, so the exception leaves `test_instruction_following_strict` and stops grading of the run. Test: `test_grader_harness_survives_checker_exception`. | The check returns a verdict (fail: an empty field is not enclosed in quotes) | 0 in the panel; 0 in 412,800 fuzz calls | same code in R |

### Checkers

| Id | Check | Fixture: exact response (kwargs) | Contract | G / R / label | Share (panel) |
|---|---|---|---|---|---|
| F-conj-variants | count:conjunctions | `count:conjunctions-d587c200`: `And and, AND and.` (small_n=2) | distinct conjunctions, case ignored: 1 | pass / pass / fail | 188 of 1,596 (11.8%), all false passes |
| F-keywords-substring | count:keywords_multiple | `count:keywords_multiple-22b2bdee`: the passing text plus ` We sat indoors.`; `-cd1b9464`: "door" occurs only inside "indoor" (keywords door, bread, blue, lamp, river) | whole-word counts; "indoors" is not "door" (C1) | fail / pass / pass and pass / fail / fail | 1 of 1,140 |
| F-numbers-joined | count:numbers | `count:numbers-1e85aac9`: `Read pages 10-20 tonight.` (N=2) | a range holds two numbers | fail / fail / pass | 3 of 1,824 |
| F-word-count-split | count:word_count_range | `count:word_count_range-d0ffdfa2`: `I don't think it's well-known.` (min=max=5) | 5 words under either reading of "word"; `\w+` counts 8 | fail / fail / pass | 135 of 2,508 (5.4%): 57 false passes, 78 false fails |
| F-japanese-skip | count:words_japanese | `count:words_japanese-220af62c`: `Hello - world 日本` (N=2) | the 2nd word ("world", or the token "-") is not Japanese; the grader skips the emptied token but still counts its position | pass / pass / fail | 1 of 1,140 |
| F-charrev-partial | custom:character_reverse | `custom:character_reverse-78bf4bd5`: `The answer is elgae dlab.` | the whole sentence is reversed per letter | pass / pass / fail | 5 of 228 (2.2%) |
| F-capitals-key | custom:european_capitals_sort | `custom:european_capitals_sort-7c1bd6bc`: the grader's 27-capital list with `Kyiv` after `Brussels` (definition `CAPITALS_28`); `-6aea6f9e`: the list without Kyiv | Kyiv (50.45 N) is the capital of a European country north of 45 N under every reading; the answer key omits it | fail / fail / pass and pass / pass / fail | 0 of 228 (no response passes under either key) |
| F-mcq-label | custom:mcq_count_length | `custom:mcq_count_length-7a52df67`: four questions labeled `Question:` without a number, five options each, stems getting longer (definition `MCQ_NOLABELNUM`) | the label "Question" is present | fail / fail / pass | 22 of 228 (9.6%) |
| F-africa-incomplete | custom:reverse_newline | `custom:reverse_newline-a733ec60`: 52 of the 54 countries (Kenya and Ghana removed) in reverse order, one per line (definition `AFRICA_REV_MISSING2`) | the list covers the countries of Africa; the grader checks only order and at least 52 lines from "Zimbabwe" | pass / pass / fail | 6 of 228 (2.6%) |
| F-alphabet-quote | custom:sentence_alphabet | `custom:sentence_alphabet-ca748461`: `SENT26` with the first sentence `"Apples fall," said Ann.` | the first word starts with A; the opening quotation mark is not part of it | fail / **pass** / pass | 23 of 228 (10.1%) |
| F-emoji-sequence | format:emoji | `format:emoji-dbfa7128`: `We love Japan 🇯🇵. It is far 🇯🇵.` | a flag is an emoji; `emoji.is_emoji` is applied to single code points | fail / fail / pass | 28 of 2,052 (1.4%) |
| F-indent-tabs | format:line_indent | `format:line_indent-7ce590ee`: `a\n\tb\n\t\tc` | tab indentation is indentation; only spaces are counted | fail / fail / pass | 2 of 2,052 (both indent findings) |
| F-indent-blank-lines | format:line_indent | `format:line_indent-750deda2`: `a\n\n\n  b\n    c` | blank lines are not lines of the staircase; removing items while iterating leaves one blank line in | fail / fail / pass | (above) |
| F-list-anywhere | format:list | `format:list-caad469d`: `This well-known fact is up-to-date.` (sep="-") | prose with hyphenated words is not a list; the grader counts any two occurrences of the separator | pass / pass / fail | 17 of 2,052 |
| F-nbb-blank-lines | format:no_bullets_bullets | `format:no_bullets_bullets-5e18057a`: `First sentence. Second sentence.\n\n* one\n\n* two` | blank lines are not text after the bullets | fail / fail / pass | 135 of 1,140 (11.8%), false fails |
| F-nbb-period | format:no_bullets_bullets | `format:no_bullets_bullets-fde0a7fb`: `Is this a question? Yes it is!\n* one\n* two` | two sentences ending in a period; the grader counts any two sentences | pass / pass / fail | 37 of 1,140 (3.2%), false passes |
| F-template-check | format:output_template | `format:output_template-3d64d1fa`: `Future Outlook: Z\nMy Conclusion: Y\nMy Answer: X`; `-fe5a21db`: `My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]` | labels in template order with the placeholders filled; the grader checks only that the three labels occur | pass / pass / fail | 0 of 912 (the prompt itself passes: see content-free) |
| F-quote-unquote-curly | format:quote_unquote | `format:quote_unquote-c3a4cc73`: `The motto is “carpe diem”` | a quoted phrase with no explanation after it; `value.replace('"', '"')` is a no-op, so curly quotes are never seen | pass / pass / fail | 1 of 1,140 |
| F-quotes-curly | format:quotes | `format:quotes-07be1176`: `“She said, ‘He told me “go” now’ loudly.”` | three alternating levels; only straight quotes are counted | fail / fail / pass | 29 of 1,824 (1.6%) |
| F-subbullets-check | format:sub-bullets | `format:sub-bullets-0dc9fe92`: `No bullets here at all.`; `-4d5da15b`: `* A well-known item\n* Another up-to-date item`; `-fcb0d05e`: `* **Fruit**:\n  - apple\n* **Veg**:\n  - kale` | at least one `*` bullet and a `-` sub-bullet line under each; the grader splits on every `*` and looks for any `-` | pass / pass / fail, pass / pass / fail, fail / fail / pass | 1,110 of 2,736 (40.6%): 206 false passes, 904 false fails (bold text inside bullets) |
| F-thesis-each | format:thesis | `format:thesis-bfe73c86`: `## Rise\n<i>Rome rose by roads.</i> Roads moved armies.\n\n## Fall\nRome fell by debt. Debt ruined it.`; `-03092647`: `Rome rose by roads. <i>Roads moved armies.</i> Then more came.` | every section begins with the italic thesis; the grader accepts one italic span anywhere | pass / pass / fail | 245 of 2,052 (11.9%) with D-section at its non-proposed reading; 297 more under the proposed one |
| F-titlecase-minor | format:title_case | `format:title_case-00f3eeac`: `The Rise of Rome` | the prompt defines title case as capitalizing every major word, so "of" may be lower case (C2) | fail / fail / pass | 18 of 912 (both title-case findings) |
| F-titlecase-contraction | format:title_case | `format:title_case-45d9ac62`: `Don't Stop Believing` | NLTK splits `n't` off and the lower-case piece fails | fail / fail / pass | (above) |
| F-overlap-char | ratio:overlap | `ratio:overlap-aa84b728`: `the lazy dog jumps over the quick brown fox` (reference_text `the quick brown fox jumps over the lazy dog`, percentage 57) | word trigrams: 4 of 7 = 57.1%; `nltk.ngrams(value, 3)` on a string makes character trigrams | fail / **pass** / pass | 202 of 2,736 (7.4%): 162 false passes, 40 false fails; G and R differ on 227 |
| F-balance-zero | ratio:sentence_balance | `ratio:sentence_balance-3dde92ac`: `hello there` | no typed sentence is not a balance of three types; `0 == 0 == 0` passes | pass / pass / fail | 8 of 1,596 |
| F-ratio-zero | ratio:sentence_type | `ratio:sentence_type-18b41e80`: `Wow! Amazing!` | 0 declarative and 0 interrogative is not 2:1 | pass / pass / fail | 0 of 1,368 |
| F-sentence-words-unique | ratio:sentence_words | `ratio:sentence_words-a355e378`: `Cats nap. Cats nap. Cats nap.` | "using all different words" | pass / **fail** / fail | 1 of 1,596 |
| F-repeat-change-same | repeat:repeat_change | `repeat:repeat_change-5b871fd0`: the request of row 60 unchanged plus a trailing newline | the first word must change; the grader only tests inequality of the whole string | pass / pass / fail | 0 of 684 |
| F-span-char | repeat:repeat_span | `repeat:repeat_span-c1af1019`: `code and theory behind`; `-b8bcc875`: `lain` (row 284, indices 3 and 6) | the prompt says "the indices are word indices, split by whitespace"; the grader slices characters 3..6 | fail / **pass** / pass and pass / **fail** / fail | 0 of 912 (no response passes either) |
| F-alliteration-sum | sentence:alliteration_increment | `sentence:alliteration_increment-da974956`: `Big bears bite. Cats chase mice and dogs dig.` | longest run 3, then 2; the grader adds up all runs (2+2=4) | pass / pass / fail | 121 of 1,140 (10.6%): 114 false passes |
| F-word-tokenize-contractions | words:keywords_specific_position | `words:keywords_specific_position-4290eb1b`: `I don't giggle often.` (keyword giggle, n=1, m=3) | "giggle" is the 3rd word; NLTK makes "do" and "n't" two words | fail / fail / pass | 0 of 912 |
| F-attached-punct | words:last_first, words:paragraph_last_first | `words:last_first-bd3a8757`: `I like tea! Tea, warm and sweet, is good.`; `words:paragraph_last_first-4619fc58`: `Love, they say, conquers all; love.` | the first word is "Tea" / "Love"; the grader keeps the comma | fail / fail / pass | 64 (35 of 1,140 and 29 of 1,368) |
| F-startverb-tagger | words:start_verb | `words:start_verb-73fbc65e`: `Describe the scene in detail.`; `-0b8e5968`: `Explore the ruins of Rome.` | an imperative verb; the perceptron tagger tags the capitalized first word NNP / IN | fail / fail / pass | 352 of 1,368 (25.7%) by the replacement's heuristic; at least 223 (16.3%) start with a listed imperative such as "Imagine" or "Explore" (`audit/scripts/analyze_extra.py`) |
| F-startverb-markup | words:start_verb | `words:start_verb-4102f6b2`: `**Write** a short poem about rain.` | bold markers are not words | fail / fail / pass | (in the 352) |
| F-words-position-punct | words:words_position | `words:words_position-c5f037b9`: `Yes, vibrant colors are truly vibrant fun.` (keyword vibrant) | the 2nd word is "vibrant"; the grader's 2nd token is "," | fail / **pass** / pass | 5 of 684 |
| F-date-invalid | custom:date_format_list | `custom:date_format_list-47a6dff5`: `1805-00-00, 1806-10-14` | month 00 and day 00 are not dates | pass / pass / fail | 0 of 228 |
| F-loose-content | loose score (both harnesses) | `test_stress.py::loose-wordcount-lastline`: `one two three four five\nsix seven eight` (word_count_range 5..5) passes loose by dropping its last line; `loose-nowhitespace-firstline`: `Two words\nOneword`; `loose-sentencetype-firstline`: `Really? Truly?\nI agree. It works. Is it?` | the removed line is content, not a preamble or sign-off, so no reading of D-preamble allows the pass | strict fail, loose pass / same in R / fail | loose rescues 3,666 verdicts: 1,798 by removing `*`, 1,814 by removing a first or last line, 54 by both. Splitting preamble removals (decision) from content removals (finding) needs the review |
| F-crlf | format:newline | `test_stress.py::crlf-newline`: `Hello\r\n\r\nworld.` | line-ending encoding is not content; `\r`-only lines are not removed | fail / fail / pass | not measured (no stored response contains `\r\n`: field `response`) |
| F-curly-apostrophe | format:options, words:prime_lengths | `test_stress.py::curly-apostrophe-options`: `I don’t know` (options "I know or I don't know"); `curly-apostrophe-prime`: `It’s` | the apostrophe's glyph is not content | fail / fail / pass | not measured (field `response`, character U+2019) |

Every finding fixture reproduces with `audit/repro.py <fixture id>`. The loose, CRLF and apostrophe cases are pytest ids in `audit/tests/test_stress.py`; reproduce them with `audit/repro.py --check <id> --kw '<json>' --text '<text>'`, which also prints the loose verdict. Examples:

    .venv/Scripts/python.exe -I -X utf8 audit/repro.py format:sub-bullets-0dc9fe92
    .venv/Scripts/python.exe -I -X utf8 audit/repro.py --check count:word_count_range --kw '{"min_words": 5, "max_words": 5}' --text 'one two three four five\nsix seven eight'
    .venv/Scripts/python.exe -I -X utf8 audit/repro.py --check format:newline --text 'Hello\r\n\r\nworld.'

The first prints `G (grader under audit): True` with label False; the second prints `G (grader under audit): False` and `G loose: True (first passing variant: last line removed)`; the third prints `G (grader under audit): False`.

## Decision entries for the maintainers

The prompt text allows two verdicts at each of these points. Each entry has a proposed reading (P), the contract's reading. The switch column is the replacement grader with only that decision moved to P: the number of panel verdicts that change and the change in pooled strict prompt-level accuracy. Entries without a switch were not measured. Fixture ids give an example where the grader takes the non-proposed reading.

| Entry | Proposed reading (P) | Grader's reading | Example fixture | Panel effect of P |
|---|---|---|---|---|
| D-options-exact | the answer is one option; letter options accept "B)", "b", "b) Larceny" | exact string `a)`..`d)` | `format:options-e4dbcaf3` (`B)`), `-06abb3ba` | 321 verdicts, +0.47 |
| D-explanation | each quote is followed by unquoted words before the next quote or the end of its sentence | only adjacent quotes or a final quote fail | `format:quote_unquote-d71862bf` | 359, -0.53 |
| D-palindrome-distinct | ten distinct palindromes | ten occurrences | `words:palindrome-a5f3219d` | 317, -0.46 |
| D-csv-wrapper | a code fence or prose around the CSV block is allowed | only the CSV text | `custom:csv_city-d4761430` | 228, +0.33 |
| D-section | without headings, blank-line blocks are sections | (none: one italic anywhere passes; the switch's other setting is "whole text is one section") | `format:thesis-11994780` | 297, -0.31 |
| D-nbb-order | text after the bullets is allowed | nothing may follow the bullets | `format:no_bullets_bullets-18738238` | 190, +0.28 |
| D-punct-set | 11 marks: `. , ? ! ; : ' " - ( )` and `?!` or `‽` | the six marks `. , ? ! ; :` and an interrobang (C3) | `count:punctuation-231107ed` | 180, -0.26 |
| D-sentence | a line break also ends a sentence | NLTK punkt, which ignores line breaks | `sentence:keyword-bde64213` (`Intro\nI saw a giraffe.`) | 202, -0.10 |
| D-template-repeat | the template is filled once | any number of copies | `format:output_template-baf612a5` | 43, -0.06 |
| D-list-sep | one inline separator between two items suffices | at least two separators | `format:list-6fecded5` (`apples !?!? pears`) | 67, +0.06 |
| D-this-sentence | "Only output this sentence" means the sentence before the instruction | the instruction sentence itself | `repeat:repeat_simple-390d0492`, `-8a59eec5` | 33, -0.05 |
| D-trim | surrounding whitespace is ignored | every character counts | `format:no_whitespace-f7449c64` (`Hello,world!\n`) | 15, +0.02 |
| D-verb | a gerund subject ("Running is fun") is not a verb start | any VB* tag | `words:start_verb-53f06176` | 9, -0.01 |
| D-vowel-paragraph | paragraph form not graded | no line break allowed | `words:vowel-b4f6d372` | 6, +0.01 |
| D-japanese-digits | a numeral at an Nth position fails | numerals are skipped (C8) | `count:words_japanese-16200d9c` | 4, -0.01 |
| D-word | punctuation-only tokens such as `-` are not words | whitespace tokens | `words:consonants-23f48817` | 5, -0.00 |
| D-keyword-form | inflections ("doors") do not count | substrings count (G); whole words (R) | `count:keywords_multiple-aa825562` | not measured |
| D-empty, D-vacuous, D-preamble, D-markdown, D-loose | see `audit/contracts.md` | empty fails (= P); vacuous passes (= P); preamble graded in strict, removed in loose; `*` removed in loose | content-free and loose results below | not measured separately |
| all other entries | see `audit/contracts.md` and `audit/contracts_changes.md` | the grader agrees with P on every fixture | | not measured |

With all implemented decisions at P (XP), pooled strict prompt-level accuracy is 25.36% (+0.44 against G). Per configuration the change runs from -3.37 to +4.00 points (`audit/panel_tables.md`).

## Steps and what each found

### Step 1. Pinned inputs

Recorded in `audit/ISSUE.md`: case manifest (424 files, all match), grader file hashes, reference commit 1c40f0c, dataset revision 2e8a48de with one sha256 per row (`audit/frozen/dataset_rows.tsv`), prompt rendering and generation settings from `panel/CONFIGS.md`, the stored extraction rule (verified on all 68,400 records), Python 3.12.10 and the lockfile (equal to `pip freeze`), NLTK data, emoji 2.15.0, syllapy 0.8.0.

- **Unverified: the grader commit.** The case has no git metadata. Verify with `git log -1 -- <vendored path>` in Marin and a diff against Evalchemy.
- **Unverified: the graded-text extraction in the real pipeline.** The Evalchemy modules that `eval_instruct.py` imports (`eval.sources.common.text_specs`, `eval.task`) are not in the case. Verify with `grep -rn "test_instruction_following\|protocol.*ifbench" eval/` in Marin's Evalchemy checkout. This audit grades the stored `response` field.
- **Not recorded in the run records:** the vLLM version of the two thinking configurations. Also unpinned: the dataset revision (F-pin-dataset) and the NLTK data (F-pin-nltk).
- Records already show: 4,165 truncated responses (6.1%), whose prompt-level pass rate under G is 19.8% (25.2% for complete ones); 136 unclosed reasoning blocks; 37 empty responses, which every grader fails.

### Step 2. Contracts

There are 58 check contracts, general rules G1-G11 and 62 decision entries, written from the prompts and the README only. The file was hashed at 05:55:05 UTC, before any code was read. Eleven later changes are logged with reasons in `audit/contracts_changes.md`. C1 and C2 narrow an entry whose non-proposed reading the text does not support (substring keyword matches; "every word capitalized" against the prompt's own definition of title case). The others add readings or entries, so that the grader's verdict counts as a decision rather than a finding.

### Step 3. Fixtures and the replacement grader

There are 208 fixtures in `audit/tests/fixtures.py`, covering every check with at least one pass and one fail fixture, plus near misses. Ids are the check plus a content hash. `pytest audit/tests` gives 540 passed and 76 xfailed. The xfails are the fixtures and stress cases that the current grader gets wrong, marked `xfail(strict=True)`, so the change that fixes the grader must remove the mark.

The replacement grader (`audit/lib/replacement.py`) fixes every checker finding above. It has 16 working decision switches (D-keyword-form is listed but not implemented): defaults `AS_IS` (the grader's reading) and `PROPOSED`. It delegates unchanged checks to the reference checker. It passes all 208 fixtures under `PROPOSED`, and all non-decision fixtures under `AS_IS`. It was changed once after the first panel pass, on non-held-out files only. That change fixed its own errors in list-marker detection, curly-apostrophe handling, Congo aliases and plural-noun starts, and added the D-section and D-template-repeat switches. Each change came with a new fixture. A later change makes the csv checks return fail instead of raising (F-csv-quotes-exception); no panel response reaches that path.

Limits of the replacement: `start_verb` uses a tagging heuristic validated only on fixtures, and `reverse_newline` uses an alias table for country names. For format:list it does not implement the "no other bullet markers" clause.

### Step 4. Reference comparison and stress tests

- **Grader against the reference.** Fixtures: G and R differ on 9 fixtures, all six code differences, and R matches the contract on each. Panel: G and R differ on 257 verdicts: ratio:overlap 227, custom:sentence_alphabet 23, words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1. All are grader defects that the reference has fixed. repeat:repeat_span differs in code but no response passes either version. The panel's R verdicts come from the reference's checkers, called through the logic of its strict path. The reference's whole pipeline (`run_eval.py`: prompt lookup, strict then loose, aggregation) was also run on the 16 `greedy` runs with `audit/scripts/run_reference_pipeline.py`, and its per-prompt verdicts match the per-check R and R-loose verdicts in all 4,800 prompts. Its generation code was not run, because the exercise has no compute. Its `data/IFBench_test.jsonl` differs from the parquet in two prompts by whitespace only, and its `get_response_for_prompt` tolerates that.
- **Reference unit tests** (`audit/scripts/run_reference_tests.py`, results in `audit/frozen/reftests_*.txt`). R passes all. G fails 5, which are the tests the reference added with its fixes. X fails 3, and the contract contradicts each assertion:
  - `test_europe_capitals[TEST_EUROPE]` expects the 27-capital list without Kyiv to pass (F-capitals-key).
  - `test_reverse_newline[TEST_NEWLINE_COUNTRIES]` expects a list without Ethiopia and The Gambia to pass (F-africa-incomplete).
  - `test_quote_explanation__handles_empty_string_after_stripping` expects the empty string to pass (D-empty).

  Under PROPOSED, five more assertions encode a non-proposed decision reading: `TEST_OPTIONS` (D-options-exact), `TEST_PALINDROME2` (D-palindrome-distinct), `TEST_PUNCTUATION2` (D-punct-set), `TEST_QUOTE_EXPLANATION` (D-explanation), `TEST_THREE_VOWEL_FALSE` (D-vowel-paragraph).
- **Metamorphic tests** (`audit/scripts/stress.py`). These start from the fixtures that pass under the contract and under G. LF to CRLF flips 1 verdict (F-crlf). Straight to curly apostrophes flips 4 (F-curly-apostrophe, plus two format:quotes cases whose apostrophes the checker reads as quotes). Appending a newline flips 6 (D-trim for format:no_whitespace and format:options; F-nbb-blank-lines; ratio:overlap through F-overlap-char).
- **Fuzzing.** 400 random texts per instruction instance (seed 10060) gave 412,800 checker calls with no exception in G, R or X. The fuzzer did not reach the IndexError of F-csv-quotes-exception, which a hand-written input finds. These are counts, not rates.
- **Loose grading** (F-loose-content). Loose passes are tested against the contract. The loose score accepts a response if any of eight edited versions passes. Removing a first or last line is correct only when that line is a preamble or sign-off (D-preamble). The fixtures show passes that come from deleting content. On the panel, loose adds 4.03 prompt-level points (24.92% to 28.95%).
- **Content-free responses under G strict.**
  - Empty and whitespace-only responses fail every check.
  - `the` repeated 200 times passes format:sub-bullets 12/12, ratio:sentence_balance 7/7 and ratio:sentence_type 6/6 (findings). It also passes format:line_indent 9/9, sentence:increment 8/8, sentence:alliteration_increment 5/5 and words:last_first 5/5 through vacuous truth (D-vacuous), and words:consonants, words:prime_lengths and words:paragraph_last_first 5/5 to 15/15, which the text allows.
  - Restating the prompt passes format:output_template 4/4 (the prompt contains the three labels: F-template-check), count:person_names 6/6 (the prompt lists the names) and format:line_indent 9/9.

### Step 5. Model panel

All 228 stored run files were graded with G, G loose, R, R loose, X, X with every decision at P, and X with each decision alone at P (`audit/scripts/grade_panel.py`). Scored coverage is complete for every grader: 78,432 of 78,432 verdicts, with no exception. Per-check pass rates, disagreements and per-configuration tables are in `audit/panel_tables.md`; all numbers are in `audit/frozen/panel_summary.json` and `audit/frozen/panel_extra.json`.

Strict prompt-level accuracy (%), mean over each configuration's runs:

| Configuration | Runs | G | R | X | XP | X-G [min, max over runs] | G loose | greedy_repeat - greedy (G) | SD over sample runs (G) |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.08 | 34.14 | 33.39 | 30.71 | -0.69 [-1.67, +0.33] | 37.84 | -1.00 | 1.86 |
| Qwen2.5-32B-Instruct | 13 | 35.18 | 35.18 | 34.56 | 34.21 | -0.62 [-1.67, +1.67] | 38.28 | -1.33 | 2.03 |
| Qwen2.5-7B-Instruct | 17 | 27.41 | 27.51 | 26.27 | 26.76 | -1.14 [-2.67, +0.00] | 30.39 | -0.33 | 1.34 |
| Qwen3-14B (thinking off) | 17 | 27.75 | 27.84 | 29.57 | 29.14 | +1.82 [+1.00, +2.67] | 31.25 | -0.33 | 1.44 |
| Qwen3-14B (thinking on) | 3 | 34.33 | 34.67 | 39.33 | 38.33 | +5.00 [+5.00, +5.00] | 39.33 | +1.00 | n/a |
| Qwen3-32B (thinking off) | 13 | 25.10 | 25.21 | 27.90 | 27.46 | +2.79 [+1.33, +3.33] | 29.41 | -0.67 | 2.10 |
| Qwen3-8B (thinking off) | 17 | 25.18 | 25.08 | 25.94 | 24.88 | +0.76 [-0.33, +1.67] | 29.51 | +0.00 | 1.18 |
| Qwen3-8B (thinking on) | 3 | 32.44 | 32.44 | 31.67 | 30.89 | -0.78 [-1.33, -0.33] | 36.33 | +0.00 | n/a |
| Llama-3.1-Tulu-3-8B | 17 | 22.67 | 22.75 | 24.35 | 24.88 | +1.69 [+0.67, +2.67] | 26.27 | +0.33 | 1.26 |
| OLMo-2-0325-32B-Instruct | 13 | 33.28 | 33.31 | 34.46 | 31.33 | +1.18 [+0.33, +2.67] | 37.00 | +0.00 | 1.69 |
| OLMo-2-1124-13B-Instruct | 17 | 22.65 | 22.75 | 23.08 | 21.67 | +0.43 [-0.33, +1.00] | 26.76 | +0.00 | 1.36 |
| OLMo-2-1124-7B-Instruct | 17 | 20.37 | 20.37 | 21.14 | 20.14 | +0.76 [-0.67, +2.00] | 24.86 | +0.67 | 0.84 |
| marin-8b-instruct | 17 | 17.39 | 17.41 | 18.29 | 18.14 | +0.90 [-0.67, +3.00] | 21.55 | -1.00 | 1.12 |
| phi-4 | 17 | 19.06 | 19.27 | 21.78 | 22.27 | +2.73 [+1.00, +4.33] | 24.27 | +0.00 | 2.10 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.63 | 17.63 | 18.00 | 18.55 | +0.37 [-0.67, +1.33] | 20.80 | +0.33 | 1.08 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.82 | 22.26 | 25.87 | 25.69 | +4.05 [+1.67, +5.00] | 27.92 | -0.33 | 1.27 |

Rerun comparison: `greedy_repeat` repeats `greedy` with identical settings. Its differences under G are -1.33 to +1.00 points, and the batch-invariant reruns differ by -1.33 to +1.33. The per-run X-G change is a paired difference on the same responses, so rerun noise does not enter it. It is larger in magnitude than the largest rerun difference for the six configurations named in the Result section. Most of the change comes from four checks: format:sub-bullets (1,110 verdicts), words:start_verb (352), format:thesis (246) and ratio:overlap (202). This grader is not an RL reward, so false rewards were not counted.

### Step 6. Blinded review: not run

No reviewers were available, so no sample was drawn, frozen or rendered, and no error rate or interval exists. The recommendation still needs the following from step 6:

1. **Decision rule, recorded before the review** (also in `audit/ISSUE.md`): recommend replacing the grader with the replacement if the replacement passes every fixture (it does), scored coverage is complete (it is), and its error rate is lower than the current grader's, with a 95% paired bootstrap interval that excludes zero.
2. **Sample.** Draw from the held-out files only (`sample7` of the 14 sampled configurations and `greedy_repeat` of the two thinking configurations: 4,800 responses, 5,504 verdicts, of which G and X disagree on 194). The replacement was changed after the first panel pass, and those files were set aside before that pass. Stratify by G-X disagreement: take all 194 disagreements, and at least 130 consensus cases from the agreement stratum (5,310 verdicts, 96% of the population) for an upper bound near 2%. Use a recorded seed and write the case list's sha256 in the issue before any review.
3. **Review.** Two reviewers label every case in separate runs and different orders, with `skill/references/reviewer-prompt.md` and a helper that prints the exact response. Report Cohen's kappa, the disputed cases, the rates over definite verdicts, and the paired G-X difference.
4. **Extraction failures.** The 136 unclosed-reasoning responses go in the review as their own label, or are counted separately as G1 requires.

Without step 6 there is no evidence that the replacement's verdicts on start_verb, thesis and sub-bullets, the checks that move scores most, are right more often than the grader's. Its fixtures and the reference tests are the only check so far.

## Steps skipped because the exercise lacks the infrastructure

- No issue tracker: `audit/ISSUE.md` holds the issue record.
- No repository or research branch: fixtures are tests under `audit/tests/`, and scripts and the replacement are under `audit/`. Nothing was landed through `manage-pr`.
- No Hugging Face dataset: frozen files are under `audit/frozen/`, with sha256 values in `audit/ISSUE.md`.
- No compute or job launcher (`use-iris`): step 5 used the stored panel only, and no response was generated.
- No reviewers: step 6 was not run.
- `skill/references/ifbench.md` and `validation.md` were not provided. The loose-grading test follows the skill text alone.

## Files

- `audit/ISSUE.md`: issue record (progress, pins, contract hash and time, held-out set, decision rule, frozen hashes)
- `audit/contracts.md`, `audit/contracts_changes.md`: contracts and logged changes
- `audit/tests/`: fixtures and tests (`fixtures.py`, `test_fixtures.py`, `test_stress.py`)
- `audit/lib/ifbaudit.py` (G and R harness wrappers), `audit/lib/replacement.py` (X)
- `audit/repro.py`: reproduces a fixture or an inline input
- `audit/scripts/`: pinning, grading, analysis and stress scripts
- `audit/panel_tables.md`, `audit/frozen/`: panel tables, verdicts and summaries
