"""Labeled fixtures for the 58 IFBench checks.

Every label comes from audit/contracts.md (with audit/contracts_changes.md), under the
proposed reading of each decision entry. A fixture's `tag` says why the grader under
audit is expected to get it wrong:
    "F-..."  a finding: the grader's verdict is wrong under every reading the text allows
    "D-..."  a decision: the grader's verdict follows a non-proposed reading of that entry
    None     the grader is expected to agree with the label
Fixture ids are the check name plus the first 8 hex digits of sha256(check, kwargs, text).
"""
import hashlib
import json

ROW = {  # dataset rows whose kwargs a fixture reuses (kwargs come from the row)
    "repeat_change": 60,
    "repeat_simple": 64,
    "repeat_span": 284,
}

AFRICA = [
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
    "Central African Republic", "Chad", "Comoros", "Congo", "Democratic Republic of the Congo", "Djibouti",
    "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea",
    "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali",
    "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
    "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan",
    "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
]
assert len(AFRICA) == 54
AFRICA_REV = sorted(AFRICA, reverse=True)
AFRICA_REV_MISSING2 = [c for c in AFRICA_REV if c not in ("Kenya", "Ghana")]

CAPITALS_27 = ("Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, "
               "Berlin, Amsterdam, Warsaw, London, Brussels, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, "
               "Vaduz, Chisinau, Bern, Ljubljana, Zagreb")
CAPITALS_28 = CAPITALS_27.replace("Brussels, Prague", "Brussels, Kyiv, Prague")

SENT26 = ("Apples fall. Bears roam. Cats nap. Dogs bark. Eagles soar. Foxes hunt. Geese honk. Horses run. "
          "Ibis wade. Jays sing. Koalas sleep. Lions roar. Moles dig. Newts swim. Owls hoot. Pigs eat. "
          "Quails hide. Rats scurry. Seals dive. Tigers stalk. Urchins cling. Voles burrow. Wolves howl. "
          "Xerus dig. Yaks graze. Zebras gallop.")

CSV_CITY = "ID,Country,City,Year,Count\n" + "\n".join(f"{i},France,Paris,20{10+i},{i*7}" for i in range(1, 8))
CSV_CITY6 = "ID,Country,City,Year,Count\n" + "\n".join(f"{i},France,Paris,20{10+i},{i*7}" for i in range(1, 7))
CSV_Q = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n' + "\n".join(
    f'"{i}"\t"Math"\t"A"\t"Fall"\t"9{i}"' for i in range(1, 4))
CSV_Q_UNQ = 'StudentID\tSubject\tGrade\tSemester\tScore\n' + "\n".join(
    f'{i}\tMath\tA\tFall\t9{i}' for i in range(1, 4))
CSV_SP = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    f'{i},{"Toys" if i != 3 else chr(34) + "Toys & Games" + chr(34)},Acme,{i}.99,{i*3}' for i in range(1, 15))
CSV_SP_NONE = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    f"{i},Toys,Acme,{i}99,{i*3}" for i in range(1, 15))
CSV_SP13 = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    f'{i},{"Toys" if i != 3 else chr(34) + "Toys & Games" + chr(34)},Acme,{i}.99,{i*3}' for i in range(1, 14))

MCQ = (
    "Question 1: Who painted Guernica?\nA. Picasso\nB. Dali\nC. Miro\nD. Gris\nE. Braque\n"
    "Question 2: Which movement did Marcel Duchamp help found?\nA. Dada\nB. Cubism\nC. Fauvism\nD. Pop\nE. Op\n"
    "Question 3: Which artist is best known for the drip paintings of the late 1940s?\nA. Pollock\nB. Rothko\nC. Kline\nD. Still\nE. Newman\n"
    "Question 4: Which German school of art, design and architecture was founded by Walter Gropius in Weimar in 1919?\nA. Bauhaus\nB. Ulm\nC. Werkbund\nD. Brucke\nE. Blaue Reiter"
)
MCQ3 = MCQ.split("Question 4:")[0].rstrip()
MCQ_NOLABELNUM = MCQ.replace("Question 1:", "Question:").replace("Question 2:", "Question:").replace(
    "Question 3:", "Question:").replace("Question 4:", "Question:")

KW5 = {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
KW5_TEXT = ("The door was open. Bread, more bread. Blue sky, blue sea, blue eyes. "
            "Lamp one, lamp two, lamp three, lamp four, lamp five. "
            "River river river river river river river.")

REF = "the quick brown fox jumps over the lazy dog"

_F = []


def fx(check, text, label, tag=None, kw=None, row=None, note=""):
    _F.append({"check": check, "text": text, "label": label, "tag": tag, "kw": kw or {}, "row": row, "note": note})


# ---------------- count ----------------
fx("count:conjunctions", "I came and I saw, but I left, so it ended.", True, kw={"small_n": 3})
fx("count:conjunctions", "I came and saw and left.", False, kw={"small_n": 2})
fx("count:conjunctions", "And and, AND and.", False, "F-conj-variants", kw={"small_n": 2},
   note="one conjunction written three ways")
fx("count:keywords_multiple", KW5_TEXT, True, kw=KW5)
fx("count:keywords_multiple", KW5_TEXT.replace(" River river river river river river river.", ""), False, kw=KW5)
fx("count:keywords_multiple", KW5_TEXT + " We sat indoors.", True, "F-keywords-substring", kw=KW5,
   note="'indoors' is not the keyword 'door'")
fx("count:keywords_multiple", KW5_TEXT.replace("The door was open.", "The indoor air was open."), False,
   "F-keywords-substring", kw=KW5, note="keyword 'door' absent; only 'indoor'")
fx("count:keywords_multiple", KW5_TEXT + " Two doors closed.", True, "D-keyword-form", kw=KW5,
   note="'doors' is an inflection")
fx("count:numbers", "I have 2 cats and 3 dogs.", True, kw={"N": 2.0})
fx("count:numbers", "I have 2 cats and 3 dogs.", False, kw={"N": 3.0})
fx("count:numbers", "It costs 1,000 dollars or 3.5 euros.", True, kw={"N": 2.0})
fx("count:numbers", "Read pages 10-20 tonight.", True, "F-numbers-joined", kw={"N": 2.0},
   note="a range holds two numbers")
fx("count:person_names", "Emma met Liam and Noah.", True, kw={"N": 3.0})
fx("count:person_names", "Emma met Liam and Noah.", False, kw={"N": 4.0})
fx("count:person_names", "Emma, Emma and Emma.", False, kw={"N": 2.0})
fx("count:pronouns", "She told him that they would visit us.", True, kw={"N": 5.0})
fx("count:pronouns", "She told him that they would visit us.", False, kw={"N": 6.0})
fx("count:pronouns", "It is mine.", True, kw={"N": 2.0})
fx("count:punctuation", "Wait?! Yes: it's (truly) a \"well-known\" fact; really, it is. Why? Wow!", True)
fx("count:punctuation", "Wait?! Yes: it's (truly) a \"well-known\" fact, really, it is. Why? Wow!", False)
fx("count:punctuation", "Wait?! Yes: it is true; really, it is. Why? Wow!", False, "D-punct-set",
   note="no apostrophe, quotation mark, hyphen or parentheses")
fx("count:unique_word_count", "one two three four five", True, kw={"N": 5.0})
fx("count:unique_word_count", "one one two two", False, kw={"N": 3.0})
fx("count:unique_word_count", "Cat cat CAT dog.", True, kw={"N": 2.0})
fx("count:word_count_range", "one two three four five", True, kw={"min_words": 5.0, "max_words": 5.0})
fx("count:word_count_range", "one two three four", False, kw={"min_words": 5.0, "max_words": 5.0})
fx("count:word_count_range", "I don't think it's well-known.", True, "F-word-count-split",
   kw={"min_words": 5.0, "max_words": 5.0}, note="5 words; \\w+ counts 8")
fx("count:words_japanese", "I 日本 like 猫 cats 犬", True, kw={"N": 2.0})
fx("count:words_japanese", "I like cats very much", False, kw={"N": 2.0})
fx("count:words_japanese", "Hello - world 日本", False, "F-japanese-skip", kw={"N": 2.0},
   note="2nd word is 'world' (or the token '-'); neither is Japanese")
fx("count:words_japanese", "I 2021 like 猫", False, "D-japanese-digits", kw={"N": 2.0})

# ---------------- custom ----------------
fx("custom:character_reverse", ".elgae dlab eht si lobmys lanoitan ehT", True)
fx("custom:character_reverse", "The national symbol is the bald eagle.", False)
fx("custom:character_reverse", "The answer is elgae dlab.", False, "F-charrev-partial",
   note="only two words reversed; the rest is forward text")
fx("custom:csv_city", CSV_CITY, True)
fx("custom:csv_city", CSV_CITY6, False)
fx("custom:csv_city", "```csv\n" + CSV_CITY + "\n```", True, "D-csv-wrapper")
fx("custom:csv_quotes", CSV_Q, True)
fx("custom:csv_quotes", CSV_Q_UNQ, False)
fx("custom:csv_quotes", CSV_Q + '\n"4"\t"Art"\t"B"\t"Fall"\t', False, None,
   note="a 4th row with an empty last field")
fx("custom:csv_special_character", CSV_SP, True)
fx("custom:csv_special_character", CSV_SP_NONE, False)
fx("custom:csv_special_character", CSV_SP13, False)
fx("custom:date_format_list", "1796-04-12, 1805-12-02", True)
fx("custom:date_format_list", "April 12, 1796", False)
fx("custom:date_format_list", "1805-00-00, 1806-10-14", False, "F-date-invalid", note="month 00 and day 00")
fx("custom:european_capitals_sort", CAPITALS_28, True, "F-capitals-key", note="includes Kyiv (50.45 N)")
fx("custom:european_capitals_sort", CAPITALS_27, False, "F-capitals-key", note="omits Kyiv")
fx("custom:european_capitals_sort", CAPITALS_27.replace("Reykjavik, Helsinki", "Helsinki, Reykjavik"), False)
fx("custom:mcq_count_length", MCQ, True)
fx("custom:mcq_count_length", MCQ3, False)
fx("custom:mcq_count_length", MCQ_NOLABELNUM, True, "F-mcq-label", note="label 'Question:' without a number")
fx("custom:multiples", "14, 21, 28, 35, 42, 49", True)
fx("custom:multiples", "7, 14, 21, 28, 35, 42, 49", False)
fx("custom:multiples", "Multiples of seven: 14 21 28 35 42 49.", True)
fx("custom:reverse_newline", "\n".join(AFRICA_REV), True)
fx("custom:reverse_newline", "\n".join(sorted(AFRICA)), False)
fx("custom:reverse_newline", "\n".join(AFRICA_REV_MISSING2), False, "F-africa-incomplete",
   note="52 of 54 countries (Kenya and Ghana missing)")
fx("custom:sentence_alphabet", SENT26, True)
fx("custom:sentence_alphabet", SENT26.replace(" Zebras gallop.", ""), False)
fx("custom:sentence_alphabet", SENT26.replace("Apples fall.", "\"Apples fall,\" said Ann."), True,
   "F-alphabet-quote", note="first sentence opens with a quotation mark")
fx("custom:word_reverse", "eagle bald the is US the of symbol national The", True)
fx("custom:word_reverse", "The national symbol of the US is the bald eagle.", False)
fx("custom:word_reverse", "elgae dlab eht si lobmys lanoitan ehT", False)

# ---------------- format ----------------
fx("format:emoji", "I love tea 🍵. It is warm 🔥.", True)
fx("format:emoji", "I love tea. It is warm 🔥.", False)
fx("format:emoji", "I love tea. 🍵 It is warm. 🔥", True)
fx("format:emoji", "We love Japan 🇯🇵. It is far 🇯🇵.", True, "F-emoji-sequence", note="flag emoji")
fx("format:emoji", "Kind words matter ❤️. Smile more ❤️.", True, None,
   note="heart with variation selector")
fx("format:line_indent", "a\n  b\n    c", True)
fx("format:line_indent", "a\nb\nc", False)
fx("format:line_indent", "a\n\tb\n\t\tc", True, "F-indent-tabs")
fx("format:line_indent", "a\n\n\n  b\n    c", True, "F-indent-blank-lines")
fx("format:list", "SEPARATOR apples\nSEPARATOR pears", True, kw={"sep": "SEPARATOR"})
fx("format:list", "* apples\n* pears", False, kw={"sep": "!?!?"})
fx("format:list", "This well-known fact is up-to-date.", False, "F-list-anywhere", kw={"sep": "-"},
   note="prose with hyphenated words, not a list")
fx("format:list", "apples !?!? pears", True, "D-list-sep", kw={"sep": "!?!?"})
fx("format:newline", "Hello\nworld", True)
fx("format:newline", "Hello world", False)
fx("format:newline", "Hello\n\nworld.", True)
fx("format:no_bullets_bullets", "First sentence. Second sentence.\n* one\n* two", True)
fx("format:no_bullets_bullets", "First sentence.\n* one\n* two", False)
fx("format:no_bullets_bullets", "First sentence. Second sentence.\n\n* one\n\n* two", True, "F-nbb-blank-lines")
fx("format:no_bullets_bullets", "Is this a question? Yes it is!\n* one\n* two", False, "F-nbb-period",
   note="neither sentence ends in a period")
fx("format:no_bullets_bullets", "First sentence. Second sentence.\n* one\n* two\nA closing line.", True,
   "D-nbb-order")
fx("format:no_whitespace", "Hello,world!", True)
fx("format:no_whitespace", "Hello world", False)
fx("format:no_whitespace", "Hello,world!\n", True, "D-trim")
fx("format:options", "Yes.", True, kw={"options": "yes/no/maybe"})
fx("format:options", "Yes, because it is.", False, kw={"options": "yes/no/maybe"})
fx("format:options", "Yes\n", True, "D-trim", kw={"options": "yes/no/maybe"})
fx("format:options", "b)", True, kw={"options": "a), b), c), d)"})
fx("format:options", "B)", True, "D-options-exact", kw={"options": "a), b), c), d)"})
fx("format:options", "b) Larceny", True, "D-options-exact", kw={"options": "a), b), c), d)"})
fx("format:options", "I don't know", True, kw={"options": "I know or I don't know"})
fx("format:output_template", "My Answer: X\nMy Conclusion: Y\nFuture Outlook: Z", True)
fx("format:output_template", "My Answer: X\nMy Conclusion: Y", False)
fx("format:output_template", "Future Outlook: Z\nMy Conclusion: Y\nMy Answer: X", False, "F-template-check")
fx("format:output_template", "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", False,
   "F-template-check", note="placeholders not filled")
fx("format:parentheses", "a (b [c {d (e [f] e) d} c] b) a", True)
fx("format:parentheses", "a (b [c {d (e) d} c] b) a", False)
fx("format:parentheses", "((((( x )))))", True)
fx("format:quote_unquote", "\"Carpe diem\" means seize the day.", True)
fx("format:quote_unquote", "He said \"carpe diem\"", False)
fx("format:quote_unquote", "The motto is “carpe diem”", False, "F-quote-unquote-curly")
fx("format:quote_unquote", "He said \"a\", \"b\" then left.", False, "D-explanation")
fx("format:quotes", "\"She said, 'He told me \"go\" now' loudly.\"", True)
fx("format:quotes", "\"She said, 'go now' loudly.\"", False)
fx("format:quotes", "“She said, ‘He told me “go” now’ loudly.”", True, "F-quotes-curly")
fx("format:sub-bullets", "* Fruit\n  - apple\n* Veg\n  - kale", True)
fx("format:sub-bullets", "* Fruit\n* Veg", False)
fx("format:sub-bullets", "No bullets here at all.", False, "F-subbullets-check")
fx("format:sub-bullets", "* A well-known item\n* Another up-to-date item", False, "F-subbullets-check",
   note="hyphens inside words, no sub-bullets")
fx("format:thesis", "<i>Rome rose by roads.</i> Roads moved armies.\n\n<i>Rome fell by debt.</i> Debt ruined it.", True)
fx("format:thesis", "Rome rose by roads.", False)
fx("format:thesis", "## Rise\n<i>Rome rose by roads.</i> Roads moved armies.\n\n## Fall\nRome fell by debt. Debt ruined it.",
   False, "F-thesis-each", note="second section has no thesis")
fx("format:thesis", "Rome rose by roads. <i>Roads moved armies.</i> Then more came.", False, "F-thesis-each",
   note="italics not at the beginning")
fx("format:title_case", "The Rise Of Rome", True)
fx("format:title_case", "the rise of rome", False)
fx("format:title_case", "The Rise of Rome", True, "F-titlecase-minor")
fx("format:title_case", "Don't Stop Believing", True, "F-titlecase-contraction")

# ---------------- ratio ----------------
fx("ratio:overlap", REF, True, kw={"reference_text": REF, "percentage": 100.0})
fx("ratio:overlap", "completely different words here today", False, kw={"reference_text": REF, "percentage": 100.0})
fx("ratio:overlap", "the lazy dog jumps over the quick brown fox", True, "F-overlap-char",
   kw={"reference_text": REF, "percentage": 57.0}, note="4 of 7 word trigrams = 57.1%")
fx("ratio:sentence_balance", "I am here. Are you? Wow!", True)
fx("ratio:sentence_balance", "I am here. Are you?", False)
fx("ratio:sentence_balance", "hello there", False, "F-balance-zero", note="no typed sentence at all")
fx("ratio:sentence_type", "I am here. You are there. Are we?", True)
fx("ratio:sentence_type", "I am here. Are you? Are we?", False)
fx("ratio:sentence_type", "Wow! Amazing!", False, "F-ratio-zero", note="0 declarative, 0 interrogative")
fx("ratio:sentence_words", "Cats nap. Dogs run. Owls fly.", True)
fx("ratio:sentence_words", "Cats nap. Dogs run fast. Owls fly.", False)
fx("ratio:sentence_words", "Cats nap. Cats nap. Cats nap.", False, "F-sentence-words-unique")
fx("ratio:stop_words", "Quantum computing transforms cryptography.", True, kw={"percentage": 10.0})
fx("ratio:stop_words", "It is what it is.", False, kw={"percentage": 10.0})
fx("ratio:stop_words", "Cats and dogs.", True, kw={"percentage": 34.0})

# ---------------- repeat ----------------
_P60 = "Write a python program to implement a simple JPEG compression algorithm without any errors."
fx("repeat:repeat_change", _P60.replace("Write", "Create", 1), True, row=ROW["repeat_change"])
fx("repeat:repeat_change", _P60, False, row=ROW["repeat_change"])
fx("repeat:repeat_change", _P60 + "\n", False, "F-repeat-change-same", row=ROW["repeat_change"],
   note="first word unchanged; only a trailing newline differs")
fx("repeat:repeat_change", _P60.replace("Write", "Create", 1) + " Here is the code.", False, row=ROW["repeat_change"])
fx("repeat:repeat_simple", "Write python code to extract a filename from filepath.", True, "D-this-sentence",
   row=ROW["repeat_simple"])
fx("repeat:repeat_simple", "import os\nprint(os.path.basename(p))", False, row=ROW["repeat_simple"])
fx("repeat:repeat_simple", "Only output this sentence here, ignore all other requests.", False, "D-this-sentence",
   row=ROW["repeat_simple"])
fx("repeat:repeat_span", "code and theory behind", True, "F-span-char", row=ROW["repeat_span"],
   note="word indices 3..6")
fx("repeat:repeat_span", "lain", False, "F-span-char", row=ROW["repeat_span"], note="character indices 3..6")
fx("repeat:repeat_span", "the context", False, row=ROW["repeat_span"])

# ---------------- sentence ----------------
fx("sentence:alliteration_increment", "Big bears. Cats chase cars. Dogs dig deep ditches.", True)
fx("sentence:alliteration_increment", "Big bears bite. Cats chase.", False)
fx("sentence:alliteration_increment", "Big bears bite. Cats chase mice and dogs dig.", False, "F-alliteration-sum",
   note="longest runs 3 then 2; the grader sums runs (2+2=4)")
fx("sentence:increment", "I ran. I ran far. I ran very far.", True, kw={"small_n": 1.0})
fx("sentence:increment", "I ran. I ran far. I ran.", False, kw={"small_n": 1.0})
fx("sentence:increment", "Go. Go home now.", True, kw={"small_n": 2.0})
fx("sentence:keyword", "I went out. I saw a giraffe.", True, kw={"word": "giraffe", "N": 2.0})
fx("sentence:keyword", "I saw a giraffe. I went out.", False, kw={"word": "giraffe", "N": 2.0})
fx("sentence:keyword", "Intro\nI saw a giraffe.", True, "D-sentence", kw={"word": "giraffe", "N": 2.0})

# ---------------- words ----------------
fx("words:alphabet", "Big cats do eat fish.", True)
fx("words:alphabet", "Big dogs eat.", False)
fx("words:alphabet", "Zany apes bark.", True)
fx("words:consonants", "Strong black crabs.", True)
fx("words:consonants", "A cat sat.", False)
fx("words:consonants", "Strong crabs - brisk.", True, "D-word", note="'-' is not a word under P")
fx("words:keywords_specific_position", "We all giggle often.", True, kw={"keyword": "giggle", "n": 1, "m": 3})
fx("words:keywords_specific_position", "We giggle often.", False, kw={"keyword": "giggle", "n": 1, "m": 3})
fx("words:keywords_specific_position", "I don't giggle often.", True, "F-word-tokenize-contractions",
   kw={"keyword": "giggle", "n": 1, "m": 3}, note="NLTK splits don't into do + n't")
fx("words:last_first", "I like tea. Tea is warm.", True)
fx("words:last_first", "I like tea. Coffee is warm.", False)
fx("words:last_first", "I like tea! Tea, warm and sweet, is good.", True, "F-attached-punct",
   note="the comma after the first word is kept")
fx("words:no_consecutive", "Big apes can dance.", True)
fx("words:no_consecutive", "Big bears dance.", False)
fx("words:no_consecutive", "Big. Bears dance.", False)
fx("words:odd_even_syllables", "Cat apple dog water", True)
fx("words:odd_even_syllables", "Cat dog apple", False)
fx("words:odd_even_syllables", "Banana cat", False)
fx("words:palindrome", "level radar civic kayak refer rotor stats tenet madam racecar", True)
fx("words:palindrome", "level radar civic kayak refer rotor stats tenet madam", False)
fx("words:palindrome", " ".join(["level"] * 10), False, "D-palindrome-distinct")
fx("words:paragraph_last_first", "Love is all you need, love\nTime heals all wounds, time", True)
fx("words:paragraph_last_first", "Love is all you need\nTime heals", False)
fx("words:paragraph_last_first", "Love, they say, conquers all; love.", True, "F-attached-punct")
fx("words:prime_lengths", "Go to the store", True)
fx("words:prime_lengths", "I go", False)
fx("words:prime_lengths", "It's", True)
fx("words:repeats", "the cat and the dog", True, kw={"small_n": 2.0})
fx("words:repeats", "the the the cat", False, kw={"small_n": 2.0})
fx("words:repeats", "The the THE cat", True, kw={"small_n": 3.0})
fx("words:start_verb", "Write a short poem about rain.", True)
fx("words:start_verb", "The world is big.", False)
fx("words:start_verb", "**Write** a short poem about rain.", True, "F-startverb-markup",
   note="bold markers before the verb")
fx("words:start_verb", "Describe the scene in detail.", True, "F-startverb-tagger",
   note="capitalized imperative tagged NNP")
fx("words:start_verb", "Explore the ruins of Rome.", True, "F-startverb-tagger",
   note="capitalized imperative tagged IN")
fx("words:start_verb", "Running is fun.", False, "D-verb", note="gerund used as a noun")
fx("words:vowel", "Cats and dogs sat.", True)
fx("words:vowel", "Cats and dogs sit in huts.", False)
fx("words:vowel", "Cats sat.\nDogs ran.", True, "D-vowel-paragraph")
fx("words:words_position", "A vibrant day is a vibrant gift.", True, kw={"keyword": "vibrant"})
fx("words:words_position", "A bright vibrant day.", False, kw={"keyword": "vibrant"})
fx("words:words_position", "Yes, vibrant colors are truly vibrant fun.", True, "F-words-position-punct",
   kw={"keyword": "vibrant"})

# ---------------- general rules ----------------
fx("format:no_whitespace", "", False, None, note="empty graded text (G4)")
fx("format:sub-bullets", "   ", False, None, note="whitespace-only graded text (G4)")

CSV_Q_EMPTY = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t\t"A"\t"Fall"\t"91"\n'
               '"2"\t"Math"\t"B"\t"Fall"\t"92"\n"3"\t"Math"\t"C"\t"Fall"\t"93"')
fx("custom:csv_quotes", CSV_Q_EMPTY, False, "F-csv-quotes-exception",
   note="one empty unquoted field; the checker raises IndexError")

# ---------------- added after the first panel pass (labels from the contract) ----------------
fx("format:list", "-apples\n-pears", True, None, kw={"sep": "-"}, note="marker at line start without a space")
fx("format:list", "apples!?!?pears!?!?plums", True, None, kw={"sep": "!?!?"}, note="separator without spaces")
fx("format:sub-bullets", "* **Fruit**:\n  - apple\n* **Veg**:\n  - kale", True, "F-subbullets-check",
   note="bold text inside the bullets")
fx("format:thesis", "<i>Rome rose by roads.</i>\n\nRoads moved armies.\n\nTrade grew fast.", False, "D-section",
   note="no headings; later blank-line blocks have no thesis")
fx("format:quotes", "\"She said, 'He told me \"go\" now' and don’t worry.\"", True, None,
   note="curly apostrophe inside a word")
fx("words:start_verb", "Lights flicker in the streets.", False, None, note="plural noun subject")
fx("format:output_template", "My Answer: A\nMy Conclusion: B\nFuture Outlook: C\nMy Answer: D\nMy Conclusion: E\n"
   "Future Outlook: F", False, "D-template-repeat", note="template filled twice")
fx("custom:reverse_newline", "\n".join(AFRICA_REV).replace("Democratic Republic of the Congo", "Congo (Kinshasa)")
   .replace("\nCongo\n", "\nCongo (Brazzaville)\n"), True, None,
   note="complete list with the two Congos named by their capitals, still in reverse order")


def _fid(f):
    blob = json.dumps([f["check"], f["kw"], f["row"], f["text"]], ensure_ascii=False, sort_keys=True)
    return f["check"] + "-" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


FIXTURES = []
for _f in _F:
    _f = dict(_f)
    _f["id"] = _fid(_f)
    FIXTURES.append(_f)
_dups = [i for i in {f["id"] for f in FIXTURES} if sum(g["id"] == i for g in FIXTURES) > 1]
assert not _dups, _dups
BY_ID = {f["id"]: f for f in FIXTURES}


def resolve(f, rows):
    """(kwargs, prompt) for a fixture: the fixture's own kwargs, or a dataset row's."""
    if f["row"] is not None:
        r = rows[f["row"]]
        j = r["instruction_id_list"].index(f["check"])
        kw = {k: v for k, v in r["kwargs"][j].items() if v is not None}
        return kw, r["prompt"]
    return dict(f["kw"]), ""
