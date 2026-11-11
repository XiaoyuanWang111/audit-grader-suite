# Audit: Marin's vendored IFBench grader (Evalchemy)

Offline audit following `skill/SKILL.md`. Working folder W = `<W>`.
Every command below runs in Git Bash from W. The record (pinned inputs, contract hash, decisions,
findings) is in `audit/ISSUE.md`; the contracts are in `audit/CONTRACTS.md`.

## 1. Error rate and effect on scores

**Error rate: not estimated.** Step 6 (blinded review) was not run in this exercise, so there is no
consensus label set and no error rate for the grader or the replacement. What follows is
disagreement with a replacement grader built from the contracts, measured on the stored panel
(68,400 responses, 78,432 instruction verdicts, 16 configurations).

- **Findings alone** (replacement profile FIX: every finding fixed, every decision kept at the
  grader's own reading): the replacement changes **2,581 of 78,432 instruction verdicts (3.3%)**:
  1,306 grader passes become fails and 1,275 grader fails become passes.
- **Findings plus proposed readings** (profile PROPOSED): **5,503 verdicts (7.0%)** change.
- **Reference implementation** (allenai/IFBench at 1c40f0c): differs from the grader on 257 verdicts
  (0.3%); 227 of them are `ratio:overlap`, where the reference counts word trigrams and the grader
  character trigrams.
- **Model scores** (strict prompt-level accuracy, mean over each configuration's runs): FIX moves
  scores by **-1.71 to +3.78 points**, PROPOSED by **-4.14 to +2.45 points**; the reference by at
  most +0.44. Rerun differences with identical settings are at most 1.33 points
  (`greedy` vs `greedy_repeat`, and `greedy` vs `bi_greedy`); the per-run standard deviation of the
  sampled runs is 0.84-2.10 points. Under FIX, 8 of 16 configurations move by more than the larger of
  their two rerun differences (Qwen3-14B thinking +3.78, Qwen3-8B thinking +2.00, Mistral-Small-24B
  +1.77, Qwen2.5-14B -1.71, Qwen3-32B +1.03, Qwen2.5-7B -0.74, Mistral-7B -0.69, phi-4 +0.49).
- **Ranking**: Kendall tau between the grader's ranking of the 16 configurations and FIX's is 0.850
  (9 of 120 pairs swap), PROPOSED's 0.867 (8 pairs). Under FIX the two Qwen3 thinking configurations
  move from ranks 2 and 5 to ranks 1 and 2, and Qwen2.5-32B drops from 1 to 3.
- **Loose score** (reported by `eval_instruct.py` as `loose_*_accuracy`): 3,666 verdicts pass only
  loosely; FIX fails 2,667 of them (73%) on the full response.
- **Extraction**: 136 thinking-mode completions never close `</think>`; the stored `response` is then
  the whole completion, and the grader passes 45 of their 157 instruction verdicts.

**Recommendation: fix the grader** (provisional until step 6 measures error rates). Of the 43
findings below (39 checker defects, 4 pipeline and input findings), 5 are fixed in the benchmark
authors' current code, and the other checker defects are fixable check by check (the replacement
passes 229 of 232 fixtures). Nothing found makes the benchmark
itself unusable. What the recommendation still needs from step 6 is listed in section 6.

## 2. Scope, inputs and skipped steps

- Grader: `case/grader/IFBench/` (file hashes in `audit/ISSUE.md`; imported from byte-identical
  copies in `audit/frozen/code/`, because importing from `case/` writes into it). Reference:
  allenai/IFBench 1c40f0c. Dataset: allenai/IFBench_test 2e8a48d, 300 prompts, 58 checks, 344
  instruction instances; per-row hashes in `audit/out/row_hashes.tsv`.
- Contract: `audit/CONTRACTS.md`, v1 sha256 `b25309b9...9f82` recorded 2026-11-10 23:05:36 UTC
  before any grader or reference code was read (frozen copy `audit/frozen/CONTRACTS_v1.md`); later
  entries are in its change log with reasons.
- Skipped (offline): issue tracker (`audit/ISSUE.md` instead), repository test directory and
  `manage-pr` (fixtures in `audit/tests/`), research branch, Hugging Face dataset for frozen samples,
  `use-iris` and new generations (stored panel only), step 6 (no reviewers).

Reproduce everything:

    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider audit/tests
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/run_fixtures.py
    bash audit/step4/run_ref_tests.sh replacement      # also: reference, grader
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/step4_stress.py
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/step4_fixture_fuzz.py
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/panel_grade.py
    .venv/Scripts/python.exe -B audit/scripts/panel_analyze.py
    NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/panel_extra.py

Any fixture's exact input and verdicts: `NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/repro.py <fixture id>`.
It prints the check, kwargs, response (JSON-escaped), contract label, and the verdicts of the grader
(through `IFBench.grader.test_instruction_following_strict`), the reference and the replacement.

## 3. Findings

"Share" is the share of the check's panel verdicts on which the grader and the replacement FIX
differ (FIX fixes findings only), out of the check's instances in the panel; it bounds what the
finding moves on this panel. Status "same" means the reference at 1c40f0c has the same code.
Fixture ids are in `audit/tests/fixtures_data.py`; each line of the third column is reproduced by
`repro.py <id>` (command above), which prints the grader verdict given in brackets.

### 3.1 Checker defects

| id | check | fixture: exact response and kwargs [grader verdict] | contract broken | share (panel) | reference |
|---|---|---|---|---|---|
| F-span-chars | repeat:repeat_span | `repeat:repeat_span:62b5b521`: `"lain"`, request "explain the context, code and theory behind the paper ...", n_start 3, n_end 6 [pass]; `repeat:repeat_span:16643eb4`: `"code and theory behind"` [fail] | indices are word indices, split by whitespace; the grader slices characters 3..6 | 0/912 changed (no model copies a span), but every correct answer to the 4 prompts fails | fixed |
| F-sw-words | ratio:sentence_words | `ratio:sentence_words:5044f134`: `"Cats nap. Cats nap. Cats nap."` [pass] | "using all different words" is never checked | 1/1596 | fixed |
| F-kw-substring | count:keywords_multiple | `count:keywords_multiple:e4a90a39`: exact counts plus `"We stayed indoors near the doorway."`, keyword1 `door` [fail] | counts `door` inside `indoors`, `doorway` (substring count) | 1/1140 | fixed |
| F-words-position | words:words_position | `words:words_position:ca248e63`: `"Yes, despite the rain we went despite it."`, keyword `despite` [fail] | the comma after word 1 is taken as word 2 | 5/684 | fixed |
| F-alphabet-quote | custom:sentence_alphabet | `custom:sentence_alphabet:f7f9545f`: 26-sentence story whose 13th sentence opens `"Moles came to the party," said the host.` [fail] | first word read with its opening quote | 23/228 (10.1%) | fixed |
| F-subbullets | format:sub-bullets | `format:sub-bullets:ec22004d`: `"A plain paragraph without any list."` [pass]; `format:sub-bullets:0c74076c`: `"* A well-known point\n* Another long-term point"` [pass]; `format:sub-bullets:e7495b86`: `"**Intro**\n* Point one\n  - detail\n* Point two\n  - detail"` [fail] | splits on every `*`: no bullets passes, any hyphen counts as a sub-bullet, bold text breaks it | 1121/2736 (41.0%): 207 false passes, 914 false fails | same |
| F-quotes-apostrophe | format:quotes | `format:quotes:7cf9bcaf`: `"\"It's\" he said \"and that's all\""` [pass]; `format:quotes:9c4f075a`: three levels in curly quotes [fail] | apostrophes counted as quote marks; curly quotes ignored | 345/1824 (18.9%) | same |
| F-conj-case | count:conjunctions | `count:conjunctions:fb8f23a5`: `"And and, AND but."`, small_n 3 [pass] | distinct conjunctions counted on raw tokens (`And`, `and,` differ) | 188/1596 (11.8%) | same |
| F-nbb-period | format:no_bullets_bullets | `format:no_bullets_bullets:bc1d39c3`: `"Hello there\nHow are you\n* item one\n* item two"` [pass]; `...:a820b2b3`: `"I. Intro\nII. Body\n* item one\n* item two"` [pass] | sentences need not end in a period | with the next two: 124/1140 (10.9%) | same |
| F-nbb-blank | format:no_bullets_bullets | `format:no_bullets_bullets:efebab63`: `"First sentence. Second sentence.\n\n* item one\n\n* item two"` [fail]; `...:31e6bc5f`: same with one trailing newline [fail] | a blank line or trailing newline after the first bullet fails | (above) | same |
| F-nbb-bold | format:no_bullets_bullets | `format:no_bullets_bullets:409944b6`: `"**Intro**\nFirst sentence here. Second one here.\n* item one\n* item two"` [fail] | a bold line is taken as a bullet | (above) | same |
| F-alliteration-sum | sentence:alliteration_increment | `sentence:alliteration_increment:db02ba92`: `"Big bears roam far away. Cats cry and dogs dig."` [pass] | sums all alliterative runs instead of the longest sequence (2 then 2) | 120/1140 (10.5%) | same |
| F-template-presence | format:output_template | `format:output_template:e80c73b8`: labels in reverse order [pass]; `...:9b7e96d4`: `"Sure, here it is.\n"` before the template [pass]; `...:c70ec147`: `"My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]"` [pass] | only checks that the three labels occur somewhere | 79/912 (8.7%) | same |
| F-paren-unclosed | format:parentheses | `format:parentheses:01e07b33`: `"(((((x)"` [pass] | counts unclosed outer brackets as nesting | 144/1824 (7.9%) | same |
| F-quote-unquote | format:quote_unquote | `format:quote_unquote:33f1ee47`: `"\"alpha\", \"beta\" are words."` [pass]; `...:ba581987`: `"\u201cCarpe diem\u201d \u201cseize the day\u201d"` [pass] | a phrase followed only by punctuation passes; curly quotes are invisible (`value.replace('"', '"')` is a no-op) | 83/1140 (7.3%) | same |
| F-thesis-anywhere | format:thesis | `format:thesis:89ea3cce`: `"Cats are great pets. They purr, and <i>dogs bark</i> loudly."` [pass] | any `<i>` anywhere passes; no section begins with it | 88/2052 (4.3%) | same |
| F-mcq-label | custom:mcq_count_length | `custom:mcq_count_length:86822fab`: 4 questions labeled `Question:` with 5 options each, stems growing [fail] | requires `Question <number>` | 22/228 (9.6%) | same |
| F-list-anywhere | format:list | `format:list:90f8f100`: `"A well-known and long-term plan."`, sep `-` [pass]; `format:list:e6d2440b`: `"Use SEPARATOR or SEPARATOR as you like."`, sep `SEPARATOR` [pass] | any two occurrences of the marker count, including hyphens inside words | 49/2052 (2.4%) | same |
| F-lastfirst-punct | words:last_first | `words:last_first:2a473278`: `"I love tea. Tea. Tea is warm."` [fail] | a one-word sentence keeps its period (`tea.` vs `tea`) | 35/1140 (3.1%) | same |
| F-para-punct | words:paragraph_last_first | `words:paragraph_last_first:521560db`: `"Time, they say, heals wounds over time."` [fail] | punctuation inside the line stays on the first word (`time,`) | 29/1368 (2.1%) | same |
| F-titlecase-minor | format:title_case | `format:title_case:9063eb4c`: `"The Lord of the Rings Is a Great Book"` [fail]; `...:56e39eb0`: `"Don't Stop Believing"` [fail] | minor words must be capitalized; `n't` token fails | 18/912 (2.0%) | same |
| F-start-verb-markup | words:start_verb | `words:start_verb:d764651e`: `"**Imagine** a world of peace."` [fail]; `...:736f53b6`: `"# Imagine a world of peace\nIt is calm."` [fail] | markdown symbols are tagged as the first word | 22/1368 (1.6%) | same |
| F-start-verb-tagger | words:start_verb | `words:start_verb:b4dfed1c`: `"Discover the truth."` [fail]; `...:19a9602d`: `"Craft a story."` [fail] | the NLTK tagger tags sentence-initial imperatives IN / NNP | not measurable without review (the replacement keeps the tagger); stored field: `g_strict` for `words:start_verb` | same |
| F-ratio-zero | ratio:sentence_type, ratio:sentence_balance | `ratio:sentence_type:47e0156f`: `"Wow! Amazing!"` [pass]; `ratio:sentence_balance:cf43cd91`: `"I like tea\nI like coffee"` [pass] | 0:0 passes as 2:1; 0:0:0 passes as balanced | type 19/1368 (with the next), balance 8/1596 | same |
| F-sentence-marks | ratio:sentence_type | `ratio:sentence_type:23f613f7`: `"He said \"I like tea.\" She said \"I like milk.\" Do you?"` [fail] | a sentence ending `."` is not counted as declarative | (above) | same |
| F-reverse-substring | custom:character_reverse, custom:word_reverse | `custom:character_reverse:e7477945`: `"The bald eagle. Reversed: elgae dlab ehT"` [pass]; `custom:word_reverse:cbe8ddff`: `"Eagle bald the is animal national the. I hope this helps you today."` [pass] | substring `elgae dlab` anywhere passes; forward-order extra sentences pass | 5/228 each | same |
| F-africa-content | custom:reverse_newline | `custom:reverse_newline:2707bd0a`: `Zimbabwe` plus 51 invented names in reverse order [pass]; `...:fe647857`: correct numbered list `1. Zimbabwe` ... [fail] | lines are never checked to be countries; numbering breaks the sort | 6/228 (2.6%) | same |
| F-capitals-kyiv | custom:european_capitals_sort | `custom:european_capitals_sort:c87b7247`: the 28 capitals above 45 N including Kyiv (50.45 N), in order [fail] | the hard-coded list omits Kyiv, so a complete correct answer fails | 0/228 (no model gives either list exactly) | same; its unit test `TEST_EUROPE` asserts the list without Kyiv |
| F-word-symbols | count:unique_word_count, sentence:increment, words:consonants, words:prime_lengths, words:repeats, format:newline | `count:unique_word_count:ab14b0e9`: `"\u201cAlpha\u201d alpha alpha, Alpha. beta"`, N 3 [pass]; `...:745e6c9c`: `"red \u2014 green \u2014 blue"`, N 4 [pass]; `sentence:increment:0c38c97a`: `"I run. I run \u2014 very fast."` [fail]; `words:consonants:e9460db8`: `"Strong \u2014 black crabs."` [fail]; `words:prime_lengths:4cbf79a7`: `"We are \u2014 not big."` [fail]; `words:repeats:569c4d44`: `"red \u2014 green \u2014 blue \u2014 pink"`, small_n 2 [fail] | dashes, curly quotes and other non-ASCII symbols are counted as words or as parts of words | unique 13/2052, consonants 7/3420, newline 5/1368, others 0 | same |
| F-numbers-merge | count:numbers | `count:numbers:769c4c75`: `"Delivery takes 3-5 days."`, N 2 [fail]; `...:7ab4b231`: `"Pick 1,2,3 now."`, N 3 [fail] | deleting punctuation merges `3-5` and `1,2,3` into one number | 4/1824 | same |
| F-japanese-digits | count:words_japanese | `count:words_japanese:8da2143c`: `"I like 2 very much \u672c\u5f53\u306b."`, N 3 [pass] | a numeral at a Japanese position is skipped | 9/1140 (0.8%) | same |
| F-syllables | words:odd_even_syllables | `words:odd_even_syllables:82ff7429`: `"Duo cat happy dog."` [fail]; `...:f3db27e7`: `"Trio happy."` [pass]; `...:b18da036`: `"It isn't hot."` [fail] | syllapy miscounts words with one accepted count (`duo`, `trio` 2; `isn't` read as `isnt`, 1) | 0/2052 changed (the replacement fixes only listed words) | same |
| F-indent-tabs | format:line_indent | `format:line_indent:5213f6b9`: `"a\n\tb\n\t\tc"` [fail] | only spaces count as indentation | 2/2052 | same |
| F-newline-blank | format:newline | `format:newline:98ea1892`: `"Hello world\n \nagain"` [pass] | a whitespace-only line offsets a line holding two words | (in newline 5/1368) | same |
| F-options-apostrophe | format:options | `format:options:9dd5e6e6`: `"I don\u2019t know."`, options `I know or I don't know` [fail] | a typographic apostrophe makes the option unequal | 0/1368 on stored text; 7 flips when apostrophes are made typographic (section 4) | same |
| F-repeat-change | repeat:repeat_change | `repeat:repeat_change:aacd3c2c`: the request unchanged plus one trailing space [pass]; `...:a4fc246e`: the request unchanged with a double space [pass] | an unchanged first word passes when whitespace differs | 0/684 stored; 7 flips under trailing newline or double spaces (section 4) | same |
| F-date-zero | custom:date_format_list | `custom:date_format_list:c648f919`: `"1805-00-00, 1815-06-18"` [pass] | month 00 and day 00 are accepted as dates | 0/228 | same |
| F-csv-special-rows | custom:csv_special_character | `custom:csv_special_character:8e4e9882`: 14 rows, special field in row 1, row 5 has 3 fields [pass] | returns at the first special field before checking later rows | 0/228 | same |
| F-exception | custom:csv_quotes; pipeline | `custom:csv_quotes:02ad842f`: quoted header, a row with an empty unquoted field (`"1"\t\t"A"\t"Fall"\t"95"`) [raises `IndexError`] | a grading failure, not a verdict; `grader.py` has no exception handling | 0 on the panel; 10 of 11,600 fixture-seeded fuzz inputs; one such response aborts the reference's whole run (`bash audit/out/runeval_crash/run.sh`: exit 1, no output files); the Evalchemy caller of `grader.py` is not in `case/` | same |

### 3.2 Pipeline and input findings

| id | stage | evidence | effect | reference |
|---|---|---|---|---|
| F-extraction | graded-text extraction | `grader.py` grades the string it is given; no `</think>` handling. In the stored panel 136 thinking completions (Qwen3-8B 104, Qwen3-14B 32) never close `</think>`, so `response` holds the reasoning. | the grader passes 45 of their 157 verdicts; under the contract (extraction failure fails every check) Qwen3-8B thinking drops from 31.78 to 29.22 (PROPOSED), Qwen3-14B thinking from 36.78 to 36.11. Whether Evalchemy strips reasoning is unverified (`eval/sources/common.py::text_specs`, not in `case/`). Stored fields: `raw_response`, `finish_reason`. | no extraction either |
| F-pin-commit | inputs | `case/TASK.md` names no Marin or Evalchemy commit for the vendored grader | a run cannot be tied to grader code | n/a |
| F-pin-dataset | inputs | `eval_instruct.py`: `load_dataset("allenai/IFBench_test", split="train")` without `revision` | the evaluated prompts can change silently | the reference ships its own JSONL |
| F-pin-nltk | inputs | `instructions_util.download_nltk_resources()` downloads `punkt`, `punkt_tab`, `stopwords`, `averaged_perceptron_tagger_eng` at import when absent; `instructions.py` points `NLTK_DATA` at an empty folder next to the code | sentence splitting, stop words and POS tags (and so verdicts of about 25 checks) depend on whatever version is downloaded at run time | same |

## 4. Reference comparison and stress tests (step 4)

- **Reference vs grader**: 7 checks differ in code. On the panel they disagree on 257 verdicts:
  `ratio:overlap` 227 (D-overlap-def), `custom:sentence_alphabet` 23, `words:words_position` 5,
  `count:keywords_multiple` 1, `ratio:sentence_words` 1. The grader fails 5 of the reference's own unit
  tests (`test_keywords_multiple__counts_whole_words`, `test_repeat_span__uses_word_indices`,
  `test_sentence_alphabet__ignores_leading_punctuation`, `test_sentence_words__requires_unique_words`,
  `test_words_position__ignores_punctuation_tokens`): `bash audit/step4/run_ref_tests.sh grader`.
- **Reference unit tests vs the replacement** (`bash audit/step4/run_ref_tests.sh replacement`: 8 failed,
  64 passed). Every failing assertion encodes a non-proposed reading; none is a replacement defect:
  `TEST_EUROPE_INCOMPLETE` and `TEST_NEWLINE_COUNTRIES_FALSE_INCOMPLETE` (completeness, D-custom-content B);
  `TEST_OPTIONS` (bare `A` for `(A), (B), (C)` must fail, D-options B); `TEST_PALINDROME2` (`abcba` ten
  times passes, D-palindrome B); `TEST_PUNCTUATION2` (six marks suffice, D-punct-set C);
  `test_quote_explanation__handles_empty_string_after_stripping` (empty response passes the checker,
  D-empty B; the pipeline fails empty responses anyway); `TEST_SUBBULLET` (one bullet, D-plural B);
  `TEST_THREE_VOWEL` (one vowel type, D-vowel C). The passing `TEST_EUROPE` asserts that the list
  without Kyiv is the complete answer, which the contract contradicts under the completeness reading.
- **Content-free responses** (`audit/out/step4_content_free.tsv`): empty and whitespace-only responses
  fail every check in all graders. The single letter `a` passes 17 checks in the grader (116 instances),
  15 in the replacement; the contract contradicts the grader on `format:sub-bullets` (12),
  `ratio:sentence_balance` (7), `ratio:sentence_type` (6) and, under D-vowel A, `words:vowel` (10).
  `the` repeated 60 times passes 14 checks in the grader (96 instances), including `format:sub-bullets`,
  both sentence-ratio checks and `ratio:overlap` (1). Restating the prompt passes 15 checks in the grader
  (50 instances), including `format:output_template` (4) and `format:sub-bullets` (11), which the
  replacement fails.
- **Metamorphic edits the contract ignores** (16 greedy runs, `audit/out/step4_metamorphic.tsv`):
  making apostrophes typographic flips 29 grader verdicts (`format:quotes` 16, `format:options` 7,
  `format:title_case` 6); doubling spaces flips 15 (`repeat:repeat_change` 7, `ratio:overlap` 4,
  `custom:mcq_count_length` 4); appending one newline flips 130 (`format:options` 58,
  `format:no_whitespace` 37, `format:no_bullets_bullets` 28, `repeat:repeat_change` 7). The replacement
  (PROPOSED) flips 0 under each edit. On the stored text, the 415 non-empty responses that end in
  whitespace change no grader verdict when their trailing whitespace is removed.
- **Fuzzing** (counts depend on the generator): 12,000 random strings (seed 10060) and 14,400 mutated
  greedy responses (seed 10061) raise no exception in any grader; 11,600 mutations of the 232 fixtures
  (seed 10062) raise 10 `IndexError` in `custom:csv_quotes` in the grader and the reference, 0 in the
  replacement (`audit/out/step4_fixture_fuzz.tsv`).
- **Loose grading** (score-level transform; D-loose): the grader also accepts the response with its
  first and/or last line removed or with every `*` removed. On the panel 3,666 verdicts pass only
  loosely; 2,667 of these fail the contract on the full response (FIX), most in `format:sub-bullets` 823,
  `format:line_indent` 232, `ratio:stop_words` 164, `count:word_count_range` 156, `count:numbers` 138,
  `custom:multiples` 122. Deleting a line can remove the very text that breaks an instruction (a
  preamble before a required first word, an extra keyword occurrence), so a loose pass is not evidence
  of compliance.

## 5. Model panel (step 5)

Stored records only (no generation). Records: 68,400 responses; 4,165 hit the token limit
(`finish_reason == "length"`); 136 thinking completions never close `</think>`; 37 responses are empty;
448 end in whitespace. Scored coverage is complete (78,432 of 78,432 verdicts) for every grader.
Held-out runs (never used to change the replacement): `sample7` of each configuration with sample runs,
`greedy_repeat` of the thinking configurations.

Strict prompt-level accuracy, mean over runs (instruction-level in brackets), from
`audit/out/panel_scores.tsv`:

| configuration | runs | grader | reference | repl FIX | repl PROPOSED | PROPOSED + extraction failures | grader loose | rerun diff (greedy vs repeat / bi) |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.08 [36.58] | 34.14 | 32.37 | 29.94 | 29.94 | 37.84 | 1.00 / 0.67 |
| Qwen2.5-32B-Instruct | 13 | 35.18 [38.98] | 35.18 | 34.28 | 32.51 | 32.51 | 38.28 | 1.33 / 1.00 |
| Qwen2.5-7B-Instruct | 17 | 27.41 [29.55] | 27.51 | 26.67 | 24.39 | 24.39 | 30.39 | 0.33 / 0.33 |
| Qwen3-14B | 17 | 27.75 [30.98] | 27.84 | 27.75 | 27.59 | 27.59 | 31.25 | 0.33 / 1.33 |
| Qwen3-14B thinking | 3 | 34.33 [37.31] | 34.67 | 38.11 | 36.78 | 36.11 | 39.33 | 1.00 / - |
| Qwen3-32B | 13 | 25.10 [28.47] | 25.21 | 26.13 | 25.33 | 25.33 | 29.41 | 0.67 / 0.33 |
| Qwen3-8B | 17 | 25.18 [28.27] | 25.08 | 25.08 | 23.86 | 23.86 | 29.51 | 0.00 / 1.00 |
| Qwen3-8B thinking | 3 | 32.44 [35.95] | 32.44 | 34.44 | 31.78 | 29.22 | 36.33 | 0.00 / - |
| Llama-3.1-Tulu-3-8B | 17 | 22.67 [25.55] | 22.75 | 23.24 | 23.41 | 23.41 | 26.27 | 0.33 / 1.33 |
| OLMo-2-0325-32B-Instruct | 13 | 33.28 [36.69] | 33.31 | 32.97 | 29.82 | 29.82 | 37.00 | 0.00 / 1.33 |
| OLMo-2-1124-13B-Instruct | 17 | 22.65 [24.30] | 22.75 | 21.71 | 20.35 | 20.35 | 26.76 | 0.00 / 1.00 |
| OLMo-2-1124-7B-Instruct | 17 | 20.37 [23.14] | 20.37 | 20.02 | 19.45 | 19.45 | 24.86 | 0.66 / 1.00 |
| marin-8b-instruct | 17 | 17.39 [20.02] | 17.41 | 17.22 | 17.47 | 17.47 | 21.55 | 1.00 / 0.34 |
| phi-4 | 17 | 19.06 [21.24] | 19.27 | 19.55 | 21.35 | 21.35 | 24.27 | 0.00 / 0.00 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.63 [20.18] | 17.63 | 16.94 | 17.59 | 17.59 | 20.80 | 0.34 / 0.34 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.82 [24.64] | 22.26 | 23.59 | 23.23 | 23.23 | 27.92 | 0.34 / 1.33 |

Per-check pass rates and every disagreement count are in `audit/out/panel_checks.tsv`; the run log
with the full table is `audit/out/panel_analyze.log`.

## 6. Blinded review (step 6): not run

No reviewers were available, so no sample was drawn, frozen or rendered, and there is no error rate,
interval, kappa or disputed-case list. The recommendation needs from step 6:

1. The result recorded in advance (see `audit/ISSUE.md`): fix stands if the replacement passes every
   fixture except the 3 listed, scored coverage is complete, and the replacement's error rate is lower
   than the grader's with a paired 95% bootstrap interval that excludes zero.
2. A sample stratified by grader-vs-replacement disagreement, drawn from the held-out runs with a
   recorded seed: all or most of the disagreement stratum (on the held-out runs about 1/16 of the
   5,503 PROPOSED disagreements) and about 130 consensus cases from the agreement stratum, which holds
   about 93% of verdicts, for an upper end near 2%.
3. Two reviewers per case with `skill/references/reviewer-prompt.md`, consensus by leans, rates per
   stratum weighted by stratum size, and the zero-error correction of section 6.5 of the skill. The
   decision entries must be settled by the maintainers first, or the review reported per reading.
4. A separate count for `words:start_verb` (F-start-verb-tagger) and `format:quotes`, where the
   replacement's own rules are heuristic (spot checks found one spurious quote chain in the
   replacement's passes).

## 7. Decision entries for the maintainers

Full readings and examples are in `audit/CONTRACTS.md`. "Grader" names the reading the grader follows.
"Panel effect" is the number of verdicts on which PROPOSED and FIX differ in the checks where the entry
is switched (several entries can share a check; switches not implemented are marked n/i).

| entry | proposed reading (A) | grader's reading | fixture | panel effect |
|---|---|---|---|---|
| D-trim | ignore leading/trailing whitespace | every character counts | `format:no_whitespace:e1335b1e`, `format:options:bd7bd578` | no_whitespace 15/912 (leading spaces: 5,219 stored `response` values start with whitespace); options counted under D-options |
| D-empty | empty answer fails | fails (strict precheck) | content-free tests | 0 |
| D-word | whitespace tokens minus symbols | regex `\w+` runs (`don't` = 2) | `count:word_count_range:ac5b7463`, `words:keywords_specific_position:4d8978c8` | word_count_range 142/2508, stop_words 24/2736 |
| D-sentence | line ends also end sentences | punkt only | `format:emoji:9722e32a` | sentence:keyword 140/3420, sentence:increment 35/1824, sentence_balance 45/1596 (with D-balance), alliteration 9/1140, sentence_type 8/1368, mcq 7/228, emoji 2/2052, sentence_alphabet 1/228 |
| D-keyword-match | exact form, whole word | substring (finding) / reference: exact | `count:keywords_multiple:4b402522`, `sentence:keyword:bcda4752` | 0 beyond F-kw-substring |
| D-vacuous | no instance passes | passes | `sentence:increment:eb642849`, `words:last_first:0898d832`, `count:words_japanese:df3cbf25` | 0 |
| D-loose | report loose separately, never as the score | loose is a reported metric | section 4 | 2,667 contract-failing loose passes |
| D-conj-role | count word forms | forms | `count:conjunctions:4e97dd36` | n/i |
| D-count-exact | "once/twice" = exactly | exactly | - | 0 |
| D-number | digit numerals; dates 3, times 2 | dates, times, fractions one number | `count:numbers:ce26fb0c` | 1/1824 |
| D-name-case | capitalized whole word | capitalized | `count:person_names:e6d95dac` | n/i |
| D-pronoun-set | pronouns standing for nouns | every listed word form (C) | `count:pronouns:8934b742` | n/i |
| D-punct-set | 15 marks plus `?!` | six marks plus `?!` (C) | `count:punctuation:afe819ad` | 267/1368 |
| D-unique | distinct types | distinct types | `count:unique_word_count:01bf49f1` | n/i (same) |
| D-japanese-words | unspaced Japanese run = one word | same | - | n/i |
| D-emoji-position | before or after the mark | either | - | n/i |
| D-stairs-blank | blank lines ignored | ignored, except two in a row break it | `format:line_indent:0009a4a9` | 0 |
| D-list-form | intro text allowed | allowed | - | (in D-list-placement) |
| D-list-placement | marker starts each line | marker anywhere (B) | `format:list:c2761702` | 425/2052 |
| D-nbb-order | text after bullets allowed | no text after bullets | `format:no_bullets_bullets:2d161ca4` | with D-bullet-syntax 163/1140 |
| D-bullet-syntax | `* ` with a space | `*` followed by anything | `format:no_bullets_bullets:8a6f0dc6` | (above), sub-bullets 79/2736 with D-plural |
| D-whitespace | Unicode whitespace | Unicode | `format:no_whitespace:5c7eec93` | 0 |
| D-options | starts with one option, explanation allowed, letter variants | exact option | `format:options:5b0597f3`, `...:781c381b`, `...:997a5787` | 468/1368 |
| D-template-markup | emphasis around labels allowed | allowed | `format:output_template:e087274e` | 0 |
| D-paren-types | any bracket type | any | `format:parentheses:3372396c` | 0 |
| D-quote-chars | double quotes and guillemets | straight double only (finding) | - | n/i |
| D-explanation | one unquoted word | none required (finding) | `format:quote_unquote:934349a0` | n/i |
| D-subbullet-indent | not required | not required | `format:sub-bullets:1bdb9696` | 0 |
| D-plural | "bullet points" = at least two | at least one | `format:sub-bullets:268841ea` | (in sub-bullets 79) |
| D-section | headings, else blank-line blocks | one italic anywhere (finding); FIX uses whole answer | `format:thesis:f9618240` | 410/2052 |
| D-titlecase | minor words free, all caps passes | all caps passes | `format:title_case:251571d1` | 0 |
| D-overlap-def | word trigrams, share of the answer's | character trigrams (reference: word trigrams) | `ratio:overlap:e50d301f` | 204/2736 |
| D-balance | counts within 1 | exactly equal | `ratio:sentence_balance:11908b56` | (with D-sentence) 45/1596 |
| D-ratio-exact | exactly 2:1 | exactly | - | 0 |
| D-sw-chars | all characters | all characters | - | n/i |
| D-sw-words | no word repeated anywhere | no check (finding); reference: anywhere | `ratio:sentence_words:ce578480` | 0 |
| D-stopwords | NLTK English list | NLTK, unpinned version | - | n/i |
| D-simple-referent | the instruction sentence | same | - | n/i |
| D-simple-case | case must match | case-insensitive | `repeat:repeat_simple:85aa3774` | 0 |
| D-change-case | case-only change is no change | counts as change | `repeat:repeat_change:0fa08b40` | 0 |
| D-index-base | 0-based | characters (finding); reference 0-based | `repeat:repeat_span:8097e5e3` | 0 |
| D-alliteration | same first letter | first letter | - | n/i |
| D-consonant-y | `y` consonant | consonant | `words:consonants:7904d7e5` | n/i |
| D-syllables | variant pronunciations both accepted | syllapy | - | n/i |
| D-palindrome | distinct words | occurrences | `words:palindrome:098d5b94` | 321/1596 |
| D-repeats | at most N occurrences | at most N | `words:repeats:057c3b2a` | 0 |
| D-verb | any verb form | tagger VB* | - | n/i |
| D-vowel | one paragraph, exactly three vowel types | at most three (C) | `words:vowel:59b54517` | 63/2280 |
| D-reverse-form | exact reversal of an answer sentence | substring (finding) | - | n/i |
| D-csv-wrap | code fence and surrounding text allowed | CSV only | `custom:csv_city:8ee73126` | csv_city 91, csv_quotes 43, csv_special 46 (with D-special), of 228 each |
| D-special | exactly one special quoted field | at least one | `custom:csv_special_character:a26bf6d5` | (above) |
| D-custom-content | completeness not required | complete list required | `custom:reverse_newline:84e3b32f`, `custom:european_capitals_sort:4e482a5e` | european_capitals 23/228 |
| D-mcq-length | stem characters | stem characters | - | n/i |

## 8. Limits of this audit

- No error rate (step 6 not run); the panel numbers are disagreements with a replacement that has
  only been checked against 232 fixtures, the reference's unit tests and spot checks.
- The grader was audited as vendored; how Evalchemy builds `response` (reasoning stripping, retries,
  exception handling) is unverified, and the panel was generated by offline vLLM, not by Evalchemy.
- Several decision switches are not implemented in the replacement (n/i above); their effect is not
  measured. The replacement keeps the grader's POS tagger and syllable counter, with small patches.
- The replacement was adjusted after looking at disagreements in non-held-out runs (thesis wrappers,
  list markers, outline lines, `*Text` bullets); two held-out responses were displayed during that
  spot check and neither prompted a change.
