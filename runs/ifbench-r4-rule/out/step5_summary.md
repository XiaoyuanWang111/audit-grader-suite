# Step 5 panel summary

228 run files, 78432 (row, check) items, 16 configurations. Accuracies are means over a configuration's runs, in percent.

## Prompt-level accuracy (strict unless marked loose)

| configuration | runs | G (as loaded) | Gi (int kwargs) | R (reference) | G-R | Gi-R | XG (replacement, grader readings) | X (replacement, proposed readings) | XG-Gi (defects) | X-XG (decisions, G1) | X-G (total) | GL loose | RL loose | R, extraction failures failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 17 | 34.08 | 34.08 | 34.14 | -0.06 | -0.06 | 31.92 | 30.57 | -2.16 | -1.35 | -3.51 | 37.84 | 37.94 | 34.14 |
| Qwen__Qwen2.5-32B-Instruct | 13 | 35.18 | 35.18 | 35.18 | +0.00 | +0.00 | 33.05 | 32.59 | -2.13 | -0.46 | -2.59 | 38.28 | 38.28 | 35.18 |
| Qwen__Qwen2.5-7B-Instruct | 17 | 27.41 | 27.41 | 27.51 | -0.10 | -0.10 | 25.55 | 24.73 | -1.86 | -0.82 | -2.69 | 30.39 | 30.49 | 27.51 |
| Qwen__Qwen3-14B | 17 | 27.75 | 27.75 | 27.84 | -0.10 | -0.10 | 27.96 | 26.59 | +0.22 | -1.37 | -1.16 | 31.25 | 31.35 | 27.84 |
| Qwen__Qwen3-14B__thinking | 3 | 34.33 | 34.33 | 34.67 | -0.33 | -0.33 | 37.56 | 36.22 | +3.22 | -1.33 | +1.89 | 39.33 | 39.67 | 34.00 |
| Qwen__Qwen3-32B | 13 | 25.10 | 25.10 | 25.21 | -0.10 | -0.10 | 25.31 | 24.56 | +0.21 | -0.74 | -0.54 | 29.41 | 29.49 | 25.21 |
| Qwen__Qwen3-8B | 17 | 25.18 | 25.18 | 25.08 | +0.10 | +0.10 | 24.63 | 23.47 | -0.55 | -1.16 | -1.71 | 29.51 | 29.39 | 25.08 |
| Qwen__Qwen3-8B__thinking | 3 | 32.44 | 32.44 | 32.44 | +0.00 | +0.00 | 32.44 | 29.11 | +0.00 | -3.33 | -3.33 | 36.33 | 36.56 | 29.22 |
| allenai__Llama-3.1-Tulu-3-8B | 17 | 22.67 | 22.67 | 22.75 | -0.08 | -0.08 | 22.35 | 22.14 | -0.31 | -0.22 | -0.53 | 26.27 | 26.39 | 22.75 |
| allenai__OLMo-2-0325-32B-Instruct | 13 | 33.28 | 33.28 | 33.31 | -0.03 | -0.03 | 32.23 | 30.59 | -1.05 | -1.64 | -2.69 | 37.00 | 37.00 | 33.31 |
| allenai__OLMo-2-1124-13B-Instruct | 17 | 22.65 | 22.65 | 22.75 | -0.10 | -0.10 | 21.02 | 19.02 | -1.63 | -2.00 | -3.63 | 26.76 | 26.90 | 22.75 |
| allenai__OLMo-2-1124-7B-Instruct | 17 | 20.37 | 20.37 | 20.37 | +0.00 | +0.00 | 19.47 | 18.71 | -0.90 | -0.76 | -1.67 | 24.86 | 24.86 | 20.37 |
| marin-community__marin-8b-instruct | 17 | 17.39 | 17.39 | 17.41 | -0.02 | -0.02 | 16.92 | 16.45 | -0.47 | -0.47 | -0.94 | 21.55 | 21.55 | 17.41 |
| microsoft__phi-4 | 17 | 19.06 | 19.06 | 19.27 | -0.22 | -0.22 | 18.96 | 19.49 | -0.10 | +0.53 | +0.43 | 24.27 | 24.41 | 19.27 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17 | 17.63 | 17.63 | 17.63 | +0.00 | +0.00 | 17.08 | 16.45 | -0.55 | -0.63 | -1.18 | 20.80 | 20.78 | 17.63 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 13 | 21.82 | 21.82 | 22.26 | -0.44 | -0.44 | 22.85 | 22.15 | +1.03 | -0.69 | +0.33 | 27.92 | 28.18 | 22.26 |

## Instruction-level accuracy (strict)

| configuration | G | Gi | R | G-R | Gi-R | X | X-Gi |
|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 36.58 | 36.58 | 36.58 | +0.00 | +0.00 | 33.57 | -3.01 |
| Qwen__Qwen2.5-32B-Instruct | 38.98 | 38.98 | 38.84 | +0.13 | +0.13 | 36.05 | -2.93 |
| Qwen__Qwen2.5-7B-Instruct | 29.55 | 29.55 | 29.53 | +0.02 | +0.02 | 26.01 | -3.54 |
| Qwen__Qwen3-14B | 30.98 | 30.98 | 30.97 | +0.02 | +0.02 | 29.14 | -1.85 |
| Qwen__Qwen3-14B__thinking | 37.31 | 37.31 | 37.89 | -0.58 | -0.58 | 38.37 | +1.07 |
| Qwen__Qwen3-32B | 28.47 | 28.47 | 28.38 | +0.09 | +0.09 | 27.71 | -0.76 |
| Qwen__Qwen3-8B | 28.27 | 28.27 | 27.96 | +0.31 | +0.31 | 26.76 | -1.50 |
| Qwen__Qwen3-8B__thinking | 35.95 | 35.95 | 35.76 | +0.19 | +0.19 | 31.88 | -4.07 |
| allenai__Llama-3.1-Tulu-3-8B | 25.55 | 25.55 | 25.43 | +0.12 | +0.12 | 24.71 | -0.84 |
| allenai__OLMo-2-0325-32B-Instruct | 36.69 | 36.69 | 36.47 | +0.22 | +0.22 | 33.81 | -2.88 |
| allenai__OLMo-2-1124-13B-Instruct | 24.30 | 24.30 | 24.18 | +0.12 | +0.12 | 20.25 | -4.05 |
| allenai__OLMo-2-1124-7B-Instruct | 23.14 | 23.14 | 22.98 | +0.15 | +0.15 | 20.81 | -2.33 |
| marin-community__marin-8b-instruct | 20.02 | 20.02 | 19.85 | +0.17 | +0.17 | 18.48 | -1.54 |
| microsoft__phi-4 | 21.24 | 21.24 | 21.36 | -0.12 | -0.12 | 21.51 | +0.27 |
| mistralai__Mistral-7B-Instruct-v0.3 | 20.18 | 20.18 | 19.97 | +0.21 | +0.21 | 18.40 | -1.78 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 24.64 | 24.64 | 24.71 | -0.07 | -0.07 | 24.35 | -0.29 |

## Rerun differences (prompt-level, reference strict R and grader G)

| configuration | greedy | greedy_repeat - greedy (R) | greedy_shuffled - greedy (R) | bi_greedy_shuffled - bi_greedy (R) | sample sd (R) | sample sd (G) | max abs(G-R) over runs |
|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 35.33 | -1.33 | -0.67 | +0.00 | 1.91 | 1.86 | 0.33 |
| Qwen__Qwen2.5-32B-Instruct | 37.00 | -1.00 | +0.00 | +0.00 | 2.06 | 2.03 | 0.33 |
| Qwen__Qwen2.5-7B-Instruct | 29.33 | -0.33 | +0.33 | +0.00 | 1.36 | 1.34 | 0.33 |
| Qwen__Qwen3-14B | 28.33 | -0.33 | +0.33 | +0.00 | 1.40 | 1.44 | 0.67 |
| Qwen__Qwen3-14B__thinking | 34.33 | +1.00 | +0.00 | n/a | n/a | n/a | 0.33 |
| Qwen__Qwen3-32B | 24.67 | -0.67 | -1.33 | +0.00 | 2.08 | 2.10 | 0.33 |
| Qwen__Qwen3-8B | 24.33 | +0.00 | +0.33 | +0.00 | 1.19 | 1.18 | 0.33 |
| Qwen__Qwen3-8B__thinking | 32.33 | +0.00 | +0.33 | n/a | n/a | n/a | 0.00 |
| allenai__Llama-3.1-Tulu-3-8B | 21.67 | +0.33 | +1.00 | +0.00 | 1.28 | 1.26 | 0.33 |
| allenai__OLMo-2-0325-32B-Instruct | 35.00 | +0.00 | -1.00 | +0.00 | 1.62 | 1.69 | 0.33 |
| allenai__OLMo-2-1124-13B-Instruct | 23.00 | +0.00 | +0.00 | +0.00 | 1.38 | 1.36 | 0.33 |
| allenai__OLMo-2-1124-7B-Instruct | 19.67 | +0.67 | +0.67 | +0.00 | 0.84 | 0.84 | 0.00 |
| marin-community__marin-8b-instruct | 16.33 | -1.00 | -0.33 | +0.00 | 1.10 | 1.12 | 0.67 |
| microsoft__phi-4 | 20.00 | +0.00 | +0.00 | +0.00 | 2.03 | 2.10 | 0.67 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17.33 | +0.33 | +1.33 | +0.00 | 1.08 | 1.08 | 0.00 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 23.00 | -0.33 | +0.00 | +0.00 | 1.35 | 1.27 | 0.67 |

## Per check (all runs pooled)

| check | items | G pass % | Gi pass % | R pass % | G exceptions | G!=R | Gi!=R | X pass % | Gi!=X | Gi!=XG (defects) | XG!=X (decisions, G1) | loose-only passes (Gi) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1596 | 64.3 | 64.3 | 64.3 | 0 | 0 | 0 | 32.4 | 509 | 188 | 321 | 0 |
| count:keywords_multiple | 1140 | 0.3 | 0.3 | 0.2 | 0 | 1 | 1 | 0.2 | 1 | 1 | 0 | 1 |
| count:numbers | 1824 | 38.0 | 38.0 | 38.0 | 0 | 0 | 0 | 37.9 | 5 | 5 | 0 | 138 |
| count:person_names | 1368 | 87.2 | 87.2 | 87.2 | 0 | 0 | 0 | 87.2 | 0 | 0 | 0 | 0 |
| count:pronouns | 1824 | 82.0 | 82.0 | 82.0 | 0 | 0 | 0 | 59.0 | 419 | 0 | 419 | 0 |
| count:punctuation | 1368 | 19.5 | 19.5 | 19.5 | 0 | 0 | 0 | 0.0 | 267 | 267 | 0 | 0 |
| count:unique_word_count | 2052 | 79.6 | 79.6 | 79.6 | 0 | 0 | 0 | 78.4 | 24 | 12 | 12 | 0 |
| count:word_count_range | 2508 | 21.7 | 21.7 | 21.7 | 0 | 0 | 0 | 22.6 | 144 | 0 | 144 | 156 |
| count:words_japanese | 1140 | 17.7 | 17.7 | 17.7 | 0 | 0 | 0 | 14.9 | 34 | 34 | 0 | 22 |
| custom:character_reverse | 228 | 2.2 | 2.2 | 2.2 | 0 | 0 | 0 | 0.0 | 5 | 0 | 5 | 0 |
| custom:csv_city | 228 | 50.4 | 50.4 | 50.4 | 0 | 0 | 0 | 90.4 | 91 | 0 | 91 | 0 |
| custom:csv_quotes | 228 | 6.6 | 6.6 | 6.6 | 0 | 0 | 0 | 25.4 | 43 | 0 | 43 | 0 |
| custom:csv_special_character | 228 | 7.5 | 7.5 | 7.5 | 0 | 0 | 0 | 50.0 | 97 | 0 | 97 | 13 |
| custom:date_format_list | 228 | 68.9 | 68.9 | 68.9 | 0 | 0 | 0 | 69.3 | 1 | 0 | 1 | 0 |
| custom:european_capitals_sort | 228 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 | 0.0 | 0 | 0 | 0 | 0 |
| custom:mcq_count_length | 228 | 25.0 | 25.0 | 25.0 | 0 | 0 | 0 | 40.8 | 36 | 29 | 7 | 9 |
| custom:multiples | 228 | 0.4 | 0.4 | 0.4 | 0 | 0 | 0 | 0.4 | 0 | 0 | 0 | 122 |
| custom:reverse_newline | 228 | 3.9 | 3.9 | 3.9 | 0 | 0 | 0 | 1.3 | 6 | 6 | 0 | 0 |
| custom:sentence_alphabet | 228 | 21.1 | 21.1 | 31.1 | 0 | 23 | 23 | 31.6 | 24 | 23 | 1 | 22 |
| custom:word_reverse | 228 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 | 4.4 | 6 | 4 | 2 | 0 |
| format:emoji | 2052 | 34.4 | 34.4 | 34.4 | 0 | 0 | 0 | 33.9 | 64 | 58 | 6 | 104 |
| format:line_indent | 2052 | 12.1 | 12.1 | 12.1 | 0 | 0 | 0 | 12.2 | 2 | 2 | 0 | 233 |
| format:list | 2052 | 64.9 | 64.9 | 64.9 | 0 | 0 | 0 | 57.2 | 159 | 158 | 1 | 0 |
| format:newline | 1368 | 34.1 | 34.1 | 34.1 | 0 | 0 | 0 | 34.9 | 11 | 11 | 0 | 94 |
| format:no_bullets_bullets | 1140 | 27.9 | 27.9 | 27.9 | 0 | 0 | 0 | 53.2 | 362 | 172 | 190 | 59 |
| format:no_whitespace | 912 | 51.9 | 51.9 | 51.9 | 0 | 0 | 0 | 53.5 | 15 | 0 | 15 | 0 |
| format:options | 1368 | 60.0 | 60.0 | 60.0 | 0 | 0 | 0 | 60.0 | 0 | 0 | 0 | 43 |
| format:output_template | 912 | 97.6 | 97.6 | 97.6 | 0 | 0 | 0 | 88.9 | 79 | 88 | 9 | 0 |
| format:parentheses | 1824 | 29.7 | 29.7 | 29.7 | 0 | 0 | 0 | 18.6 | 202 | 0 | 202 | 0 |
| format:quote_unquote | 1140 | 90.4 | 90.4 | 90.4 | 0 | 0 | 0 | 76.1 | 171 | 171 | 0 | 25 |
| format:quotes | 1824 | 23.8 | 23.8 | 23.8 | 0 | 0 | 0 | 15.7 | 270 | 269 | 1 | 10 |
| format:sub-bullets | 2736 | 36.5 | 36.5 | 36.5 | 0 | 0 | 0 | 61.9 | 1113 | 1113 | 0 | 1737 |
| format:thesis | 2052 | 33.1 | 33.1 | 33.1 | 0 | 0 | 0 | 20.8 | 255 | 255 | 0 | 0 |
| format:title_case | 912 | 50.7 | 50.7 | 50.7 | 0 | 0 | 0 | 52.6 | 18 | 18 | 0 | 6 |
| ratio:overlap | 2736 | 5.9 | 5.9 | 2.4 | 0 | 227 | 227 | 1.6 | 205 | 0 | 205 | 38 |
| ratio:sentence_balance | 1596 | 3.5 | 3.5 | 3.5 | 0 | 0 | 0 | 5.0 | 48 | 8 | 40 | 78 |
| ratio:sentence_type | 1368 | 4.4 | 4.4 | 4.4 | 0 | 0 | 0 | 4.2 | 35 | 20 | 19 | 69 |
| ratio:sentence_words | 1596 | 0.1 | 0.1 | 0.1 | 0 | 1 | 1 | 0.1 | 1 | 1 | 0 | 0 |
| ratio:stop_words | 2736 | 47.8 | 47.8 | 47.8 | 0 | 0 | 0 | 47.0 | 35 | 0 | 35 | 164 |
| repeat:repeat_change | 684 | 6.1 | 6.1 | 6.1 | 0 | 0 | 0 | 6.1 | 0 | 0 | 0 | 10 |
| repeat:repeat_simple | 456 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 | 7.0 | 0 | 0 | 0 | 0 |
| repeat:repeat_span | 912 | 0.0 | 0.0 | 0.0 | 911 | 911 | 0 | 0.0 | 0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1140 | 19.0 | 19.0 | 19.0 | 0 | 0 | 0 | 8.8 | 127 | 120 | 9 | 106 |
| sentence:increment | 1824 | 3.1 | 3.1 | 3.1 | 0 | 0 | 0 | 1.2 | 35 | 0 | 35 | 74 |
| sentence:keyword | 3420 | 25.6 | 25.6 | 25.6 | 0 | 0 | 0 | 23.8 | 137 | 0 | 137 | 84 |
| words:alphabet | 1368 | 10.4 | 10.4 | 10.4 | 0 | 0 | 0 | 10.4 | 0 | 0 | 0 | 17 |
| words:consonants | 3420 | 6.0 | 6.0 | 6.0 | 0 | 0 | 0 | 6.0 | 0 | 0 | 0 | 4 |
| words:keywords_specific_position | 912 | 0.0 | 0.0 | 0.0 | 156 | 156 | 0 | 0.0 | 0 | 0 | 0 | 0 |
| words:last_first | 1140 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 | 10.1 | 35 | 35 | 0 | 12 |
| words:no_consecutive | 1824 | 4.2 | 4.2 | 4.2 | 0 | 0 | 0 | 4.0 | 3 | 3 | 0 | 40 |
| words:odd_even_syllables | 2052 | 0.8 | 0.8 | 0.8 | 0 | 0 | 0 | 0.8 | 0 | 0 | 0 | 3 |
| words:palindrome | 1596 | 30.3 | 30.3 | 30.3 | 0 | 0 | 0 | 9.9 | 326 | 1 | 327 | 0 |
| words:paragraph_last_first | 1368 | 7.8 | 7.8 | 7.8 | 0 | 0 | 0 | 9.9 | 29 | 29 | 0 | 50 |
| words:prime_lengths | 1140 | 4.6 | 4.6 | 4.6 | 0 | 0 | 0 | 4.7 | 2 | 2 | 0 | 0 |
| words:repeats | 1140 | 17.5 | 17.5 | 17.5 | 0 | 0 | 0 | 17.5 | 0 | 0 | 0 | 16 |
| words:start_verb | 1368 | 39.5 | 39.5 | 39.5 | 0 | 0 | 0 | 41.1 | 21 | 0 | 21 | 79 |
| words:vowel | 2280 | 4.1 | 4.1 | 4.1 | 0 | 0 | 0 | 4.0 | 1 | 1 | 0 | 27 |
| words:words_position | 684 | 0.3 | 0.3 | 1.0 | 0 | 5 | 5 | 0.9 | 4 | 4 | 0 | 1 |

## Scored coverage (items with a verdict / expected items)

- g: 77365/78432 = 98.640%
- gi: 78432/78432 = 100.000%
- r: 78432/78432 = 100.000%
- gl: 77365/78432 = 98.640%
- gli: 78432/78432 = 100.000%
- rl: 78432/78432 = 100.000%
- x: 78432/78432 = 100.000%
- xg: 78432/78432 = 100.000%

## Responses: extraction failures, truncation, empty

| configuration | unclosed reasoning (extraction failures) | checks passed on them (G / Gi / R) | truncated | empty |
|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 0 | 0 / 0 / 0 | 163 | 0 |
| Qwen__Qwen2.5-32B-Instruct | 0 | 0 / 0 / 0 | 113 | 0 |
| Qwen__Qwen2.5-7B-Instruct | 0 | 0 / 0 / 0 | 214 | 0 |
| Qwen__Qwen3-14B | 0 | 0 / 0 / 0 | 522 | 28 |
| Qwen__Qwen3-14B__thinking | 32 | 7 / 7 / 7 | 53 | 0 |
| Qwen__Qwen3-32B | 0 | 0 / 0 / 0 | 427 | 0 |
| Qwen__Qwen3-8B | 0 | 0 / 0 / 0 | 695 | 5 |
| Qwen__Qwen3-8B__thinking | 104 | 38 / 38 / 38 | 135 | 0 |
| allenai__Llama-3.1-Tulu-3-8B | 0 | 0 / 0 / 0 | 275 | 0 |
| allenai__OLMo-2-0325-32B-Instruct | 0 | 0 / 0 / 0 | 78 | 0 |
| allenai__OLMo-2-1124-13B-Instruct | 0 | 0 / 0 / 0 | 146 | 0 |
| allenai__OLMo-2-1124-7B-Instruct | 0 | 0 / 0 / 0 | 212 | 0 |
| marin-community__marin-8b-instruct | 0 | 0 / 0 / 0 | 444 | 4 |
| microsoft__phi-4 | 0 | 0 / 0 / 0 | 202 | 0 |
| mistralai__Mistral-7B-Instruct-v0.3 | 0 | 0 / 0 / 0 | 253 | 0 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 0 | 0 / 0 / 0 | 233 | 0 |

## Held-out runs only (sample7; greedy_repeat for the thinking configurations), prompt-level

| configuration | run | G | Gi | R | XG | X | X-G | X-XG |
|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | sample7 | 34.33 | 34.33 | 34.33 | 31.33 | 29.67 | -4.67 | -1.67 |
| Qwen__Qwen2.5-32B-Instruct | sample7 | 35.00 | 35.00 | 35.33 | 32.33 | 33.33 | -1.67 | +1.00 |
| Qwen__Qwen2.5-7B-Instruct | sample7 | 26.00 | 26.00 | 25.67 | 24.33 | 24.00 | -2.00 | -0.33 |
| Qwen__Qwen3-14B | sample7 | 30.00 | 30.00 | 30.33 | 29.33 | 28.00 | -2.00 | -1.33 |
| Qwen__Qwen3-14B__thinking | greedy_repeat | 35.00 | 35.00 | 35.33 | 38.00 | 36.67 | +1.67 | -1.33 |
| Qwen__Qwen3-32B | sample7 | 27.33 | 27.33 | 27.33 | 26.00 | 24.67 | -2.67 | -1.33 |
| Qwen__Qwen3-8B | sample7 | 27.67 | 27.67 | 27.67 | 26.00 | 24.67 | -3.00 | -1.33 |
| Qwen__Qwen3-8B__thinking | greedy_repeat | 32.33 | 32.33 | 32.33 | 32.67 | 29.67 | -2.67 | -3.00 |
| allenai__Llama-3.1-Tulu-3-8B | sample7 | 20.33 | 20.33 | 20.33 | 21.33 | 21.00 | +0.67 | -0.33 |
| allenai__OLMo-2-0325-32B-Instruct | sample7 | 30.00 | 30.00 | 30.33 | 29.67 | 28.67 | -1.33 | -1.00 |
| allenai__OLMo-2-1124-13B-Instruct | sample7 | 24.33 | 24.33 | 24.33 | 21.67 | 18.33 | -6.00 | -3.33 |
| allenai__OLMo-2-1124-7B-Instruct | sample7 | 20.00 | 20.00 | 20.00 | 17.67 | 17.00 | -3.00 | -0.67 |
| marin-community__marin-8b-instruct | sample7 | 18.67 | 18.67 | 18.67 | 17.00 | 15.00 | -3.67 | -2.00 |
| microsoft__phi-4 | sample7 | 18.33 | 18.33 | 18.67 | 19.33 | 20.33 | +2.00 | +1.00 |
| mistralai__Mistral-7B-Instruct-v0.3 | sample7 | 17.33 | 17.33 | 17.33 | 17.33 | 17.00 | -0.33 | -0.33 |
| mistralai__Mistral-Small-24B-Instruct-2501 | sample7 | 23.33 | 23.33 | 24.00 | 24.00 | 22.33 | -1.00 | -1.67 |
| mean of 16 held-out runs | | 26.25 | 26.25 | 26.38 | 25.50 | 24.40 | -1.85 | -1.10 |
- verdicts where g != r: 1324/78432 = 1.69%
- verdicts where gi != r: 257/78432 = 0.33%
- verdicts where gi != xg: 3108/78432 = 3.96%
- verdicts where xg != x: 2395/78432 = 3.05%
- verdicts where g != x: 6544/78432 = 8.34%
