# Audit of the IFBench grader in Marin's Evalchemy copy

Report of the audit skill's step 7, written 2026-11-10 23:13 UTC. The record of
the audit (pinned inputs, contract hashes and changes, step results) is in
`audit/ISSUE.md`; the contracts are in `audit/CONTRACTS.md` (v4).

**Recommendation: fix the grader** (provisional until step 6 runs; see
"What step 6 still has to show"). The defects are fixable checker bugs and
unpinned inputs, not a broken benchmark. Fixing them changes per-model strict
scores by up to 5 points and swaps the order of 9 of 120 model pairs.

## 1. Error rate and effect on scores

**Error rate: not estimated.** Step 6 (blinded review) was not run in this
exercise, so there is no consensus label set and no error-rate interval for any
grader. What the panel does measure is how often the grader under audit
disagrees with the replacement grader built from the contracts, and how much
that moves scores:

- Panel: 16 configurations, 228 stored runs, 68,400 responses, 78,432 check
  verdicts (no new generation). Scored coverage is 100% for every grader: no
  stored response makes a checker raise.
- Grader vs replacement (proposed readings): 6,329 verdicts differ (8.1%).
  3,147 (4.0%) are explained by a decision entry (some measured alternative
  reading gives the grader's verdict); 45 are reasoning-only responses
  (extraction failures, F-EXTRACT); 3,137 (4.0%) match no measured reading and
  are findings or replacement errors, which only the review can separate. On the
  held-out runs (16 runs, 5,504 verdicts) the shares are the same: 445 differ
  (8.1%), 224 by a decision, 206 unexplained, 15 extraction failures.
- Grader vs the benchmark authors' reference (allenai/IFBench at 1c40f0c):
  257 verdicts differ (0.33%), all in the checkers the reference has fixed since
  the copy was vendored (ratio:overlap 227, custom:sentence_alphabet 23,
  words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1).
  Every other finding below is shared by the reference.

Strict prompt-level accuracy (the primary metric), mean over each configuration's runs, in percent:

| Configuration | Runs | Grader | Reference | Grader + finding patches | Replacement | Replacement - grader | Findings only | Rerun diff (grader / repl.) | Run SD (grader) | Grader loose |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.1 | 34.1 | 32.0 | 29.0 | -5.1 | -2.1 | -1.0 / -0.3 | 1.5 | 37.8 |
| Qwen2.5-32B-Instruct | 13 | 35.2 | 35.2 | 33.5 | 33.5 | -1.7 | -1.7 | -1.3 / -0.7 | 1.9 | 38.3 |
| Qwen2.5-7B-Instruct | 17 | 27.4 | 27.5 | 25.7 | 25.4 | -2.0 | -1.7 | -0.3 / +0.0 | 1.4 | 30.4 |
| Qwen3-14B (thinking off) | 17 | 27.7 | 27.8 | 27.7 | 28.4 | +0.7 | -0.1 | -0.3 / +0.0 | 1.2 | 31.3 |
| Qwen3-14B (thinking on) | 3 | 34.3 | 34.7 | 37.4 | 37.9 | +3.6 | +3.1 | +1.0 / +1.0 | 0.5 | 39.3 |
| Qwen3-32B (thinking off) | 13 | 25.1 | 25.2 | 25.9 | 26.4 | +1.3 | +0.8 | -0.7 / +0.0 | 1.7 | 29.4 |
| Qwen3-8B (thinking off) | 17 | 25.2 | 25.1 | 25.3 | 24.6 | -0.6 | +0.1 | +0.0 / +0.3 | 1.1 | 29.5 |
| Qwen3-8B (thinking on) | 3 | 32.4 | 32.4 | 33.4 | 30.1 | -2.3 | +1.0 | +0.0 / +1.0 | 0.2 | 36.3 |
| Llama-3.1-Tulu-3-8B | 17 | 22.7 | 22.7 | 23.8 | 23.2 | +0.6 | +1.2 | +0.3 / +0.3 | 1.1 | 26.3 |
| OLMo-2-0325-32B-Instruct | 13 | 33.3 | 33.3 | 32.7 | 30.4 | -2.9 | -0.6 | +0.0 / +1.0 | 1.5 | 37.0 |
| OLMo-2-1124-13B-Instruct | 17 | 22.6 | 22.7 | 21.7 | 19.3 | -3.3 | -1.0 | +0.0 / +0.0 | 1.2 | 26.8 |
| OLMo-2-1124-7B-Instruct | 17 | 20.4 | 20.4 | 20.6 | 18.7 | -1.6 | +0.3 | +0.7 / +0.3 | 0.7 | 24.9 |
| marin-8b-instruct | 17 | 17.4 | 17.4 | 17.5 | 16.8 | -0.6 | +0.2 | -1.0 / -0.3 | 1.2 | 21.5 |
| phi-4 | 17 | 19.1 | 19.3 | 20.1 | 20.7 | +1.6 | +1.1 | +0.0 / +0.0 | 1.8 | 24.3 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.6 | 17.6 | 17.6 | 17.1 | -0.5 | -0.0 | +0.3 / -0.3 | 0.9 | 20.8 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.8 | 22.3 | 24.3 | 23.5 | +1.6 | +2.4 | -0.3 / -0.3 | 1.5 | 27.9 |
| **Pooled** | 228 | 24.9 | 25.0 | 24.9 | 24.0 | -0.9 | -0.0 | | | 29.0 |

- "Grader + finding patches" is the grader with every minimal finding patch of
  section 2 applied (start_verb excluded, its patch is approximate). "Findings
  only" is that column minus the grader; the rest of "Replacement - grader"
  comes from the decision readings the replacement proposes and from checks
  whose patch is the replacement's own logic.
- Noise: rerunning greedy decoding with identical settings (greedy vs
  greedy_repeat) moves a configuration's score by at most 1.3 points (grader)
  and 1.0 (replacement); the run-to-run SD over each configuration's runs is
  0.2 to 1.9 points. Five configurations move by more than both rerun
  differences and twice the run SD: Qwen2.5-14B (-5.1), Qwen3-14B thinking
  (+3.6), Qwen3-8B thinking (-2.3), OLMo-2-13B (-3.3), OLMo-2-7B (-1.6).
- Ranking: Kendall tau between the grader's and the replacement's model order
  is 0.85; 9 of 120 pairs swap (for example Qwen3-14B thinking now ranks above
  Qwen2.5-32B, and Mistral-Small-24B above OLMo-2-13B).
- Instruction-level accuracy, pooled: grader 27.7%, reference 27.6%,
  replacement 26.2%. Loose grading (reported by the harness as a secondary
  metric) adds 4.0 prompt-level points over strict, and about 71% of the passes
  it adds are contradicted by the contract (F-LOOSE).
- Truncation: 4,165 responses (6.1%) hit the token limit; they stay in every
  denominator. Extraction failures: 136 thinking-on completions never close
  `</think>` (Qwen3-8B thinking 104 of 900, Qwen3-14B thinking 32 of 900, all
  truncated at 8,192 tokens). Under the contract they fail every check, which
  lowers Qwen3-8B thinking by a further 2.8 points (F-EXTRACT).

Sources: `audit/work/panel_summary.json`, `panel_extra.json`,
`patched_grader.json`, `finding_shares.json` (frozen copies and hashes in
`audit/ISSUE.md`).

## 2. Findings

To reproduce any fixture case (from `W = <W>`, Git Bash):

    cd <W>
    export NLTK_DATA=<W>/case/deps/nltk_data
    .venv/Scripts/python.exe audit/scripts/verdict.py --fixture '<fixture id>'

It prints the input, the contract label, and the verdicts of the grader (strict
and loose), the reference and the replacement. Panel cases use
`verdict.py --panel <folder> <run> <key>`. `audit/scripts/report_cases.py check`
re-runs every case below and checks the verdicts stated here (last run: 0
mismatches). Inputs are written as Python `ascii()` literals, so `\n`, `\t` and
`\u201c` stand for the actual characters.

"Share" is the share of that check's panel verdicts that flip when only this
defect is patched (`audit/scripts/finding_probes.py`; the probe is a minimal
patch, the reference's fixed checker, or the replacement's logic for that check,
as noted), out of all 78,432 verdicts in brackets. "Ref." is the reference's
verdict on the same input / whether the reference has the defect.

### Pipeline and pinning

| Id | Stage | Evidence | Contract or rule broken | Share | Reference |
|---|---|---|---|---|---|
| F-PIN-DATASET | data loading | `eval_instruct.py` calls `load_dataset("allenai/IFBench_test", split="train")` with no `revision=` | step 1: every input that can change a verdict is pinned | all verdicts depend on it; verify by recording the resolved revision in the run record | reference reads a vendored JSONL |
| F-PIN-NLTK | dependencies | `instructions_util.py` runs `nltk.download("punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger_eng")` at import when missing, unversioned; `instructions.py` creates `IFBench/.nltk_data/` inside the package and puts it first on `nltk.data.path` | step 1 | the 17 checks whose checker calls the punkt tokenizer, the tagger or the stop-word list (`audit/scripts/claims_check.py`) | same code |
| F-PIN-GRADER | provenance | no Marin or Evalchemy commit is recorded for the vendored copy; it lacks the fixes the reference commit 1c40f0c has in six checkers (5 of the reference's unit tests fail on it) | step 1 | 257 verdicts differ from the reference (0.33%) | n/a |
| F-PIN-VLLM | generation | `case/panel/CONFIGS.md`: vLLM version "not recorded" for both thinking configurations | step 1 | 1,800 responses | n/a |
| F-EXTRACT | graded text | the vendored code has no reasoning extraction (it lives in Evalchemy's `text_specs`, not provided: UNVERIFIED). With the panel's rule, a completion with no `</think>` is graded on its reasoning text | contract G1/G2: reasoning that never closes is an extraction failure and fails every check | 136 responses, 157 verdicts; the grader passes 45 of them; -2.8 points for Qwen3-8B thinking | same harness |
| F-EXC | harness | fixture `custom:csv_quotes#1737bf8c` (input in the table below) raises `IndexError` in `QuotesCSVChecker`; `grader.py` has no try/except, so one exception stops the whole run (shown for the grader's strict loop and the reference `run_eval` replica, `loose_and_contentfree.py`) | G8: an exception is a grading failure, counted separately, and must not stop the run | 0 panel responses; fuzzing: 10 of 40,616 calls | same |
| F-LOOSE | score transform | loose grading passes a check if any of 8 edited responses passes (first/last line dropped, every `*` deleted). Example: `format:options` key 100, response `'Yes\nBecause games can teach empathy.'` -> strict False, loose True; `format:sub-bullets` passes any response once `*` is deleted | G9: a pass obtained only on an edited response contradicts the contract unless the contract ignores the removed content | 2,604 of the 3,666 passes loose adds over strict (71.0%) fail the contract | same |

### Checker findings with fixtures

| Id | Check | Fixture | Exact input | Label | Grader | Ref. |
|---|---|---|---|---|---|---|
| F-CONJ | count:conjunctions (key 9, N=4) | `count:conjunctions#85e471f8` | `'Tea and cake and, jam. And milk. AND bread.'` | fail | True | True |
| F-KWM | count:keywords_multiple (key 2) | `count:keywords_multiple#487922bc` | `'A door. Bread and bread. Blue, blue, blue. Lamp lamp lamp lamp lamp. River river river river river river river. The driver waved.'` | pass | False | True |
| F-NUM | count:numbers (key 17, N=2) | `count:numbers#57019ffa` | `'From 1990-2005 the town grew.'` | pass | False | False |
| F-CONTRACTION | count:word_count_range (key 42, 57-61) | `count:word_count_range#7c51fcd2` | 52 NATO words + `" don't can't won't isn't aren't."` (57 words; full literal printed by the command) | pass | False | False |
| F-CONTRACTION | ratio:stop_words (key 175, 39%) | `ratio:stop_words#2cf31b94` | `"Cats don't bark loudly."` | pass | False | False |
| F-STYPE | ratio:sentence_type (key 163) | `ratio:sentence_type#3738487b` | `'Wow! Amazing!'` | fail | True | True |
| F-STYPE | ratio:sentence_type | `ratio:sentence_type#389403cd` | `'It is so. It is "true." Why?'` | pass | False | False |
| F-SBAL | ratio:sentence_balance (key 155) | `ratio:sentence_balance#b7761e44` | `'He had critics. "Why?" "Stop!"'` | pass | False | False |
| F-SWORDS | ratio:sentence_words (key 166) | `ratio:sentence_words#9bf12340` | `'Cats sleep all day. Dogs sleep all day. Fish swim in ponds.'` | fail | True | False |
| F-INDENT | format:line_indent (key 74) | `format:line_indent#5ca22c1c` | `'Step one\n\n\n  Step two\n    Step three'` | pass | False | False |
| F-INDENT | format:line_indent | `format:line_indent#3006987f` | `'Step one\n\tStep two\n\t\tStep three'` | pass | False | False |
| F-NEWLINE | format:newline (key 90) | `format:newline#e5f78837` | `'Alpha Beta\n \nGamma'` | fail | True | True |
| F-NEWLINE | format:newline | `format:newline#07733d8b` | `'Alpha\n \nGamma'` | pass | False | False |
| F-LIST | format:list (key 86, SEP `-`) | `format:list#2584034b` | `'Entanglement is a well-known effect in state-of-the-art physics.'` | fail | True | True |
| F-LIST | format:list (key 83, SEP `!?!?`) | `format:list#10c5eeb0` | `'!?!? Preludes are short.\n* Caprichos are lively.\n!?!? Romances are lyrical.'` | fail | True | True |
| F-NBB | format:no_bullets_bullets (key 98) | `format:no_bullets_bullets#625c6237` | `'Deism is weak.\n\nIt ignores revelation.\n* Point one\n* Point two'` | pass | False | False |
| F-NBB | format:no_bullets_bullets | `format:no_bullets_bullets#d44d9892` | `'Deism is weak. It ignores revelation.\n* Point one\n* Point two\n'` | pass | False | False |
| F-NBB | format:no_bullets_bullets | `format:no_bullets_bullets#653b564a` | `'Deism is weak. It ignores revelation.\n\n* Point one\n* Point two\n\nIn sum, deism fails.'` | pass | False | False |
| F-NBB | format:no_bullets_bullets | `format:no_bullets_bullets#41d069e7` | `'Deism is weak! It ignores revelation!\n* Point one\n* Point two'` | fail | True | True |
| F-OPTIONS | format:options (key 100, yes/no/maybe) | `format:options#927580bf` | `'Yes\n'` | pass | False | False |
| F-OPTIONS | format:options (key 101) | `format:options#bf4d4ea8` | `'I don\u2019t know'` | pass | False | False |
| F-TEMPLATE | format:output_template (key 292) | `format:output_template#3880c6d1` | `'Sure, here it is.\nMy Answer: X.\nMy Conclusion: Y.\nFuture Outlook: Z.'` | fail | True | True |
| F-TEMPLATE | format:output_template | `format:output_template#e6f2680a` | `'My Conclusion: Y.\nMy Answer: X.\nFuture Outlook: Z.'` | fail | True | True |
| F-TEMPLATE | format:output_template | `format:output_template#32aa85d6` | `'My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]'` | fail | True | True |
| F-PAREN | format:parentheses (key 110) | `format:parentheses#9fc38630` | `'((((( x )'` | fail | True | True |
| F-QU | format:quote_unquote (key 116) | `format:quote_unquote#9f008108` | `'"a", "b" means x'` | fail | True | True |
| F-QU | format:quote_unquote | `format:quote_unquote#278caa31` | `'The claim is \u201cfalse\u201d'` | fail | True | True |
| F-QUOTES | format:quotes (key 120) | `format:quotes#60347bc9` | `'\u201cShe said \u2018He wrote \u201cyes\u201d there\u2019 again\u201d'` | pass | False | False |
| F-SUBB | format:sub-bullets (key 132) | `format:sub-bullets#212d5ee1` | `'Memorization is copying.'` | fail | True | True |
| F-SUBB | format:sub-bullets | `format:sub-bullets#da21f6a4` | `'* A well-known fact\n* Another long-term view'` | fail | True | True |
| F-SUBB | format:sub-bullets | `format:sub-bullets#35b65fdf` | `'**Overview**\n* Memorization\n  - Copying\n* Why care\n  - Privacy'` | pass | False | False |
| F-THESIS | format:thesis (key 142) | `format:thesis#844e324a` | `'It favors tradition, <i>the party is conservative</i>.'` | fail | True | True |
| F-THESIS | format:thesis | `format:thesis#8b0c3daa` | `'<i>The party is conservative.</i>'` | pass | False | False |
| F-TITLE | format:title_case (key 291) | `format:title_case#95beef7e` | `"Don't Stop Believing."` | pass | False | False |
| F-TITLE | format:title_case | `format:title_case#26d02f70` | `'The Party of Japan'` | pass | False | False |
| F-ALLIT | sentence:alliteration_increment (key 179) | `sentence:alliteration_increment#1a1b19f2` | `'ReLU is simple. Big bold models matter. Very vast vectors vary.'` | pass | False | False |
| F-ALLIT | sentence:alliteration_increment | `sentence:alliteration_increment#20fedc4e` | `'Very vast vectors. Big bold cats, tiny tame dogs, red rats.'` | fail | True | True |
| F-CAPITALS | custom:european_capitals_sort (key 278) | `custom:european_capitals_sort#113de779` | `'Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb'` | pass | False | False |
| F-AFRICA | custom:reverse_newline (key 281) | `custom:reverse_newline#1d2258e7` | the 54 countries one per line in reverse order with Zambia and Zimbabwe swapped: `'Zambia\nZimbabwe\nUganda\n...\nAlgeria'` | fail | True | True |
| F-AFRICA | custom:reverse_newline | `custom:reverse_newline#1a03b821` | the same list correctly ordered and numbered: `'1. Zimbabwe\n2. Zambia\n...\n54. Algeria'` | pass | False | False |
| F-ALPHA-SENT | custom:sentence_alphabet (key 282) | `custom:sentence_alphabet#cca075f6` | 26 sentences A..Z, the third being `'"Coffee brewed slowly," she said.'` | pass | False | True |
| F-CSVSPECIAL | custom:csv_special_character (key 276) | `custom:csv_special_character#be0ed161` | header + `'P01,Tools,"Smith & Sons",11.99,3'` + 13 rows `'P02,Tools,Acme'` ... `'P14,Tools,Acme'` (3 fields) | fail | True | True |
| F-EXC | custom:csv_quotes (key 275) | `custom:csv_quotes#1737bf8c` | `'"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"S1"\t\t"A"\t"Fall"\t"95"\n"S2"\t"Art"\t"B"\t"Spring"\t"85"\n"S3"\t"Biology"\t"C"\t"Fall"\t"75"'` | fail | IndexError | IndexError |
| F-DATE | custom:date_format_list (key 277) | `custom:date_format_list#443b4fe3` | `'1796-00-00, 1805-12-02'` | fail | True | True |
| F-MCQ | custom:mcq_count_length (key 279) | `custom:mcq_count_length#278fd6e3` | 4 valid questions followed by `'\n\nExplanation: these test core knowledge.'` | fail | True | True |
| F-MCQ | custom:mcq_count_length | `custom:mcq_count_length#d7804689` | the same 4 questions with labels written `'**Question 1:**'` | pass | False | False |
| F-RCHANGE | repeat:repeat_change (key 61) | `repeat:repeat_change#093afd81` | the request unchanged plus `'\n'`: `'Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons.\n'` | fail | True | True |
| F-RCHANGE | repeat:repeat_change | `repeat:repeat_change#a49f0741` | the request unchanged with `'Use  Python'` (two spaces) | fail | True | True |
| F-RSPAN | repeat:repeat_span (key 284, indices 3..6) | `repeat:repeat_span#88520227` | `'code and theory behind'` | pass | False | True |
| F-VERB | words:start_verb (key 258) | `words:start_verb#45b07647` | `'Explore Galois theory through symmetry.'` | pass | False | False |
| F-VERB | words:start_verb | `words:start_verb#b16e7117` | `'**Consider** the field extension.'` | pass | False | False |
| F-WPOS | words:words_position (key 16, "despite") | `words:words_position#0b054f68` | `'Art, despite war, grew despite everything.'` | pass | False | True |
| F-MARKUP | count:person_names (key 27, N=3) | `count:person_names#44a20674` | `'Emma, _Liam_ and Sophia met at noon.'` | pass | False | False |
| F-MARKUP | words:no_consecutive (key 225) | `words:no_consecutive#6af2c5f4` | `'Honest <b>talks</b> build trust.'` | pass | False | False |

Panel cases (`verdict.py --panel ...`): F-QUOTES `Qwen__Qwen3-8B sample8 118`
(grader True, replacement False: apostrophes in "Scorpio's" are paired as
single quotes); F-SUBB `microsoft__phi-4 sample0 127` (grader False,
replacement True: `* **Personal Growth and Learning**` is split at every `*`);
F-NBB `marin-community__marin-8b-instruct bi_greedy 97` (grader False,
replacement True: blank line among the opening lines); F-PAREN
`Qwen__Qwen3-32B greedy_shuffled 110` (grader True, replacement False: 9
brackets opened, no properly closed group deeper than 1); F-VERB
`mistralai__Mistral-Small-24B-Instruct-2501 sample3 257` (grader False,
replacement True: the response opens with the imperative "Imagine").

What each finding is, the contract clause it breaks, and its share:

| Id | Defect | Contract broken | Share of check [of all] | Reference |
|---|---|---|---|---|
| F-CONJ | counts distinct raw tokens, so `and`, `and,`, `And`, `AND` are four conjunctions | count:conjunctions, G6 | 188 of 1,589 (11.8%) [0.24%] | same |
| F-KWM | counts substrings (`river` in `driver`) | G6 (v3) | 1 [0.00%] | fixed |
| F-NUM | deletes punctuation before counting digit runs, so `1990-2005` (also `/`, `:`) is one number | count:numbers | 5 (0.3%) | same |
| F-CONTRACTION | `\w+` tokens split `don't` into two words in word counts and stop-word ratios | G3 (both D-word readings count a contraction as one word) | word_count_range 57 (2.3%); stop_words 17 (0.6%) | same |
| F-STYPE | passes 0 declarative : 0 interrogative; misses sentences closed by a quote or bracket after `.`/`?` | ratio:sentence_type (interrogative >= 1); G4 | 19 (1.4%) | same |
| F-SBAL | misses sentences closed by a quote or bracket | G4 | 1 (0.1%) | same |
| F-SWORDS | does not check "all different words" | ratio:sentence_words | 1 (0.1%) | fixed |
| F-INDENT | removes blank lines while iterating, so two consecutive blank lines break it; tab indentation counts as none | format:line_indent | 2 (0.1%) | same |
| F-NEWLINE | whitespace-only lines count as lines (false pass and false fail) | format:newline | 5 (0.4%) | same |
| F-LIST | counts SEP anywhere (hyphens inside words count for SEP `-`; a `*` item is ignored) | format:list | 135 (6.6%) | same |
| F-NBB | its `sentences` flag is overwritten by the sentence list, so a blank line among the opening sentences returns False; any line after the bullets (even a trailing newline) returns False; `!`/`?` sentences count as "ending in a period" | format:no_bullets_bullets, G10 | 350 (30.7%) | same |
| F-OPTIONS | a trailing newline and a typographic apostrophe fail | G1, G10 | 0 in the panel | same |
| F-TEMPLATE | only checks that the three labels occur somewhere | format:output_template | 79 (8.7%) | same |
| F-PAREN | returns True as soon as any pair closes after 5 brackets were opened | format:parentheses ("properly matched") | 201 (11.0%) | same |
| F-QU | a quote followed only by punctuation and another quote passes; typographic quotes are ignored (the replace call is a no-op) | format:quote_unquote, G10 | 96 (8.4%) | same |
| F-QUOTES | typographic quotes ignored; apostrophes treated as single quotes | format:quotes, G10 | 275 (15.1%) | same |
| F-SUBB | no `*` at all passes; `-` anywhere (hyphenated words) counts as a sub-bullet; `**bold**` splits bullets | format:sub-bullets | 1,110 (40.6%) [1.4%] | same |
| F-THESIS | accepts the first `<i>`/`<em>` anywhere in the text; fails a section that is only its thesis | format:thesis | 206 (10.1%) | same |
| F-TITLE | requires minor words (`of`, `and`) to be capitalized, contradicting "every major word"; `n't` tokens always fail | format:title_case | 21 (2.3%) | same |
| F-ALLIT | measures the total number of alliterative words in a sentence, not the longest consecutive sequence | sentence:alliteration_increment | 120 (10.6%) | same |
| F-CAPITALS | the answer key omits Kyiv (50.45 N); every reading that keeps Moscow (as the key does) needs Kyiv | custom:european_capitals_sort | 0 in the panel (no model listed exactly the key or the corrected list) | same |
| F-AFRICA | ignores every line before the first line containing "Zimbabwe"; numbered lines fail | custom:reverse_newline | 3 (1.3%) | same |
| F-ALPHA-SENT | a sentence opening with a quotation mark fails | custom:sentence_alphabet | 23 (10.1%) | fixed |
| F-CSVSPECIAL | returns True at the first row with a quoted special field without checking later rows | custom:csv_special_character | 0 in the panel | same |
| F-DATE | accepts month 00 and day 00 | custom:date_format_list | 0 in the panel | same |
| F-MCQ | text after the last option passes; markup around the `Question` label fails | custom:mcq_count_length ("Do not provide an explanation"; markup allowed) | 36 (15.8%) | same |
| F-RCHANGE | "first word changed" is tested as "whole string differs", so the unchanged request with different whitespace passes | repeat:repeat_change | 0 in the panel | same |
| F-RSPAN | slices character indices although the prompt says word indices split by whitespace; every correct span fails | repeat:repeat_span | 0 in the panel (no response gave either span) | fixed |
| F-VERB | NLTK's tagger reads capitalized sentence-initial imperatives (`Explore`, `Write`, `Discover`, `Imagine`) as non-verbs; a leading `**` or list label is the first token | words:start_verb | 549 flips (40.1%) with the replacement's approximate tagger logic; 273 of them are not explained by D-verb-context. Needs the review | same |
| F-WPOS | punctuation tokens count as words | G3 | 5 (0.7%) | fixed |
| F-MARKUP | markup around a word changes verdicts: `_Liam_` defeats `\b` matching, `<b>talks</b>` leaves `btalksb`; also found by the metamorphic tests in count:pronouns, count:word_count_range, custom:reverse_newline, words:start_verb, format:options (typographic quotes) | G3, G10 | 0 in the panel for the probed checks | same |

Further evidence (step 4): the metamorphic edits (list label, bold, italics,
HTML tag, typographic quotes, punctuation after a word, blank line, trailing
newline) changed the grader's verdict in 27 (check, edit) pairs: 15 are
findings (above; 5 of them are start_verb), 12 are decisions (D-word,
D-word-numbers, D-strip-ends). The replacement
changed none. Content-free responses: restating the prompt passes 15 grader
checks, including `format:output_template` (the template is in the prompt),
`format:list`, `format:sub-bullets`, `format:line_indent` and
`sentence:alliteration_increment`; 40 repetitions of "This is a response."
pass 6 (count:pronouns, format:line_indent, format:quote_unquote,
format:sub-bullets, ratio:overlap, words:no_consecutive). Details:
`audit/ISSUE.md`, "Step 4 results".

## 3. Decision entries for the maintainers

Each entry is a point where the prompt text allows two verdicts. The proposed
reading is the one the contract and the replacement use; the effect is the
change in pooled replacement verdicts when that one entry takes the
alternative (`audit/work/panel_summary.json`, `decision_effects`; 78,432
verdicts, 68,400 prompt responses). "Grader" says which reading the grader
under audit implements.

| Entry | Proposed reading | Alternative | Grader | Effect of the alternative (verdicts; prompts) |
|---|---|---|---|---|
| D-options-text | option letter in any form (`c`, `C.`, `(c)`) or followed by its own text | label only; v4: the exact option string | exact string for letter options, loose for text options | label only -151; exact -624 (-569 prompts) |
| D-word | runs of letters/digits with internal `'` and `-`; markup and lone punctuation are not words | whitespace tokens compared as written | mixed by checker | -557 (+297/-699 prompts) |
| D-title-minor | minor words may take either case | minor words must be lower-case | neither (all words capitalized: F-TITLE) | -454 |
| D-sentence | ends at `. ! ? …` and at line breaks; headings are sentences | punkt sentences, no line breaks | punkt | -407 (+41/-388 prompts) |
| D-pronoun-set | personal, possessive, reflexive pronouns | also demonstratives, interrogatives, indefinites (`that`, `all`, `some`) | broad | +391 |
| D-subbullet-indent | `-` lines need not be indented | sub-bullets must be indented | no indentation (and no structure: F-SUBB) | -387 |
| D-vowel-scope | the whole response uses at most 3 vowel letters | each word has at most 3 | whole response | +366 |
| D-csv-rows | "N rows" = N data rows besides the header | N lines including the header | data rows | -360 |
| D-list-sep | SEP as line prefix or as inline separator | line prefix only | anywhere (F-LIST) | -356 |
| D-section | sections are headed blocks, else paragraphs | whole response is one section | first italic span anywhere (F-THESIS) | +326 |
| D-palindrome-distinct | 10 distinct palindromes | 10 occurrences | occurrences | +320 |
| D-count-exact | keyword counts exactly 1, 2, 3, 5, 7 | at least | exact | +307 |
| D-verb-context | verb in context (finite, imperative, auxiliary) | any word that can be a verb (gerunds) | POS tag VB* | +287 |
| D-punct-set | 13 marks (. , ? ! : ; ' " - dash () [] ...) plus `?!` | the six marks `. , ! ? ; :` plus `?!`/`!?`/`‽` | the six marks | +263 (short list with quotes: +161) |
| D-emoji-position | emoji before or after the terminal mark | emoji must be the last character | either | -251 |
| D-csv-wrapper | prose outside a code fence is ignored | the response must be CSV only | CSV only | -217 |
| D-number | digit runs (`3.14`, `1,000` one each) | also number words | digit runs | -154 |
| D-indent-min | at least two non-blank lines | one line passes | one line passes | +126 |
| D-list-intro-sep | an introduction line before the SEP items is allowed | not allowed | allowed | -125 |
| D-paren-types | any mix of `()[]{}` | all three kinds in the nesting | any mix | -124 |
| D-overlap-def | share of the response's word trigrams found in the reference text | reference-side share; Jaccard; character trigrams | character trigrams (reference: word trigrams) | char +123; reference-side +102; Jaccard +13 |
| D-between | "between A and B" inclusive | exclusive | inclusive | -89 |
| D-repeats-count | "repeat more than N times" = more than N occurrences | more than N repetitions (N+1 occurrences) | occurrences | +76 |
| D-word-numbers | digit-only tokens are not words for letter checks | they are | they are | -70 |
| D-date-extra | nothing but dates | labels allowed | nothing but dates | +70 |
| D-italic-tag | `<i>` or `<em>` | `<i>` only | both | -69 |
| D-unique-case | unique words case-insensitive | case-sensitive | insensitive | +68 |
| D-csv-one-field | at least one quoted special field | exactly one quoted field | at least one | -68 |
| D-indent-step | any increase | constant step | any | -64 |
| D-keyword-match | whole word, no inflections | inflected forms count | substring (F-KWM) | +49 |
| D-plural | one `*` bullet suffices | at least two | one | -41 |
| D-balanced | all three sentence types, counts within 1 | exactly equal counts | exactly equal (0:0:0 passes) | -33 |
| D-overlap-tol | +-2 percentage points | +-2% relative | points | -30 |
| D-quotes-start | outermost quote either kind | outermost double | either | -30 |
| D-mcq-length | question length in characters | in words | characters | -26 |
| D-capitals-complete | all capitals required | order and membership only | complete (27-name key) | +23 |
| D-strip-ends | leading/trailing whitespace of the answer is ignored | it counts | counts (no_whitespace fails on a trailing newline) | -15 |
| D-sentence-type | unterminated lines count as declarative | excluded | excluded | +13 |
| D-consonant-y | `y` is a consonant | a vowel | consonant | -11 |
| D-special-char | non-alphanumeric, excluding `.`/`-`/`,` inside numbers | any non-alphanumeric | any non-word character | +10 |
| D-template-markup | markup around labels allowed | plain labels only | presence only (F-TEMPLATE) | -9 |
| D-vowel-paragraph | one paragraph (blank-line blocks) | several allowed | one line | +6 |
| D-span-base | word indices 0-based | 1-based | character indices (F-RSPAN) | +5 |
| D-paragraph-newline | each non-blank line is a paragraph | blank-line blocks | lines | +3 |
| D-reverse-extra, D-reverse-answer | nothing but the reversed answer, which names the eagle | extra text allowed / any reversed sentence | substring `elgae dlab` / `bald eagle` after reversal | -1 (+10/-11 prompts) |
| D-char-count, D-different-words | all characters; no word twice in the response | letters only; no word shared across sentences | all characters; no word check (F-SWORDS) | -1 |
| D-name-case | names case-sensitive | case-insensitive | sensitive | +1 |
| D-paragraph | blank-line blocks | single newlines | lines (words:vowel) | measured with D-vowel-paragraph |
| D-empty, D-vacuous | empty fails; no units -> literal pass | vacuous pass / presupposition fails | empty fails; literal | not measured (harness guard; not switchable) |
| D-conj-role, D-japanese-seg, D-japanese-script, D-alliteration, D-syllables, D-quote-explanation, D-africa-set, D-alphabet-start, D-repeat-tail, D-ratio-exact, D-bullet-marker, D-whitespace-set, D-multiples-extra, D-list-intro, D-africa-complete, D-csv-header-quoted | see `audit/CONTRACTS.md` | | | no measurable effect on the panel (under 5 verdicts) or not computable from text alone (grammatical role, pronunciation, semantic explanation) |

Entries that most change model scores are D-options-text, D-word,
D-title-minor, D-sentence, D-pronoun-set and D-subbullet-indent (each moves
300-600 verdicts). Choosing all proposed readings versus the grader's readings
accounts for the "Replacement - grader" column minus the "Findings only" column
in section 1.

## 4. What this audit could not do

- No issue tracker, repository, research branch, Hugging Face dataset or job
  launcher: the issue record is `audit/ISSUE.md`; fixtures are pytest tests in
  `audit/tests/` (`test_fixtures.py`, strict xfail marks listed in
  `xfail_ids.py`); frozen files are in `audit/frozen/` with sha256 in the issue;
  scripts and the replacement are under `audit/`. No `file-issue`,
  `research-engineering`, `manage-pr` or `use-iris` step was run, and the issue
  writing-style guide (`docs/dev-guide/writing-style/issues.md`) was not
  available.
- No compute: the panel is the stored responses only. No rerun of any
  configuration was generated; the rerun comparison uses the stored
  greedy/greedy_repeat pairs.
- Step 6 not run (no reviewers): no error rate, no interval, no kappa, no
  disputed-case list, no confusion matrix.
- Not verified: Marin's and Evalchemy's commits; how Evalchemy extracts the
  graded text (`eval.sources.common.text_specs` and the `instructions` grader
  registry are not in the case); whether Evalchemy catches checker
  exceptions; the dataset revision a real run resolves.
- Side effect to know about when rerunning: importing the grader (or the
  reference) creates an empty `.nltk_data/` directory inside its package
  (F-PIN-NLTK). The audit removed the two it created under `case/` at the end
  (23:20 UTC) and `case/MANIFEST.sha256` verifies; rerunning the commands above
  creates them again. No bytecode was written under `case/`.
- The replacement approximates three readings that need language judgment:
  start_verb (POS tags plus an infinitive test), syllable counts (syllapy word
  list), and quote explanations (any unquoted word). Its verdicts on those
  checks are the least certain.

## 5. What step 6 still has to show

Pre-registered result that would change the recommendation (also in
`audit/ISSUE.md`):

- Adopt the replacement (with the maintainers' readings) if it passes every
  fixture (it does: 426 of 426), has complete scored coverage (it does), and its
  error rate is lower than the grader's with a paired 95% bootstrap interval
  that excludes zero.
- Otherwise fix only the findings whose cases reviewers confirm, starting with
  F-SUBB, F-NBB, F-QUOTES, F-PAREN, F-THESIS, F-CONJ, F-LIST, F-ALLIT,
  F-TEMPLATE and F-QU, and re-vendor the reference commit for the six checkers
  it has fixed.
- Sample: from the held-out runs only (16 runs, 4,800 responses, 5,504
  verdicts), because the replacement was adjusted on the other runs. Stratify
  by grader-vs-replacement disagreement: all 445 held-out disagreements
  (15 of them extraction failures) and at least 170 agreement cases with a
  consensus, so that each grader's upper bound can fall below 2% when no error
  is found there (agreement is 91.9% of the held-out verdicts, and
  0.919 x (1 - 0.025^(1/n)) < 0.02 needs n >= 168). Two reviewers
  per case, blinded to graders and models, with
  `skill/references/reviewer-prompt.md`.
- The review must settle the 206 held-out disagreements that no decision
  explains (findings vs replacement errors), above all the start_verb cases
  (273 unexplained panel-wide), and report the error rate of the grader and of
  the replacement per stratum.

Until then, treat IFBench scores from this grader as moving by up to 5 points
per model for reasons unrelated to the models, and do not compare them with
scores from the authors' current reference without noting the 257-verdict
difference.
