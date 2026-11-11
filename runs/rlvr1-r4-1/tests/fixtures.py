"""Labeled fixtures, written from audit/CONTRACTS.md alone.

Each fixture: (check id, kwargs, response text, contract label, note). The label is the
contract's verdict under the proposed reading of every decision entry. Fixture ids are the check
id plus the first 12 hex digits of sha256 over (check, kwargs, text). Grader verdicts and the
finding/decision classification are computed by audit/scripts/classify_fixtures.py and frozen in
audit/tests/fixture_expectations.json.
"""
import hashlib
import json

T, F = True, False

CW = {"capital_frequency": 2, "capital_relation": "at least"}
RP = {"phrase": "Time flies when having fun", "small_n": 2}
RP5 = {"phrase": "Laughter is the best medicine", "small_n": 2}
CC = {"n_sent": 3, "n_words": 2}
PS = {"postscript_marker": "P.S."}
PPS = {"postscript_marker": "P.P.S"}
MS = {"num_sections": 2, "section_spliter": "SECTION"}
NB = {"num_bullets": 2}
KE = {"keywords": ["act", "garden"]}
KF = {"forbidden_words": ["kick", "option"]}
KFR = {"keyword": "act", "frequency": 2, "relation": "less than"}
KSP = {"keyword": "village", "n": 2, "m": 3}
LF = {"letter": "s", "let_frequency": 3, "let_relation": "at least"}
WCL = {"keyword": "policy", "frequency": 2, "relation": "less than"}
WCA = {"keyword": "policy", "frequency": 2, "relation": "at least"}
NPF = {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}

FIXTURES = [
    # change_case:capital_word_frequency
    ("change_case:capital_word_frequency", CW, "NASA and the FBI met today.", T, "two capital words"),
    ("change_case:capital_word_frequency", CW, "Only NASA came.", F, "one capital word"),
    ("change_case:capital_word_frequency", {"capital_frequency": 3, "capital_relation": "less than"},
     "I think NASA and ESA agree.", F, "I counts as a capital word: 3, not fewer than 3"),
    ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"},
     "COVID-19 and NATO.", F, "hyphenated capital word counts once: 2"),
    # change_case:english_capital
    ("change_case:english_capital", {}, "THE WEATHER IS NICE TODAY AND I WILL GO TO THE PARK WITH MY FRIENDS.", T, "English, all capitals"),
    ("change_case:english_capital", {}, "The weather is nice today.", F, "lowercase letters"),
    ("change_case:english_capital", {}, "LE TEMPS EST TRÈS BEAU AUJOURD'HUI ET JE VAIS AU PARC AVEC MES AMIS POUR JOUER.", F, "French in capitals is not English"),
    ("change_case:english_capital", {}, "", F, "empty"),
    # change_case:english_lowercase
    ("change_case:english_lowercase", {}, "the weather is nice today and i will go to the park with my friends.", T, "English, all lowercase"),
    ("change_case:english_lowercase", {}, "The weather is nice.", F, "capital letter"),
    ("change_case:english_lowercase", {}, "el clima es muy agradable hoy y voy a ir al parque con mis amigos para jugar.", F, "Spanish in lowercase is not English"),
    # combination:two_responses
    ("combination:two_responses", {}, "Paris is the capital.\n******\nThe capital is Paris.", T, "two different responses"),
    ("combination:two_responses", {}, "Same answer.\n******\nSame answer.", F, "identical responses"),
    ("combination:two_responses", {}, "First answer.\n*******\nSecond answer.", F, "seven asterisks are not the separator"),
    ("combination:two_responses", {}, "Only one answer here.", F, "no separator"),
    # copy:repeat_phrase
    ("copy:repeat_phrase", RP, "Time flies while having fun. Time flies whilst having fun.", T, "two one-word variants"),
    ("copy:repeat_phrase", RP, "Time flies when having fun. Time flies when having fun.", F, "two unchanged copies, no variant"),
    ("copy:repeat_phrase", RP, "Time flies when having fun. Time flies while having fun.", F, "one copy and one variant: one variant"),
    ("copy:repeat_phrase", RP5, "Laughter is a best medicine. Laughter is our best medicine. Laughter is the best medicine.", T,
     "two variants plus the original"),
    ("copy:repeat_phrase", RP, "time flies while having fun\ntime flies whilst having fun", T, "variants in lowercase on two lines"),
    ("copy:repeat_phrase", RP, "Time flies when having joy. Time flies when having games.", F, "last word replaced"),
    ("copy:repeat_phrase", RP, "1. Time flies while having fun!\n2. Time flies whilst having fun!", T, "variants in a numbered list"),
    # count:count_unique
    ("count:count_unique", {}, "Every word here differs.", T, "all distinct"),
    ("count:count_unique", {}, "The cat saw the dog.", F, "the repeated, ignoring case"),
    ("count:count_unique", {}, "Cats sleep. Dogs bark.", T, "punctuation is not a word"),
    # count:counting_composition
    ("count:counting_composition", CC,
     "Birds sing. Dogs bark. Cats purr.\n* * *\nSun shines. Rain falls. Wind blows.\n* * *\nKids play. Adults work. Elders rest.", T,
     "three paragraphs with the instructed * * * divider"),
    ("count:counting_composition", CC,
     "Birds sing. Dogs bark. Cats purr.\n***\nSun shines. Rain falls. Wind blows.\n***\nKids play. Adults work. Elders rest.", T,
     "three paragraphs with *** dividers"),
    ("count:counting_composition", CC, "Birds sing loudly today.", F, "one sentence"),
    ("count:counting_composition", CC, "Birds sing all day long. Dogs bark at night. Cats purr softly.", F, "one paragraph, long sentences"),
    # count:lowercase_counting
    ("count:lowercase_counting", {"N": 2}, "Apples and pears and plums.", T, "each lowercase word at most twice"),
    ("count:lowercase_counting", {"N": 2}, "the cat and the dog and the bird", F, "the three times"),
    ("count:lowercase_counting", {"N": 2}, "NASA ESA JAXA", T, "no lowercase word"),
    ("count:lowercase_counting", {"N": 2}, "The cat. the dog. the end.", T, "the twice; The is not the lowercase word"),
    # detectable_content:number_placeholders
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], your order ships to [address].", T, "two placeholders"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], thanks.", F, "one placeholder"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "Fill in [] and [ ].", F, "empty brackets are not placeholders"),
    ("detectable_content:number_placeholders", {"num_placeholders": 2}, "See [1] and [2].", T, "any bracketed text counts"),
    # detectable_content:postscript
    ("detectable_content:postscript", PS, "Thanks for reading.\n\nP.S. Bring an umbrella.", T, "postscript line"),
    ("detectable_content:postscript", PS, "Thanks for reading. Bring an umbrella.", F, "no postscript"),
    ("detectable_content:postscript", PS, "Remember the P.S. note in my letter.", F, "marker only mid-line"),
    ("detectable_content:postscript", PS, "Thanks.\n\nP.P.S. Bring an umbrella.", F, "P.P.S is not P.S."),
    ("detectable_content:postscript", PS, "Thanks.\n\np.s. bring an umbrella.", F, "lowercase marker"),
    ("detectable_content:postscript", PPS, "Thanks.\n\nP.P.S Bring an umbrella.", T, "P.P.S line"),
    ("detectable_content:postscript", PS, "Thanks.\n\n**P.S.** Bring an umbrella.", T, "bold marker at line start"),
    # detectable_format:bigram_wrapping
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>>", T, "two bigrams"),
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>> today", F, "a word outside brackets"),
    ("detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>> <<now>>", T, "odd final word in its own group"),
    ("detectable_format:bigram_wrapping", {}, "I am at home", F, "no brackets"),
    # detectable_format:constrained_response
    ("detectable_format:constrained_response", {}, "My answer is yes.", T, "one option"),
    ("detectable_format:constrained_response", {}, "My answer is yes. My answer is no.", F, "two options"),
    ("detectable_format:constrained_response", {}, "My answer is maybe. It depends on the weather.", F, "option plus text"),
    ("detectable_format:constrained_response", {}, "Yes.", F, "not an option"),
    # detectable_format:json_format
    ("detectable_format:json_format", {}, '{"a": 1}', T, "object"),
    ("detectable_format:json_format", {}, '```json\n{"a": 1}\n```', T, "fenced object"),
    ("detectable_format:json_format", {}, '```json {"a": 1} ```', T, "fence on one line"),
    ("detectable_format:json_format", {}, '```JSON\n{"a": 1}\n```', T, "fence tag in capitals"),
    ("detectable_format:json_format", {}, 'Here is the JSON:\n{"a": 1}', F, "text outside the JSON"),
    ("detectable_format:json_format", {}, '"just a string"', F, "a bare JSON string"),
    # detectable_format:multiple_sections
    ("detectable_format:multiple_sections", MS, "SECTION 1\nIntro text.\nSECTION 2\nMore text.", T, "two sections"),
    ("detectable_format:multiple_sections", MS, "SECTION 1\nIntro text.", F, "one section"),
    ("detectable_format:multiple_sections", MS, "SECTION 1\nA.\nSECTION 2\nB.\nSECTION 3\nC.", F, "three sections"),
    ("detectable_format:multiple_sections", MS, "Section 1\nA.\nSection 2\nB.", F, "splitter in other case"),
    ("detectable_format:multiple_sections", {"num_sections": 1, "section_spliter": "SECTION"},
     "This answer has one part. See SECTION 2 of the manual.", F, "marker only mid-sentence"),
    ("detectable_format:multiple_sections", MS, "## SECTION 1\nA.\n## SECTION 2\nB.", T, "markdown headings"),
    # detectable_format:number_bullet_lists
    ("detectable_format:number_bullet_lists", NB, "* Apples\n* Pears", T, "two bullets"),
    ("detectable_format:number_bullet_lists", NB, "* Apples\n* Pears\n* Plums", F, "three bullets"),
    ("detectable_format:number_bullet_lists", NB, "* Apples\n* Pears\n\n---\n\nThat is all.", T, "a horizontal rule is not a bullet"),
    ("detectable_format:number_bullet_lists", NB, "- Apples\n- Pears", T, "dash bullets"),
    ("detectable_format:number_bullet_lists", NB, "+ Apples\n+ Pears", T, "plus bullets"),
    ("detectable_format:number_bullet_lists", NB, "*Note:* fruit list follows.\n* Apples\n* Pears", T, "italic line start is not a bullet"),
    ("detectable_format:number_bullet_lists", NB, "* Apples\n  * Green apples\n* Pears", F, "nested bullet counts: three"),
    ("detectable_format:number_bullet_lists", NB, "-5 degrees is cold.\n* Apples\n* Pears", T, "a line starting with -5 is not a bullet"),
    # detectable_format:number_highlighted_sections
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* and *urgent*.", T, "two highlights"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "This is *important* only.", F, "one highlight"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "**Key** and **Note**", T, "bold spans"),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Compute 2 * 3 * 4 now.", F, "multiplication signs are not emphasis"),
    # detectable_format:sentence_hyphens
    ("detectable_format:sentence_hyphens", {}, "I like tea.-You like coffee.-We both like water.", T, "sentences joined by hyphens"),
    ("detectable_format:sentence_hyphens", {}, "I like tea. You like coffee.", F, "joined by a space"),
    ("detectable_format:sentence_hyphens", {}, "I like tea.- You like coffee.", F, "space after the hyphen"),
    ("detectable_format:sentence_hyphens", {}, "This is a well-known fact.-Everyone agrees.", T, "a hyphenated word inside a sentence"),
    ("detectable_format:sentence_hyphens", {}, "Hello-world.", T, "a single sentence"),
    # detectable_format:square_brackets
    ("detectable_format:square_brackets", {}, "[Hello] [world]", T, "every word bracketed"),
    ("detectable_format:square_brackets", {}, "[Hello] world", F, "a bare word"),
    ("detectable_format:square_brackets", {}, "[Hello], [world].", T, "punctuation outside the brackets"),
    ("detectable_format:square_brackets", {}, "[Hello world]", F, "two words in one group"),
    # detectable_format:title
    ("detectable_format:title", {}, "<<Spring Rain>>\nThe rain falls.", T, "title"),
    ("detectable_format:title", {}, "Spring Rain\nThe rain falls.", F, "no title marker"),
    ("detectable_format:title", {}, "<< >>\nText.", F, "blank title"),
    # first_word:first_word_answer
    ("first_word:first_word_answer", {"first_word": "development"}, "Development matters.", T, "first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "Growth matters.", F, "other first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "development, as a field, matters.", T, "comma after the first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters.", T, "bold first word"),
    ("first_word:first_word_answer", {"first_word": "development"}, '"development" is the word.', T, "quoted first word"),
    # first_word:first_word_sent
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace comes first. Peace stays.", T, "every sentence"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace comes first. War follows.", F, "second sentence"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "peace, friends, comes first. peace stays.", T, "comma after the word"),
    ("first_word:first_word_sent", {"first_word": "peace"}, "Peace now\nWar later.", F, "a line is a sentence"),
    # keywords:existence
    ("keywords:existence", KE, "We act in the garden.", T, "both keywords"),
    ("keywords:existence", KE, "We act indoors.", F, "garden missing"),
    ("keywords:existence", KE, "The action happens in the gardens.", F, "only longer words"),
    ("keywords:existence", KE, "ACT now in the GARDEN.", T, "capitals"),
    # keywords:forbidden_words
    ("keywords:forbidden_words", KF, "Choose wisely.", T, "none present"),
    ("keywords:forbidden_words", KF, "Kick the ball.", F, "kick present"),
    ("keywords:forbidden_words", KF, "There are many options.", T, "options is not option"),
    # keywords:frequency
    ("keywords:frequency", KFR, "We act now.", T, "once, fewer than 2"),
    ("keywords:frequency", KFR, "We act now and act later.", F, "twice"),
    ("keywords:frequency", KFR, "The actor acted in the act.", T, "act as a word once"),
    # keywords:keyword_specific_position
    ("keywords:keyword_specific_position", KSP, "I live nearby. We love village life.", T, "3rd word of sentence 2"),
    ("keywords:keyword_specific_position", KSP, "I live nearby. We love city life.", F, "other word"),
    ("keywords:keyword_specific_position", KSP, "I live nearby. Well, the village is big.", T, "a comma is not a word"),
    ("keywords:keyword_specific_position", {"keyword": "village", "n": 1, "m": 1}, "Village life is calm.", T, "capitalized at sentence start"),
    # keywords:letter_frequency
    ("keywords:letter_frequency", LF, "She sells seashells.", T, "many s"),
    ("keywords:letter_frequency", LF, "Hello there.", F, "no s"),
    ("keywords:letter_frequency", LF, "Sss.", T, "capital S counts"),
    # keywords:no_adjacent_consecutive
    ("keywords:no_adjacent_consecutive", {}, "Zebras eat grass quietly.", T, "no consecutive starts"),
    ("keywords:no_adjacent_consecutive", {}, "A big cat.", F, "a then b"),
    ("keywords:no_adjacent_consecutive", {}, "Cats bark loudly.", F, "c then b"),
    ("keywords:no_adjacent_consecutive", {}, '"Apples" bring joy.', F, "a then b behind a quote mark"),
    ("keywords:no_adjacent_consecutive", {}, "Room 1 2 here.", T, "digits are not letters"),
    ("keywords:no_adjacent_consecutive", {}, "The the end.", T, "repeated word is allowed"),
    # keywords:palindrome
    ("keywords:palindrome", {}, "The level was high.", T, "level"),
    ("keywords:palindrome", {}, "Items:\n- one\n- two", F, "no palindromic word"),
    ("keywords:palindrome", {}, "I saw a cat.", F, "only one-letter words"),
    ("keywords:palindrome", {}, "Level ground.", T, "capitalized palindrome"),
    ("keywords:palindrome", {}, "Fast racecar.", T, "palindrome before a period"),
    # keywords:start_end
    ("keywords:start_end", {}, "Hello there my friend hello", T, "same word"),
    ("keywords:start_end", {}, "Hello there my friend hello.", F, "trailing period"),
    ("keywords:start_end", {}, "Hello there.", F, "different words"),
    ("keywords:start_end", {}, "**Hello** there my friend hello", T, "bold first word"),
    # keywords:word_count_different_numbers
    ("keywords:word_count_different_numbers", WCL, "This policy and that policy differ.", T, "exactly 2 (relation less than hidden)"),
    ("keywords:word_count_different_numbers", WCA, "This policy and that policy and another policy.", F, "3, not 2"),
    ("keywords:word_count_different_numbers", WCL, "One policy only.", F, "1, not 2"),
    ("keywords:word_count_different_numbers", WCA, "This policy and that policy.", T, "exactly 2"),
    # keywords:word_once
    ("keywords:word_once", {"keyword": "fix"}, "We fix it.", T, "once"),
    ("keywords:word_once", {"keyword": "fix"}, "We fix it and fix it again.", T, "twice is still included"),
    ("keywords:word_once", {"keyword": "fix"}, "We repair it.", F, "absent"),
    ("keywords:word_once", {"keyword": "fix"}, "The prefix matters.", F, "only inside a longer word"),
    # language:response_language
    ("language:response_language", {"language": "fr"}, "Bonjour, je m'appelle Marie et j'habite à Paris depuis dix ans avec ma famille.", T, "French"),
    ("language:response_language", {"language": "fr"}, "Hello, my name is Marie and I have lived in Paris for ten years with my family.", F, "English"),
    ("language:response_language", {"language": "fr"}, "12345 !!!", F, "no language at all"),
    ("language:response_language", {"language": "fr"}, "", F, "empty"),
    # last_word:last_word_answer
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the limit.", T, "last word"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the end.", F, "other word"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "We reached the **limit**.", T, "bold last word"),
    ("last_word:last_word_answer", {"last_word": "limit"}, "", F, "empty"),
    # last_word:last_word_sent
    ("last_word:last_word_sent", {"last_word": "limit"}, "We hit the limit. They passed the limit!", T, "every sentence"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "We hit the limit. They passed it.", F, "second sentence"),
    ("last_word:last_word_sent", {"last_word": "limit"}, "Title here\nWe hit the limit.", F, "a line is a sentence"),
    # length_constraints:nth_paragraph_first_word
    ("length_constraints:nth_paragraph_first_word", NPF, "Rain falls.\n\nIf it stops, we go out.", T, "paragraph 2 starts with If"),
    ("length_constraints:nth_paragraph_first_word", NPF, "Rain falls.\n\nWhen it stops, we go out.", F, "other word"),
    ("length_constraints:nth_paragraph_first_word", NPF, "Rain falls.\n\n\n\nif it stops, we go out.", T, "two blank lines between"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 3, "nth_paragraph": 3, "first_word": "foo"},
     "x\n\n\n\nfoo here\n\nbar here", F, "paragraph 3 is 'bar here'"),
    ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "if"},
     "if: rain falls.\n\nThen we stay.", T, "colon after the first word"),
    # length_constraints:number_paragraphs
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", T, "divider line"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n\n***\n\nSecond paragraph.", T, "divider between blank lines"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n\nSecond paragraph.", F, "no divider"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "***Bold intro*** first part.\n***\nSecond part.", T, "bold-italic is not a divider"),
    # length_constraints:number_sentences
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One. Two. Three.", T, "three"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "One. Two.", F, "two"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "Title\nFirst line.\nSecond line.", T, "a heading line is a sentence"),
    # length_constraints:number_words
    ("length_constraints:number_words", {"num_words": 5, "relation": "less than"}, "One two three four.", T, "four words"),
    ("length_constraints:number_words", {"num_words": 5, "relation": "less than"}, "One two three four five.", F, "five words"),
    ("length_constraints:number_words", {"num_words": 5, "relation": "less than"}, "It's a well-known fact.", T, "contraction and compound are one word each"),
    # letters:letter_counting
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Yes, indeed.", T, "many letters"),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "Ok", F, "two letters"),
    ("letters:letter_counting", {"N": 3, "relation": "at least"}, "是的，没错。", T, "Chinese characters are letters"),
    # letters:letter_counting2
    ("letters:letter_counting2", LF, "She sells seashells.", T, "many s"),
    ("letters:letter_counting2", LF, "Hello there.", F, "no s"),
    # paragraphs:paragraphs
    ("paragraphs:paragraphs", {}, "First part.\n***\nSecond part.", T, "two by divider"),
    ("paragraphs:paragraphs", {}, "First part.\n***\nSecond part.\n***\nThird part.", F, "three by divider"),
    ("paragraphs:paragraphs", {}, "First part.\n\nSecond part.", F, "no divider"),
    # paragraphs:paragraphs2
    ("paragraphs:paragraphs2", {}, "First part.\n\nSecond part.", T, "two by blank line"),
    ("paragraphs:paragraphs2", {}, "First part.\n\nSecond part.\n\nThird part.", F, "three"),
    ("paragraphs:paragraphs2", {}, "First part.\n \nSecond part.", T, "blank line holding a space"),
    ("paragraphs:paragraphs2", {}, "First part.\n\n\n\nSecond part.", T, "two blank lines"),
    # punctuation
    ("punctuation:no_comma", {}, "No commas here.", T, "none"),
    ("punctuation:no_comma", {}, "Yes, commas.", F, "ASCII comma"),
    ("punctuation:no_comma", {}, "你好，世界", F, "full-width comma"),
    ("punctuation:punctuation_dot", {}, "No dots here", T, "none"),
    ("punctuation:punctuation_dot", {}, "A dot.", F, "dot"),
    ("punctuation:punctuation_dot", {}, "你好。", F, "ideographic full stop"),
    ("punctuation:punctuation_dot", {}, "Version 3.5 is out", F, "dot in a number"),
    ("punctuation:punctuation_exclamation", {}, "Calm text", T, "none"),
    ("punctuation:punctuation_exclamation", {}, "Wow!", F, "ASCII"),
    ("punctuation:punctuation_exclamation", {}, "好！", F, "full-width"),
    # startend:end_checker
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Thanks for asking. Any other questions?", T, "exact end"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Any other questions? Thanks.", F, "text after the phrase"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Thanks. any other questions?", F, "other case"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, 'He said "Thanks. Any other questions?"', F, "closing quote after the phrase"),
    ("startend:end_checker", {"end_phrase": "Any other questions?"}, "Thanks. Any other questions?**", F, "markdown after the phrase"),
    # startend:quotation
    ("startend:quotation", {}, '"Hello there."', T, "double quotes"),
    ("startend:quotation", {}, "Hello there.", F, "no quotes"),
    ("startend:quotation", {}, "'Hello there.'", F, "single quotes are not double quotation marks"),
    ("startend:quotation", {}, "“Hello there.”", T, "curly double quotes"),
    # added after the first panel pass (development half), 2026-11-11
    ("detectable_format:bigram_wrapping", {}, "<<In>> <<spark>> <<using>> <<select>>", F, "one word per group"),
    ("detectable_format:bigram_wrapping", {}, "我不能按照您的要求进行角色扮演", F, "no brackets, one whitespace token"),
    ("detectable_format:bigram_wrapping", {}, "", F, "empty"),
    ("change_case:english_capital", {}, "THE NEW LIBRARY OPENS ON MONDAY, AND STUDENTS CAN BORROW BOOKS, LAPTOPS, AND CAMERAS.", T,
     "English in capitals"),
    ("change_case:english_capital", {}, "TO JEST PROCES ARTYSTYCZNY, ZALEŻNY OD OSOBY I JEJ STYLU.", F, "Polish in capitals"),
    ("keywords:palindrome", {}, "Я знаю, оно здесь.", T, "Cyrillic palindrome оно"),
    ("detectable_format:sentence_hyphens", {}, "First clause here - second clause here - third clause", F, "spaced hyphens"),
    ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "今天很好。我们去公园。然后回家。", T,
     "three sentences ended by the ideographic full stop"),
    ("keywords:start_end", {}, "Parliament", T, "a one-word response"),
    ("keywords:start_end", {}, '- "hello" there my friend hello', T, "list dash and quote before the first word"),
    ("count:lowercase_counting", {"N": 2}, "это это это слово", F, "a Cyrillic lowercase word three times"),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 1}, "Only paragraph.\n\n***", F, "trailing divider"),
    ("combination:two_responses", {}, "******\nFirst answer.\n******\nSecond answer.", F, "leading separator"),
    ("keywords:no_adjacent_consecutive", {}, "вот где мы", T, "Cyrillic в then г"),
]

# Graded-text extraction fixtures: (id-suffix, reasoning model?, raw text, record, contract row reward, note)
EXTRACTION = [
    ("unclosed-thinking", True, "Okay the user wants no commas so I will avoid them entirely and keep going",
     {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}, 0.0,
     "reasoning never closed: extraction failure, fails every check"),
    ("closed-thinking", True, "Plan: list, then answer, carefully.</think>Final answer here",
     {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}, 1.0, "text after </think> has no comma"),
    ("literal-think-tag", False, "Hello, use the <think> tag here",
     {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}, 0.0,
     "non-reasoning answer with a comma before a literal <think>"),
]


def fixture_id(check: str, kwargs: dict, text: str) -> str:
    blob = json.dumps([check, kwargs, text], ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"{check}:{hashlib.sha256(blob).hexdigest()[:12]}"


def all_fixtures():
    out = []
    for check, kwargs, text, label, note in FIXTURES:
        out.append({"id": fixture_id(check, kwargs, text), "check": check, "kwargs": kwargs, "text": text,
                    "label": bool(label), "note": note})
    return out
