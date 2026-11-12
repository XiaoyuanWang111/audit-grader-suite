"""Hand-written fixtures, labeled from audit/CONTRACTS.md v2 alone.

Each entry: (instruction_id, kwargs, response, label, deps, note)
- label: "pass" or "fail" under the contract's proposed readings.
- deps: decision entries whose other reading would change the label (empty: unambiguous).
Pipeline fixtures (graded text extraction) are in PIPELINE: (instruction_id, kwargs, raw response,
thinking configuration?, label, deps, note).
"""

TF = {"phrase": "Time flies when having fun", "small_n": 2}
SEC2 = {"num_sections": 2, "section_spliter": "SECTION"}

FIXTURES = [
    # change_case:capital_word_frequency
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "at least"}, "NASA and the FBI met.", "pass", [], "two all-caps words"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "at least"}, "Nasa and the Fbi met.", "fail", [], "none"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "NASA and the FBI met.", "fail", [], "2 is not less than 2"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "I think NASA is great.", "fail", ["D-allcaps-short"], "I counts"),
    ("change_case:capital_word_frequency", {"capital_frequency": 1, "capital_relation": "at least"}, "ÉTÉ is a French word.", "pass", [], "accented all-caps word"),
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "at least"}, "WHO, UN, and EU agreed.", "pass", [], "three"),
    # change_case:english_capital
    ("change_case:english_capital", None, "THIS IS MY ANSWER. IT IS WRITTEN IN ENGLISH FOR THE READER.", "pass", [], ""),
    ("change_case:english_capital", None, "This is my answer in English for the reader.", "fail", [], "lowercase letters"),
    ("change_case:english_capital", None, "C'EST MA RÉPONSE EN FRANÇAIS. JE PARLE DE LA VILLE ET DE SES HABITANTS.", "fail", [], "all caps but French"),
    ("change_case:english_capital", None, "THIS IS MY ANSWER FOR THE READER, mostly.", "fail", [], "one lowercase word"),
    ("change_case:english_capital", None, "USE THE COMMAND `ls -la` TO LIST THE FILES IN THE CURRENT FOLDER.", "fail", ["D-case-scope"], "lowercase inside code"),
    ("change_case:english_capital", None, "", "fail", [], "empty: not in English"),
    # change_case:english_lowercase
    ("change_case:english_lowercase", None, "this is my answer. it is written in english and has no capital letters at all.", "pass", [], ""),
    ("change_case:english_lowercase", None, "This is my answer in english for the reader.", "fail", [], "one capital"),
    ("change_case:english_lowercase", None, "i went to Paris last year and loved the museums there.", "fail", [], "proper noun capital"),
    ("change_case:english_lowercase", None, "je suis allé à la plage avec mes amis hier soir et nous avons nagé.", "fail", [], "lowercase but French"),
    ("change_case:english_lowercase", None, "", "fail", [], "empty: not in English"),
    # combination:two_responses
    ("combination:two_responses", None, "Paris is the capital of France.\n******\nThe capital of France is Paris.", "pass", [], ""),
    ("combination:two_responses", None, "Paris is the capital.\n\nParis is the capital city.", "fail", [], "no separator"),
    ("combination:two_responses", None, "Paris.\n******\nParis.", "fail", [], "identical"),
    ("combination:two_responses", None, "A one.\n******\nB two.\n******\nC three.", "fail", [], "three responses"),
    ("combination:two_responses", None, "First answer here.\n*******\nSecond answer here.", "fail", ["D-two-sep"], "seven asterisks"),
    ("combination:two_responses", None, "Only one answer here.\n******", "fail", [], "empty second side"),
    # copy:repeat_phrase
    ("copy:repeat_phrase", TF, "Time flies while having fun. Time flies during having fun.", "pass", [], "two center variants"),
    ("copy:repeat_phrase", TF, "Time flies when having fun. Time flies when having fun.", "fail", [], "copies only"),
    ("copy:repeat_phrase", TF, "Time flies while having fun. Time flies during having fun. Time flies after having fun.", "fail", [], "three variants"),
    ("copy:repeat_phrase", TF, "Time flies when having fun. Time flies while having fun.", "fail", [], "one copy and one variant: not two transformed repetitions"),
    ("copy:repeat_phrase", TF, "time flies while having fun. time flies during having fun.", "pass", ["D-keyword-case"], "lowercase variants"),
    ("copy:repeat_phrase", TF, "Here are my variations:\nTime flies while having fun\nTime flies during having fun", "pass", [], "lines with an intro"),
    ("copy:repeat_phrase", TF, "Time goes while having fun. Time flies during having fun.", "fail", [], "first repetition changes two words"),
    ("copy:repeat_phrase", {"phrase": "Don't judge a book by cover", "small_n": 2}, "Don't judge a novel by cover. Don't judge a movie by cover.", "pass", [], ""),
    # count:count_unique
    ("count:count_unique", None, "Cats chase mice quickly.", "pass", [], ""),
    ("count:count_unique", None, "The cat saw the dog.", "fail", ["D-unique-case"], "The/the"),
    ("count:count_unique", None, "dog chases another dog", "fail", [], ""),
    ("count:count_unique", None, "I run. You walk. We swim.", "pass", [], "repeated periods are not words"),
    # count:counting_composition
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Cats purr. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs leap. Bees buzz.\n* * *\nSun shines. Rain falls. Wind blows.", "pass", [], ""),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Cats purr loudly. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs leap. Bees buzz.\n* * *\nSun shines. Rain falls. Wind blows.", "fail", [], "three words in one sentence"),
    # count:lowercase_counting
    ("count:lowercase_counting", {"N": 2}, "The Cat Sat On The Mat.", "pass", [], "no lowercase words"),
    ("count:lowercase_counting", {"N": 2}, "the cat and the dog", "pass", ["D-lowercase-scope"], "each lowercase word at most twice"),
    ("count:lowercase_counting", {"N": 2}, "the the the cat", "fail", [], "the three times"),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], your order ships to [address].", "pass", [], ""),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], thanks.", "fail", [], ""),
    ("detectable_content:number_placeholders", {"num_placeholders": 1}, "Use [] here.", "fail", [], "empty brackets"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "See [1] and [the docs](http://example.org).", "pass", ["D-placeholder"], ""),
    # detectable_content:postscript
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\nP.S. Thanks for reading.", "pass", [], ""),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer. Thanks for reading.", "fail", [], ""),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "P.S. Read this first.\n\nHere is the main answer in a long paragraph.", "fail", ["D-postscript-end"], "postscript at the start"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "My answer, as the P.S. below explains, is yes.", "fail", [], "marker inside a sentence"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main answer.\n\nP.P.S. Extra note.", "fail", [], "a P.P.S. is not a P.S."),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Main answer.\n\nP.S: thanks.", "pass", ["D-postscript-dot"], ""),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "main answer.\n\np.s. thanks.", "pass", ["D-postscript-case"], ""),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main answer.\n\nP.P.S Thanks again.", "pass", [], ""),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main answer.\n\n**P.P.S.** Thanks again.", "pass", [], "emphasis before the marker"),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> <<with my>> <<cute dog>>", "pass", [], ""),
    ("detectable_format:bigram_wrapping", None, "I am at home with my cute dog.", "fail", [], ""),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> with", "fail", [], "last word unwrapped"),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<home>>", "pass", ["D-bigram-odd"], "odd word count"),
    ("detectable_format:bigram_wrapping", None, "<<I>> <<am>> <<at>> <<home>>", "fail", [], "unigrams"),
    ("detectable_format:bigram_wrapping", None, "<<I am at>> <<home now>>", "fail", [], "trigram"),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", None, "My answer is yes.", "pass", [], ""),
    ("detectable_format:constrained_response", None, "  My answer is maybe.  ", "pass", [], ""),
    ("detectable_format:constrained_response", None, "My answer is yes. Because the data supports it.", "fail", ["D-constrained-extra"], ""),
    ("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", "fail", [], "two options"),
    ("detectable_format:constrained_response", None, "Yes.", "fail", [], ""),
    # detectable_format:json_format
    ("detectable_format:json_format", None, '{"a": 1}', "pass", [], ""),
    ("detectable_format:json_format", None, '```json\n{"a": 1}\n```', "pass", [], ""),
    ("detectable_format:json_format", None, '```JSON\n{"a": 1}\n```', "pass", [], "uppercase fence tag"),
    ("detectable_format:json_format", None, 'Here is the JSON:\n```json\n{"a": 1}\n```', "fail", [], "text outside"),
    ("detectable_format:json_format", None, '{"a": 1,}', "fail", [], ""),
    ("detectable_format:json_format", None, "NaN", "fail", [], "not JSON"),
    ("detectable_format:json_format", None, '"hello"', "pass", ["D-json-scalar"], ""),
    ("detectable_format:json_format", None, '{"a": 1}\n{"b": 2}', "fail", [], "two JSON texts"),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", SEC2, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", "pass", [], ""),
    ("detectable_format:multiple_sections", SEC2, "SECTION 1\nIntro text.\nSECTION 2\nMore text.\nSECTION 3\nEven more.", "fail", [], "three sections"),
    ("detectable_format:multiple_sections", SEC2, "SECTION 1\nIntro.\nSECTION 2\nAs noted in SECTION 1, more.", "pass", [], "mention inside a line"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "Section"}, "SECTION 1\nIntro.\nSECTION 2\nMore.", "fail", ["D-sections-case"], ""),
    ("detectable_format:multiple_sections", {"num_sections": 1, "section_spliter": "SECTION"}, "SECTION 1\nAll content here.", "pass", [], ""),
    ("detectable_format:multiple_sections", SEC2, "SECTION 1\nIntro.\nSECTION 3\nMore.", "fail", ["D-sections-number"], ""),
    ("detectable_format:multiple_sections", SEC2, "My Plan\nSECTION 1\nIntro.\nSECTION 2\nMore.", "pass", ["D-sections-preamble"], ""),
    ("detectable_format:multiple_sections", SEC2, "SECTION 1\nSECTION 2\nOnly text here.", "fail", [], "empty first section"),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears", "pass", [], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n* Plums", "fail", [], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "- Apples\n- Pears", "pass", ["D-bullet-markers"], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n\n---\n\nThat is all.", "pass", [], "horizontal rule"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "*Note: fruit list below*\n* Apples\n* Pears", "pass", [], "italic line"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* Fruits\n  * Apples\n  * Pears", "pass", ["D-bullet-nested"], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "+ Apples\n+ Pears", "pass", ["D-bullet-markers"], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "1. Apples\n2. Pears", "fail", [], ""),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n\n* * *\n\nDone.", "pass", [], "* * * rule"),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* and *urgent*.", "pass", [], ""),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* only.", "fail", [], ""),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "This is **important**.", "pass", ["D-highlight-bold"], ""),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Compute 2 * 3 * 4 now.", "fail", [], "multiplication signs"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "* item one\n* item two", "fail", [], "bullets"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Note: ** ** here.", "fail", [], "empty"),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", None, "I like cats.-They are cute.-Dogs are fine too.", "pass", [], ""),
    ("detectable_format:sentence_hyphens", None, "I like cats. They are cute.", "fail", [], ""),
    ("detectable_format:sentence_hyphens", None, "I like cats.- They are cute.", "fail", [], "space after hyphen"),
    ("detectable_format:sentence_hyphens", None, "Cats are well-known pets.-They purr.", "pass", [], "hyphenated word"),
    ("detectable_format:sentence_hyphens", None, "Hello world.", "pass", ["D-hyphens-single"], ""),
    ("detectable_format:sentence_hyphens", None, "I like cats.\nThey are cute.", "fail", [], "line break"),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", None, "[Hello] [world]", "pass", [], ""),
    ("detectable_format:square_brackets", None, "Hello [world]", "fail", [], ""),
    ("detectable_format:square_brackets", None, "[Hello], [world].", "pass", [], "punctuation outside"),
    ("detectable_format:square_brackets", None, "[Hello world]", "fail", ["D-brackets-per-word"], ""),
    ("detectable_format:square_brackets", None, "[Hello] world", "fail", [], ""),
    # detectable_format:title
    ("detectable_format:title", None, "<<Poem of Joy>>\nRoses are red.", "pass", [], ""),
    ("detectable_format:title", None, "Poem of Joy\nRoses are red.", "fail", [], ""),
    ("detectable_format:title", None, "<<   >>\nRoses are red.", "fail", [], "blank title"),
    ("detectable_format:title", None, "Intro line.\n<<My Title>>\nBody.", "pass", ["D-title-position"], ""),
    # first_word:first_word_answer
    ("first_word:first_word_answer", {"first_word": "development"}, "Development is key to growth.", "pass", [], ""),
    ("first_word:first_word_answer", {"first_word": "development"}, "Development, as a concept, matters.", "pass", [], "comma after the word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters.", "pass", ["D-first-last-markup"], ""),
    ("first_word:first_word_answer", {"first_word": "development"}, "Growth needs development.", "fail", [], ""),
    ("first_word:first_word_answer", {"first_word": "development"}, "development is lowercase here.", "pass", [], ""),
    ("first_word:first_word_answer", {"first_word": "development"}, "Developments are many.", "fail", [], ""),
    # first_word:first_word_sent
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good. Peace is calm.", "pass", [], ""),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good. War is bad.", "fail", [], ""),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace, friends, is good. Peace matters.", "pass", [], "comma after the word"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good!! Peace wins.", "pass", [], "double exclamation"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "# Title\nPeace is good. Peace is calm.", "fail", [], "heading"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace is good\nPeace is calm", "pass", [], "lines"),
    # keywords:existence
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "A quote about teaching.", "pass", [], ""),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "A quote about learning.", "fail", [], ""),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "Many quotes about teachings.", "fail", ["D-keyword-substring"], ""),
    ("keywords:existence", {"keywords": ["quote", "teaching"]}, "QUOTE and TEACHING in caps.", "pass", ["D-keyword-case"], ""),
    # keywords:forbidden_words
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "A quiet room.", "pass", [], ""),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "The sound was loud.", "fail", [], ""),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "The soundtrack was loud.", "pass", ["D-keyword-substring"], ""),
    ("keywords:forbidden_words", {"forbidden_words": ["sound", "square"]}, "SOUND check.", "fail", ["D-keyword-case"], ""),
    # keywords:frequency
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "The monitor and another monitor.", "pass", [], ""),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "The monitor.", "fail", [], ""),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "less than"}, "The monitor is on.", "pass", [], ""),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "less than"}, "The monitors and the monitoring.", "pass", ["D-keyword-substring"], ""),
    ("keywords:frequency", {"keyword": "monitor", "frequency": 2, "relation": "at least"}, "monitor, monitors", "fail", ["D-keyword-substring"], ""),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 1, "m": 3}, "We visited village markets today.", "pass", [], ""),
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 1, "m": 3}, "First, the village was quiet.", "pass", [], "comma is not a word"),
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 2, "m": 1}, "Hello there. Village life is calm.", "pass", ["D-keyword-case"], ""),
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 2, "m": 2}, "One sentence only with village.", "fail", [], ""),
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 1, "m": 2}, "A village. Then more.", "pass", [], ""),
    # keywords:letter_frequency
    ("keywords:letter_frequency", {"letter": "p", "let_frequency": 3, "let_relation": "at least"}, "Pop Pip", "pass", ["D-letter-case"], ""),
    ("keywords:letter_frequency", {"letter": "e", "let_frequency": 2, "let_relation": "less than"}, "Hello there.", "fail", [], "three e"),
    ("keywords:letter_frequency", {"letter": "e", "let_frequency": 2, "let_relation": "less than"}, "Hi.", "pass", [], ""),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", None, "Cats like fish.", "pass", [], ""),
    ("keywords:no_adjacent_consecutive", None, "Big cats run.", "fail", [], "b c"),
    ("keywords:no_adjacent_consecutive", None, "Cats bite.", "fail", ["D-consecutive-order"], "c b"),
    ("keywords:no_adjacent_consecutive", None, "**Apple** **banana** time.", "fail", [], "a b behind markup"),
    ("keywords:no_adjacent_consecutive", None, "Item 1 2 go.", "pass", [], "digits"),
    ("keywords:no_adjacent_consecutive", None, "Apples, bananas.", "fail", [], ""),
    # keywords:palindrome
    ("keywords:palindrome", None, "We saw a racecar today.", "pass", [], ""),
    ("keywords:palindrome", None, "We saw a car today.", "fail", ["D-palindrome-min"], "only a"),
    ("keywords:palindrome", None, "Cats run fast.", "fail", [], ""),
    ("keywords:palindrome", None, "- Cats run fast\n- Dogs walk home", "fail", [], "bullet dashes"),
    ("keywords:palindrome", None, "Level up your game.", "pass", [], "capitalized"),
    ("keywords:palindrome", None, "Never odd or even, they say.", "pass", [], "phrase palindrome"),
    ("keywords:palindrome", None, "Look at the radar.", "pass", [], "period attached"),
    # keywords:start_end
    ("keywords:start_end", None, "Hello world and hello", "pass", [], ""),
    ("keywords:start_end", None, "Hello world and hello.", "fail", [], "trailing period"),
    ("keywords:start_end", None, "Hello world and goodbye", "fail", [], ""),
    ("keywords:start_end", None, "**Hello** world and **hello**", "fail", [], "trailing markup"),
    ("keywords:start_end", None, "Hello", "pass", ["D-start-end-single"], ""),
    ("keywords:start_end", None, '"Hello," she said hello', "pass", ["D-start-markup"], "leading quote"),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "at least"}, "Skin care and skin health.", "pass", [], ""),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "at least"}, "skin skin skin", "fail", ["D-appear-n-times"], ""),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "less than"}, "Skin care and skin health.", "pass", [], "hidden relation"),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 2, "relation": "less than"}, "No mention here.", "fail", [], "hidden relation"),
    ("keywords:word_count_different_numbers", {"keyword": "skin", "frequency": 1, "relation": "less than"}, "My skin is fine.", "pass", [], "hidden relation"),
    # keywords:word_once
    ("keywords:word_once", {"keyword": "fix"}, "Please fix it.", "pass", [], ""),
    ("keywords:word_once", {"keyword": "fix"}, "Fix it and fix it again.", "pass", [], "include, twice"),
    ("keywords:word_once", {"keyword": "fix"}, "Nothing here.", "fail", [], ""),
    ("keywords:word_once", {"keyword": "fix"}, "Please fix the prefix.", "pass", [], "substring elsewhere"),
    ("keywords:word_once", {"keyword": "fix"}, "The prefix is wrong.", "fail", ["D-keyword-substring"], ""),
    # language:response_language
    ("language:response_language", {"language": "es"}, "Hola, ¿cómo estás? Hoy hace buen tiempo en la ciudad y vamos al parque con los niños.", "pass", [], ""),
    ("language:response_language", {"language": "es"}, "Hello, how are you? The weather is nice in the city today and we are going to the park.", "fail", [], ""),
    ("language:response_language", {"language": "es"}, "", "fail", [], "empty"),
    ("language:response_language", {"language": "es"}, "12345 67890", "fail", [], "digits only"),
    ("language:response_language", {"language": "ko"}, "안녕하세요. 오늘은 날씨가 정말 좋습니다. 공원에 산책하러 가요.", "pass", [], ""),
    # last_word:last_word_answer
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the limit.", "pass", [], ""),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the **limit**.", "pass", ["D-first-last-markup"], ""),
    ("last_word:last_word_answer", {"last_word": "limit"}, "The limit was reached.", "fail", [], ""),
    ("last_word:last_word_answer", {"last_word": "limit"}, "", "fail", [], "empty"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the LIMIT", "pass", [], "case of the word"),
    # last_word:last_word_sent
    ("last_word:last_word_sent", {"last_word": "limit"}, "This is the limit. That is a limit!", "pass", [], ""),
    ("last_word:last_word_sent", {"last_word": "limit"}, "This is the limit. That is fine.", "fail", [], ""),
    ("last_word:last_word_sent", {"last_word": "limit"}, "This is the limit... Another limit.", "pass", [], "ellipsis"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "# Heading\nThis is the limit.", "fail", ["D-sentence-lines"], "heading"),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}, "Intro paragraph here.\n\nCrash tests are useful.", "pass", [], ""),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nTests crash often.", "fail", [], ""),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\n\n\nCrash tests.", "pass", ["D-paragraph-blank"], ""),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nCrash: tests are useful.", "pass", [], "colon after the word"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "crash"}, "Crash one.\n\nCrash two.", "fail", [], "unsatisfiable: paragraph 3 of 2"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}, "Intro.\n\nCrash tests.\n\nThird paragraph.", "fail", [], "three paragraphs"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 1, "nth_paragraph": 1, "first_word": "brick"}, "Brick walls last.", "pass", [], ""),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", "pass", [], ""),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n\nSecond paragraph.", "fail", [], "no divider"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First.\n***\nSecond.\n***\nThird.", "fail", [], ""),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First with ***bold italic*** text.\n***\nSecond.", "pass", ["D-divider-line"], ""),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 1}, "Just one paragraph.", "pass", [], ""),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "A.\n\n***\n\nB.\n\n***\n\nC.", "pass", [], "dividers between blank lines"),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One. Two. Three.", "pass", [], ""),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "less than"}, "One. Two. Three.", "fail", [], ""),
    ("length_constraints:number_sentences", {"num_sentences": 2, "relation": "at least"}, "Dr. Smith arrived. He sat.", "pass", [], ""),
    ("length_constraints:number_sentences", {"num_sentences": 2, "relation": "less than"}, "Title line\nThis is one sentence.", "fail", ["D-sentence-lines"], ""),
    # length_constraints:number_words
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "One two three four five.", "pass", [], ""),
    ("length_constraints:number_words", {"num_words": 5, "relation": "less than"}, "One two three four five.", "fail", [], ""),
    ("length_constraints:number_words", {"num_words": 3, "relation": "at least"}, "Привет как дела", "pass", [], "Cyrillic words"),
    ("length_constraints:number_words", {"num_words": 3, "relation": "less than"}, "我爱你中国", "fail", ["D-word-cjk"], ""),
    ("length_constraints:number_words", {"num_words": 4, "relation": "at least"}, "Don't stop now.", "fail", ["D-word"], ""),
    # letters:letter_counting
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Hello", "pass", [], ""),
    ("letters:letter_counting", {"N": 2, "relation": "less than"}, "Hello", "fail", [], ""),
    ("letters:letter_counting", {"N": 2, "relation": "less than"}, "A", "pass", [], ""),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Привет", "pass", [], "Cyrillic letters"),
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "42", "pass", [], ""),
    # letters:letter_counting2
    ("letters:letter_counting2", {"letter": "r", "let_frequency": 2, "let_relation": "at least"}, "Red roses.", "pass", [], ""),
    ("letters:letter_counting2", {"letter": "r", "let_frequency": 2, "let_relation": "less than"}, "Red roses.", "fail", [], ""),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", None, "First.\n***\nSecond.", "pass", [], ""),
    ("paragraphs:paragraphs", None, "First.\n\nSecond.", "fail", [], "no divider"),
    ("paragraphs:paragraphs", None, "First.\n***\nSecond.\n***\nThird.", "fail", [], "three"),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", None, "First.\n\nSecond.", "pass", [], ""),
    ("paragraphs:paragraphs2", None, "First.\n\nSecond.\n\nThird.", "fail", [], "three"),
    ("paragraphs:paragraphs2", None, "First.\nSecond.", "fail", [], "one"),
    ("paragraphs:paragraphs2", None, "First.\n\n\nSecond.", "pass", [], ""),
    ("paragraphs:paragraphs2", None, "First.\n\n\n\nSecond.", "pass", ["D-paragraph-blank"], ""),
    # punctuation
    ("punctuation:no_comma", None, "No commas here.", "pass", [], ""),
    ("punctuation:no_comma", None, "Yes, commas.", "fail", [], ""),
    ("punctuation:no_comma", None, "你好，世界", "fail", ["D-comma-variants"], "full-width comma"),
    ("punctuation:punctuation_dot", None, "No dots here", "pass", [], ""),
    ("punctuation:punctuation_dot", None, "One dot.", "fail", [], ""),
    ("punctuation:punctuation_dot", None, "Pi is 3 or 3.14 roughly", "fail", [], "decimal point"),
    ("punctuation:punctuation_dot", None, "Wait…", "fail", ["D-dot-variants"], "ellipsis character"),
    ("punctuation:punctuation_exclamation", None, "Calm text.", "pass", [], ""),
    ("punctuation:punctuation_exclamation", None, "Wow!", "fail", [], ""),
    ("punctuation:punctuation_exclamation", None, "¡Hola amigos", "fail", ["D-exclamation-variants"], ""),
    ("punctuation:punctuation_exclamation", None, "你好！", "fail", ["D-exclamation-variants"], ""),
    # startend:end_checker
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the answer. Any other questions?", "pass", [], ""),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Any other questions? Thanks.", "fail", [], ""),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the answer. **Any other questions?**", "pass", ["D-end-trailing"], ""),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the answer. any other questions?", "fail", ["D-end-case"], ""),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the answer. Many other questions?", "fail", [], "different word"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Answer.\nAny other questions?\n", "pass", [], ""),
    ("startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "Done. Is there anything else I can help with?", "pass", [], ""),
    # startend:quotation
    ("startend:quotation", None, '"Hello world."', "pass", [], ""),
    ("startend:quotation", None, "Hello world.", "fail", [], ""),
    ("startend:quotation", None, "“Hello world.”", "pass", ["D-quote-curly"], ""),
    ("startend:quotation", None, "'Hello world.'", "fail", [], "single quotes"),
    ("startend:quotation", None, '"', "fail", [], "one character"),
]

# contract v4 additions (prompted by development panel responses; see ISSUE.md)
FIXTURES += [
    ("detectable_format:sentence_hyphens", None, "Calm minds begin – our therapists offer care – empathy drives every session", "fail", [], "spaced en dashes"),
    ("detectable_format:sentence_hyphens", None, "I like cats.—They are cute.", "fail", ["D-hyphen-dash"], "em dash"),
    ("combination:two_responses", None, "A first.\n******\nB second.\n******", "fail", ["D-two-sep-edge"], "trailing separator"),
    ("keywords:no_adjacent_consecutive", None, "потом раз", "fail", ["D-consecutive-script"], "Cyrillic p r"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Main text here - P.P.S This is extra", "fail", ["D-postscript-line"], "marker mid-line"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "[Main] [text]\n[P.P.S] [extra]", "pass", [], "bracketed marker"),
    ("detectable_format:multiple_sections", {"num_sections": 1, "section_spliter": "SECTION"}, '"SECTION 1\nall text here"', "pass", [], "quoted response"),
    ("change_case:english_capital", None, "SCHOOL OF REALISM", "pass", [], "short all-caps English"),
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "at least"}, "これはTEST、ROBOT、MATCHです。", "pass", [], "all-caps words between CJK punctuation"),
    ("detectable_format:sentence_hyphens", None, "", "pass", ["D-hyphens-single"], "empty: no sentences to connect"),
]

# Graded-text extraction: (instruction_id, kwargs, raw response, thinking configuration, label, deps, note)
PIPELINE = [
    ("punctuation:no_comma", None, "The user wants no commas, so I will avoid them and answer briefly", True, "fail", [], "reasoning never closed (thinking model)"),
    ("punctuation:no_comma", None, "<think>Reasoning, with commas, here.</think>\n\nFinal answer without any", True, "pass", [], "graded text after </think>"),
    ("punctuation:no_comma", None, "Reasoning, with commas, here.</think>\n\nFinal answer without any", True, "pass", [], "template-opened think block"),
    ("keywords:existence", {"keywords": ["tag"]}, "Use the <think> tag to mark private reasoning in a template.", False, "pass", ["D-think-nonthinking"], "non-thinking answer mentions <think>"),
    ("punctuation:no_comma", None, "<think>Let me think about this, carefully, before", False, "fail", [], "unclosed reasoning block (non-thinking)"),
    ("keywords:existence", {"keywords": ["paris"]}, "Thinking, more thinking.</think>The capital is Paris.", True, "pass", [], ""),
    ("keywords:existence", {"keywords": ["paris"]}, "The user asks for the capital of France. It is Paris, so the answer should name Paris", True, "fail", [], "reasoning never closed (thinking model): graded as the answer"),
]
