# Panel tables (exclude_heldout; 72928 instruction instances)

Coverage (share with a verdict): grader strict 100.0000%, grader loose 100.0000%, reference strict 100.0000%, reference loose 100.0000%, replacement 100.0000%

| configuration | runs | grader strict | replacement | change | reference strict | grader loose | greedy change | rerun diffs (greedy_repeat / shuffled / bi) | sample SD |
|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-14B-Instruct | 16 | 34.1 | 30.2 | -3.9 | 34.1 | 37.9 | -5.0 | +nan / -0.3 / -0.7 | 1.9 |
| Qwen__Qwen2.5-32B-Instruct | 12 | 35.1 | 33.5 | -1.6 | 35.1 | 38.1 | -3.3 | +nan / -0.3 / -1.0 | 2.0 |
| Qwen__Qwen2.5-7B-Instruct | 16 | 27.3 | 24.9 | -2.4 | 27.4 | 30.4 | -2.7 | +nan / +0.3 / -0.3 | 1.3 |
| Qwen__Qwen3-14B | 16 | 27.7 | 27.8 | +0.0 | 27.8 | 31.2 | -0.3 | +nan / +0.3 / -1.3 | 1.4 |
| Qwen__Qwen3-14B__thinking | 2 | 34.0 | 37.2 | +3.2 | 34.3 | 39.2 | +3.0 | +nan / +0.0 / +nan | - |
| Qwen__Qwen3-32B | 12 | 25.2 | 25.8 | +0.6 | 25.3 | 29.6 | -0.3 | +nan / -1.7 / +0.3 | 2.1 |
| Qwen__Qwen3-8B | 16 | 25.2 | 23.7 | -1.5 | 25.1 | 29.5 | -1.3 | +nan / +0.3 / -1.0 | 1.2 |
| Qwen__Qwen3-8B__thinking | 2 | 32.5 | 30.0 | -2.5 | 32.5 | 36.0 | -2.7 | +nan / +0.3 / +nan | - |
| allenai__Llama-3.1-Tulu-3-8B | 16 | 22.7 | 23.5 | +0.8 | 22.8 | 26.3 | +1.0 | +nan / +1.0 / +1.3 | 1.3 |
| allenai__OLMo-2-0325-32B-Instruct | 12 | 33.1 | 30.5 | -2.7 | 33.2 | 36.8 | -3.0 | +nan / -1.0 / -1.3 | 1.7 |
| allenai__OLMo-2-1124-13B-Instruct | 16 | 22.6 | 18.8 | -3.8 | 22.7 | 26.8 | -4.7 | +nan / +0.0 / +1.0 | 1.4 |
| allenai__OLMo-2-1124-7B-Instruct | 16 | 20.4 | 18.2 | -2.2 | 20.4 | 24.9 | -1.0 | +nan / +0.7 / +1.0 | 0.8 |
| marin-community__marin-8b-instruct | 16 | 17.5 | 16.8 | -0.7 | 17.5 | 21.7 | -0.7 | +nan / -0.3 / +0.3 | 1.1 |
| microsoft__phi-4 | 16 | 19.0 | 20.2 | +1.3 | 19.2 | 24.2 | +0.7 | +nan / +0.0 / +0.0 | 2.1 |
| mistralai__Mistral-7B-Instruct-v0.3 | 16 | 17.6 | 16.3 | -1.3 | 17.6 | 20.8 | -1.0 | +nan / +1.3 / +0.3 | 1.1 |
| mistralai__Mistral-Small-24B-Instruct-2501 | 12 | 21.8 | 23.2 | +1.4 | 22.2 | 27.9 | +1.7 | +nan / +0.0 / +1.3 | 1.3 |

| check | n | grader | replacement | reference | grader loose | grader pass, repl. fail | grader fail, repl. pass | grader vs ref |
|---|---|---|---|---|---|---|---|---|
| count:conjunctions | 1484 | 64.0 | 51.8 | 64.0 | 64.0 | 181 | 0 | 0 |
| count:keywords_multiple | 1060 | 0.3 | 0.2 | 0.2 | 0.4 | 1 | 0 | 1 |
| count:numbers | 1696 | 37.7 | 37.6 | 37.7 | 45.3 | 4 | 1 | 0 |
| count:person_names | 1272 | 87.1 | 87.1 | 87.1 | 87.1 | 0 | 0 | 0 |
| count:pronouns | 1696 | 82.1 | 58.2 | 82.1 | 82.1 | 406 | 1 | 0 |
| count:punctuation | 1272 | 19.4 | 0.0 | 19.4 | 19.4 | 247 | 0 | 0 |
| count:unique_word_count | 1908 | 79.6 | 76.8 | 79.6 | 79.6 | 55 | 2 | 0 |
| count:word_count_range | 2332 | 21.4 | 22.2 | 21.4 | 27.6 | 52 | 70 | 0 |
| count:words_japanese | 1060 | 17.9 | 9.9 | 17.9 | 19.9 | 85 | 0 | 0 |
| custom:character_reverse | 212 | 1.9 | 0.0 | 1.9 | 1.9 | 4 | 0 | 0 |
| custom:csv_city | 212 | 50.0 | 90.1 | 50.0 | 50.0 | 0 | 85 | 0 |
| custom:csv_quotes | 212 | 6.1 | 25.0 | 6.1 | 6.1 | 0 | 40 | 0 |
| custom:csv_special_character | 212 | 6.6 | 48.6 | 6.6 | 12.3 | 1 | 90 | 0 |
| custom:date_format_list | 212 | 69.3 | 69.3 | 69.3 | 69.3 | 0 | 0 | 0 |
| custom:european_capitals_sort | 212 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| custom:mcq_count_length | 212 | 24.5 | 40.1 | 24.5 | 28.8 | 0 | 33 | 0 |
| custom:multiples | 212 | 0.5 | 0.5 | 0.5 | 53.3 | 0 | 0 | 0 |
| custom:reverse_newline | 212 | 3.8 | 0.9 | 3.8 | 3.8 | 6 | 0 | 0 |
| custom:sentence_alphabet | 212 | 20.3 | 33.0 | 30.7 | 30.2 | 0 | 27 | 22 |
| custom:word_reverse | 212 | 7.1 | 13.2 | 7.1 | 7.1 | 8 | 21 | 0 |
| format:emoji | 1908 | 34.2 | 40.8 | 34.2 | 39.3 | 14 | 140 | 0 |
| format:line_indent | 1908 | 11.8 | 5.8 | 11.8 | 23.3 | 117 | 1 | 0 |
| format:list | 1908 | 64.8 | 62.1 | 64.8 | 64.8 | 52 | 0 | 0 |
| format:newline | 1272 | 34.0 | 34.5 | 34.0 | 40.8 | 4 | 10 | 0 |
| format:no_bullets_bullets | 1060 | 27.4 | 52.5 | 27.4 | 32.4 | 33 | 299 | 0 |
| format:no_whitespace | 848 | 51.4 | 53.1 | 51.4 | 51.4 | 0 | 14 | 0 |
| format:options | 1272 | 60.0 | 61.5 | 60.0 | 63.1 | 0 | 19 | 0 |
| format:output_template | 848 | 97.6 | 93.6 | 97.6 | 97.6 | 34 | 0 | 0 |
| format:parentheses | 1696 | 29.7 | 15.4 | 29.7 | 29.7 | 242 | 0 | 0 |
| format:quote_unquote | 1060 | 90.4 | 60.2 | 90.4 | 92.5 | 324 | 4 | 0 |
| format:quotes | 1696 | 23.9 | 14.7 | 23.9 | 24.5 | 219 | 63 | 0 |
| format:sub-bullets | 2544 | 36.5 | 61.5 | 36.5 | 100.0 | 197 | 832 | 0 |
| format:thesis | 1908 | 33.0 | 6.7 | 33.0 | 33.0 | 501 | 0 | 0 |
| format:title_case | 848 | 50.7 | 52.6 | 50.7 | 51.4 | 0 | 16 | 0 |
| ratio:overlap | 2544 | 5.9 | 1.5 | 2.4 | 7.2 | 149 | 37 | 209 |
| ratio:sentence_balance | 1484 | 3.4 | 3.2 | 3.4 | 8.4 | 9 | 7 | 0 |
| ratio:sentence_type | 1272 | 4.2 | 3.9 | 4.2 | 9.1 | 15 | 11 | 0 |
| ratio:sentence_words | 1484 | 0.1 | 0.1 | 0.1 | 0.1 | 1 | 0 | 1 |
| ratio:stop_words | 2544 | 47.7 | 47.8 | 47.7 | 53.7 | 15 | 17 | 0 |
| repeat:repeat_change | 636 | 5.5 | 5.5 | 5.5 | 6.9 | 0 | 0 | 0 |
| repeat:repeat_simple | 424 | 7.1 | 7.1 | 7.1 | 7.1 | 0 | 0 | 0 |
| repeat:repeat_span | 848 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| sentence:alliteration_increment | 1060 | 19.0 | 9.1 | 19.0 | 28.2 | 111 | 6 | 0 |
| sentence:increment | 1696 | 3.1 | 0.1 | 3.1 | 7.1 | 52 | 0 | 0 |
| sentence:keyword | 3180 | 25.6 | 24.0 | 25.6 | 28.1 | 100 | 50 | 0 |
| words:alphabet | 1272 | 10.2 | 10.1 | 10.2 | 11.5 | 4 | 2 | 0 |
| words:consonants | 3180 | 5.9 | 5.6 | 5.9 | 6.0 | 8 | 0 | 0 |
| words:keywords_specific_position | 848 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |
| words:last_first | 1060 | 6.9 | 8.0 | 6.9 | 8.0 | 24 | 36 | 0 |
| words:no_consecutive | 1696 | 4.2 | 3.5 | 4.2 | 6.4 | 12 | 0 | 0 |
| words:odd_even_syllables | 1908 | 0.8 | 0.8 | 0.8 | 1.0 | 0 | 0 | 0 |
| words:palindrome | 1484 | 29.7 | 9.4 | 29.7 | 29.7 | 301 | 0 | 0 |
| words:paragraph_last_first | 1272 | 7.5 | 9.5 | 7.5 | 11.2 | 0 | 25 | 0 |
| words:prime_lengths | 1060 | 4.4 | 4.4 | 4.4 | 4.4 | 1 | 1 | 0 |
| words:repeats | 1060 | 17.4 | 17.2 | 17.4 | 18.8 | 2 | 0 | 0 |
| words:start_verb | 1272 | 39.7 | 70.0 | 39.7 | 45.4 | 42 | 427 | 0 |
| words:vowel | 2120 | 4.0 | 4.0 | 4.0 | 5.2 | 1 | 0 | 0 |
| words:words_position | 636 | 0.3 | 0.8 | 0.9 | 0.5 | 0 | 3 | 4 |
