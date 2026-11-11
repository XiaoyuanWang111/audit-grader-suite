# Panel tables (held-out files only)

Verdict rows (response x instruction): 5504

## Scored coverage and grading failures

| column | verdicts | pass | fail | exception | coverage |
|---|---|---|---|---|---|
| g_strict | 5504 | 1608 | 3896 | 0  | 100.000% |
| g_loose | 5504 | 1865 | 3639 | 0  | 100.000% |
| r_strict | 5504 | 1604 | 3900 | 0  | 100.000% |
| r_loose | 5504 | 1856 | 3648 | 0  | 100.000% |
| rep | 5504 | 1546 | 3958 | 0  | 100.000% |
| rep_gr | 5504 | 1592 | 3912 | 0  | 100.000% |

## Strict prompt-level accuracy per configuration (mean over runs, %)

| configuration | runs | grader | reference | replacement | replacement, grader's readings | replacement - grader | of which decisions | of which defects | grader loose | rerun diff (grader, greedy vs greedy_repeat) | rerun diff (replacement) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 1 | 37.00 | 37.00 | 32.00 | 32.00 | -5.00 | +0.00 | -5.00 | 40.00 | nan | nan |
| Qwen__Qwen2.5-32B-Instruct | 1 | 34.67 | 34.67 | 35.00 | 34.00 | +0.33 | +1.00 | -0.67 | 38.00 | nan | nan |
| Qwen__Qwen2.5-7B-Instruct | 1 | 28.00 | 28.00 | 28.00 | 28.00 | +0.00 | +0.00 | +0.00 | 30.67 | nan | nan |
| Qwen__Qwen3-14B | 1 | 26.00 | 26.67 | 27.00 | 27.00 | +1.00 | +0.00 | +1.00 | 30.33 | nan | nan |
| Qwen__Qwen3-14B__thinking | 1 | 35.00 | 35.33 | 38.00 | 39.67 | +3.00 | -1.67 | +4.67 | 39.67 | nan | nan |
| Qwen__Qwen3-32B | 1 | 26.00 | 26.33 | 25.00 | 25.67 | -1.00 | -0.67 | -0.33 | 31.67 | nan | nan |
| Qwen__Qwen3-8B | 1 | 25.33 | 25.33 | 25.00 | 25.67 | -0.33 | -0.67 | +0.33 | 29.00 | nan | nan |
| Qwen__Qwen3-8B__thinking | 1 | 32.33 | 32.33 | 31.00 | 32.00 | -1.33 | -1.00 | -0.33 | 37.00 | nan | nan |
| allenai__Llama-3.1-Tulu-3-8B | 1 | 23.00 | 23.00 | 25.00 | 25.00 | +2.00 | +0.00 | +2.00 | 26.00 | nan | nan |
| allenai__OLMo-2-0325-32B-Instruct | 1 | 32.67 | 32.67 | 31.00 | 32.67 | -1.67 | -1.67 | +0.00 | 36.33 | nan | nan |
| allenai__OLMo-2-1124-13B-Instruct | 1 | 23.67 | 24.00 | 19.67 | 21.67 | -4.00 | -2.00 | -2.00 | 28.33 | nan | nan |
| allenai__OLMo-2-1124-7B-Instruct | 1 | 20.33 | 20.33 | 18.33 | 19.00 | -2.00 | -0.67 | -1.33 | 24.67 | nan | nan |
| marin-community__marin-8b-instruct | 1 | 18.00 | 18.00 | 17.67 | 17.33 | -0.33 | +0.33 | -0.67 | 23.33 | nan | nan |
| microsoft__phi-4 | 1 | 21.33 | 21.33 | 21.00 | 22.00 | -0.33 | -1.00 | +0.67 | 26.33 | nan | nan |
| mistralai__Mistral-7B-Instruct-v0.3 | 1 | 18.67 | 18.67 | 16.33 | 18.33 | -2.33 | -2.00 | -0.33 | 21.00 | nan | nan |
| mistralai__Mistral-Small-24B-Instruct-2501 | 1 | 20.67 | 21.33 | 23.67 | 23.00 | +3.00 | +0.67 | +2.33 | 28.33 | nan | nan |

Ranking by grader strict: 1. Qwen__Qwen2.5-14B-Instruct, 2. Qwen__Qwen3-14B__thinking, 3. Qwen__Qwen2.5-32B-Instruct, 4. allenai__OLMo-2-0325-32B-Instruct, 5. Qwen__Qwen3-8B__thinking, 6. Qwen__Qwen2.5-7B-Instruct, 7. Qwen__Qwen3-14B, 8. Qwen__Qwen3-32B, 9. Qwen__Qwen3-8B, 10. allenai__OLMo-2-1124-13B-Instruct, 11. allenai__Llama-3.1-Tulu-3-8B, 12. microsoft__phi-4, 13. mistralai__Mistral-Small-24B-Instruct-2501, 14. allenai__OLMo-2-1124-7B-Instruct, 15. mistralai__Mistral-7B-Instruct-v0.3, 16. marin-community__marin-8b-instruct

Ranking by replacement: 1. Qwen__Qwen3-14B__thinking, 2. Qwen__Qwen2.5-32B-Instruct, 3. Qwen__Qwen2.5-14B-Instruct, 4. Qwen__Qwen3-8B__thinking, 5. allenai__OLMo-2-0325-32B-Instruct, 6. Qwen__Qwen2.5-7B-Instruct, 7. Qwen__Qwen3-14B, 8. Qwen__Qwen3-32B, 9. Qwen__Qwen3-8B, 10. allenai__Llama-3.1-Tulu-3-8B, 11. mistralai__Mistral-Small-24B-Instruct-2501, 12. microsoft__phi-4, 13. allenai__OLMo-2-1124-13B-Instruct, 14. allenai__OLMo-2-1124-7B-Instruct, 15. marin-community__marin-8b-instruct, 16. mistralai__Mistral-7B-Instruct-v0.3

## Strict instruction-level accuracy per configuration (mean over runs, %)

| configuration | grader | reference | replacement | replacement - grader |
|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 39.24 | 39.24 | 35.47 | -3.78 |
| Qwen__Qwen2.5-32B-Instruct | 38.95 | 38.37 | 37.79 | -1.16 |
| Qwen__Qwen2.5-7B-Instruct | 29.07 | 29.07 | 28.20 | -0.87 |
| Qwen__Qwen3-14B | 29.07 | 29.65 | 29.65 | +0.58 |
| Qwen__Qwen3-14B__thinking | 38.08 | 38.66 | 40.70 | +2.62 |
| Qwen__Qwen3-32B | 28.78 | 29.07 | 27.91 | -0.87 |
| Qwen__Qwen3-8B | 28.78 | 28.20 | 27.91 | -0.87 |
| Qwen__Qwen3-8B__thinking | 35.76 | 35.76 | 33.43 | -2.33 |
| allenai__Llama-3.1-Tulu-3-8B | 26.74 | 26.74 | 27.03 | +0.29 |
| allenai__OLMo-2-0325-32B-Instruct | 36.34 | 36.05 | 33.72 | -2.62 |
| allenai__OLMo-2-1124-13B-Instruct | 24.71 | 24.71 | 20.06 | -4.65 |
| allenai__OLMo-2-1124-7B-Instruct | 22.67 | 22.38 | 19.77 | -2.91 |
| marin-community__marin-8b-instruct | 20.35 | 20.06 | 18.90 | -1.45 |
| microsoft__phi-4 | 23.55 | 23.26 | 23.26 | -0.29 |
| mistralai__Mistral-7B-Instruct-v0.3 | 21.51 | 21.22 | 19.19 | -2.33 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 23.84 | 23.84 | 26.45 | +2.62 |

## Rerun and batch-invariance differences (prompt-level strict, grader)

| configuration | greedy | greedy_repeat | greedy_shuffled | bi_greedy | bi_greedy_shuffled | max-min |
|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | - | - | - | - | - | - |
| Qwen__Qwen2.5-32B-Instruct | - | - | - | - | - | - |
| Qwen__Qwen2.5-7B-Instruct | - | - | - | - | - | - |
| Qwen__Qwen3-14B | - | - | - | - | - | - |
| Qwen__Qwen3-14B__thinking | - | 35.00 | - | - | - | 0.00 |
| Qwen__Qwen3-32B | - | - | - | - | - | - |
| Qwen__Qwen3-8B | - | - | - | - | - | - |
| Qwen__Qwen3-8B__thinking | - | 32.33 | - | - | - | 0.00 |
| allenai__Llama-3.1-Tulu-3-8B | - | - | - | - | - | - |
| allenai__OLMo-2-0325-32B-Instruct | - | - | - | - | - | - |
| allenai__OLMo-2-1124-13B-Instruct | - | - | - | - | - | - |
| allenai__OLMo-2-1124-7B-Instruct | - | - | - | - | - | - |
| marin-community__marin-8b-instruct | - | - | - | - | - | - |
| microsoft__phi-4 | - | - | - | - | - | - |
| mistralai__Mistral-7B-Instruct-v0.3 | - | - | - | - | - | - |
| mistralai__Mistral-Small-24B-Instruct-2501 | - | - | - | - | - | - |

## Per-check pass rates (%) and disagreements (counts of verdicts)

| check | n | grader | reference | replacement | grader pass, contract fail | grader fail, contract pass | of which defect (vs replacement with grader's readings) | of which decision | grader != reference |
|---|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 112 | 71.4 | 71.4 | 40.2 | 35 | 0 | 17 | 18 | 0 |
| count:keywords_multiple | 80 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| count:numbers | 128 | 40.6 | 40.6 | 24.2 | 23 | 2 | 1 | 24 | 0 |
| count:person_names | 96 | 85.4 | 85.4 | 85.4 | 0 | 0 | 0 | 0 | 0 |
| count:pronouns | 128 | 85.2 | 85.2 | 77.3 | 10 | 0 | 10 | 0 | 0 |
| count:punctuation | 96 | 19.8 | 19.8 | 1.0 | 18 | 0 | 25 | 43 | 0 |
| count:unique_word_count | 144 | 82.6 | 82.6 | 79.2 | 5 | 0 | 6 | 3 | 0 |
| count:word_count_range | 176 | 25.0 | 25.0 | 26.1 | 3 | 5 | 1 | 7 | 0 |
| count:words_japanese | 80 | 12.5 | 12.5 | 10.0 | 2 | 0 | 1 | 3 | 0 |
| custom:character_reverse | 16 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| custom:csv_city | 16 | 56.2 | 56.2 | 93.8 | 0 | 6 | 0 | 6 | 0 |
| custom:csv_quotes | 16 | 12.5 | 12.5 | 31.2 | 0 | 3 | 0 | 3 | 0 |
| custom:csv_special_character | 16 | 12.5 | 12.5 | 25.0 | 0 | 2 | 0 | 2 | 0 |
| custom:date_format_list | 16 | 87.5 | 87.5 | 87.5 | 0 | 0 | 0 | 0 | 0 |
| custom:european_capitals_sort | 16 | 0.0 | 0.0 | 25.0 | 0 | 4 | 0 | 4 | 0 |
| custom:mcq_count_length | 16 | 12.5 | 12.5 | 31.2 | 0 | 3 | 3 | 0 | 0 |
| custom:multiples | 16 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| custom:reverse_newline | 16 | 6.2 | 6.2 | 6.2 | 0 | 0 | 0 | 0 | 0 |
| custom:sentence_alphabet | 16 | 18.8 | 25.0 | 25.0 | 0 | 1 | 1 | 0 | 1 |
| custom:word_reverse | 16 | 12.5 | 12.5 | 6.2 | 1 | 0 | 1 | 0 | 0 |
| format:emoji | 144 | 40.3 | 40.3 | 48.6 | 0 | 12 | 1 | 11 | 0 |
| format:line_indent | 144 | 11.8 | 11.8 | 8.3 | 5 | 0 | 0 | 5 | 0 |
| format:list | 144 | 67.4 | 67.4 | 64.6 | 5 | 1 | 6 | 0 | 0 |
| format:newline | 96 | 36.5 | 36.5 | 36.5 | 0 | 0 | 16 | 16 | 0 |
| format:no_bullets_bullets | 80 | 37.5 | 37.5 | 62.5 | 2 | 22 | 10 | 14 | 0 |
| format:no_whitespace | 64 | 57.8 | 57.8 | 57.8 | 0 | 0 | 0 | 0 | 0 |
| format:options | 96 | 61.5 | 61.5 | 74.0 | 0 | 12 | 0 | 12 | 0 |
| format:output_template | 64 | 98.4 | 98.4 | 92.2 | 4 | 0 | 2 | 2 | 0 |
| format:parentheses | 128 | 32.0 | 32.0 | 18.8 | 17 | 0 | 17 | 0 | 0 |
| format:quote_unquote | 80 | 91.2 | 91.2 | 87.5 | 4 | 1 | 5 | 0 | 0 |
| format:quotes | 128 | 22.7 | 22.7 | 21.9 | 12 | 11 | 23 | 0 | 0 |
| format:sub-bullets | 192 | 37.5 | 37.5 | 63.5 | 17 | 67 | 84 | 0 | 0 |
| format:thesis | 144 | 36.8 | 36.8 | 9.0 | 40 | 0 | 16 | 24 | 0 |
| format:title_case | 64 | 50.0 | 50.0 | 50.0 | 0 | 0 | 10 | 10 | 0 |
| ratio:overlap | 192 | 6.8 | 3.6 | 2.6 | 13 | 5 | 0 | 18 | 20 |
| ratio:sentence_balance | 112 | 1.8 | 1.8 | 4.5 | 0 | 3 | 1 | 2 | 0 |
| ratio:sentence_type | 96 | 7.3 | 7.3 | 10.4 | 0 | 3 | 3 | 0 | 0 |
| ratio:sentence_words | 112 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| ratio:stop_words | 192 | 50.0 | 50.0 | 49.0 | 2 | 0 | 2 | 0 | 0 |
| repeat:repeat_change | 48 | 14.6 | 14.6 | 14.6 | 0 | 0 | 0 | 0 | 0 |
| repeat:repeat_simple | 32 | 9.4 | 9.4 | 9.4 | 0 | 0 | 0 | 0 | 0 |
| repeat:repeat_span | 64 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 80 | 17.5 | 17.5 | 10.0 | 8 | 2 | 9 | 1 | 0 |
| sentence:increment | 128 | 3.9 | 3.9 | 0.0 | 5 | 0 | 6 | 1 | 0 |
| sentence:keyword | 240 | 27.1 | 27.1 | 27.9 | 1 | 3 | 2 | 6 | 0 |
| words:alphabet | 96 | 14.6 | 14.6 | 14.6 | 0 | 0 | 7 | 7 | 0 |
| words:consonants | 240 | 5.0 | 5.0 | 5.0 | 0 | 0 | 3 | 3 | 0 |
| words:keywords_specific_position | 64 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| words:last_first | 80 | 7.5 | 7.5 | 11.2 | 0 | 3 | 3 | 2 | 0 |
| words:no_consecutive | 128 | 7.8 | 7.8 | 7.8 | 0 | 0 | 1 | 1 | 0 |
| words:odd_even_syllables | 144 | 0.7 | 0.7 | 0.7 | 0 | 0 | 0 | 0 | 0 |
| words:palindrome | 112 | 35.7 | 35.7 | 16.1 | 22 | 0 | 3 | 19 | 0 |
| words:paragraph_last_first | 96 | 9.4 | 9.4 | 15.6 | 0 | 6 | 6 | 0 | 0 |
| words:prime_lengths | 80 | 5.0 | 5.0 | 6.2 | 0 | 1 | 0 | 1 | 0 |
| words:repeats | 80 | 13.8 | 13.8 | 13.8 | 0 | 0 | 1 | 1 | 0 |
| words:start_verb | 96 | 38.5 | 38.5 | 51.0 | 2 | 14 | 16 | 0 | 0 |
| words:vowel | 160 | 3.8 | 3.8 | 4.4 | 0 | 1 | 0 | 1 | 0 |
| words:words_position | 48 | 0.0 | 2.1 | 2.1 | 0 | 1 | 1 | 0 | 1 |
| **all** | 5504 | | | | 256 | 194 | 320 | 270 | 22 |

## Responses whose reasoning never closed (extraction failures under G1)

Verdict rows: 49; responses: 42
Grader strict passes on them: 15; reference strict passes: 15; grader loose passes: 15
Checks passed by the grader on unclosed reasoning: [["count:unique_word_count", 4], ["words:palindrome", 3], ["ratio:stop_words", 2], ["count:conjunctions", 2], ["count:pronouns", 2], ["format:list", 1], ["format:sub-bullets", 1]]
- Qwen__Qwen3-8B__thinking: grader strict 32.33% -> 29.33% when extraction failures fail every check
- Qwen__Qwen3-14B__thinking: grader strict 35.00% -> 34.33% when extraction failures fail every check

## Stored-record counts

Empty responses (verdict rows): 1; finish_reason=length rows: 314
Truncated (length) but reasoning closed or no reasoning: 265 rows; grader passes among them: 68

## Effect of each decision's alternative reading on the replacement

| alternative | verdicts changed | prompt-level accuracy change, mean over configurations (points) |
|---|---|---|
| D-trailing-ws=count | 0 | +0.000 |
| D-sentence-fragment=drop | 10 | +0.021 |
| D-word-split=split | 57 | -0.500 |
| D-list-label=word | 42 | +0.000 |
| D-vacuous=fail | 0 | +0.000 |
| D-count-exact=atleast | 26 | +0.542 |
| D-keyword-form=prefix | 0 | +0.000 |
| D-punct-set=six | 43 | +0.896 |
| D-punct-set=ascii | 1 | -0.021 |
| D-unique=hapax | 32 | -0.667 |
| D-between=exclusive | 7 | -0.104 |
| D-titlecase-minor=all | 0 | +0.000 |
| D-overlap-def=char_resp | 18 | -0.063 |
| D-overlap-def=word_ref | 17 | +0.062 |
| D-overlap-def=jaccard | 5 | +0.021 |
| D-balance=equal | 2 | -0.021 |
| D-different-words=across | 0 | +0.000 |
| D-repeat-count=n_plus_1 | 5 | +0.104 |
| D-palindrome-distinct=occurrences | 19 | +0.396 |
| D-vowel-scope=per_word_atmost3 | 35 | +0.604 |
| D-vowel-scope=response_exactly3 | 6 | -0.104 |
| D-vowel-paragraph=one_line | 1 | -0.021 |
| D-options-extra=contains | 19 | -0.125 |
| D-multiples-prose=prose_ok | 0 | +0.000 |
| D-custom-content=complete | 4 | -0.083 |
| D-nbb-after=forbidden | 14 | -0.292 |
| D-index-base=1 | 2 | +0.042 |
| D-change-case=change | 0 | +0.000 |
| D-csv-space=strict | 0 | +0.000 |
| D-conjunction-role=surface | 18 | +0.229 |
| D-section=whole | 24 | +0.396 |
| D-wrapper-csv=strict | 11 | -0.229 |
| D-wrapper-template=ok | 2 | +0.042 |
| D-wrapper-list=ok | 0 | +0.000 |
| D-indent-single=pass | 5 | +0.000 |
| D-options-label=strict | 12 | -0.250 |
| D-japanese-mixed=contains | 2 | +0.042 |

## Loose grading (grader)

Verdicts that loose turns into a pass: 257; of these the contract (replacement) fails 172
By check: [["format:sub-bullets", 53], ["format:line_indent", 16], ["ratio:stop_words", 11], ["custom:multiples", 9], ["count:numbers", 8], ["format:emoji", 7], ["ratio:sentence_type", 7], ["ratio:sentence_balance", 6], ["count:word_count_range", 6], ["sentence:alliteration_increment", 6], ["words:vowel", 5], ["format:newline", 5], ["words:start_verb", 4], ["sentence:increment", 4], ["ratio:overlap", 4], ["sentence:keyword", 4], ["words:paragraph_last_first", 3], ["words:no_consecutive", 2], ["words:repeats", 2], ["words:last_first", 2]]
