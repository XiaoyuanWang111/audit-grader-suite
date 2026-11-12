"""Hand-written fixtures, labeled from audit/CONTRACTS.md (proposed readings) alone.

Each entry: (instruction_id, kwargs, response, label, note). A label that depends on a decision
entry is the proposed reading's verdict; the build script records which entries can flip it.
"""

P, F = "pass", "fail"

KW = {
    "cap3": {"capital_frequency": 3, "capital_relation": "at least"},
    "cap_lt4": {"capital_frequency": 4, "capital_relation": "less than"},
    "phrase": {"phrase": "Laughter is the best medicine", "small_n": 2},
    "comp": {"n_sent": 3, "n_words": 2},
    "low2": {"N": 2},
    "ph2": {"num_placeholders": 2},
    "ps": {"postscript_marker": "P.S."},
    "pps": {"postscript_marker": "P.P.S"},
    "sec2": {"num_sections": 2, "section_spliter": "SECTION"},
    "bul2": {"num_bullets": 2},
    "hl2": {"num_highlights": 2},
    "fwa": {"first_word": "development"},
    "fws": {"first_word": "peace"},
    "exist": {"keywords": ["food", "poetry"]},
    "forbid": {"forbidden_words": ["bet", "raw"]},
    "freq": {"keyword": "box", "frequency": 2, "relation": "at least"},
    "pos": {"keyword": "shot", "n": 2, "m": 3},
    "pos1": {"keyword": "repeat", "n": 1, "m": 1},
    "letz": {"letter": "z", "let_frequency": 2, "let_relation": "at least"},
    "leta": {"letter": "a", "let_frequency": 3, "let_relation": "less than"},
    "wcd_lt": {"keyword": "box", "frequency": 2, "relation": "less than"},
    "wcd_al": {"keyword": "box", "frequency": 2, "relation": "at least"},
    "once": {"keyword": "fix"},
    "fr": {"language": "fr"},
    "lwa": {"last_word": "hello"},
    "lws": {"last_word": "limit"},
    "nth": {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"},
    "nth_bad": {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"},
    "np2": {"num_paragraphs": 2},
    "ns3": {"num_sentences": 3, "relation": "at least"},
    "nw5": {"num_words": 5, "relation": "at least"},
    "lc3": {"N": 3, "relation": "less than"},
    "lc2": {"N": 2, "relation": "less than"},
    "end": {"end_phrase": "Any other questions?"},
}

FIXTURES = [
    # change_case:capital_word_frequency
    ("change_case:capital_word_frequency", KW["cap3"], "The NASA and FBI teams met the CIA today.", P, "three all-caps words"),
    ("change_case:capital_word_frequency", KW["cap3"], "The NASA team met today.", F, "one all-caps word"),
    ("change_case:capital_word_frequency", KW["cap3"], "I saw NASA and FBI.", P, "single-letter I counts (D-capital-single-letter)"),
    ("change_case:capital_word_frequency", KW["cap_lt4"], "DON'T STOP NOW please.", P, "three all-caps words, less than 4"),
    # change_case:english_capital
    ("change_case:english_capital", None, "THIS IS MY ANSWER. IT IS WRITTEN IN ENGLISH AND USES ONLY CAPITAL LETTERS.", P, "control"),
    ("change_case:english_capital", None, "This is my answer in English.", F, "lowercase letters"),
    ("change_case:english_capital", None, "THIS IS MY ANSWER WITH ONE word IN LOWERCASE.", F, "one lowercase word"),
    ("change_case:english_capital", None, "ESTO ES MI RESPUESTA EN ESPAÑOL Y TODO ESTÁ ESCRITO EN MAYÚSCULAS.", F, "not English (D-english)"),
    # change_case:english_lowercase
    ("change_case:english_lowercase", None, "this is my answer. it is written in english with no capital letters at all.", P, "control"),
    ("change_case:english_lowercase", None, "This is my answer.", F, "capital T"),
    ("change_case:english_lowercase", None, "this is my answer about NASA and the moon.", F, "capitals inside"),
    ("change_case:english_lowercase", None, "esto es mi respuesta en español y todo está escrito en minúsculas.", F, "not English (D-english)"),
    # combination:two_responses
    ("combination:two_responses", None, "Paris is the capital of France.\n******\nThe capital of France is Paris.", P, "control"),
    ("combination:two_responses", None, "Paris.\n******\nParis.", F, "identical responses"),
    ("combination:two_responses", None, "Paris is the capital of France.", F, "no separator"),
    ("combination:two_responses", None, "Answer one is Paris.\n*******\nAnswer two is Lyon.", F, "seven asterisks are not the separator"),
    ("combination:two_responses", None, "Paris.\n******\nLyon.\n******\nNice.", F, "three responses"),
    # copy:repeat_phrase
    ("copy:repeat_phrase", KW["phrase"], "Laughter is a best medicine. Laughter is our best medicine.", P, "middle word replaced twice"),
    ("copy:repeat_phrase", KW["phrase"], "Laughter is the best medicine. Laughter is the best medicine.", F, "unchanged copies"),
    ("copy:repeat_phrase", KW["phrase"], "Laughter is a best medicine.", F, "one repetition, two asked"),
    ("copy:repeat_phrase", KW["phrase"], "Joy is the best medicine. Music is the best medicine.", F, "edge word replaced"),
    ("copy:repeat_phrase", KW["phrase"], "Laughter is the best medicine. Laughter is our best medicine.", F, "one unchanged copy and one transformed"),
    ("copy:repeat_phrase", KW["phrase"], "Laughter is the greatest medicine. Laughter is the finest medicine.", P, "inner, non-middle word replaced (D-repeat-center)"),
    # count:count_unique
    ("count:count_unique", None, "Every word here appears once.", P, "control"),
    ("count:count_unique", None, "The cat saw the dog.", F, "the repeated (case-insensitive, D-unique-case)"),
    ("count:count_unique", None, "Apples, pears, plums.", P, "repeated commas are not words"),
    ("count:count_unique", None, "A cat saw one dog.", P, "control"),
    # count:counting_composition
    ("count:counting_composition", KW["comp"], "Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies.", P, "three paragraphs of three two-word sentences"),
    ("count:counting_composition", KW["comp"], "Birds sing. Cats sleep. Dogs run.", F, "one paragraph"),
    ("count:counting_composition", KW["comp"], "Birds sing loudly. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies.", F, "a three-word sentence"),
    # count:lowercase_counting
    ("count:lowercase_counting", KW["low2"], "I like it", P, "each lowercase word once, two in total"),
    ("count:lowercase_counting", KW["low2"], "the cat and the dog", P, "each lowercase word at most twice (D-lowercase-counting-scope)"),
    ("count:lowercase_counting", KW["low2"], "the the the end", F, "the three times"),
    ("count:lowercase_counting", KW["low2"], "Hello World", P, "no lowercase words"),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", KW["ph2"], "Dear [name], your order ships to [address].", P, "control"),
    ("detectable_content:number_placeholders", KW["ph2"], "Dear [name], thanks.", F, "one placeholder"),
    ("detectable_content:number_placeholders", KW["ph2"], "Dear [name],\nyour order ships to [street\naddress].", F, "a bracket span across a line break is not a placeholder"),
    # detectable_content:postscript
    ("detectable_content:postscript", KW["ps"], "Here is my answer.\n\nP.S. Remember to drink water.", P, "control"),
    ("detectable_content:postscript", KW["ps"], "Here is my answer.", F, "no postscript"),
    ("detectable_content:postscript", KW["ps"], "Here is my answer.\n\nP.S Remember to drink water.", P, "marker without final dot (D-postscript-marker)"),
    ("detectable_content:postscript", KW["ps"], "Here is my answer.\n\nP.P.S. Remember to drink water.", F, "P.P.S is not P.S. (D-postscript-pps)"),
    ("detectable_content:postscript", KW["ps"], "P.S. Remember to drink water.\n\nHere is my answer in full.", F, "postscript not at the end (D-postscript-position)"),
    ("detectable_content:postscript", KW["ps"], "Ship the parcel with U.P.S. today.", F, "U.P.S. is not a postscript"),
    ("detectable_content:postscript", KW["ps"], "Here is my answer. P.S. Remember to drink water.", P, "marker after a sentence on the same line (D-postscript-line)"),
    ("detectable_content:postscript", KW["ps"], "Here is my answer.\n\np.s. Remember to drink water.", P, "lowercase marker (D-postscript-case, v4 proposal: case-insensitive)"),
    ("combination:two_responses", None, "******\nParis is the capital.\n******\nLyon is a city.", F, "leading separator (D-two-responses-edge)"),
    ("detectable_content:postscript", KW["pps"], "Here is my answer.\n\nP.P.S Remember to drink water.", P, "control P.P.S"),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> <<with my>> <<cute dog>>", P, "control"),
    ("detectable_format:bigram_wrapping", None, "I am at home with my cute dog.", F, "no brackets"),
    ("detectable_format:bigram_wrapping", None, "<<I am>> home", F, "last word outside brackets"),
    ("detectable_format:bigram_wrapping", None, "Hello", F, "one unwrapped word"),
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<home>>", P, "odd final one-word group (D-bigram-odd)"),
    ("detectable_format:bigram_wrapping", None, "<<I am home>>", F, "three words in one group"),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", None, "My answer is yes.", P, "control"),
    ("detectable_format:constrained_response", None, "Yes.", F, "not an option"),
    ("detectable_format:constrained_response", None, "My answer is yes. Because it is sunny.", F, "option plus explanation (D-constrained-extra)"),
    ("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", F, "two options"),
    # detectable_format:json_format
    ("detectable_format:json_format", None, '{"answer": "Paris"}', P, "control"),
    ("detectable_format:json_format", None, '```json\n{"answer": "Paris"}\n```', P, "fenced"),
    ("detectable_format:json_format", None, '```json {"answer": "Paris"} ```', P, "fence on one line"),
    ("detectable_format:json_format", None, "The answer is Paris.", F, "not JSON"),
    ("detectable_format:json_format", None, '"Paris"', F, "JSON scalar (D-json-scalar)"),
    ("detectable_format:json_format", None, 'Here you go:\n```json\n{"a": 1}\n```', F, "text outside the fence"),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", KW["sec2"], "SECTION 1\nCats are great pets.\nSECTION 2\nDogs are loyal friends.", P, "control"),
    ("detectable_format:multiple_sections", KW["sec2"], "SECTION 1\nCats are great pets.", F, "one section"),
    ("detectable_format:multiple_sections", KW["sec2"], "SECTION 1\nA cat.\nSECTION 2\nA dog.\nSECTION 3\nA bird.", F, "three sections (D-sections-count)"),
    ("detectable_format:multiple_sections", KW["sec2"], "SECTION 1\nCats are great; see SECTION 2 for dogs.", F, "inline mention is not a section marker"),
    ("detectable_format:multiple_sections", KW["sec2"], "Section 1\nCats.\nSection 2\nDogs.", P, "splitter case differs (D-sections-case, v4 proposal: case-insensitive)"),
    ("detectable_format:multiple_sections", KW["sec2"], "## SECTION 1\nCats.\n## SECTION 2\nDogs.", P, "markers as headings"),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", KW["bul2"], "* Apples are red.\n* Bananas are yellow.", P, "control"),
    ("detectable_format:number_bullet_lists", KW["bul2"], "- Apples are red.\n- Bananas are yellow.", P, "dash bullets (D-bullet-dash)"),
    ("detectable_format:number_bullet_lists", KW["bul2"], "* Apples.\n* Bananas.\n* Cherries.", F, "three bullets"),
    ("detectable_format:number_bullet_lists", KW["bul2"], "* Apples.\n* Bananas.\n\n---\n\nThat is all.", P, "a --- divider is not a bullet"),
    ("detectable_format:number_bullet_lists", KW["bul2"], "*Note* the list:\n* Apples.\n* Bananas.", P, "an italic word at line start is not a bullet"),
    ("detectable_format:number_bullet_lists", KW["bul2"], "* Fruits\n  * Apples\n* Vegetables", F, "nested bullet counts (D-bullet-nested)"),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", KW["hl2"], "This is *important* and *urgent*.", P, "control"),
    ("detectable_format:number_highlighted_sections", KW["hl2"], "This is **important** and **urgent**.", P, "bold (D-highlight-bold)"),
    ("detectable_format:number_highlighted_sections", KW["hl2"], "This is *important*.", F, "one highlight"),
    ("detectable_format:number_highlighted_sections", KW["hl2"], "* item one\n* item two", F, "bullets are not highlights"),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", None, "I like cats.-They are cute.-Dogs are fine too.", P, "control (D-hyphen-scope)"),
    ("detectable_format:sentence_hyphens", None, "I like cats. They are cute.", F, "space between sentences"),
    ("detectable_format:sentence_hyphens", None, "I like well-known cats.-They are cute.", P, "hyphen inside a sentence"),
    ("detectable_format:sentence_hyphens", None, "I like cats.- They are cute.", F, "space after hyphen"),
    ("detectable_format:sentence_hyphens", None, "I like cats.", P, "one sentence (D-hyphen-single)"),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", None, "[I] [like] [cats]", P, "control"),
    ("detectable_format:square_brackets", None, "I like cats.", F, "no brackets"),
    ("detectable_format:square_brackets", None, "[I] like cats.", F, "one bracketed word"),
    ("detectable_format:square_brackets", None, "[I] [like] [cats].", P, "final period outside the brackets"),
    ("detectable_format:square_brackets", None, "[I like cats]", F, "several words in one pair (D-brackets-one-word)"),
    # detectable_format:title
    ("detectable_format:title", None, "<<My Day>>\nIt was fine.", P, "control"),
    ("detectable_format:title", None, "My Day\nIt was fine.", F, "no title marker"),
    ("detectable_format:title", None, "<< >>\nIt was fine.", F, "empty title"),
    ("detectable_format:title", None, "It was fine.\n<<My Day>>", P, "title not first (D-title-position)"),
    # first_word:first_word_answer
    ("first_word:first_word_answer", KW["fwa"], "Development is a long process.", P, "control"),
    ("first_word:first_word_answer", KW["fwa"], "Development, as a concept, matters.", P, "comma after the first word"),
    ("first_word:first_word_answer", KW["fwa"], "\"Development\" is the word.", P, "quoted first word"),
    ("first_word:first_word_answer", KW["fwa"], "**Development** is key.", P, "bold first word (D-edge-word)"),
    ("first_word:first_word_answer", KW["fwa"], "The development is slow.", F, "second word"),
    ("first_word:first_word_answer", KW["fwa"], "Developments are slow.", F, "different word"),
    # first_word:first_word_sent
    ("first_word:first_word_sent", KW["fws"], "Peace is good. Peace is calm.", P, "control"),
    ("first_word:first_word_sent", KW["fws"], "Peace is good. War is bad.", F, "second sentence"),
    ("first_word:first_word_sent", KW["fws"], "Peace, they say, is good. Peace is calm.", P, "comma after the first word"),
    ("first_word:first_word_sent", KW["fws"], "Peace notes\nWar is bad.", F, "a line is a sentence (D-sentence)"),
    # keywords:existence
    ("keywords:existence", KW["exist"], "Food and poetry go together.", P, "control"),
    ("keywords:existence", KW["exist"], "Food is good.", F, "poetry missing"),
    ("keywords:existence", KW["exist"], "Seafood and poetry go together.", F, "food only inside seafood (D-keyword-match)"),
    # keywords:forbidden_words
    ("keywords:forbidden_words", KW["forbid"], "I would better draw the line.", P, "only inside other words"),
    ("keywords:forbidden_words", KW["forbid"], "I bet you will win.", F, "forbidden word"),
    ("keywords:forbidden_words", KW["forbid"], "BET on it.", F, "upper case"),
    # keywords:frequency
    ("keywords:frequency", KW["freq"], "A box and another box.", P, "control"),
    ("keywords:frequency", KW["freq"], "One box.", F, "once"),
    ("keywords:frequency", KW["freq"], "A box and a boxer.", F, "boxer is not box (D-keyword-match)"),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", KW["pos"], "I went out. The big shot came home.", P, "control"),
    ("keywords:keyword_specific_position", KW["pos"], "I went out. Then, the shot came.", P, "comma is not a word"),
    ("keywords:keyword_specific_position", KW["pos"], "I went out. The shot came home.", F, "second word"),
    ("keywords:keyword_specific_position", KW["pos1"], "Repeat after me. Good.", P, "capitalized sentence-initial keyword"),
    # keywords:letter_frequency
    ("keywords:letter_frequency", KW["letz"], "Zebras zoom.", P, "upper and lower z"),
    ("keywords:letter_frequency", KW["letz"], "Zebra.", F, "one z"),
    ("keywords:letter_frequency", KW["leta"], "a cat", P, "two a"),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", None, "Tom ate cake.", P, "control"),
    ("keywords:no_adjacent_consecutive", None, "A big dog.", F, "a then b"),
    ("keywords:no_adjacent_consecutive", None, "Big apples.", F, "b then a (D-consecutive-order)"),
    ("keywords:no_adjacent_consecutive", None, "(apple) banana split.", F, "apple then banana behind a parenthesis"),
    ("keywords:no_adjacent_consecutive", None, "Tom ate ate cake.", P, "a repeated word is allowed"),
    # keywords:palindrome
    ("keywords:palindrome", None, "We saw a racecar today.", P, "control"),
    ("keywords:palindrome", None, "We saw a car today.", F, "only the one-letter word a (D-palindrome-length)"),
    ("keywords:palindrome", None, "Big cats run.", F, "no palindrome"),
    ("keywords:palindrome", None, "Cats run - dogs walk.", F, "a hyphen is not a palindrome"),
    ("keywords:palindrome", None, "Cats run.\n\n---\n\nDogs walk.", F, "a --- divider is not a palindrome"),
    ("keywords:palindrome", None, "A man, a plan, a canal: Panama!", P, "phrase palindrome"),
    # keywords:start_end
    ("keywords:start_end", None, "Hello world and hello", P, "control"),
    ("keywords:start_end", None, "Hello world and hello.", F, "punctuation after the last word"),
    ("keywords:start_end", None, "**Hello** world and hello", P, "markup before the first word (D-start-end-leading)"),
    ("keywords:start_end", None, "Hello", P, "one word (D-start-end-one-word)"),
    ("keywords:start_end", None, "Hello world and goodbye", F, "different words"),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", KW["wcd_lt"], "A box and another box.", P, "two times, as the text says"),
    ("keywords:word_count_different_numbers", KW["wcd_lt"], "No crates here.", F, "zero times"),
    ("keywords:word_count_different_numbers", KW["wcd_al"], "A box, a box and a box.", F, "three times (D-bare-count)"),
    ("keywords:word_count_different_numbers", KW["wcd_al"], "A box and another box.", P, "two times"),
    # keywords:word_once
    ("keywords:word_once", KW["once"], "Let me fix it.", P, "control"),
    ("keywords:word_once", KW["once"], "Fix it now and fix it well.", P, "included twice"),
    ("keywords:word_once", KW["once"], "Let me fix the prefix.", P, "included once, plus prefix"),
    ("keywords:word_once", KW["once"], "Let me repair it.", F, "missing"),
    # language:response_language
    ("language:response_language", KW["fr"], "Bonjour, je suis très heureux de vous aider aujourd'hui avec votre question sur la cuisine française.", P, "control"),
    ("language:response_language", KW["fr"], "Hello, I am very happy to help you today with your question about French cuisine.", F, "English"),
    ("language:response_language", KW["fr"], "12345 67890", F, "no French text"),
    ("language:response_language", KW["fr"], "Bonjour, je suis très heureux de vous aider aujourd'hui avec votre question sur la cuisine française et ses traditions.\n\nHowever, I should also tell you in English that the best bread in the whole world is baked in small villages.", F, "a paragraph in English (D-language-mixed)"),
    # last_word:last_word_answer
    ("last_word:last_word_answer", KW["lwa"], "I just want to say hello.", P, "control"),
    ("last_word:last_word_answer", KW["lwa"], "I just want to say **hello**.", P, "bold last word (D-edge-word)"),
    ("last_word:last_word_answer", KW["lwa"], "Hello, I just want to say hi.", F, "first word only"),
    # last_word:last_word_sent
    ("last_word:last_word_sent", KW["lws"], "I know my limit. You know your limit!", P, "control"),
    ("last_word:last_word_sent", KW["lws"], "I know my limit. You know yours.", F, "second sentence"),
    ("last_word:last_word_sent", KW["lws"], "My title\nI know my limit.", F, "a line is a sentence (D-sentence)"),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", KW["nth"], "Cats are nice.\n\nIf you like dogs, fine.", P, "control"),
    ("length_constraints:nth_paragraph_first_word", KW["nth"], "Cats are nice.\n\nDogs are fine.", F, "wrong first word"),
    ("length_constraints:nth_paragraph_first_word", KW["nth"], "Cats are nice.\n\n\n\nIf you like dogs, fine.", P, "four line breaks are one separator (D-paragraph-blank-run)"),
    ("length_constraints:nth_paragraph_first_word", KW["nth"], "Cats are nice.\n\nIf: you like dogs, fine.", P, "colon after the first word"),
    ("length_constraints:nth_paragraph_first_word", KW["nth"], "Cats are nice.\n\n**If** you like dogs, fine.", P, "bold first word (D-edge-word)"),
    ("length_constraints:nth_paragraph_first_word", KW["nth_bad"], "History is long.\n\nHistory is fun.", F, "text asks for paragraph 3 of 2: unsatisfiable"),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", KW["np2"], "Cats are nice.\n***\nDogs are loyal.", P, "control"),
    ("length_constraints:number_paragraphs", KW["np2"], "Cats are nice.\n\nDogs are loyal.", F, "blank line instead of the divider"),
    ("length_constraints:number_paragraphs", KW["np2"], "***Cats*** are nice and dogs are loyal.", F, "bold-italic markup is not a divider"),
    ("length_constraints:number_paragraphs", KW["np2"], "Cats are nice.\n***\nDogs are loyal.\n***", F, "trailing divider (D-divider-edge)"),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", KW["ns3"], "I run. You walk. We talk.", P, "control"),
    ("length_constraints:number_sentences", KW["ns3"], "I run. You walk.", F, "two sentences"),
    ("length_constraints:number_sentences", KW["ns3"], "Dr. Smith runs. You walk.", F, "Dr. does not end a sentence"),
    ("length_constraints:number_sentences", KW["ns3"], "Shopping list\n- eggs\n- milk", P, "three lines (D-sentence)"),
    # length_constraints:number_words
    ("length_constraints:number_words", KW["nw5"], "One two three four five.", P, "control"),
    ("length_constraints:number_words", KW["nw5"], "One two three four.", F, "four words"),
    ("length_constraints:number_words", KW["nw5"], "Привет как дела у тебя", P, "five Russian words"),
    ("length_constraints:number_words", KW["nw5"], "Don't stop me now", F, "four words (D-word)"),
    # letters:letter_counting
    ("letters:letter_counting", KW["lc3"], "No.", P, "two letters"),
    ("letters:letter_counting", KW["lc3"], "Yes.", F, "three letters"),
    ("letters:letter_counting", KW["lc2"], "是的", F, "two letters of another script (D-letters-unit)"),
    # letters:letter_counting2
    ("letters:letter_counting2", KW["letz"], "Zebras zoom.", P, "upper and lower z"),
    ("letters:letter_counting2", KW["letz"], "Zebra.", F, "one z"),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", None, "Cats are nice.\n***\nDogs are loyal.", P, "control"),
    ("paragraphs:paragraphs", None, "Cats are nice.", F, "one paragraph"),
    ("paragraphs:paragraphs", None, "Cats are nice.\n\nDogs are loyal.", F, "blank line instead of the divider"),
    ("paragraphs:paragraphs", None, "Cats.\n***\nDogs.\n***\nBirds.", F, "three paragraphs"),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", None, "Cats are nice.\n\nDogs are loyal.", P, "control"),
    ("paragraphs:paragraphs2", None, "Cats are nice. Dogs are loyal.", F, "one paragraph"),
    ("paragraphs:paragraphs2", None, "Cats.\n\nDogs.\n\nBirds.", F, "three paragraphs"),
    ("paragraphs:paragraphs2", None, "Cats are nice.\n\n\n\nDogs are loyal.", P, "four line breaks (D-paragraph-blank-run)"),
    # punctuation:no_comma
    ("punctuation:no_comma", None, "No commas here.", P, "control"),
    ("punctuation:no_comma", None, "Yes, commas here.", F, "comma"),
    ("punctuation:no_comma", None, "你好，世界", F, "fullwidth comma (D-comma-variants)"),
    # punctuation:punctuation_dot
    ("punctuation:punctuation_dot", None, "No dots here", P, "control"),
    ("punctuation:punctuation_dot", None, "A dot here.", F, "dot"),
    ("punctuation:punctuation_dot", None, "Pi is 3.14 today", F, "dot in a number"),
    ("punctuation:punctuation_dot", None, "你好。", F, "ideographic full stop (D-dot-variants)"),
    # punctuation:punctuation_exclamation
    ("punctuation:punctuation_exclamation", None, "Calm words", P, "control"),
    ("punctuation:punctuation_exclamation", None, "Wow!", F, "exclamation mark"),
    ("punctuation:punctuation_exclamation", None, "哇！", F, "fullwidth exclamation (D-exclamation-variants)"),
    # startend:end_checker
    ("startend:end_checker", KW["end"], "Here is the answer. Any other questions?", P, "control"),
    ("startend:end_checker", KW["end"], "Here is the answer.", F, "no phrase"),
    ("startend:end_checker", KW["end"], "Here is the answer. **Any other questions?**", F, "markup after the phrase (D-end-trailing-markup)"),
    ("startend:end_checker", KW["end"], "\"Here is the answer. Any other questions?\"", F, "quotation mark after the phrase (D-end-trailing-markup)"),
    ("startend:end_checker", KW["end"], "Here is the answer. any other questions?", P, "case differs (D-end-case, v4 proposal: case-insensitive)"),
    ("startend:end_checker", KW["end"], "Any other questions? Bye.", F, "words after the phrase"),
    # startend:quotation
    ("startend:quotation", None, "\"Hello there.\"", P, "control"),
    ("startend:quotation", None, "Hello there.", F, "no quotes"),
    ("startend:quotation", None, "“Hello there.”", P, "typographic quotes (D-quotation-typographic)"),
    ("startend:quotation", None, "'Hello there.'", F, "single quotes"),
    ("startend:quotation", None, "\"Hello there.\"\n", P, "trailing newline (D-strip)"),
]

# Pipeline (graded-text extraction) fixtures: (instruction_id, kwargs, raw response, reasoning_model, label, note)
EXTRACTION_FIXTURES = [
    ("punctuation:no_comma", None, "Okay the user wants a short answer so I will think about it", True, F,
     "reasoning model, reasoning never closed: extraction failure"),
    ("keywords:existence", {"keywords": ["tag"]}, "Write the <think> tag before your notes.", False, P,
     "non-reasoning answer that mentions a <think> tag"),
    ("keywords:existence", {"keywords": ["tag"]}, "Some reasoning.</think>\n\nUse a tag here.", True, P,
     "control: closed reasoning"),
]
