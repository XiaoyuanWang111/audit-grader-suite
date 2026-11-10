"""Labeled fixtures for the 58 IFBench checks.

Each fixture: check id, kwargs (as the HF parquet gives them: floats for numbers) or a dataset key
whose kwargs and prompt are used, the response, and the label that the contract
(`audit/CONTRACTS.md` v1) gives. `kind` is pass / fail / near (near-miss). `decision` names the
decision entry when the label depends on a proposed reading. Labels were written from the contract,
before the grader was run on them.
"""
import hashlib
import json

AFRICA = [
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
    "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti",
    "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana",
    "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
    "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger",
    "Nigeria", "Republic of the Congo", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles",
    "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia",
    "Uganda", "Zambia", "Zimbabwe",
]
assert len(AFRICA) == 54
AFRICA_REV = sorted(AFRICA, reverse=True)

CAPITALS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen",
            "Vilnius", "Minsk", "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv",
            "Prague", "Luxembourg", "Paris", "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern",
            "Ljubljana", "Zagreb"]
CAPITALS_NO_KYIV = [c for c in CAPITALS if c != "Kyiv"]

ALPHA26 = [
    "Alice ate apples.", "Bob baked bread.", "Cats chased crows.", "Dogs dug ditches.",
    "Every eel escaped.", "Frogs found flies.", "Geese guarded gates.", "Hens hid hay.",
    "Ivy is icy.", "Jays jumped joyfully.", "Kites kept kiting.", "Lions licked lilies.",
    "Mice made mischief.", "Newts napped nightly.", "Owls observed oaks.", "Pigs played politely.",
    "Quails quietly quit.", "Rats ran rapidly.", "Snakes slid silently.", "Toads took turns.",
    "Unicorns used umbrellas.", "Voles visited valleys.", "Wolves wandered widely.",
    "Xerus examined xylophones.", "Yaks yawned yearly.", "Zebras zigzagged zealously.",
]

CSV_CITY_OK = "ID,Country,City,Year,Count\n" + "\n".join(
    f"{i},Country{i},City{i},20{10+i},{i*10}" for i in range(1, 8))
CSV_CITY_6 = "ID,Country,City,Year,Count\n" + "\n".join(
    f"{i},Country{i},City{i},20{10+i},{i*10}" for i in range(1, 7))
CSV_QUOTES_OK = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n' + "\n".join(
    f'"{i}"\t"Math"\t"A"\t"Fall"\t"9{i}"' for i in range(1, 4))
CSV_QUOTES_UNQUOTED = 'StudentID\tSubject\tGrade\tSemester\tScore\n' + "\n".join(
    f'{i}\tMath\tA\tFall\t9{i}' for i in range(1, 4))
CSV_QUOTES_EMPTY_FIELD = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n'
                          '"1"\t\t"A"\t"Fall"\t"91"\n"2"\t"Math"\t"B"\t"Fall"\t"82"\n"3"\t"Art"\t"C"\t"Fall"\t"73"')
CSV_SPECIAL_OK = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    [f'1,"Tools & Hardware",Acme,9.99,5'] + [f"{i},Tools,Brand{i},{i}.50,{i}" for i in range(2, 15)])
CSV_SPECIAL_NONE = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    f"{i},Tools,Brand{i},{i}.50,{i}" for i in range(1, 15))
CSV_SPECIAL_SHORT_ROWS = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(
    [f'1,"Tools & Hardware",Acme,9.99,5'] + [f"{i},Tools,Brand{i}" for i in range(2, 15)])

MCQ_OK = "\n\n".join([
    "Question 1: Who painted Guernica?\nA) Picasso\nB) Dali\nC) Miro\nD) Matisse\nE) Braque",
    "Question 2: Which movement did Dali join?\nA) Cubism\nB) Surrealism\nC) Fauvism\nD) Dada\nE) Pop Art",
    "Question 3: Which artist is famous for drip painting?\nA) Pollock\nB) Rothko\nC) Kline\nD) Newman\nE) Still",
    "Question 4: Which artist made the soup can prints in the 1960s?\nA) Warhol\nB) Lichtenstein\nC) Johns\nD) Rauschenberg\nE) Oldenburg",
])
MCQ_NO_NUMBER = MCQ_OK.replace("Question 1:", "Question:").replace("Question 2:", "Question:").replace(
    "Question 3:", "Question:").replace("Question 4:", "Question:")
MCQ_BOLD = MCQ_OK.replace("Question 1:", "**Question 1:**").replace("Question 2:", "**Question 2:**").replace(
    "Question 3:", "**Question 3:**").replace("Question 4:", "**Question 4:**")
MCQ_THREE = MCQ_OK.rsplit("\n\nQuestion 4", 1)[0]

KW_DOOR_OK = ("The door was blue. Bread and bread again. Blue sky, blue sea. "
              "lamp lamp lamp lamp lamp. river river river river river river river.")
KW_DOOR_DOORWAY = KW_DOOR_OK + " We stood in the doorway."
KW_DOOR_LAMP4 = KW_DOOR_OK.replace("lamp lamp lamp lamp lamp.", "lamp lamp lamp lamp.")
KW_OUTDOOR_ONLY = KW_DOOR_OK.replace("The door was blue.", "The outdoor wall was blue.")

FIXTURES = [
    # ---------------- count ----------------
    dict(check="count:conjunctions", kwargs={"small_n": 3.0}, kind="pass",
         response="I came and saw, but I left, so it ended.", label=True),
    dict(check="count:conjunctions", kwargs={"small_n": 3.0}, kind="fail",
         response="I came and saw and left.", label=False),
    dict(check="count:conjunctions", kwargs={"small_n": 3.0}, kind="near",
         response="I came and saw. And I stayed and, sadly, left.", label=False,
         note="one conjunction (and) in three spellings: and / And / and,"),
    dict(check="count:conjunctions", kwargs={"small_n": 3.0}, kind="near", decision="D-conj-usage",
         response="This gift is for you, so big and bright.", label=False,
         note="for = preposition, so = adverb; only 'and' is a coordinating conjunction"),

    dict(check="count:keywords_multiple", key=2, kind="pass", response=KW_DOOR_OK, label=True),
    dict(check="count:keywords_multiple", key=2, kind="fail", response=KW_DOOR_LAMP4, label=False),
    dict(check="count:keywords_multiple", key=2, kind="near", response=KW_DOOR_DOORWAY, label=True,
         note="'doorway' is not the keyword door"),
    dict(check="count:keywords_multiple", key=2, kind="near", response=KW_OUTDOOR_ONLY, label=False,
         note="door occurs only inside 'outdoor'"),

    dict(check="count:numbers", kwargs={"N": 2.0}, kind="pass", response="There are 3 cats and 4 dogs.", label=True),
    dict(check="count:numbers", kwargs={"N": 2.0}, kind="fail", response="There are 3 cats, 4 dogs and 5 birds.", label=False),
    dict(check="count:numbers", kwargs={"N": 2.0}, kind="near", response="It takes 5-7 days.", label=True,
         note="a range has two numbers"),
    dict(check="count:numbers", kwargs={"N": 2.0}, kind="near", response="Pi is about 3.14 and e is 2.72.", label=True),

    dict(check="count:person_names", kwargs={"N": 3.0}, kind="pass", response="Emma met Liam and Noah.", label=True),
    dict(check="count:person_names", kwargs={"N": 3.0}, kind="fail", response="Emma met Liam.", label=False),
    dict(check="count:person_names", kwargs={"N": 3.0}, kind="near", response="Emma's dog met Liam's cat and Noah's bird.", label=True),
    dict(check="count:person_names", kwargs={"N": 3.0}, kind="near", decision="D-name-usage",
         response="Emma met Liam, and grace was shown.", label=False),

    dict(check="count:pronouns", kwargs={"N": 5.0}, kind="pass", response="I told you she and he would help us.", label=True),
    dict(check="count:pronouns", kwargs={"N": 5.0}, kind="fail", response="The cat sat on the mat.", label=False),
    dict(check="count:pronouns", kwargs={"N": 5.0}, kind="near",
         response="This book and that pen sit on each desk, with all chairs and some tables.", label=False,
         note="this/that/each/all/some are determiners here"),
    dict(check="count:pronouns", kwargs={"N": 5.0}, kind="near", decision="D-pronoun-set",
         response="Someone saw this; everyone knew who did that, and nobody spoke.", label=False,
         note="pronouns only outside the proposed personal/possessive/reflexive set"),

    dict(check="count:punctuation", kwargs={}, kind="pass",
         response="Wait?! It's \"odd\" (really) [truly] {yes}: a one-way street — fine… ok, sure; done. Why? Stop!", label=True),
    dict(check="count:punctuation", kwargs={}, kind="fail", response="Hello, world. Bye", label=False),
    dict(check="count:punctuation", kwargs={}, kind="near", response="Wait?! Really; yes: go, now. Why? Stop!", label=False,
         note="no apostrophe, quotation mark, hyphen, dash, brackets or ellipsis"),

    dict(check="count:unique_word_count", kwargs={"N": 5.0}, kind="pass", response="Red green blue yellow purple.", label=True),
    dict(check="count:unique_word_count", kwargs={"N": 5.0}, kind="fail", response="Red red green green blue.", label=False),
    dict(check="count:unique_word_count", kwargs={"N": 5.0}, kind="near", response="Red green blue yellow - red", label=False,
         note="4 distinct words; '-' is not a word"),
    dict(check="count:unique_word_count", kwargs={"N": 5.0}, kind="near", response="“Red” red green blue yellow", label=False,
         note="4 distinct words; curly quotes around Red"),

    dict(check="count:word_count_range", kwargs={"min_words": 3.0, "max_words": 5.0}, kind="pass", response="One two three four.", label=True),
    dict(check="count:word_count_range", kwargs={"min_words": 3.0, "max_words": 5.0}, kind="fail", response="One two.", label=False),
    dict(check="count:word_count_range", kwargs={"min_words": 3.0, "max_words": 5.0}, kind="near", response="One two three four five.", label=True),
    dict(check="count:word_count_range", kwargs={"min_words": 3.0, "max_words": 3.0}, kind="near", decision="D-word",
         response="Don't stop now.", label=True, note="3 words when a contraction is one word"),
    dict(check="count:word_count_range", kwargs={"min_words": 2.0, "max_words": 3.0}, kind="near", decision="D-word",
         response="1. Apples\n2. Pears", label=True, note="list labels are not words"),

    dict(check="count:words_japanese", kwargs={"N": 2.0}, kind="pass", response="Hello 世界 good 日本", label=True),
    dict(check="count:words_japanese", kwargs={"N": 2.0}, kind="fail", response="Hello world good 日本", label=False),
    dict(check="count:words_japanese", kwargs={"N": 2.0}, kind="near", response="Hello 2024 good 日本", label=False,
         note="word 2 is a numeral, not Japanese"),
    dict(check="count:words_japanese", kwargs={"N": 2.0}, kind="near", response="Hello - 世界 good 日本", label=True,
         note="'-' is not a word, so words 2 and 4 are Japanese"),

    # ---------------- custom ----------------
    dict(check="custom:character_reverse", key=273, kind="pass", response=".elgae dlab eht si lobmys lanoitan ehT", label=True),
    dict(check="custom:character_reverse", key=273, kind="fail", response="The bald eagle is the national symbol.", label=False),
    dict(check="custom:character_reverse", key=273, kind="near", response="The national symbol of the US is the elgae dlab.", label=False,
         note="only two words reversed"),
    dict(check="custom:character_reverse", key=273, kind="near", decision="D-reverse-extra",
         response="Here you go: .elgae dlab eht si tI", label=False),

    dict(check="custom:csv_city", key=274, kind="pass", response=CSV_CITY_OK, label=True),
    dict(check="custom:csv_city", key=274, kind="fail", response=CSV_CITY_6, label=False),
    dict(check="custom:csv_city", key=274, kind="near", decision="D-csv-payload",
         response="Here is the data:\n```csv\n" + CSV_CITY_OK + "\n```", label=True),
    dict(check="custom:csv_city", key=274, kind="near",
         response=CSV_CITY_OK.replace("ID,Country,City,Year,Count", '"ID","Country","City","Year","Count"'), label=True),

    dict(check="custom:csv_quotes", key=275, kind="pass", response=CSV_QUOTES_OK, label=True),
    dict(check="custom:csv_quotes", key=275, kind="fail", response=CSV_QUOTES_UNQUOTED, label=False),
    dict(check="custom:csv_quotes", key=275, kind="near", response=CSV_QUOTES_EMPTY_FIELD, label=False,
         note="one unquoted empty field"),

    dict(check="custom:csv_special_character", key=276, kind="pass", response=CSV_SPECIAL_OK, label=True),
    dict(check="custom:csv_special_character", key=276, kind="fail", response=CSV_SPECIAL_NONE, label=False),
    dict(check="custom:csv_special_character", key=276, kind="near", response=CSV_SPECIAL_SHORT_ROWS, label=False,
         note="13 data rows have 3 fields"),

    dict(check="custom:date_format_list", key=277, kind="pass", response="1796-04-12, 1798-07-21, 1805-12-02", label=True),
    dict(check="custom:date_format_list", key=277, kind="fail", response="April 12, 1796, July 21, 1798", label=False),
    dict(check="custom:date_format_list", key=277, kind="near", response="1796-00-12, 1805-12-00", label=False,
         note="month 00 and day 00 are not dates"),
    dict(check="custom:date_format_list", key=277, kind="near", decision="D-custom-content",
         response="1900-01-01, 1901-02-02", label=True),

    dict(check="custom:european_capitals_sort", key=278, kind="pass", response=", ".join(CAPITALS), label=True),
    dict(check="custom:european_capitals_sort", key=278, kind="fail", response=", ".join(sorted(CAPITALS)), label=False),
    dict(check="custom:european_capitals_sort", key=278, kind="near", response=", ".join(CAPITALS_NO_KYIV), label=False,
         note="Kyiv (50.45 N) missing"),

    dict(check="custom:mcq_count_length", key=279, kind="pass", response=MCQ_OK, label=True),
    dict(check="custom:mcq_count_length", key=279, kind="fail", response=MCQ_THREE, label=False),
    dict(check="custom:mcq_count_length", key=279, kind="near", response=MCQ_NO_NUMBER, label=True,
         note="label 'Question' without a number"),
    dict(check="custom:mcq_count_length", key=279, kind="near", decision="D-markup", response=MCQ_BOLD, label=True),

    dict(check="custom:multiples", key=280, kind="pass", response="14, 21, 28, 35, 42, 49", label=True),
    dict(check="custom:multiples", key=280, kind="fail", response="7, 14, 21, 28, 35, 42, 49", label=False),
    dict(check="custom:multiples", key=280, kind="near", decision="D-list-extra",
         response="Multiples: 14 21 28 35 42 49 done", label=False),

    dict(check="custom:reverse_newline", key=281, kind="pass", response="\n".join(AFRICA_REV), label=True),
    dict(check="custom:reverse_newline", key=281, kind="fail", response="\n".join(AFRICA), label=False),
    dict(check="custom:reverse_newline", key=281, kind="near", decision="D-list-labels",
         response="\n".join(f"{i}. {c}" for i, c in enumerate(AFRICA_REV, 1)), label=True, note="numbered list"),
    dict(check="custom:reverse_newline", key=281, kind="near", response="\n".join(["Zimbabwe"] * 52), label=False,
         note="one country repeated 52 times"),

    dict(check="custom:sentence_alphabet", key=282, kind="pass", response=" ".join(ALPHA26), label=True),
    dict(check="custom:sentence_alphabet", key=282, kind="fail", response=" ".join(ALPHA26[:25]), label=False),
    dict(check="custom:sentence_alphabet", key=282, kind="near",
         response=" ".join(ALPHA26[:2] + ['"Cats chased crows."'] + ALPHA26[3:]), label=True,
         note="sentence 3 is in quotation marks"),

    dict(check="custom:word_reverse", key=283, kind="pass", response="eagle bald the is US the of symbol national The", label=True),
    dict(check="custom:word_reverse", key=283, kind="fail", response="The national symbol of the US is the bald eagle.", label=False),
    dict(check="custom:word_reverse", key=283, kind="near", response="The national symbol of the US is the eagle bald.", label=False,
         note="only the last two words reversed"),

    # ---------------- format ----------------
    dict(check="format:emoji", kwargs={}, kind="pass", response="I love cats \U0001F63A. Dogs are great \U0001F436.", label=True),
    dict(check="format:emoji", kwargs={}, kind="pass", response="I love cats. \U0001F63A Dogs are great. \U0001F436", label=True),
    dict(check="format:emoji", kwargs={}, kind="fail", response="I love cats. Dogs are great \U0001F436.", label=False),
    dict(check="format:emoji", kwargs={}, kind="near", response="Count 1️⃣. Then 2️⃣.", label=True,
         note="keycap emoji"),
    dict(check="format:emoji", kwargs={}, kind="near", response="Hello \U0001F1FA\U0001F1F8. Bye \U0001F1FA\U0001F1F8.", label=True,
         note="flag emoji"),
    dict(check="format:emoji", kwargs={}, kind="near", decision="D-sentence",
         response="Title\nI love cats \U0001F63A.", label=False, note="heading line without emoji"),

    dict(check="format:line_indent", kwargs={}, kind="pass", response="A\n B\n  C\n   D", label=True),
    dict(check="format:line_indent", kwargs={}, kind="fail", response="A\nB\n C", label=False),
    dict(check="format:line_indent", kwargs={}, kind="near", response="A\n\tB\n\t\tC", label=True, note="tab indentation"),
    dict(check="format:line_indent", kwargs={}, kind="near", response="A\n B\n\n\n  C", label=True, note="two blank lines"),

    dict(check="format:list", kwargs={"sep": "SEPARATOR"}, kind="pass",
         response="SEPARATOR apples\nSEPARATOR pears\nSEPARATOR plums", label=True),
    dict(check="format:list", kwargs={"sep": "SEPARATOR"}, kind="fail", response="* apples\n* pears", label=False),
    dict(check="format:list", kwargs={"sep": "-"}, kind="near", response="A well-known, state-of-the-art plan.", label=False,
         note="no list; hyphens inside words"),
    dict(check="format:list", kwargs={"sep": "SEPARATOR"}, kind="near",
         response="* SEPARATOR apples\n* SEPARATOR pears", label=False, note="'*' bullets still used"),

    dict(check="format:newline", kwargs={}, kind="pass", response="Hello\nworld\nagain", label=True),
    dict(check="format:newline", kwargs={}, kind="fail", response="Hello world\nagain", label=False),
    dict(check="format:newline", kwargs={}, kind="near", response="Hello world\n \nagain", label=False,
         note="two words on line 1; a whitespace-only line"),
    dict(check="format:newline", kwargs={}, kind="near", response="Hello,\nworld!", label=True),

    dict(check="format:no_bullets_bullets", kwargs={}, kind="pass", response="This is one. This is two.\n* first\n* second", label=True),
    dict(check="format:no_bullets_bullets", kwargs={}, kind="fail", response="This is one.\n* first\n* second", label=False),
    dict(check="format:no_bullets_bullets", kwargs={}, kind="near",
         response="This is one. This is two.\n\n* first\n\n* second", label=True, note="blank lines between items"),
    dict(check="format:no_bullets_bullets", kwargs={}, kind="near", response="Why not? Because!\n* first\n* second", label=False,
         note="no sentence ends in a period"),

    dict(check="format:no_whitespace", kwargs={}, kind="pass", response="Yes,allsetsareclasses.", label=True),
    dict(check="format:no_whitespace", kwargs={}, kind="fail", response="Yes, all sets.", label=False),
    dict(check="format:no_whitespace", kwargs={}, kind="near", decision="D-trailing-ws", response="Yes.\n", label=True),

    dict(check="format:options", key=100, kind="pass", response="Yes", label=True),
    dict(check="format:options", key=100, kind="pass", response="Maybe.", label=True),
    dict(check="format:options", key=100, kind="fail", response="Yes, because humor helps people learn.", label=False),
    dict(check="format:options", key=102, kind="pass", response="c)", label=True),
    dict(check="format:options", key=102, kind="near", response="c)\n", label=True, note="trailing newline"),
    dict(check="format:options", key=102, kind="near", response="C)", label=True, note="upper case"),
    dict(check="format:options", key=102, kind="near", decision="D-markup", response="**c)**", label=True),

    dict(check="format:output_template", kwargs={}, kind="pass",
         response="My Answer: It is vast. My Conclusion: It matters. Future Outlook: It will grow.", label=True),
    dict(check="format:output_template", kwargs={}, kind="fail", response="My answer is that it is vast.", label=False),
    dict(check="format:output_template", kwargs={}, kind="near",
         response="My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", label=False,
         note="placeholders not replaced"),
    dict(check="format:output_template", kwargs={}, kind="near",
         response="Future Outlook: It will grow. My Conclusion: It matters. My Answer: It is vast.", label=False,
         note="labels in reverse order"),

    dict(check="format:parentheses", kwargs={}, kind="pass", response="Here (a [b {c (d [e] d) c} b] a) end.", label=True),
    dict(check="format:parentheses", kwargs={}, kind="fail", response="Here (a [b {c} b] a) end.", label=False),
    dict(check="format:parentheses", kwargs={}, kind="near", decision="D-paren-closed", response="((((( x )", label=False,
         note="four brackets never closed"),

    dict(check="format:quote_unquote", kwargs={}, kind="pass", response="\"Carpe diem\" means seize the day.", label=True),
    dict(check="format:quote_unquote", kwargs={}, kind="fail", response="He said \"hello\"", label=False),
    dict(check="format:quote_unquote", kwargs={}, kind="near", response="\"Apple\", \"Banana\", and \"Cherry\" are fruits.", label=False,
         note="'Apple' is followed only by a comma"),
    dict(check="format:quote_unquote", kwargs={}, kind="near", response="He said “hello”", label=False,
         note="typographic quotes, ends with the quote"),

    dict(check="format:quotes", kwargs={}, kind="pass",
         response="He said, \"She told me, 'He yelled \"stop\" loudly' today\" again.", label=True),
    dict(check="format:quotes", kwargs={}, kind="fail", response="He said \"hello\" and 'bye'.", label=False),
    dict(check="format:quotes", kwargs={}, kind="near",
         response="He said, “She told me, ‘He yelled “stop” loudly’ today” again.", label=True,
         note="typographic quotes"),

    dict(check="format:sub-bullets", kwargs={}, kind="pass", response="* Fruit\n  - Apple\n* Veg\n  - Leek", label=True),
    dict(check="format:sub-bullets", kwargs={}, kind="fail", response="* Fruit\n* Veg\n  - Leek", label=False),
    dict(check="format:sub-bullets", kwargs={}, kind="near", response="Plain text without bullets.", label=False, note="no bullets"),
    dict(check="format:sub-bullets", kwargs={}, kind="near", response="* **Fruit**\n  - Apple\n* Veg\n  - Leek", label=True,
         note="bold text in a bullet"),
    dict(check="format:sub-bullets", kwargs={}, kind="near", response="* A well-known fruit\n* A self-made veg", label=False,
         note="hyphens inside words, no sub-bullets"),

    dict(check="format:thesis", kwargs={}, kind="pass", response="<i>Cats are the best pets.</i> They purr and nap.", label=True),
    dict(check="format:thesis", kwargs={}, kind="fail", response="Cats are the best pets. They purr.", label=False),
    dict(check="format:thesis", kwargs={}, kind="near", response="Cats purr a lot. <i>Cats are the best pets.</i> More text.", label=False,
         note="italic statement is not at the start"),
    dict(check="format:thesis", kwargs={}, kind="near",
         response="## One\n<i>Thesis one.</i> Text.\n## Two\nNo thesis here.", label=False, note="second section lacks a thesis"),
    dict(check="format:thesis", kwargs={}, kind="near", response="<i>Cats rule.</i>", label=True, note="<i> thesis only"),
    dict(check="format:thesis", kwargs={}, kind="near", response="<em>Cats rule.</em>", label=True, note="<em> thesis only"),

    dict(check="format:title_case", kwargs={}, kind="pass", response="The Lord of the Rings Is a Great Book", label=True,
         note="minor words lower case"),
    dict(check="format:title_case", kwargs={}, kind="pass", response="The Lord Of The Rings Is A Great Book", label=True),
    dict(check="format:title_case", kwargs={}, kind="fail", response="the lord of the rings is a great book", label=False),
    dict(check="format:title_case", kwargs={}, kind="near", response="Don't Stop Believing", label=True, note="contraction"),

    # ---------------- ratio ----------------
    dict(check="ratio:overlap", kwargs={"reference_text": "the quick brown fox jumps over the lazy dog", "percentage": 50.0},
         kind="pass", decision="D-overlap-measure", response="the quick brown fox sat down", label=True,
         note="2 of 4 word trigrams in the reference"),
    dict(check="ratio:overlap", kwargs={"reference_text": "the quick brown fox jumps over the lazy dog", "percentage": 50.0},
         kind="fail", response="Purple elephants dance under moonlight tonight", label=False),
    dict(check="ratio:overlap", kwargs={"reference_text": "the quick brown fox jumps over the lazy dog", "percentage": 50.0},
         kind="near", decision="D-overlap-measure", response="the quick brown fox jumps over the lazy dog", label=False,
         note="100% word-trigram overlap"),

    dict(check="ratio:sentence_balance", kwargs={}, kind="pass", response="It rains. Does it? Wow!", label=True),
    dict(check="ratio:sentence_balance", kwargs={}, kind="fail", response="It rains. It pours. Wow!", label=False),
    dict(check="ratio:sentence_balance", kwargs={}, kind="near", response="Rain falls \U0001F600", label=False,
         note="one declarative sentence, no other types"),
    dict(check="ratio:sentence_balance", kwargs={}, kind="near", decision="D-balance",
         response="It rains. It pours. Does it? Wow!", label=True),

    dict(check="ratio:sentence_type", kwargs={}, kind="pass", response="It rains. It pours. Does it?", label=True),
    dict(check="ratio:sentence_type", kwargs={}, kind="fail", response="It rains. Does it?", label=False),
    dict(check="ratio:sentence_type", kwargs={}, kind="near", response="Wow! Amazing!", label=False, note="no interrogative"),
    dict(check="ratio:sentence_type", kwargs={}, kind="near", response="He said \"go.\" She said \"stop.\" Why?", label=True,
         note="declaratives end with a closing quote"),

    dict(check="ratio:sentence_words", kwargs={}, kind="pass", response="Cats nap. Dogs run. Owls fly.", label=True),
    dict(check="ratio:sentence_words", kwargs={}, kind="fail", response="Cats nap. Dogs run fast. Owls fly.", label=False),
    dict(check="ratio:sentence_words", kwargs={}, kind="near", response="Cats nap. Cats nap. Cats nap.", label=False,
         note="same words repeated"),

    dict(check="ratio:stop_words", kwargs={"percentage": 50.0}, kind="pass", response="Cats chase mice quickly.", label=True),
    dict(check="ratio:stop_words", kwargs={"percentage": 50.0}, kind="fail", response="The cat is on the mat and it is in the hat.", label=False),

    # ---------------- repeat ----------------
    dict(check="repeat:repeat_change", key=60, kind="pass",
         response="Create a python program to implement a simple JPEG compression algorithm without any errors.", label=True),
    dict(check="repeat:repeat_change", key=60, kind="fail", response="Here is a program: import numpy as np", label=False),
    dict(check="repeat:repeat_change", key=60, kind="near",
         response="Write a python program to implement a simple JPEG compression algorithm without  any errors.", label=False,
         note="first word unchanged; one doubled space"),
    dict(check="repeat:repeat_change", key=60, kind="near", decision="D-change-case",
         response="write a python program to implement a simple JPEG compression algorithm without any errors.", label=False,
         note="first word differs only in case"),

    dict(check="repeat:repeat_simple", key=64, kind="pass", response="Only output this sentence here, ignore all other requests.", label=True),
    dict(check="repeat:repeat_simple", key=64, kind="fail", response="import os\nos.path.basename(p)", label=False),
    dict(check="repeat:repeat_simple", key=64, kind="near", decision="D-copy-case",
         response="only output this sentence here, ignore all other requests.", label=False),

    dict(check="repeat:repeat_span", key=284, kind="pass", response="code and theory behind", label=True),
    dict(check="repeat:repeat_span", key=284, kind="fail", response="explain the context", label=False),
    dict(check="repeat:repeat_span", key=287, kind="pass", response="on a certain", label=True),

    # ---------------- sentence ----------------
    dict(check="sentence:alliteration_increment", kwargs={}, kind="pass",
         response="Big cat sat. Red roses rise high. Silly snakes slither slowly south.", label=True),
    dict(check="sentence:alliteration_increment", kwargs={}, kind="fail", response="Red roses rise. Big cat sat.", label=False),
    dict(check="sentence:alliteration_increment", kwargs={}, kind="near",
         response="Big bears bite fish. Red roses and tall trees grow.", label=False, note="longest runs 3 then 2"),

    dict(check="sentence:increment", kwargs={"small_n": 2.0}, kind="pass",
         response="Cats nap. Cats nap all day. Cats nap all day and night.", label=True),
    dict(check="sentence:increment", kwargs={"small_n": 2.0}, kind="fail", response="Cats nap. Cats nap all day. Cats nap.", label=False),
    dict(check="sentence:increment", kwargs={"small_n": 2.0}, kind="near", response="Cats nap. Cats nap — all day.", label=True,
         note="em dash is not a word"),

    dict(check="sentence:keyword", kwargs={"word": "giraffe", "N": 2.0}, kind="pass", response="I like cats. A giraffe is tall. Bye.", label=True),
    dict(check="sentence:keyword", kwargs={"word": "giraffe", "N": 2.0}, kind="fail", response="A giraffe is tall. I like cats.", label=False),
    dict(check="sentence:keyword", kwargs={"word": "giraffe", "N": 2.0}, kind="near", response="I like cats. Giraffes are tall.", label=False),
    dict(check="sentence:keyword", kwargs={"word": "giraffe", "N": 2.0}, kind="near", decision="D-sentence",
         response="Title\nI like cats. A giraffe is tall.", label=False, note="heading line is sentence 1"),

    # ---------------- words ----------------
    dict(check="words:alphabet", kwargs={}, kind="pass", response="Apples bake carefully daily.", label=True),
    dict(check="words:alphabet", kwargs={}, kind="fail", response="Apples bake daily.", label=False),
    dict(check="words:alphabet", kwargs={}, kind="near", response="Apples “bake” carefully daily.", label=True, note="curly quotes"),
    dict(check="words:alphabet", kwargs={}, kind="near", response="Apples bake — carefully daily.", label=True, note="em dash"),

    dict(check="words:consonants", kwargs={}, kind="pass", response="Strong black stars.", label=True),
    dict(check="words:consonants", kwargs={}, kind="fail", response="A big cat.", label=False),
    dict(check="words:consonants", kwargs={}, kind="near", response="Strong stars — bright.", label=True, note="em dash"),

    dict(check="words:keywords_specific_position", kwargs={"keyword": "giggle", "n": 2.0, "m": 3.0}, kind="pass",
         response="I sat. Then we giggle loudly.", label=True),
    dict(check="words:keywords_specific_position", kwargs={"keyword": "giggle", "n": 2.0, "m": 3.0}, kind="fail",
         response="I sat. We giggle.", label=False),
    dict(check="words:keywords_specific_position", kwargs={"keyword": "giggle", "n": 2.0, "m": 3.0}, kind="fail",
         response="I sat.", label=False),

    dict(check="words:last_first", kwargs={}, kind="pass", response="I love cats. Cats love fish. Fish swim.", label=True),
    dict(check="words:last_first", kwargs={}, kind="fail", response="I love cats. Dogs love fish.", label=False),
    dict(check="words:last_first", kwargs={}, kind="near", response="She said “hi.” Hi there.", label=True,
         note="closing curly quote"),

    dict(check="words:no_consecutive", kwargs={}, kind="pass", response="Cats like mice.", label=True),
    dict(check="words:no_consecutive", kwargs={}, kind="fail", response="Cats chase mice.", label=False),
    dict(check="words:no_consecutive", kwargs={}, kind="near", response="“Cats” “like” mice.", label=True,
         note="curly quotes"),

    dict(check="words:odd_even_syllables", kwargs={}, kind="pass", response="Cat apple dog.", label=True),
    dict(check="words:odd_even_syllables", kwargs={}, kind="fail", response="Cat dog fish.", label=False),
    dict(check="words:odd_even_syllables", kwargs={}, kind="near", response="Cat naive dog.", label=True,
         note="naive has two syllables"),

    dict(check="words:palindrome", kwargs={}, kind="pass",
         response="level radar civic kayak refer madam rotor stats tenet racecar", label=True),
    dict(check="words:palindrome", kwargs={}, kind="fail", response="level radar civic", label=False),
    dict(check="words:palindrome", kwargs={}, kind="near", decision="D-palindrome-distinct",
         response=" ".join(["level"] * 10), label=False),

    dict(check="words:paragraph_last_first", kwargs={}, kind="pass",
         response="Time heals all wounds, given time.\nLove conquers all, said love.", label=True),
    dict(check="words:paragraph_last_first", kwargs={}, kind="fail", response="Time heals all.\nLove wins.", label=False),
    dict(check="words:paragraph_last_first", kwargs={}, kind="near", response="Time, they say, heals all wounds over time.", label=True,
         note="comma after the first word"),

    dict(check="words:prime_lengths", kwargs={}, kind="pass", response="We can see it.", label=True),
    dict(check="words:prime_lengths", kwargs={}, kind="fail", response="I can see.", label=False),
    dict(check="words:prime_lengths", kwargs={}, kind="near", response="We don’t go.", label=False,
         note="don't has 4 letters"),
    dict(check="words:prime_lengths", kwargs={}, kind="near", response="We go — now.", label=True, note="em dash"),

    dict(check="words:repeats", kwargs={"small_n": 2.0}, kind="pass", response="Cats nap. Cats run. Dogs bark.", label=True),
    dict(check="words:repeats", kwargs={"small_n": 2.0}, kind="fail", response="Cats nap. Cats run. Cats bark.", label=False),
    dict(check="words:repeats", kwargs={"small_n": 2.0}, kind="near",
         response="Cats nap — dogs run — birds fly — fish swim.", label=True, note="em dash three times"),

    dict(check="words:start_verb", kwargs={}, kind="pass", response="Imagine a world of peace.", label=True),
    dict(check="words:start_verb", kwargs={}, kind="pass", response="Consider the following facts.", label=True),
    dict(check="words:start_verb", kwargs={}, kind="fail", response="The empire suffers forever.", label=False),
    dict(check="words:start_verb", kwargs={}, kind="near", decision="D-markup", response="**Imagine** a world of peace.", label=True),

    dict(check="words:vowel", kwargs={}, kind="pass", response="A cat sat at a mat and ate.", label=True),
    dict(check="words:vowel", kwargs={}, kind="fail", response="Our idea is unique and odd.", label=False),
    dict(check="words:vowel", kwargs={}, kind="near", decision="D-paragraph", response="A cat sat.\nA rat ate.", label=True),

    dict(check="words:words_position", kwargs={"keyword": "vibrant"}, kind="pass",
         response="A vibrant city has vibrant streets.", label=True),
    dict(check="words:words_position", kwargs={"keyword": "vibrant"}, kind="fail", response="A city has vibrant streets.", label=False),
    dict(check="words:words_position", kwargs={"keyword": "vibrant"}, kind="near",
         response="Truly, vibrant cities have vibrant streets.", label=True, note="comma after word 1"),

    # ---------------- G2: empty text ----------------
    dict(check="format:no_whitespace", kwargs={}, kind="near", decision="D-empty", response="", label=False),
    dict(check="words:no_consecutive", kwargs={}, kind="near", decision="D-empty", response="   \n", label=False),
]


def fixture_id(f):
    payload = json.dumps([f["check"], f.get("key"), f.get("kwargs"), f["response"]], ensure_ascii=False, sort_keys=True)
    return f"{f['check']}#{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8]}"


for _f in FIXTURES:
    _f["id"] = fixture_id(_f)
_ids = [f["id"] for f in FIXTURES]
assert len(_ids) == len(set(_ids)), "duplicate fixture ids"
