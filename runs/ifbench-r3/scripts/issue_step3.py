p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep("- Later changes to the contract are listed here with their reason.\n",
    """- Later changes to the contract are listed here with their reason.
- Version 2, 2026-11-09 22:43 UTC, sha256 5175ec90cbced57cadf39c59e9976731a73ef803e231b06f56df5adc0b0bb813
  (copy `audit/frozen/CONTRACT_v2.md`), written after the grader code was read; no proposed
  reading changed. D-paragraph gains reading C (every line break starts a paragraph) and
  D-options gains reading D (only the bare option string counts). Reason: both are readings a
  careful reader could defend that version 1 omitted (details at the top of the decision table).
  Effect: two fixtures that the grader fails (`words:vowel-f01e48fd`, `format:options-ff170446`)
  count as decisions, not findings.
""")
rep("| 3. Fixtures | not started | `audit/tests/` |",
    "| 3. Fixtures | done 2026-11-09 22:50 UTC: 277 fixtures, grader wrong on 84 (52 finding, 32 decision) | `audit/tests/fixtures_data.py`, `test_fixtures_grader.py` |")
rep("Next: build fixtures (step 3) in `audit/tests/`, labeled from `audit/CONTRACT.md` alone.",
    "Next: step 4 (reference comparison, reference unit tests against a replacement, property and\n"
    "metamorphic tests, fuzzing, content-free responses, loose transform), then the replacement grader.")
rep("## Findings\n",
    """## Step 3. Fixtures

- `audit/tests/fixtures_data.py`: 277 fixtures, at least a pass, a fail and a near-miss for every
  one of the 58 checks (68 pass, 57 fail, 62 near-miss, 47 defect reproductions, 43 decision
  probes). Labels come from the contract's proposed readings; `decisions` lists the entries
  whose other readings would flip a label. Id = check + first 8 hex of sha256(kwargs, response).
- `audit/tests/test_fixtures_grader.py` runs them against the grader (strict); the 84 the grader
  gets wrong carry `pytest.mark.xfail(strict=True)` with the finding or decision id as reason.
  `test_fixtures_reference.py` does the same for the reference (75 wrong: 46 finding, 29
  decision). Run: `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider audit/tests`
  (2026-11-09 22:48 UTC: 395 passed, 159 xfailed).
- Grader-wrong fixtures that are decisions (a non-proposed reading makes the grader right):
  D-vacuous 7, D-word 3, D-custom-facts 3, D-csv 2, D-match 2, D-palindrome 2, and one each for
  D-conj, D-indent, D-options, D-overlap, D-paragraph, D-paren, D-punct-set, D-repeat-change,
  D-section, D-sentence, D-subbullet, D-template, D-title.

## Findings
""")

FINDINGS = r"""
Checker findings from step 3 (verdict wrong under every reading the text allows). Fixture ids
are in `audit/tests/fixtures_data.py`; "Ref" gives the reference's status at 1c40f0c. Shares of
verdicts affected are added in step 5.

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
"""
anchor = "| F-pin-4 | dataset | `eval_instruct.py` loads `allenai/IFBench_test` without a revision, so a dataset update changes prompts and kwargs silently. | `eval_instruct.py` `load_questions` |\n"
rep(anchor, anchor + FINDINGS)
s = s.replace("- 2026-11-09 22:30 UTC: read the grader and the reference code (diff: the reference commit fixes 7 checkers); code-level pins recorded.\n",
              "- 2026-11-09 22:30 UTC: read the grader and the reference code (diff: the reference commit fixes 7 checkers); code-level pins recorded.\n"
              "- 2026-11-09 22:43 UTC: contract version 2 (two readings added, reasons above).\n"
              "- 2026-11-09 22:50 UTC: step 3 done, 277 fixtures; findings table added.\n")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
