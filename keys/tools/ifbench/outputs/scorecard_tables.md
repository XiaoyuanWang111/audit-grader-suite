| Earlier audit's findings | Reported as a finding | As a decision entry | Not reported | Left out |
|---|---|---|---|---|
| holds under every reading (34) | 28 | 3 | 3 | 0 |
| rests on a decision (9) | 3 | 5 | 1 | 0 |
| protocol (7) | 3 | 2 | 1 | 1 |

| Earlier finding | Check | Class | Rerun's item | Note |
|---|---|---|---|---|
| F1 | repeat:repeat_span | finding | F-span-characters |  |
| F2 | ratio:overlap | decision entry | D-overlap | character trigrams are the grader's reading of D-overlap |
| F3 | format:sub-bullets | finding | F-subbullets-none, F-subbullets-any-hyphen, F-subbullets-bold |  |
| F4 | format:list | finding | F-list-anywhere |  |
| F5 (rests on a decision) | format:parentheses | decision entry | D-paren |  |
| F6 | ratio:sentence_words | finding | F-sentwords-no-word-check |  |
| F7 | count:keywords_multiple | decision entry | D-match | substring counts are the grader's reading of D-match |
| F8 | words:words_position | finding | F-wordspos-comma |  |
| F9 | custom:sentence_alphabet | finding | F-alphabet-story-quote |  |
| F10 | format:thesis | finding | F-thesis-anywhere | in part: not the `<em>` slicing |
| F11 | format:quote_unquote | finding | F-quote-curly | in part: not the guillemets |
| F12 | format:quotes | finding | F-quotes-apostrophe |  |
| F13 | count:conjunctions | finding | F-conj-surface-forms |  |
| F14 | custom:european_capitals_sort | finding | F-capitals-kyiv |  |
| F15 | custom:csv_quotes | finding | F-csvquotes-indexerror |  |
| F16 | custom:csv_special_character | finding | F-csvspecial-early-return |  |
| F17 | ratio:sentence_type, ratio:sentence_balance | finding | F-ratio-quote-endings | both checks |
| F18 | sentence:alliteration_increment | finding | F-alliteration-sum |  |
| F19 | format:newline | finding | F-newline-blank-offset |  |
| F20 | format:line_indent | finding | F-indent-blank-lines, F-indent-tabs |  |
| F21 | words:paragraph_last_first | finding | F-paralastfirst-comma |  |
| F22 | format:no_bullets_bullets | finding | F-nbb-blank-line, F-nbb-period, F-nbb-trailing-text |  |
| F23 | repeat:repeat_change | finding | F-repeatchange-whitespace |  |
| F24 | format:output_template | finding | F-template-presence-only |  |
| F25 | format:title_case | finding | F-title-contraction | in part: lowercase minor words are the decision D-title |
| F26 | format:options | finding | F-options-whitespace |  |
| F27 | format:emoji | finding | F-emoji-flag | in part, and only after the review: flags, not keycaps or an emoji followed by a letter |
| F28 | words:start_verb | finding | F-startverb-tagger |  |
| F29 (rests on a decision) | count:numbers | finding | F-numbers-joined |  |
| F30 | count:unique_word_count | decision entry | D-word | a standalone punctuation token as a word is the grader's reading of D-word |
| F31 (rests on a decision) | words:consonants | decision entry | D-word |  |
| F32 | words:prime_lengths | not reported | none | curly quotes count toward a word's length |
| F33 (rests on a decision) | count:words_japanese | decision entry | D-vacuous |  |
| F34 (rests on a decision) | words:last_first, words:paragraph_last_first, sentence:increment, format:line_indent | decision entry | D-vacuous |  |
| F35 (rests on a decision) | words:palindrome | decision entry | D-palindrome |  |
| F36 (rests on a decision) | words:keywords_specific_position | finding | F-position-contractions |  |
| F37 | custom:date_format_list | finding | F-dates-invalid | in part: month 00 and day 00, not 1801-02-29 |
| F38 | custom:reverse_newline, custom:word_reverse, custom:character_reverse | finding | F-wordrev-mixed, F-charrev-substring | two of the three checks |
| F39 | custom:mcq_count_length | finding | F-mcq-label-number | in part: not the text before the first label |
| F40 | words:last_first | not reported | none | a comma after the repeated word; F-lastfirst-quotes is another behavior of the check |
| F41 (rests on a decision) | words:start_verb | finding | F-startverb-markup |  |
| F42 (rests on a decision) | words:words_position | not reported | none | a list number shifts the word positions |
| F43 | format:emoji, sentence:keyword | not reported | none | a list label read as a sentence; D-sentence covers line breaks only |
| G1 | protocol | left out | F-loose-deletes-constrained | SKILL.md names loose grading; left out of the counts |
| G2 | protocol | finding | F-options-whitespace | in part: the fixture on prompt 105, not the conflict of its two instructions |
| G3 | protocol | decision entry | D-options |  |
| G4 | protocol | not reported | none | integer arguments stored as doubles |
| G5 | protocol | finding | F-pin-3, F-pin-4 |  |
| G6 | protocol | finding | F-csvquotes-indexerror | in part: the caller that the exception stops is not in the case |
| G7 | protocol | decision entry | D-sentence |  |

Rerun findings: 56. matches the earlier audit: 40; valid and new: 5; decision-level: 8; not about the grader: 3; false: 0.

| Rerun's finding | Class | Earlier finding or reason |
|---|---|---|
| F-pin-1 | not about the grader | the working directory records no commit for the vendored grader |
| F-pin-2 | not about the grader | the stored panel's settings file lacks stop sequences and one server version |
| F-pin-3 | matches the earlier audit | G5 |
| F-pin-4 | matches the earlier audit | G5 |
| F-conj-surface-forms | matches the earlier audit | F13 |
| F-numbers-joined | matches the earlier audit | F29 |
| F-pronouns-determiners | decision-level | one of the rerun's two reviewers marked all 3 reviewed cases ambiguous |
| F-punct-six-marks | valid and new | count:punctuation: only six marks and the interrobang are required; in 4 reviewed cases both reviewers gave a definite fail to a response the grader passed |
| F-wordcount-contractions | decision-level | the earlier audit's decision D-word-tokens (is `don't` one word) |
| F-japanese-skip-tokens | valid and new | count:words_japanese: a hyphen at position 5 is skipped; wrong whether or not a hyphen is a word |
| F-charrev-substring | matches the earlier audit | F38 |
| F-wordrev-mixed | matches the earlier audit | F38 |
| F-csvspecial-early-return | matches the earlier audit | F16 |
| F-dates-invalid | matches the earlier audit | F37 |
| F-capitals-kyiv | matches the earlier audit | F14 |
| F-mcq-label-number | matches the earlier audit | F39 |
| F-africa-numbering | valid and new | custom:reverse_newline: a numbered list in the right order fails; the same list without numbers passes |
| F-alphabet-story-quote | matches the earlier audit | F9 |
| F-indent-tabs | matches the earlier audit | F20 |
| F-indent-blank-lines | matches the earlier audit | F20 |
| F-list-anywhere | matches the earlier audit | F4 |
| F-newline-blank-offset | matches the earlier audit | F19 |
| F-nbb-blank-line | matches the earlier audit | F22 |
| F-nbb-trailing-text | matches the earlier audit | F22 |
| F-nbb-period | matches the earlier audit | F22 |
| F-options-case | decision-level | the earlier audit's decision D-option-case |
| F-options-whitespace | matches the earlier audit | F26, G2 |
| F-template-presence-only | matches the earlier audit | F24 |
| F-quote-curly | matches the earlier audit | F11 |
| F-quotes-apostrophe | matches the earlier audit | F12 |
| F-quotes-curly | decision-level | the earlier audit's decision D-curly-quotes |
| F-subbullets-none | matches the earlier audit | F3 |
| F-subbullets-any-hyphen | matches the earlier audit | F3 |
| F-subbullets-bold | matches the earlier audit | F3 |
| F-thesis-anywhere | matches the earlier audit | F10 |
| F-title-contraction | matches the earlier audit | F25 |
| F-ratio-quote-endings | matches the earlier audit | F17 |
| F-sentwords-no-word-check | matches the earlier audit | F6 |
| F-stopwords-contractions | decision-level | the earlier audit's decision D-word-tokens |
| F-repeatchange-whitespace | matches the earlier audit | F23 |
| F-span-characters | matches the earlier audit | F1 |
| F-alliteration-sum | matches the earlier audit | F18 |
| F-position-contractions | matches the earlier audit | F36 |
| F-lastfirst-quotes | valid and new | words:last_first: a quotation mark stays on the last word; the same sentence without quotes passes |
| F-noconsec-digits | decision-level | the earlier audit's decision D-non-word-tokens (are numbers words) |
| F-paralastfirst-comma | matches the earlier audit | F21 |
| F-startverb-tagger | matches the earlier audit | F28 |
| F-startverb-markup | matches the earlier audit | F41 |
| F-wordspos-comma | matches the earlier audit | F8 |
| F-csvquotes-indexerror | matches the earlier audit | F15, G6 |
| F-loose-deletes-constrained | matches the earlier audit | G1 |
| F-extract-unclosed | not about the grader | the stored panel keeps responses whose reasoning never closes |
| F-sentence-html-tags | valid and new | sentence checks: a period followed by an HTML closing tag does not end a sentence, so `<i>Cats sleep.</i> Dogs run fast.` is one sentence; added after the review. The earlier audit notes the behavior under its open question on sentences and found no changed verdict |
| F-wordcount-html-tags | decision-level | the earlier audit's decision D-non-word-tokens (are HTML tags words); added after the review |
| F-emoji-flag | matches the earlier audit | F27 |
| F-quote-separator | decision-level | the earlier audit's decision D-explanation-word (is a symbol after a quote an explanation); added after the review |
