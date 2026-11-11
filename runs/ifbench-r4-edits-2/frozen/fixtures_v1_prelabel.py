"""Labeled fixtures for the 58 IFBench checks (step 3).

Every label comes from audit/CONTRACTS.md alone (written and labeled before the
grader code was read). `decisions` names the decision entries a label depends
on; an empty tuple means the label holds under every reading the text allows.
`kind` is pass, fail or near (near-miss).
"""
import hashlib
import json

F = []


def fx(check, kwargs, response, label, kind, decisions=(), note=""):
    F.append(dict(check=check, kwargs=kwargs, response=response, label=label,
                  kind=kind, decisions=tuple(decisions), note=note))


# ---------------------------------------------------------------- count
c = "count:conjunctions"
fx(c, {"small_n": 3}, "I like tea and coffee, but not juice, or soda.", "pass", "pass")
fx(c, {"small_n": 3}, "I like tea and coffee and juice.", "fail", "fail")
fx(c, {"small_n": 3}, "I like tea and coffee, but not juice.", "fail", "near")
fx(c, {"small_n": 3}, "Tea and milk and sugar, but never salt, but never pepper.", "fail", "near", note="2 distinct")
fx(c, {"small_n": 3}, "And then it rained. But we stayed. Or did we?", "pass", "pass", ["D-case"])
fx(c, {"small_n": 4}, "I went for a walk, and so did she, but nobody came.", "pass", "pass", ["D-conj-usage"])

c = "count:keywords_multiple"
KW = {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
base = ("The door was open. Fresh bread, warm bread. Blue sky, blue sea, blue eyes. "
        "A lamp, a lamp, a lamp, a lamp, a lamp. "
        "River, river, river, river, river, river, river.")
fx(c, KW, base, "pass", "pass", ["D-case"])
fx(c, KW, base.replace(" river.", "."), "fail", "near", note="river six times")
fx(c, KW, base.replace("The door was open.", "The door was open. Another door."), "fail", "near", ["D-count-exact"], note="door twice")
fx(c, KW, base + " The doors creaked.", "pass", "pass", ["D-keyword-form"], note="doors is not door")
fx(c, KW, "Nothing relevant here.", "fail", "fail")

c = "count:numbers"
fx(c, {"N": 3}, "I have 2 cats, 3 dogs and 10 fish.", "pass", "pass")
fx(c, {"N": 3}, "I have 2 cats and 3 dogs.", "fail", "fail")
fx(c, {"N": 3}, "It cost 1,000 dollars in 2024 at 3.5 percent.", "pass", "near", note="1,000 and 3.5 are one number each")
fx(c, {"N": 3}, "I have five cats, 2 dogs, 3 birds and 4 fish.", "pass", "pass", ["D-number-words"])
fx(c, {"N": 3}, "I have 2 cats, 3 dogs, 10 fish and 1 bird.", "fail", "near")

c = "count:person_names"
fx(c, {"N": 3}, "Emma met Liam and Sophia at the park.", "pass", "pass")
fx(c, {"N": 3}, "Emma met Liam at the park.", "fail", "fail")
fx(c, {"N": 3}, "Emma met Liam and Bob at the park.", "fail", "near", note="Bob not in list")
fx(c, {"N": 3}, "Emma, Emma and Emma went home.", "fail", "near")
fx(c, {"N": 3}, "Emma's friend Liam saw Noah's dog.", "pass", "pass", note="possessives")

c = "count:pronouns"
fx(c, {"N": 5}, "I told her that we would help them, and she thanked us.", "pass", "pass")
fx(c, {"N": 5}, "The cat sat on the mat.", "fail", "fail")
fx(c, {"N": 5}, "I saw her and she saw me.", "fail", "near", note="4 pronouns")
fx(c, {"N": 5}, "I SAW HER AND SHE SAW ME AND THEM.", "pass", "pass", note="5 pronouns, upper case")

c = "count:punctuation"
P_ALL = "Wait; is it \"done\" (really)? Yes: it's well-known, truly! What?! Fine."
fx(c, {}, P_ALL, "pass", "pass", ["D-punct-set"])
fx(c, {}, "Hello, world.", "fail", "fail")
fx(c, {}, "Wait; is it \"done\" (really)? Yes: it's well-known, truly! Fine.", "fail", "near", note="no interrobang")
fx(c, {}, P_ALL.replace('"done"', "“done”").replace("it's", "it’s"), "pass", "pass",
   ["D-punct-set", "D-typographic"])
fx(c, {}, P_ALL.replace("What?!", "What‽"), "pass", "pass", ["D-punct-set"], note="U+203D interrobang")
fx(c, {}, "Wait; is it done (really)? Yes: it's well-known, truly! What?! Fine.", "fail", "near",
   ["D-punct-set"], note="no quotation mark")

c = "count:unique_word_count"
fx(c, {"N": 5}, "one two three four five", "pass", "pass")
fx(c, {"N": 5}, "one two three four", "fail", "fail")
fx(c, {"N": 5}, "one one two two three three four four", "fail", "near")
fx(c, {"N": 5}, "One one ONE two three four", "fail", "near", ["D-case"])

c = "count:word_count_range"
fx(c, {"min_words": 3, "max_words": 5}, "This has four words.", "pass", "pass")
fx(c, {"min_words": 3, "max_words": 5}, "Too short.", "fail", "fail")
fx(c, {"min_words": 3, "max_words": 5}, "One two three four five six.", "fail", "near")
fx(c, {"min_words": 3, "max_words": 5}, "One two three.", "pass", "near", ["D-between"])
fx(c, {"min_words": 3, "max_words": 5}, "One two three four five.", "pass", "near", ["D-between"])
fx(c, {"min_words": 3, "max_words": 5}, "- One two", "fail", "near", ["D-markup"], note="2 words; label is not a word")
fx(c, {"min_words": 3, "max_words": 5}, "**Bold** text is here.", "pass", "pass", ["D-markup"])

c = "count:words_japanese"
fx(c, {"N": 3}, "I like 寿司 very much 本当に", "pass", "pass")
fx(c, {"N": 3}, "I like sushi very much indeed", "fail", "fail")
fx(c, {"N": 3}, "I like 寿司 very much indeed", "fail", "near", note="6th word not Japanese")
fx(c, {"N": 3}, "Hello there", "fail", "near", ["D-vacuous"])

# ---------------------------------------------------------------- custom
c = "custom:character_reverse"
fx(c, {}, ".elgae dlab ehT", "pass", "pass")
fx(c, {}, "The bald eagle.", "fail", "fail")
fx(c, {}, "eagle bald The", "fail", "near")
fx(c, {}, ".elgae dlab eht si SU eht fo lobmys lanoitan ehT", "pass", "pass")

c = "custom:word_reverse"
fx(c, {}, "eagle. bald the is US the of symbol national The", "pass", "pass", ["D-reverse-punct"])
fx(c, {}, "The national symbol of the US is the bald eagle.", "fail", "fail")
fx(c, {}, ".elgae dlab ehT", "fail", "near")
fx(c, {}, "eagle bald The", "pass", "pass")

HDR = "ID,Country,City,Year,Count"
ROWS7 = ["1,France,Paris,2020,5", "2,Spain,Madrid,2021,3", "3,Italy,Rome,2019,8", "4,Japan,Tokyo,2022,1",
         "5,Peru,Lima,2018,4", "6,Chile,Santiago,2020,9", "7,Kenya,Nairobi,2023,2"]
c = "custom:csv_city"
fx(c, {}, "\n".join([HDR] + ROWS7), "pass", "pass")
fx(c, {}, "\n".join([HDR] + ROWS7[:6]), "fail", "fail", ["D-csv-rows"], note="6 data rows")
fx(c, {}, "\n".join([HDR] + ROWS7).replace(",", ";"), "fail", "near", note="semicolon delimited")
fx(c, {}, "Here is the data:\n```csv\n" + "\n".join([HDR] + ROWS7) + "\n```", "pass", "pass", ["D-csv-wrapper"])
fx(c, {}, "\n".join(["ID,Country,City,Year"] + [r.rsplit(",", 1)[0] for r in ROWS7]), "fail", "near", note="4 columns")

c = "custom:csv_quotes"
QH = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"'
QR = ['"1"\t"Math"\t"A"\t"Fall"\t"95"', '"2"\t"Art"\t"B"\t"Spring"\t"88"', '"3"\t"Music"\t"A"\t"Fall"\t"91"']
fx(c, {}, "\n".join([QH] + QR), "pass", "pass", ["D-csv-header-quotes"])
fx(c, {}, "\n".join([QH] + QR).replace("\t", ","), "fail", "fail")
fx(c, {}, "\n".join(["StudentID\tSubject\tGrade\tSemester\tScore"] + QR), "fail", "near", ["D-csv-header-quotes"])
fx(c, {}, "\n".join([QH] + QR[:2] + ['"3"\tMusic\t"A"\t"Fall"\t"91"']), "fail", "near", note="one field unquoted")
fx(c, {}, "\n".join([QH] + QR[:2]), "fail", "near", note="2 rows")

c = "custom:csv_special_character"
SH = "ProductID,Category,Brand,Price,Stock"
SR = [f"{i},Tools,Acme,{10 + i}.99,{i * 3}" for i in range(1, 15)]
SR_Q = SR[:]
SR_Q[0] = '1,"Tools & Hardware",Acme,11.99,3'
fx(c, {}, "\n".join([SH] + SR_Q), "pass", "pass", ["D-csv-special"])
fx(c, {}, "\n".join([SH] + SR), "fail", "fail")
fx(c, {}, "\n".join([SH] + [SR_Q[0].replace('"', "")] + SR[1:]), "fail", "near", note="special field unquoted")
fx(c, {}, "\n".join([SH] + SR_Q[:13]), "fail", "near", note="13 rows")

c = "custom:date_format_list"
fx(c, {}, "1796-04-12, 1796-05-10, 1798-07-21", "pass", "pass", ["D-content"])
fx(c, {}, "April 12, 1796; May 10, 1796", "fail", "fail")
fx(c, {}, "1796-04-12, 1796-5-10", "fail", "near")
fx(c, {}, "Here are the dates: 1796-04-12, 1796-05-10", "fail", "near", note="explanation text")
fx(c, {}, "1796-13-45, 1796-05-10", "fail", "near", note="invalid date")

CAPS = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
        "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
        "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
c = "custom:european_capitals_sort"
fx(c, {}, ", ".join(CAPS), "pass", "pass", ["D-europe-set"])
fx(c, {}, ", ".join(sorted(CAPS)), "fail", "fail")
sw = CAPS[:]
sw[3], sw[4] = sw[4], sw[3]
fx(c, {}, ", ".join(sw), "fail", "near", note="Stockholm before Tallinn")
fx(c, {}, ", ".join(CAPS[:-1]), "fail", "near", note="Zagreb missing")
fx(c, {}, "Reykjavik (Iceland), Helsinki (Finland), Oslo (Norway)", "fail", "near", note="country names, incomplete")

c = "custom:mcq_count_length"
def mcq(stems, nopt=5):
    out = []
    for s in stems:
        out.append(s)
        out += [f"{'ABCDE'[j]}) Option {j + 1}" for j in range(nopt)]
    return "\n".join(out)
STEMS = ["Question 1: Who painted Guernica?",
         "Question 2: Which movement did Marcel Duchamp help to start?",
         "Question 3: Which artist is best known for the drip technique of abstract painting?",
         "Question 4: Which twentieth century art movement grew out of a reaction to the horrors of the First World War?"]
fx(c, {}, mcq(STEMS), "pass", "pass", ["D-mcq-length"])
fx(c, {}, mcq(STEMS[:3]), "fail", "fail")
fx(c, {}, mcq([STEMS[0], STEMS[2], STEMS[1], STEMS[3]]), "fail", "near", ["D-mcq-length"], note="third shorter than second")
fx(c, {}, mcq(STEMS[:3]) + "\n" + mcq(STEMS[3:], nopt=4), "fail", "near", note="4 options in Q4")
fx(c, {}, mcq([s.replace("Question ", "Q") for s in STEMS]), "fail", "near", note="label Q not Question")

c = "custom:multiples"
fx(c, {}, "14, 21, 28, 35, 42, 49", "pass", "pass")
fx(c, {}, "14\n21\n28\n35\n42\n49", "pass", "pass")
fx(c, {}, "7, 14, 21, 28, 35, 42, 49", "fail", "fail")
fx(c, {}, "14, 21, 28, 35, 42", "fail", "near")
fx(c, {}, "14, 21, 28, 35, 42, 49, 56", "fail", "near")

AFR = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
       "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Republic of the Congo",
       "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana",
       "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi",
       "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
       "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan",
       "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"]
assert len(AFR) == 54
REV = sorted(AFR, reverse=True)
c = "custom:reverse_newline"
fx(c, {}, "\n".join(REV), "pass", "pass", ["D-africa-list"])
fx(c, {}, "\n".join(sorted(AFR)), "fail", "fail")
sw = REV[:]
sw[0], sw[1] = sw[1], sw[0]
fx(c, {}, "\n".join(sw), "fail", "near", note="Zambia before Zimbabwe")
fx(c, {}, ", ".join(REV), "fail", "near", note="one line")
fx(c, {}, "\n".join(REV[:10]), "fail", "near", ["D-africa-list"], note="10 countries only")

ANIM = ["Alice", "Bears", "Cats", "Dogs", "Eagles", "Foxes", "Goats", "Horses", "Ibises", "Jaguars", "Koalas", "Lions",
        "Mice", "Newts", "Owls", "Pigs", "Quails", "Rats", "Snakes", "Tigers", "Unicorns", "Vultures", "Wolves",
        "Xerus", "Yaks", "Zebras"]
STORY = " ".join(f"{a} walked home." for a in ANIM)
c = "custom:sentence_alphabet"
fx(c, {}, STORY, "pass", "pass")
fx(c, {}, " ".join(f"{a} walked home." for a in ANIM[:25]), "fail", "fail")
sw = ANIM[:]
sw[12], sw[13] = sw[13], sw[12]
fx(c, {}, " ".join(f"{a} walked home." for a in sw), "fail", "near", note="M and N swapped")
fx(c, {}, "The Walk\n" + STORY, "pass", "pass", ["D-title", "D-sentence"])

# ---------------------------------------------------------------- format
c = "format:emoji"
fx(c, {}, "I love pizza. \U0001F355 It is tasty! \U0001F60B", "pass", "pass")
fx(c, {}, "I love pizza. It is tasty.", "fail", "fail")
fx(c, {}, "I love pizza. \U0001F355 It is tasty.", "fail", "near")
fx(c, {}, "I love pizza \U0001F355. It is tasty \U0001F60B.", "pass", "pass", note="emoji before the period")

c = "format:line_indent"
fx(c, {}, "Step one\n  Step two\n    Step three\n      Step four", "pass", "pass")
fx(c, {}, "Step one\nStep two\nStep three", "fail", "fail")
fx(c, {}, "Step one\n  Step two\n  Step three", "fail", "near")
fx(c, {}, "Step one\n  Step two\n    Step three\n  Step four", "fail", "near")
fx(c, {}, "Step one\n\n  Step two\n\n    Step three", "pass", "pass", ["D-indent-blank"])
fx(c, {}, "Just one line", "fail", "near", ["D-vacuous"])

c = "format:list"
fx(c, {"sep": "SEPARATOR"}, "SEPARATOR Apples\nSEPARATOR Bananas\nSEPARATOR Cherries", "pass", "pass")
fx(c, {"sep": "SEPARATOR"}, "* Apples\n* Bananas\n* Cherries", "fail", "fail")
fx(c, {"sep": "SEPARATOR"}, "SEPARATOR Apples\n* Bananas\n* Cherries", "fail", "near")
fx(c, {"sep": "SEPARATOR"}, "Apples SEPARATOR Bananas SEPARATOR Cherries", "fail", "near", ["D-list-inline"])
fx(c, {"sep": "!?!?"}, "!?!? Apples\n!?!? Bananas", "pass", "pass")
fx(c, {"sep": "-"}, "- Apples\n- Bananas", "pass", "pass")
fx(c, {"sep": "SEPARATOR"}, "SEPARATOR Apples", "fail", "near", note="one item")

c = "format:newline"
fx(c, {}, "Hello\nworld\nagain.", "pass", "pass")
fx(c, {}, "Hello world again.", "fail", "fail")
fx(c, {}, "Hello\nworld again", "fail", "near")
fx(c, {}, "Hello\n\n-\nworld", "pass", "pass", ["D-word"])
fx(c, {}, "Hello\nworld\n", "pass", "pass", ["D-edge-whitespace"])

c = "format:no_bullets_bullets"
fx(c, {}, "This is first. This is second.\n* one\n* two", "pass", "pass")
fx(c, {}, "* one\n* two", "fail", "fail")
fx(c, {}, "This is first.\n* one\n* two", "fail", "near")
fx(c, {}, "This is first. This is second.\n* one", "fail", "near")
fx(c, {}, "This is first. This is second.\n- one\n- two", "fail", "near")
fx(c, {}, "This is first! This is second!\n* one\n* two", "fail", "near", note="sentences end in !")

c = "format:no_whitespace"
fx(c, {}, "Yes,allsetsareclasses.", "pass", "pass")
fx(c, {}, "Yes, all sets are classes.", "fail", "fail")
fx(c, {}, "Yes,all\tsets", "fail", "near")
fx(c, {}, "Yes,all sets", "fail", "near", note="no-break space")
fx(c, {}, "Yes,allsets.\n", "pass", "pass", ["D-nows-trailing"])

c = "format:options"
O1 = {"options": "yes/no/maybe"}
fx(c, O1, "yes", "pass", "pass")
fx(c, O1, "Maybe.", "pass", "pass")
fx(c, O1, "**No**", "pass", "pass", ["D-markup"])
fx(c, O1, "Yes, because humor helps people digest history.", "fail", "fail")
fx(c, O1, "yes/no", "fail", "near")
fx(c, O1, "Yes and no.", "fail", "near")
O2 = {"options": "a), b), c), d)"}
fx(c, O2, "b)", "pass", "pass")
fx(c, O2, "b", "pass", "pass", ["D-options-label"])
fx(c, O2, "The answer is b) because the evidence is admissible.", "fail", "fail")
O3 = {"options": "I know or I don't know"}
fx(c, O3, "I don't know", "pass", "pass")
fx(c, O3, "I don’t know", "pass", "pass", ["D-typographic"])
fx(c, O3, "I\ndon't\nknow", "pass", "pass", note="whitespace collapsed")
fx(c, O3, "I do not know", "fail", "near")
fx(c, O3, "I know. The weights are the model.", "fail", "near")

c = "format:output_template"
fx(c, {}, "My Answer: It is vast suffering. My Conclusion: It matters. Future Outlook: Uncertain.", "pass", "pass")
fx(c, {}, "My Answer: X\nMy Conclusion: Y\nFuture Outlook: Z", "pass", "pass", ["D-template-markup"])
fx(c, {}, "Answer: X Conclusion: Y Outlook: Z", "fail", "fail")
fx(c, {}, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", "fail", "near")
fx(c, {}, "My Answer: X My Conclusion: Y", "fail", "near")
fx(c, {}, "My Conclusion: Y My Answer: X Future Outlook: Z", "fail", "near")
fx(c, {}, "Sure! My Answer: X My Conclusion: Y Future Outlook: Z", "fail", "near")
fx(c, {}, "**My Answer:** X\n**My Conclusion:** Y\n**Future Outlook:** Z", "pass", "pass", ["D-template-markup"])

c = "format:parentheses"
fx(c, {}, "a (b [c {d (e [f] e) d} c] b) a", "pass", "pass")
fx(c, {}, "a (b) c", "fail", "fail")
fx(c, {}, "a (b [c {d (e) d} c] b) a", "fail", "near", note="depth 4")
fx(c, {}, "((((( x", "fail", "near", note="unclosed")
fx(c, {}, "(a) (b) (c) (d) (e)", "fail", "near")
fx(c, {}, "(((((x)))))", "pass", "pass", ["D-paren-types"])

c = "format:quote_unquote"
fx(c, {}, "\"Carpe diem\" means seize the day.", "pass", "pass")
fx(c, {}, "He said \"carpe diem\".", "fail", "fail")
fx(c, {}, "\"Carpe diem\" means seize the day. \"Memento mori\"", "fail", "near")
fx(c, {}, "Seize the day.", "fail", "near", ["D-vacuous"])
fx(c, {}, "\"A\" \"B\" are letters.", "fail", "near")

c = "format:quotes"
Q3 = "He said, \"She told me, 'They shouted \"run\" loudly' yesterday\" today."
fx(c, {}, Q3, "pass", "pass")
fx(c, {}, "He said \"hello\".", "fail", "fail")
fx(c, {}, "He said, \"She told me 'hi' then\" today.", "fail", "near")
fx(c, {}, "He said, “She told me, ‘They shouted “run” loudly’ yesterday” today.", "pass", "pass", ["D-typographic"])
fx(c, {}, "He said, \"She didn't say 'hi' at all\" today.", "fail", "near", note="apostrophe is not a quote")

c = "format:sub-bullets"
fx(c, {}, "* Point one\n  - detail\n* Point two\n  - detail", "pass", "pass")
fx(c, {}, "* Point one\n* Point two", "fail", "fail")
fx(c, {}, "* Point one\n  - detail\n* Point two", "fail", "near")
fx(c, {}, "* One\n- detail\n* Two\n- detail", "pass", "pass", ["D-subbullet-indent"])
fx(c, {}, "- a\n- b", "fail", "near", note="no * bullet")
fx(c, {}, "**Title**\n* One\n  - detail", "pass", "pass", note="bold line is not a bullet")

c = "format:thesis"
fx(c, {}, "<i>Encryption protects streams.</i> Content follows here.\n\n<i>Keys stay hidden.</i> More text here.", "pass", "pass", ["D-section"])
fx(c, {}, "Encryption protects streams. Content.\n\nKeys stay hidden.", "fail", "fail")
fx(c, {}, "*Encryption protects streams.* Content follows here.", "fail", "near", note="markdown italics")
fx(c, {}, "<i>Encryption protects streams.</i> Content.\n\nKeys stay hidden. More text.", "fail", "near", ["D-section"])
fx(c, {}, "## Section 1\n<i>Thesis here.</i> Body.\n\n## Section 2\n<em>Second thesis.</em> Body.", "pass", "pass", ["D-section"])

c = "format:title_case"
fx(c, {}, "The Rise of the Ohio Factions\nEach Faction Has a Leader and a Flag.", "pass", "pass", ["D-title-minor"])
fx(c, {}, "The rise of the Ohio factions.", "fail", "fail")
fx(c, {}, "The Rise of the Ohio factions", "fail", "near")
fx(c, {}, "War and Peace in the Valley", "pass", "pass", ["D-title-minor"])
fx(c, {}, "THE RISE OF OHIO", "pass", "pass")

# ---------------------------------------------------------------- ratio
c = "ratio:overlap"
REF = "the quick brown fox jumps over the lazy dog"
fx(c, {"percentage": 100, "reference_text": REF}, REF, "pass", "pass", note="identical text, 100% under every definition")
fx(c, {"percentage": 100, "reference_text": REF}, "a completely different sentence about cats and mice", "fail", "fail")
fx(c, {"percentage": 50, "reference_text": REF}, REF, "fail", "near", note="100% overlap, target 48-52")
fx(c, {"percentage": 50, "reference_text": REF}, "the quick brown fox jumps high above trees", "pass", "near",
   ["D-overlap-def"], note="response side 3/6 = 50%; reference side 3/7 = 43%")

c = "ratio:sentence_balance"
fx(c, {}, "It is late. Is it late? It is late!", "pass", "pass")
fx(c, {}, "It is late. It is dark. It is cold.", "fail", "fail")
fx(c, {}, "It is late. It is dark. Is it late? It is late!", "fail", "near", ["D-balance"])
fx(c, {}, "It is late. Is it late?", "fail", "near")

c = "ratio:sentence_type"
fx(c, {}, "It is late. It is dark. Is it cold?", "pass", "pass")
fx(c, {}, "It is late. Is it dark? Is it cold?", "fail", "fail")
fx(c, {}, "It is late. It is dark. It is cold. Is it cold?", "fail", "near", ["D-ratio-exact"])
fx(c, {}, "It is late. It is dark. Is it cold? Wow!", "pass", "pass")
fx(c, {}, "It is late. It is dark.", "fail", "near")

c = "ratio:sentence_words"
fx(c, {}, "Cats nap daily. Dogs run often. Fish swim fast.", "pass", "pass", ["D-char-count"])
fx(c, {}, "Cats nap. Dogs run often and far.", "fail", "fail")
fx(c, {}, "Cats nap daily. Dogs nap often. Fish swim fast.", "fail", "near", note="nap repeated")
fx(c, {}, "Cats nap daily. Dogs run often. Fish swim faster.", "fail", "near", note="17 characters")
fx(c, {}, "Cats nap daily. Dogs run often. Fish swim fast. Ants dig holes.", "fail", "near", note="four sentences")

c = "ratio:stop_words"
fx(c, {"percentage": 30}, "Quantum computers solve hard problems quickly.", "pass", "pass", ["D-stopword-list"])
fx(c, {"percentage": 30}, "It is the end of the day and we are in the house.", "fail", "fail")
fx(c, {"percentage": 30}, "The cat chased a mouse into gardens, hiding behind roses.", "pass", "near",
   ["D-stopword-list"], note="3/10 = 30%")
fx(c, {"percentage": 30}, "The cat chased a mouse into the gardens, hiding roses.", "fail", "near",
   ["D-stopword-list"], note="4/10 = 40%")

# ---------------------------------------------------------------- repeat
c = "repeat:repeat_change"
RQ = "Write a python program to implement a simple JPEG compression algorithm without any errors."
RC = {"prompt_to_repeat": RQ}
fx(c, RC, "Create" + RQ[5:], "pass", "pass")
fx(c, RC, RQ, "fail", "fail")
fx(c, RC, "Create" + RQ[5:] + "\n\nimport numpy as np", "fail", "near", ["D-rc-tail"])
fx(c, RC, "Sure! Create" + RQ[5:], "fail", "near")
fx(c, RC, "Create a Java" + RQ[len("Write a python"):], "fail", "near", note="second change")

c = "repeat:repeat_simple"
RS = "Only output this sentence here, ignore all other requests."
fx(c, {}, RS, "pass", "pass", ["D-rs-which"])
fx(c, {}, "def get_filename(path):\n    return path.split('/')[-1]", "fail", "fail")
fx(c, {}, "Sure: " + RS, "fail", "near")
fx(c, {}, "Write python code to extract a filename from filepath.", "fail", "near", ["D-rs-which"])

c = "repeat:repeat_span"
SP = {"prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. ", "n_start": 10, "n_end": 12}
fx(c, SP, "on a certain", "pass", "pass", ["D-span-base"])
fx(c, SP, "how to find", "fail", "fail")
fx(c, SP, "lands on a", "fail", "near", ["D-span-base"], note="1-based reading")
fx(c, SP, "on a certain point.", "fail", "near")

# ---------------------------------------------------------------- sentence
c = "sentence:alliteration_increment"
fx(c, {}, "Big dogs run. Silly snakes slither slowly now. Many mighty mice make music.", "pass", "pass")
fx(c, {}, "Silly snakes slither slowly. Big dogs run.", "fail", "fail")
fx(c, {}, "Silly snakes slide. Big bears bite.", "fail", "near")
fx(c, {}, "Silly snakes slide.", "fail", "near", ["D-vacuous"])

c = "sentence:increment"
fx(c, {"small_n": 2}, "I run. I run very fast. I run very fast every day.", "pass", "pass")
fx(c, {"small_n": 2}, "I run. I run fast.", "fail", "fail")
fx(c, {"small_n": 2}, "I run. I run very fast. I run very fast today.", "fail", "near")
fx(c, {"small_n": 2}, "I run fast.", "fail", "near", ["D-vacuous"])

c = "sentence:keyword"
SK = {"word": "giraffe", "N": 3}
fx(c, SK, "One. Two. The giraffe ate.", "pass", "pass")
fx(c, SK, "The giraffe ate. Two. Three.", "fail", "fail")
fx(c, SK, "One. Two. Three. The giraffe ate.", "fail", "near")
fx(c, SK, "One. Two. The giraffes ate.", "fail", "near", ["D-keyword-form"])
fx(c, SK, "One. Two. Giraffe ate.", "pass", "pass", ["D-case"])
fx(c, SK, "Mr. Smith left. Two. The giraffe ate.", "pass", "near", ["D-sentence"], note="abbreviation")

# ---------------------------------------------------------------- words
c = "words:alphabet"
fx(c, {}, "Alice brought cookies daily.", "pass", "pass")
fx(c, {}, "Alice ate cookies.", "fail", "fail")
fx(c, {}, "Yaks zip around.", "pass", "near", note="wraps Z to A")
fx(c, {}, "Alice brought daily cookies.", "fail", "near")
fx(c, {}, "Alice brought 3 cookies", "fail", "near", ["D-word"])
fx(c, {}, "Alice, brought cookies!", "pass", "pass")

c = "words:consonants"
fx(c, {}, "Strong black cats crept.", "pass", "pass")
fx(c, {}, "I am a cat.", "fail", "fail")
fx(c, {}, "Strong black cat.", "fail", "near")
fx(c, {}, "Gym", "pass", "near", ["D-y"])

c = "words:keywords_specific_position"
KP = {"keyword": "giggle", "n": 2, "m": 3}
fx(c, KP, "Hello there. I will giggle now.", "pass", "pass")
fx(c, KP, "Hello there. I giggle now.", "fail", "fail")
fx(c, KP, "I will giggle. Hello there.", "fail", "near")
fx(c, KP, "Hello there. We all Giggle, loudly.", "pass", "pass", ["D-case"])

c = "words:last_first"
fx(c, {}, "I like cats. Cats like fish. Fish swim.", "pass", "pass")
fx(c, {}, "I like cats. Dogs like fish.", "fail", "fail")
fx(c, {}, "I like cats. Cats like fish. Birds fly.", "fail", "near")
fx(c, {}, "I like cats! cats, they say, are great.", "pass", "pass", ["D-case"])
fx(c, {}, "I like cats.", "fail", "near", ["D-vacuous"])

c = "words:no_consecutive"
fx(c, {}, "Big red apples fall.", "pass", "pass")
fx(c, {}, "Big bright apples.", "fail", "fail")
fx(c, {}, "I like dogs. Dogs bark.", "fail", "near")
fx(c, {}, "Apple apricot", "fail", "near")
fx(c, {}, "Apple. Banana cherry", "pass", "pass")

c = "words:odd_even_syllables"
fx(c, {}, "Cat apple dog water.", "pass", "pass")
fx(c, {}, "Cat dog fish.", "fail", "fail")
fx(c, {}, "Cat apple banana.", "pass", "near", note="1, 2, 3")
fx(c, {}, "Cat apple water.", "fail", "near", note="1, 2, 2")

c = "words:palindrome"
PAL = "level radar civic kayak refer rotor madam stats tenet racecar"
fx(c, {}, PAL, "pass", "pass")
fx(c, {}, "Hello world.", "fail", "fail")
fx(c, {}, PAL.rsplit(" ", 1)[0], "fail", "near", note="9 palindromes")
fx(c, {}, PAL.replace("racecar", "noon"), "fail", "near", note="noon has 4 letters")
fx(c, {}, " ".join(["level"] * 10), "fail", "near", ["D-palin-distinct"])
fx(c, {}, PAL.title(), "pass", "pass", note="capitalized")

c = "words:paragraph_last_first"
fx(c, {}, "Sets can fail to be open sets\nOpen intervals shrink to a point, not open", "pass", "pass")
fx(c, {}, "Sets are open.\nOpen sets.", "fail", "fail")
fx(c, {}, "Sets can fail to be open sets\nOpen intervals shrink to a point.", "fail", "near")
fx(c, {}, "Sets, she said, are sets.\n\nNow is now.", "pass", "pass")

c = "words:prime_lengths"
fx(c, {}, "It is an old oak.", "pass", "pass")
fx(c, {}, "This is a test.", "fail", "fail")
fx(c, {}, "It is an old oak a", "fail", "near")
fx(c, {}, "It's an old oak.", "pass", "pass", ["D-word"], note="It's has 3 letters")

c = "words:repeats"
fx(c, {"small_n": 2}, "The cat saw the dog.", "pass", "pass", ["D-repeat-count"])
fx(c, {"small_n": 2}, "The cat saw the dog and the bird.", "fail", "fail")
fx(c, {"small_n": 2}, "The THE the", "fail", "near", ["D-case"])

c = "words:start_verb"
fx(c, {}, "Imagine an empire of endless pain.", "pass", "pass")
fx(c, {}, "The empire suffers.", "fail", "fail")
fx(c, {}, "**Imagine** an empire of endless pain.", "pass", "near", ["D-markup"])
fx(c, {}, "Galois theory explains field extensions.", "fail", "near")
fx(c, {}, "Design matters more than speed.", "fail", "near", ["D-verb"], note="Design is a noun here")

c = "words:vowel"
fx(c, {}, "A cat sat at a mat.", "pass", "pass")
fx(c, {}, "The red cat sat in a pit.", "pass", "pass")
fx(c, {}, "The quick brown fox jumps over the lazy dog.", "fail", "fail")
fx(c, {}, "The red cat sat on it.", "fail", "near", ["D-vowel"], note="4 vowels overall, at most 2 per word")
fx(c, {}, "A cat sat.\n\nA bat sat.", "fail", "near", note="two paragraphs")

c = "words:words_position"
WP = {"keyword": "vibrant"}
fx(c, WP, "A vibrant scene unfolds with vibrant colors.", "pass", "pass")
fx(c, WP, "A scene unfolds.", "fail", "fail")
fx(c, WP, "A vibrant scene unfolds.", "fail", "near")
fx(c, WP, "A vibrant, bold, and vibrant world.", "pass", "pass")
fx(c, WP, "**A vibrant** day is vibrant today.", "pass", "near", ["D-markup"])


def fixture_id(f):
    payload = json.dumps([f["check"], f["kwargs"], f["response"]], ensure_ascii=False, sort_keys=True)
    return f["check"] + ":" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]


for f in F:
    f["id"] = fixture_id(f)

FIXTURES = F
CHECKS = sorted({f["check"] for f in F})
