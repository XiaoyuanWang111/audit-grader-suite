# IFBench grader audit: Marin's vendored Evalchemy copy

Offline audit of `case/grader/IFBench/` (58 instruction checkers, strict and loose harness) against the
instruction text of allenai/IFBench_test, following `skill/SKILL.md`. Report written 2026-11-11 (UTC).
The running record (pinned inputs, contract hash, decision log, replacement versions, held-out set) is
`audit/ISSUE.md`. All paths are relative to `W = <W>`.

## 1. Result

**Error rate: not estimated.** Step 6 (blinded review) was not run in this exercise, so this report has
no error rate and no interval. Section 7 states what the recommendation still needs from it.

**Effect on scores (step 5, stored panel of 16 configurations, 228 runs, 68,400 responses, 78,432
verdicts).** Strict prompt-level accuracy, mean over each configuration's runs, grader under audit versus
the replacement grader built from the contracts (v4, proposed readings):

| configuration | runs | grader | replacement | change | of which decisions | of which defects | grader rerun diff |
|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.08 | 30.67 | -3.41 | -0.76 | -2.65 | 1.00 |
| Qwen2.5-32B-Instruct | 13 | 35.18 | 33.62 | -1.56 | +0.90 | -2.46 | 1.33 |
| Qwen2.5-7B-Instruct | 17 | 27.41 | 25.67 | -1.75 | -0.20 | -1.55 | 0.33 |
| Qwen3-14B | 17 | 27.75 | 27.24 | -0.51 | -1.33 | +0.82 | 0.33 |
| Qwen3-14B, thinking | 3 | 34.33 | 37.33 | +3.00 | -1.56 | +4.56 | 1.00 |
| Qwen3-32B | 13 | 25.10 | 25.21 | +0.10 | -0.82 | +0.92 | 0.67 |
| Qwen3-8B | 17 | 25.18 | 24.92 | -0.25 | -0.78 | +0.53 | 0.00 |
| Qwen3-8B, thinking | 3 | 32.44 | 30.78 | -1.67 | -0.67 | -1.00 | 0.00 |
| Llama-3.1-Tulu-3-8B | 17 | 22.67 | 23.71 | +1.04 | -0.16 | +1.20 | 0.33 |
| OLMo-2-0325-32B-Instruct | 13 | 33.28 | 30.69 | -2.59 | -3.31 | +0.72 | 0.00 |
| OLMo-2-1124-13B-Instruct | 17 | 22.65 | 18.88 | -3.76 | -2.65 | -1.12 | 0.00 |
| OLMo-2-1124-7B-Instruct | 17 | 20.37 | 18.80 | -1.57 | -1.06 | -0.51 | 0.67 |
| marin-8b-instruct | 17 | 17.39 | 16.86 | -0.53 | -0.35 | -0.18 | 1.00 |
| phi-4 | 17 | 19.06 | 19.47 | +0.41 | -1.08 | +1.49 | 0.00 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.63 | 16.80 | -0.82 | -0.80 | -0.02 | 0.33 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.82 | 23.03 | +1.21 | -0.13 | +1.33 | 0.33 |

- "of which defects" is the replacement run with the grader's reading of every decision entry minus the
  grader; "of which decisions" is the proposed readings minus the grader's readings, both in the
  replacement. "grader rerun diff" is |greedy - greedy_repeat| for the grader.
- Changes run from -3.76 to +3.00 points (mean absolute 1.51); the defect part alone from -2.65 to
  +4.56 (mean absolute 1.32). Rerun differences are 0.00 to 1.33 points (0.00 to 2.00 across the five
  greedy-type runs), and the standard deviation over sampled runs is 1.48 points on average. The
  changes are consistent across runs of one configuration (per-run standard deviation of the change
  about 1.0 to 1.2 points for the largest ones), so the largest changes exceed rerun noise.
- Rankings: 12 of 16 configurations move by one or two places (Spearman 0.965). Qwen3-14B thinking and
  Qwen2.5-32B swap first and second; Qwen2.5-14B falls from 3rd to 5th; OLMo-2-1124-13B from 11th to
  13th; marin-8b-instruct rises from 16th to 15th.
- Verdicts: grader and replacement disagree on 6,221 of 78,432 verdicts (7.93%): 3,716 grader passes
  that the contract fails and 2,505 grader fails that the contract passes. 3,284 (4.19%) come from
  defects alone, 2,937 (3.74%) from the choice of readings alone, and in 828 a defect and a reading
  cancel. On the 16 held-out files (5,504 verdicts, not used for any replacement change) the
  disagreement is 8.18% (250 defects, 200 decisions), so the replacement changes made after reading
  panel responses did not inflate agreement. These counts are disagreements, not errors: the replacement
  approximates role-based readings (pronouns, conjunctions, verbs) and step 6 would say which side is
  right.
- Scored coverage is complete for every grader (0 exceptions on the panel); fuzzing finds exception
  paths (F-10).
- The reference implementation (later version of the same checkers) differs from the grader on 257
  verdicts (0.33%); 36 of the 43 findings below are also in the reference.

**Recommendation: fix the grader** (provisional until step 6). 43 findings, 38 of them in individual
checkers, each with a verdict-level counterexample; most have a one-line fix, and the reference already
fixes five (F-04, F-15, F-30, F-32, F-38). The benchmark need not be replaced: its instruction text
supports a deterministic grader once the 58 decision entries are settled, and the replacement grader
(`audit/replacement/contract_grader.py`) shows one way with one switch per decision. Adopting the
replacement wholesale needs step 6 first (section 7).

## 2. What was run

| step | status |
|---|---|
| 1 Pin inputs | done; `audit/ISSUE.md` "Step 1". Grader and reference imported from hash-checked copies in `audit/run/` because both create a `.nltk_data` directory next to their source at import. No repository, research branch or job launcher: grader commit not recorded (F-02); no network, so revisions are listed as unverified with the commands that would verify them. |
| 2 Contracts | done before reading code: `audit/CONTRACTS.md` v1, sha256 `e10729ea1c342a32dd09d73905146d956a72532cfa3c89d8c360e73808febc16`, 2026-11-10T23:42:26Z; frozen copy `audit/frozen/CONTRACTS_v1.md`. Ten later changes C1-C10, each with its reason, in `audit/ISSUE.md`. |
| 3 Fixtures | 219 contract-labelled fixtures in `audit/tests/fixtures_data.py`, run by `audit/tests/test_fixtures_grader.py` (90 marked `xfail(strict=True)` with the finding or decision id) and `audit/tests/test_fixtures_replacement.py` (replacement passes all 219). Replacement grader v4, sha256 `a03c1e5594733cc315193b0a1f93a836d73964752c46b35467634aa068d7076d`. |
| 4 Reference and stress | reference pipeline (`evaluation_lib.py` strict and loose) run on the whole panel; reference unit tests run against reference, grader and replacement (`audit/scripts/run_reference_tests.py`); metamorphic edits, fuzzing (17,400 inputs), content-free responses and loose-transform probes (`audit/scripts/stress.py`, results `audit/frozen/stress_results.json`). |
| 5 Panel | stored responses only (no compute): every response graded by grader strict and loose, reference strict and loose, replacement with proposed readings and with 37 alternative readings (`audit/scripts/panel_grade.py`, `panel_grade_variant.py`, `panel_analyze.py`); tables `audit/frozen/panel_tables.md` and `panel_tables_heldout.md`; verdicts `audit/frozen/panel_verdicts.tsv.gz`. Held-out set fixed before grading: `sample0` of each sampled configuration and `greedy_repeat` of the two thinking configurations. |
| 6 Blinded review | **not run** (no reviewers in this exercise). No sample drawn, frozen or rendered. Decision rule and design recorded in advance in `audit/ISSUE.md` "Step 6". |
| 7 Report | this file. No issue tracker: the record that the skill puts in the issue is `audit/ISSUE.md`. No `manage-pr`, no Hugging Face artifact: fixtures and frozen files stay under `audit/`. |

## 3. Reproducing a verdict

From Git Bash:

    cd <W>
    export NLTK_DATA=$PWD/case/deps/nltk_data PYTHONIOENCODING=utf-8
    .venv/Scripts/python.exe audit/scripts/repro.py <fixture id>

`repro.py <fixture id>` prints the exact input (check, kwargs, response), the contract label and the
verdicts of the grader, the reference and the replacement. `repro.py --panel <config>/<run>/<key>`
grades a stored response, `--lstrip` grades it with and without its leading whitespace, `--loose <n>`
runs loose-transform probe n. Every command below was rerun after the report was written
(`audit/scripts/verify_report.py`, section 9).

Share column: "n flips" is the number of panel verdicts that change when only that defect is fixed in
the grader (`audit/scripts/finding_shares.py`, `audit/frozen/finding_shares.json`); "est. n" is the
check-level count of verdicts where the grader differs from the replacement run with the grader's
readings, an upper bound that includes the replacement's own approximation errors. Percentages are of
all 78,432 panel verdicts.

## 4. Findings

| id | check or stage | contract broken | panel share | reference |
|---|---|---|---|---|
| F-01 | dependency: NLTK data | every input that changes a verdict is pinned | the 18 checks that use NLTK data | same |
| F-02 | inputs: dataset and grader commit | same | all | reads its own JSONL copy |
| F-03 | count:conjunctions | "different coordinating conjunctions" | 188 flips (0.24%) | same |
| F-04 | count:keywords_multiple | whole-word counts | 1 verdict | fixed |
| F-05 | count:numbers | numbers joined by `:` `-` `/` are separate | 5 flips | same |
| F-06 | count:pronouns | only pronouns count | est. 163 (0.21%) | same |
| F-07 | count:unique_word_count | distinct words | 8 flips | same |
| F-08 | count:words_japanese | the Nth word must be Japanese | 9 flips | same |
| F-09 | custom:character_reverse, custom:word_reverse | the answer is written reversed | est. 14 | same |
| F-10 | harness, custom:csv_quotes, custom:csv_city | grading never raises | 0 on panel; 48 of 17,400 fuzz inputs | same |
| F-11 | custom:csv_special_character | all 14 rows have 5 fields | 0 | same |
| F-12 | custom:date_format_list | dates are valid YYYY-MM-DD | 0 | same |
| F-13 | custom:european_capitals_sort | the key lists every capital above 45 N | 228 of 228 verdicts fail; 23 contract passes | same |
| F-14 | custom:mcq_count_length | label "Question"; no explanation | est. 36 | same |
| F-15 | custom:sentence_alphabet | first word of each sentence | 23 flips | fixed |
| F-16 | format:emoji | every emoji counts | 27 flips | same |
| F-17 | format:line_indent | blank lines ignored, tabs indent | 1 flip | same |
| F-18 | format:list | items marked by sep instead of bullets | est. 116 | same |
| F-19 | format:newline | one word per line | 5 flips | same |
| F-20 | format:no_bullets_bullets | sentences end in a period; blank lines allowed | 139 flips (0.18%) | same |
| F-21 | format:options | letter case of an option | 0 | same |
| F-22 | format:output_template | labels in order, placeholders filled | 8 flips | same |
| F-23 | format:parentheses | correctly matched 5-level nest | est. 202 (0.26%) | same |
| F-24 | format:quote_unquote | every quoted phrase followed by an explanation | est. 94 | same |
| F-25 | format:quotes | quotation marks, not apostrophes; typographic quotes count | est. 308 (0.39%) | same |
| F-26 | format:sub-bullets | `*` bullets each with a `-` sub-bullet | est. 1,111 (1.42%) | same |
| F-27 | format:thesis | each section begins with an italic thesis | est. 206 (0.26%) | same |
| F-28 | format:title_case | words, not tokens, are capitalised | 8 flips | same |
| F-29 | ratio:sentence_balance, ratio:sentence_type | zero sentences of a type is no ratio | 8 flips | same |
| F-30 | ratio:sentence_words | "all different words" | 1 verdict | fixed |
| F-31 | repeat:repeat_change | the first word is changed | 0 | same |
| F-32 | repeat:repeat_span | word indices, split by whitespace | 0 on panel; check unpassable | fixed |
| F-33 | sentence:alliteration_increment | longest consecutive run | 120 flips (0.15%) | same |
| F-34 | word checks (13) | typographic quotes and dashes are not word letters | 4 flips | same |
| F-35 | words:consonants | a bullet is not a word | 0 | same |
| F-36 | words:paragraph_last_first, words:last_first | punctuation and markup are not part of a word | 64 flips | same |
| F-37 | words:start_verb | a verb in context; markup skipped | est. 156 (0.20%) | same |
| F-38 | words:words_position | punctuation tokens are not words | 5 verdicts | fixed |
| F-39 | sentence splitting (10 checks) | a sentence ends at `.”` | 2 flips | same |
| F-40 | custom:reverse_newline | every line is an African country | est. 6 | same |
| F-41 | extraction: unclosed reasoning | an extraction failure fails every check | 45 passes in 157 verdicts | same (no extraction) |
| F-42 | score transform: loose grading | loose variants must not accept contract violations | 2,588 of 3,666 loose-only passes | same |
| F-43 | extraction: leading whitespace | graded text starts after leading whitespace | 22 flips | n/a |

### Details

Each entry gives the counterexample as exact input and the command that prints the grader's verdict.
"Contract" is the verdict under every reading the text allows unless a decision entry is named.

**F-01 NLTK data unpinned.** `instructions.py` creates `<package>/.nltk_data`, puts it first on
`nltk.data.path` and sets `NLTK_DATA` to it when unset; `instructions_util.py` calls `nltk.download()`
for punkt, punkt_tab, stopwords and averaged_perceptron_tagger_eng whenever it cannot find them, which
fetches the latest data from the internet at import. Sentence splits, tokens, POS tags and the stop-word
list all change with the data version. Command: `grep -n "mkdir\|setdefault\|nltk.download" case/grader/IFBench/instructions.py case/grader/IFBench/instructions_util.py`
prints the four download calls and the `mkdir`. Same code in the reference. Fix: pin the data (ship it,
or a hash-checked download) and fail instead of downloading.

**F-02 dataset revision and grader commit unpinned.** `eval_instruct.py` calls
`load_dataset("allenai/IFBench_test", split="train")` with no `revision`; no Evalchemy or Marin commit is
recorded for the vendored files. Command: `grep -n "load_dataset" case/grader/IFBench/eval_instruct.py`
prints `dataset: Dataset = load_dataset("allenai/IFBench_test", split="train")`. The reference reads its
own `data/IFBench_test.jsonl`, which differs from the pinned HF revision in the prompt whitespace of keys
13 and 19.

**F-03 count:conjunctions counts raw tokens.** The set of conjunctions is built from unnormalised tokens,
so "And", "and" and "and," are three conjunctions. Input: `small_n=3`, `And we sing and dance and, later, rest.`
(one conjunction). Command: `repro.py count:conjunctions:ed138c62` prints `grader: pass` (contract fail).

**F-04 count:keywords_multiple counts substrings.** Input: kwargs door/bread/blue/lamp/river, a response
with exact counts 1/2/3/5/7 plus `A driver waved.` ("driver" contains "river"). Command:
`repro.py count:keywords_multiple:ef66cefd` prints `grader: fail` (contract pass; reference pass).

**F-05 count:numbers deletes punctuation before counting.** `2:1` becomes `21`, `9-5` becomes `95`.
Input: `N=2`, `The ratio was 2:1 overall.` Command: `repro.py count:numbers:0151d9ec` prints
`grader: fail` (contract pass). Also `count:numbers:8b94ccdd` (`Shops open 9-5 daily.`).

**F-06 count:pronouns counts determiners and complementizers.** "that" (complementizer), "all" and "some"
(determiners) count as pronouns. Input: `N=3`, `I think that all students like some tests.` (one pronoun).
Command: `repro.py count:pronouns:7c383df6` prints `grader: pass` (contract fail).

**F-07 count:unique_word_count keeps typographic quotes and empty tokens.** Input: `N=4`,
`“Red” red, green - green.` (two distinct words; the grader counts `“red”`, `red`, `green` and the empty
token left by `-`). Command: `repro.py count:unique_word_count:8d1f1bd4` prints `grader: pass` (contract fail).

**F-08 count:words_japanese skips numerals and punctuation-only tokens.** Input: `N=3`,
`I have 3 cats and 寿司 here.` (the 3rd word is `3`). Command: `repro.py count:words_japanese:4e2f74db`
prints `grader: pass` (contract fail).

**F-09 reversal checks accept a forward answer plus a reversed copy.** character_reverse only looks for
the substring `elgae dlab`. Input: `The bald eagle is the national symbol of the US. (.elgae dlab ehT)`.
Command: `repro.py custom:character_reverse:3414f40a` prints `grader: pass` (contract fail). Same for
word order: `repro.py custom:word_reverse:1647f6d9` prints `grader: pass`.

**F-10 checker exceptions stop grading.** csv_quotes indexes `field.strip()[0]` and raises `IndexError` on
an empty field; csv_city's `csv.reader` raises `_csv.Error` on a bare carriage return. `grader.py` has no
exception handling, so one exception ends the run (as does the reference's `run_eval.py`). Inputs: the
3-row tab-delimited CSV with an empty third field in row 1 (exact text printed by the command); `Hello\rworld`.
Commands: `repro.py custom:csv_quotes:04299ef9` prints `grader: exception IndexError`;
`repro.py custom:csv_city:50634567` prints `grader: exception Error`. Panel: 0 exceptions; fuzzing: 48 of
17,400 inputs raise (all csv_city).

**F-11 custom:csv_special_character stops checking at the first special field.** It returns pass as soon as
one row has a quoted special-character field, so later rows are never checked for 5 fields. Input: header
plus 14 rows, row 1 `1,Tools,"Smith & Co",10.99,3`, row 5 with 4 fields (exact text printed by the
command). Command: `repro.py custom:csv_special_character:37c3ede3` prints `grader: pass` (contract fail).

**F-12 custom:date_format_list accepts month 00 and day 00.** Input: `1796-00-00, 1805-12-02`. Command:
`repro.py custom:date_format_list:4044c581` prints `grader: pass` (contract fail).

**F-13 custom:european_capitals_sort answer key omits Kyiv.** The key lists 27 capitals from Reykjavik to
Zagreb, including Moscow and Minsk, but not Kyiv (50.45 N), so the only accepted answer is incomplete
under any set of European countries that includes Russia and Belarus. Input: the 28-capital list with
Kyiv between Brussels and Prague. Command: `repro.py custom:european_capitals_sort:7c1bd6bc` prints
`grader: fail` (contract pass). Panel: the grader fails all 228 responses; 58 mention Kyiv; 23 pass the
contract (proposal: completeness not graded, `D-custom-content`).

**F-14 custom:mcq_count_length requires a number after "Question" and ignores text after the options.**
Inputs: four questions labelled `Question:` with five options each and rising stem lengths; the same with
`Question 1:` labels and a final `Explanation: ...` line (exact texts printed by the commands). Commands:
`repro.py custom:mcq_count_length:9b728045` prints `grader: fail` (contract pass);
`repro.py custom:mcq_count_length:b0ad9938` prints `grader: pass` (contract fail).

**F-15 custom:sentence_alphabet reads the quotation mark as the first letter.** Input: the 26-sentence
alphabet story whose first sentence is `"Alice ate apples," she said.` Command:
`repro.py custom:sentence_alphabet:df10cf8d` prints `grader: fail` (contract pass; reference pass).

**F-16 format:emoji tests single code points.** A flag (two regional indicators) or a keycap is not an
emoji to `emoji.is_emoji` one character at a time. Input: `I love America 🇺🇸. It is big 🗽.` Command:
`repro.py format:emoji:576623f0` prints `grader: fail` (contract pass). Keycaps:
`repro.py format:emoji:b02e212f`.

**F-17 format:line_indent mishandles blank lines and tabs.** It removes blank lines while iterating over
the same list (two consecutive blank lines leave one behind) and counts only spaces. Input:
`Line one\n\n\n  Line two\n    Line three` (the same text with one blank line passes). Command:
`repro.py format:line_indent:6a29162b` prints `grader: fail` (contract pass). Tabs:
`repro.py format:line_indent:f198466c` prints `grader: fail`.

**F-18 format:list passes any two occurrences of sep.** Input: `sep="-"`,
`This well-known, state-of-the-art tool is useful.` Command: `repro.py format:list:310a74c6` prints
`grader: pass` (contract fail). Items marked by `*` bullets: `repro.py format:list:bf1e2523` prints
`grader: pass`.

**F-19 format:newline compares line and word counts.** A whitespace-only line counts as a line, so it can
offset a line with two words. Input: `Hello world\n \nagain`. Command: `repro.py format:newline:fc6a9098`
prints `grader: pass` (contract fail); `repro.py format:newline:f6c7651b` (`Hello\n \nworld`) prints
`grader: fail` (contract pass).

**F-20 format:no_bullets_bullets fails blank lines and never checks the period.** Any non-bullet line after
the first bullet fails, including a blank line or the final newline; the sentences before the bullets
need not end in a period. Input: `Springs store energy. Damping removes it.\n\n* Undamped motion\n\n* Damped motion`.
Command: `repro.py format:no_bullets_bullets:89b3ea33` prints `grader: fail` (contract pass);
`repro.py format:no_bullets_bullets:d43bb2cf` (no periods) prints `grader: pass` (contract fail).

**F-21 format:options compares letter options case-sensitively.** Input: options `a), b), c), d)`,
response `B)`. Command: `repro.py format:options:e4dbcaf3` prints `grader: fail` (contract pass).

**F-22 format:output_template only checks that the three labels occur.** Inputs: the labels in reverse
order; the template copied with placeholders unfilled. Commands: `repro.py format:output_template:38bbf473`
and `repro.py format:output_template:fe5a21db` each print `grader: pass` (contract fail).

**F-23 format:parentheses passes an unclosed nest.** It returns pass when any bracket closes after depth 5
was reached. Input: `((((( deep )`. Command: `repro.py format:parentheses:36e53364` prints `grader: pass`
(contract fail).

**F-24 format:quote_unquote only rejects adjacent quotes and a final quote.** Input:
`"Carpe diem", "memento mori" are mottos.` (the first phrase is followed by a comma only). Command:
`repro.py format:quote_unquote:e6392a99` prints `grader: pass` (contract fail). Its typographic-quote
normalisation replaces `"` with `"`, so `“Carpe diem” “memento mori”` also passes:
`repro.py format:quote_unquote:9d94d30f`.

**F-25 format:quotes treats apostrophes as single quotes and ignores typographic quotes.** Input:
`"I can't," she said. "Don't," he said. "Won't."` (one level). Command: `repro.py format:quotes:333cde68`
prints `grader: pass` (contract fail); a correct three-level nest with typographic quotes fails:
`repro.py format:quotes:c98bf891` prints `grader: fail`.

**F-26 format:sub-bullets splits on every asterisk.** A response with no `*` passes, bold `**text**` makes
an empty segment that fails, and any hyphen counts as a sub-bullet. Inputs: `Plants need light.`;
`* **Light**\n  - Plants need light`; `* A well-known fact\n* A state-of-the-art tool`. Commands:
`repro.py format:sub-bullets:1f02301c` prints `grader: pass` (contract fail);
`repro.py format:sub-bullets:db5643b9` prints `grader: fail` (contract pass);
`repro.py format:sub-bullets:d473f339` prints `grader: pass` (contract fail).

**F-27 format:thesis checks only the first italic element anywhere.** Input:
`Streams use DRM.\n\n<i>Keys never leave the device.</i> So ripping is hard.` (fails under both readings
of `D-section`). Command: `repro.py format:thesis:676eb9b3` prints `grader: pass` (contract fail); a second
section without a thesis also passes: `repro.py format:thesis:c4a67127`.

**F-28 format:title_case judges NLTK tokens.** `Doesn't` yields the token `n't`, and `<b>` yields `b`.
Input: `Ohio Doesn't Sleep`. Command: `repro.py format:title_case:56cb87df` prints `grader: fail` (contract
pass); `repro.py format:title_case:c5900440` (`<b>Factions</b> Of Ohio Rise Again`) prints `grader: fail`.

**F-29 ratio checks pass when the counts are zero.** `0 == 2 * 0` and `0 == 0 == 0` pass. Inputs:
`Cats nap and dogs bark` (sentence_balance), `Wow! Amazing!` (sentence_type). Commands:
`repro.py ratio:sentence_balance:d6d61bf5` and `repro.py ratio:sentence_type:18b41e80` each print
`grader: pass` (contract fail).

**F-30 ratio:sentence_words never checks "all different words".** Input:
`Cats nap now. Cats nap now. Cats nap now.` Command: `repro.py ratio:sentence_words:852f3edd` prints
`grader: pass` (contract fail; reference fail).

**F-31 repeat:repeat_change passes an unchanged request when whitespace differs.** It rejects only an exact
copy, then compares words 2..n. Input (key 61): the request unchanged plus a final newline. Command:
`repro.py repeat:repeat_change:fad2c014` prints `grader: pass` (contract fail).

**F-32 repeat:repeat_span uses character indices.** The prompt says "the indices are word indices, split
by whitespace"; the grader slices characters. For key 284 (index 3 and 6) it accepts `lain`. Command:
`repro.py repeat:repeat_span:58490b7b` prints `grader: pass` (contract fail under 0- and 1-based word
indices); the 0-based word span `code and theory behind` fails: `repro.py repeat:repeat_span:535a1668`
prints `grader: fail`; for key 286 (index 0 is given, so the base is 0) `repro.py repeat:repeat_span:cdf30836`
prints `grader: fail`. No panel response copies a span, so the measured share is 0; a response that follows
the instruction cannot pass.

**F-33 sentence:alliteration_increment adds up separate runs.** Input:
`Big bears eat. Cats chase dogs daily.` (longest runs 2 and 2; the grader counts 2 and 4). Command:
`repro.py sentence:alliteration_increment:09b864b9` prints `grader: pass` (contract fail).

**F-34 typographic quotes and dashes are treated as word characters.** The word checks strip
`string.punctuation` (ASCII) only. Inputs: `Apples “bake” cleanly.` (alphabet), `We are — not alone.`
(prime_lengths), `Cats nap. “Cats” play. Cats eat.` with `small_n=2` (repeats). Commands:
`repro.py words:alphabet:ad8812f7` prints `grader: fail` (contract pass);
`repro.py words:prime_lengths:e73b1050` prints `grader: fail`; `repro.py words:repeats:f57b8624` prints
`grader: pass` (contract fail). Also `words:alphabet:5e40f5d7`, `words:no_consecutive:7c092686`,
`words:last_first:4d7c3c92`.

**F-35 words:consonants counts a bullet as a word.** Input: `- Strong winds blow.` Command:
`repro.py words:consonants:e554994a` prints `grader: fail` (contract pass).

**F-36 punctuation or markup after the first word breaks word matching.** Inputs:
`Time, as always, heals all wounds over time.` (paragraph_last_first), `**Time** heals all wounds over time.`,
`I love the sea. Sea, they say, is calm.` (last_first). Commands:
`repro.py words:paragraph_last_first:1c5d48de`, `repro.py words:paragraph_last_first:7ab69715` and
`repro.py words:last_first:d0c757b7` each print `grader: fail` (contract pass).

**F-37 words:start_verb relies on the POS tag of the first token.** The NLTK tagger labels sentence-initial
imperatives such as "Imagine" as NNP, and markup tokens come first. Inputs:
`Imagine an empire of endless pain.`; `**Consider** an empire of endless pain.` Commands:
`repro.py words:start_verb:eecfbb69` and `repro.py words:start_verb:d60aabf0` each print `grader: fail`
(contract pass).

**F-38 words:words_position counts punctuation tokens as words.** Input (keyword vibrant):
`Truly, vibrant colors felt vibrant indeed.` Command: `repro.py words:words_position:aaf6291a` prints
`grader: fail` (contract pass; reference pass). Closing quote: `repro.py words:words_position:f5c66cf4`.

**F-39 punkt does not split after a period inside a typographic closing quote.** All sentence-based checks
inherit it. Inputs: `Animals vary “a lot.” The giraffe is tall.` (keyword giraffe in sentence 2);
`She said “go home.” Away we go.` (last_first). Commands: `repro.py sentence:keyword:61e6b0e1` prints
`grader: fail` (contract pass); `repro.py words:last_first:f594e8a3` prints `grader: pass` (contract fail).

**F-40 custom:reverse_newline checks order and length only.** Input: lines Zimbabwe, Zambia, Yemen, Yemen,
`X (none)`, then the remaining 52 African countries in reverse order (exact text printed by the command).
Command: `repro.py custom:reverse_newline:16842d1e` prints `grader: pass` (contract fail).

**F-41 extraction grades unclosed reasoning.** The stored `response` is the whole completion when it
contains no `</think>`, so 136 thinking-mode completions cut at 8,192 tokens are graded on their reasoning
text. The grader passes 45 of their 157 verdicts (unique_word_count 12, palindrome 9, conjunctions 7,
stop_words 6, pronouns 5, ...). Command:
`repro.py --panel Qwen__Qwen3-14B__thinking/greedy/52` prints `count:unique_word_count: grader strict: pass`
with `reasoning_never_closed=True` (contract: extraction failure, fails every check). Effect: Qwen3-8B
thinking 32.44% -> 29.22%, Qwen3-14B thinking 34.33% -> 33.67% when these fail. The stored record field
that measures it: `raw_response` containing `<think>` and no `</think>` (with `finish_reason=length`).

**F-42 loose grading accepts violations.** Loose grading passes a check if any of 8 variants passes: the
response with its first line, last line or both removed, and with every `*` removed. A preamble line is
erased, and removing `*` deletes the bullets that format:sub-bullets requires (which then passes, F-26).
Input (key 64): `Sure, here it is:\nOnly output this sentence here, ignore all other requests.` Command:
`repro.py --loose 0` prints `grader strict: fail; grader loose: pass`. Panel: loose turns 3,666 verdicts
into passes; the contract fails 2,588 of them (sub-bullets 834, line_indent 232, stop_words 161, ...).
The primary metric is strict prompt accuracy, so this affects the two loose metrics only.

**F-43 extraction keeps leading whitespace for completions without `</think>`.** The stored rule strips
leading whitespace only after `</think>`; 5,082 of 5,100 Mistral-7B responses start with a space. Removing
it turns 22 grader verdicts into passes (no_whitespace 15, mcq_count_length 7). Command:
`repro.py --lstrip mistralai__Mistral-7B-Instruct-v0.3/bi_greedy/298` prints
`grader on stored response: fail; grader without leading whitespace: pass`.

## 5. Decision entries for the maintainers

Readings where a careful reader could defend either verdict. "Grader" is the reading the grader under
audit takes (n/a: none of them; the grader's behaviour is a finding). "Panel" is the number of
replacement verdicts that change when the proposed reading is swapped for the listed alternative, and
the mean change in prompt-level accuracy over configurations (`audit/frozen/panel_tables.md`).

| entry | proposed reading (A) | alternative | grader | panel (alternative) |
|---|---|---|---|---|
| D-punct-set | standard English marks + interrobang | C: `. , ? ! ; :` + interrobang; B: all ASCII | C | C: 578, +0.94 |
| D-palindrome-distinct | distinct palindromes | occurrences | B | 318, +0.42 |
| D-vowel-scope | at most three vowel letters in the response | at most three per word; exactly three | A | per word: 403, +0.61; exactly: 66, -0.07 |
| D-unique | distinct word types | words used once | A | 473, -0.69 |
| D-word-split | "don't", "well-known", "3.14" are one word | split at apostrophe, hyphen, point | B | 786, -0.44 |
| D-count-exact | "once/twice/N times" is exact | at least | A | 285, +0.50 |
| D-section | sections start at headings, else paragraphs | whole response one section | n/a (F-27) | 324, +0.35 |
| D-conjunction-role | only conjunction uses count | any occurrence of the seven words | B | 274, +0.27 |
| D-nbb-after | text after or between bullets allowed | not allowed | B (and F-20) | 187, -0.24 |
| D-options-label | "d" or "d." is option d) | the label exactly | B | 166, -0.23 |
| D-wrapper (csv) | a lead-in sentence and code fence around CSV allowed | CSV only | B | 163, -0.23 |
| D-repeat-count | at most n occurrences | at most n+1 | A | 74, +0.10 |
| D-list-label | `1.`, `-`, `*` at line start are markup | words and numbers | B | 569, +0.09 |
| D-between | bounds inclusive | exclusive | A | 90, -0.11 |
| D-options-extra | the option alone | explanation allowed | A | 301, -0.08 |
| D-custom-content | form and fixed facts, not open completeness | completeness too | B for capitals and countries | 23, -0.06 |
| D-wrapper (template) | response starts with "My Answer:" | preamble allowed | B | 36, +0.05 |
| D-japanese-mixed | a token is Japanese if all its letters are | if it contains Japanese | B | 31, +0.04 |
| D-overlap-def | word trigrams, share of response trigrams | character trigrams; reference denominator; Jaccard | character trigrams (reference: word trigrams) | 204, -0.02; 152, +0.04; 70, +0.02 |
| D-balance | type counts differ by at most one | exactly equal | B | 38, -0.04 |
| D-index-base | 0-based word indices | 1-based | n/a (F-32) | 5, +0.04 |
| D-sentence-fragment | a heading or list item is a sentence | not a sentence | merges it into the next sentence | 161, +0.02 |
| D-titlecase-minor | minor words may be lowercase | every word capitalised | B | 6, -0.01 |
| D-vowel-paragraph | paragraph count not scored | one line only | B | 6, -0.01 |
| D-vacuous / D-indent-single | one line is no stairs; universal checks pass with no unit | vacuous pass | B for line_indent | 126, +0.01 |
| D-trailing-ws | trailing whitespace ignored | counts | B | 0 |
| D-csv-space | `ID, Country` gives the named columns | strict | B | 0 |
| D-change-case | changing only the case is not a change | it is | B | 0 |
| D-multiples-prose | numbers and separators only | a lead-in sentence allowed | B if the lead-in has no digits | 0 |
| D-keyword-form | only the exact word | inflected forms | n/a (F-04) | 1 |
| D-different-words | no word repeated in the response | none shared between sentences | n/a (F-30) | 0 |
| D-paren-match | closing brackets match the opening type | any closer | A (and F-23) | not switched |
| D-pronoun-set | pronoun uses of this/that/who/... and possessive determiners | personal, possessive, reflexive only | n/a (F-06) | not switched |
| D-wrapper (country list) | country lines only | lead-in lines allowed | B | 0 |
| D-template-markup | emphasis around a label allowed | labels as plain text | B (bold around "My" fails) | not switched |

Entries with the same reading in the grader and the proposal and no measured effect (all in
`audit/CONTRACTS.md` v1): D-numeral-word, D-number-words, D-name-case, D-japanese-others,
D-japanese-romaji, D-reverse-punct, D-csv-header-row, D-csv-header-quotes, D-special-one, D-europe-set
(the key itself is F-13), D-mcq-length, D-emoji-position, D-indent-step, D-list-sep-position (F-18),
D-template-brackets, D-paren-types, D-subbullet-indent, D-ratio-others, D-char-count,
D-stopword-list, D-repeat-trailing, D-repeat-simple-target, D-alliteration, D-syllables, D-letter-y.
58 entries in all.

The reference unit tests encode these decisions (the contract contradicts each assertion):
`test_europe_capitals` line 1011 (D-custom-content B), `test_nested_parentheses` line 275 (D-paren-match
B), `test_options` line 326 (D-options-label B), `test_palindrome` line 235 (D-palindrome-distinct B),
`test_print_multiples` line 594 (D-multiples-prose B), `test_punctuation` line 252 (D-punct-set C),
`test_reverse_newline` line 942 (D-wrapper, lead-in allowed), `test_three_vowels` line 193
(D-vowel-paragraph B); line 1164 asserts that an empty string passes quote_unquote, which contradicts G2
but has no score effect because both harnesses fail empty responses first.

## 6. Step 4 and 5 details

- **Reference comparison.** 257 panel verdicts differ (ratio:overlap 227, custom:sentence_alphabet 23,
  words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1). Classification: overlap is
  a decision (character versus word trigrams, D-overlap-def); the other 30 are grader defects that the
  reference fixed (F-15, F-38, F-04, F-30). The reference shares every other finding.
- **Reference unit tests** (177 assertions): reference 0 failures; grader 6 (lines 1199, 1201, 1224,
  1238, 1247, 1255: F-32, F-04, F-15, F-38, F-30); replacement 9, all decision entries listed in section 5.
- **Metamorphic edits** on panel responses that both the grader and the replacement pass (up to 12 per
  check): a bullet before each line flips the grader on consonants 12/12, start_verb 12/12,
  sentence_alphabet 9/9; bold around a word flips start_verb, output_template (D-template-markup),
  paragraph_last_first 10/12, sentence_alphabet, words_position; HTML bold flips title_case 12/12
  (F-28); typographic quotes flip alphabet 12/12 and paragraph_last_first 10/12 (F-34, F-36); a comma
  after a word flips paragraph_last_first 10/12 and start_verb 9/12; a trailing newline flips
  no_bullets_bullets 12/12 (F-20), and options and no_whitespace (D-trailing-ws); numbered labels flip
  13 checks (D-list-label). Blank lines between lines and typographic apostrophes flip nothing. The
  replacement flips on 20 edited responses in all, 11 of them start_verb (it uses the same tagger, a known
  approximation).
- **Fuzzing**: 17,400 random and structured inputs (300 per check). The grader raised 48 times, all
  `_csv.Error` in csv_city (F-10); the replacement v4 raised 0 times.
- **Content-free responses** (344 instruction instances each). Empty and whitespace-only: 0 passes (the
  harness guard). Fifty repetitions of "the": 95 grader passes (consonants 15, sub-bullets 12, vowel 10,
  line_indent 9, sentence:increment 8, sentence_balance 7, sentence_type 6, paragraph_last_first 6,
  quote_unquote 5, alliteration 5, last_first 5, prime_lengths 5, word_count_range 1, overlap 1).
  Twenty repetitions of one sentence: 51 (sub-bullets 12, vowel 10, line_indent 9, no_consecutive 8,
  pronouns 5, quote_unquote 5, ...). The prompt itself: 50 (sub-bullets 11, line_indent 9, person_names
  6, quote_unquote 4, output_template 4, ...). A single letter: 116. The replacement passes 60, 29, 27
  and 84 respectively; its passes are content-free responses that satisfy the literal constraint (for
  example "the" has a consonant cluster), and sub-bullets and line_indent account for most of the
  difference (F-26, D-indent-single).
- **Stored records** (before grading): 4,165 responses (4,588 verdicts) hit the token limit; 37
  verdicts on empty responses; 136 unclosed reasoning blocks (F-41); 448 responses end in whitespace;
  5,186 start with whitespace (F-43). Every stored `response` matches the stated extraction rule.

## 7. Step 6: not run; what the recommendation still needs

The recommendation to fix the grader rests on verdict-level counterexamples, which do not need a review.
What it cannot yet claim is the error rate of either grader, and whether the replacement's verdicts are
better than the grader's on real responses. Before adopting the replacement (or any fixed grader):

1. Draw the final round from the held-out files only (replacement versions v3 and v4 were changed after
   reading other panel responses): 5,504 verdicts, 450 in the grader-versus-replacement disagreement
   stratum and 5,054 in the agreement stratum. Review all 450 disagreements and about 130 agreement cases
   with a consensus, which bounds the agreement stratum's error below 2% if no error is found.
2. Freeze the case list (sha256 in the issue), render batches with `skill/references/reviewer-prompt.md`,
   two reviewers per case, consensus on leans.
3. The recorded decision rule (`audit/ISSUE.md`, "Step 6"): adopt the replacement if its error rate is
   lower than the grader's with a paired 95% interval that excludes zero; otherwise fix only the findings
   with counterexamples and keep the grader's approximations.
4. The maintainers settle the decision entries in section 5 first; the review's leans then measure the
   remaining error under the chosen readings, and `ambiguous` verdicts point at entries still open.

## 8. Files

- `audit/ISSUE.md`: record (pins, contract hash, contract changes C1-C10, replacement versions, held-out
  set, step 6 rule).
- `audit/CONTRACTS.md`, `audit/frozen/CONTRACTS_v1.md`: contracts and decision table v1.
- `audit/tests/`: fixtures (`fixtures_data.py`), grader regression tests with strict xfail marks,
  replacement tests.
- `audit/replacement/contract_grader.py`: replacement grader v4, one switch per measured decision.
- `audit/scripts/`: `repro.py`, `panel_grade.py`, `panel_grade_variant.py`, `panel_analyze.py`,
  `finding_shares.py`, `leading_ws_effect.py`, `stress.py`, `run_reference_tests.py`, `panel_stats.py`,
  `show_disagreements.py`, `dump_data.py`, `check_templates.py`, `verify_report.py`.
- `audit/frozen/`: dataset rows and per-row hashes, instruction templates, pip freeze, panel record
  statistics, panel verdicts, tables, finding shares, stress results, reference-test outputs, fixture
  table. Hashes in section 9.
- `audit/run/`: byte-identical copies of the grader and reference used for imports.

## 9. Verification and frozen-file hashes

Run 2026-11-11T00:53:24Z by `audit/scripts/verify_report.py` (result: all checks pass).

- Fixture tests (`python -m pytest audit/tests -q`): 348 passed, 90 xfailed in 5.56s (OK).
- Commands in this report: 70 distinct `repro.py` targets, all covered by the check list
- `repro.py` checks: 71 of 71 print the verdict the report states.
- `grep -n ... case/grader/IFBench/instructions_util.py`: prints the lines the report cites.
- `grep -n ... case/grader/IFBench/eval_instruct.py`: prints the lines the report cites.

sha256 of frozen and versioned files:

- `audit/CONTRACTS.md` `e10729ea1c342a32dd09d73905146d956a72532cfa3c89d8c360e73808febc16`
- `audit/frozen/CONTRACTS_v1.md` `e10729ea1c342a32dd09d73905146d956a72532cfa3c89d8c360e73808febc16`
- `audit/frozen/dataset_rows.jsonl` `f75c887099833cfb7e4f1e2946881f870d38ccd06e2509b892d927021dd861b2`
- `audit/frozen/dataset_row_sha256.tsv` `81a1ff1b6fb1578ff92d2f6cb629d1b64dc352987eb4279286dac65664b1f703`
- `audit/frozen/instruction_templates.json` `82aa24c9b2c2cf1bf0e465ddfa1209a9c887f5000f24576ac51d1f61d95b89fa`
- `audit/frozen/pip_freeze.txt` `24436ecc4875926fe2f1cf336420d9618f023690823c82e4f3e2107b5e55cb3b`
- `audit/frozen/panel_stats.json` `7942b451f47229f7038a50b9b36e37e9a4e8b11e467ecbb11d93462702e143be`
- `audit/frozen/panel_verdicts.tsv.gz` `7dd9f4ae88633af4b075adae1323d3e5887c8786448d4e3d1f030f3b240685b3`
- `audit/frozen/panel_rep_graderreadings.tsv.gz` `c43305f5e3c3eb2f112e5b7b7ae11e43eb4b73b51563c4a79405ed74101649fd`
- `audit/frozen/panel_tables.md` `9964edaa8713dd70349943c39acb6903c6201065d180de59f315ba0f66b44052`
- `audit/frozen/panel_tables_heldout.md` `038d1084f05d53e94e161fe56ea1cf3524704354ace9df35a2ec51fe66fb968c`
- `audit/frozen/panel_numbers.json` `74b71d61038cc6c34953b816032eacacf1a632d81c53f070979b032667a3a657`
- `audit/frozen/panel_numbers_heldout.json` `a1fe56054bd25e258335c05a87651605a160387b3d05d435f1c98480aa7b5852`
- `audit/frozen/finding_shares.json` `9e0e8d1e7ef63420699c1a9377042df1a9d03d8533aa914827d5aa1ec1db3f2f`
- `audit/frozen/leading_ws_effect.json` `acea163d006566ff8e1e8cfc3c02dc012f6b78b48e36de45bb802c88cd24c861`
- `audit/frozen/disagreement_decomposition.json` `defe6368b6cd50efea58416cf35761437c2cef6aa89b4ac572498874aa01eb64`
- `audit/frozen/stress_results.json` `aabb0cfe5d181bb995e8e765eacc436b3b7efbcaf26d995f7bc16b95d2da2ce8`
- `audit/frozen/reftests_replacement_v4.json` `66a3df958b5df9522f13431757e0b5d20d638f2d7abf2d471e68acb7c64a079a`
- `audit/frozen/reftests_grader.json` `1911dbdfaba31a136c1020bef88bc17adc165a175c798259d0e508ee99c4f72e`
- `audit/frozen/fixture_table.tsv` `afc4881574d49c419b9dfe06f19fce17add0b7b6a0db6d628ed7d8134e520c52`
- `audit/replacement/contract_grader.py` `a03c1e5594733cc315193b0a1f93a836d73964752c46b35467634aa068d7076d`
- `audit/tests/fixtures_data.py` `2cb30400a85340671b39b29111ca4c53316b5b4b31362db487617d2aba7f1ea6`
