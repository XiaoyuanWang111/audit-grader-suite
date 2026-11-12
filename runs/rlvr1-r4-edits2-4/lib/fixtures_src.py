"""Hand-written fixtures, labeled from audit/CONTRACTS.md alone (proposed readings).

Each entry: (instruction_id, kwargs, response, label, note). A response is graded text,
except entries whose note starts with "thinking:", which are raw thinking-mode responses.
"""

AT, LT = "at least", "less than"

FIXTURES = [
    # change_case:capital_word_frequency
    ("change_case:capital_word_frequency", {"capital_relation": LT, "capital_frequency": 3}, "The NASA team met at noon.", "pass", "control"),
    ("change_case:capital_word_frequency", {"capital_relation": AT, "capital_frequency": 3}, "The NASA team met at noon.", "fail", "control"),
    ("change_case:capital_word_frequency", {"capital_relation": AT, "capital_frequency": 2}, "I saw NASA today.", "pass", "D-capital-word: I counts"),
    ("change_case:capital_word_frequency", {"capital_relation": LT, "capital_frequency": 2}, "DON'T panic.", "pass", "D-word-units: DON'T is one word"),
    # change_case:english_capital
    ("change_case:english_capital", {}, "THE WEATHER IS NICE TODAY AND WE ARE GOING TO THE PARK WITH OUR FRIENDS.", "pass", "control"),
    ("change_case:english_capital", {}, "The weather is nice today and we are going to the park.", "fail", "control"),
    ("change_case:english_capital", {}, "LE TEMPS EST TRÈS BEAU AUJOURD'HUI ET NOUS ALLONS AU PARC AVEC NOS AMIS.", "fail", "not English"),
    ("change_case:english_capital", {}, "123 456", "fail", "no letters"),
    # change_case:english_lowercase
    ("change_case:english_lowercase", {}, "the weather is nice today and we are going to the park with our friends.", "pass", "control"),
    ("change_case:english_lowercase", {}, "The weather is nice today.", "fail", "control"),
    ("change_case:english_lowercase", {}, "le temps est très beau aujourd'hui et nous allons au parc avec nos amis.", "fail", "not English"),
    # combination:two_responses
    ("combination:two_responses", {}, "Paris is the capital of France.\n******\nThe capital of France is Paris.", "pass", "control"),
    ("combination:two_responses", {}, "Paris is the capital of France.", "fail", "control"),
    ("combination:two_responses", {}, "Paris.\n******\nParis.", "fail", "identical"),
    ("combination:two_responses", {}, "A cat.\n******\nA dog.\n******\nA cow.", "fail", "three responses"),
    ("combination:two_responses", {}, "A cat.\n*******\nA dog.", "fail", "seven asterisks are not the separator"),
    # copy:repeat_phrase
    ("copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is our best medicine. Laughter is my best medicine.", "pass", "control: center word replaced"),
    ("copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is the best medicine. Laughter is the best medicine.", "fail", "unchanged copies"),
    ("copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is the best medicine. Laughter is our best medicine.", "fail", "one unchanged copy and one variant (fails under both D-repeat-original readings)"),
    ("copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is the finest medicine. Laughter is the greatest medicine.", "fail", "D-repeat-center: 4th of 5 words replaced"),
    ("copy:repeat_phrase", {"phrase": "Don't judge a book by cover", "small_n": 2}, "Don’t judge the book by cover. Don’t judge one book by cover.", "pass", "typographic apostrophe"),
    ("copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "They said laughter is our best medicine and laughter is my best medicine.", "pass", "D-word-case: lowercase repetition"),
    # count:count_unique
    ("count:count_unique", {}, "Every cat sleeps quietly.", "pass", "control"),
    ("count:count_unique", {}, "We like cats and cats.", "fail", "control"),
    ("count:count_unique", {}, "Apples, pears, plums.", "pass", "punctuation is not a word"),
    ("count:count_unique", {}, "The cat saw THE dog.", "fail", "D-word-case"),
    # count:counting_composition
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep. Dogs bark.\n* * *\nFish swim. Bees buzz. Cows moo.\n* * *\nKids play. Moms cook. Dads read.", "pass", "control: the instructed divider"),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep.", "fail", "control"),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep. Dogs bark. Fish swim. Bees buzz. Cows moo. Kids play. Moms cook. Dads read.", "fail", "no paragraphs"),
    # count:lowercase_counting
    ("count:lowercase_counting", {"N": 2}, "The cat sat on a mat.", "pass", "D-lowercase-scope: each lowercase word once"),
    ("count:lowercase_counting", {"N": 2}, "the the the end", "fail", "a lowercase word three times"),
    ("count:lowercase_counting", {"N": 2}, "I AM OK.", "pass", "no lowercase words"),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], meet me at [address].", "pass", "control"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], meet me there.", "fail", "control"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [], meet me at [].", "fail", "empty brackets"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [ ], meet me at [ ].", "fail", "whitespace-only brackets"),
    # detectable_content:postscript
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\nP.S. Thanks for asking.", "pass", "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer. Thanks for asking.", "fail", "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Remember to read the P.S. section of the letter.\n\nThanks.", "fail", "mention inside a sentence"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\nP.P.S. One more note.", "fail", "P.P.S. is not P.S."),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "P.S. Thanks.\n\nHere is my answer.", "fail", "D-postscript-position"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\n**P.S.** Thanks for asking.", "pass", "bold marker"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Here is my answer.\n\nP.P.S. One more note.", "pass", "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\np.s. thanks for asking.", "fail", "D-postscript-case"),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>> <<with my>> <<cute dog>>", "pass", "control"),
    ("detectable_format:bigram_wrapping", {}, "I am at home with my cute dog.", "fail", "control"),
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>> today", "fail", "unwrapped last word"),
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>>.", "pass", "punctuation after the last group"),
    ("detectable_format:bigram_wrapping", {}, "hello", "fail", "one unwrapped word"),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", {}, "My answer is yes.", "pass", "control"),
    ("detectable_format:constrained_response", {}, "Yes, I think so.", "fail", "control"),
    ("detectable_format:constrained_response", {}, "My answer is yes. My answer is no.", "fail", "two options"),
    ("detectable_format:constrained_response", {}, "My answer is yes. The data supports it.", "pass", "D-constrained-extra"),
    # detectable_format:json_format
    ("detectable_format:json_format", {}, '{"name": "Ada", "age": 36}', "pass", "control"),
    ("detectable_format:json_format", {}, '```json\n{"a": 1}\n```', "pass", "control fenced"),
    ("detectable_format:json_format", {}, 'Here is the JSON: {"a": 1}', "fail", "control"),
    ("detectable_format:json_format", {}, '"hello"', "fail", "D-json-value"),
    ("detectable_format:json_format", {}, '```JSON\n{"a": 1}\n```', "pass", "uppercase fence tag"),
    ("detectable_format:json_format", {}, "NaN", "fail", "NaN is not JSON"),
    ("detectable_format:json_format", {}, '```{"a": 1}```', "pass", "one-line fence"),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nIntro text here.\nSECTION 2\nMore text here.", "pass", "control"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nOnly one section here.", "fail", "control"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text.", "fail", "three sections for two"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nSee SECTION 2 below for details.", "fail", "mention inside a sentence"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "Section 1\nA text.\nSection 2\nB text.", "pass", "D-section-case"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION A\nA text.\nSECTION B\nB text.", "pass", "D-section-label"),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears", "pass", "control"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n* Plums", "fail", "control"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "*Note:* fruit list\n* Apples\n* Pears", "pass", "italic at a line start is not a bullet"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n---\nThat is all.", "pass", "a horizontal rule is not a bullet"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "-5 degrees today.\n* Apples\n* Pears", "pass", "a negative number is not a bullet"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n* * *\nDone.", "pass", "a * * * divider is not a bullet"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 2}, "+ Apples\n+ Pears", "pass", "D-bullet-markers"),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* and *urgent*.", "pass", "control"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* only.", "fail", "control"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is **important** and **urgent**.", "pass", "D-highlight-bold"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "Compute 2 * 3 * 4 and *done*.", "fail", "multiplication signs"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "* * *\nText *one*.", "fail", "a divider is not a highlight"),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", {}, "The sun rose.-Birds sang.-We walked home.", "pass", "D-hyphens-spaces: spaces inside sentences"),
    ("detectable_format:sentence_hyphens", {}, "Sunrise.-Birdsong.-Walks.", "pass", "control"),
    ("detectable_format:sentence_hyphens", {}, "The sun rose. Birds sang. We walked home.", "fail", "control"),
    ("detectable_format:sentence_hyphens", {}, "The well-known poet arrived.-We listened.", "pass", "hyphenated word inside a sentence"),
    ("detectable_format:sentence_hyphens", {}, "Well-known. Fine-tuned.", "fail", "space between sentences"),
    ("detectable_format:sentence_hyphens", {}, "The sun rose.", "pass", "D-hyphens-single; D-hyphens-spaces"),
    ("detectable_format:sentence_hyphens", {}, "The-sun-rose.-Birds-sang.", "pass", "no spaces at all"),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", {}, "[The] [sun] [is] [bright]", "pass", "control"),
    ("detectable_format:square_brackets", {}, "The sun is bright.", "fail", "control"),
    ("detectable_format:square_brackets", {}, "[The] sun is bright.", "fail", "one word bracketed"),
    ("detectable_format:square_brackets", {}, "[The] [sun] [is] [bright].", "pass", "final period outside the brackets"),
    ("detectable_format:square_brackets", {}, "[The sun is bright]", "fail", "D-brackets-each"),
    # detectable_format:title
    ("detectable_format:title", {}, "<<Ode to Rain>>\nThe rain falls softly.", "pass", "control"),
    ("detectable_format:title", {}, "Ode to Rain\nThe rain falls softly.", "fail", "control"),
    ("detectable_format:title", {}, "<< >>\nThe rain falls softly.", "fail", "blank title"),
    ("detectable_format:title", {}, "The rain falls softly.\n<<Ode to Rain>>", "pass", "D-title-position"),
    # first_word:first_word_answer
    ("first_word:first_word_answer", {"first_word": "development"}, "Development is key to growth.", "pass", "control"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Growth needs development.", "fail", "control"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Development, in short, matters.", "pass", "comma after the first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters.", "pass", "bold first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Developments matter.", "fail", "control: another word"),
    # first_word:first_word_sent
    ("first_word:first_word_sent", {"first_word": "rain"}, "Rain falls today. Rain cools the air.", "pass", "control"),
    ("first_word:first_word_sent", {"first_word": "rain"}, "Rain falls today. Clouds gather.", "fail", "control"),
    ("first_word:first_word_sent", {"first_word": "rain"}, "Rain, again, falls. Rain cools the air.", "pass", "comma after the first word"),
    ("first_word:first_word_sent", {"first_word": "rain"}, "Rain report\nClouds gather. Rain falls.", "fail", "D-sentence-split"),
    # keywords:existence
    ("keywords:existence", {"keywords": ["art", "home"]}, "Art makes a house a home.", "pass", "control"),
    ("keywords:existence", {"keywords": ["art", "home"]}, "Art makes a house warm.", "fail", "control"),
    ("keywords:existence", {"keywords": ["art", "home"]}, "We start at home.", "fail", "art only inside start"),
    ("keywords:existence", {"keywords": ["art", "home"]}, "Arts make a house a home.", "fail", "D-keyword-inflection"),
    # keywords:forbidden_words
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "The rules are fair.", "pass", "control"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "The law is fair.", "fail", "control"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "The lawyer is fair.", "pass", "control: another word"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "The law-abiding citizen waited.", "pass", "D-word-units"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "sound"]}, "LAW and order.", "fail", "control: case"),
    # keywords:frequency
    ("keywords:frequency", {"keyword": "cat", "relation": LT, "frequency": 2}, "A cat sleeps.", "pass", "control"),
    ("keywords:frequency", {"keyword": "cat", "relation": LT, "frequency": 2}, "A cat and another cat.", "fail", "control"),
    ("keywords:frequency", {"keyword": "cat", "relation": LT, "frequency": 2}, "A cat reads the catalog.", "pass", "catalog is not cat"),
    ("keywords:frequency", {"keyword": "cat", "relation": AT, "frequency": 2}, "The category of cat.", "fail", "category is not cat"),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far. Then the river appeared.", "pass", "control"),
    ("keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far. The river appeared.", "fail", "control"),
    ("keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far. Then, the river appeared.", "pass", "a comma is not a word"),
    ("keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far. Then the River appeared.", "pass", "D-word-case"),
    # keywords:letter_frequency
    ("keywords:letter_frequency", {"letter": "z", "let_relation": AT, "let_frequency": 2}, "Zebras graze.", "pass", "control"),
    ("keywords:letter_frequency", {"letter": "z", "let_relation": AT, "let_frequency": 2}, "A lazy day.", "fail", "control"),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", {}, "Zebras graze quietly near water.", "pass", "control"),
    ("keywords:no_adjacent_consecutive", {}, "A big dog.", "fail", "a then b"),
    ("keywords:no_adjacent_consecutive", {}, "Big apples grow.", "fail", "D-consecutive-order: b then a"),
    ("keywords:no_adjacent_consecutive", {}, "The the end.", "pass", "repeated word, no consecutive letters"),
    ("keywords:no_adjacent_consecutive", {}, '"apple" "banana" were eaten.', "fail", "quoted words a then b"),
    ("keywords:no_adjacent_consecutive", {}, "Chapter 1 2 ended.", "pass", "digits are not letters"),
    # keywords:palindrome
    ("keywords:palindrome", {}, "Mom saw a racecar.", "pass", "control"),
    ("keywords:palindrome", {}, "The weather is warm.", "fail", "control"),
    ("keywords:palindrome", {}, "I saw the sea.", "fail", "D-palindrome-length: only I"),
    ("keywords:palindrome", {}, "* Apples\n* Pears", "fail", "a bullet marker is not a palindrome"),
    ("keywords:palindrome", {}, "Rain fell - then stopped.", "fail", "a dash is not a palindrome"),
    ("keywords:palindrome", {}, "Rain fell.\n---\nThen it stopped.", "fail", "a horizontal rule is not a palindrome"),
    ("keywords:palindrome", {}, "Level ground.", "pass", "capitalized palindrome"),
    ("keywords:palindrome", {}, "Paddle the kayak.", "pass", "palindrome before a period"),
    # keywords:start_end
    ("keywords:start_end", {}, "Hello there my friend hello", "pass", "control"),
    ("keywords:start_end", {}, "Hello there my friend", "fail", "control"),
    ("keywords:start_end", {}, "Hello there my friend hello.", "fail", "period after the last word"),
    ("keywords:start_end", {}, "**Hello** there my friend hello", "pass", "bold first word"),
    ("keywords:start_end", {}, "! !", "fail", "no words"),
    ("keywords:start_end", {}, "Hello", "pass", "D-start-end-single"),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", {"keyword": "tree", "relation": AT, "frequency": 2}, "A tree and a tree.", "pass", "control"),
    ("keywords:word_count_different_numbers", {"keyword": "tree", "relation": LT, "frequency": 2}, "A tree and a tree.", "pass", "hidden relation less than"),
    ("keywords:word_count_different_numbers", {"keyword": "tree", "relation": LT, "frequency": 2}, "Nothing here.", "fail", "hidden relation less than, zero occurrences"),
    ("keywords:word_count_different_numbers", {"keyword": "tree", "relation": AT, "frequency": 2}, "A tree, a tree, a tree.", "fail", "D-word-count-exact"),
    # keywords:word_once
    ("keywords:word_once", {"keyword": "river"}, "The river flows.", "pass", "control"),
    ("keywords:word_once", {"keyword": "river"}, "The stream flows.", "fail", "control"),
    ("keywords:word_once", {"keyword": "river"}, "The river flows into another river.", "pass", "keyword twice"),
    ("keywords:word_once", {"keyword": "river"}, "The riverbank is wet.", "fail", "river only inside riverbank"),
    # language:response_language
    ("language:response_language", {"language": "fr"}, "Le temps est très beau aujourd'hui et nous allons au parc avec nos amis.", "pass", "control"),
    ("language:response_language", {"language": "fr"}, "The weather is very nice today and we are going to the park.", "fail", "control"),
    ("language:response_language", {"language": "fr"}, "12345", "fail", "no language"),
    # last_word:last_word_answer
    ("last_word:last_word_answer", {"last_word": "limit"}, "We pushed to the limit.", "pass", "control"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "The limit was reached.", "fail", "control"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "", "fail", "empty response"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We hit the speed-limit.", "fail", "control: another word"),
    # last_word:last_word_sent
    ("last_word:last_word_sent", {"last_word": "limit"}, "We reached the limit. They also hit the limit!", "pass", "control"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "We reached the limit. They stopped.", "fail", "control"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "Speed\nWe reached the limit.", "fail", "D-sentence-split"),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\nRain fell all night.", "pass", "control"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\nThe rain fell all night.", "fail", "control"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\n**Rain** fell all night.", "pass", "bold first word"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\nRain: it fell all night.", "pass", "colon after the first word"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\n\n\nRain fell all night.", "pass", "D-paragraph-blank-lines"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "rain"}, "Rain fell.\n\nRain stopped.", "fail", "nth beyond num: no response can pass"),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", "pass", "control"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond.\n***\nThird.", "fail", "control"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n\nSecond paragraph.", "fail", "no divider"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "***Note*** first part.\n***\nSecond part.", "pass", "bold italics are not a divider"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First part.\n***\nSecond part.\n***", "fail", "D-divider-edges"),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", {"relation": LT, "num_sentences": 3}, "One idea. Two ideas.", "pass", "control"),
    ("length_constraints:number_sentences", {"relation": LT, "num_sentences": 3}, "One. Two. Three.", "fail", "control"),
    ("length_constraints:number_sentences", {"relation": AT, "num_sentences": 2}, "We met Dr. Smith today.", "fail", "abbreviation"),
    ("length_constraints:number_sentences", {"relation": AT, "num_sentences": 3}, "Title\nOne idea. Two ideas.", "pass", "D-sentence-split"),
    # length_constraints:number_words
    ("length_constraints:number_words", {"relation": AT, "num_words": 5}, "We walked to the old mill.", "pass", "control"),
    ("length_constraints:number_words", {"relation": AT, "num_words": 5}, "We walked home.", "fail", "control"),
    ("length_constraints:number_words", {"relation": LT, "num_words": 5}, "Don't stop, it's fine.", "pass", "D-word-units"),
    ("length_constraints:number_words", {"relation": AT, "num_words": 3}, "Мы пошли домой сегодня.", "pass", "Cyrillic words"),
    # letters:letter_counting
    ("letters:letter_counting", {"relation": AT, "N": 3}, "Hello", "pass", "control"),
    ("letters:letter_counting", {"relation": AT, "N": 3}, "Hi", "fail", "control"),
    ("letters:letter_counting", {"relation": LT, "N": 3}, "OK", "pass", "control"),
    ("letters:letter_counting", {"relation": AT, "N": 3}, "你好吗", "pass", "D-letter-script"),
    # letters:letter_counting2
    ("letters:letter_counting2", {"letter": "z", "let_relation": LT, "let_frequency": 2}, "A lazy day.", "pass", "control"),
    ("letters:letter_counting2", {"letter": "z", "let_relation": LT, "let_frequency": 2}, "Zebras graze.", "fail", "control"),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", {}, "First part.\n***\nSecond part.", "pass", "control"),
    ("paragraphs:paragraphs", {}, "First part.\n***\nSecond part.\n***\nThird part.", "fail", "three paragraphs"),
    ("paragraphs:paragraphs", {}, "First part.\n\nSecond part.\n\nThird part.", "fail", "no divider"),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", {}, "First part.\n\nSecond part.", "pass", "control"),
    ("paragraphs:paragraphs2", {}, "First part.\n\nSecond part.\n\nThird part.", "fail", "three paragraphs"),
    ("paragraphs:paragraphs2", {}, "First part.\n\n\n\nSecond part.", "pass", "D-paragraph-blank-lines"),
    # punctuation:no_comma
    ("punctuation:no_comma", {}, "No commas here.", "pass", "control"),
    ("punctuation:no_comma", {}, "Yes, there is one.", "fail", "control"),
    ("punctuation:no_comma", {}, "你好，世界", "fail", "D-comma-chars"),
    # punctuation:punctuation_dot
    ("punctuation:punctuation_dot", {}, "No dots here", "pass", "control"),
    ("punctuation:punctuation_dot", {}, "One dot.", "fail", "control"),
    ("punctuation:punctuation_dot", {}, "你好。", "fail", "D-dot-chars"),
    # punctuation:punctuation_exclamation
    ("punctuation:punctuation_exclamation", {}, "Calm words here.", "pass", "control"),
    ("punctuation:punctuation_exclamation", {}, "Wow!", "fail", "control"),
    ("punctuation:punctuation_exclamation", {}, "好！", "fail", "D-exclamation-chars"),
    # startend:end_checker
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan. Any other questions?", "pass", "control"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Any other questions? Here is the plan.", "fail", "control"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan. Many other questions?", "fail", "phrase inside a longer word"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan. **Any other questions?**", "pass", "D-end-markup"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan. any other questions?", "fail", "D-end-case"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, '"Here is the plan. Any other questions?"', "pass", "D-end-markup: closing quote"),
    # startend:quotation
    ("startend:quotation", {}, '"Hello there."', "pass", "control"),
    ("startend:quotation", {}, "Hello there.", "fail", "control"),
    ("startend:quotation", {}, "“Hello there.”", "pass", "D-quote-chars"),
    ("startend:quotation", {}, "'Hello there.'", "fail", "single quotation marks"),
    # graded-text extraction (raw thinking-mode responses)
    ("keywords:word_once", {"keyword": "river"}, "The user wants the word river once, so I will plan a short answer about a", "fail", "thinking: reasoning never closed"),
    ("punctuation:no_comma", {}, "I should avoid commas in my answer and write short sentences", "fail", "thinking: reasoning never closed"),
    ("keywords:word_once", {"keyword": "river"}, "Plan the answer.\n</think>\n\nThe river flows.", "pass", "thinking: control"),
    # empty graded text (D-empty-response)
    ("punctuation:no_comma", {}, "", "fail", "D-empty-response"),
]
