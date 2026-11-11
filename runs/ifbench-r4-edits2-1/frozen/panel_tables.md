# Panel tables (all 228 files)

Verdict rows (response x instruction): 78432

## Scored coverage and grading failures

| column | verdicts | pass | fail | exception | coverage |
|---|---|---|---|---|---|
| g_strict | 78432 | 21708 | 56724 | 0  | 100.000% |
| g_loose | 78432 | 25374 | 53058 | 0  | 100.000% |
| r_strict | 78432 | 21637 | 56795 | 0  | 100.000% |
| r_loose | 78432 | 25273 | 53159 | 0  | 100.000% |
| rep | 78432 | 20497 | 57935 | 0  | 100.000% |
| rep_gr | 78432 | 21496 | 56936 | 0  | 100.000% |

## Strict prompt-level accuracy per configuration (mean over runs, %)

| configuration | runs | grader | reference | replacement | replacement, grader's readings | replacement - grader | of which decisions | of which defects | grader loose | rerun diff (grader, greedy vs greedy_repeat) | rerun diff (replacement) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 17 | 34.08 | 34.14 | 30.67 | 31.43 | -3.41 | -0.76 | -2.65 | 37.84 | 1.00 | 0.33 |
| Qwen__Qwen2.5-32B-Instruct | 13 | 35.18 | 35.18 | 33.62 | 32.72 | -1.56 | +0.90 | -2.46 | 38.28 | 1.33 | 1.00 |
| Qwen__Qwen2.5-7B-Instruct | 17 | 27.41 | 27.51 | 25.67 | 25.86 | -1.75 | -0.20 | -1.55 | 30.39 | 0.33 | 0.67 |
| Qwen__Qwen3-14B | 17 | 27.75 | 27.84 | 27.24 | 28.57 | -0.51 | -1.33 | +0.82 | 31.25 | 0.33 | 0.33 |
| Qwen__Qwen3-14B__thinking | 3 | 34.33 | 34.67 | 37.33 | 38.89 | +3.00 | -1.56 | +4.56 | 39.33 | 1.00 | 0.67 |
| Qwen__Qwen3-32B | 13 | 25.10 | 25.21 | 25.21 | 26.03 | +0.10 | -0.82 | +0.92 | 29.41 | 0.67 | 0.33 |
| Qwen__Qwen3-8B | 17 | 25.18 | 25.08 | 24.92 | 25.71 | -0.25 | -0.78 | +0.53 | 29.51 | 0.00 | 0.00 |
| Qwen__Qwen3-8B__thinking | 3 | 32.44 | 32.44 | 30.78 | 31.44 | -1.67 | -0.67 | -1.00 | 36.33 | 0.00 | 0.67 |
| allenai__Llama-3.1-Tulu-3-8B | 17 | 22.67 | 22.75 | 23.71 | 23.86 | +1.04 | -0.16 | +1.20 | 26.27 | 0.33 | 0.67 |
| allenai__OLMo-2-0325-32B-Instruct | 13 | 33.28 | 33.31 | 30.69 | 34.00 | -2.59 | -3.31 | +0.72 | 37.00 | 0.00 | 0.67 |
| allenai__OLMo-2-1124-13B-Instruct | 17 | 22.65 | 22.75 | 18.88 | 21.53 | -3.76 | -2.65 | -1.12 | 26.76 | 0.00 | 0.33 |
| allenai__OLMo-2-1124-7B-Instruct | 17 | 20.37 | 20.37 | 18.80 | 19.86 | -1.57 | -1.06 | -0.51 | 24.86 | 0.67 | 0.33 |
| marin-community__marin-8b-instruct | 17 | 17.39 | 17.41 | 16.86 | 17.22 | -0.53 | -0.35 | -0.18 | 21.55 | 1.00 | 1.00 |
| microsoft__phi-4 | 17 | 19.06 | 19.27 | 19.47 | 20.55 | +0.41 | -1.08 | +1.49 | 24.27 | 0.00 | 0.00 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17 | 17.63 | 17.63 | 16.80 | 17.61 | -0.82 | -0.80 | -0.02 | 20.80 | 0.33 | 0.33 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 13 | 21.82 | 22.26 | 23.03 | 23.15 | +1.21 | -0.13 | +1.33 | 27.92 | 0.33 | 0.33 |

Ranking by grader strict: 1. Qwen__Qwen2.5-32B-Instruct, 2. Qwen__Qwen3-14B__thinking, 3. Qwen__Qwen2.5-14B-Instruct, 4. allenai__OLMo-2-0325-32B-Instruct, 5. Qwen__Qwen3-8B__thinking, 6. Qwen__Qwen3-14B, 7. Qwen__Qwen2.5-7B-Instruct, 8. Qwen__Qwen3-8B, 9. Qwen__Qwen3-32B, 10. allenai__Llama-3.1-Tulu-3-8B, 11. allenai__OLMo-2-1124-13B-Instruct, 12. mistralai__Mistral-Small-24B-Instruct-2501, 13. allenai__OLMo-2-1124-7B-Instruct, 14. microsoft__phi-4, 15. mistralai__Mistral-7B-Instruct-v0.3, 16. marin-community__marin-8b-instruct

Ranking by replacement: 1. Qwen__Qwen3-14B__thinking, 2. Qwen__Qwen2.5-32B-Instruct, 3. Qwen__Qwen3-8B__thinking, 4. allenai__OLMo-2-0325-32B-Instruct, 5. Qwen__Qwen2.5-14B-Instruct, 6. Qwen__Qwen3-14B, 7. Qwen__Qwen2.5-7B-Instruct, 8. Qwen__Qwen3-32B, 9. Qwen__Qwen3-8B, 10. allenai__Llama-3.1-Tulu-3-8B, 11. mistralai__Mistral-Small-24B-Instruct-2501, 12. microsoft__phi-4, 13. allenai__OLMo-2-1124-13B-Instruct, 14. allenai__OLMo-2-1124-7B-Instruct, 15. marin-community__marin-8b-instruct, 16. mistralai__Mistral-7B-Instruct-v0.3

## Strict instruction-level accuracy per configuration (mean over runs, %)

| configuration | grader | reference | replacement | replacement - grader |
|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 36.58 | 36.58 | 33.76 | -2.82 |
| Qwen__Qwen2.5-32B-Instruct | 38.98 | 38.84 | 36.63 | -2.35 |
| Qwen__Qwen2.5-7B-Instruct | 29.55 | 29.53 | 26.56 | -2.99 |
| Qwen__Qwen3-14B | 30.98 | 30.97 | 30.04 | -0.94 |
| Qwen__Qwen3-14B__thinking | 37.31 | 37.89 | 39.63 | +2.33 |
| Qwen__Qwen3-32B | 28.47 | 28.38 | 28.24 | -0.22 |
| Qwen__Qwen3-8B | 28.27 | 27.96 | 28.06 | -0.21 |
| Qwen__Qwen3-8B__thinking | 35.95 | 35.76 | 33.53 | -2.42 |
| allenai__Llama-3.1-Tulu-3-8B | 25.55 | 25.43 | 25.62 | +0.07 |
| allenai__OLMo-2-0325-32B-Instruct | 36.69 | 36.47 | 33.50 | -3.20 |
| allenai__OLMo-2-1124-13B-Instruct | 24.30 | 24.18 | 20.16 | -4.14 |
| allenai__OLMo-2-1124-7B-Instruct | 23.14 | 22.98 | 20.31 | -2.82 |
| marin-community__marin-8b-instruct | 20.02 | 19.85 | 18.69 | -1.33 |
| microsoft__phi-4 | 21.24 | 21.36 | 21.36 | +0.12 |
| mistralai__Mistral-7B-Instruct-v0.3 | 20.18 | 19.97 | 18.78 | -1.40 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 24.64 | 24.71 | 24.89 | +0.25 |

## Rerun and batch-invariance differences (prompt-level strict, grader)

| configuration | greedy | greedy_repeat | greedy_shuffled | bi_greedy | bi_greedy_shuffled | max-min |
|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 35.00 | 34.00 | 34.67 | 34.33 | 34.33 | 1.00 |
| Qwen__Qwen2.5-32B-Instruct | 37.33 | 36.00 | 37.00 | 36.33 | 36.33 | 1.33 |
| Qwen__Qwen2.5-7B-Instruct | 29.00 | 28.67 | 29.33 | 28.67 | 28.67 | 0.67 |
| Qwen__Qwen3-14B | 28.33 | 28.00 | 28.67 | 27.00 | 27.00 | 1.67 |
| Qwen__Qwen3-14B__thinking | 34.00 | 35.00 | 34.00 | - | - | 1.00 |
| Qwen__Qwen3-32B | 24.67 | 24.00 | 23.00 | 25.00 | 25.00 | 2.00 |
| Qwen__Qwen3-8B | 24.67 | 24.67 | 25.00 | 23.67 | 23.67 | 1.33 |
| Qwen__Qwen3-8B__thinking | 32.33 | 32.33 | 32.67 | - | - | 0.33 |
| allenai__Llama-3.1-Tulu-3-8B | 21.67 | 22.00 | 22.67 | 23.00 | 23.00 | 1.33 |
| allenai__OLMo-2-0325-32B-Instruct | 35.00 | 35.00 | 34.00 | 33.67 | 33.67 | 1.33 |
| allenai__OLMo-2-1124-13B-Instruct | 23.00 | 23.00 | 23.00 | 24.00 | 24.00 | 1.00 |
| allenai__OLMo-2-1124-7B-Instruct | 19.67 | 20.33 | 20.33 | 20.67 | 20.67 | 1.00 |
| marin-community__marin-8b-instruct | 16.33 | 15.33 | 16.00 | 16.67 | 16.67 | 1.33 |
| microsoft__phi-4 | 20.00 | 20.00 | 20.00 | 20.00 | 20.00 | 0.00 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17.33 | 17.67 | 18.67 | 17.67 | 17.67 | 1.33 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 22.67 | 22.33 | 22.67 | 24.00 | 24.00 | 1.67 |

## Per-check pass rates (%) and disagreements (counts of verdicts)

| check | n | grader | reference | replacement | grader pass, contract fail | grader fail, contract pass | of which defect (vs replacement with grader's readings) | of which decision | grader != reference |
|---|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1596 | 64.3 | 64.3 | 34.8 | 471 | 0 | 197 | 274 | 0 |
| count:keywords_multiple | 1140 | 0.3 | 0.2 | 0.2 | 1 | 0 | 1 | 0 | 1 |
| count:numbers | 1824 | 38.0 | 38.0 | 23.5 | 322 | 56 | 5 | 373 | 0 |
| count:person_names | 1368 | 87.2 | 87.2 | 87.2 | 0 | 0 | 0 | 0 | 0 |
| count:pronouns | 1824 | 82.0 | 82.0 | 73.1 | 163 | 0 | 163 | 0 | 0 |
| count:punctuation | 1368 | 19.5 | 19.5 | 0.3 | 264 | 1 | 315 | 578 | 0 |
| count:unique_word_count | 2052 | 79.6 | 79.6 | 78.4 | 25 | 0 | 47 | 42 | 0 |
| count:word_count_range | 2508 | 21.7 | 21.7 | 22.6 | 61 | 83 | 2 | 142 | 0 |
| count:words_japanese | 1140 | 17.7 | 17.7 | 14.9 | 33 | 1 | 31 | 41 | 0 |
| custom:character_reverse | 228 | 2.2 | 2.2 | 0.0 | 5 | 0 | 5 | 0 | 0 |
| custom:csv_city | 228 | 50.4 | 50.4 | 91.2 | 0 | 93 | 2 | 91 | 0 |
| custom:csv_quotes | 228 | 6.6 | 6.6 | 25.4 | 0 | 43 | 0 | 43 | 0 |
| custom:csv_special_character | 228 | 7.5 | 7.5 | 19.7 | 1 | 29 | 1 | 29 | 0 |
| custom:date_format_list | 228 | 68.9 | 68.9 | 69.3 | 0 | 1 | 1 | 0 | 0 |
| custom:european_capitals_sort | 228 | 0.0 | 0.0 | 10.1 | 0 | 23 | 0 | 23 | 0 |
| custom:mcq_count_length | 228 | 25.0 | 25.0 | 40.8 | 0 | 36 | 36 | 0 | 0 |
| custom:multiples | 228 | 0.4 | 0.4 | 0.4 | 0 | 0 | 0 | 0 | 0 |
| custom:reverse_newline | 228 | 3.9 | 3.9 | 1.3 | 6 | 0 | 6 | 0 | 0 |
| custom:sentence_alphabet | 228 | 21.1 | 31.1 | 32.0 | 0 | 25 | 24 | 1 | 23 |
| custom:word_reverse | 228 | 7.0 | 7.0 | 7.5 | 4 | 5 | 9 | 0 | 0 |
| format:emoji | 2052 | 34.4 | 34.4 | 42.1 | 3 | 161 | 31 | 133 | 0 |
| format:line_indent | 2052 | 12.1 | 12.1 | 6.1 | 126 | 2 | 2 | 126 | 0 |
| format:list | 2052 | 64.9 | 64.9 | 61.2 | 96 | 20 | 116 | 0 | 0 |
| format:newline | 1368 | 34.1 | 34.1 | 34.9 | 0 | 11 | 178 | 187 | 0 |
| format:no_bullets_bullets | 1140 | 27.9 | 27.9 | 52.8 | 37 | 321 | 172 | 188 | 0 |
| format:no_whitespace | 912 | 51.9 | 51.9 | 53.5 | 0 | 15 | 15 | 0 | 0 |
| format:options | 1368 | 60.0 | 60.0 | 72.1 | 0 | 166 | 0 | 166 | 0 |
| format:output_template | 912 | 97.6 | 97.6 | 88.9 | 79 | 0 | 43 | 36 | 0 |
| format:parentheses | 1824 | 29.7 | 29.7 | 18.6 | 202 | 0 | 202 | 0 | 0 |
| format:quote_unquote | 1140 | 90.4 | 90.4 | 82.8 | 90 | 4 | 94 | 0 | 0 |
| format:quotes | 1824 | 23.8 | 23.8 | 16.8 | 218 | 90 | 308 | 0 | 0 |
| format:sub-bullets | 2736 | 36.5 | 36.5 | 61.9 | 208 | 903 | 1111 | 0 | 0 |
| format:thesis | 2052 | 33.1 | 33.1 | 7.4 | 528 | 0 | 206 | 324 | 0 |
| format:title_case | 912 | 50.7 | 50.7 | 52.6 | 0 | 18 | 103 | 115 | 0 |
| ratio:overlap | 2736 | 5.9 | 2.4 | 1.5 | 162 | 42 | 0 | 204 | 227 |
| ratio:sentence_balance | 1596 | 3.5 | 3.5 | 5.8 | 8 | 45 | 15 | 38 | 0 |
| ratio:sentence_type | 1368 | 4.4 | 4.4 | 3.9 | 17 | 11 | 27 | 1 | 0 |
| ratio:sentence_words | 1596 | 0.1 | 0.1 | 0.1 | 1 | 0 | 1 | 0 | 1 |
| ratio:stop_words | 2736 | 47.8 | 47.8 | 47.0 | 29 | 7 | 6 | 30 | 0 |
| repeat:repeat_change | 684 | 6.1 | 6.1 | 6.1 | 0 | 0 | 0 | 0 | 0 |
| repeat:repeat_simple | 456 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 | 0 | 0 |
| repeat:repeat_span | 912 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1140 | 19.0 | 19.0 | 9.3 | 117 | 6 | 131 | 22 | 0 |
| sentence:increment | 1824 | 3.1 | 3.1 | 1.0 | 40 | 1 | 45 | 4 | 0 |
| sentence:keyword | 3420 | 25.6 | 25.6 | 25.4 | 61 | 55 | 71 | 57 | 0 |
| words:alphabet | 1368 | 10.4 | 10.4 | 10.4 | 0 | 0 | 79 | 79 | 0 |
| words:consonants | 3420 | 6.0 | 6.0 | 6.2 | 0 | 7 | 25 | 32 | 0 |
| words:keywords_specific_position | 912 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| words:last_first | 1140 | 7.0 | 7.0 | 10.3 | 0 | 37 | 54 | 25 | 0 |
| words:no_consecutive | 1824 | 4.2 | 4.2 | 4.0 | 3 | 0 | 14 | 17 | 0 |
| words:odd_even_syllables | 2052 | 0.8 | 0.8 | 0.8 | 0 | 0 | 2 | 2 | 0 |
| words:palindrome | 1596 | 30.3 | 30.3 | 9.9 | 326 | 0 | 16 | 324 | 0 |
| words:paragraph_last_first | 1368 | 7.8 | 7.8 | 9.9 | 0 | 29 | 29 | 0 | 0 |
| words:prime_lengths | 1140 | 4.6 | 4.6 | 4.6 | 0 | 1 | 1 | 2 | 0 |
| words:repeats | 1140 | 17.5 | 17.5 | 17.5 | 0 | 0 | 9 | 9 | 0 |
| words:start_verb | 1368 | 39.5 | 39.5 | 49.6 | 9 | 147 | 156 | 0 | 0 |
| words:vowel | 2280 | 4.1 | 4.1 | 4.3 | 0 | 6 | 0 | 6 | 0 |
| words:words_position | 684 | 0.3 | 1.0 | 0.9 | 0 | 4 | 5 | 1 | 5 |
| **all** | 78432 | | | | 3716 | 2505 | 4112 | 3765 | 257 |

## Responses whose reasoning never closed (extraction failures under G1)

Verdict rows: 157; responses: 136
Grader strict passes on them: 45; reference strict passes: 45; grader loose passes: 45
Checks passed by the grader on unclosed reasoning: [["count:unique_word_count", 12], ["words:palindrome", 9], ["count:conjunctions", 7], ["ratio:stop_words", 6], ["count:pronouns", 5], ["format:sub-bullets", 3], ["format:quotes", 1], ["format:list", 1], ["format:parentheses", 1]]
- Qwen__Qwen3-8B__thinking: grader strict 32.44% -> 29.22% when extraction failures fail every check
- Qwen__Qwen3-14B__thinking: grader strict 34.33% -> 33.67% when extraction failures fail every check

## Stored-record counts

Empty responses (verdict rows): 37; finish_reason=length rows: 4588
Truncated (length) but reasoning closed or no reasoning: 4431 rows; grader passes among them: 968

## Effect of each decision's alternative reading on the replacement

| alternative | verdicts changed | prompt-level accuracy change, mean over configurations (points) |
|---|---|---|
| D-trailing-ws=count | 0 | +0.000 |
| D-sentence-fragment=drop | 161 | +0.019 |
| D-word-split=split | 786 | -0.442 |
| D-list-label=word | 569 | +0.089 |
| D-vacuous=fail | 0 | +0.000 |
| D-count-exact=atleast | 285 | +0.495 |
| D-keyword-form=prefix | 1 | +0.001 |
| D-punct-set=six | 578 | +0.941 |
| D-punct-set=ascii | 4 | -0.022 |
| D-unique=hapax | 473 | -0.688 |
| D-between=exclusive | 90 | -0.107 |
| D-titlecase-minor=all | 6 | -0.009 |
| D-overlap-def=char_resp | 204 | -0.016 |
| D-overlap-def=word_ref | 152 | +0.036 |
| D-overlap-def=jaccard | 70 | +0.016 |
| D-balance=equal | 38 | -0.035 |
| D-different-words=across | 0 | +0.000 |
| D-repeat-count=n_plus_1 | 74 | +0.102 |
| D-palindrome-distinct=occurrences | 318 | +0.423 |
| D-vowel-scope=per_word_atmost3 | 403 | +0.605 |
| D-vowel-scope=response_exactly3 | 66 | -0.070 |
| D-vowel-paragraph=one_line | 6 | -0.007 |
| D-options-extra=contains | 301 | -0.080 |
| D-multiples-prose=prose_ok | 0 | +0.000 |
| D-custom-content=complete | 23 | -0.057 |
| D-nbb-after=forbidden | 187 | -0.239 |
| D-index-base=1 | 5 | +0.035 |
| D-change-case=change | 0 | +0.000 |
| D-csv-space=strict | 0 | +0.000 |
| D-conjunction-role=surface | 274 | +0.265 |
| D-section=whole | 324 | +0.352 |
| D-wrapper-csv=strict | 163 | -0.225 |
| D-wrapper-template=ok | 36 | +0.049 |
| D-wrapper-list=ok | 0 | +0.000 |
| D-indent-single=pass | 126 | +0.006 |
| D-options-label=strict | 166 | -0.231 |
| D-japanese-mixed=contains | 31 | +0.038 |

## Loose grading (grader)

Verdicts that loose turns into a pass: 3666; of these the contract (replacement) fails 2588
By check: [["format:sub-bullets", 834], ["format:line_indent", 232], ["ratio:stop_words", 161], ["count:word_count_range", 149], ["count:numbers", 126], ["custom:multiples", 122], ["sentence:alliteration_increment", 104], ["format:newline", 94], ["format:emoji", 94], ["sentence:keyword", 83], ["sentence:increment", 73], ["ratio:sentence_balance", 70], ["ratio:sentence_type", 69], ["words:start_verb", 56], ["format:options", 43], ["words:paragraph_last_first", 43], ["words:no_consecutive", 40], ["ratio:overlap", 36], ["format:quote_unquote", 22], ["words:vowel", 21]]
