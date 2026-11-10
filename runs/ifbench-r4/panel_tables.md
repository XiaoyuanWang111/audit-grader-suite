## Per-configuration scores (mean over the configuration's runs; strict prompt-level accuracy, %)

| Configuration | Runs | G | R | X (as-is) | XP (proposed) | X-G mean [min, max over runs] | R-G mean | XP-G mean | G loose | greedy_repeat - greedy (G) | bi_greedy - greedy (G) | SD over sample runs (G) | Rank G -> X |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 17 | 34.08 | 34.14 | 33.39 | 30.71 | -0.69 [-1.67, +0.33] | +0.06 | -3.37 | 37.84 | -1.00 | -0.67 | 1.86 | 3 -> 4 |
| Qwen__Qwen2.5-32B-Instruct | 13 | 35.18 | 35.18 | 34.56 | 34.21 | -0.62 [-1.67, +1.67] | +0.00 | -0.97 | 38.28 | -1.33 | -1.00 | 2.03 | 1 -> 2 |
| Qwen__Qwen2.5-7B-Instruct | 17 | 27.41 | 27.51 | 26.27 | 26.76 | -1.14 [-2.67, +0.00] | +0.10 | -0.65 | 30.39 | -0.33 | -0.33 | 1.34 | 7 -> 8 |
| Qwen__Qwen3-14B | 17 | 27.75 | 27.84 | 29.57 | 29.14 | +1.82 [+1.00, +2.67] | +0.10 | +1.39 | 31.25 | -0.33 | -1.33 | 1.44 | 6 -> 6 |
| Qwen__Qwen3-14B__thinking | 3 | 34.33 | 34.67 | 39.33 | 38.33 | +5.00 [+5.00, +5.00] | +0.33 | +4.00 | 39.33 | +1.00 | n/a | n/a | 2 -> 1 |
| Qwen__Qwen3-32B | 13 | 25.10 | 25.21 | 27.90 | 27.46 | +2.79 [+1.33, +3.33] | +0.10 | +2.36 | 29.41 | -0.67 | +0.33 | 2.10 | 9 -> 7 |
| Qwen__Qwen3-8B | 17 | 25.18 | 25.08 | 25.94 | 24.88 | +0.76 [-0.33, +1.67] | -0.10 | -0.29 | 29.51 | +0.00 | -1.00 | 1.18 | 8 -> 9 |
| Qwen__Qwen3-8B__thinking | 3 | 32.44 | 32.44 | 31.67 | 30.89 | -0.78 [-1.33, -0.33] | +0.00 | -1.56 | 36.33 | +0.00 | n/a | n/a | 5 -> 5 |
| allenai__Llama-3.1-Tulu-3-8B | 17 | 22.67 | 22.75 | 24.35 | 24.88 | +1.69 [+0.67, +2.67] | +0.08 | +2.22 | 26.27 | +0.33 | +1.33 | 1.26 | 10 -> 11 |
| allenai__OLMo-2-0325-32B-Instruct | 13 | 33.28 | 33.31 | 34.46 | 31.33 | +1.18 [+0.33, +2.67] | +0.03 | -1.95 | 37.00 | +0.00 | -1.33 | 1.69 | 4 -> 3 |
| allenai__OLMo-2-1124-13B-Instruct | 17 | 22.65 | 22.75 | 23.08 | 21.67 | +0.43 [-0.33, +1.00] | +0.10 | -0.98 | 26.76 | +0.00 | +1.00 | 1.36 | 11 -> 12 |
| allenai__OLMo-2-1124-7B-Instruct | 17 | 20.37 | 20.37 | 21.14 | 20.14 | +0.76 [-0.67, +2.00] | +0.00 | -0.24 | 24.86 | +0.67 | +1.00 | 0.84 | 13 -> 14 |
| marin-community__marin-8b-instruct | 17 | 17.39 | 17.41 | 18.29 | 18.14 | +0.90 [-0.67, +3.00] | +0.02 | +0.75 | 21.55 | -1.00 | +0.33 | 1.12 | 16 -> 15 |
| microsoft__phi-4 | 17 | 19.06 | 19.27 | 21.78 | 22.27 | +2.73 [+1.00, +4.33] | +0.22 | +3.22 | 24.27 | +0.00 | +0.00 | 2.10 | 14 -> 13 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17 | 17.63 | 17.63 | 18.00 | 18.55 | +0.37 [-0.67, +1.33] | +0.00 | +0.92 | 20.80 | +0.33 | +0.33 | 1.08 | 15 -> 16 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 13 | 21.82 | 22.26 | 25.87 | 25.69 | +4.05 [+1.67, +5.00] | +0.44 | +3.87 | 27.92 | -0.33 | +1.33 | 1.27 | 12 -> 10 |

## Per-configuration instruction-level accuracy (%, mean over runs)

| Configuration | G | R | X | XP | G loose |
|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 36.58 | 36.58 | 36.44 | 33.98 | 41.23 |
| Qwen__Qwen2.5-32B-Instruct | 38.98 | 38.84 | 38.04 | 37.34 | 42.49 |
| Qwen__Qwen2.5-7B-Instruct | 29.55 | 29.53 | 28.01 | 28.11 | 33.02 |
| Qwen__Qwen3-14B | 30.98 | 30.97 | 32.28 | 31.91 | 35.28 |
| Qwen__Qwen3-14B__thinking | 37.31 | 37.89 | 41.67 | 40.79 | 41.67 |
| Qwen__Qwen3-32B | 28.47 | 28.38 | 30.90 | 30.46 | 33.18 |
| Qwen__Qwen3-8B | 28.27 | 27.96 | 29.09 | 28.16 | 33.09 |
| Qwen__Qwen3-8B__thinking | 35.95 | 35.76 | 34.30 | 33.33 | 40.31 |
| allenai__Llama-3.1-Tulu-3-8B | 25.55 | 25.43 | 26.90 | 27.34 | 29.58 |
| allenai__OLMo-2-0325-32B-Instruct | 36.69 | 36.47 | 37.37 | 34.10 | 40.27 |
| allenai__OLMo-2-1124-13B-Instruct | 24.30 | 24.18 | 24.33 | 23.08 | 29.55 |
| allenai__OLMo-2-1124-7B-Instruct | 23.14 | 22.98 | 23.50 | 22.14 | 28.13 |
| marin-community__marin-8b-instruct | 20.02 | 19.85 | 20.57 | 20.28 | 24.74 |
| microsoft__phi-4 | 21.24 | 21.36 | 23.68 | 24.13 | 27.43 |
| mistralai__Mistral-7B-Instruct-v0.3 | 20.18 | 19.97 | 20.52 | 21.00 | 24.78 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 24.64 | 24.71 | 28.24 | 28.04 | 31.31 |

## Per-check verdicts over all 78,432 instruction instances

| Check | n | G pass % | R pass % | X pass % | XP pass % | G!=R | G!=X | G pass, X fail | G fail, X pass | G loose rescues |
|---|---|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1596 | 64.3 | 64.3 | 52.1 | 52.1 | 0 | 195 | 195 | 0 | 0 |
| count:keywords_multiple | 1140 | 0.3 | 0.2 | 0.2 | 0.2 | 1 | 1 | 1 | 0 | 1 |
| count:numbers | 1824 | 38.0 | 38.0 | 37.9 | 37.9 | 0 | 3 | 3 | 0 | 138 |
| count:person_names | 1368 | 87.2 | 87.2 | 87.2 | 87.2 | 0 | 0 | 0 | 0 | 0 |
| count:pronouns | 1824 | 82.0 | 82.0 | 81.7 | 81.7 | 0 | 5 | 5 | 0 | 0 |
| count:punctuation | 1368 | 19.5 | 19.5 | 19.5 | 6.4 | 0 | 0 | 0 | 0 | 0 |
| count:unique_word_count | 2052 | 79.6 | 79.6 | 79.0 | 79.0 | 0 | 12 | 12 | 0 | 0 |
| count:word_count_range | 2508 | 21.7 | 21.7 | 22.5 | 22.5 | 0 | 135 | 57 | 78 | 156 |
| count:words_japanese | 1140 | 17.7 | 17.7 | 17.6 | 17.3 | 0 | 1 | 1 | 0 | 22 |
| custom:character_reverse | 228 | 2.2 | 2.2 | 0.0 | 0.0 | 0 | 5 | 5 | 0 | 0 |
| custom:csv_city | 228 | 50.4 | 50.4 | 50.4 | 90.4 | 0 | 0 | 0 | 0 | 0 |
| custom:csv_quotes | 228 | 6.6 | 6.6 | 6.6 | 25.4 | 0 | 0 | 0 | 0 | 0 |
| custom:csv_special_character | 228 | 7.5 | 7.5 | 7.5 | 48.7 | 0 | 0 | 0 | 0 | 13 |
| custom:date_format_list | 228 | 68.9 | 68.9 | 68.9 | 68.9 | 0 | 0 | 0 | 0 | 0 |
| custom:european_capitals_sort | 228 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| custom:mcq_count_length | 228 | 25.0 | 25.0 | 34.6 | 34.6 | 0 | 22 | 0 | 22 | 9 |
| custom:multiples | 228 | 0.4 | 0.4 | 0.4 | 0.4 | 0 | 0 | 0 | 0 | 122 |
| custom:reverse_newline | 228 | 3.9 | 3.9 | 1.3 | 1.3 | 0 | 6 | 6 | 0 | 0 |
| custom:sentence_alphabet | 228 | 21.1 | 31.1 | 31.1 | 31.6 | 23 | 23 | 0 | 23 | 22 |
| custom:word_reverse | 228 | 7.0 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 | 0 | 0 |
| format:emoji | 2052 | 34.4 | 34.4 | 35.6 | 35.5 | 0 | 28 | 1 | 27 | 104 |
| format:line_indent | 2052 | 12.1 | 12.1 | 12.2 | 12.2 | 0 | 2 | 0 | 2 | 233 |
| format:list | 2052 | 64.9 | 64.9 | 64.0 | 66.4 | 0 | 18 | 18 | 0 | 0 |
| format:newline | 1368 | 34.1 | 34.1 | 34.1 | 34.1 | 0 | 0 | 0 | 0 | 94 |
| format:no_bullets_bullets | 1140 | 27.9 | 27.9 | 36.5 | 53.2 | 0 | 172 | 37 | 135 | 59 |
| format:no_whitespace | 912 | 51.9 | 51.9 | 51.9 | 53.5 | 0 | 0 | 0 | 0 | 0 |
| format:options | 1368 | 60.0 | 60.0 | 60.0 | 83.5 | 0 | 0 | 0 | 0 | 43 |
| format:output_template | 912 | 97.6 | 97.6 | 97.6 | 92.9 | 0 | 0 | 0 | 0 | 0 |
| format:parentheses | 1824 | 29.7 | 29.7 | 29.6 | 29.6 | 0 | 1 | 1 | 0 | 0 |
| format:quote_unquote | 1140 | 90.4 | 90.4 | 90.3 | 58.8 | 0 | 1 | 1 | 0 | 25 |
| format:quotes | 1824 | 23.8 | 23.8 | 25.3 | 25.3 | 0 | 30 | 1 | 29 | 10 |
| format:sub-bullets | 2736 | 36.5 | 36.5 | 61.9 | 61.9 | 0 | 1113 | 209 | 904 | 1737 |
| format:thesis | 2052 | 33.1 | 33.1 | 21.2 | 6.7 | 0 | 246 | 245 | 1 | 0 |
| format:title_case | 912 | 50.7 | 50.7 | 52.6 | 52.6 | 0 | 18 | 0 | 18 | 6 |
| ratio:overlap | 2736 | 5.9 | 2.4 | 1.5 | 1.5 | 227 | 202 | 162 | 40 | 38 |
| ratio:sentence_balance | 1596 | 3.5 | 3.5 | 3.0 | 3.4 | 0 | 8 | 8 | 0 | 78 |
| ratio:sentence_type | 1368 | 4.4 | 4.4 | 4.4 | 4.7 | 0 | 0 | 0 | 0 | 69 |
| ratio:sentence_words | 1596 | 0.1 | 0.1 | 0.1 | 0.1 | 1 | 1 | 1 | 0 | 0 |
| ratio:stop_words | 2736 | 47.8 | 47.8 | 47.6 | 47.6 | 0 | 6 | 6 | 0 | 164 |
| repeat:repeat_change | 684 | 6.1 | 6.1 | 6.1 | 6.1 | 0 | 0 | 0 | 0 | 10 |
| repeat:repeat_simple | 456 | 7.0 | 7.0 | 7.0 | 0.2 | 0 | 0 | 0 | 0 | 0 |
| repeat:repeat_span | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1140 | 19.0 | 19.0 | 9.6 | 8.9 | 0 | 121 | 114 | 7 | 106 |
| sentence:increment | 1824 | 3.1 | 3.1 | 3.1 | 1.2 | 0 | 0 | 0 | 0 | 74 |
| sentence:keyword | 3420 | 25.6 | 25.6 | 25.6 | 23.9 | 0 | 0 | 0 | 0 | 84 |
| words:alphabet | 1368 | 10.4 | 10.4 | 10.4 | 10.4 | 0 | 0 | 0 | 0 | 17 |
| words:consonants | 3420 | 6.0 | 6.0 | 6.0 | 6.0 | 0 | 0 | 0 | 0 | 4 |
| words:keywords_specific_position | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 |
| words:last_first | 1140 | 7.0 | 7.0 | 10.1 | 10.1 | 0 | 35 | 0 | 35 | 12 |
| words:no_consecutive | 1824 | 4.2 | 4.2 | 4.2 | 3.9 | 0 | 0 | 0 | 0 | 40 |
| words:odd_even_syllables | 2052 | 0.8 | 0.8 | 0.8 | 0.8 | 0 | 0 | 0 | 0 | 3 |
| words:palindrome | 1596 | 30.3 | 30.3 | 29.8 | 9.9 | 0 | 9 | 9 | 0 | 0 |
| words:paragraph_last_first | 1368 | 7.8 | 7.8 | 9.9 | 9.9 | 0 | 29 | 0 | 29 | 50 |
| words:prime_lengths | 1140 | 4.6 | 4.6 | 4.6 | 4.6 | 0 | 0 | 0 | 0 | 0 |
| words:repeats | 1140 | 17.5 | 17.5 | 17.5 | 17.5 | 0 | 0 | 0 | 0 | 16 |
| words:start_verb | 1368 | 39.5 | 39.5 | 65.3 | 64.6 | 0 | 352 | 0 | 352 | 79 |
| words:vowel | 2280 | 4.1 | 4.1 | 4.1 | 4.3 | 0 | 0 | 0 | 0 | 27 |
| words:words_position | 684 | 0.3 | 1.0 | 1.0 | 1.0 | 5 | 5 | 0 | 5 | 1 |

## Decision switches (X with one decision at its proposed reading, against X as-is, all 68,400 responses)

| Decision | Instances touched | Verdicts changed | Prompt-level change (points) | Instruction-level change (points) |
|---|---|---|---|---|
| D-csv-wrapper | 684 | 228 | +0.333 | +0.291 |
| D-explanation | 1140 | 359 | -0.525 | -0.458 |
| D-japanese-digits | 1140 | 4 | -0.006 | -0.005 |
| D-list-sep | 2052 | 67 | +0.064 | +0.062 |
| D-nbb-order | 1140 | 190 | +0.278 | +0.242 |
| D-options-exact | 1368 | 321 | +0.469 | +0.409 |
| D-palindrome-distinct | 1596 | 317 | -0.463 | -0.404 |
| D-punct-set | 1368 | 180 | -0.263 | -0.229 |
| D-section | 2052 | 297 | -0.310 | -0.379 |
| D-sentence | 16644 | 202 | -0.096 | -0.117 |
| D-template-repeat | 912 | 43 | -0.063 | -0.055 |
| D-this-sentence | 456 | 33 | -0.045 | -0.040 |
| D-trim | 2280 | 15 | +0.022 | +0.019 |
| D-verb | 1368 | 9 | -0.013 | -0.011 |
| D-vowel-paragraph | 2280 | 6 | +0.009 | +0.008 |
| D-word | 8892 | 5 | -0.003 | -0.006 |
