"""Labeled fixtures for the IFBench checks, labeled from audit/CONTRACTS.md alone.

Each fixture: check id, kwargs (as in the dataset, numeric values given as ints here;
the runner also feeds them as floats, the type the parquet stores), response, label
("pass"/"fail") and tags. A tag "D-..." means the label depends on that decision
entry's proposed reading; a fixture without D-tags is unambiguous under the contract.
"""
import hashlib
import json

NAMES = ("Emma, Liam, Sophia, Jackson, Olivia, Noah, Ava, Lucas, Isabella, Mason, Mia, Ethan, "
         "Charlotte, Alexander, Amelia, Benjamin, Harper, Leo, Zoe, Daniel, Chloe, Samuel, Lily, "
         "Matthew, Grace, Owen, Abigail, Gabriel, Ella, Jacob, Scarlett, Nathan, Victoria, Elijah, "
         "Layla, Nicholas, Audrey, David, Hannah, Christopher, Penelope, Thomas, Nora, Andrew, Aria, "
         "Joseph, Claire, Ryan, Stella, Jonathan")

KW5 = {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
KM_PASS = ("The door. Bread, bread. Blue blue blue. Lamp lamp lamp lamp lamp. "
           "River river river river river river river.")

CSV_CITY_ROWS = ["1,France,Paris,2020,15", "2,Japan,Tokyo,2021,30", "3,Brazil,Rio de Janeiro,2019,12",
                 "4,Canada,Toronto,2022,8", "5,Kenya,Nairobi,2018,21", "6,India,Mumbai,2020,44",
                 "7,Spain,Madrid,2023,17", "8,Chile,Santiago,2017,9"]
CSV_CITY_HDR = "ID,Country,City,Year,Count"

Q = '"'
def _tabq(fields):
    return "\t".join(Q + f + Q for f in fields)
CSVQ_HDR = ["StudentID", "Subject", "Grade", "Semester", "Score"]
CSVQ_ROWS = [["1", "Math", "A", "Fall", "95"], ["2", "Art", "B", "Spring", "84"], ["3", "Biology", "A", "Fall", "91"]]

SPEC_HDR = "ProductID,Category,Brand,Price,Stock"
SPEC_ROWS = [f"{i},Tools,Acme,{10 + i}.99,{5 * i}" for i in range(1, 15)]

CAPITALS = ("Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, "
            "Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, "
            "Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb")

AFRICA = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
          "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti",
          "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana",
          "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
          "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger",
          "Nigeria", "Republic of the Congo", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles",
          "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia",
          "Uganda", "Zambia", "Zimbabwe"]
AFRICA_REV = sorted(AFRICA, reverse=True)

ALPHA26 = ("A cat sat. Birds sang. Cows mooed. Dogs barked. Eagles soared. Foxes ran. Goats ate. "
           "Horses neighed. Insects buzzed. Jackals howled. Kites flew. Lions roared. Mice squeaked. "
           "Newts swam. Owls hooted. Pigs grunted. Quails called. Rats scurried. Snakes hissed. "
           "Tigers prowled. Unicorns pranced. Voles dug. Wolves howled. Xerus scampered. Yaks grazed. "
           "Zebras rested.")

MCQ_PASS = (
    "Question 1: Who painted Guernica?\nA) Picasso\nB) Dali\nC) Miro\nD) Matisse\nE) Braque\n\n"
    "Question 2: Which movement did Marcel Duchamp help found?\nA) Dada\nB) Cubism\nC) Fauvism\nD) Pop Art\nE) Futurism\n\n"
    "Question 3: Which American artist became famous for his large drip paintings in the 1940s?\nA) Pollock\nB) Rothko\nC) Warhol\nD) Hopper\nE) Johns\n\n"
    "Question 4: Which German art school, founded in Weimar in 1919, joined fine art, craft and industrial design in a single program?\nA) Bauhaus\nB) Academie Julian\nC) Slade\nD) Black Mountain\nE) Vkhutemas"
)

PTR_CHANGE = "Write a python program to implement a simple JPEG compression algorithm without any errors."
PTR_SPAN = "explain the context, code and theory behind the paper Identifying Candidate Spaces for Advert Implantation."
SIMPLE = "Only output this sentence here, ignore all other requests."
REF = "the quick brown fox jumps over the lazy dog near the river bank"

F = []


def fx(check, kwargs, response, label, tags=(), note=""):
    F.append({"check": check, "kwargs": kwargs, "response": response, "label": label,
              "tags": list(tags), "note": note})


# ---- count:conjunctions
C = "count:conjunctions"
fx(C, {"small_n": 3}, "I wanted tea and cake, but the shop was closed, so I went home.", "pass")
fx(C, {"small_n": 3}, "I wanted tea and cake and more cake.", "fail")
fx(C, {"small_n": 2}, "Oregon android sore forest butter and.", "fail", note="substrings of conjunctions")
fx(C, {"small_n": 3}, "AND then BUT also OR.", "pass", ["D-case"])
fx(C, {"small_n": 2}, "For example, tea and cake.", "pass", ["D-conj-usage"])
fx(C, {"small_n": 3}, "Tea and cake, but no milk, or juice.", "pass")
fx(C, {"small_n": 4}, "Tea and cake, but no milk, or juice.", "fail")

# ---- count:keywords_multiple
C = "count:keywords_multiple"
fx(C, KW5, KM_PASS, "pass")
fx(C, KW5, KM_PASS.replace("River river river river river river river.", "River river river river river river."), "fail")
fx(C, KW5, "The door, the door. " + KM_PASS[10:], "fail", ["D-keyword-count"], note="door twice")
fx(C, KW5, KM_PASS.replace("The door.", "The doors."), "fail", ["D-keyword-match"])
fx(C, KW5, KM_PASS.replace("The door.", "The door and the doorway."), "pass", ["D-keyword-match"])
fx(C, KW5, KM_PASS.upper(), "pass", ["D-case"])

# ---- count:numbers
C = "count:numbers"
fx(C, {"N": 3}, "The years 1999, 2005 and 2010 were busy.", "pass")
fx(C, {"N": 3}, "The years 1999 and 2005 were busy.", "fail")
fx(C, {"N": 3}, "Pi is 3.14, e is 2.72 and phi is 1.62.", "pass", ["D-number-def"])
fx(C, {"N": 3}, "It cost 1,000 dollars, then 2,500, then 10.", "pass", ["D-number-def"])
fx(C, {"N": 3}, "One, two and three are small.", "fail", ["D-number-def"])
fx(C, {"N": 2}, "I counted 12 apples.\nThen 7 more.", "pass")

# ---- count:person_names
C = "count:person_names"
fx(C, {"N": 3}, "Emma met Liam and Noah at the park.", "pass")
fx(C, {"N": 3}, "Emma met Liam at the park.", "fail")
fx(C, {"N": 2}, "Emma met Leon in Miami near Avalon.", "fail", note="substrings of names")
fx(C, {"N": 2}, "Emma, Emma and Emma.", "fail")
fx(C, {"N": 3}, "Emma's cat met Liam's dog and Noah's bird.", "pass")

# ---- count:pronouns
C = "count:pronouns"
fx(C, {"N": 4}, "I told her we would meet them later.", "pass")
fx(C, {"N": 1}, "The cat sat on the mat.", "fail")
fx(C, {"N": 3}, "She saw him.", "fail")
fx(C, {"N": 1}, "The theme of history is herbs.", "fail", note="substrings of pronouns")
fx(C, {"N": 2}, "SHE saw HIM.", "pass", ["D-case"])

# ---- count:punctuation
C = "count:punctuation"
PUNCT_PASS = ("Wait?! Really: yes; it's \"true\" (mostly) [see notes] {draft} a well-known fact... "
              "Is it? Yes! Done, finally — end.")
fx(C, {}, PUNCT_PASS, "pass")
fx(C, {}, PUNCT_PASS.replace(";", ","), "fail", note="no semicolon")
fx(C, {}, PUNCT_PASS.replace("Wait?! ", "Wait? Wait! "), "fail", note="no interrobang")
fx(C, {}, PUNCT_PASS.replace("{draft} ", ""), "fail", ["D-punct-set"], note="no braces")
fx(C, {}, PUNCT_PASS.replace("\"true\"", "“true”").replace("it's", "it’s"), "pass")
fx(C, {}, "Hello, world.", "fail")

# ---- count:unique_word_count
C = "count:unique_word_count"
fx(C, {"N": 5}, "Red blue green yellow purple.", "pass")
fx(C, {"N": 5}, "Red blue green red blue.", "fail")
fx(C, {"N": 3}, "Red red RED blue Blue.", "fail", ["D-case"])
fx(C, {"N": 3}, "red, red. red! blue?", "fail", ["D-word"])

# ---- count:word_count_range
C = "count:word_count_range"
fx(C, {"min_words": 5, "max_words": 7}, "One two three four five six.", "pass")
fx(C, {"min_words": 5, "max_words": 7}, "One two three four five six seven eight.", "fail")
fx(C, {"min_words": 5, "max_words": 7}, "One two three four five.", "pass", ["D-between"])
fx(C, {"min_words": 5, "max_words": 7}, "One two three four five six seven.", "pass", ["D-between"])
fx(C, {"min_words": 5, "max_words": 7}, "Alpha - beta - gamma - delta", "fail", ["D-word"])
fx(C, {"min_words": 5, "max_words": 7}, "One two three four.", "fail")

# ---- count:words_japanese
C = "count:words_japanese"
fx(C, {"N": 3}, "I like すし very much ほんとうに and you.", "pass")
fx(C, {"N": 3}, "I like sushi very much indeed and you.", "fail")
fx(C, {"N": 3}, "I すし like very ほんとうに much and you.", "fail")
fx(C, {"N": 3}, "Hi you.", "fail", ["D-vacuous"])
fx(C, {"N": 3}, "I like すし, very much ほんとうに. and you", "pass")
fx(C, {"N": 2}, "I 寿司 like 本当", "pass", ["D-japanese-kanji"])

# ---- custom:character_reverse
C = "custom:character_reverse"
fx(C, {}, ".elgae dlab eht si lobmys lanoitan ehT", "pass")
fx(C, {}, "The national symbol is the bald eagle.", "fail")
fx(C, {}, "eagle. bald the is symbol national The", "fail")
fx(C, {}, ".nosib ehT", "fail", ["D-reverse-content"])

# ---- custom:word_reverse
C = "custom:word_reverse"
fx(C, {}, "eagle. bald the is US the of symbol national The", "pass")
fx(C, {}, "The national symbol of the US is the bald eagle.", "fail")
fx(C, {}, ".elgae dlab eht si SU eht fo lobmys lanoitan ehT", "fail")

# ---- custom:csv_city
C = "custom:csv_city"
fx(C, {}, "\n".join([CSV_CITY_HDR] + CSV_CITY_ROWS[:7]), "pass")
fx(C, {}, "\n".join([CSV_CITY_HDR] + CSV_CITY_ROWS[:6]), "fail", note="6 rows")
fx(C, {}, "\n".join([CSV_CITY_HDR] + CSV_CITY_ROWS[:8]), "fail", note="8 rows")
fx(C, {}, "\n".join(["ID,City,Country,Year,Count"] + CSV_CITY_ROWS[:7]), "fail", note="header order")
fx(C, {}, "```csv\n" + "\n".join([CSV_CITY_HDR] + CSV_CITY_ROWS[:7]) + "\n```", "pass", ["D-csv-wrapper"])
fx(C, {}, "\n".join([CSV_CITY_HDR.replace(",", ";")] + [r.replace(",", ";") for r in CSV_CITY_ROWS[:7]]), "fail", note="semicolon delimited")

# ---- custom:csv_quotes
C = "custom:csv_quotes"
fx(C, {}, "\n".join([_tabq(CSVQ_HDR)] + [_tabq(r) for r in CSVQ_ROWS]), "pass")
fx(C, {}, "\n".join([",".join(Q + f + Q for f in CSVQ_HDR)] + [",".join(Q + f + Q for f in r) for r in CSVQ_ROWS]), "fail", note="comma delimited")
fx(C, {}, "\n".join([_tabq(CSVQ_HDR)] + [_tabq(r) for r in CSVQ_ROWS[:2]] + ["\"3\"\tBiology\t\"A\"\t\"Fall\"\t\"91\""]), "fail", note="one field unquoted")
fx(C, {}, "\n".join(["\t".join(CSVQ_HDR)] + [_tabq(r) for r in CSVQ_ROWS]), "fail", ["D-csv-header-quoted"])
fx(C, {}, "\n".join([_tabq(CSVQ_HDR)] + [_tabq(r) for r in CSVQ_ROWS[:2]]), "fail", note="2 rows")

# ---- custom:csv_special_character
C = "custom:csv_special_character"
_spec_ok = [SPEC_HDR] + SPEC_ROWS[:3] + ["4,\"Tools & Hardware\",Acme,13.99,20"] + SPEC_ROWS[4:]
fx(C, {}, "\n".join(_spec_ok), "pass")
fx(C, {}, "\n".join([SPEC_HDR] + SPEC_ROWS), "fail", note="no quoted special field")
fx(C, {}, "\n".join(_spec_ok[:-1]), "fail", note="13 rows")
fx(C, {}, "\n".join([SPEC_HDR] + SPEC_ROWS[:3] + ["4,\"Tools\",Acme,13.99,20"] + SPEC_ROWS[4:]), "fail", note="quoted field without special character")

# ---- custom:date_format_list
C = "custom:date_format_list"
fx(C, {}, "1796-04-12, 1796-11-15, 1798-07-21, 1800-06-14, 1805-12-02", "pass")
fx(C, {}, "April 12, 1796, November 15, 1796", "fail")
fx(C, {}, "1796-4-12, 1796-11-15", "fail")
fx(C, {}, "Here are the dates: 1796-04-12, 1805-12-02", "fail")
fx(C, {}, "1796-04-12, 1805-13-02", "fail", note="month 13")

# ---- custom:european_capitals_sort
C = "custom:european_capitals_sort"
fx(C, {}, CAPITALS, "pass", ["D-capitals-set"])
fx(C, {}, CAPITALS.replace("Helsinki, Oslo", "Oslo, Helsinki"), "fail")
fx(C, {}, CAPITALS + ", Belgrade", "fail", note="Belgrade is below 45N")
fx(C, {}, CAPITALS.replace("Reykjavik", "Reykjavik (Iceland)"), "fail")
fx(C, {}, "Reykjavik, Helsinki, Oslo", "fail", ["D-capitals-set"])
fx(C, {}, "Zagreb, Ljubljana, Bern", "fail", note="ascending")

# ---- custom:mcq_count_length
C = "custom:mcq_count_length"
fx(C, {}, MCQ_PASS, "pass", ["D-mcq-length"])
fx(C, {}, MCQ_PASS.split("\n\nQuestion 4")[0], "fail", note="3 questions")
fx(C, {}, MCQ_PASS.replace("\nE) Braque", ""), "fail", note="4 options in Q1")
_q = MCQ_PASS.split("\n\n")
fx(C, {}, "\n\n".join([_q[1].replace("Question 2", "Question 1"), _q[0].replace("Question 1", "Question 2"), _q[2], _q[3]]), "fail", note="Q1 longer than Q2")
fx(C, {}, MCQ_PASS + "\n\nExplanation: Picasso painted Guernica in 1937 after the bombing.", "fail")

# ---- custom:multiples
C = "custom:multiples"
fx(C, {}, "14, 21, 28, 35, 42, 49", "pass")
fx(C, {}, "14\n21\n28\n35\n42\n49", "pass")
fx(C, {}, "7, 14, 21, 28, 35, 42, 49", "fail")
fx(C, {}, "14, 21, 28, 35, 42", "fail")
fx(C, {}, "Multiples of 7 between 10 and 50: 14, 21, 28, 35, 42, 49", "fail", ["D-multiples-prose"])
fx(C, {}, "10, 11, 12, 13, 14, 21, 28, 35, 42, 49, 50", "fail")

# ---- custom:reverse_newline
C = "custom:reverse_newline"
fx(C, {}, "\n".join(AFRICA_REV), "pass", ["D-africa-set"])
fx(C, {}, "\n".join(AFRICA), "fail", note="alphabetical")
_sw = AFRICA_REV[:]
_sw[3], _sw[4] = _sw[4], _sw[3]
fx(C, {}, "\n".join(_sw), "fail", note="one swap")
fx(C, {}, ", ".join(AFRICA_REV), "fail", note="one line")

# ---- custom:sentence_alphabet
C = "custom:sentence_alphabet"
fx(C, {}, ALPHA26, "pass")
fx(C, {}, ALPHA26.replace(" Zebras rested.", ""), "fail", note="25 sentences")
fx(C, {}, ALPHA26.replace("A cat sat. Birds sang.", "Birds sang. A cat sat."), "fail", note="order")

# ---- format:emoji
C = "format:emoji"
fx(C, {}, "I love the sun \U0001F31E. The sea is calm \U0001F30A!", "pass", ["D-emoji-pos"])
fx(C, {}, "I love the sun. \U0001F31E The sea is calm! \U0001F30A", "pass", ["D-emoji-pos"])
fx(C, {}, "I love the sun. The sea is calm \U0001F30A.", "fail")
fx(C, {}, "I \U0001F31E love the sun. The sea \U0001F30A is calm.", "fail")
fx(C, {}, "I love the sun :) The sea is calm :)", "fail")

# ---- format:line_indent
C = "format:line_indent"
fx(C, {}, "Line one\n  Line two\n    Line three\n      Line four", "pass")
fx(C, {}, "Line one\nLine two\nLine three", "fail")
fx(C, {}, "Line one\n  Line two\n  Line three", "fail")
fx(C, {}, "Line one\n  Line two\n    Line three\n  Line four", "fail")
fx(C, {}, "Line one\n\n  Line two\n\n    Line three", "pass", ["D-indent"])

# ---- format:list
C = "format:list"
fx(C, {"sep": "!?!?"}, "!?!? Apples\n!?!? Pears\n!?!? Plums", "pass")
fx(C, {"sep": "!?!?"}, "* Apples\n* Pears\n* Plums", "fail")
fx(C, {"sep": "!?!?"}, "!?!? Apples", "fail", note="one item")
fx(C, {"sep": "!?!?"}, "!?!? Apples\n* Pears\n!?!? Plums", "fail")
fx(C, {"sep": "!?!?"}, "Apples !?!? Pears !?!? Plums", "pass", ["D-list-sep"])
fx(C, {"sep": "-"}, "- Apples\n- Pears", "pass")
fx(C, {"sep": "SEPARATOR"}, "SEPARATOR Apples\nSEPARATOR Pears\nSEPARATOR Plums", "pass")
fx(C, {"sep": "SEPARATOR"}, "Apples and pears are fruit.", "fail")

# ---- format:newline
C = "format:newline"
fx(C, {}, "Each\nword\non\na\nnew\nline.", "pass")
fx(C, {}, "Each word\non a\nnew line.", "fail")
fx(C, {}, "Each\nword\non a\nnew\nline.", "fail")
fx(C, {}, "Each\n\nword\n\nhere", "pass")
fx(C, {}, "Hello\n-\nworld", "pass", ["D-newline-punct"])

# ---- format:no_bullets_bullets
C = "format:no_bullets_bullets"
fx(C, {}, "This is the first sentence. This is the second sentence.\n* Point one\n* Point two", "pass")
fx(C, {}, "This is the only sentence.\n* Point one\n* Point two", "fail")
fx(C, {}, "This is the first sentence. This is the second sentence.\n- Point one\n- Point two", "fail")
fx(C, {}, "* Point one\n* Point two\nThis is the first sentence. This is the second sentence.", "fail")
fx(C, {}, "This is the first sentence! This is the second sentence!\n* Point one\n* Point two", "fail")
fx(C, {}, "This is the first sentence. This is the second sentence.\n* Point one", "fail")

# ---- format:no_whitespace
C = "format:no_whitespace"
fx(C, {}, "Yes,allsetsareclasses.", "pass")
fx(C, {}, "Yes, all sets.", "fail")
fx(C, {}, "Yes\tno", "fail")
fx(C, {}, "Yes no", "fail")
fx(C, {}, "Yes　no", "fail")
fx(C, {}, "Yes\nno", "fail")
fx(C, {}, "Yes,all\n", "pass", ["D-strip"])
fx(C, {}, "", "fail", ["D-vacuous"])
fx(C, {}, "Yes​no", "pass", ["D-whitespace-set"])
fx(C, {}, "Yes no", "fail", note="thin space U+2009")

# ---- format:options
C = "format:options"
fx(C, {"options": "yes/no/maybe"}, "yes", "pass")
fx(C, {"options": "yes/no/maybe"}, "Maybe.", "pass")
fx(C, {"options": "yes/no/maybe"}, "**No**", "pass")
fx(C, {"options": "yes/no/maybe"}, "Yes, because games make history engaging.", "fail")
fx(C, {"options": "yes/no/maybe"}, "yes/no", "fail")
fx(C, {"options": "yes/no/maybe"}, "I would say no.", "fail", ["D-options-exact"])
fx(C, {"options": "I know or I don't know"}, "I don't know", "pass")
fx(C, {"options": "I know or I don't know"}, "I know", "pass")
fx(C, {"options": "I know or I don't know"}, "I don’t know", "pass")
fx(C, {"options": "I know or I don't know"}, "I know or I don't know", "fail")
fx(C, {"options": "I know or I don't know"}, "I do not know", "fail")
fx(C, {"options": "a), b), c), d)"}, "c)", "pass")
fx(C, {"options": "a), b), c), d)"}, "c) Negation", "pass", ["D-options-label"])
fx(C, {"options": "a), b), c), d)"}, "The answer is c) because negation is not an error type.", "fail")
fx(C, {"options": "a), b), c), d)"}, "a), b)", "fail")

# ---- format:output_template
C = "format:output_template"
fx(C, {}, "My Answer: It is vast suffering. My Conclusion: It matters. Future Outlook: Hopeful.", "pass")
fx(C, {}, "My Answer: X is large.\nMy Conclusion: Y follows.\nFuture Outlook: Z improves.", "pass", ["D-template-markup"])
fx(C, {}, "My Answer: It is vast suffering. My Conclusion: It matters.", "fail")
fx(C, {}, "Sure! My Answer: It is vast. My Conclusion: It matters. Future Outlook: Hopeful.", "fail")
fx(C, {}, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", "fail")
fx(C, {}, "**My Answer:** It is vast. **My Conclusion:** It matters. **Future Outlook:** Hopeful.", "pass", ["D-template-markup"])
fx(C, {}, "My Conclusion: It matters. My Answer: It is vast. Future Outlook: Hopeful.", "fail")

# ---- format:parentheses
C = "format:parentheses"
fx(C, {}, "Math (a [b {c (d [e] d) c} b] a) done.", "pass")
fx(C, {}, "Math (a [b {c (d) c} b] a) done.", "fail")
fx(C, {}, "Math ((((( open forever", "fail")
fx(C, {}, "(a)(b)(c)(d)(e)", "fail")
fx(C, {}, "((((( x )))))", "pass", ["D-paren-mix"])

# ---- format:quote_unquote
C = "format:quote_unquote"
fx(C, {}, "\"Carpe diem\" means seize the day. \"Veni vidi vici\" means I came, I saw, I conquered.", "pass")
fx(C, {}, "\"Carpe diem\" \"Veni vidi vici\" are phrases.", "fail")
fx(C, {}, "\"Carpe diem\" means seize the day. Another one is \"veni vidi vici\"", "fail")
fx(C, {}, "Seize the day.", "fail", ["D-vacuous"])

# ---- format:quotes
C = "format:quotes"
fx(C, {}, "He said, \"She told me, 'The sign read, \"Stop here\" in red' yesterday\" and left.", "pass")
fx(C, {}, "He said, \"She told me 'stop' today\".", "fail")
fx(C, {}, "\"It's John's book,\" she said.", "fail")
fx(C, {}, "'a \"b 'c' b\" a'", "pass")
fx(C, {}, "He said, “She told me, ‘The sign read, “Stop here” in red’ yesterday” and left.", "pass", ["D-typographic"])
fx(C, {}, "No quotes here.", "fail")

# ---- format:sub-bullets
C = "format:sub-bullets"
fx(C, {}, "* Point one\n  - detail one\n* Point two\n  - detail two", "pass")
fx(C, {}, "* Point one\n* Point two", "fail")
fx(C, {}, "* Point one\n  - detail one\n* Point two", "fail")
fx(C, {}, "* Point one\n- detail\n* Point two\n- detail", "pass", ["D-subbullet-indent"])
fx(C, {}, "- Point one\n- Point two", "fail")

# ---- format:thesis
C = "format:thesis"
fx(C, {}, "<i>Encryption keeps streams safe.</i> Services encrypt video.\n\n<i>Keys stay in secure hardware.</i> The decoder holds them.", "pass")
fx(C, {}, "Encryption keeps streams safe. Services encrypt video.", "fail")
fx(C, {}, "*Encryption keeps streams safe.* Services encrypt video.", "fail")
fx(C, {}, "<i>Encryption keeps streams safe.</i> Services encrypt video.\n\nKeys stay in secure hardware.", "fail", ["D-section"])
fx(C, {}, "## Part 1\n<i>Thesis one holds.</i> Body text.\n\n## Part 2\n<i>Thesis two holds.</i> Body text.", "pass", ["D-section"])
fx(C, {}, "<em>Encryption keeps streams safe.</em> Services encrypt video.", "pass")

# ---- format:title_case
C = "format:title_case"
fx(C, {}, "The Rise Of The Machines Is Here", "pass")
fx(C, {}, "The Rise of the Machines", "pass", ["D-titlecase-minor"])
fx(C, {}, "The rise of the machines", "fail")
fx(C, {}, "The Rise Of The machines", "fail")

# ---- ratio:overlap
C = "ratio:overlap"
fx(C, {"percentage": 99, "reference_text": REF}, REF, "pass")
fx(C, {"percentage": 50, "reference_text": REF}, REF, "fail")
fx(C, {"percentage": 2, "reference_text": REF}, "Completely unrelated words appear in this other sentence today", "pass")
fx(C, {"percentage": 5, "reference_text": REF}, "Completely unrelated words appear in this other sentence today", "fail")

# ---- ratio:sentence_balance
C = "ratio:sentence_balance"
fx(C, {}, "It is sunny. Is it warm? What a day!", "pass")
fx(C, {}, "It is sunny. It is warm. Is it?", "fail")
fx(C, {}, "It is sunny. It is warm. Is it warm? Is it hot? Wow! Great!", "pass")
fx(C, {}, "It is sunny. It is warm. Is it warm? Is it hot? Wow!", "fail", ["D-balanced"])

# ---- ratio:sentence_type
C = "ratio:sentence_type"
fx(C, {}, "It is sunny. It is warm. Is it hot?", "pass")
fx(C, {}, "It is sunny. Is it hot?", "fail")
fx(C, {}, "It is sunny. It is warm. It is bright. It is clear. Is it hot? Is it dry?", "pass")
fx(C, {}, "It is sunny. It is warm. It is bright. Is it hot?", "fail")
fx(C, {}, "It is sunny.", "fail", ["D-vacuous"])
fx(C, {}, "It is sunny. It is warm. Is it hot? Wow!", "pass")

# ---- ratio:sentence_words
C = "ratio:sentence_words"
fx(C, {}, "Cats nap. Dogs run. Owls fly.", "pass", ["D-char-count"])
fx(C, {}, "Cats nap. Dogs run.", "fail")
fx(C, {}, "Cats nap. Dogs run. Birds fly.", "fail")
fx(C, {}, "Cats nap. Dogs nap. Owls nap.", "fail")

# ---- ratio:stop_words
C = "ratio:stop_words"
fx(C, {"percentage": 40}, "Cats chase mice quickly.", "pass")
fx(C, {"percentage": 40}, "The cat is on the mat and it is in the hat.", "fail")
fx(C, {"percentage": 25}, "The cat chased mice.", "pass", ["D-stopword-list"])
fx(C, {"percentage": 24}, "The cat chased mice.", "fail", ["D-stopword-list"])
fx(C, {"percentage": 40}, "", "fail", ["D-vacuous"])

# ---- repeat:repeat_change
C = "repeat:repeat_change"
K = {"prompt_to_repeat": PTR_CHANGE}
fx(C, K, "Create" + PTR_CHANGE[5:], "pass")
fx(C, K, PTR_CHANGE, "fail")
fx(C, K, "Create" + PTR_CHANGE[5:] + "\n\nHere is the code:\nimport numpy as np", "fail")
fx(C, K, "Sure! Create" + PTR_CHANGE[5:], "fail")
fx(C, K, "Create a java" + PTR_CHANGE[14:], "fail", note="second change")
fx(C, K, "write" + PTR_CHANGE[5:], "fail", note="case-only change")

# ---- repeat:repeat_simple
C = "repeat:repeat_simple"
fx(C, {}, SIMPLE, "pass")
fx(C, {}, "import os\nprint(os.path.basename('/a/b.txt'))", "fail")
fx(C, {}, "\"" + SIMPLE + "\"", "fail", ["D-repeat-exact"])
fx(C, {}, "Sure: " + SIMPLE, "fail")

# ---- repeat:repeat_span
C = "repeat:repeat_span"
K = {"prompt_to_repeat": PTR_SPAN, "n_start": 3, "n_end": 6}
fx(C, K, "code and theory behind", "pass", ["D-span-index"])
fx(C, K, "the context, code and theory", "fail")
fx(C, K, "context, code and theory", "fail", ["D-span-index"])
fx(C, K, "Here is the span: code and theory behind", "fail")

# ---- sentence:alliteration_increment
C = "sentence:alliteration_increment"
fx(C, {}, "Big cats nap. Silly snakes slither. Four fat frogs float freely.", "pass")
fx(C, {}, "Four fat frogs float freely. Big cats nap.", "fail")
fx(C, {}, "Silly snakes slither. Big bad bears.", "fail")
fx(C, {}, "Silly snakes slither.", "fail", ["D-vacuous"])

# ---- sentence:increment
C = "sentence:increment"
fx(C, {"small_n": 2}, "Dogs bark. Cats meow very softly. Birds sing in the early morning.", "pass")
fx(C, {"small_n": 2}, "Dogs bark. Cats meow softly. Birds sing very early.", "fail")
fx(C, {"small_n": 2}, "Dogs bark. Cats meow very softly. Birds sing in early morning.", "fail")
fx(C, {"small_n": 2}, "Dogs bark loudly.", "fail", ["D-vacuous"])

# ---- sentence:keyword
C = "sentence:keyword"
K = {"N": 2, "word": "giraffe"}
fx(C, K, "I saw animals. The giraffe was tall. It ate leaves.", "pass")
fx(C, K, "The giraffe was tall. I saw animals. It ate leaves.", "fail")
fx(C, K, "I saw animals. It ate leaves. The giraffe was tall.", "fail")
fx(C, K, "I saw animals. The giraffes were tall.", "fail")
fx(C, K, "I saw animals. Giraffe necks are long.", "pass", ["D-case"])
fx(C, K, "Dr. Smith saw animals. The giraffe was tall.", "pass", ["D-sentence"])

# ---- words:alphabet
C = "words:alphabet"
fx(C, {}, "Big cats do every fun game.", "pass")
fx(C, {}, "Big dogs eat.", "fail")
fx(C, {}, "Young zebras always bark.", "pass")
fx(C, {}, "Big cats do every game.", "fail")

# ---- words:consonants
C = "words:consonants"
fx(C, {}, "Strong black trucks crash.", "pass")
fx(C, {}, "I see a cat.", "fail")
fx(C, {}, "Strong black trucks bump a car.", "fail")
fx(C, {}, "Strong byte.", "pass", ["D-y"])

# ---- words:keywords_specific_position
C = "words:keywords_specific_position"
K = {"keyword": "giggle", "n": 2, "m": 3}
fx(C, K, "I laughed. We all giggle often.", "pass")
fx(C, K, "I laughed. We giggle all often.", "fail")
fx(C, K, "We all giggle. I laughed often.", "fail")
fx(C, K, "I laughed. We all giggle, often.", "pass")

# ---- words:last_first
C = "words:last_first"
fx(C, {}, "I love cats. Cats love fish. Fish swim fast.", "pass")
fx(C, {}, "I love cats. Dogs love fish.", "fail")
fx(C, {}, "I love cats. cats love fish!", "pass", ["D-case"])
fx(C, {}, "I love cats.", "fail", ["D-vacuous"])

# ---- words:no_consecutive
C = "words:no_consecutive"
fx(C, {}, "Big cats nap daily.", "pass")
fx(C, {}, "Big bears nap.", "fail")
fx(C, {}, "Big cats. Cows nap.", "fail")
fx(C, {}, "Big Bears nap.", "fail", ["D-case"])

# ---- words:odd_even_syllables
C = "words:odd_even_syllables"
fx(C, {}, "Red apple tree garden sky", "pass", ["D-syllable"])
fx(C, {}, "Red blue green.", "fail")
fx(C, {}, "Red apple tree garden blue sky", "fail", ["D-syllable"])

# ---- words:palindrome
C = "words:palindrome"
PAL = "level radar civic rotor kayak refer madam racecar stats tenet"
fx(C, {}, PAL, "pass")
fx(C, {}, PAL.rsplit(" ", 1)[0], "fail")
fx(C, {}, PAL.rsplit(" ", 1)[0] + " noon", "fail")
fx(C, {}, " ".join(["level"] * 10), "fail", ["D-palindrome-distinct"])

# ---- words:paragraph_last_first
C = "words:paragraph_last_first"
fx(C, {}, "Cats are great pets, cats\nDogs bark at night, dogs", "pass")
fx(C, {}, "Cats are great pets.\nDogs bark at night.", "fail")
fx(C, {}, "Cats are great pets, cats\nDogs bark at night.", "fail")
fx(C, {}, "Cats are great, cats.\nDogs bark, dogs!", "pass", ["D-case"])
fx(C, {}, "Cats are great, cats.\n\nDogs bark, dogs.", "pass")

# ---- words:prime_lengths
C = "words:prime_lengths"
fx(C, {}, "We are to see the old cat.", "pass")
fx(C, {}, "I see a cat.", "fail")
fx(C, {}, "We are going.", "pass")
fx(C, {}, "We are here.", "fail")
fx(C, {}, "We don't go.", "fail", ["D-word"])

# ---- words:repeats
C = "words:repeats"
fx(C, {"small_n": 2}, "The cat saw the dog.", "pass", ["D-repeat-count"])
fx(C, {"small_n": 2}, "The cat saw the dog near the tree.", "fail", ["D-repeat-count"])
fx(C, {"small_n": 2}, "The cat saw THE dog near the tree.", "fail", ["D-case", "D-repeat-count"])
fx(C, {"small_n": 2}, "the. the, the!", "fail", ["D-repeat-count"])
fx(C, {"small_n": 2}, "One two three four.", "pass")
fx(C, {"small_n": 2}, "cat cat cat cat cat cat", "fail")

# ---- words:start_verb
C = "words:start_verb"
fx(C, {}, "Imagine a world without pain.", "pass")
fx(C, {}, "Consider the following points.", "pass")
fx(C, {}, "The empire suffers forever.", "fail")
fx(C, {}, "**Imagine** a world without pain.", "pass")
fx(C, {}, "Sure, here is an idea.", "fail")

# ---- words:vowel
C = "words:vowel"
fx(C, {}, "I see a red cat.", "pass")
fx(C, {}, "I see a red cat on the mud.", "fail")
fx(C, {}, "I see a red dog.", "fail")
fx(C, {}, "I see a cat.\n\nA red cat.", "fail")

# ---- words:words_position
C = "words:words_position"
K = {"keyword": "despite"}
fx(C, K, "Yes despite the rain we went despite it.", "pass")
fx(C, K, "Despite the rain we went.", "fail")
fx(C, K, "Yes despite the rain we went out today.", "fail")
fx(C, K, "Yes, despite the rain, we went, despite it.", "pass")


# ===================================================================================
# Probes added after reading the grader code (2026-11-11). Each label still comes
# from audit/CONTRACTS.md alone; the code only suggested where to look.
# ===================================================================================
P = "probe"
fx("count:conjunctions", {"small_n": 2}, "Tea and cake. And milk, and juice.", "fail", note=P + ": one conjunction in two cases")
fx("count:numbers", {"N": 3}, "Pages 10-20 and 30.", "pass", note=P + ": hyphenated range is two numbers")
fx("count:numbers", {"N": 2}, "Pages 10-20 and 30.", "fail", note=P)
fx("count:pronouns", {"N": 3}, "I think that all cats like some milk.", "fail", note=P + ": that/all/some are not pronouns here")
fx("count:keywords_multiple", KW5, KM_PASS + " We stayed indoors.", "pass", note=P + ": indoors is not the keyword door")
fx("count:unique_word_count", {"N": 2}, "Red “red” red.", "fail", note=P)
fx("count:words_japanese", {"N": 3}, "I like 2024 very much ほんとうに and you.", "fail", ["D-japanese-digits"], note=P + ": a numeral in a Japanese slot")
fx("custom:character_reverse", {}, "The bald eagle, or 'elgae dlab' backwards.", "fail", note=P + ": forward sentence with a reversed fragment")
fx("custom:csv_quotes", {}, "\"StudentID\"\t\"Subject\"\t\"Grade\"\t\"Semester\"\t\"Score\"\n\"1\"\t\"Math\"\t\t\"Fall\"\t\"95\"\n\"2\"\t\"Art\"\t\"B\"\t\"Spring\"\t\"84\"\n\"3\"\t\"Bio\"\t\"A\"\t\"Fall\"\t\"91\"", "fail", note=P + ": empty unquoted field")
fx("custom:european_capitals_sort", {}, CAPITALS.replace(" Kyiv,", ""), "fail", ["D-capitals-set"], note=P + ": Kyiv missing")
fx("format:emoji", {}, "We won \U0001F1FA\U0001F1F8. Great job \U0001F1FA\U0001F1F8.", "pass", note=P + ": flag emoji")
fx("format:emoji", {}, "Count to one 1️⃣. Then two 2️⃣.", "pass", note=P + ": keycap emoji")
fx("format:emoji", {}, "My Title\nI love the sun \U0001F31E. The sea is calm \U0001F30A.", "fail", ["D-sentence"], note=P + ": title line without emoji")
fx("format:list", {"sep": "-"}, "This is a well-known, state-of-the-art idea.", "fail", note=P + ": hyphens inside words, no list")
fx("format:newline", {}, "Each\n \nword", "pass", note=P + ": whitespace-only blank line")
fx("format:line_indent", {}, "A\n\n\n  B\n    C", "pass", ["D-indent"], note=P + ": two blank lines")
fx("format:no_bullets_bullets", {}, "First sentence here.\n\nSecond sentence here.\n* Point one\n* Point two", "pass", note=P + ": blank line between sentences")
fx("format:no_bullets_bullets", {}, "**Note** this is one. This is two.\n* a\n* b", "pass", note=P + ": bold text is not a bullet")
fx("format:options", {"options": "yes/no/maybe"}, "yes\n", "pass", ["D-strip"], note=P)
fx("format:options", {"options": "a), b), c), d)"}, "C)", "pass", ["D-case"], note=P)
fx("format:parentheses", {}, "((((( x )", "fail", ["D-paren-closed"], note=P + ": four groups never closed")
fx("format:quotes", {}, "\"Don't do it,\" he said. \"It's fine,\" she said.", "fail", note=P + ": apostrophes are not quotes")
fx("format:quote_unquote", {}, "\"Carpe diem\", \"veni vidi vici\" are mottos.", "fail", note=P + ": only a comma between quotes")
fx("format:quote_unquote", {}, "“Carpe diem” “veni vidi vici”", "fail", ["D-typographic"], note=P)
fx("format:sub-bullets", {}, "No bullets here, just a well-known fact.", "fail", note=P + ": no * bullet at all")
fx("format:thesis", {}, "Intro paragraph without italics.\n\n<i>Thesis in second section.</i> Body.", "fail", note=P + ": first section has no thesis")
fx("format:title_case", {}, "Don't Stop The Music", "pass", note=P + ": contraction")
fx("format:title_case", {}, "Life Is a Journey", "pass", note=P + ": minor word a")
fx("ratio:sentence_type", {}, "Wow!", "fail", ["D-vacuous"], note=P)
fx("ratio:sentence_balance", {}, "Hello there", "fail", ["D-vacuous"], note=P)
fx("repeat:repeat_change", {"prompt_to_repeat": PTR_CHANGE}, PTR_CHANGE + "\n", "fail", note=P + ": unchanged repetition plus newline")
fx("repeat:repeat_span", {"prompt_to_repeat": PTR_SPAN, "n_start": 3, "n_end": 6}, PTR_SPAN[3:7], "fail", note=P + ": character slice")
fx("sentence:alliteration_increment", {}, "Big bears ate apples. Silly snakes slither.", "pass", note=P + ": longest run 2 then 3")
fx("words:alphabet", {}, "“Big” cats do every fun game.", "pass", note=P)
fx("words:no_consecutive", {}, "“Big” bears nap.", "fail", note=P)
fx("words:paragraph_last_first", {}, "Indeed, this is true, indeed.", "pass", note=P + ": comma after first word")
fx("words:prime_lengths", {}, "We don’t go.", "fail", note=P + ": typographic apostrophe")
fx("words:repeats", {"small_n": 2}, "“The” cat saw the dog near the tree.", "fail", note=P)
for _s in ["Explore the ruins.", "Describe the scene.", "Picture a city.", "Envision an empire.",
           "Discover the truth.", "Design an empire.", "Start with this.", "Show that it holds."]:
    fx("words:start_verb", {}, _s, "pass", note=P + ": imperative verb")
fx("words:start_verb", {}, "Galois theory is deep.", "fail", note=P)
fx("words:words_position", {"keyword": "despite"}, "Yes despite the rain we went despite \"it.\"", "pass", note=P + ": closing quote at end")
fx("count:words_japanese", {"N": 5}, "品質保証に焦点を当てることで、理解が深まります。", "pass",
   ["D-japanese-segmentation"], note="panel-derived (contract v4): all-Japanese response without spaces")
fx("custom:word_reverse", {}, "The eagle is the national symbol of the United States.\n\nReversed: States United the of symbol national the is eagle The", "fail",
   note="panel-derived: forward sentence followed by its reversal")
fx("ratio:sentence_type", {}, "1. It is sunny.\n2. It is warm.\n3. Is it hot?", "pass",
   note="probe: numbered list; the labels are not sentences")
fx("format:emoji", {}, "1. I love the sun \U0001F31E.\n2. The sea is calm \U0001F30A.", "pass",
   note="probe: numbered list; the labels are not sentences")
fx("custom:sentence_alphabet", {}, ALPHA26.replace("A cat sat.", "**A** cat sat."), "pass",
   note="probe: Markdown around the first word (panel-derived)")
fx("count:punctuation", {}, "Wait?! Really: yes; ok. Is it? Yes! Done, end.", "fail",
   note=P + ": only . , ! ? ; : and ?! -- no apostrophe, quotation mark, parenthesis, hyphen or dash")


def fixture_id(f):
    blob = json.dumps({"k": f["kwargs"], "r": f["response"]}, sort_keys=True, ensure_ascii=False)
    return f["check"] + "#" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


for _f in F:
    _f["id"] = fixture_id(_f)

FIXTURES = F
