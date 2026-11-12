| Run | Rows | A score | Replacement score | Replacement − A, points [95% CI] | Held-out rows | Held-out replacement − A [95% CI] | B gate pass | Replacement gate pass | Replacement − B gate, points [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| Qwen__Qwen2.5-7B-Instruct/sample0.jsonl | 4000 | 20.0 | 19.7 | -0.4 [-1.5, +0.7] | 3700 | -0.4 [-1.4, +0.7] | 32.5 | 24.6 | -7.9 [-9.2, -6.6] |
| Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl | 1000 | 29.3 | 34.6 | +5.3 [+3.3, +7.3] | 700 | +5.3 [+3.1, +7.7] | 49.6 | 42.8 | -6.8 [-9.6, -4.1] |
| Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl | 1000 | 29.5 | 34.9 | +5.4 [+3.4, +7.4] | 700 | +5.1 [+2.7, +7.6] | 49.7 | 43.3 | -6.4 [-9.2, -3.5] |
| Qwen__Qwen3-4B-Instruct-2507/sample0.jsonl | 11817 | 29.6 | 34.8 | +5.3 [+4.6, +5.9] | 11517 | +5.3 [+4.7, +5.9] | 47.3 | 43.3 | -4.1 [-5.0, -3.1] |
| Qwen__Qwen3-4B-Thinking-2507__thinking/sample0.jsonl | 1500 | 55.3 | 65.5 | +10.2 [+8.1, +12.1] | 1200 | +11.1 [+8.9, +13.4] | 63.3 | 68.7 | +5.4 [+3.3, +7.7] |
| allenai__OLMo-2-1124-7B-Instruct/sample0.jsonl | 3998 | 19.1 | 18.1 | -1.0 [-2.0, -0.1] | 3698 | -1.1 [-2.0, -0.1] | 31.6 | 23.7 | -7.9 [-9.0, -6.5] |

| Run | A passes | A false rewards (replacement fails) | A missed rewards | B false gate passes | B false gate fails |
|---|---|---|---|---|---|
| Qwen__Qwen2.5-7B-Instruct/sample0.jsonl | 801 | 258 (32.2%) | 244 | 503 | 189 |
| Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl | 293 | 25 (8.5%) | 78 | 144 | 76 |
| Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl | 295 | 27 (9.2%) | 81 | 143 | 79 |
| Qwen__Qwen3-4B-Instruct-2507/sample0.jsonl | 3493 | 429 (12.3%) | 1051 | 1658 | 1182 |
| Qwen__Qwen3-4B-Thinking-2507__thinking/sample0.jsonl | 830 | 52 (6.3%) | 205 | 104 | 185 |
| allenai__OLMo-2-1124-7B-Instruct/sample0.jsonl | 763 | 195 (25.6%) | 155 | 507 | 195 |

Unsatisfiable nth-paragraph rows: 77 rows; 161 panel responses; grader A's row reward differs across 10 gradings of the same response for 23; at least one of the 10 gives reward 1.0 for 23.

Thinking run: 139 of 1500 responses never close their reasoning; grader A row reward 1.0 on 1, grader B gate passed on 18; constraint passes by A on these: 84 of 350.
Non-reasoning responses with a literal opening marker: 22; graded as empty by A and B; A reward 1.0 on 8; replacement (whole text) reward 1.0 on 0.
Grader B deterministic coverage: 25680 of 28219 constraints get a check; 2539 go to the LLM judge; 94 rows have no deterministic constraint.

| Check | Panel verdicts | A pass % | B pass % | Replacement pass % | A ≠ replacement: finding / decision / error | B ≠ replacement: finding / decision |
|---|---|---|---|---|---|---|
| `change_case:capital_word_frequency` | 1207 | 76 | 80 | 75 | 0 / 21 / 0 | 20 / 81 |
| `change_case:english_capital` | 1534 | 45 | 55 | 48 | 77 / 31 / 0 | 0 / 106 |
| `change_case:english_lowercase` | 1208 | 69 | 77 | 67 | 2 / 25 / 0 | 2 / 127 |
| `combination:two_responses` | 557 | 82 | 82 | 76 | 0 / 30 / 0 | 0 / 30 |
| `copy:repeat_phrase` | 1059 | 9 | 46 | 4 | 57 / 2 / 0 | 485 / 39 |
| `count:count_unique` | 1341 | 15 | judge | 22 | 99 / 14 / 0 | – |
| `count:counting_composition` | 1 | 0 | 0 | 0 | 0 / 0 / 0 | 0 / 0 |
| `count:lowercase_counting` | 1712 | 15 | 88 | 27 | 63 / 293 / 0 | 1219 / 106 |
| `detectable_content:number_placeholders` | 1201 | 92 | 91 | 91 | 1 / 1 / 0 | 1 / 0 |
| `detectable_content:postscript` | 1277 | 83 | 72 | 76 | 61 / 206 / 0 | 3 / 237 |
| `detectable_format:bigram_wrapping` | 1157 | 19 | judge | 3 | 183 / 4 / 0 | – |
| `detectable_format:constrained_response` | 243 | 90 | 58 | 58 | 3 / 75 / 0 | 0 / 0 |
| `detectable_format:json_format` | 266 | 82 | 82 | 82 | 0 / 0 / 0 | 0 / 0 |
| `detectable_format:multiple_sections` | 917 | 87 | 85 | 82 | 44 / 46 / 0 | 39 / 2 |
| `detectable_format:number_bullet_lists` | 1019 | 80 | 82 | 81 | 22 / 0 / 0 | 3 / 0 |
| `detectable_format:number_highlighted_sections` | 1070 | 93 | 93 | 90 | 34 / 0 / 0 | 32 / 0 |
| `detectable_format:sentence_hyphens` | 1300 | 20 | 19 | 82 | 16 / 815 / 0 | 3 / 816 |
| `detectable_format:square_brackets` | 1079 | 16 | 95 | 14 | 73 / 19 / 0 | 724 / 144 |
| `detectable_format:title` | 1189 | 97 | 97 | 97 | 2 / 0 / 0 | 2 / 0 |
| `first_word:first_word_answer` | 1089 | 72 | 85 | 85 | 114 / 22 / 0 | 7 / 0 |
| `first_word:first_word_sent` | 1024 | 32 | 43 | 41 | 80 / 36 / 0 | 19 / 17 |
| `keywords:existence` | 1856 | 76 | 72 | 72 | 0 / 65 / 0 | 1 / 0 |
| `keywords:forbidden_words` | 1687 | 97 | 97 | 97 | 1 / 0 / 0 | 1 / 0 |
| `keywords:frequency` | 1200 | 81 | 81 | 81 | 0 / 45 / 0 | 0 / 0 |
| `keywords:keyword_specific_position` | 1341 | 3 | 4 | 4 | 13 / 12 / 0 | 9 / 8 |
| `keywords:letter_frequency` | 1507 | 57 | 57 | 56 | 0 / 0 / 0 | 0 / 0 |
| `keywords:no_adjacent_consecutive` | 1499 | 24 | 77 | 24 | 162 / 59 / 0 | 870 / 52 |
| `keywords:palindrome` | 1165 | 90 | 63 | 75 | 45 / 210 / 0 | 145 / 7 |
| `keywords:start_end` | 989 | 30 | 37 | 34 | 14 / 44 / 0 | 65 / 14 |
| `keywords:word_count_different_numbers` | 1015 | 54 | 54 | 37 | 263 / 227 / 0 | 262 / 226 |
| `keywords:word_once` | 1808 | 25 | 26 | 74 | 819 / 123 / 0 | 782 / 82 |
| `language:response_language` | 1600 | 88 | judge | 84 | 8 / 79 / 0 | – |
| `last_word:last_word_answer` | 1285 | 70 | 76 | 75 | 0 / 68 / 1 | 14 / 2 |
| `last_word:last_word_sent` | 1203 | 28 | 33 | 27 | 28 / 51 / 0 | 48 / 40 |
| `length_constraints:nth_paragraph_first_word` | 1048 | 39 | 38 | 38 | 17 / 3 / 0 | 4 / 0 |
| `length_constraints:number_paragraphs` | 1345 | 74 | 42 | 63 | 81 / 108 / 0 | 480 / 12 |
| `length_constraints:number_sentences` | 1131 | 70 | 70 | 73 | 71 / 72 / 0 | 87 / 71 |
| `length_constraints:number_words` | 1443 | 74 | 70 | 74 | 4 / 40 / 0 | 59 / 32 |
| `letters:letter_counting` | 961 | 62 | judge | 66 | 0 / 97 / 0 | – |
| `letters:letter_counting2` | 1346 | 55 | 55 | 54 | 1 / 0 / 0 | 1 / 0 |
| `paragraphs:paragraphs` | 1150 | 83 | 97 | 72 | 104 / 32 / 0 | 240 / 40 |
| `paragraphs:paragraphs2` | 1391 | 62 | 94 | 63 | 0 / 5 / 0 | 435 / 2 |
| `punctuation:no_comma` | 1523 | 89 | 89 | 87 | 0 / 27 / 0 | 0 / 27 |
| `punctuation:punctuation_dot` | 1749 | 52 | 52 | 48 | 0 / 55 / 0 | 0 / 55 |
| `punctuation:punctuation_exclamation` | 1284 | 95 | 95 | 95 | 0 / 9 / 0 | 0 / 9 |
| `startend:end_checker` | 997 | 87 | 68 | 84 | 0 / 29 / 0 | 0 / 161 |
| `startend:quotation` | 810 | 86 | 86 | 86 | 0 / 1 / 0 | 0 / 0 |
