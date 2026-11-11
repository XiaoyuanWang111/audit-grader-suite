# IFBench grader audit: Marin's vendored Evalchemy copy

Grader under audit: `case/grader/IFBench/` (58 instruction checkers, strict and loose harness). Reference: allenai/IFBench at 1c40f0c (`case/reference/IFBench/`). Data: allenai/IFBench_test at 2e8a48d, 300 prompts, 344 (prompt, instruction) items. Panel: the 68,400 stored responses in `case/panel/` (16 configurations, 228 runs), 78,432 instruction verdicts per grader.

## Summary

**Error rate: not estimated.** Step 6 (blinded review) was not run in this exercise, so no error rate with an interval exists for the grader or for the replacement. What the panel does show:

- Fixing the 30 checker findings one at a time in the grader's own code changes **at least 2,596 of 78,432 strict instruction verdicts (3.3%)**, and the grader passes 45 of the 157 verdicts on thinking responses whose reasoning never closed (finding F33). These are lower bounds on the grader's error: they exclude the decision entries, and some findings have no minimal fix to measure.
- The grader and the replacement grader (built from the contracts, proposal reading of every decision) disagree on **6,777 verdicts (8.6%)**: 3,945 grader passes the replacement fails, 2,832 the other way. Setting the replacement's switches to the grader's readings of the modelled decisions leaves **4,703 disagreements (6.0%)**; the 2,074 difference is the effect of the decision entries. The replacement's own error rate is unmeasured, so these counts mix grader errors with replacement errors.
- **Effect on scores** (strict prompt-level accuracy, mean over each configuration's runs): replacement minus grader ranges from **-4.4 points (Qwen2.5-14B-Instruct) to +2.9 points (Qwen3-14B thinking)**. An identical-settings rerun (`greedy_repeat` minus `greedy`) moves a configuration's grader score by at most 1.3 points; one sampled run has a standard deviation of 0.8 to 2.1 points. Nine of 16 configurations move by more than 1.5 points, and the ranking changes (for example Qwen2.5-14B falls from 3rd to 5th, Qwen2.5-7B from 7th to 10th, phi-4 rises from 14th to 12th).
- Pooled over all 228 runs: grader 24.92% prompt-level / 27.68% instruction-level; reference 25.00 / 27.59; replacement 24.01 / 26.26. Loose grading adds 4.0 points (28.95 / 32.35); 2,609 of its 3,666 extra passes are responses the contract fails (F32).
- The vendored grader is an older copy of AI2's code: the reference fixes 5 of the findings (F01, F02, F03, F29, F30) and switches `ratio:overlap` from character to word trigrams. Grader and reference disagree on 257 panel verdicts (0.33%). The remaining 25 checker findings are in the reference too.
- No grader exception occurred on the panel. Fuzzing (17,400 inputs) and fixtures found two inputs that raise in `custom:csv_city` and `custom:csv_quotes`; the harness has no exception handler, so one such response stops the whole run (F18, F31).

**Recommendation: fix the grader**, provisionally. Replace the vendored copy with the reference at 1c40f0c or later, fix the 25 checker findings still present there and the harness findings F31 to F36, and have the maintainers settle the decision table. Adopting `audit/scripts/replacement.py` as the fix needs step 6 first (see the last section). Replacing the benchmark is not indicated: every finding has a code fix, and the ambiguous instructions are decisions, not defects.

## How to reproduce

All commands run in Git Bash from `W = <W>`:

```
cd <W>
export NLTK_DATA=$PWD/case/deps/nltk_data PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe audit/scripts/setup_run_copies.py   # byte-identical copies under audit/run/, checked against the MANIFEST
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests   # 591 passed, 74 xfailed
.venv/Scripts/python.exe audit/scripts/repro.py              # every counterexample below; ends "all reported verdicts reproduced"
.venv/Scripts/python.exe audit/scripts/verify_report.py       # runs every command quoted in this report; ends "43 commands checked, 0 failed"
```

`audit/scripts/probe.py <instruction_id> '<kwargs JSON>' '<response JSON string>'` grades one response with all five graders; the response is a JSON string literal, so `\n`, `\t` and `\uXXXX` are exact characters. `audit/scripts/repro.py <ID>` prints one case's verdicts and its exact kwargs and response as JSON. The graders run from copies because both packages create `<package>/.nltk_data` on import; `audit/scripts/graders.py` blocks `nltk.download`.

## Findings

Each finding gives the check or stage, the counterexample (an exact input), the command that reproduces the grader's verdict, the contract clause it breaks (`audit/CONTRACTS.md`), the panel verdicts it changes, and its status in the reference. "Changed" counts the panel's strict verdicts that the minimal fix flips, out of that check's panel verdicts (`audit/scripts/finding_shares.py`, output `audit/work/finding_shares.txt`). Fixture ids are in `audit/tests/xfail_grader.json` under the finding id.

### Checker findings

**F01 `repeat:repeat_span` uses character indices.** The instruction says "the indices are word indices, split by whitespace!", but the grader slices characters. For key 287 it expects `d w`.
- Input: kwargs `{"prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. ", "n_start": 10, "n_end": 12}`, response `"d w"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py repeat:repeat_span '{"prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. ", "n_start": 10, "n_end": 12}' '"d w"'` prints `grader_strict: True`. The word span `"on a certain"` prints `grader_strict: False` (case F01b).
- Contract: repeat:repeat_span (word tokens n_start..n_end). Wrong under both readings of D-span-base.
- Panel: all 912 verdicts (4 prompts) are graded against a wrong target; 0 changed, because no response contains the word span either. Reference: fixed.

**F02 `ratio:sentence_words` never checks "using all different words".**
- Input: kwargs `{}`, response `"Cats nap daily. Dogs nap often. Fish swim fast."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py ratio:sentence_words '{}' '"Cats nap daily. Dogs nap often. Fish swim fast."'` prints `grader_strict: True`.
- Contract: ratio:sentence_words ("nap" occurs in two sentences). Panel: 1 of 1,596 changed. Reference: fixed.

**F03 `count:keywords_multiple` counts substrings.** "throughout" counts as "through".
- Input: kwargs `{"keyword1": "quickly", "keyword2": "transform", "keyword3": "abundant", "keyword4": "bridge", "keyword5": "through"}`, response `"quickly. transform transform. abundant abundant abundant. bridge bridge bridge bridge bridge. through through through through through through throughout."` (6 whole-word "through").
- `.venv/Scripts/python.exe audit/scripts/repro.py F03` prints `grader_strict=True`.
- Contract: G5 (whole words); the substring reading of D-keyword-form covers inflections, not a keyword inside another word. Panel: 1 of 1,140 changed. Reference: fixed.

**F04 `count:conjunctions` deduplicates raw tokens.** `and,`, `And` and `and.` count as three different conjunctions.
- Input: kwargs `{"small_n": 3}`, response `"Tea and, And coffee and."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py count:conjunctions '{"small_n": 3}' '"Tea and, And coffee and."'` prints `grader_strict: True`.
- Contract: count:conjunctions (distinct words; one conjunction here). Panel: 188 of 1,596 changed (11.8%), all false passes. Reference: same defect.

**F05 `ratio:sentence_type` and `ratio:sentence_balance` pass when no sentence has the counted types** (0 = 2 x 0; 0 = 0 = 0).
- Inputs: `ratio:sentence_type` with response `"Wow! Amazing!"`; `ratio:sentence_balance` with response `"hello there"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py ratio:sentence_type '{}' '"Wow! Amazing!"'` prints `grader_strict: True`; `.venv/Scripts/python.exe audit/scripts/probe.py ratio:sentence_balance '{}' '"hello there"'` prints `grader_strict: True`.
- Contract: ratio:sentence_type (#interrogative >= 1), ratio:sentence_balance (all three types occur). Panel: sentence_type 0 of 1,368, sentence_balance 8 of 1,596 changed. Reference: same defect.

**F06 `sentence:alliteration_increment` sums alliterative words over separate runs** instead of measuring the longest run of consecutive alliterative words.
- Input: kwargs `{}`, response `"Silly snakes slither. Big bad dogs dig."` (longest runs 3 then 2; the grader scores 3 then 4).
- `.venv/Scripts/python.exe audit/scripts/probe.py sentence:alliteration_increment '{}' '"Silly snakes slither. Big bad dogs dig."'` prints `grader_strict: True`.
- Contract: sentence:alliteration_increment ("a longer sequence of consecutive alliterative words"). Panel: 120 of 1,140 changed (10.5%): 114 false passes, 6 false fails. Reference: same defect.

**F07 `format:newline` counts whitespace-only lines as lines,** so a blank line of spaces offsets a line with two words.
- Input: kwargs `{}`, response `"Hello world\n \nfoo"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:newline '{}' '"Hello world\n \nfoo"'` prints `grader_strict: True`.
- Contract: format:newline (every non-empty line holds one word). Panel: 5 of 1,368 changed. Reference: same defect.

**F08 `format:line_indent` measures only spaces;** tab indentation counts as zero.
- Input: kwargs `{}`, response `"a\n\tb\n\t\tc"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:line_indent '{}' '"a\n\tb\n\t\tc"'` prints `grader_strict: False`.
- Contract: format:line_indent (leading whitespace strictly increases). Panel: 1 of 2,052 changed. Reference: same defect. (The checker also removes items from the list it is iterating, so two consecutive blank lines fail while one passes; that is filed under D-indent-blank.)

**F09 `format:quote_unquote` ignores typographic quotes and accepts punctuation as the explanation.**
- Inputs: response `"He said \u201ccarpe diem\u201d."` (curly quotes, nothing after the quote); response `"\"A\". \"B\" means b."` (only a period after `"A"`).
- `.venv/Scripts/python.exe audit/scripts/probe.py format:quote_unquote '{}' '"He said \u201ccarpe diem\u201d."'` prints `grader_strict: True`; `.venv/Scripts/python.exe audit/scripts/probe.py format:quote_unquote '{}' '"\"A\". \"B\" means b."'` prints `grader_strict: True`.
- Contract: format:quote_unquote. A curly-quoted phrase is a quoted phrase under both readings of D-typographic. Panel: 58 of 1,140 changed (5.1%). Reference: same defect.

**F10 `format:list` counts the separator anywhere in the text.** With `sep` = `-`, two hyphens inside words pass.
- Input: kwargs `{"sep": "-"}`, response `"I am well-known and up-to-date."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:list '{"sep": "-"}' '"I am well-known and up-to-date."'` prints `grader_strict: True`.
- Contract: format:list (items start with sep). Not a list under either reading of D-list-inline. Panel: 459 of 2,052 changed (22.4%), all false passes. Reference: same defect.

**F11 `format:thesis` checks only the first italic span,** not that each section begins with one.
- Input: kwargs `{}`, response `"## A\n<i>Thesis one.</i> Body.\n\n## B\nNo thesis here."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:thesis '{}' '"## A\n<i>Thesis one.</i> Body.\n\n## B\nNo thesis here."'` prints `grader_strict: True`.
- Contract: format:thesis; section B has no thesis under both readings of D-section. Panel: 254 of 2,052 grader passes fail under both section readings (12.4%). Reference: same defect.

**F12 `format:sub-bullets` passes without any `*` bullet and fails on bold markup.** It splits the text on every `*`.
- Inputs: response `"Hello world."`; response `"* **Bold** point\n  - detail"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:sub-bullets '{}' '"Hello world."'` prints `grader_strict: True`; `.venv/Scripts/python.exe audit/scripts/probe.py format:sub-bullets '{}' '"* **Bold** point\n  - detail"'` prints `grader_strict: False`.
- Contract: format:sub-bullets ("must include bullet points denoted by *"; `**` is not a bullet). Panel: 833 of 2,736 changed (30.4%): 182 false passes, 651 false fails. Reference: same defect.

**F13 `format:no_bullets_bullets` does not check "ending in a period", and an empty line resets its state.**
- Inputs: response `"This is first! This is second!\n* one\n* two"`; response `"This is first.\n\nThis is second.\n* one\n* two"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:no_bullets_bullets '{}' '"This is first! This is second!\n* one\n* two"'` prints `grader_strict: True`; `.venv/Scripts/python.exe audit/scripts/probe.py format:no_bullets_bullets '{}' '"This is first.\n\nThis is second.\n* one\n* two"'` prints `grader_strict: False`.
- Contract: format:no_bullets_bullets. Panel: 159 of 1,140 changed (13.9%): 25 false passes, 134 false fails (empty lines between paragraphs or between bullets). Reference: same defect.

**F14 `custom:character_reverse` accepts any response containing "elgae dlab".**
- Input: kwargs `{}`, response `"The bald eagle (elgae dlab)."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py custom:character_reverse '{}' '"The bald eagle (elgae dlab)."'` prints `grader_strict: True`.
- Contract: custom:character_reverse (the response read backwards is the answer). Panel: 5 of 228 changed. Reference: same defect.

**F15 `custom:reverse_newline` ignores every line before the first "Zimbabwe" line and never checks that lines are countries.**
- Input: kwargs `{}`, response `"Zimbabwe\n" + "\n".join(f"Y{chr(122 - i // 26)}{chr(122 - i % 26)}" for i in range(51))` (Python; `Zimbabwe` then 51 reverse-sorted non-countries; sha256 prefix 249113cb7d85).
- `.venv/Scripts/python.exe audit/scripts/repro.py F15` prints `grader_strict=True` and the exact response.
- Contract: custom:reverse_newline; fails even under the lenient reading of D-africa-list (no completeness). Panel: 9 of 228 grader passes fail under both readings. Reference: same defect.

**F16 `custom:european_capitals_sort` omits Kyiv from its answer key.** The correct list fails and the list without Kyiv passes.
- Input: kwargs `{}`, response `"Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb"`.
- `.venv/Scripts/python.exe audit/scripts/repro.py F16` prints `grader_strict=False`.
- Contract: custom:european_capitals_sort (Kyiv, 50.45 N, is the capital of a European country under both readings of D-europe-set). Panel: 0 changed (no response passes either key). Reference: same defect; its unit test `TEST_EUROPE` encodes it.

**F17 `custom:csv_special_character` returns at the first quoted special field** without checking the field count of later rows.
- Input: kwargs `{}`, response: header `ProductID,Category,Brand,Price,Stock`, row 1 `1,"Tools & Hardware",Acme,11.99,3`, rows 2 to 14 with 5 fields except row 5 `5,Tools,Acme` (exact text: `repro.py F17`).
- `.venv/Scripts/python.exe audit/scripts/repro.py F17` prints `grader_strict=True`.
- Contract: custom:csv_special_character (14 rows of 5 fields). Panel: 0 changed. Reference: same defect.

**F18 `custom:csv_quotes` and `custom:csv_city` raise exceptions.** An unquoted empty field raises IndexError in csv_quotes; a bare carriage return raises `_csv.Error` in csv_city.
- Inputs: csv_quotes response `"\"StudentID\"\t\"Subject\"\t\"Grade\"\t\"Semester\"\t\"Score\"\n\"1\"\t\t\"A\"\t\"Fall\"\t\"95\"\n\"2\"\t\"Art\"\t\"B\"\t\"Spring\"\t\"88\"\n\"3\"\t\"Music\"\t\"A\"\t\"Fall\"\t\"91\""`; csv_city response `"a\rb"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py custom:csv_city '{}' '"a\rb"'` prints `grader_strict: ERR:Error:new-line character seen in unquoted field ...`; `.venv/Scripts/python.exe audit/scripts/repro.py F18a` prints `grader_strict=ERR:IndexError`.
- Contract: G2 (an exception is a grading failure and must not stop the run; see F31). Panel: 0 exceptions (no stored response contains a carriage return). Fuzzing: 25 csv_city exceptions in 300 inputs, strict and loose. Reference: same defect.

**F19 `custom:date_format_list` accepts month 00 and day 00.**
- Input: kwargs `{}`, response `"1796-00-00, 1796-05-10"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py custom:date_format_list '{}' '"1796-00-00, 1796-05-10"'` prints `grader_strict: True`.
- Contract: custom:date_format_list (valid dates). Panel: 0 changed. Reference: same defect.

**F20 `format:title_case` requires every word capitalized and splits contractions.** Lowercase articles and short prepositions fail, although the instruction defines title case as capitalizing "every major word"; `Doesn't` becomes `Does` + `n't`, and `n't` fails.
- Inputs: response `"War and Peace in the Valley"`; response `"It Doesn't Matter"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:title_case '{}' '"War and Peace in the Valley"'` prints `grader_strict: False`; `.venv/Scripts/python.exe audit/scripts/repro.py F20b` prints `grader_strict=False`.
- Contract: format:title_case (v2, section 9 item 1). Panel: 8 of 912 changed. Reference: same defect.

**F21 `format:output_template` only checks that the three labels occur.** Unfilled placeholders and reversed order pass.
- Inputs: response `"My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]"`; response `"Future Outlook: Z My Conclusion: Y My Answer: X"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:output_template '{}' '"My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]"'` prints `grader_strict: True`; `.venv/Scripts/python.exe audit/scripts/probe.py format:output_template '{}' '"Future Outlook: Z My Conclusion: Y My Answer: X"'` prints `grader_strict: True`.
- Contract: format:output_template. Panel: 43 of 912 grader passes fail even with prose outside the template allowed (4.7%). Reference: same defect.

**F22 `repeat:repeat_change` never checks that the first word changed.** A whitespace-only difference passes.
- Input: kwargs `{"prompt_to_repeat": "Write a python program to implement a simple JPEG compression algorithm without any errors."}`, response `"Write  a python program to implement a simple JPEG compression algorithm without any errors."` (two spaces after "Write").
- `.venv/Scripts/python.exe audit/scripts/probe.py repeat:repeat_change '{"prompt_to_repeat": "Write a python program to implement a simple JPEG compression algorithm without any errors."}' '"Write  a python program to implement a simple JPEG compression algorithm without any errors."'` prints `grader_strict: True`.
- Contract: repeat:repeat_change. Panel: 0 changed. Reference: same defect.

**F23 `format:options` compares letter options case-sensitively.**
- Input: kwargs `{"options": "a), b), c), d)"}`, response `"B)"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py format:options '{"options": "a), b), c), d)"}' '"B)"'` prints `grader_strict: False`.
- Contract: format:options (case-insensitive). Panel: 0 changed. Reference: same defect.

**F24 `format:parentheses` counts unmatched open brackets toward the depth.**
- Input: kwargs `{}`, response `"((((()"` (one matched pair).
- `.venv/Scripts/python.exe audit/scripts/probe.py format:parentheses '{}' '"((((()"'` prints `grader_strict: True`.
- Contract: format:parentheses (5 properly matched nested pairs). Panel: 201 of 1,824 changed (11.0%), all false passes. Reference: same defect; its test `TEST_NESTED_PARENTHESES_TRUE2` (20 openers, brackets mismatched after the first close) encodes it.

**F25 `words:prime_lengths` counts non-ASCII punctuation as a one-letter word.**
- Input: kwargs `{}`, response `"It is \u2014 an old oak."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py words:prime_lengths '{}' '"It is \u2014 an old oak."'` prints `grader_strict: False`.
- Contract: G3 (a token without a letter or digit is not a word). Panel: 0 changed. Reference: same defect.

**F26 `words:last_first` and `words:paragraph_last_first` compare words with punctuation attached.** `Cats,` does not match `cats`.
- Inputs: last_first response `"I like cats. Cats, they say, are great."`; paragraph_last_first response `"Open, she said, is open\nSets are sets"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py words:last_first '{}' '"I like cats. Cats, they say, are great."'` prints `grader_strict: False`; `.venv/Scripts/python.exe audit/scripts/probe.py words:paragraph_last_first '{}' '"Open, she said, is open\nSets are sets"'` prints `grader_strict: False`.
- Contract: G3, G5. Panel: last_first 35 of 1,140, paragraph_last_first 29 of 1,368 changed, all false fails. Reference: same defect.

**F27 `format:emoji` tests single code points,** so flag and keycap emoji at the end of a sentence fail.
- Input: kwargs `{}`, response `"I love the USA \ud83c\uddfa\ud83c\uddf8. It is big \ud83d\ude00."` (U+1F1FA U+1F1F8 is the US flag).
- `.venv/Scripts/python.exe audit/scripts/probe.py format:emoji '{}' '"I love the USA \ud83c\uddfa\ud83c\uddf8. It is big \ud83d\ude00."'` prints `grader_strict: False`.
- Contract: format:emoji. Panel: 27 of 2,052 changed with an emoji-sequence-aware test. Reference: same defect.

**F28 `words:start_verb` misses capitalized imperatives:** the POS tagger tags a sentence-initial `Imagine`, `Create` or `Assume` as NNP or NN.
- Input: kwargs `{}`, response `"Imagine an empire of endless pain."`.
- `.venv/Scripts/python.exe audit/scripts/probe.py words:start_verb '{}' '"Imagine an empire of endless pain."'` prints `grader_strict: False`.
- Contract: words:start_verb (a verb in its sentence under both readings of D-verb). Panel: at least 124 of 1,368 changed (9.1%, all false fails): grader fails where tagging the first token in lower case gives a verb. The replacement passes 362 more items than the grader, so the true count is likely higher; step 6 would measure it. Reference: same defect.

**F29 `custom:sentence_alphabet` fails a sentence that starts with punctuation,** such as an opening quotation mark.
- Input: kwargs `{}`, response: the 26-sentence story `"Alice walked home." Bears walked home. ... Zebras walked home.` with the first sentence in double quotes (exact text: `repro.py F29`).
- `.venv/Scripts/python.exe audit/scripts/repro.py F29` prints `grader_strict=False`.
- Contract: custom:sentence_alphabet (the first word starts with A). Panel: 23 of 228 verdicts differ from the reference, which fixed this. Reference: fixed.

**F30 `words:words_position` handles only one trailing punctuation token.**
- Input: kwargs `{"keyword": "vibrant"}`, response `"A vibrant day is vibrant today!)"`.
- `.venv/Scripts/python.exe audit/scripts/probe.py words:words_position '{"keyword": "vibrant"}' '"A vibrant day is vibrant today!)"'` prints `grader_strict: False`.
- Contract: words:words_position, G3. Panel: 5 of 684 verdicts differ from the reference. Reference: fixed.

### Harness, pipeline and input findings

**F31 One checker exception stops the run.** `grader.py` calls `check_following` with no exception handler (lines 52-53 strict, 99-103 loose), so F18's inputs propagate out of `test_instruction_following_strict`.
- `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'audit/scripts'); import graders; from IFBench import grader as g; g.test_instruction_following_strict(g.InputExample(0, ['custom:csv_city'], 'p', [{}]), {'p': 'a\rb'})"` ends with `_csv.Error: new-line character seen in unquoted field`.
- Contract: G2. Whether Evalchemy's `instructions` grader catches the exception is unverified (that code is not in the case). Reference: same (`evaluation_lib.py` has no handler either).

**F32 Loose grading passes responses that the contract fails.** It grades 8 variants (first line removed, last line removed, both, each with every `*` deleted) and keeps any pass. Deleting `*` removes all bullets, which then pass F12's vacuous check, so loose grading passes **all 2,736** `format:sub-bullets` verdicts; deleting the first line moves the "second word".
- Inputs: `format:sub-bullets` response `"* One\n* Two"` (no sub-bullets); `words:words_position` kwargs `{"keyword": "vibrant"}` response `"Here is my answer:\nA vibrant scene with vibrant colors."`.
- `.venv/Scripts/python.exe audit/scripts/repro.py L1a L1b` prints `grader_strict=False ... grader_loose=True` for both.
- Contract: G9. Panel: 3,666 loose-only passes, 2,609 of them failed by the replacement (2,609 of 78,432 verdicts, 3.3%). Reference: same transform.

**F33 Unclosed reasoning is graded as an answer.** The records' extraction rule (CONFIGS.md) grades the whole completion when it has no `</think>`, so 136 of 1,800 thinking responses (Qwen3-8B thinking 104, Qwen3-14B thinking 32) are graded with their reasoning text. The grader passes 45 of their 157 instruction verdicts. Contract: G1 (an extraction failure fails every check and is counted separately). Stored fields: `raw_response` (no `</think>`) and `run` in `case/panel/Qwen__Qwen3-*__thinking/*.jsonl`. The vendored files do not show Evalchemy's extraction, so whether the Marin run does the same is unverified.

**F34 The dataset revision is not pinned.** `case/grader/IFBench/eval_instruct.py` line 61: `load_dataset("allenai/IFBench_test", split="train")`, no `revision`. Command: `grep -n "load_dataset(" case/grader/IFBench/eval_instruct.py`.

**F35 NLTK data is not pinned.** `instructions.py` lines 26-32 create `<package>/.nltk_data` and put it first on `nltk.data.path`; `instructions_util.py` lines 1551-1571 download punkt, punkt_tab, stopwords and averaged_perceptron_tagger_eng at import when missing, at whatever version the server has. Sentence splitting, word tokenization, stop words and the POS tagger decide the verdicts of 17 checkers. Command: `sed -n '26,32p' case/grader/IFBench/instructions.py; sed -n '1551,1571p' case/grader/IFBench/instructions_util.py`. Reference: same.

**F36 Run records leave inputs unpinned, and the comparability claim is false.** CONFIGS.md records no vLLM version for the two thinking configurations and no grader or Evalchemy commit; `eval_instruct.py`'s docstring calls the vendored files "the canonical AI2 graders ... directly comparable to the IFBench paper's", but they differ from AI2's code at 1c40f0c in 7 places (F01, F02, F03, F29, F30, `ratio:overlap` trigram unit, refactors). Command: `diff <(tr -d '\r' < case/reference/IFBench/ifbench/instructions.py) <(tr -d '\r' < case/grader/IFBench/instructions.py)`.

## Decision entries for the maintainers

There are 65 decision entries (59 in contract v1, 5 added in v2, 1 in v3). The full list with both readings and examples is in `audit/CONTRACTS.md` (sections 1 to 8, changes in section 9); each is a reading the text allows, so none is counted as a defect. Effect = panel verdicts the replacement changes when only that switch takes the alternative reading (`audit/work/panel_summary.txt`).

| Entry | Readings | Proposal | Grader's reading | Panel effect |
|---|---|---|---|---|
| D-vacuous | missing presupposed structure (fewer than N words, no quote, one line, one sentence) fails / passes | fails | passes | 602 of 12,517 |
| D-list-inline | separator at line start / inline separators also count | line start | anywhere (F10) | 480 of 2,051 |
| D-punct-set | broad set (adds ' " ( ) -) / . , ? ! ; : plus interrobang | broad | narrow | 434 of 1,368 |
| D-vowel | at most 3 distinct vowels in the whole response / per word | whole | whole | 365 of 2,264 |
| D-palin-distinct | 10 distinct palindromes / 10 occurrences | distinct | occurrences | 319 of 1,587 |
| D-count-exact | "once", "twice" exact / minimum | exact | exact | 307 of 1,140 |
| D-section | sections by blank line or heading / by heading only | blank line or heading | first span only (F11) | 288 of 2,049 |
| D-csv-wrapper | CSV inside a code fence with prose allowed / bare CSV only | allowed | bare | 220 of 684 |
| D-overlap-def | word / character trigrams; response side / reference side | word, response side | character, response side | 201 (unit), 149 (side) of 2,733 |
| D-typographic | curly quotes and apostrophes = straight / distinct | same | distinct | 103 of 7,742 |
| D-options-whitespace, D-options-label | whitespace collapsed; `b` or `b) <option text>` accepted | collapsed; accepted | exact string | 78 of 1,368 |
| D-keyword-form | whole word / inflections count | whole word | substring (F03) | 63 of 4,557 |
| D-punct-separate | `?!` also supplies ? and ! / separate ones needed | supplies | separate | 60 of 1,368 |
| D-balance | equal counts / within one | equal | equal | 38 of 1,595 |
| D-template-outside | prose outside the template not allowed / allowed | not allowed | allowed | 36 of 912 |
| D-indent-blank | blank lines ignored / count as lines | ignored | one ignored, two count | 31 of 2,052 |
| D-span-base | 0-based / 1-based word indices | 0-based | character indices (F01) | 5 of 910 |
| D-vowel-paragraph, D-europe-set, D-africa-list, D-nows-trailing | see CONTRACTS.md | | mixed | 0 each |
| D-word, D-sentence, D-markup, D-edge-whitespace | what a word, a sentence and a line are; markup and list labels; surrounding whitespace | CONTRACTS.md G1-G7 | per-checker tokenizers (`str.split`, `\w+`, NLTK); markup and labels count as words | not switched; part of the 4,703 residual |
| others (39) | D-conj-usage, D-number-words, D-number-labels, D-name-case, D-pronoun-set, D-unique, D-between, D-japanese-segmentation, D-reverse-content, D-reverse-punct, D-csv-rows, D-csv-header-quotes, D-csv-special, D-content, D-mcq-length, D-multiples-extra, D-title, D-indent-step, D-nbb-after, D-template-markup, D-paren-types, D-qu-single, D-qu-scope, D-subbullet-indent, D-title-minor (borderline words), D-ratio-exact, D-char-count, D-different-words, D-stopword-list, D-rc-tail, D-rs-which, D-alliteration-sound, D-alpha-start, D-y, D-syllables, D-repeat-count, D-verb, D-empty-output, D-case | CONTRACTS.md | mostly the proposal | not switched |

Two items need the maintainers even if every proposal is accepted:

- Prompt 105 asks for "I know or I don't know" and "Write each word on a new line". Under the grader's exact reading of D-options-whitespace its two instructions cannot both pass.
- `custom:european_capitals_sort`, `repeat:repeat_span` and `words:keywords_specific_position` have 0% pass rates on all 228 runs under every grader, and `count:keywords_multiple`, `ratio:sentence_words` and `words:words_position` are below 1.1%; these items measure little in this panel.

## Comparison with the reference (step 4)

- Panel: grader and reference disagree on 257 of 78,432 verdicts: `ratio:overlap` 227 (D-overlap-def, character vs word trigrams), `custom:sentence_alphabet` 23 (F29), `words:words_position` 5 (F30), F02 1, F03 1. Each is a grader defect the reference fixed, or the trigram decision.
- Fixtures: the reference gets 63 of 332 fixtures wrong, the grader 74, the replacement 0.
- The reference's unit tests (`instructions_test.py`, 177 assertions): the reference passes all, the vendored grader fails 6 (the reference's fixes), the replacement fails 9. The contract contradicts 2 of those 9 under every reading (`TEST_EUROPE` without Kyiv, F16; `TEST_NESTED_PARENTHESES_TRUE2`, F24) and 7 under the proposal of one decision: `TEST_THREE_VOWEL_FALSE` (D-vowel-paragraph), `TEST_PALINDROME2` (D-palin-distinct), `TEST_PUNCTUATION2` (D-punct-set), `TEST_QUOTE_EXPLANATION` (D-qu-scope), quote_unquote on `"123..."` (D-vacuous) and on `""` (D-empty-output), `TEST_NEWLINE_COUNTRIES` (52 countries, no Ethiopia or Gambia: D-africa-list). Command: `.venv/Scripts/python.exe audit/scripts/run_reference_tests.py replacement`.

## Stress tests (step 4)

- Metamorphic edits (`audit/scripts/step4_metamorphic.py`, 3,727 edits on 871 passing responses): the grader gives 163 wrong verdicts after an edit the contract ignores or forbids. A trailing newline flips `format:no_whitespace` (26), `format:options` (24) and `format:no_bullets_bullets` (15); a list label on the first line flips `words:consonants` (19), `words:start_verb` (17) and `count:words_japanese` (2); typographic quotes flip `format:quotes` (13), the CSV checks (10), `format:title_case` (5) and `format:options` (3); a blank line flips `format:no_bullets_bullets` (9, F13) and `format:line_indent` (3); a comma after a word flips `words:last_first` (F26). All except F13 and F26 follow the grader's non-proposed readings of D-edge-whitespace, D-markup and D-typographic. The replacement's 14 flips are artifacts of the edits (checked one by one; for example an edit that added a second list label).
- Fuzzing (`audit/scripts/step4_fuzz.py`, seed 10060, 17,400 inputs over 58 checks): grader exceptions only in `custom:csv_city` (25 strict, 25 loose; carriage return, F18). These are counts that depend on the fuzzer; the panel had none.
- Content-free responses (`audit/scripts/step4_content_free.py`, 344 items each): empty and whitespace responses fail every check in the grader, although the empty output satisfies `format:no_whitespace` (D-empty-output). `"the"` repeated 200 times passes 94 items over 13 checks in the grader (`ratio:overlap`, `ratio:sentence_balance`, `ratio:sentence_type`, `sentence:alliteration_increment`, `sentence:increment`, `words:last_first`, `format:line_indent`, `format:quote_unquote`, `format:sub-bullets` among them) and 36 items over 4 checks in the replacement (`words:consonants`, `words:paragraph_last_first`, `words:prime_lengths`, `words:vowel`, which "the the the" literally satisfies). Restating the prompt passes 50 items over 15 checks in the grader and 21 over 10 in the replacement.

## Panel records (step 5)

- Truncated (`finish_reason` = `length`): 4,165 of 68,400 responses (6.1%), from 78 (OLMo-2-0325-32B) to 695 (Qwen3-8B).
- Extraction failures: 136 thinking responses without `</think>` (F33). One thinking-off Qwen3-32B response contains `</think>`.
- Empty responses: 37 (Qwen3-14B 28, Qwen3-8B 5, marin-8b-instruct 4).
- All 228 files align with the dataset order (key and prompt). Scored coverage is 100% for every grader (no exception on the panel).
- Per-configuration scores (strict prompt-level %, mean over runs; "Decisions only" = replacement minus replacement under the grader's readings; "Rest" = the latter minus the grader):

| Configuration | Runs | Grader | Reference | Replacement | Replacement - grader | Decisions only | Rest | greedy_repeat - greedy (grader) | SD of one sampled run (grader) | Loose (grader) |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.1 | 34.1 | 29.7 | -4.4 | -1.4 | -3.0 | -1.0 | 1.9 | 37.8 |
| Qwen2.5-32B-Instruct | 13 | 35.2 | 35.2 | 33.0 | -2.2 | -1.2 | -1.0 | -1.3 | 2.0 | 38.3 |
| Qwen2.5-7B-Instruct | 17 | 27.4 | 27.5 | 23.7 | -3.7 | -1.8 | -1.9 | -0.3 | 1.3 | 30.4 |
| Qwen3-14B | 17 | 27.7 | 27.8 | 28.3 | +0.5 | -1.0 | +1.6 | -0.3 | 1.4 | 31.3 |
| Qwen3-14B thinking | 3 | 34.3 | 34.7 | 37.2 | +2.9 | -2.7 | +5.6 | +1.0 | | 39.3 |
| Qwen3-32B | 13 | 25.1 | 25.2 | 25.9 | +0.8 | -1.2 | +2.0 | -0.7 | 2.1 | 29.4 |
| Qwen3-8B | 17 | 25.2 | 25.1 | 24.4 | -0.7 | -2.3 | +1.5 | +0.0 | 1.2 | 29.5 |
| Qwen3-8B thinking | 3 | 32.4 | 32.4 | 31.3 | -1.1 | -3.4 | +2.3 | +0.0 | | 36.3 |
| Llama-3.1-Tulu-3-8B | 17 | 22.7 | 22.7 | 24.0 | +1.3 | -0.9 | +2.3 | +0.3 | 1.3 | 26.3 |
| OLMo-2-0325-32B-Instruct | 13 | 33.3 | 33.3 | 30.4 | -2.8 | -2.4 | -0.4 | +0.0 | 1.7 | 37.0 |
| OLMo-2-1124-13B-Instruct | 17 | 22.6 | 22.7 | 20.2 | -2.5 | -2.4 | -0.1 | +0.0 | 1.4 | 26.8 |
| OLMo-2-1124-7B-Instruct | 17 | 20.4 | 20.4 | 19.2 | -1.2 | -1.9 | +0.7 | +0.7 | 0.8 | 24.9 |
| marin-8b-instruct | 17 | 17.4 | 17.4 | 17.0 | -0.4 | -1.0 | +0.6 | -1.0 | 1.1 | 21.5 |
| phi-4 | 17 | 19.1 | 19.3 | 20.9 | +1.8 | -0.5 | +2.3 | +0.0 | 2.1 | 24.3 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.6 | 17.6 | 16.0 | -1.6 | -1.7 | +0.1 | +0.3 | 1.1 | 20.8 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.8 | 22.3 | 23.7 | +1.9 | -1.7 | +3.6 | -0.3 | 1.3 | 27.9 |

The replacement minus grader difference is a paired difference on the same responses, so it carries no sampling noise of its own; the rerun column shows how far an identical-settings rerun moves a single run's score. Per-check pass rates and disagreements are in `audit/work/panel_summary.txt`.

## Steps not run or changed in this exercise

- No issue tracker: the record is `audit/ISSUE.md`. No repository, research branch, `manage-pr`, Hugging Face dataset or job launcher: fixtures are tests under `audit/tests/`, frozen files under `audit/frozen/` with hashes in ISSUE.md, scripts under `audit/scripts/`.
- Step 5: no compute; the stored responses are the panel, and no new responses were generated. The panel has no LLM judge and no RL reward, so the judge and false-reward items do not apply (F32 counts loose grading's contract-contradicted passes instead).
- Step 6: not run. No sample was drawn, frozen or rendered.
- Unverified inputs (ISSUE.md lists how to verify each): the vendored files equal what Marin runs; the reference copy equals 1c40f0c; the parquet equals revision 2e8a48d; Evalchemy's extraction rule and exception handling; the vLLM version of the thinking configurations.

## What step 6 still has to settle

The recommendation to fix the grader rests on findings that hold under every reading, but the size of the grader's error and whether the replacement is better are not measured. Before the replacement is adopted, step 6 must show:

1. The replacement passes all 332 fixtures (it does today) and has 100% scored coverage (it has on the panel).
2. Its error rate is lower than the grader's, with a 95% paired bootstrap interval for the difference that excludes zero. The review sample should be drawn with a recorded seed from the held-out runs (`sample7` of each configuration with sampled runs, `greedy_repeat` of the two thinking configurations; 5,504 verdicts), stratified by grader-vs-replacement disagreement (480 held-out disagreements, to sample all or most of) and agreement (sized for the interval: about 130 consensus cases per stratum that holds 70% of the population for an upper end below 2% when no error is found).
3. The checks where the replacement is least certain get reviewed: `words:start_verb` (heuristic for imperatives), `format:emoji`, `format:quotes`, `format:sub-bullets`, `format:no_bullets_bullets`, `format:options`, `custom:csv_*` and `custom:mcq_count_length`, where the replacement passes many items the grader fails.

If the replacement's error rate is not lower, the fix should instead be the reference plus targeted patches for F04 to F28 and F31 to F35, each with its fixtures.
