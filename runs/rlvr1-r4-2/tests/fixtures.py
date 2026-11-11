"""Labeled fixtures, written from audit/CONTRACTS.md (version 2) alone.

Each fixture: check id, kwargs, graded text, label under the proposed readings, and `flip`: the
decision entries whose alternative reading would flip the label. `wrong` maps a grader ("A" SkyRL
reward with NVIDIA's checkers, "B" task-curation gate with verifyit's checks) to the finding or
decision id that explains its wrong verdict; the tests mark those `xfail(strict=True)`. `ctx` holds
row context the contract needs (the postscript marker as the prompt shows it).

Fixture id: the check's family (text before the colon) plus the first 12 hex digits of the sha256
of the check id, kwargs and response.
"""

import hashlib
import json

FIXTURES = []


def F(check, kwargs, response, label, flip=(), wrong=None, ctx=None, note="", finding=None):
    """`finding` names the finding a wrong verdict shows when the check has more than one."""
    key = json.dumps([check, kwargs, response], ensure_ascii=False, sort_keys=True)
    fid = check.split(":")[0] + "-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    FIXTURES.append({"id": fid, "check": check, "kwargs": kwargs, "response": response, "label": label,
                     "flip": tuple(flip), "wrong": dict(wrong or {}), "ctx": dict(ctx or {}), "note": note,
                     "finding": dict(finding or {})})


# change_case:capital_word_frequency
C = "change_case:capital_word_frequency"
F(C, {"capital_frequency": 3, "capital_relation": "at least"}, "The USA and NASA work with the EU.", True)
F(C, {"capital_frequency": 3, "capital_relation": "at least"}, "The USA and NASA work together.", False)
F(C, {"capital_frequency": 1, "capital_relation": "less than"}, "Nothing shouty here.", True)
F(C, {"capital_frequency": 2, "capital_relation": "less than"}, "I think NASA is great.", False, flip=["D-allcaps-single"])

# change_case:english_capital
C = "change_case:english_capital"
F(C, None, "HELLO WORLD, THIS IS AN ANSWER IN ENGLISH ABOUT THE WEATHER TODAY.", True)
F(C, None, "HELLO World, this is mixed case text in English.", False)
F(C, None, "BONJOUR TOUT LE MONDE, COMMENT ALLEZ-VOUS AUJOURD'HUI? JE VAIS TRES BIEN, MERCI BEAUCOUP.", False, flip=["D-english"])
F(C, None, "你好世界，这是一个中文回答。", False)

# change_case:english_lowercase
C = "change_case:english_lowercase"
F(C, None, "hello world, this is an answer in english about the weather today.", True)
F(C, None, "hello World, this is mixed case text in english.", False)
F(C, None, "bonjour tout le monde, comment allez-vous aujourd'hui? je vais tres bien, merci beaucoup.", False, flip=["D-english"])

# combination:two_responses
C = "combination:two_responses"
F(C, None, "Response one is short.\n******\nResponse two is different.", True)
F(C, None, "Same text.\n******\nSame text.", False)
F(C, None, "One.\n******\nTwo.\n******\nThree.", False)
F(C, None, "One.\n*****\nTwo.", False)
F(C, None, "One.\n*******\nTwo.", False, note="seven asterisks are not the six-asterisk separator")

# copy:repeat_phrase
C = "copy:repeat_phrase"
G6 = {"phrase": "All that glitters is not gold", "small_n": 2}
F(C, G6, "All that shines is not gold\nAll that sparkles is not gold", True)
F(C, G6, "All that glitters is not gold\nAll that glitters is not gold", False)
F(C, G6, "All that shines is not gold\nAll that sparkles is not gold\nAll that gleams is not gold", False)
F(C, {"phrase": "Laughter is the best medicine", "small_n": 2},
  "Laughter is the finest medicine\nLaughter is the greatest medicine", False, flip=["D-repeat-center"])
F(C, {"phrase": "All that glitters is not gold", "small_n": 3},
  "All that glitters is not gold\nAll that glitters is not gold\nAll that shines is not gold", False)
F(C, G6, "All variations: All that shines is not gold; All that sparkles is not gold.", True)
F(C, G6, "all that shines is not gold\nall that sparkles is not gold", True, flip=["D-word-case"])
F(C, G6, "The phrase is All that glitters is not gold.\nAll that shines is not gold\nAll that sparkles is not gold", True,
  flip=["D-repeat-original"])

# count:count_unique (grader A only)
C = "count:count_unique"
F(C, None, "Every word here is different.", True)
F(C, None, "The cat saw the dog.", False, flip=["D-word-case"])
F(C, None, "Apples, pears, plums.", True)
F(C, None, "red red", False)

# count:counting_composition
C = "count:counting_composition"
K = {"n_sent": 3, "n_words": 2}
F(C, K, "Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Moms smile. Dads cook.", True)
F(C, K, "Birds sing. Cats sleep. Dogs run.", False)
F(C, K, "Birds sing loudly. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Moms smile. Dads cook.", False)

# count:lowercase_counting
C = "count:lowercase_counting"
F(C, {"N": 2}, "The Cat Sat On A Mat, and then left.", True, flip=["D-lowercase-counting"])
F(C, {"N": 2}, "Big Red Dog and cat.", True)
F(C, {"N": 2}, "the the the end", False)
F(C, {"N": 2}, "ALL CAPS ONLY.", True)

# detectable_content:number_placeholders
C = "detectable_content:number_placeholders"
F(C, {"num_placeholders": 2}, "Dear [name], see you at [address].", True)
F(C, {"num_placeholders": 2}, "Dear [name], see you soon.", False)
F(C, {"num_placeholders": 2}, "Dear [], see you at [ ].", False)
F(C, {"num_placeholders": 2}, "See [the docs](http://x.org) and [name].", True, flip=["D-placeholder-link"])

# detectable_content:postscript
C = "detectable_content:postscript"
PS = {"postscript_marker": "P.S."}
F(C, PS, "Main answer here.\n\nP.S. Thanks for asking.", True)
F(C, PS, "Main answer here.", False)
F(C, PS, "I added a P.S. note at the end, see below.\n\nThat is all.", False)
F(C, PS, "P.S. Thanks.\n\nMain answer here.", False, flip=["D-postscript-end"])
F(C, {"postscript_marker": "P.P.S"}, "Answer.\n\nP.P.S Remember to rest.", True)
F(C, {"postscript_marker": "P.P.S"}, "Answer.\n\nP.S. one more thing", False)
F(C, PS, "Answer.\n\nP.P.S. extra", False)
F(C, PS, "Answer.\n\nP.S: thanks", True, flip=["D-postscript-dot"], ctx={"shown_marker": "P.S"})
F(C, PS, "Answer.\n\np.s. thanks", False, flip=["D-postscript-case"])

# detectable_format:bigram_wrapping (grader A only)
C = "detectable_format:bigram_wrapping"
F(C, None, "<<I am>> <<at home>>", True)
F(C, None, "<<I am at home>>", False)
F(C, None, "<<I am>> <<at home>> today", False)
F(C, None, "<<I am>> <<home>>", True, flip=["D-bigram-odd"])
F(C, None, "I am at home", False)

# detectable_format:constrained_response
C = "detectable_format:constrained_response"
F(C, None, "My answer is yes.", True)
F(C, None, "My answer is yes. My answer is no.", False)
F(C, None, "My answer is maybe. It depends on the details.", False, flip=["D-constrained-exact"])
F(C, None, "Yes.", False)

# detectable_format:json_format
C = "detectable_format:json_format"
F(C, None, '{"a": 1}', True)
F(C, None, '```json\n{"a": 1}\n```', True)
F(C, None, 'Here is the JSON:\n```json\n{"a": 1}\n```', False)
F(C, None, '"just a string"', False, flip=["D-json-scalar"])
F(C, None, '{"a": 1,}', False)

# detectable_format:multiple_sections
C = "detectable_format:multiple_sections"
S2 = {"num_sections": 2, "section_spliter": "SECTION"}
F(C, S2, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", True)
F(C, S2, "SECTION 1\nOnly one.", False)
F(C, S2, "SECTION 1\nAs noted in SECTION 2 below, x.\nSECTION 2\nMore.", True)
F(C, S2, "SECTION 1\nThis part mentions SECTION 2 inline only.", False)
F(C, S2, "SECTION 1\na\nSECTION 2\nb\nSECTION 3\nc", False, flip=["D-section-count"])
F(C, S2, "Section 1\na\nSection 2\nb", False, flip=["D-section-case"])
F(C, S2, "SUBSECTION 1\na\nSUBSECTION 2\nb", False)

# detectable_format:number_bullet_lists
C = "detectable_format:number_bullet_lists"
B2 = {"num_bullets": 2}
F(C, B2, "* Apples\n* Pears", True)
F(C, B2, "* Apples\n* Pears\n* Plums", False)
F(C, B2, "- Apples\n- Pears", True, flip=["D-bullet-marker"])
F(C, B2, "* Apples\n* Pears\n\n* * *\n\nDone.", True)
F(C, B2, "*Note:* fruit list\n* Apples\n* Pears", True)
F(C, B2, "* Apples\n* Pears\n-5 degrees is cold.", True)
F(C, B2, "+ Apples\n+ Pears", True, flip=["D-bullet-marker"])

# detectable_format:number_highlighted_sections
C = "detectable_format:number_highlighted_sections"
H2 = {"num_highlights": 2}
F(C, H2, "This is *important* and *urgent*.", True)
F(C, H2, "This is *important* only.", False)
F(C, H2, "This is **important** and **urgent**.", True, flip=["D-highlight-bold"])
F(C, H2, "Compute 5 * 3 * 2 and *done*.", False)

# detectable_format:sentence_hyphens
C = "detectable_format:sentence_hyphens"
F(C, None, "I like tea.-You like coffee.-We both like cake.", True)
F(C, None, "I like tea. You like coffee.", False)
F(C, None, "Just one sentence here.", True, flip=["D-hyphen-plural"])
F(C, None, "I like tea.- You like coffee.", False)
F(C, None, "I-like-tea. You-like-coffee.", False)

# detectable_format:square_brackets
C = "detectable_format:square_brackets"
F(C, None, "[Hello] [world]", True)
F(C, None, "[Hello] world", False)
F(C, None, "[Hello], [world].", True, flip=["D-bracket-punct"])
F(C, None, "[Hello world]", False, flip=["D-brackets-per-word"])
F(C, None, "Hello [world] how are you", False)

# detectable_format:title
C = "detectable_format:title"
F(C, None, "<<My Poem>>\nRoses are red.", True)
F(C, None, "My Poem\nRoses are red.", False)
F(C, None, "<< >>\nRoses are red.", False)
F(C, None, "Roses are red.\n<<My Poem>>", True, flip=["D-title-position"])

# first_word:first_word_answer
C = "first_word:first_word_answer"
FW = {"first_word": "development"}
F(C, FW, "Development is key.", True)
F(C, FW, "Growth is key.", False)
F(C, FW, "development, as a concept, matters.", True)
F(C, FW, "**Development** matters.", True, flip=["D-edge-markup"])
F(C, FW, "Developmental work matters.", False)

# first_word:first_word_sent
C = "first_word:first_word_sent"
FS = {"first_word": "care"}
F(C, FS, "Care is good. Care is kind.", True)
F(C, FS, "Care is good. People are kind.", False)
F(C, FS, "care, always. care, forever.", True)
F(C, FS, "Care is key\nkey points follow. Care wins.", False, flip=["D-sentence"])

# keywords:existence
C = "keywords:existence"
F(C, {"keywords": ["art", "she"]}, "Art is what she loves.", True)
F(C, {"keywords": ["art", "she"]}, "She loves music.", False)
F(C, {"keywords": ["art", "she"]}, "She started to finish the task.", False)
F(C, {"keywords": ["beer", "wine"]}, "We like beers and wines.", False, flip=["D-keyword-match"])

# keywords:forbidden_words
C = "keywords:forbidden_words"
FB = {"forbidden_words": ["kick", "option"]}
F(C, FB, "No such words here.", True)
F(C, FB, "Kick the ball.", False)
F(C, FB, "Options are open.", True, flip=["D-keyword-match"])
F(C, FB, "A wheel-option design.", True, flip=["D-keyword-match"])

# keywords:frequency
C = "keywords:frequency"
F(C, {"keyword": "sale", "frequency": 2, "relation": "at least"}, "Sale today. Big sale tomorrow.", True)
F(C, {"keyword": "sale", "frequency": 2, "relation": "at least"}, "Sale today.", False)
F(C, {"keyword": "sale", "frequency": 2, "relation": "at least"}, "Sale today, wholesale prices.", False)
F(C, {"keyword": "stroke", "frequency": 1, "relation": "less than"}, "Heatstroke is dangerous.", True)

# keywords:keyword_specific_position
C = "keywords:keyword_specific_position"
KP = {"keyword": "village", "n": 2, "m": 3}
F(C, KP, "We walked far. The old village slept.", True)
F(C, KP, "We walked far. The village slept.", False)
F(C, KP, "We walked far. Indeed, the village slept.", True)
F(C, {"keyword": "village", "n": 1, "m": 1}, "Village life is calm.", True, flip=["D-word-case"])

# keywords:letter_frequency
C = "keywords:letter_frequency"
LP = {"letter": "p", "let_frequency": 3, "let_relation": "at least"}
F(C, LP, "pepper", True)
F(C, LP, "pup", False)
F(C, LP, "Pup p", True, flip=["D-letter-case"])
F(C, {"letter": "t", "let_frequency": 2, "let_relation": "less than"}, "cat", True)
F(C, {"letter": "t", "let_frequency": 2, "let_relation": "less than"}, "tat", False)

# keywords:no_adjacent_consecutive
C = "keywords:no_adjacent_consecutive"
F(C, None, "The cat sat", True)
F(C, None, "A big dog", False)
F(C, None, "Big apple", False, flip=["D-consecutive-order"])
F(C, None, "Steps 1 2 now", True)
F(C, None, "very very good", True)

# keywords:palindrome
C = "keywords:palindrome"
F(C, None, "Wow, that is a level road.", True)
F(C, None, "This sentence has none.", False)
F(C, None, "I like it.", False, flip=["D-palindrome-length"])
F(C, None, "Top results\n---\nNotes here", False)

# keywords:start_end
C = "keywords:start_end"
F(C, None, "Hello world, I say hello", True)
F(C, None, "Hello world, I say hello.", False)
F(C, None, "Hello world, goodbye", False)
F(C, None, "- Hello world -", False)
F(C, None, "**Hello** world, I say hello", True, flip=["D-edge-markup"])

# keywords:word_count_different_numbers
C = "keywords:word_count_different_numbers"
WC = {"keyword": "contact", "frequency": 2, "relation": "at least"}
F(C, WC, "Contact us. Contact them.", True)
F(C, WC, "Contact us.", False)
F(C, WC, "Contact us. Contact them. Contact all.", False, flip=["D-word-count-relation"])
F(C, {"keyword": "refuse", "frequency": 1, "relation": "less than"}, "I refuse.", True)

# keywords:word_once
C = "keywords:word_once"
F(C, {"keyword": "beer"}, "I like beer.", True)
F(C, {"keyword": "beer"}, "I like wine.", False)
F(C, {"keyword": "beer"}, "Beer is good and beer is cheap.", True)
F(C, {"keyword": "star"}, "The start of the story.", False)

# language:response_language (grader A only)
C = "language:response_language"
ES = {"language": "es"}
F(C, ES, "Hola, ¿cómo estás? Espero que tengas un buen día con tu familia y que todo vaya muy bien en el trabajo.", True)
F(C, ES, "Hello, how are you? I hope you have a good day with your family and that everything goes well at work.", False)
F(C, ES, "12345 67890", False)
F(C, ES, "", False)
F(C, ES,
  "Hola, ¿cómo estás? Espero que tengas un buen día con tu familia y que todo vaya muy bien en el trabajo. "
  "Mañana vamos a visitar a mis abuelos en el pueblo y comeremos juntos en la plaza mayor.\n\n"
  "This last paragraph is written in English and talks about the weather, which is sunny today.",
  False, flip=["D-language-mixed"])

# last_word:last_word_answer
C = "last_word:last_word_answer"
LW = {"last_word": "payment"}
F(C, LW, "Please send the payment.", True)
F(C, LW, "Please send the money.", False)
F(C, LW, "Please send the **payment**", True, flip=["D-edge-markup"])
F(C, LW, "", False)

# last_word:last_word_sent
C = "last_word:last_word_sent"
LS = {"last_word": "limit"}
F(C, LS, "Know your limit. Respect the limit!", True)
F(C, LS, "Know your limit. Respect the rules.", False)

# length_constraints:nth_paragraph_first_word
C = "length_constraints:nth_paragraph_first_word"
NP = {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "fight"}
F(C, NP, "Intro text here.\n\nFight for it.", True)
F(C, NP, "Intro text here.\n\nWin for it.", False)
F(C, NP, "Intro.\n\nFight.\n\nMore.", False)
F(C, NP, "Intro text here.\n\n\n\nFight for it.", True, flip=["D-blank-run"])
F(C, NP, "Intro.\n\n**Fight** on.", True, flip=["D-edge-markup"])
F(C, NP, "Intro.\n\n- Fight on.", True, flip=["D-edge-markup"])

# length_constraints:number_paragraphs
C = "length_constraints:number_paragraphs"
P2 = {"num_paragraphs": 2}
F(C, P2, "First paragraph.\n***\nSecond paragraph.", True)
F(C, P2, "First paragraph.\n\nSecond paragraph.", False)
F(C, P2, "First.\n***\nSecond.\n***\nThird.", False)
F(C, P2, "First paragraph has ***bold italic*** text.\n***\nSecond paragraph.", True)
F(C, P2, "First.\n***\nSecond.\n***", False, flip=["D-divider-edge"])
F(C, {"num_paragraphs": 1}, "Just one paragraph.", True)

# length_constraints:number_sentences
C = "length_constraints:number_sentences"
F(C, {"num_sentences": 3, "relation": "at least"}, "One here. Two here. Three here.", True)
F(C, {"num_sentences": 3, "relation": "at least"}, "One here. Two here.", False)
F(C, {"num_sentences": 3, "relation": "at least"}, "Title line\nOne here. Two here.", True, flip=["D-sentence"])
F(C, {"num_sentences": 2, "relation": "less than"}, "Dr. Smith arrived.", True)

# length_constraints:number_words
C = "length_constraints:number_words"
F(C, {"num_words": 5, "relation": "at least"}, "One two three four five.", True)
F(C, {"num_words": 5, "relation": "at least"}, "One two three four.", False)
F(C, {"num_words": 5, "relation": "at least"}, "Это очень хороший и полезный ответ.", True)
F(C, {"num_words": 4, "relation": "at least"}, "你好世界", True, flip=["D-word-cjk"])
F(C, {"num_words": 3, "relation": "less than"}, "Don't stop.", True)

# letters:letter_counting (grader A only)
C = "letters:letter_counting"
F(C, {"N": 3, "relation": "at least"}, "Yes, sure.", True)
F(C, {"N": 3, "relation": "at least"}, "Ok", False)
F(C, {"N": 3, "relation": "at least"}, "Да, конечно, это так.", True)
F(C, {"N": 3, "relation": "less than"}, "Yes", False, flip=["D-letter-unit"])

# letters:letter_counting2
C = "letters:letter_counting2"
F(C, {"letter": "b", "let_frequency": 2, "let_relation": "at least"}, "Bob is big.", True)
F(C, {"letter": "b", "let_frequency": 4, "let_relation": "at least"}, "Bob is big.", False)

# paragraphs:paragraphs
C = "paragraphs:paragraphs"
F(C, {}, "First.\n***\nSecond.", True)
F(C, {}, "First.\n\nSecond.", False)
F(C, {}, "First.\n***\nSecond.\n***\nThird.", False)

# paragraphs:paragraphs2
C = "paragraphs:paragraphs2"
F(C, {}, "First paragraph.\n\nSecond paragraph.", True)
F(C, {}, "First paragraph.\nSecond line.", False)
F(C, {}, "A.\n\nB.\n\nC.", False)
F(C, {}, "First.\n***\nSecond.", False)
F(C, {}, "A.\n\n\n\nB.", True, flip=["D-blank-run"])

# punctuation
F("punctuation:no_comma", None, "No commas here.", True)
F("punctuation:no_comma", None, "Yes, commas.", False)
F("punctuation:no_comma", None, "你好，世界", False, flip=["D-comma-chars"])
F("punctuation:punctuation_dot", None, "No dots here", True)
F("punctuation:punctuation_dot", None, "A dot.", False)
F("punctuation:punctuation_dot", None, "Wait…", False, flip=["D-dot-chars"])
F("punctuation:punctuation_dot", None, "Pi is about 3,14 or 3.14", False)
F("punctuation:punctuation_exclamation", None, "Calm text", True)
F("punctuation:punctuation_exclamation", None, "Wow!", False)
F("punctuation:punctuation_exclamation", None, "好！", False, flip=["D-exclamation-chars"])

# startend:end_checker
C = "startend:end_checker"
EC = {"end_phrase": "Any other questions?"}
F(C, EC, "Here is the answer. Any other questions?", True)
F(C, EC, "Here is the answer. Any other questions? Thanks.", False)
F(C, EC, "Here is the answer. **Any other questions?**", True, flip=["D-end-trailing"])
F(C, EC, "Here is the answer. any other questions?", False, flip=["D-end-case"])
F(C, EC, '"Here is the answer. Any other questions?"', True, flip=["D-end-trailing"])

# startend:quotation
C = "startend:quotation"
F(C, None, '"Hello there."', True)
F(C, None, "Hello there.", False)
F(C, None, "“Hello there.”", True, flip=["D-quote-chars"])
F(C, None, "'Hello there.'", False)

# ---- added after the first panel run (contract version 3) ----
F("count:lowercase_counting", {"N": 2}, "Он сказал да да да да.", False, finding={"A": "F37"})
F("detectable_format:square_brackets", None, "[Hello]and[world]", False, finding={"A": "F38"})
F("last_word:last_word_sent", {"last_word": "limit"}, "We use Node.js to set the limit.", True, finding={"A": "F39"})
F("last_word:last_word_sent", {"last_word": "limit"}, "Respect it。Know the limit", False, finding={"A": "F39"})
F("first_word:first_word_sent", {"first_word": "care"}, "care for map.module.scss files.", True, finding={"A": "F39"})
F("detectable_content:postscript", {"postscript_marker": "P.S."}, "Answer.\n\n**P.S.** Thanks.", True, finding={"B": "F40"})
F("last_word:last_word_answer", {"last_word": "ask"}, "Feel free to ask 朋友", False, finding={"B": "F24"})
F("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "at least"}, "ПРИВЕТ МИР, как дела.", True,
  finding={"B": "F24"})
F("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "I'm sure NASA is fine.", True,
  finding={"A": "F23"})
F("detectable_format:sentence_hyphens", None, "A well-known fact.", True, flip=["D-hyphen-inner"])
F("keywords:existence", {"keywords": ["atmosphere", "system"]}, "Dans l'atmosphere du system.", True)
F("change_case:english_lowercase", None, "hello world, this is english text with one 中文 word in the middle of it.", False,
  flip=["D-language-mixed"])

F("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "第一句。第二句。第三句。", True,
  finding={"A": "F39", "B": "F36"})
F("detectable_format:sentence_hyphens", None, "第一句。第二句。", False, finding={"A": "F39"})
F("length_constraints:number_sentences", {"num_sentences": 2, "relation": "at least"}, 'He said "Stop." Then he left.', True,
  finding={"B": "F36"})

assert len({f["id"] for f in FIXTURES}) == len(FIXTURES)
