"""Hand-written fixtures, labeled from audit/CONTRACTS.md alone (proposed readings).

Each entry: (instruction_id, kwargs, response, label, decisions). `decisions` lists the decision
entries whose proposed reading the label depends on; an empty list means the label holds under
every reading the contract allows. The fixture id is the check family plus the first 16 hex digits
of sha256(instruction_id, kwargs, response).
"""

import hashlib
import json

P, F = "pass", "fail"
CAPF = "change_case:capital_word_frequency"
LOW = "count:lowercase_counting"

RAW = [
    # change_case:capital_word_frequency
    (CAPF, {"capital_frequency": 3, "capital_relation": "at least"}, "NASA and the FBI met in DC today.", P, []),
    (CAPF, {"capital_frequency": 4, "capital_relation": "at least"}, "NASA and the FBI met in DC today.", F, []),
    (CAPF, {"capital_frequency": 2, "capital_relation": "at least"}, "I think NASA is great.", P, ["D-capital-single-letter"]),
    (CAPF, {"capital_frequency": 2, "capital_relation": "less than"}, "The USA is big.", P, []),
    (CAPF, {"capital_frequency": 1, "capital_relation": "less than"}, "Hello, WORLD and USA.", F, []),
    # change_case:english_capital
    ("change_case:english_capital", None, "YES, I CAN HELP YOU WITH THAT. HERE IS THE ANSWER IN CAPITAL LETTERS.", P, []),
    ("change_case:english_capital", None, "This is my answer.", F, []),
    ("change_case:english_capital", None, "THIS IS MY ANSWER. thanks", F, []),
    ("change_case:english_capital", None, "DAS IST MEINE ANTWORT UND SIE IST AUF DEUTSCH GESCHRIEBEN WORDEN.", F, ["D-english-part"]),
    ("change_case:english_capital", None, "", F, []),
    ("change_case:english_capital", None, "HELLO WORLD", P, []),
    ("change_case:english_capital", None, "OKAY.", P, []),
    # change_case:english_lowercase
    ("change_case:english_lowercase", None, "this is my answer in english, and it is all in lowercase letters.", P, []),
    ("change_case:english_lowercase", None, "This is my answer.", F, []),
    ("change_case:english_lowercase", None, "this is my answer about NASA.", F, []),
    ("change_case:english_lowercase", None, "das ist meine antwort und sie ist auf deutsch klein geschrieben worden.", F, ["D-english-part"]),
    # combination:two_responses
    ("combination:two_responses", None, "First answer: use a map.\n******\nSecond answer: ask a local.", P, []),
    ("combination:two_responses", None, "Use a map. Or ask a local.", F, []),
    ("combination:two_responses", None, "Use a map.\n******\nUse a map.", F, []),
    ("combination:two_responses", None, "A map.\n******\nA local.\n******\nA guide.", F, []),
    ("combination:two_responses", None, "Use a map.\n*******\nAsk a local.", F, []),
    # copy:repeat_phrase
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each moment to the fullest. Live each week to the fullest.", P, []),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each day to the fullest. Live each day to the fullest.", F, ["D-repeat-original"]),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each moment to the fullest.", F, []),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each moment to the fullest. Live each week to the fullest. Live each hour to the fullest.", F, []),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live every moment to the fullest. Live each week to the fullest.", F, []),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "live each moment to the fullest. LIVE EACH WEEK TO THE FULLEST.", P, []),
    ("copy:repeat_phrase", {"phrase": "The early bird catches the worm", "small_n": 2},
     "The early bird gets the worm. The early fox catches the worm. Then the dog ate the worm.", P, []),
    ("copy:repeat_phrase", {"phrase": "Live each day to the fullest", "small_n": 2},
     "Live each day to the fullest. Live each week to the fullest.", F, ["D-repeat-original"]),
    # count:count_unique
    ("count:count_unique", None, "Every word here appears once.", P, []),
    ("count:count_unique", None, "I saw a cat and a dog.", F, []),
    ("count:count_unique", None, "Red, green, blue, yellow.", P, []),
    ("count:count_unique", None, "The cat chased the dog", F, ["D-unique-case"]),
    # count:counting_composition
    ("count:counting_composition", {"n_sent": 3, "n_words": 2},
     "Birds sing. Rivers flow. Stars shine.\n* * *\nCats sleep. Dogs bark. Kids play.\n* * *\nWinds blow. Trees sway. Leaves fall.", P, []),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2},
     "Birds sing. Rivers flow. Stars shine.\n***\nCats sleep. Dogs bark. Kids play.\n***\nWinds blow. Trees sway. Leaves fall.", P, ["D-divider-form"]),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2},
     "Birds sing. Rivers flow. Stars shine.\n* * *\nCats sleep. Dogs bark. Kids play.", F, []),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2},
     "Birds sing loudly. Rivers flow. Stars shine.\n* * *\nCats sleep. Dogs bark. Kids play.\n* * *\nWinds blow. Trees sway. Leaves fall.", F, []),
    # count:lowercase_counting
    (LOW, {"N": 2}, "Apples are red and bananas are yellow.", P, ["D-lowercase-scope"]),
    (LOW, {"N": 2}, "the cat and the dog and the bird", F, []),
    (LOW, {"N": 2}, "The cat, the dog, the bird.", P, ["D-lowercase-count", "D-lowercase-scope"]),
    (LOW, {"N": 3}, "Apples are red.", P, []),
    (LOW, {"N": 2}, "Apples are red and green.", P, ["D-lowercase-scope"]),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], your order ships to [address].", P, []),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], thanks.", F, []),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [], see [ ].", F, []),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "See [the docs](http://x.y) and [name].", P, ["D-placeholder-kind"]),
    # detectable_content:postscript
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main text here.\n\nP.S. Remember to drink water.", P, []),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main text here. Nothing else.", F, []),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main text.\n\nP.P.S. Extra note.", F, []),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main text.\n\nP.S: one more thing.", P, []),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main text.\n\n**P.S.** One more thing.", P, []),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "P.S. Note first.\n\nThen the main text continues here.", F, ["D-postscript-end"]),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "main text.\n\np.s. one more thing.", P, ["D-postscript-case"]),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main text.\n\nP.S. First note.\n\nP.P.S. Second note.", P, []),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main text.\n\nP.S. Only one note.", F, []),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main text.\n\nP.P.S Remember this.", P, []),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> <<with my>> <<cute dog>>", P, []),
    ("detectable_format:bigram_wrapping", None, "I am at home with my cute dog.", F, []),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> with my <<cute dog>>", F, []),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> <<today>>", P, ["D-bigram-odd"]),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>>.", P, []),
    ("detectable_format:bigram_wrapping", None, "<<I am at>> <<home now>>", F, []),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", None, "My answer is yes.", P, []),
    ("detectable_format:constrained_response", None, "My answer is no. The data does not support it.", P, ["D-constrained-exact"]),
    ("detectable_format:constrained_response", None, "Yes.", F, []),
    ("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", F, []),
    ("detectable_format:constrained_response", None, "**My answer is maybe.**", P, []),
    # detectable_format:json_format
    ("detectable_format:json_format", None, '{"answer": 42}', P, []),
    ("detectable_format:json_format", None, '```json\n{"answer": 42}\n```', P, []),
    ("detectable_format:json_format", None, 'Here is the JSON: {"answer": 42}', F, []),
    ("detectable_format:json_format", None, '{"answer": 42,}', F, []),
    ("detectable_format:json_format", None, '```json\n{"a": 1}\n```\nHope this helps.', F, []),
    ("detectable_format:json_format", None, '"hello"', P, ["D-json-toplevel"]),
    ("detectable_format:json_format", None, '```JSON\n{"a": 1}\n```', P, []),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", P, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nA.\nSECTION 2\nB.\nSECTION 3\nC.", F, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nIntro text, as noted in SECTION 2 below.\nSECTION 2\nMore text.", P, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "## SECTION 1\nText one.\n## SECTION 2\nText two.", P, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "Section"}, "SECTION 1\nText one.\nSECTION 2\nText two.", P, ["D-sections-case"]),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "Here you go.\nSECTION 1\nA.\nSECTION 2\nB.", P, ["D-sections-preamble"]),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nSECTION 2\nText.", F, []),
    ("detectable_format:multiple_sections", {"num_sections": 1, "section_spliter": "Section"}, "Section 1\nAll text. See Section 2 of the law.", P, []),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* First point.\n* Second point.", P, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "- First point.\n- Second point.", P, ["D-bullet-marker"]),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* First.\n* Second.\n* Third.", F, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* First point.\n* Second point.\n\n---\n\nThanks.", P, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* First.\n* Second.\n* * *\nEnd.", P, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "*Note:* this is italic.\n* First.\n* Second.", P, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "1. First\n2. Second", F, []),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* A\n  * a1\n* B", P, ["D-bullet-nested"]),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* First point.\n* Second point.\n-5 degrees is cold.", P, []),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* and *urgent*.", P, []),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* only.", F, []),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is **important** and **urgent**.", P, ["D-highlight-bold"]),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "* item one\n* item two", F, []),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Compute 2 * 3 * 4 now.", F, []),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", None, "I like tea.-It is warm.-It calms me.", P, []),
    ("detectable_format:sentence_hyphens", None, "I like tea. It is warm.", F, []),
    ("detectable_format:sentence_hyphens", None, "I like tea. - It is warm.", F, []),
    ("detectable_format:sentence_hyphens", None, "My well-known recipe works.-It is quick.", P, []),
    ("detectable_format:sentence_hyphens", None, "I like tea.", P, []),
    ("detectable_format:sentence_hyphens", None, "I like tea.-It is warm.\nIt calms me.", F, []),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", None, "[I] [like] [tea].", P, []),
    ("detectable_format:square_brackets", None, "[I] [like] [tea]", P, []),
    ("detectable_format:square_brackets", None, "[I] like [tea]", F, []),
    ("detectable_format:square_brackets", None, "[I like tea]", F, ["D-bracket-group"]),
    ("detectable_format:square_brackets", None, "[Hello], [world]!", P, []),
    # detectable_format:title
    ("detectable_format:title", None, "<<My Day>>\nIt was fine.", P, []),
    ("detectable_format:title", None, "Here is a poem.\n<<Ode to Rain>>\nDrops fall.", P, ["D-title-position"]),
    ("detectable_format:title", None, "My Day\nIt was fine.", F, []),
    ("detectable_format:title", None, "<< >> text", F, []),
    ("detectable_format:title", None, "<<My\nDay>> text", F, []),
    # first_word:first_word_answer
    ("first_word:first_word_answer", {"first_word": "development"}, "Development of the city was slow.", P, []),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development**: the city grew slowly.", P, []),
    ("first_word:first_word_answer", {"first_word": "development"}, "Development, as a process, is slow.", P, []),
    ("first_word:first_word_answer", {"first_word": "development"}, "The development was slow.", F, []),
    ("first_word:first_word_answer", {"first_word": "development"}, "Developments were slow.", F, []),
    # first_word:first_word_sent
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good. Peace is calm.", P, []),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace, friends, is good. Peace matters!", P, []),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good. War is bad.", F, []),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good\nPeace is calm", P, []),
    # keywords:existence
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "This quote is about teaching.", P, []),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "QUOTE: Teaching matters.", P, []),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "This quote is nice.", F, []),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "These quotes are about teachings.", F, ["D-keyword-boundary"]),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "A teaching-focused quote.", P, []),
    # keywords:forbidden_words
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "The circle was quiet.", P, []),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "The square was quiet.", F, []),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "SOUND is loud.", F, []),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "The sounds were soundtrack-like.", P, ["D-keyword-boundary"]),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "A sound-proof room.", F, []),
    # keywords:frequency
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "The monitor is big. I like this monitor.", P, []),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "The monitor is big.", F, []),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "The monitors are big. I like this monitor.", F, ["D-keyword-boundary"]),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "less than"}, "One monitor.", P, []),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "less than"}, "Monitor, monitor.", F, []),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", {"keyword": "shot", "n": 2, "m": 3}, "I tried hard. It was shot down quickly.", P, []),
    ("keywords:keyword_specific_position", {"keyword": "shot", "n": 2, "m": 3}, "I tried hard. It was not shot.", F, []),
    ("keywords:keyword_specific_position", {"keyword": "shot", "n": 2, "m": 3}, "I tried hard. Then a Shot rang out.", P, []),
    ("keywords:keyword_specific_position", {"keyword": "shot", "n": 2, "m": 3}, "I tried hard. Well, a shot rang out.", P, []),
    ("keywords:keyword_specific_position", {"keyword": "shot", "n": 2, "m": 3}, "It was shot down quickly.", F, []),
    # keywords:letter_frequency
    ("keywords:letter_frequency", {"letter": "r", "let_frequency": 3, "let_relation": "at least"}, "Rare red roses.", P, []),
    ("keywords:letter_frequency", {"letter": "r", "let_frequency": 3, "let_relation": "at least"}, "Blue skies.", F, []),
    ("keywords:letter_frequency", {"letter": "r", "let_frequency": 3, "let_relation": "at least"}, "RRR", P, ["D-letter-case"]),
    ("keywords:letter_frequency", {"letter": "r", "let_frequency": 3, "let_relation": "less than"}, "rr", P, []),
    ("keywords:letter_frequency", {"letter": "r", "let_frequency": 3, "let_relation": "less than"}, "rrr", F, []),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", None, "The cat sat on the mat.", P, []),
    ("keywords:no_adjacent_consecutive", None, "A big dog.", F, []),
    ("keywords:no_adjacent_consecutive", None, "Big apple pie.", F, ["D-consecutive-order"]),
    ("keywords:no_adjacent_consecutive", None, "Room 1 2 3 was open.", P, []),
    ("keywords:no_adjacent_consecutive", None, "Cats * + run.", P, []),
    ("keywords:no_adjacent_consecutive", None, "The cat. Dog runs.", F, []),
    ("keywords:no_adjacent_consecutive", None, "We met at noon.", P, []),
    # keywords:palindrome
    ("keywords:palindrome", None, "We saw a racecar today.", P, []),
    ("keywords:palindrome", None, "Wow, that was fun.", P, []),
    ("keywords:palindrome", None, "We saw a car today.", F, ["D-palindrome-length"]),
    ("keywords:palindrome", None, "Nothing here matches.", F, []),
    ("keywords:palindrome", None, "- item one\n- item two", F, []),
    ("keywords:palindrome", None, "Level 1 complete.", P, []),
    # keywords:start_end
    ("keywords:start_end", None, "Hello there my friend hello", P, []),
    ("keywords:start_end", None, "Hello there my friend hello.", F, []),
    ("keywords:start_end", None, "Hello there my friend.", F, []),
    ("keywords:start_end", None, "**Hello** there my friend hello", P, []),
    ("keywords:start_end", None, "Hello", P, ["D-start-end-one-word"]),
    ("keywords:start_end", None, "Data matters. We trust data", P, []),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "less than"}, "Skin care matters. Protect your skin.", P, []),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "less than"}, "Skin care matters.", F, []),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "at least"}, "Skin, skin, skin.", F, ["D-appear-n-times"]),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 1, "relation": "less than"}, "No mention here.", F, []),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "at least"}, "Skin care matters. Protect your skin.", P, []),
    # keywords:word_once
    ("keywords:word_once", {"keyword": "fix"}, "I will fix it.", P, []),
    ("keywords:word_once", {"keyword": "fix"}, "Fix it now, then fix it again.", P, []),
    ("keywords:word_once", {"keyword": "fix"}, "I will repair it.", F, []),
    ("keywords:word_once", {"keyword": "fix"}, "The prefix changed.", F, ["D-keyword-boundary"]),
    # language:response_language
    ("language:response_language", {"language": "fr"}, "Bonjour, je suis heureux de vous aider avec cette question aujourd'hui.", P, []),
    ("language:response_language", {"language": "fr"}, "Hello, I am happy to help you with this question today.", F, []),
    ("language:response_language", {"language": "fr"}, "", F, []),
    ("language:response_language", {"language": "ru"}, "Привет, я рад помочь вам с этим вопросом сегодня.", P, []),
    ("language:response_language", {"language": "ru"}, "Привет! Я использую Python и NumPy для анализа данных каждый день.", P, ["D-language-mixed"]),
    # last_word:last_word_answer
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the limit.", P, []),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the **limit**!", P, []),
    ("last_word:last_word_answer", {"last_word": "limit"}, "The limit was reached.", F, []),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the limits.", F, []),
    ("last_word:last_word_answer", {"last_word": "limit"}, "", F, []),
    # last_word:last_word_sent
    ("last_word:last_word_sent", {"last_word": "train"}, "I took the train. She missed the train!", P, []),
    ("last_word:last_word_sent", {"last_word": "train"}, "I took the train. She walked home.", F, []),
    ("last_word:last_word_sent", {"last_word": "train"}, "I took the train, the train.", P, []),
    ("last_word:last_word_sent", {"last_word": "train"}, "Travel Notes\nI took the train.", F, ["D-sentence"]),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro paragraph.\n\nCrash tests matter.\n\nConclusion here.", P, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\n**Crash** tests matter.\n\nEnd.", P, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nCrash: tests matter.\n\nEnd.", P, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nCrash tests matter.", F, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nTests matter.\n\nCrash end.", F, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\n\nCrash tests.\n\n\nEnd.", P, ["D-blank-run"]),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 4, "first_word": "crash"}, "A.\n\nB.\n\nCrash.", F, []),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 4, "first_word": "crash"}, "A.\n\nB.\n\nC.\n\nCrash.", F, []),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n***\nSecond.\n***\nThird.", P, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n\n***\n\nSecond.\n\n***\n\nThird.", P, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n* * *\nSecond.\n* * *\nThird.", P, ["D-divider-form"]),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n\nSecond.\n\nThird.", F, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n***\nSecond.", F, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First ***note*** here.\n***\nSecond.\n***\nThird.", P, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.\n***\nSecond.\n***\nThird.\n***", F, ["D-divider-empty"]),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One is here. Two is here. Three is here.", P, []),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One is here. Two is here.", F, []),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "less than"}, "Dr. Smith came. He left. We stayed.", F, []),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "less than"}, "One is here. Two is here.", P, []),
    # length_constraints:number_words
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "This sentence has five words.", P, []),
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "Only four words here.", F, []),
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "Привет как у тебя дела", P, []),
    ("length_constraints:number_words", {"num_words": 5, "relation": "less than"}, "I don't like it", P, []),
    ("length_constraints:number_words", {"num_words": 4, "relation": "less than"}, "Café crème brûlée", P, []),
    # letters:letter_counting
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "Ok", P, []),
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "Okay", F, ["D-letters-unit"]),
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "Привет", F, ["D-letters-unit"]),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Hi!", F, []),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Hey", P, ["D-letters-unit"]),
    # letters:letter_counting2
    ("letters:letter_counting2", {"letter": "o", "let_frequency": 2, "let_relation": "at least"}, "Good food.", P, []),
    ("letters:letter_counting2", {"letter": "o", "let_frequency": 2, "let_relation": "at least"}, "Fine day.", F, []),
    ("letters:letter_counting2", {"letter": "o", "let_frequency": 1, "let_relation": "at least"}, "One apple.", P, ["D-letter-case"]),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", {}, "First paragraph.\n***\nSecond paragraph.", P, []),
    ("paragraphs:paragraphs", {}, "First.\n***\nSecond.\n***\nThird.", F, []),
    ("paragraphs:paragraphs", {}, "First.\n\nSecond.", F, []),
    ("paragraphs:paragraphs", {}, "First ***bold*** words here.\n***\nSecond.", P, []),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", {}, "First paragraph.\n\nSecond paragraph.", P, []),
    ("paragraphs:paragraphs2", {}, "One.\n\nTwo.\n\nThree.", F, []),
    ("paragraphs:paragraphs2", {}, "Only one paragraph.", F, []),
    ("paragraphs:paragraphs2", {}, "First line\nstill first.\n\nSecond.", P, []),
    ("paragraphs:paragraphs2", {}, "First.\n***\nSecond.", F, []),
    # punctuation:no_comma
    ("punctuation:no_comma", None, "No commas here.", P, []),
    ("punctuation:no_comma", None, "Yes, there is one.", F, []),
    ("punctuation:no_comma", None, "这是，中文", F, ["D-comma-chars"]),
    # punctuation:punctuation_dot
    ("punctuation:punctuation_dot", None, "No dots here!", P, []),
    ("punctuation:punctuation_dot", None, "Version 2.0 is out", F, []),
    ("punctuation:punctuation_dot", None, "这是中文。", F, ["D-dot-chars"]),
    # punctuation:punctuation_exclamation
    ("punctuation:punctuation_exclamation", None, "Calm text.", P, []),
    ("punctuation:punctuation_exclamation", None, "Wow!", F, []),
    ("punctuation:punctuation_exclamation", None, "太好了！", F, ["D-excl-chars"]),
    # startend:end_checker
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "Here it is. Is there anything else I can help with?", P, []),
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "Here it is. Is there anything else I can help with?\n", P, []),
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "Here it is. **Is there anything else I can help with?**", P, ["D-end-trailing"]),
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "Is there anything else I can help with? Thanks.", F, []),
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "here it is. is there anything else i can help with?", F, ["D-end-case"]),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, '"Here it is. Any other questions?"', P, ["D-end-trailing"]),
    # startend:quotation
    ("startend:quotation", None, '"Hello there."', P, []),
    ("startend:quotation", None, "Hello there.", F, []),
    ("startend:quotation", None, "“Hello there.”", P, ["D-quote-chars"]),
    ("startend:quotation", None, "'Hello there.'", F, []),
    ("startend:quotation", None, '"', F, []),
    # added after the development panel review (labels from the contract; see ISSUE.md)
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, '"SECTION 1\nText one.\nSECTION 2\nText two."', P, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nText one. SECTION 2\nText two.", P, []),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "这是*重点*和*关键*。", P, []),
    ("detectable_format:square_brackets", None, "[J][u][s][t] [g][o]", F, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.***\n\nSecond.***\n\nThird.", P, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph here. *** Second paragraph here.", P, []),
    ("combination:two_responses", None, "Answer one.\n******\nAnswer two.\n******", F, ["D-two-responses-edge"]),
    ("keywords:no_adjacent_consecutive", None, "Я вижу город.", P, ["D-consecutive-script"]),
    (LOW, {"N": 2}, "这是 这是 这是 测试", P, []),
    (LOW, {"N": 2}, "мы мы мы идём", F, []),
    ("keywords:palindrome", None, "A man, a plan, a canal, Panama.", P, []),
    ("keywords:palindrome", None, "Noon is lunch time.", P, []),
    ("detectable_format:sentence_hyphens", None, "I like tea - it is warm - it calms me", F, []),
    ("detectable_format:sentence_hyphens", None, "CAN-DO-USED-IN-THE-BUILDING", P, []),
    ("change_case:english_capital", None, "THIS IS ENGLISH TEXT FOR YOU AND IT IS LONG ENOUGH TO READ.\n\n这是一个完整的中文段落。", F, ["D-english-part"]),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Привет мир друзья", P, []),
]


def fixture_id(iid, kwargs, response):
    h = hashlib.sha256(json.dumps([iid, kwargs, response], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return iid.split(":")[1] + ":" + h[:16]


FIXTURES = [
    {"id": fixture_id(i, k, s), "instruction_id": i, "kwargs": k, "response": s, "label": lab, "decisions": d}
    for (i, k, s, lab, d) in RAW
]
assert len({f["id"] for f in FIXTURES}) == len(FIXTURES), "duplicate fixture"
