# Panel tables (all; 78432 instruction instances)

Coverage (share with a verdict): grader strict 100.0000%, grader loose 100.0000%, reference strict 100.0000%, reference loose 100.0000%, replacement 100.0000%

| configuration | runs | grader strict | replacement | change | reference strict | grader loose | greedy change | rerun diffs (greedy_repeat / shuffled / bi) | sample SD |
|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 17 | 34.1 | 30.1 | -3.9 | 34.1 | 37.8 | -5.0 | -1.0 / -0.3 / -0.7 | 1.9 |
| Qwen__Qwen2.5-32B-Instruct | 13 | 35.2 | 33.5 | -1.7 | 35.2 | 38.3 | -3.3 | -1.3 / -0.3 / -1.0 | 2.0 |
| Qwen__Qwen2.5-7B-Instruct | 17 | 27.4 | 25.0 | -2.4 | 27.5 | 30.4 | -2.7 | -0.3 / +0.3 / -0.3 | 1.3 |
| Qwen__Qwen3-14B | 17 | 27.7 | 27.8 | +0.0 | 27.8 | 31.3 | -0.3 | -0.3 / +0.3 / -1.3 | 1.4 |
| Qwen__Qwen3-14B__thinking | 3 | 34.3 | 37.6 | +3.2 | 34.7 | 39.3 | +3.0 | +1.0 / +0.0 / +nan | - |
| Qwen__Qwen3-32B | 13 | 25.1 | 25.8 | +0.7 | 25.2 | 29.4 | -0.3 | -0.7 / -1.7 / +0.3 | 2.1 |
| Qwen__Qwen3-8B | 17 | 25.2 | 23.7 | -1.5 | 25.1 | 29.5 | -1.3 | +0.0 / +0.3 / -1.0 | 1.2 |
| Qwen__Qwen3-8B__thinking | 3 | 32.4 | 30.1 | -2.3 | 32.4 | 36.3 | -2.7 | +0.0 / +0.3 / +nan | - |
| allenai__Llama-3.1-Tulu-3-8B | 17 | 22.7 | 23.4 | +0.8 | 22.7 | 26.3 | +1.0 | +0.3 / +1.0 / +1.3 | 1.3 |
| allenai__OLMo-2-0325-32B-Instruct | 13 | 33.3 | 30.6 | -2.7 | 33.3 | 37.0 | -3.0 | +0.0 / -1.0 / -1.3 | 1.7 |
| allenai__OLMo-2-1124-13B-Instruct | 17 | 22.6 | 18.8 | -3.9 | 22.7 | 26.8 | -4.7 | +0.0 / +0.0 / +1.0 | 1.4 |
| allenai__OLMo-2-1124-7B-Instruct | 17 | 20.4 | 18.3 | -2.1 | 20.4 | 24.9 | -1.0 | +0.7 / +0.7 / +1.0 | 0.8 |
| marin-community__marin-8b-instruct | 17 | 17.4 | 16.7 | -0.7 | 17.4 | 21.5 | -0.7 | -1.0 / -0.3 / +0.3 | 1.1 |
| microsoft__phi-4 | 17 | 19.1 | 20.3 | +1.2 | 19.3 | 24.3 | +0.7 | +0.0 / +0.0 / +0.0 | 2.1 |
| mistralai__Mistral-7B-Instruct-v0.3 | 17 | 17.6 | 16.3 | -1.3 | 17.6 | 20.8 | -1.0 | +0.3 / +1.3 / +0.3 | 1.1 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 13 | 21.8 | 23.3 | +1.4 | 22.3 | 27.9 | +1.7 | -0.3 / +0.0 / +1.3 | 1.3 |

| check | n | grader | replacement | reference | grader loose | grader pass, repl. fail | grader fail, repl. pass | grader vs ref |
|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1596 | 64.3 | 52.1 | 64.3 | 64.3 | 195 | 0 | 0 |
| count:keywords_multiple | 1140 | 0.3 | 0.2 | 0.2 | 0.4 | 1 | 0 | 1 |
| count:numbers | 1824 | 38.0 | 37.9 | 38.0 | 45.6 | 4 | 1 | 0 |
| count:person_names | 1368 | 87.2 | 87.2 | 87.2 | 87.2 | 0 | 0 | 0 |
| count:pronouns | 1824 | 82.0 | 58.3 | 82.0 | 82.0 | 435 | 2 | 0 |
| count:punctuation | 1368 | 19.5 | 0.0 | 19.5 | 19.5 | 267 | 0 | 0 |
| count:unique_word_count | 2052 | 79.6 | 76.8 | 79.6 | 79.6 | 60 | 2 | 0 |
| count:word_count_range | 2508 | 21.7 | 22.6 | 21.7 | 27.9 | 58 | 80 | 0 |
| count:words_japanese | 1140 | 17.7 | 9.8 | 17.7 | 19.6 | 90 | 0 | 0 |
| custom:character_reverse | 228 | 2.2 | 0.0 | 2.2 | 2.2 | 5 | 0 | 0 |
| custom:csv_city | 228 | 50.4 | 90.4 | 50.4 | 50.4 | 0 | 91 | 0 |
| custom:csv_quotes | 228 | 6.6 | 25.4 | 6.6 | 6.6 | 0 | 43 | 0 |
| custom:csv_special_character | 228 | 7.5 | 49.1 | 7.5 | 13.2 | 1 | 96 | 0 |
| custom:date_format_list | 228 | 68.9 | 68.9 | 68.9 | 68.9 | 0 | 0 | 0 |
| custom:european_capitals_sort | 228 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| custom:mcq_count_length | 228 | 25.0 | 40.8 | 25.0 | 28.9 | 0 | 36 | 0 |
| custom:multiples | 228 | 0.4 | 0.4 | 0.4 | 53.9 | 0 | 0 | 0 |
| custom:reverse_newline | 228 | 3.9 | 1.3 | 3.9 | 3.9 | 6 | 0 | 0 |
| custom:sentence_alphabet | 228 | 21.1 | 33.3 | 31.1 | 30.7 | 0 | 28 | 23 |
| custom:word_reverse | 228 | 7.0 | 13.6 | 7.0 | 7.0 | 8 | 23 | 0 |
| format:emoji | 2052 | 34.4 | 41.1 | 34.4 | 39.4 | 15 | 154 | 0 |
| format:line_indent | 2052 | 12.1 | 6.0 | 12.1 | 23.5 | 126 | 1 | 0 |
| format:list | 2052 | 64.9 | 62.1 | 64.9 | 64.9 | 58 | 0 | 0 |
| format:newline | 1368 | 34.1 | 34.6 | 34.1 | 41.0 | 4 | 11 | 0 |
| format:no_bullets_bullets | 1140 | 27.9 | 52.7 | 27.9 | 33.1 | 38 | 321 | 0 |
| format:no_whitespace | 912 | 51.9 | 53.5 | 51.9 | 51.9 | 0 | 15 | 0 |
| format:options | 1368 | 60.0 | 61.5 | 60.0 | 63.2 | 0 | 20 | 0 |
| format:output_template | 912 | 97.6 | 93.6 | 97.6 | 97.6 | 36 | 0 | 0 |
| format:parentheses | 1824 | 29.7 | 15.4 | 29.7 | 29.7 | 261 | 0 | 0 |
| format:quote_unquote | 1140 | 90.4 | 60.0 | 90.4 | 92.5 | 350 | 4 | 0 |
| format:quotes | 1824 | 23.8 | 14.8 | 23.8 | 24.3 | 233 | 69 | 0 |
| format:sub-bullets | 2736 | 36.5 | 61.9 | 36.5 | 100.0 | 209 | 904 | 0 |
| format:thesis | 2052 | 33.1 | 6.8 | 33.1 | 33.1 | 540 | 0 | 0 |
| format:title_case | 912 | 50.7 | 52.6 | 50.7 | 51.3 | 0 | 18 | 0 |
| ratio:overlap | 2736 | 5.9 | 1.4 | 2.4 | 7.3 | 162 | 39 | 227 |
| ratio:sentence_balance | 1596 | 3.5 | 3.3 | 3.5 | 8.4 | 12 | 8 | 0 |
| ratio:sentence_type | 1368 | 4.4 | 4.0 | 4.4 | 9.4 | 17 | 12 | 0 |
| ratio:sentence_words | 1596 | 0.1 | 0.1 | 0.1 | 0.1 | 1 | 0 | 1 |
| ratio:stop_words | 2736 | 47.8 | 47.9 | 47.8 | 53.8 | 17 | 18 | 0 |
| repeat:repeat_change | 684 | 6.1 | 6.1 | 6.1 | 7.6 | 0 | 0 | 0 |
| repeat:repeat_simple | 456 | 7.0 | 7.0 | 7.0 | 7.0 | 0 | 0 | 0 |
| repeat:repeat_span | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1140 | 19.0 | 8.9 | 19.0 | 28.3 | 121 | 6 | 0 |
| sentence:increment | 1824 | 3.1 | 0.1 | 3.1 | 7.2 | 56 | 0 | 0 |
| sentence:keyword | 3420 | 25.6 | 24.2 | 25.6 | 28.1 | 105 | 56 | 0 |
| words:alphabet | 1368 | 10.4 | 10.2 | 10.4 | 11.6 | 4 | 2 | 0 |
| words:consonants | 3420 | 6.0 | 5.7 | 6.0 | 6.1 | 9 | 0 | 0 |
| words:keywords_specific_position | 912 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| words:last_first | 1140 | 7.0 | 8.1 | 7.0 | 8.1 | 25 | 37 | 0 |
| words:no_consecutive | 1824 | 4.2 | 3.4 | 4.2 | 6.4 | 14 | 0 | 0 |
| words:odd_even_syllables | 2052 | 0.8 | 0.8 | 0.8 | 1.0 | 0 | 0 | 0 |
| words:palindrome | 1596 | 30.3 | 9.9 | 30.3 | 30.3 | 326 | 0 | 0 |
| words:paragraph_last_first | 1368 | 7.8 | 9.9 | 7.8 | 11.5 | 0 | 29 | 0 |
| words:prime_lengths | 1140 | 4.6 | 4.6 | 4.6 | 4.6 | 1 | 1 | 0 |
| words:repeats | 1140 | 17.5 | 17.3 | 17.5 | 18.9 | 2 | 0 | 0 |
| words:start_verb | 1368 | 39.5 | 70.0 | 39.5 | 45.3 | 43 | 459 | 0 |
| words:vowel | 2280 | 4.1 | 4.0 | 4.1 | 5.3 | 1 | 0 | 0 |
| words:words_position | 684 | 0.3 | 0.9 | 1.0 | 0.4 | 0 | 4 | 5 |
