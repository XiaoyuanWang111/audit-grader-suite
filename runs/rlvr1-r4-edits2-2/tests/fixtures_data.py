"""Labeled fixtures, written from audit/CONTRACTS.md alone (proposed readings).

Each fixture: (check, kwargs, response, label, ref). label is the contract verdict (True = pass).
ref is "control", a decision entry "D-..." whose proposed reading sets the label, or "edge" for a
near-miss that probes a specific clause. The fixture id is the check plus the first 12 hex digits of
sha256 over json.dumps([check, kwargs, response]).
"""

import hashlib
import json

PHRASE = "Live each day to the fullest"
F = [
    # change_case:capital_word_frequency
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "at least"}, "We met NASA and FBI agents at the UN.", True, "control"),
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "at least"}, "We met NASA agents.", False, "control"),
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "at least"}, "I SAW IT", True, "D-capital-word"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "OK, we go.", True, "control"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "OK, we go NOW.", False, "edge"),
    # change_case:english_capital
    ("change_case:english_capital", None, "THE CAT SAT ON THE MAT AND LOOKED AT THE BIRDS IN THE GARDEN.", True, "control"),
    ("change_case:english_capital", None, "HELLO WORLD, THIS IS MY ANSWER.", True, "edge"),
    ("change_case:english_capital", None, "HELLO WORLD", True, "edge"),
    ("change_case:english_capital", None, "The cat sat on the mat.", False, "control"),
    ("change_case:english_capital", None, "THE CAT SAT ON THE MAT, said the narrator.", False, "edge"),
    ("change_case:english_capital", None, "ПРИВЕТ МИР, КАК ТВОИ ДЕЛА СЕГОДНЯ?", False, "edge"),
    # change_case:english_lowercase
    ("change_case:english_lowercase", None, "the cat sat on the mat and looked at the birds in the garden.", True, "control"),
    ("change_case:english_lowercase", None, "The cat sat on the mat.", False, "control"),
    ("change_case:english_lowercase", None, "bonjour je suis très content de vous voir aujourd'hui mon ami", False, "edge"),
    ("change_case:english_lowercase", None, "the cat sat on the mat near NASA headquarters.", False, "edge"),
    # combination:two_responses
    ("combination:two_responses", None, "Tea is warm.\n******\nCoffee is strong.", True, "control"),
    ("combination:two_responses", None, "Tea is warm.\n******\nTea is warm.", False, "control"),
    ("combination:two_responses", None, "Tea is warm. Coffee is strong.", False, "control"),
    ("combination:two_responses", None, "Tea is warm.\n*******\nCoffee is strong.", False, "edge"),
    ("combination:two_responses", None, "A tea.\n******\nB tea.\n******\nC tea.", False, "edge"),
    # copy:repeat_phrase
    ("copy:repeat_phrase", {"phrase": PHRASE, "small_n": 2}, "Live each moment to the fullest. Live each hour to the fullest.", True, "control"),
    ("copy:repeat_phrase", {"phrase": PHRASE, "small_n": 2}, "Live each day to the fullest. Live each day to the fullest.", False, "edge"),
    ("copy:repeat_phrase", {"phrase": PHRASE, "small_n": 3}, "Live each day to the fullest. Live each day to the fullest. Live each hour to the fullest.", False, "edge"),
    ("copy:repeat_phrase", {"phrase": PHRASE, "small_n": 2}, "Live each moment to the fullest.", False, "control"),
    ("copy:repeat_phrase", {"phrase": PHRASE, "small_n": 2}, "Love each day to the fullest. Live each day to the max.", False, "edge"),
    # count:count_unique
    ("count:count_unique", None, "Every word here appears once.", True, "control"),
    ("count:count_unique", None, "The cat saw the dog.", False, "D-count-unique-case"),
    ("count:count_unique", None, "Hello, world, friend.", True, "edge"),
    # count:counting_composition
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Dogs bark. Cats purr. Birds sing.\n* * *\nFish swim. Bees buzz. Cows moo.\n* * *\nKids play. Moms cook. Dads work.", True, "control"),
    ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Dogs bark loudly. Cats purr softly. Birds sing sweetly.", False, "control"),
    # count:lowercase_counting
    ("count:lowercase_counting", {"N": 2}, "Apples and pears and plums.", True, "D-lowercase-total"),
    ("count:lowercase_counting", {"N": 2}, "the cat and the dog and the bird", False, "control"),
    ("count:lowercase_counting", {"N": 2}, "Hello World", True, "control"),
    ("count:lowercase_counting", {"N": 2}, "The the the", True, "D-lowercase-counting"),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], meet me at [address].", True, "control"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], meet me soon.", False, "control"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], see [] and [ ].", False, "edge"),
    # detectable_content:postscript
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks for reading.\n\nP.S. See you soon.", True, "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks for reading.", False, "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks.\n\nP.P.S. See you soon.", False, "edge"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks, as the P.S. says, for reading.", False, "edge"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks.\n\n**P.S.** See you soon.", True, "edge"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "P.S. Early note.\n\nMain answer follows here.", False, "D-postscript"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "Thanks.\n\nP.P.S. More soon.", True, "control"),
    ("detectable_content:postscript", {"postscript_marker": "P.S."}, "thanks.\n\np.s. see you.", False, "D-postscript-case"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "The two limits are equal. P.P.S. This answer is done.", False, "D-postscript-line"),
    ("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "The two limits are equal.\n\nP.P.S.", False, "edge"),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>>", True, "control"),
    ("detectable_format:bigram_wrapping", None, "I am at home", False, "control"),
    ("detectable_format:bigram_wrapping", None, "<<I am>> at <<home now>>", False, "edge"),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", None, "My answer is yes.", True, "control"),
    ("detectable_format:constrained_response", None, "My answer is yes. The sky is blue today.", True, "D-constrained-exact"),
    ("detectable_format:constrained_response", None, "Yes, I agree.", False, "control"),
    ("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", False, "edge"),
    # detectable_format:json_format
    ("detectable_format:json_format", None, '{"a": 1}', True, "control"),
    ("detectable_format:json_format", None, '```json\n{"a": 1}\n```', True, "control"),
    ("detectable_format:json_format", None, 'Here is JSON: {"a": 1}', False, "control"),
    ("detectable_format:json_format", None, "{'a': 1}", False, "control"),
    ("detectable_format:json_format", None, '{"a": NaN}', False, "edge"),
    ("detectable_format:json_format", None, '```JSON\n{"a": 1}\n```', True, "edge"),
    ("detectable_format:json_format", None, '```json\n{"a": 1}\n```\nHope this helps.', False, "control"),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", True, "control"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nIntro text.", False, "control"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text.", False, "edge"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nAs SECTION 2 below shows, tea.\nSECTION 2\nB text.", True, "edge"),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "Section 1\nA text.\nSection 2\nB text.", False, "D-sections-case"),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two\n* three", True, "control"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "- one\n- two\n- three", True, "D-bullets"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two", False, "control"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two\n* three\n\n---\n\nDone.", True, "edge"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "*Note*: intro\n* one\n* two\n* three", True, "edge"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two\n* three\n\n* * *\n\nEnd.", True, "edge"),
    ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "+ one\n+ two\n+ three", True, "D-bullets"),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* and *urgent*.", True, "control"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "**Key** and **Value** matter.", True, "D-highlight"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "Nothing highlighted here.", False, "control"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 3}, "* **Alpha**: one\n* **Beta**: two", False, "edge"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Text.\n\n* * *\n\nMore.", False, "edge"),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", None, "I like tea.-You like coffee.-We both like water.", True, "control"),
    ("detectable_format:sentence_hyphens", None, "I like tea. You like coffee.", False, "control"),
    ("detectable_format:sentence_hyphens", None, "I like tea.- You like coffee.", False, "edge"),
    ("detectable_format:sentence_hyphens", None, "Tea is well-known.-Coffee is too.", True, "edge"),
    ("detectable_format:sentence_hyphens", None, "I like tea.", True, "D-hyphens-single"),
    ("detectable_format:sentence_hyphens", None, "Tea is warm - coffee is strong - water is cold", False, "edge"),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", None, "[I] [like] [tea]", True, "control"),
    ("detectable_format:square_brackets", None, "I like tea", False, "control"),
    ("detectable_format:square_brackets", None, "[I] like tea", False, "edge"),
    ("detectable_format:square_brackets", None, "[I], [like] [tea].", True, "edge"),
    ("detectable_format:square_brackets", None, "[I like tea]", False, "D-square-brackets"),
    # detectable_format:title
    ("detectable_format:title", None, "<<Morning Song>>\nThe sun rises.", True, "control"),
    ("detectable_format:title", None, "Morning Song\nThe sun rises.", False, "control"),
    ("detectable_format:title", None, "<<>> The sun rises.", False, "edge"),
    ("detectable_format:title", None, "The sun rises. <<Morning Song>>", True, "D-title"),
    # first_word:first_word_answer
    ("first_word:first_word_answer", {"first_word": "development"}, "Development matters.", True, "control"),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters.", True, "edge"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Development, as a field, matters.", True, "edge"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Growth matters.", False, "control"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Developments matter.", False, "edge"),
    # first_word:first_word_sent
    ("first_word:first_word_sent", {"first_word": "tea"}, "Tea is warm. Tea is calm.", True, "control"),
    ("first_word:first_word_sent", {"first_word": "tea"}, "Tea is warm. Coffee is calm.", False, "control"),
    ("first_word:first_word_sent", {"first_word": "tea"}, "Tea, I think, is warm. Tea is calm.", True, "edge"),
    ("first_word:first_word_sent", {"first_word": "tea"}, "", False, "D-empty"),
    # keywords:existence
    ("keywords:existence", {"keywords": ["food", "poetry"]}, "Food and poetry go together.", True, "control"),
    ("keywords:existence", {"keywords": ["food", "poetry"]}, "Food goes together.", False, "control"),
    ("keywords:existence", {"keywords": ["food", "poetry"]}, "Foods and poetry.", False, "D-keyword-match"),
    ("keywords:existence", {"keywords": ["food", "poetry"]}, "The food's taste inspired poetry.", True, "control"),
    # keywords:forbidden_words
    ("keywords:forbidden_words", {"forbidden_words": ["law", "top"]}, "We discussed rules.", True, "control"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "top"]}, "The law is clear.", False, "control"),
    ("keywords:forbidden_words", {"forbidden_words": ["law", "top"]}, "Laws and topics.", True, "D-keyword-match"),
    # keywords:frequency
    ("keywords:frequency", {"keyword": "art", "frequency": 2, "relation": "at least"}, "Art is long. I love art.", True, "control"),
    ("keywords:frequency", {"keyword": "art", "frequency": 2, "relation": "at least"}, "Art is long.", False, "control"),
    ("keywords:frequency", {"keyword": "art", "frequency": 2, "relation": "at least"}, "Art starts in the heart.", False, "D-keyword-match"),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", {"keyword": "tea", "n": 2, "m": 3}, "I like coffee. We drink tea daily.", True, "control"),
    ("keywords:keyword_specific_position", {"keyword": "tea", "n": 2, "m": 3}, "I like coffee. We drink milk daily.", False, "control"),
    ("keywords:keyword_specific_position", {"keyword": "tea", "n": 2, "m": 3}, "I like coffee. Yes, drink tea daily.", True, "edge"),
    ("keywords:keyword_specific_position", {"keyword": "tea", "n": 1, "m": 1}, "Tea is warm.", True, "D-first-last-case"),
    # keywords:letter_frequency
    ("keywords:letter_frequency", {"letter": "z", "let_frequency": 2, "let_relation": "at least"}, "Zebras zoom.", True, "D-letter-case"),
    ("keywords:letter_frequency", {"letter": "z", "let_frequency": 2, "let_relation": "at least"}, "Zebras run.", False, "control"),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", None, "The cat sat on the mat.", True, "control"),
    ("keywords:no_adjacent_consecutive", None, "A big dog.", False, "control"),
    ("keywords:no_adjacent_consecutive", None, "Big apple pie.", False, "D-consecutive-order"),
    ("keywords:no_adjacent_consecutive", None, "The the cat.", True, "edge"),
    ("keywords:no_adjacent_consecutive", None, "Step 1 2 done.", True, "edge"),
    ("keywords:no_adjacent_consecutive", None, '"A" big dog.', False, "edge"),
    ("keywords:no_adjacent_consecutive", None, "вот где дом", False, "D-alphabet"),
    # keywords:palindrome
    ("keywords:palindrome", None, "We saw a level road.", True, "control"),
    ("keywords:palindrome", None, "We saw a flat road.", False, "D-palindrome-length"),
    ("keywords:palindrome", None, "This - that.", False, "edge"),
    ("keywords:palindrome", None, "Level up now.", True, "edge"),
    ("keywords:palindrome", None, "Our noon, meeting.", True, "edge"),
    ("keywords:palindrome", None, "It was as a joke.", False, "D-palindrome-phrase"),
    ("keywords:palindrome", None, "A man, a plan, a canal: Panama.", True, "edge"),
    # keywords:start_end
    ("keywords:start_end", None, "Hello there my friend hello", True, "control"),
    ("keywords:start_end", None, "Hello there my friend", False, "control"),
    ("keywords:start_end", None, "Hello there my friend hello.", False, "edge"),
    ("keywords:start_end", None, "Hello there my friend **hello**", False, "edge"),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "at least"}, "A box and a box.", True, "control"),
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "at least"}, "A box, a box, a box.", False, "D-word-count-exact"),
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "A box and a box.", True, "edge"),
    ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "No containers here.", False, "edge"),
    # keywords:word_once
    ("keywords:word_once", {"keyword": "beer"}, "I like beer.", True, "control"),
    ("keywords:word_once", {"keyword": "beer"}, "Beer is good and beer is cold.", True, "edge"),
    ("keywords:word_once", {"keyword": "beer"}, "I like wine.", False, "control"),
    # language:response_language
    ("language:response_language", {"language": "fr"}, "Bonjour, je suis très content de vous voir aujourd'hui.", True, "control"),
    ("language:response_language", {"language": "fr"}, "Hello, I am very happy to see you today.", False, "control"),
    ("language:response_language", {"language": "ta"}, "12345", False, "edge"),
    # last_word:last_word_answer
    ("last_word:last_word_answer", {"last_word": "end"}, "This is the end.", True, "control"),
    ("last_word:last_word_answer", {"last_word": "end"}, "This is the **end**", True, "control"),
    ("last_word:last_word_answer", {"last_word": "end"}, "This is the finish.", False, "control"),
    ("last_word:last_word_answer", {"last_word": "end"}, "", False, "edge"),
    # last_word:last_word_sent
    ("last_word:last_word_sent", {"last_word": "limit"}, "We reached the limit. They passed the limit!", True, "control"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "We reached the limit. They passed it.", False, "control"),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "Fuel is costly.\n\nPrices rise.", True, "control"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "**Fuel** is costly.\n\nPrices rise.", True, "edge"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "Fuel: costly.\n\nPrices rise.", True, "edge"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "Gas is costly.\n\nPrices rise.", False, "control"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "Fuel is costly.\n\nPrices rise.\n\nEnd now.", False, "control"),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n***\nTwo.\n***\nThree.", True, "control"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n\n***\n\nTwo.\n\n***\n\nThree.", True, "control"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n***\nTwo.", False, "control"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n\nTwo.\n\nThree.", False, "edge"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One ***bold*** text.\n***\nTwo.\n***\nThree.", True, "D-divider"),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One. Two. Three.", True, "control"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One. Two.", False, "control"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "Title\nOne. Two.", True, "D-sentence"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "我喜欢茶。你喜欢咖啡。他喜欢水。", True, "edge"),
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "Это очень хороший ответ сегодня.", True, "edge"),
    ("first_word:first_word_answer", {"first_word": "development"}, "- Development matters.", True, "edge"),
    # length_constraints:number_words
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "One two three four five.", True, "control"),
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "One two three.", False, "control"),
    ("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "well-known well-known well-known well-known", False, "D-word"),
    # letters:letter_counting
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "Ok", True, "control"),
    ("letters:letter_counting", {"N": 3, "relation": "less than"}, "Okay", False, "control"),
    ("letters:letter_counting", {"N": 2, "relation": "less than"}, "日本", False, "D-letters-count"),
    # letters:letter_counting2
    ("letters:letter_counting2", {"letter": "l", "let_frequency": 3, "let_relation": "at least"}, "Hello all", True, "control"),
    ("letters:letter_counting2", {"letter": "l", "let_frequency": 3, "let_relation": "at least"}, "Hello", False, "control"),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", None, "One.\n***\nTwo.", True, "control"),
    ("paragraphs:paragraphs", None, "One.", False, "control"),
    ("paragraphs:paragraphs", None, "One.\n***\nTwo.\n***\nThree.", False, "edge"),
    ("paragraphs:paragraphs", None, "One.\n\nTwo.", False, "edge"),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", None, "One.\n\nTwo.", True, "control"),
    ("paragraphs:paragraphs2", None, "One. Two.", False, "control"),
    ("paragraphs:paragraphs2", None, "One.\n\nTwo.\n\nThree.", False, "edge"),
    ("paragraphs:paragraphs2", None, "One.\n***\nTwo.", False, "edge"),
    ("paragraphs:paragraphs2", None, "One.\n\n\n\nTwo.", True, "D-paragraph-separator"),
    # punctuation
    ("punctuation:no_comma", None, "No commas here.", True, "control"),
    ("punctuation:no_comma", None, "Yes, commas.", False, "control"),
    ("punctuation:no_comma", None, "你好，世界", False, "D-punct-variants"),
    ("punctuation:punctuation_dot", None, "No dots here", True, "control"),
    ("punctuation:punctuation_dot", None, "A dot.", False, "control"),
    ("punctuation:punctuation_dot", None, "Wait…", False, "D-punct-variants"),
    ("punctuation:punctuation_exclamation", None, "Calm text", True, "control"),
    ("punctuation:punctuation_exclamation", None, "Wow!", False, "control"),
    ("punctuation:punctuation_exclamation", None, "Wow！", False, "D-punct-variants"),
    # startend:end_checker
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is my answer. Any other questions?", True, "control"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is my answer.", False, "control"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is my answer. Any other questions? Thanks.", False, "control"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is my answer. any other questions?", False, "D-end-phrase-case"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is my answer. **Any other questions?**", True, "D-end-phrase-markup"),
    # startend:quotation
    ("startend:quotation", None, '"Hello there."', True, "control"),
    ("startend:quotation", None, "Hello there.", False, "control"),
    ("startend:quotation", None, "'Hello there.'", False, "edge"),
    ("startend:quotation", None, "“Hello there.”", True, "D-quotation-typographic"),
]


def fixture_id(check, kwargs, response):
    digest = hashlib.sha256(json.dumps([check, kwargs, response], ensure_ascii=False).encode("utf-8")).hexdigest()
    return f"{check}:{digest[:12]}"


FIXTURES = [
    {"id": fixture_id(c, k, r), "check": c, "kwargs": k, "response": r, "label": lab, "ref": ref}
    for c, k, r, lab, ref in F
]
assert len({f["id"] for f in FIXTURES}) == len(FIXTURES)
