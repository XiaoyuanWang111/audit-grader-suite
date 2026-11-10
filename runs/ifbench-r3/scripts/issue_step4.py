p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


STEP4 = """## Step 4. Reference comparison and stress (2026-11-09, 23:10 to 23:45 UTC)

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
  Evalchemy and not in the case). Reproduce: header line of prompt 275 plus a data row ending
  in a tab.
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

"""
rep("## Findings\n", STEP4 + "## Findings\n")
FIND = """| F-indent-blank-lines | format:line_indent | One blank line between stairs is ignored, two consecutive blank lines fail the response (list mutated while iterated). | test_properties.py::indent-second-blank-line | same |
| F-csvquotes-indexerror | custom:csv_quotes | Any empty field raises IndexError, which stops the per-prompt function. | step 4 targeted input | same |
| F-loose-deletes-constrained | loose transform (all checks) | Loose grading passes responses by deleting the first or last line or every `*`, text the instructions constrain. | test_properties.py::loose-* | same |
"""
anchor = "| F-wordspos-comma | words:words_position | Punctuation tokens count as words except one at the very end. | words:words_position-bd6267af | fixed |\n"
rep(anchor, anchor + FIND)
rep("| 4. Reference comparison and stress | not started | |",
    "| 4. Reference comparison and stress | done 2026-11-09 23:45 UTC | this file, \"Step 4\"; `audit/tests/test_properties.py` |")
rep("Next: step 4 (reference comparison, reference unit tests against a replacement, property and\n"
    "metamorphic tests, fuzzing, content-free responses, loose transform), then the replacement grader.",
    "Next: step 5 analysis of `audit/work/panel_verdicts.jsonl` (`audit/scripts/analyze_panel.py`), then\n"
    "step 6.1-6.3 (`audit/scripts/draw_review_sample.py`).")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
