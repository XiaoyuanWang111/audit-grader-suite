"""Hand-written fixtures, each labeled from audit/contracts.md alone (proposed readings).

Fields: iid, kw, response, label ("pass"/"fail"), optional prompt (the requirement text
as the prompt shows it, when the contract depends on it), optional raw=True with
reasoning_model (the response is the model's raw text and goes through each pipeline's
extraction), note (why the label holds).
"""

PS_SHOWN_WITHOUT_PERIOD = (
    "Please ensure your answer follows these guidelines: In your entire response, refrain from the use of any "
    "commas and At the end of your response, please explicitly add a postscript starting with P.S"
)


def F(iid, kw, response, label, note="", **extra):
    d = {"iid": iid, "kw": kw, "response": response, "label": label, "note": note}
    d.update(extra)
    return d


CW = "change_case:capital_word_frequency"
EC = "change_case:english_capital"
EL = "change_case:english_lowercase"
TR = "combination:two_responses"
RP = "copy:repeat_phrase"
CU = "count:count_unique"
CC = "count:counting_composition"
LC = "count:lowercase_counting"
NP = "detectable_content:number_placeholders"
PS = "detectable_content:postscript"
BW = "detectable_format:bigram_wrapping"
CR = "detectable_format:constrained_response"
JS = "detectable_format:json_format"
MS = "detectable_format:multiple_sections"
BL = "detectable_format:number_bullet_lists"
HS = "detectable_format:number_highlighted_sections"
SH = "detectable_format:sentence_hyphens"
SB = "detectable_format:square_brackets"
TI = "detectable_format:title"
FA = "first_word:first_word_answer"
FS = "first_word:first_word_sent"
KE = "keywords:existence"
KF = "keywords:forbidden_words"
KQ = "keywords:frequency"
KP = "keywords:keyword_specific_position"
LF = "keywords:letter_frequency"
NA = "keywords:no_adjacent_consecutive"
PA = "keywords:palindrome"
SE = "keywords:start_end"
WD = "keywords:word_count_different_numbers"
WO = "keywords:word_once"
RL = "language:response_language"
LA = "last_word:last_word_answer"
LS = "last_word:last_word_sent"
NF = "length_constraints:nth_paragraph_first_word"
NPG = "length_constraints:number_paragraphs"
NS = "length_constraints:number_sentences"
NW = "length_constraints:number_words"
LTC = "letters:letter_counting"
LT2 = "letters:letter_counting2"
P1 = "paragraphs:paragraphs"
P2 = "paragraphs:paragraphs2"
NC = "punctuation:no_comma"
ND = "punctuation:punctuation_dot"
NE = "punctuation:punctuation_exclamation"
EN = "startend:end_checker"
QU = "startend:quotation"

AT2 = {"capital_relation": "at least", "capital_frequency": 2}
LT2_ = {"capital_relation": "less than", "capital_frequency": 2}
PHR = {"phrase": "Live each day to the fullest", "small_n": 2}
SEC = {"num_sections": 2, "section_spliter": "SECTION"}
NFK = {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "home"}

FIXTURES = [
    # change_case:capital_word_frequency
    F(CW, AT2, "NASA and the FBI met today.", "pass", "NASA, FBI: 2 >= 2"),
    F(CW, AT2, "NASA met today.", "fail", "1 all-capital word"),
    F(CW, LT2_, "I think NASA is great.", "fail", "I and NASA: 2, not < 2 (I counts)"),
    F(CW, AT2, "**NASA** and (FBI) agents.", "pass", "markup and brackets do not change the words"),
    F(CW, {"capital_relation": "less than", "capital_frequency": 3}, "COVID-19 hit NASA hard.", "pass", "2 < 3"),
    # change_case:english_capital
    F(EC, {}, "THIS IS MY ANSWER IN ENGLISH.", "pass"),
    F(EC, {}, "This is my answer in English.", "fail", "lower-case letters"),
    F(EC, {}, "ESTO ES MI RESPUESTA EN ESPAÑOL Y NO EN INGLÉS PORQUE ASÍ LO QUIERO.", "fail", "not English"),
    F(EC, {}, "", "fail", "empty response is not in English"),
    F(EC, {}, "THE RESULT IS 42 (SEE TABLE 3 IN THE REPORT).", "pass"),
    # change_case:english_lowercase
    F(EL, {}, "this is my answer in english, written for you.", "pass"),
    F(EL, {}, "this is my answer in English.", "fail", "capital E"),
    F(EL, {}, "esta es mi respuesta en español y no en inglés porque así lo quiero.", "fail", "not English"),
    F(EL, {}, "", "fail", "empty response is not in English"),
    # combination:two_responses
    F(TR, {}, "Paris is the capital of France.\n******\nThe capital of France is Paris.", "pass"),
    F(TR, {}, "Paris is the capital.\n******\nParis is the capital.", "fail", "identical responses"),
    F(TR, {}, "Answer one.\n*******\nAnswer two.", "fail", "seven asterisks, not six"),
    F(TR, {}, "Answer one.\n******\nAnswer two.\n******\nAnswer three.", "fail", "three responses"),
    F(TR, {}, "Answer one. Answer two.", "fail", "no separator"),
    F(TR, {}, "******\nAnswer one.\n******\nAnswer two.", "fail", "two separators; the first separates nothing"),
    # copy:repeat_phrase
    F(RP, PHR, "Live each moment to the fullest. Live each day for the fullest.", "pass", "two one-word changes of a middle word"),
    F(RP, PHR, "Live each moment to the fullest. Live each day to their fullest.", "pass", "two one-word inner changes"),
    F(RP, PHR, "Live each day to the fullest. Live each moment to the fullest.", "fail",
      "one unchanged copy and one transformed: only 1 transformed repetition"),
    F(RP, PHR, "Live each moment to the fullest. Live every moment to the fullest.", "fail",
      "second changes two words: 1 valid repetition"),
    F(RP, PHR, "Live each moment to the fullest. Live each day to their fullest. Live each hour to the fullest.",
      "fail", "three repetitions, not two"),
    F(RP, PHR, "live each hour to the fullest! Live each week to the fullest", "pass",
      "letter case of the first word does not change it (G4)"),
    F(RP, PHR, "Live each moment to the fullest\nLive each day to their fullest", "pass"),
    F(RP, PHR, "Live each day to the fullest.", "fail", "one unchanged copy"),
    # count:count_unique
    F(CU, {}, "Every word here differs.", "pass"),
    F(CU, {}, "The cat saw the dog.", "fail", "The/the repeated"),
    F(CU, {}, "Apples, pears, plums.", "pass", "commas are not words"),
    F(CU, {}, "I like it, I do.", "fail", "I twice"),
    # count:counting_composition
    F(CC, {"n_sent": 3, "n_words": 2},
      "Cats sleep. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs jump. Bees buzz.\n* * *\nKids play. Adults work. Elders rest.",
      "pass"),
    F(CC, {"n_sent": 3, "n_words": 2},
      "Cats sleep. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs jump. Bees buzz.", "fail", "two paragraphs"),
    F(CC, {"n_sent": 3, "n_words": 2},
      "Cats sleep. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs jump high. Bees buzz.\n* * *\nKids play. Adults work. Elders rest.",
      "fail", "a three-word sentence"),
    # count:lowercase_counting
    F(LC, {"N": 2}, "Big cats and big dogs.", "pass", "each lower-case word at most twice"),
    F(LC, {"N": 2}, "the the the end", "fail", "the three times"),
    F(LC, {"N": 2}, "ALL CAPS HERE.", "pass"),
    # detectable_content:number_placeholders
    F(NP, {"num_placeholders": 2}, "Dear [name], your order [order_id] shipped.", "pass"),
    F(NP, {"num_placeholders": 2}, "Dear [name], your order shipped.", "fail"),
    F(NP, {"num_placeholders": 2}, "Dear [], your order [ ] shipped.", "fail", "empty brackets are not placeholders"),
    F(NP, {"num_placeholders": 2}, "See [the docs](http://example.com) and [name].", "pass", "link text counts (D-placeholder)"),
    # detectable_content:postscript
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading.\n\nP.S. Remember to rest.", "pass"),
    F(PS, {"postscript_marker": "P.S."}, "P.S. Remember to rest.\n\nThanks for reading, and see the plan above.", "fail",
      "the postscript is not at the end"),
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading, and remember the P.S. rule from class.", "fail",
      "no postscript: the marker is inside a sentence"),
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading.\n\n**P.S.** Remember to rest.", "pass"),
    F(PS, {"postscript_marker": "P.S."}, "Thanks.\n\np.s. remember to rest.", "pass", "D-postscript-case"),
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading.\n\nP.S: Remember to rest.", "pass",
      "the prompt shows the marker as P.S", prompt=PS_SHOWN_WITHOUT_PERIOD),
    F(PS, {"postscript_marker": "P.P.S"}, "Thanks.\n\nP.P.S. Remember to rest.", "pass"),
    F(PS, {"postscript_marker": "P.P.S"}, "Thanks.\n\nP.S. Remember to rest.", "fail", "P.S. is not P.P.S"),
    # detectable_format:bigram_wrapping
    F(BW, {}, "<<I am>> <<at home>> <<with my>> <<cute dog>>", "pass"),
    F(BW, {}, "<<I am at>> <<home now>>", "fail", "a group of three words"),
    F(BW, {}, "I am <<at home>>", "fail", "words outside groups"),
    F(BW, {}, "<<I am>> <<at home>> <<now>>", "pass", "odd final word alone (D-bigram-odd)"),
    F(BW, {}, "<<I am>> <<at home>>.", "pass", "a period after the last group is not a word"),
    # detectable_format:constrained_response
    F(CR, {}, "My answer is yes.", "pass"),
    F(CR, {}, "My answer is yes. The data clearly supports it.", "pass", "D-constrained-extra"),
    F(CR, {}, "My answer is yes. My answer is no.", "fail", "two different options"),
    F(CR, {}, "Yes.", "fail"),
    # detectable_format:json_format
    F(JS, {}, '{"a": 1}', "pass"),
    F(JS, {}, '```json\n{"a": 1}\n```', "pass"),
    F(JS, {}, 'Here is the JSON:\n```json\n{"a": 1}\n```', "fail", "text outside the JSON"),
    F(JS, {}, '"just a string"', "pass", "D-json-scalar"),
    F(JS, {}, '```JSON\n{"a": 1}\n```', "pass", "a fence with a language tag"),
    F(JS, {}, '{"a": 1}\n{"b": 2}', "fail", "two JSON values"),
    # detectable_format:multiple_sections
    F(MS, SEC, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", "pass"),
    F(MS, SEC, "SECTION 1\nIntro.\nSECTION 2\nMore.\nSECTION 3\nEven more.", "fail", "three sections, not two"),
    F(MS, SEC, "Section 1\nIntro.\nSection 2\nMore.", "pass", "D-section-case"),
    F(MS, SEC, "## SECTION 1\nIntro.\n## SECTION 2\nMore.", "pass", "D-section-markup"),
    F(MS, SEC, "SECTION 1\nIntro, as SECTION 2 explains later.\nSECTION 2\nMore.", "pass",
      "a mention mid-sentence is not a header"),
    F(MS, SEC, "SECTION 1\nOnly one section here.", "fail"),
    # detectable_format:number_bullet_lists
    F(BL, {"num_bullets": 3}, "* one\n* two\n* three", "pass"),
    F(BL, {"num_bullets": 3}, "- one\n- two\n- three", "pass", "D-bullet-markers"),
    F(BL, {"num_bullets": 3}, "* one\n* two", "fail"),
    F(BL, {"num_bullets": 3}, "* one\n* two\n* three\n\n---\nDone.", "pass", "--- is a horizontal rule, not a bullet"),
    F(BL, {"num_bullets": 3}, "**Note:** intro\n* one\n* two\n* three", "pass", "a bold line is not a bullet"),
    F(BL, {"num_bullets": 3}, "1. one\n2. two\n3. three", "fail", "numbered items are not bullet points"),
    F(BL, {"num_bullets": 3}, "* one\n  * sub\n* two", "pass", "nested bullets count (D-bullet-nested)"),
    F(BL, {"num_bullets": 3}, "+ one\n+ two\n+ three", "pass", "D-bullet-markers"),
    F(BL, {"num_bullets": 3}, "* one\n* two\n* three\n\n* * *\n\nDone.", "pass", "* * * is a horizontal rule, not a bullet"),
    F(BL, {"num_bullets": 3}, "* one\n* two\n* three\n-5 degrees is cold.", "pass",
      "a line starting with a negative number is not a bullet"),
    # detectable_format:number_highlighted_sections
    F(HS, {"num_highlights": 2}, "This is *important* and *urgent*.", "pass"),
    F(HS, {"num_highlights": 2}, "This is *important* only.", "fail"),
    F(HS, {"num_highlights": 2}, "This is **important** and **urgent**.", "pass", "D-highlight-bold"),
    F(HS, {"num_highlights": 1}, "Compute 2 * 3 * 4 here.", "fail", "multiplication signs are not a highlight"),
    F(HS, {"num_highlights": 1}, "* item one\n* item two", "fail", "bullet markers are not highlights"),
    # detectable_format:sentence_hyphens
    F(SH, {}, "The sun rose.-Birds sang.-We woke.", "pass"),
    F(SH, {}, "The sun rose. Birds sang. We woke.", "fail"),
    F(SH, {}, "The sun rose. - Birds sang.", "fail", "spaces around the hyphen"),
    F(SH, {}, "The well-known sun rose.-Birds sang.", "pass", "a hyphen inside a word is allowed"),
    F(SH, {}, "The sun rose.", "pass", "one sentence (D-hyphen-single)"),
    # detectable_format:square_brackets
    F(SB, {}, "[Hello] [world]", "pass"),
    F(SB, {}, "[Hello] world", "fail"),
    F(SB, {}, "[Hello] [world].", "pass", "punctuation outside the brackets is not a word"),
    F(SB, {}, "[Hello world]", "fail", "D-bracket-group"),
    F(SB, {}, "Hello [world]", "fail"),
    # detectable_format:title
    F(TI, {}, "<<My Poem>>\nRoses are red.", "pass"),
    F(TI, {}, "My Poem\nRoses are red.", "fail"),
    F(TI, {}, "<< >>\nRoses are red.", "fail", "empty title"),
    F(TI, {}, "Roses are red.\n<<My Poem>>", "pass", "D-title-position"),
    # first_word:first_word_answer
    F(FA, {"first_word": "development"}, "Development is key.", "pass"),
    F(FA, {"first_word": "development"}, "development, as a concept, matters.", "pass", "the comma is not part of the word"),
    F(FA, {"first_word": "development"}, "**Development** matters.", "pass", "D-markup-transparent"),
    F(FA, {"first_word": "development"}, "Growth matters.", "fail"),
    F(FA, {"first_word": "development"}, "Developmental work matters.", "fail"),
    F(FA, {"first_word": "development"}, "development: a summary.", "pass", "the colon is not part of the word"),
    # first_word:first_word_sent
    F(FS, {"first_word": "we"}, "We run. We jump.", "pass"),
    F(FS, {"first_word": "we"}, "We run. They jump.", "fail"),
    F(FS, {"first_word": "we"}, "we, the people, run. we jump!", "pass", "the comma is not part of the word"),
    F(FS, {"first_word": "we"}, "we run\nthey jump", "fail", "two lines are two sentences (D-sentence-lines)"),
    F(FS, {"first_word": "we"}, "We run.\nThey jump", "fail"),
    F(FS, {"first_word": "we"}, "1. We run.\n2. We jump.", "pass", "list labels are not sentences (D-list-label)"),
    # keywords:existence
    F(KE, {"keywords": ["river", "stone"]}, "A river ran past a stone.", "pass"),
    F(KE, {"keywords": ["river", "stone"]}, "A river ran past.", "fail"),
    F(KE, {"keywords": ["river", "stone"]}, "The RIVER hit a Stone.", "pass"),
    F(KE, {"keywords": ["river", "stone"]}, "A riverbank and a milestone.", "fail", "only inside longer words"),
    # keywords:forbidden_words
    F(KF, {"forbidden_words": ["floor", "wheel"]}, "The car moved.", "pass"),
    F(KF, {"forbidden_words": ["floor", "wheel"]}, "The wheel turned.", "fail"),
    F(KF, {"forbidden_words": ["floor", "wheel"]}, "The Wheel turned.", "fail"),
    F(KF, {"forbidden_words": ["floor", "wheel"]}, "He used a wheelchair on the floorboards.", "pass",
      "only inside longer words"),
    # keywords:frequency
    F(KQ, {"keyword": "data", "relation": "at least", "frequency": 2}, "Data matters. More data helps.", "pass"),
    F(KQ, {"keyword": "data", "relation": "at least", "frequency": 2}, "Data matters.", "fail"),
    F(KQ, {"keyword": "data", "relation": "less than", "frequency": 2}, "Our database stores data.", "pass",
      "one whole-word occurrence"),
    # keywords:keyword_specific_position
    F(KP, {"keyword": "main", "n": 2, "m": 3}, "First sentence here. The very main point.", "pass"),
    F(KP, {"keyword": "main", "n": 2, "m": 3}, "First sentence here. The main point.", "fail"),
    F(KP, {"keyword": "main", "n": 2, "m": 3}, "First sentence here. The very Main point.", "pass", "G4 case"),
    F(KP, {"keyword": "main", "n": 2, "m": 3}, "First, sentence here. Yes, the main point.", "pass",
      "commas are not words: Yes the main"),
    # keywords:letter_frequency
    F(LF, {"letter": "m", "let_relation": "less than", "let_frequency": 3}, "Mom made jam.", "fail", "4 m's"),
    F(LF, {"letter": "m", "let_relation": "less than", "let_frequency": 3}, "A cat sat.", "pass"),
    F(LF, {"letter": "m", "let_relation": "at least", "let_frequency": 2}, "Mmm.", "pass"),
    # keywords:no_adjacent_consecutive
    F(NA, {}, "Cats like fish.", "pass"),
    F(NA, {}, "Apple banana cherry.", "fail"),
    F(NA, {}, "Banana apple.", "fail", "b then a (D-consecutive-order)"),
    F(NA, {}, "Steps 1 2 3 follow.", "pass", "digits are not letters of the alphabet"),
    F(NA, {}, "**Apple** banana.", "fail", "markup does not change the first letter"),
    # keywords:palindrome
    F(PA, {}, "We saw a racecar today.", "pass"),
    F(PA, {}, "We saw a car today.", "fail", "no palindrome of 3+ letters (D-palindrome-length)"),
    F(PA, {}, "Level heads prevail.", "pass", "Level reads the same backwards ignoring case"),
    F(PA, {}, "Wow, that is great.", "pass", "the comma is not part of the word"),
    F(PA, {}, "It costs five dollars - not much.", "fail", "a dash is not a palindrome word"),
    # keywords:start_end
    F(SE, {}, "Hello there, I say hello", "pass"),
    F(SE, {}, "Hello there, I say hello.", "fail", "punctuation after the last word"),
    F(SE, {}, "Hello there, I say goodbye", "fail"),
    F(SE, {}, "**Hello** there, I say hello", "pass", "leading markup (D-markup-transparent)"),
    F(SE, {}, "Hello", "pass", "D-start-end-single"),
    # keywords:word_count_different_numbers (the text says "should appear N times")
    F(WD, {"keyword": "tree", "relation": "less than", "frequency": 2}, "A tree and another tree.", "pass",
      "exactly 2, as the text asks"),
    F(WD, {"keyword": "tree", "relation": "less than", "frequency": 2}, "A tree here.", "fail", "1, not 2"),
    F(WD, {"keyword": "tree", "relation": "at least", "frequency": 2}, "A tree, a tree, a tree.", "fail", "3, not 2"),
    # keywords:word_once ("Include keyword X in your response.")
    F(WO, {"keyword": "garden"}, "The garden is green.", "pass"),
    F(WO, {"keyword": "garden"}, "The garden is green. I love the garden.", "pass", "included (twice)"),
    F(WO, {"keyword": "garden"}, "The yard is green.", "fail"),
    F(WO, {"keyword": "garden"}, "The gardens are green.", "fail", "only inside a longer word"),
    # language:response_language
    F(RL, {"language": "fr"}, "Bonjour, je suis très heureux de vous aider aujourd'hui avec cette question difficile.", "pass"),
    F(RL, {"language": "fr"}, "Hello, I am very happy to help you today with this difficult question.", "fail"),
    F(RL, {"language": "fr"}, "", "fail", "an empty response is in no language"),
    F(RL, {"language": "ko"}, "안녕하세요. 오늘 무엇을 도와드릴까요? 질문이 있으면 말씀해 주세요.", "pass"),
    # last_word:last_word_answer
    F(LA, {"last_word": "limit"}, "We reached the limit.", "pass"),
    F(LA, {"last_word": "limit"}, "We reached the Limit!", "pass"),
    F(LA, {"last_word": "limit"}, "We reached the limits.", "fail"),
    F(LA, {"last_word": "limit"}, "We reached the **limit**.", "pass"),
    F(LA, {"last_word": "limit"}, "", "fail", "empty response"),
    # last_word:last_word_sent
    F(LS, {"last_word": "limit"}, "We hit the limit. They passed the limit!", "pass"),
    F(LS, {"last_word": "limit"}, "We hit the limit. They passed it.", "fail"),
    F(LS, {"last_word": "limit"}, "We hit the limit; they knew the limit.", "pass", "one sentence"),
    # length_constraints:nth_paragraph_first_word
    F(NF, NFK, "Intro text.\n\nHome is where we live.", "pass"),
    F(NF, NFK, "Intro text.\n\nAway from home.", "fail"),
    F(NF, NFK, "Intro text.\nHome is where we live.", "fail", "one paragraph"),
    F(NF, NFK, "Intro text.\n\n\n\nHome is where we live.", "pass", "D-paragraph-blank-lines"),
    F(NF, NFK, "Intro text.\n\nhome: where we live.", "pass", "the colon is not part of the word"),
    F(NF, NFK, "Intro text.\n\n**Home** is where we live.", "pass", "D-markup-transparent"),
    F(NF, NFK, "Intro text.\n \nHome is where we live.", "pass", "a blank line holding a space (G7)"),
    # length_constraints:number_paragraphs
    F(NPG, {"num_paragraphs": 2}, "First paragraph.\n\n***\n\nSecond paragraph.", "pass"),
    F(NPG, {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", "pass"),
    F(NPG, {"num_paragraphs": 2}, "First paragraph.\n\nSecond paragraph.", "fail", "no divider"),
    F(NPG, {"num_paragraphs": 2}, "First.\n***\nSecond.\n***\nThird.", "fail"),
    F(NPG, {"num_paragraphs": 2}, "This is ***very*** important.\n***\nSecond paragraph.", "pass", "D-divider-line"),
    F(NPG, {"num_paragraphs": 2}, "***\nFirst.\n***\nSecond.", "fail", "an empty first piece (D-divider-empty)"),
    # length_constraints:number_sentences
    F(NS, {"relation": "at least", "num_sentences": 3}, "One. Two. Three.", "pass"),
    F(NS, {"relation": "at least", "num_sentences": 3}, "One. Two.", "fail"),
    F(NS, {"relation": "less than", "num_sentences": 3}, "Dr. Smith arrived. He sat.", "pass"),
    F(NS, {"relation": "at least", "num_sentences": 3}, "# Title\nFirst line\nSecond line", "pass", "D-sentence-lines"),
    # length_constraints:number_words
    F(NW, {"relation": "less than", "num_words": 5}, "One two three four.", "pass"),
    F(NW, {"relation": "less than", "num_words": 5}, "One two three four five.", "fail"),
    F(NW, {"relation": "less than", "num_words": 3}, "Don't stop.", "pass", "a contraction is one word"),
    F(NW, {"relation": "at least", "num_words": 5}, "我们 今天 去 公园 玩。", "pass", "five space-separated words of another script"),
    # letters:letter_counting
    F(LTC, {"relation": "less than", "N": 3}, "OK", "pass"),
    F(LTC, {"relation": "less than", "N": 3}, "Yes", "fail"),
    F(LTC, {"relation": "at least", "N": 2}, "是的", "pass", "two letters of another script (D-letter-def)"),
    # letters:letter_counting2
    F(LT2, {"letter": "r", "let_relation": "at least", "let_frequency": 2}, "Red roses.", "pass"),
    F(LT2, {"letter": "r", "let_relation": "at least", "let_frequency": 2}, "A rose.", "fail"),
    # paragraphs:paragraphs
    F(P1, {}, "First paragraph.\n***\nSecond paragraph.", "pass"),
    F(P1, {}, "First paragraph.\n\nSecond paragraph.", "fail", "no divider"),
    F(P1, {}, "One.\n***\nTwo.\n***\nThree.", "fail", "three paragraphs"),
    # paragraphs:paragraphs2
    F(P2, {}, "First paragraph.\n\nSecond paragraph.", "pass"),
    F(P2, {}, "First paragraph.\nSecond paragraph.", "fail"),
    F(P2, {}, "One.\n\nTwo.\n\nThree.", "fail", "three paragraphs"),
    # punctuation:no_comma
    F(NC, {}, "No commas here.", "pass"),
    F(NC, {}, "Yes, commas.", "fail"),
    F(NC, {}, "中文，逗号", "fail", "a full-width comma (D-comma-unicode)"),
    # punctuation:punctuation_dot
    F(ND, {}, "No dots here", "pass"),
    F(ND, {}, "Version 2.0 is out", "fail"),
    F(ND, {}, "Wait… what", "fail", "an ellipsis character (D-dot-unicode)"),
    F(ND, {}, "这是句子。", "pass", "the ideographic full stop is not a dot"),
    # punctuation:punctuation_exclamation
    F(NE, {}, "Calm text.", "pass"),
    F(NE, {}, "Wow!", "fail"),
    F(NE, {}, "好！", "fail", "a full-width exclamation mark (D-exclamation-unicode)"),
    # startend:end_checker
    F(EN, {"end_phrase": "Any other questions?"}, "Here is the answer. Any other questions?", "pass"),
    F(EN, {"end_phrase": "Any other questions?"}, "Here is the answer. Any other questions? Thanks.", "fail"),
    F(EN, {"end_phrase": "Any other questions?"}, "Here is the answer. any other questions?", "fail", "D-end-case"),
    F(EN, {"end_phrase": "Any other questions?"}, "Here is the answer. **Any other questions?**", "fail", "D-end-trailing"),
    F(EN, {"end_phrase": "Any other questions?"}, '"Here is the answer. Any other questions?"', "fail", "D-end-trailing"),
    # startend:quotation
    F(QU, {}, '"Hello world."', "pass"),
    F(QU, {}, "Hello world.", "fail"),
    F(QU, {}, "“Hello world.”", "pass", "D-quotation-typographic"),
    F(QU, {}, "'Hello world.'", "fail", "single quotation marks"),
    # extraction (raw model text; G1)
    F(NC, {}, "<think>Reasoning, with commas.</think>A final answer without them.", "pass",
      "graded text is after </think>", raw=True, reasoning_model=True),
    F(NC, {}, "Okay let me think about this answer and plan it", "fail",
      "reasoning never closed: extraction failure (template-supplied <think>)", raw=True, reasoning_model=True),
    F(NC, {}, "<think>Okay let me think about this answer and plan it", "fail",
      "reasoning never closed: extraction failure", raw=True, reasoning_model=True),
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading. P.S. Remember to rest.", "pass",
      "the postscript starts after the last sentence, on the same line (D-postscript-line)"),
    F(PS, {"postscript_marker": "P.S."}, "Thanks for reading.\n\nP.P.S. Remember to rest.", "fail",
      "P.P.S. is not a postscript starting with P.S."),
    F(NA, {}, "Апельсин банан.", "fail",
      "Cyrillic a then b (D-consecutive-script)"),
    F(SH, {}, "The sun rose - birds sang - we woke", "fail", "hyphens with spaces"),
    F(NW, {"relation": "less than", "num_words": 3}, "नमस्ते दोस्त", "pass",
      "two Hindi words; vowel signs belong to their word"),
    F(TI, {}, "<<think>>\nA short poem about thought.", "pass",
      "a non-reasoning model's whole response is the answer; it has a title", raw=True, reasoning_model=False),
    F(NC, {}, "I <<think>> this works, yes.", "fail",
      "a non-reasoning model's whole response is the answer; it has commas", raw=True, reasoning_model=False),
]

# Smallest reproducing responses from audit/scripts/fuzz.py (seed 20261112), each label checked by
# hand against the contract before it was added here.
FUZZ = [
    F(CU, {}, "… …", "pass", "no words at all, so no word is repeated"),
    F(CU, {}, "Is is", "fail", "is repeated (D-unique-case)"),
    F(NP, {"num_placeholders": 1}, "[]", "fail", "empty brackets are not a placeholder"),
    F(PS, {"postscript_marker": "P.S."}, ",P.S.", "fail", "no line starts with the marker"),
    F(TR, {}, "We\n******\n*\n******\n", "fail", "two separators"),
    F(FA, {"first_word": "emergency"}, "emergency,", "pass", "the comma is not part of the word"),
    F(FS, {"first_word": "emotion"}, "emotion]", "pass", "the bracket is not part of the word"),
    F(PA, {}, ":", "fail", "a colon is not a palindrome word"),
    F(SE, {}, ">>", "fail", "no word"),
    F(WO, {"keyword": "heart"}, "heart\n******\nheart", "pass", "the keyword is included"),
    F(LA, {"last_word": "newspaper"}, "", "fail", "empty response (SkyRL raises IndexError)"),
    F(LTC, {"N": 3, "relation": "at least"}, "Привет", "pass", "six Cyrillic letters (D-letter-def)"),
    F(NA, {}, "don't don't", "pass", "d and d are not consecutive letters"),
    F(PA, {}, "'level", "pass", "level, after a leading apostrophe"),
    F(LA, {"last_word": "discussion"}, "discussion<b>", "pass", "an HTML tag is markup (D-markup-transparent)"),
    F(NPG, {"num_paragraphs": 1}, "NASA\n\n\nWe", "pass", "no *** divider: one paragraph"),
    F(P2, {}, "answer\n***\nsuccess", "fail", "no blank line: one paragraph"),
]
for _f in FUZZ:
    _f["source"] = "fuzz"
FIXTURES = FIXTURES + FUZZ
