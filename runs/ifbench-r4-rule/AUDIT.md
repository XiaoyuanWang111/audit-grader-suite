# IFBench grader audit: Marin's vendored Evalchemy copy

Audit of `case/grader/IFBench/` (58 instruction checkers plus the strict/loose harness) against the
IFBench_test prompts, following `skill/SKILL.md`. Workspace W = `<W>`;
all paths below are relative to W. Record of the audit: `audit/ISSUE.md`. Contract: `audit/CONTRACTS.md`
v1, sha256 `f2ed95e9ebd43209d32bfeb99d312eb2c422fe6b4fdc63c46252bd6782f3d900`, hashed 2026-11-10
05:47:39 UTC before any grader or reference code was read.

Steps run: 1, 2, 3, 4, 5 (stored responses only), 7. Step 6 (blinded review) was not run: no reviewers
were available in this exercise.

Names used below: **G** = the grader under audit, kwargs exactly as `eval_instruct.load_questions`
builds them from the HF parquet (numbers are `float`); **Gi** = the same grader with integer kwargs;
**R** = the reference implementation (allenai/IFBench at 1c40f0c, its own `evaluation_lib` pipeline);
**X** = the replacement grader built from the contracts (`audit/replacement/grader.py`, proposed
readings, extraction rule G1); **XG** = the replacement with every decision switch set to the
grader's reading and no G1, so that Gi vs XG isolates defects and XG vs X isolates decisions.

## 1. Error rate and effect on scores

**Error rate: not estimated.** The error rate is defined by a blinded review (step 6), which was not
run. What the audit can state without it:

- On 215 fixtures labeled from the contract alone (pass, fail and near-miss for all 58 checks), G gives
  the wrong verdict on 88: 66 contradict the contract under every reading (findings) and 22 follow a
  non-proposed reading of a decision entry. Every check has at least one fixture; 44 of the 58 checks
  have at least one finding.
- On the panel (68,400 stored responses, 78,432 graded (prompt, check) items), fixing the defects
  changes 3.96% of verdicts (Gi vs XG), the proposed readings of the decision entries and the
  extraction rule change another 3.05% (XG vs X), and in total X differs from G on 8.34% of verdicts.
  These are disagreement rates with an unreviewed replacement, not error rates; spot checks
  (section 5.4) found the replacement right in most sampled disagreements but not all.
- G gives no verdict on 1,067 items (scored coverage 98.64%): every `repeat:repeat_span` check (911 of
  912 items; the 912th is an empty response) and 156 of 912 `words:keywords_specific_position` items
  raise `TypeError` (F01).

**Effect on scores.** Prompt-level strict accuracy (Marin's primary metric), mean over each
configuration's runs, in points:

| configuration | G | R | X (replacement) | X - G | of which defects (XG - Gi) | of which decisions and G1 (X - XG) |
|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 34.08 | 34.14 | 30.57 | -3.51 | -2.16 | -1.35 |
| Qwen2.5-32B-Instruct | 35.18 | 35.18 | 32.59 | -2.59 | -2.13 | -0.46 |
| Qwen2.5-7B-Instruct | 27.41 | 27.51 | 24.73 | -2.69 | -1.86 | -0.82 |
| Qwen3-14B (thinking off) | 27.75 | 27.84 | 26.59 | -1.16 | +0.22 | -1.37 |
| Qwen3-14B (thinking on) | 34.33 | 34.67 | 36.22 | +1.89 | +3.22 | -1.33 |
| Qwen3-32B (thinking off) | 25.10 | 25.21 | 24.56 | -0.54 | +0.21 | -0.74 |
| Qwen3-8B (thinking off) | 25.18 | 25.08 | 23.47 | -1.71 | -0.55 | -1.16 |
| Qwen3-8B (thinking on) | 32.44 | 32.44 | 29.11 | -3.33 | +0.00 | -3.33 |
| Llama-3.1-Tulu-3-8B | 22.67 | 22.75 | 22.14 | -0.53 | -0.31 | -0.22 |
| OLMo-2-0325-32B-Instruct | 33.28 | 33.31 | 30.59 | -2.69 | -1.05 | -1.64 |
| OLMo-2-1124-13B-Instruct | 22.65 | 22.75 | 19.02 | -3.63 | -1.63 | -2.00 |
| OLMo-2-1124-7B-Instruct | 20.37 | 20.37 | 18.71 | -1.67 | -0.90 | -0.76 |
| marin-8b-instruct | 17.39 | 17.41 | 16.45 | -0.94 | -0.47 | -0.47 |
| phi-4 | 19.06 | 19.27 | 19.49 | +0.43 | -0.10 | +0.53 |
| Mistral-7B-Instruct-v0.3 | 17.63 | 17.63 | 16.45 | -1.18 | -0.55 | -0.63 |
| Mistral-Small-24B-Instruct-2501 | 21.82 | 22.26 | 22.15 | +0.33 | +1.03 | -0.69 |

- The changes are model-dependent (from -3.63 to +1.89 points), so they change the ranking: Spearman
  0.970 and Kendall 0.879 between the G and X orderings of the 16 configurations; 13 of the 16 change
  rank, by at most 2 places, and the top two swap (Qwen3-14B thinking moves above Qwen2.5-32B). On the
  held-out runs
  (sample7, or greedy_repeat for the thinking configurations; nothing was tuned on them) the mean
  change is -1.85 points (G 26.25, X 24.40).
- Rerun differences on identical settings (reference verdicts): greedy_repeat - greedy ranges from
  -1.33 to +1.00 points, greedy_shuffled - greedy from -1.33 to +1.33, bi_greedy_shuffled - bi_greedy is
  0.00 for every configuration, and the standard deviation over sampled runs is 0.84 to 2.08. In 9 of 16
  configurations the grader change (|X - G|) exceeds the largest greedy rerun difference (1.33). X and G
  are computed on the same responses, so the change itself is not sampling noise.
- G vs R: the two differ only in 5 checkers and in kwargs types. Prompt-level differences are at most
  0.44 points per configuration; 1.69% of verdicts differ, 1,067 of them because G raises (F01).
- Loose grading (reported by Marin as a secondary metric, and the paper's headline metric) adds +2.98 to
  +6.10 points over strict; 3,666 item verdicts pass only under loose, and for `format:sub-bullets` the
  loose variant passes every non-empty response (F42).
- Extraction failures: 136 thinking-mode responses never close their reasoning (all stopped at 8,192
  tokens). G and R grade the reasoning text and pass 45 checks on them; failing them as the contract
  requires lowers Qwen3-8B (thinking on) by 3.22 points and Qwen3-14B (thinking on) by 0.67 (F43).

## 2. Recommendation

**Fix the grader** (not admit it). 44 of 58 checks have contract violations shown by minimal
fixtures, two checks raise on every or many responses as Marin loads the data, the loose metric passes
responses the contract fails, and the defects alone move configurations by -2.16 to +3.22 points and
reorder them. The benchmark does not need replacing: every check has a mechanically gradable contract,
and the replacement passes all fixtures except one (F38, syllable counting).

Concretely: (1) cast integer kwargs or fix F01 before any further runs, since today two checks score
zero by exception; (2) replace the checkers with contract-based ones, starting from
`audit/replacement/grader.py`, with each decision entry in section 4 settled by the maintainers;
(3) apply G1 (unclosed reasoning fails) in the extraction step; (4) pin the dataset revision and NLTK
data (F39, F40); (5) report strict prompt accuracy only, or label loose as an upper bound (F41, F42).

What this recommendation still needs from step 6 (criterion recorded in `audit/ISSUE.md` before any
review): a blinded two-reviewer review drawn from the held-out runs, stratified by whether G and X
disagree, showing that X's error rate is lower than G's with a paired 95% interval that excludes zero.
Until then the audit shows that X fixes every fixture-level defect and changes 8.34% of verdicts, not
that it makes fewer errors on real responses; spot checks found replacement errors in its
approximations of `format:quotes` (prime marks read as quotes) and `format:quote_unquote` (what counts
as an explanation).

## 3. Findings

Every counterexample reproduces from W in Git Bash with

    NLTK_DATA=case/deps/nltk_data PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe audit/repro.py <ID>

which prints, for each input, `grader` (G), `grader_int` (Gi), `reference` (R) and the contract's
label (output of `repro.py all` in `audit/out/repro_all.txt`). Inputs are given as Python string
literals; `key=K` means the kwargs and prompt of dataset row K. "Panel share" is the number of panel
items in that check where Gi and XG disagree (defects only), out of the check's items, unless stated.
"Reference" is the status in R at 1c40f0c.

### Pipeline and inputs

| ID | Stage | Counterexample / evidence | Grader verdict | Contract | Panel share | Reference |
|---|---|---|---|---|---|---|
| F01 | `repeat:repeat_span`, `words:keywords_specific_position` (kwargs types) | `repeat:repeat_span` key=284, response `'code and theory behind'`; `words:keywords_specific_position` kwargs `{"keyword": "giggle", "n": 2.0, "m": 3.0}`, response `'I sat. Then we giggle loudly.'` | `EXC:TypeError` both (float used as a slice index / list index); `grader.py` does not catch it | a verdict for every item (both are passes under the contract) | 1,067 of 78,432 items get no verdict (911/912 repeat_span, 156/912 keywords_specific_position); no score change on this panel because no response passes either check under R | Same code; avoided only because R's own JSONL stores these kwargs as int |
| F39 | dataset load | `grep -n load_dataset case/grader/IFBench/eval_instruct.py` shows `load_dataset("allenai/IFBench_test", split="train")` with no `revision` | n/a | dataset revision pinned (2e8a48de...) | every item | R reads a bundled JSONL (pinned by commit) |
| F40 | NLTK data | `grep -n "_nltk_data_dir\|setdefault\|nltk.download" case/grader/IFBench/instructions.py case/grader/IFBench/instructions_util.py`: import creates `<package>/.nltk_data`, puts it first on `nltk.data.path`, and downloads any missing resource at the latest version | n/a | every grader dependency pinned | every check that uses NLTK (sentences, words, POS, stop words) | Same code |
| F41 | metric documentation | `grep -n "directly comparable\|PRIMARY_METRIC" case/grader/IFBench/eval_instruct.py` vs `case/reference/IFBench/README.md` ("we generally report the prompt-level loose accuracy") | docstring claims scores are "directly comparable to the IFBench paper's" while the primary metric is strict | a reported score names its grading mode | n/a | n/a |
| F42 | loose transform (`grader.py`) | `format:sub-bullets` loose, `'* Apples\n* Pears'`; `format:no_whitespace` loose, `'Sure!\nabc'`; `words:start_verb` loose, `'Here is my answer:\nImagine a world of peace.'` | pass, pass, pass | the whole graded text is graded; deleting a line or every `*` is not allowed except as markup (G8) | 3,666 loose-only passes; `format:sub-bullets` loose passes 1,737 of 2,736 items that strict fails (deleting every `*` leaves no bullet, which the checker passes) | Same code |
| F43 | extraction | `Qwen__Qwen3-8B__thinking/greedy.jsonl` line 9 (key 8): `<think>` without `</think>`, 8,192 tokens, `response` = whole completion; `count:conjunctions` | pass (G and R) | G1: unclosed reasoning fails every check, counted separately | 136 responses, 45 check passes; -3.22 / -0.67 points for the two thinking configurations | No extraction code (README says to strip reasoning) |

Commands for F39-F41 are the `grep` lines shown; F42 and F43 run with `audit/repro.py F42` and
`audit/repro.py F43`.

### Checkers that R fixed (grader only)

| ID | Check | Exact input | G | Contract | Panel share | Reference |
|---|---|---|---|---|---|---|
| F02 | `repeat:repeat_span` | key=284: `'code and theory behind'` (words 3-6 of the request) and `'lain'` (characters 3-6) | with int kwargs: `False` and `True` (character slice) | indices are word indices, 0-based, "split by whitespace" | 0 on this panel (no response copies a span); measured by repeat_span items whose response equals the word span | Fixed (word indices) |
| F03 | `count:keywords_multiple` | key=2 (door, bread, blue, lamp, river), `'The door was blue. Bread and bread again. Blue sky, blue sea. lamp lamp lamp lamp lamp. river river river river river river river. We stood in the doorway.'`; and the same text with `The door was blue.` replaced by `The outdoor wall was blue.` and no doorway sentence | `False`, `True` (substring count) | G6: whole-word matches | 1 of 1,140 | Fixed |
| F04 | `ratio:sentence_words` | `'Cats nap. Cats nap. Cats nap.'` | `True` | "using all different words" | 1 of 1,596 | Fixed |
| F05 | `words:words_position` | kwargs `{"keyword": "vibrant"}`, `'Truly, vibrant cities have vibrant streets.'` | `False` (the comma is token 2) | G3: punctuation is not a word | 4 of 684 | Fixed |
| F06 | `custom:sentence_alphabet` | key=282, the 26 sentences of `ALPHA26` in `audit/tests/fixtures_data.py` joined by spaces, with sentence 3 written `"Cats chased crows."` (in straight quotation marks) | `False` (first character `"`) | first word of each sentence starts with the next letter | 23 of 228 | Fixed for ASCII punctuation; a typographic quote still fails |

### Checkers with the same defect in R

| ID | Check | Exact input | G | Contract | Panel share |
|---|---|---|---|---|---|
| F07 | `format:title_case` | `'The Lord of the Rings Is a Great Book'`; `"Don't Stop Believing"` | `False`, `False` | only major words must be capitalized; `n't` is not a word | 18 of 912 |
| F08 | `format:sub-bullets` | `'Plain text without bullets.'`; `'* **Fruit**\n  - Apple\n* Veg\n  - Leek'`; `'* A well-known fruit\n* A self-made veg'` | `True`, `False`, `True` (splits on every `*`, looks for any `-`) | at least one `*` bullet, each followed by a `-` sub-bullet line | 1,113 of 2,736 |
| F09 | `format:list` | kwargs `{"sep": "-"}`, `'A well-known, state-of-the-art plan.'`; kwargs `{"sep": "SEPARATOR"}`, `'* SEPARATOR apples\n* SEPARATOR pears'` | `True`, `True` (two occurrences anywhere) | a list whose items are marked by SEP, no other bullet marker | 158 of 2,052 |
| F10 | `format:output_template` | `'My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]'`; `'Future Outlook: It will grow. My Conclusion: It matters. My Answer: It is vast.'` | `True`, `True` (labels present anywhere) | starts with `My Answer:`, labels in order, placeholders replaced | 88 of 912 |
| F11 | `format:thesis` | `'Cats purr a lot. <i>Cats are the best pets.</i> More text.'`; `'## One\n<i>Thesis one.</i> Text.\n## Two\nNo thesis here.'`; `'<i>Cats rule.</i>'` vs `'<em>Cats rule.</em>'` | `True`, `True`; `False` vs `True` | every section begins with an italic statement; `<i>` and `<em>` are equivalent | 255 of 2,052 |
| F12 | `count:punctuation` | `'Wait?! Really; yes: go, now. Why? Stop!'` | `True` (checks only `. , ! ? ; :` and `?!`) | every standard mark, including apostrophe, quotation marks, hyphen/dash, parentheses | 267 of 1,368; 179 of the 267 grader passes lack an apostrophe, quotation mark, parentheses or any hyphen/dash, which no reading of "every standard punctuation mark" allows; the other 88 lack only brackets, braces or an ellipsis (D-punct-set) |
| F13 | `count:conjunctions` | kwargs `{"small_n": 3.0}`, `'I came and saw. And I stayed and, sadly, left.'` | `True` (`and`, `And`, `and,` counted as three) | distinct conjunctions | 188 of 1,596 |
| F14 | `count:pronouns` | kwargs `{"N": 5.0}`, `'This book and that pen sit on each desk, with all chairs and some tables.'` | `True` (five determiners counted) | determiner uses are not pronouns under either D-pronoun-set reading | not separable on the panel (the replacement's grader-reading switch reuses the grader's counter); inside the 419 D-pronoun-set differences |
| F15 | `count:numbers` | kwargs `{"N": 2.0}`, `'It takes 5-7 days.'` | `False` (`5-7` becomes `57`) | a range has two numbers | 5 of 1,824 |
| F16 | `count:unique_word_count` | kwargs `{"N": 5.0}`, `'Red green blue yellow - red'`; `'\u201cRed\u201d red green blue yellow'` | `True`, `True` (empty string and `“red”` counted as words) | 4 distinct words | 12 of 2,052 |
| F17 | `count:words_japanese` | kwargs `{"N": 2.0}`, `'Hello 2024 good \u65e5\u672c'`; `'Hello - \u4e16\u754c good \u65e5\u672c'` | `True` (numerals exempt), `False` (`-` takes position 2) | every Nth word is Japanese; `-` is not a word | 34 of 1,140 |
| F18 | `custom:character_reverse`, `custom:word_reverse` | key=273, `'The national symbol of the US is the elgae dlab.'`; key=283, `'The national symbol of the US is the eagle bald.'` | `True`, `True` | the sentence itself is reversed | 0 of 228 and 4 of 228 |
| F19 | `custom:european_capitals_sort` | key=278, `'Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb'`, and the same list without `Kyiv, ` | `False`, `True` (expected list omits Kyiv, 50.45 N) | all European capitals north of 45 N | 0 of 228 (no response passes either way) |
| F20 | `custom:reverse_newline` | key=281, `'\n'.join(['Zimbabwe'] * 52)` | `True` | the lines are the countries of Africa | 6 of 228 |
| F21 | `custom:csv_special_character` | key=276, `CSV_SPECIAL_SHORT_ROWS`: `'ProductID,Category,Brand,Price,Stock\n1,"Tools & Hardware",Acme,9.99,5\n2,Tools,Brand2\n'` ... `'14,Tools,Brand14'` (rows 2-14 have 3 fields) | `True` (returns at the first special field, before checking later rows) | 14 data rows of 5 fields | 0 of 228 |
| F22 | `custom:csv_quotes` | key=275, `'"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t\t"A"\t"Fall"\t"91"\n"2"\t"Math"\t"B"\t"Fall"\t"82"\n"3"\t"Art"\t"C"\t"Fall"\t"73"'` | `EXC:IndexError` (empty field) | fail (a field is not quoted) | 0 of 228 |
| F23 | `custom:date_format_list` | key=277, `'1796-00-12, 1805-12-00'` | `True` | valid calendar dates | 0 of 228 |
| F24 | `custom:mcq_count_length` | key=279, `MCQ_NO_NUMBER` in `audit/tests/fixtures_data.py` (four questions labeled `Question:` without a number, 5 options each, stems getting longer) | `False` (split needs `Question <digit>`) | each question starts with the label "Question" | 29 of 228 |
| F25 | `format:emoji` | `'Count 1\ufe0f\u20e3. Then 2\ufe0f\u20e3.'`; `'Hello \U0001F1FA\U0001F1F8. Bye \U0001F1FA\U0001F1F8.'` | `False`, `False` (keycap and flag emoji checked per code point) | Unicode emoji count | 58 of 2,052 |
| F26 | `format:line_indent` | `'A\n\tB\n\t\tC'`; `'A\n B\n\n\n  C'` | `False`, `False` (only spaces count; removing items while iterating leaves a blank line) | indentation strictly increases over non-empty lines | 2 of 2,052 |
| F27 | `format:newline` | `'Hello world\n \nagain'` | `True` (a whitespace-only line offsets the two-word line) | one word per line | 11 of 1,368 |
| F28 | `format:no_bullets_bullets` | `'This is one. This is two.\n\n* first\n\n* second'`; `'This is one. This is two.\n* first\n* second\n'`; `'Why not? Because!\n* first\n* second'` | `False`, `False`, `True` | two sentences ending in a period, then two `*` bullets | 172 of 1,140 (+190 from D-nobullets-order) |
| F29 | `format:options` | key=102, `'c)\n'`; key=100, `'Yes\n'` | `False`, `False` (trailing newline) | surrounding whitespace ignored | 0 of 1,368 |
| F31 | `format:quote_unquote` | `'"Apple", "Banana", and "Cherry" are fruits.'`; `'He said \u201chello\u201d'` | `True`, `True` | every quoted phrase followed by an unquoted explanation | 171 of 1,140 (the replacement approximates "explanation" as two or more words; not reviewed) |
| F32 | `format:quotes` | `'He said, \u201cShe told me, \u2018He yelled \u201cstop\u201d loudly\u2019 today\u201d again.'` | `False` (typographic quotes ignored; apostrophes count as quotes) | 3 alternating levels | 269 of 1,824 (208 are grader passes; the replacement also misreads prime marks) |
| F33 | `ratio:sentence_balance`, `ratio:sentence_type` | `'Rain falls \U0001F600'`; `'Wow! Amazing!'`; `'He said "go." She said "stop." Why?'` | `True`, `True` (0 = 0), `False` (`."` not counted) | ratios need the counted types present; a sentence ending `."` is declarative | 8 of 1,596 and 20 of 1,368 |
| F34 | `repeat:repeat_change` | key=60, `'Write a python program to implement a simple JPEG compression algorithm without  any errors.'` (first word unchanged, one doubled space) | `True` | the first word changed | 0 of 684 |
| F35 | `sentence:alliteration_increment` | `'Big bears bite fish. Red roses and tall trees grow.'` | `True` (sums runs: 3, then 2 + 2) | longest run must grow (3, then 2) | 120 of 1,140 |
| F36 | typographic punctuation as words | `sentence:increment` `{"small_n": 2.0}` `'Cats nap. Cats nap \u2014 all day.'`; `words:alphabet` `'Apples bake \u2014 carefully daily.'`; `words:consonants` `'Strong stars \u2014 bright.'`; `words:no_consecutive` `'\u201cCats\u201d \u201clike\u201d mice.'`; `words:prime_lengths` `'We don\u2019t go.'`; `words:repeats` `{"small_n": 2.0}` `'Cats nap \u2014 dogs run \u2014 birds fly \u2014 fish swim.'`; `words:odd_even_syllables` `'Cat apple \u2014 dog.'` | `False`, `False`, `False`, `False`, `True`, `False`, `False` | G3: `—`, `“`, `’` are not letters | no_consecutive 3, prime_lengths 2; 0 in the others |
| F37 | `words:paragraph_last_first` | `'Time, they say, heals all wounds over time.'` | `False` (`time,` vs `time`) | first and last word compared without punctuation | 29 of 1,368 |
| F38 | `words:odd_even_syllables` | `'Cat naive dog.'` | `False` (syllapy counts `naive` as 1) | syllables by pronunciation (na-ive) | not measured (the replacement uses syllapy too) |

F30 was withdrawn: the fixture `'((((( x )'` (four brackets never closed) is a decision (D-paren-closed),
because R's own unit test asserts a pass for a string whose outer brackets never close.

Property tests (step 4) applied each contract-ignored edit to every passing fixture: a trailing
newline flips `format:no_bullets_bullets`, `format:no_whitespace` (D-trailing-ws) and `format:options`
(F28, F29); typographic quotes flip `format:quotes` (F32); an inserted em dash flips five word checks
(F36); bolding the first word flips `words:start_verb`, `words:words_position` and
`words:paragraph_last_first` (D-markup). 15 of 199 edited cases flip (`audit/out/property_results.tsv`).

## 4. Decision entries

For the maintainers. "Proposed" is the contract's reading. "Panel" is the number of item verdicts that
change when the replacement switches from the grader's reading to the proposed one (XG vs X, which
also includes G1 on the 136 extraction failures); 0 means no grader difference was observed there.

| Entry | Reading A (proposed) | Reading B | Example (fixture) | G takes | Panel |
|---|---|---|---|---|---|
| D-empty | empty or whitespace-only text fails every check | vacuous checks pass | `''` for `format:no_whitespace` | A in strict mode (R's unit test asserts `QuoteExplanationChecker.check_following("")` is True) | 0 |
| D-word | words = whitespace tokens with non-alphanumeric edges stripped; `don't`, `well-known` one word; list labels not words | `\w+` runs (`don`, `t`) | `count:word_count_range` 3-3, `"Don't stop now."` | B | 144 (word_count_range), 35 (stop_words) |
| D-sentence | a line without terminal punctuation (heading, list item) is its own sentence | punkt only, so a heading joins the next sentence | `sentence:keyword` giraffe N=2, `'Title\nI like cats. A giraffe is tall.'` | B | 137 keyword, 40 balance, 19 type, 35 increment, 9 alliteration, 6 emoji |
| D-paragraph | paragraphs separated by blank lines | any newline | `words:vowel`, `'A cat sat.\nA rat ate.'` | B | 0 |
| D-markup | Markdown markup ignored for labels, options, first words | markup is literal text | `words:start_verb`, `'**Imagine** a world of peace.'` | B | 21 start_verb, 9 output_template, 7 mcq |
| D-conj-usage | only coordinating uses of for/so/yet count | any occurrence | `'This gift is for you, so big and bright.'` (small_n 3) | B | 321 |
| D-pronoun-set | personal, possessive, reflexive pronouns | also demonstrative, relative, interrogative, indefinite | `'Someone saw this; everyone knew who did that, and nobody spoke.'` (N 5) | B (and counts determiner uses, F14) | 419 |
| D-punct-set | English marks (. , ? ! : ; ' " - — ( ) [ ] { } …) plus ?! | every ASCII punctuation character | `count:punctuation` | neither (6 marks, F12) | in F12 |
| D-csv-payload | a fenced or prose-wrapped CSV block is the payload | the whole response must be CSV | `custom:csv_city`, `'Here is the data:\n```csv\n...\n```'` | B | 91 csv_city, 43 csv_quotes, 97 csv_special_character |
| D-custom-content | format only (dates need not be historically right) | historical range checked | `'1900-01-01, 1901-02-02'` | B (years 1769-1821) | 1 |
| D-list-extra | no extra text in custom lists | words allowed if no other numbers / intro lines before the list | `custom:multiples`, `'Multiples: 14 21 28 35 42 49 done'` | B | 0 |
| D-list-labels | list labels ignored in `custom:reverse_newline` | labels are part of the line | numbered 54-country list | B | 0 |
| D-africa-set | all 54 African UN members | order and one-per-line only | R's unit test list (52 countries, Ethiopia and Gambia missing, intro line) | B (>= 52 lines from Zimbabwe on) | 0 |
| D-reverse-extra | added unreversed text fails | a reversed fragment anywhere suffices | `'Here you go: .elgae dlab eht si tI'` | B | 5 character_reverse, 2 word_reverse |
| D-balance | three types present, counts within 1 | exactly equal | `'It rains. It pours. Does it? Wow!'` | B | (in the 40 above) |
| D-overlap-measure | share of the response's word trigrams found in the reference | character trigrams (G); word trigrams via `word_tokenize` (R) | reference `'the quick brown fox jumps over the lazy dog'`, 50%, response `'the quick brown fox sat down'` | character trigrams | 205 |
| D-overlap-reference | the reference text is the prompt's request | the whole prompt | prompts never label a "reference text" | A | 0 |
| D-trailing-ws | leading and trailing whitespace ignored | trailing newline counts | `format:no_whitespace`, `'Yes.\n'` | B | 15 |
| D-change-case | a case-only change of the first word is no change | accepted | `'write a python program ...'` | B | 0 |
| D-copy-case | copies are case-sensitive | case-insensitive | `repeat:repeat_simple`, lower-case copy | B | 0 |
| D-palindrome-distinct | 10 distinct palindromes | 10 occurrences (R's test: `abcba` x10 passes) | `'level' x10` | B | 327 |
| D-paren-closed | nesting needs properly matched pairs | 5 opened, innermost closed (R's test string is mismatched at depth 19) | `'((((( x )'` | B | 202 |
| D-nobullets-order | other content may follow the bullets | only bullets after the first bullet | `format:no_bullets_bullets` | B (also fails blank lines, F28) | 190 |
| D-keyword-match, D-count-exact, D-number, D-name-usage, D-unique, D-between, D-japanese-script, D-csv-rowcount, D-csv-header-quotes, D-csv-special, D-capitals-set, D-mcq-length, D-mcq-answer, D-emoji-def, D-indent, D-list-sep, D-options-extra, D-template-brackets, D-quote-chars, D-subbullet-indent, D-section, D-title-minor, D-ratio-exact, D-char-count, D-different-words, D-stopword-list, D-repeat-trailing, D-repeat-simple-target, D-span-extra, D-alliteration, D-consonant-y, D-syllable, D-repeat-count, D-vowel, D-vacuous | readings in `audit/CONTRACTS.md` | | | G agrees with the proposed reading on the fixtures, or the difference is a finding | 0 |

## 5. Panel (step 5)

Stored responses only (`case/panel/`, 16 configurations, 228 run files, 68,400 responses); nothing was
generated. Summary tables: `audit/out/step5_summary.md`; per-item verdicts: `audit/out/panel/*.tsv`.

### 5.1 What the stored records show

- `response` equals the CONFIGS.md extraction rule on all 68,400 lines; keys and prompts match the
  dataset order on every line.
- Truncated (`finish_reason == length`): 4,165 responses (6.1%); per configuration from 53 of 900
  (Qwen3-14B, thinking on) and 78 of 3,900 (OLMo-2-0325-32B) to 695 of 5,100 (Qwen3-8B, thinking off).
- Unclosed reasoning: 136 (Qwen3-8B thinking 104, Qwen3-14B thinking 32), all truncated at 8,192 tokens;
  1 non-thinking Qwen3-32B response contains `</think>` without `<think>` (graded after it).
- Empty responses: 37 (Qwen3-14B 28, Qwen3-8B 5, marin-8b 4); every grader fails them.

### 5.2 Graders and coverage

- R's in-process verdicts equal its `run_eval.py` output row for row (marin-8b greedy, 300 of 300; run
  with `PYTHONUTF8=1`, because `run_eval.py` opens files in the locale encoding and fails on Windows).
- Scored coverage: G 98.640% (77,365 of 78,432), Gi, R, X, XG 100%.
- Per-check pass rates and disagreements: `audit/out/step5_summary.md`, "Per check". Largest G vs R
  differences: `repeat:repeat_span` 911 and `words:keywords_specific_position` 156 (F01),
  `ratio:overlap` 227 (D-overlap-measure), `custom:sentence_alphabet` 23 (F06).

### 5.3 Reruns

`bi_greedy` and `bi_greedy_shuffled` (batch-invariant process) give identical scores in every
configuration; ordinary greedy reruns differ by up to 1.33 points, so batch composition alone moves a
greedy score by about a point. Sampled runs: standard deviation 0.84-2.08 points.

### 5.4 Spot checks of Gi vs XG disagreements

`audit/scripts/spotcheck.py <check> <n>` prints short excerpts. In the samples read: sub-bullets (bold or
italic asterisks inside bullets fail G; top-level `-` bullets with italic `*` pass G), emoji (flag emoji
after a sentence), alliteration (run sums), mcq (`Question:` without a number), quotes (apostrophes give
G false depth) — the replacement was right; quotes also showed a replacement false pass from prime
marks (`T'`), and quote_unquote and output_template differences depend on the replacement's reading of
"explanation" and "each label once". These are not a review; step 6 is what would measure them.

## 6. Step 4 details

- Reference comparison: fixture verdicts of R in `audit/out/fixture_results.tsv`; R differs from the
  contract on 77 of 215 fixtures (the shared defects plus decisions).
- R's unit tests (`audit/scripts/run_ref_tests.py --target <t>`; 65 tests, 177 assertions, every
  assertion recorded): R passes all; G fails 6 assertions (lines 1199, 1201, 1224, 1238, 1247, 1255 of
  `instructions_test.py`: the tests R added for F02-F06); X fails 8 assertions, each contradicted by the
  contract: line 1007 (expected capitals without Kyiv, F19), 252 (`. , ! ? ; : !?` counted as every
  punctuation mark, F12), 275 (mismatched brackets, D-paren-closed), 235 (`abcba` x10, D-palindrome-
  distinct), 594 (`Sure! Here it is: 14,...`, D-list-extra), 942 (intro line and 52 of 54 countries,
  D-list-extra and D-africa-set), 1164 (`check_following("")` True, D-empty), 193 (one paragraph with
  a line break counted as two, D-paragraph).
- Fuzzing (`audit/scripts/step4_fuzz_contentfree.py`, seed 10060, 120 texts x 344 (row, check) pairs x 3
  implementations): exceptions only in G — `repeat:repeat_span` 480 of 480, `words:keywords_specific_
  position` 240 of 480 (F01). Gi and R raised nothing on fuzz input; the `custom:csv_quotes`
  `IndexError` (F22) needs a well-formed header and an empty field, shown by fixture. An exception
  propagates out of `grader.py`; whether it stops a run depends on Evalchemy code not in the case (U5).
- Content-free responses (Gi, 344 pairs each): empty and whitespace pass 0; `the` x50 passes 95
  (vacuous under G7 for line_indent, quote_unquote, single-sentence checks; also sub-bullets 12 (F08),
  sentence_balance 7 and sentence_type 6 (F33)); `This is a sentence.` x20 passes 51; restating the
  prompt passes 50 (person_names 6 because the prompt lists the names, output_template 4 because it
  contains the template (F10), sub-bullets 11); restating the prompt's last sentence passes 68
  (`audit/out/contentfree.tsv`).
- Loose grading: `audit/tests/test_loose.py` (6 strict-xfail cases, F42).

## 7. Step 6

Not run: no reviewers were available. No sample was drawn, frozen or rendered. The recommendation
still needs the review described in section 2, drawn from the held-out runs listed in
`audit/ISSUE.md`, with the stratum population sizes recorded and the case list hashed before review.

## 8. Inputs, unverified inputs and skipped steps

Pinned inputs are in `audit/ISSUE.md` (manifest check, grader file hashes, reference commit, dataset
revision with per-row hashes, prompt rendering, extraction rule, generation settings, lockfile, NLTK
data hash). Unverified: U1 grader source commit; U2 vLLM version of the two thinking configurations;
U3 NLTK data package versions; U4 the evaluation run's own grading records; U5 the Evalchemy/Marin
code between generation and `grader.py` (extraction, kwargs types, exception handling, reducer). Each
lists its location and verifying command in `audit/ISSUE.md`.

Skipped because this exercise has no infrastructure for them: no issue tracker (`file-issue`; the
record is `audit/ISSUE.md`), no repository or research branch (`research-engineering`, `manage-pr`;
fixtures are runnable tests under `audit/tests/` with strict xfail marks, scripts under
`audit/scripts/`), no Hugging Face dataset for frozen samples (frozen files under `audit/frozen/` with
sha256 in `audit/ISSUE.md`), no compute or job launcher (`use-iris`; the panel is the stored
responses), no reviewers (step 6), and `docs/dev-guide/writing-style/issues.md` was not available.
`skill/references/ifbench.md` and `validation.md` were not provided; the loose-grading test follows
step 4's text instead of ifbench.md section 4.

## 9. Files

- `audit/ISSUE.md` — record: progress, pins, contract hash, held-out set, step-6 criterion, entries.
- `audit/CONTRACTS.md`, `audit/frozen/CONTRACTS_v1.md` — contracts (same hash).
- `audit/tests/` — `fixtures_data.py` (215 fixtures), `test_fixtures.py`, `test_properties.py`,
  `test_loose.py`, `test_replacement.py`; xfail maps `xfail.json`, `property_xfail.json`.
  Run: `NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests -q -p no:cacheprovider`.
- `audit/repro.py` — reproduces every finding.
- `audit/replacement/grader.py` — replacement grader, switches in `SWITCHES`.
- `audit/lib/harness.py` — grades one response with G, Gi or R (imports verified copies in `audit/work/`).
- `audit/scripts/` — pipeline scripts named by step; `audit/out/` — results.
