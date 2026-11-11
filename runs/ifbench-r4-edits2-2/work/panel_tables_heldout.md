# Panel tables (heldout; 5504 instruction instances)

Coverage (share with a verdict): grader strict 100.0000%, grader loose 100.0000%, reference strict 100.0000%, reference loose 100.0000%, replacement 100.0000%

| configuration | runs | grader strict | replacement | change | reference strict | grader loose | greedy change | rerun diffs (greedy_repeat / shuffled / bi) | sample SD |
|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 1 | 34.0 | 29.7 | -4.3 | 34.0 | 37.3 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen2.5-32B-Instruct | 1 | 36.0 | 33.3 | -2.7 | 36.0 | 40.3 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen2.5-7B-Instruct | 1 | 28.7 | 26.7 | -2.0 | 29.0 | 31.0 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen3-14B | 1 | 28.0 | 28.0 | +0.0 | 28.0 | 31.7 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen3-14B__thinking | 1 | 35.0 | 38.3 | +3.3 | 35.3 | 39.7 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen3-32B | 1 | 24.0 | 25.7 | +1.7 | 24.0 | 27.7 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen3-8B | 1 | 24.7 | 24.0 | -0.7 | 24.3 | 29.0 | +nan | +nan / +nan / +nan | - |
| Qwen__Qwen3-8B__thinking | 1 | 32.3 | 30.3 | -2.0 | 32.3 | 37.0 | +nan | +nan / +nan / +nan | - |
| allenai__Llama-3.1-Tulu-3-8B | 1 | 22.0 | 22.3 | +0.3 | 22.0 | 26.3 | +nan | +nan / +nan / +nan | - |
| allenai__OLMo-2-0325-32B-Instruct | 1 | 35.0 | 32.3 | -2.7 | 35.0 | 39.3 | +nan | +nan / +nan / +nan | - |
| allenai__OLMo-2-1124-13B-Instruct | 1 | 23.0 | 18.7 | -4.3 | 23.0 | 27.0 | +nan | +nan / +nan / +nan | - |
| allenai__OLMo-2-1124-7B-Instruct | 1 | 20.3 | 19.0 | -1.3 | 20.3 | 24.7 | +nan | +nan / +nan / +nan | - |
| marin-community__marin-8b-instruct | 1 | 15.3 | 15.3 | +0.0 | 15.3 | 19.7 | +nan | +nan / +nan / +nan | - |
| microsoft__phi-4 | 1 | 20.0 | 20.7 | +0.7 | 20.0 | 25.0 | +nan | +nan / +nan / +nan | - |
| mistralai__Mistral-7B-Instruct-v0.3 | 1 | 17.7 | 15.7 | -2.0 | 17.7 | 20.3 | +nan | +nan / +nan / +nan | - |
| mistralai__Mistral-Small-24B-Instruct-2501 | 1 | 22.3 | 23.7 | +1.3 | 22.7 | 28.3 | +nan | +nan / +nan / +nan | - |

| check | n | grader | replacement | reference | grader loose | grader pass, repl. fail | grader fail, repl. pass | grader vs ref |
|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 112 | 67.9 | 55.4 | 67.9 | 67.9 | 14 | 0 | 0 |
| count:keywords_multiple | 80 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| count:numbers | 128 | 42.2 | 42.2 | 42.2 | 49.2 | 0 | 0 | 0 |
| count:person_names | 96 | 88.5 | 88.5 | 88.5 | 88.5 | 0 | 0 | 0 |
| count:pronouns | 128 | 81.2 | 59.4 | 81.2 | 81.2 | 29 | 1 | 0 |
| count:punctuation | 96 | 20.8 | 0.0 | 20.8 | 20.8 | 20 | 0 | 0 |
| count:unique_word_count | 144 | 79.2 | 75.7 | 79.2 | 79.2 | 5 | 0 | 0 |
| count:word_count_range | 176 | 25.0 | 27.3 | 25.0 | 31.8 | 6 | 10 | 0 |
| count:words_japanese | 80 | 15.0 | 8.8 | 15.0 | 16.2 | 5 | 0 | 0 |
| custom:character_reverse | 16 | 6.2 | 0.0 | 6.2 | 6.2 | 1 | 0 | 0 |
| custom:csv_city | 16 | 56.2 | 93.8 | 56.2 | 56.2 | 0 | 6 | 0 |
| custom:csv_quotes | 16 | 12.5 | 31.2 | 12.5 | 12.5 | 0 | 3 | 0 |
| custom:csv_special_character | 16 | 18.8 | 56.2 | 18.8 | 25.0 | 0 | 6 | 0 |
| custom:date_format_list | 16 | 62.5 | 62.5 | 62.5 | 62.5 | 0 | 0 | 0 |
| custom:european_capitals_sort | 16 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| custom:mcq_count_length | 16 | 31.2 | 50.0 | 31.2 | 31.2 | 0 | 3 | 0 |
| custom:multiples | 16 | 0.0 | 0.0 | 0.0 | 62.5 | 0 | 0 | 0 |
| custom:reverse_newline | 16 | 6.2 | 6.2 | 6.2 | 6.2 | 0 | 0 | 0 |
| custom:sentence_alphabet | 16 | 31.2 | 37.5 | 37.5 | 37.5 | 0 | 1 | 1 |
| custom:word_reverse | 16 | 6.2 | 18.8 | 6.2 | 6.2 | 0 | 2 | 0 |
| format:emoji | 144 | 36.8 | 45.8 | 36.8 | 41.7 | 1 | 14 | 0 |
| format:line_indent | 144 | 16.0 | 9.7 | 16.0 | 26.4 | 9 | 0 | 0 |
| format:list | 144 | 66.7 | 62.5 | 66.7 | 66.7 | 6 | 0 | 0 |
| format:newline | 96 | 35.4 | 36.5 | 35.4 | 43.8 | 0 | 1 | 0 |
| format:no_bullets_bullets | 80 | 35.0 | 56.2 | 35.0 | 42.5 | 5 | 22 | 0 |
| format:no_whitespace | 64 | 57.8 | 59.4 | 57.8 | 57.8 | 0 | 1 | 0 |
| format:options | 96 | 60.4 | 61.5 | 60.4 | 63.5 | 0 | 1 | 0 |
| format:output_template | 64 | 96.9 | 93.8 | 96.9 | 96.9 | 2 | 0 | 0 |
| format:parentheses | 128 | 28.9 | 14.1 | 28.9 | 28.9 | 19 | 0 | 0 |
| format:quote_unquote | 80 | 90.0 | 57.5 | 90.0 | 93.8 | 26 | 0 | 0 |
| format:quotes | 128 | 21.9 | 15.6 | 21.9 | 21.9 | 14 | 6 | 0 |
| format:sub-bullets | 192 | 36.5 | 67.7 | 36.5 | 100.0 | 12 | 72 | 0 |
| format:thesis | 144 | 34.7 | 7.6 | 34.7 | 34.7 | 39 | 0 | 0 |
| format:title_case | 64 | 50.0 | 53.1 | 50.0 | 50.0 | 0 | 2 | 0 |
| ratio:overlap | 192 | 6.8 | 1.0 | 2.6 | 8.3 | 13 | 2 | 18 |
| ratio:sentence_balance | 112 | 5.4 | 3.6 | 5.4 | 8.9 | 3 | 1 | 0 |
| ratio:sentence_type | 96 | 7.3 | 6.2 | 7.3 | 13.5 | 2 | 1 | 0 |
| ratio:sentence_words | 112 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| ratio:stop_words | 192 | 49.5 | 49.0 | 49.5 | 55.7 | 2 | 1 | 0 |
| repeat:repeat_change | 48 | 14.6 | 14.6 | 14.6 | 16.7 | 0 | 0 | 0 |
| repeat:repeat_simple | 32 | 6.2 | 6.2 | 6.2 | 6.2 | 0 | 0 | 0 |
| repeat:repeat_span | 64 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 80 | 20.0 | 7.5 | 20.0 | 30.0 | 10 | 0 | 0 |
| sentence:increment | 128 | 3.1 | 0.0 | 3.1 | 7.8 | 4 | 0 | 0 |
| sentence:keyword | 240 | 25.8 | 26.2 | 25.8 | 28.3 | 5 | 6 | 0 |
| words:alphabet | 96 | 12.5 | 12.5 | 12.5 | 13.5 | 0 | 0 | 0 |
| words:consonants | 240 | 7.1 | 6.7 | 7.1 | 7.1 | 1 | 0 | 0 |
| words:keywords_specific_position | 64 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| words:last_first | 80 | 8.8 | 8.8 | 8.8 | 8.8 | 1 | 1 | 0 |
| words:no_consecutive | 128 | 3.9 | 2.3 | 3.9 | 6.2 | 2 | 0 | 0 |
| words:odd_even_syllables | 144 | 0.7 | 0.7 | 0.7 | 0.7 | 0 | 0 | 0 |
| words:palindrome | 112 | 38.4 | 16.1 | 38.4 | 38.4 | 25 | 0 | 0 |
| words:paragraph_last_first | 96 | 11.5 | 15.6 | 11.5 | 15.6 | 0 | 4 | 0 |
| words:prime_lengths | 80 | 6.2 | 6.2 | 6.2 | 6.2 | 0 | 0 | 0 |
| words:repeats | 80 | 18.8 | 18.8 | 18.8 | 20.0 | 0 | 0 | 0 |
| words:start_verb | 96 | 37.5 | 69.8 | 37.5 | 44.8 | 1 | 32 | 0 |
| words:vowel | 160 | 5.0 | 5.0 | 5.0 | 6.2 | 0 | 0 | 0 |
| words:words_position | 48 | 0.0 | 2.1 | 2.1 | 0.0 | 0 | 1 | 1 |
