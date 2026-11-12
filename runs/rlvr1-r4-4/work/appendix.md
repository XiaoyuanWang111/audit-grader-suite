
## Appendix: per-check panel table

From `audit/work/analyze_all.out` (whole panel). Columns: verdicts; pass % of A, B, R (proposed
readings); for A and for B: disagreements with R, split into (unexplained grader passes /
unexplained grader fails, decision-explained); A exceptions. B is not run on the four judged ids.
Extraction failures (F-G1) are counted in the verdicts but not in the disagreements.

```text
per check: n, pass% A B R | A vs R: disagree (unexplained pass/fail, decision) | B vs R: same | A_err
change_case:capital_word_frequency              1207  75.7  78.7  75.5 | A   21 (   8/   3,   10) | B  101 (   2/  19,   80) | 0
change_case:english_capital                     1534  45.1  55.0  51.7 | A  129 (   0/ 115,   14) | B   67 (   0/   8,   59) | 0
change_case:english_lowercase                   1208  69.0  77.4  69.8 | A   18 (   0/  14,    4) | B  126 (   0/  17,  109) | 0
combination:two_responses                        557  81.3  81.3  75.9 | A   30 (   1/   0,   29) | B   30 (   1/   0,   29) | 0
copy:repeat_phrase                              1059   8.9  45.0   4.4 | A   59 (   3/   5,   51) | B  524 ( 247/  32,  245) | 0
count:count_unique                              1341  15.0  80.7  22.3 | A  114 (   0/ 106,    8) | B    0 (   0/   0,    0) | 0
count:counting_composition                         1   0.0   0.0   0.0 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
count:lowercase_counting                        1712  15.2  87.6  29.5 | A  326 (  39/  10,  277) | B 1339 (1150/ 160,   29) | 0
detectable_content:number_placeholders          1201  90.9  90.8  90.9 | A    2 (   1/   1,    0) | B    1 (   0/   1,    0) | 0
detectable_content:postscript                   1277  82.7  71.8  74.4 | A  292 ( 128/  93,   71) | B  163 (   0/  97,   66) | 0
detectable_format:bigram_wrapping               1157  19.4   2.1   3.4 | A  185 ( 182/   0,    3) | B    0 (   0/   0,    0) | 0
detectable_format:constrained_response           243  89.7  57.6  88.5 | A    3 (   3/   0,    0) | B   75 (   0/   0,   75) | 0
detectable_format:json_format                    266  82.0  82.0  82.0 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
detectable_format:multiple_sections              917  86.3  85.1  85.2 | A   60 (  35/   2,   23) | B   13 (   6/   5,    2) | 0
detectable_format:number_bullet_lists           1019  80.1  81.6  81.6 | A   21 (   3/  18,    0) | B    0 (   0/   0,    0) | 0
detectable_format:number_highlighted_sections   1070  93.2  93.2  93.0 | A   10 (   6/   1,    3) | B    8 (   5/   0,    3) | 0
detectable_format:sentence_hyphens              1300  19.6  19.5  56.2 | A  590 (  57/ 533,    0) | B  482 (   2/ 480,    0) | 0
detectable_format:square_brackets               1079  16.2  94.4  17.7 | A   98 (  20/  57,   21) | B  844 ( 667/   8,  169) | 0
detectable_format:title                         1189  96.4  96.4  96.6 | A    2 (   0/   2,    0) | B    2 (   0/   2,    0) | 0
first_word:first_word_answer                    1089  72.2  85.1  84.7 | A  136 (   0/ 133,    3) | B    7 (   6/   1,    0) | 0
first_word:first_word_sent                      1024  32.3  43.3  41.4 | A  115 (   0/ 101,   14) | B   35 (  12/   8,   15) | 0
keywords:existence                              1856  75.4  71.9  71.9 | A   66 (   0/   0,   66) | B    0 (   0/   0,    0) | 0
keywords:forbidden_words                        1687  96.6  96.6  96.6 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
keywords:frequency                              1200  80.8  80.7  80.7 | A   45 (   0/   0,   45) | B    0 (   0/   0,    0) | 0
keywords:keyword_specific_position              1341   2.8   3.7   3.7 | A   24 (   3/  14,    7) | B   16 (   4/   4,    8) | 0
keywords:letter_frequency                       1507  56.5  56.5  56.5 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
keywords:no_adjacent_consecutive                1499  23.7  76.8  23.8 | A  221 (  53/   0,  168) | B  922 ( 810/  29,   83) | 0
keywords:palindrome                             1165  90.0  63.1  73.6 | A  264 (   8/  37,  219) | B  143 (   2/ 133,    8) | 0
keywords:start_end                               989  29.5  37.1  34.2 | A   54 (   3/   1,   50) | B   83 (  54/   9,   20) | 0
keywords:word_count_different_numbers           1015  54.0  54.0  36.6 | A  489 ( 144/ 145,  200) | B  489 ( 144/ 145,  200) | 0
keywords:word_once                              1808  25.5  25.9  73.5 | A  944 (   0/ 906,   38) | B  862 (   0/ 861,    1) | 0
language:response_language                      1600  88.2  82.9  79.9 | A  142 ( 137/   3,    2) | B    0 (   0/   0,    0) | 0
last_word:last_word_answer                      1285  69.7  76.0  74.9 | A   67 (   0/   3,   64) | B   15 (  14/   1,    0) | 1
last_word:last_word_sent                        1203  27.8  33.3  27.3 | A   79 (   9/  16,   54) | B   80 (  34/   2,   44) | 0
length_constraints:nth_paragraph_first_word     1048  39.4  38.4  38.0 | A   25 (  19/   4,    2) | B    4 (   4/   0,    0) | 0
length_constraints:number_paragraphs            1345  74.1  42.4  63.7 | A  142 (   1/   1,  140) | B  491 (  57/ 370,   64) | 0
length_constraints:number_sentences             1131  70.1  69.3  70.6 | A   93 (   4/  14,   75) | B  108 (   8/  26,   74) | 0
length_constraints:number_words                 1443  73.3  70.1  73.5 | A   25 (  10/  12,    3) | B   70 (  11/  55,    4) | 0
letters:letter_counting                          961  61.2  65.6  66.2 | A   96 (  16/  55,   25) | B    0 (   0/   0,    0) | 0
letters:letter_counting2                        1346  53.9  53.9  53.8 | A    1 (   1/   0,    0) | B    1 (   1/   0,    0) | 0
paragraphs:paragraphs                           1150  83.5  96.7  80.2 | A   48 (   1/   0,   47) | B  190 ( 128/   0,   62) | 0
paragraphs:paragraphs2                          1391  62.5  94.0  62.5 | A    5 (   0/   0,    5) | B  437 ( 435/   0,    2) | 0
punctuation:no_comma                            1523  88.7  88.7  86.9 | A   27 (   0/   0,   27) | B   27 (   0/   0,   27) | 0
punctuation:punctuation_dot                     1749  51.6  51.6  48.5 | A   55 (   0/   0,   55) | B   55 (   0/   0,   55) | 0
punctuation:punctuation_exclamation             1284  95.3  95.3  94.6 | A    9 (   0/   0,    9) | B    9 (   0/   0,    9) | 0
startend:end_checker                             997  87.4  68.3  71.8 | A  169 (   0/   0,  169) | B   35 (   0/   0,   35) | 0
startend:quotation                               810  85.9  86.0  86.4 | A    4 (   0/   0,    4) | B    3 (   0/   0,    3) | 0
TOTAL {'n': 55783, 'A_disagree': 5305, 'A_unexplained': 3300, 'A_decision': 2005, 'B_disagree': 7857, 'B_unexplained': 6277, 'B_decision': 1580, 'A_err': 1}
```
