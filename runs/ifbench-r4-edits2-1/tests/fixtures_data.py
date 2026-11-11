"""Labeled fixtures for the IFBench checks, labeled from audit/CONTRACTS.md alone.

Each fixture:
  check     instruction id
  kwargs    checker kwargs as HF `datasets` gives them (ints for n/m/n_start/n_end, floats otherwise),
            or key=<dataset key> to take kwargs and prompt from that dataset row
  response  the graded text
  label     contract verdict: "pass" or "fail"
  kind      "unambiguous": the label holds under every reading the text allows;
            "decision": the label holds under the proposed reading of the listed decision entries
  decisions decision entries the label depends on (kind "decision")
  grader    id of the finding (F-xx) or decision (D-xx) when the grader under audit gets it wrong;
            the test marks those xfail(strict=True)
Fixture ids are `<check>:<first 8 hex of sha256(check + kwargs + response)>`.
"""
import hashlib
import json

FIXTURES = []


def fx(check, response, label, kwargs=None, key=None, kind="unambiguous", decisions=(), grader=None, note=""):
    FIXTURES.append(dict(check=check, response=response, label=label, kwargs=kwargs or {}, key=key,
                         kind=kind, decisions=list(decisions), grader=grader, note=note))


def fixture_id(f):
    payload = json.dumps([f["check"], f["kwargs"], f["key"], f["response"]], ensure_ascii=False, sort_keys=True)
    return f'{f["check"]}:{hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]}'


# ---------------- count ----------------
C = "count:conjunctions"
fx(C, "I like tea and coffee, but I avoid soda or juice.", "pass", {"small_n": 3.0})
fx(C, "I like tea and coffee and milk.", "fail", {"small_n": 3.0})
fx(C, "And we sing and dance and, later, rest.", "fail", {"small_n": 3.0}, grader="F-03",
   note="one conjunction (and) written three ways; the grader counts raw tokens")

C = "count:keywords_multiple"
KW2 = {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
_kw_ok = ("The door opened. Bread and bread. Blue, blue, blue. Lamp lamp lamp lamp lamp. "
          "River river river river river river river.")
fx(C, _kw_ok, "pass", KW2)
fx(C, _kw_ok.replace("river.", "."), "fail", KW2, note="river six times")
fx(C, _kw_ok + " A driver waved.", "pass", KW2, grader="F-04",
   note="'driver' is not the keyword 'river' under any reading; the grader counts substrings")
fx(C, _kw_ok + " The blues played.", "pass", KW2, kind="decision", decisions=["D-keyword-form"], grader="F-04",
   note="inflected form; proposal: only the exact word counts")

C = "count:numbers"
fx(C, "In 2020 the town had 300 homes.", "pass", {"N": 2.0})
fx(C, "In 2020 the town had 300 homes and 4 shops.", "fail", {"N": 2.0})
fx(C, "Pi is about 3.14 today.", "pass", {"N": 1.0})
fx(C, "The ratio was 2:1 overall.", "pass", {"N": 2.0}, grader="F-05", note="two numbers; the grader deletes ':' and sees 21")
fx(C, "Shops open 9-5 daily.", "pass", {"N": 2.0}, grader="F-05")
fx(C, "1. Apples\n2. Pears", "fail", {"N": 2.0}, kind="decision", decisions=["D-list-label"], grader="D-list-label")

C = "count:person_names"
fx(C, "Emma met Liam and Noah at the park.", "pass", {"N": 3.0})
fx(C, "Emma met Liam at the park.", "fail", {"N": 3.0})
fx(C, "Emma met Liam, then Emma left.", "fail", {"N": 3.0})

C = "count:pronouns"
fx(C, "She told him that they would come.", "pass", {"N": 3.0})
fx(C, "Birds fly south in winter.", "fail", {"N": 3.0})
fx(C, "I think that all students like some tests.", "fail", {"N": 3.0}, grader="F-06",
   note="one pronoun (I); 'that' is a complementizer, 'all' and 'some' are determiners")

C = "count:punctuation"
_punct_all = ("Wait?! Really: yes; no, maybe. \"Quote\" it's (a) [b] {c} well-known — dash… "
              "slash/ end! Why? #$%&*+<=>@\\^_`|~")
fx(C, _punct_all, "pass")
fx(C, _punct_all.replace(";", ","), "fail", note="no semicolon")
fx(C, "Wait?! Really: yes; no, maybe. Why? Stop!", "fail", kind="decision", decisions=["D-punct-set"],
   grader="D-punct-set", note="six sentence marks and ?! only; no apostrophe, quotes, dash, brackets")

C = "count:unique_word_count"
fx(C, "Red green blue yellow purple orange.", "pass", {"N": 5.0})
fx(C, "Red red red green green.", "fail", {"N": 5.0})
fx(C, "“Red” red, green - green.", "fail", {"N": 4.0}, grader="F-07",
   note="two distinct words; the grader also counts '“red”' and an empty token from '-'")

C = "count:word_count_range"
fx(C, "The quick brown fox jumps today.", "pass", {"min_words": 5.0, "max_words": 7.0})
fx(C, "The quick brown fox jumps over the lazy dog today.", "fail", {"min_words": 5.0, "max_words": 7.0})
fx(C, "One two three four five.", "pass", {"min_words": 5.0, "max_words": 7.0}, kind="decision", decisions=["D-between"])
fx(C, "Don't stop, it's fine now.", "pass", {"min_words": 5.0, "max_words": 5.0}, kind="decision",
   decisions=["D-word-split"], grader="D-word-split")

C = "count:words_japanese"
fx(C, "I love 寿司 and eat ラーメン often.", "pass", {"N": 3.0})
fx(C, "I love sushi and eat ramen often.", "fail", {"N": 3.0})
fx(C, "I have 3 cats and 寿司 here.", "fail", {"N": 3.0}, grader="F-08",
   note="the 3rd word is the numeral 3, not Japanese; the grader skips digit tokens")
fx(C, "I love Fabricや寿司 a lot.", "fail", {"N": 3.0}, kind="decision", decisions=["D-japanese-mixed"],
   grader="D-japanese-mixed", note="the 3rd token mixes Latin and Japanese letters")

# ---------------- custom ----------------
C = "custom:character_reverse"
fx(C, ".SU eht fo lobmys lanoitan eht si elgae dlab ehT", "pass")
fx(C, "The bald eagle is the national symbol of the US.", "fail")
fx(C, "The bald eagle is the national symbol of the US. (.elgae dlab ehT)", "fail", grader="F-09",
   note="forward answer plus a reversed fragment; the grader looks for the substring 'elgae dlab'")

C = "custom:word_reverse"
fx(C, "US the of symbol national the is eagle bald The.", "pass")
fx(C, "The bald eagle is the national symbol of the US.", "fail")
fx(C, "The bald eagle is the national symbol of the US. Reversed: US the of symbol national the is eagle bald The.", "fail",
   grader="F-09", note="forward answer followed by its reversal")

C = "custom:csv_city"
_city_rows = ["1,France,Paris,2020,5", "2,Spain,Madrid,2021,7", "3,Italy,Rome,2019,3", "4,Japan,Tokyo,2022,9",
              "5,Peru,Lima,2018,2", "6,Chile,Santiago,2020,4", "7,Kenya,Nairobi,2021,6"]
_city = "ID,Country,City,Year,Count\n" + "\n".join(_city_rows)
fx(C, _city, "pass")
fx(C, "ID,Country,City,Year,Count\n" + "\n".join(_city_rows[:6]), "fail", note="6 rows")
fx(C, _city + "\n\n", "pass", kind="decision", decisions=["D-trailing-ws"], grader="D-trailing-ws")
fx(C, "```csv\n" + _city + "\n```", "pass", kind="decision", decisions=["D-wrapper"], grader="D-wrapper")
fx(C, "Hello\rworld", "fail", grader="F-10", note="a bare carriage return; the grader's csv.reader raises _csv.Error")
fx(C, "ID, Country, City, Year, Count\n" + "\n".join(r.replace(",", ", ") for r in _city_rows), "pass",
   kind="decision", decisions=["D-csv-space"], grader="D-csv-space")

C = "custom:csv_quotes"
_q = lambda *xs: "\t".join(f'"{x}"' for x in xs)
_csvq = "\n".join([_q("StudentID", "Subject", "Grade", "Semester", "Score"), _q("1", "Math", "A", "Fall", "90"),
                   _q("2", "Art", "B", "Fall", "80"), _q("3", "Bio", "C", "Spring", "70")])
fx(C, _csvq, "pass")
fx(C, _csvq.replace("\t", ","), "fail", note="comma delimited")
fx(C, _csvq.replace('"Art"', "Art"), "fail", note="one unquoted field")
fx(C, _csvq.replace('\t"A"\t', "\t\t"), "fail", grader="F-10",
   note="an empty field; the grader raises IndexError (exception = grading failure)")

C = "custom:csv_special_character"
_sc_rows = [f"{i},Tools,Brand{i},{10 + i}.99,{i * 3}" for i in range(1, 15)]
_sc_rows[0] = '1,Tools,"Smith & Co",10.99,3'
_sc = "ProductID,Category,Brand,Price,Stock\n" + "\n".join(_sc_rows)
fx(C, _sc, "pass")
fx(C, _sc.replace('"Smith & Co"', "SmithCo"), "fail", note="no quoted special-character field")
_sc_bad = list(_sc_rows)
_sc_bad[4] = "5,Tools,Brand5,14.99"
fx(C, "ProductID,Category,Brand,Price,Stock\n" + "\n".join(_sc_bad), "fail", grader="F-11",
   note="row 5 has 4 fields; the grader stops checking rows after the first special field")

C = "custom:date_format_list"
fx(C, "1796-04-12, 1805-12-02, 1815-06-18", "pass")
fx(C, "April 12, 1796, December 2, 1805", "fail")
fx(C, "Here are the dates: 1796-04-12, 1805-12-02", "fail")
fx(C, "1796-00-00, 1805-12-02", "fail", grader="F-12", note="month 00 and day 00 are not dates")

C = "custom:european_capitals_sort"
_caps = ("Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, "
         "Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, "
         "Chisinau, Bern, Ljubljana, Zagreb")
fx(C, _caps, "pass", grader="F-13",
   note="complete list with Kyiv (50.45 N) between Brussels and Prague; the grader's key omits Kyiv")
fx(C, "Helsinki, Reykjavik, Oslo", "fail", note="not sorted")

C = "custom:mcq_count_length"
_opts = "\nA) Picasso\nB) Dali\nC) Miro\nD) Matisse\nE) Monet"
_stems = ["Who painted Guernica?", "Which artist painted the melting clocks?",
          "Which movement did Marcel Duchamp help to found in Zurich?",
          "Which painter is best known for drip paintings made on canvas laid flat on the floor?"]
_mcq = "\n".join(f"Question {i + 1}: {s}{_opts}" for i, s in enumerate(_stems))
fx(C, _mcq, "pass")
fx(C, "\n".join(f"Question {i + 1}: {s}{_opts}" for i, s in enumerate(_stems[:3])), "fail", note="3 questions")
fx(C, "\n".join(f"Question: {s}{_opts}" for s in _stems), "pass", grader="F-14",
   note="each question starts with the label 'Question'; the grader requires a number after it")
fx(C, _mcq + "\nExplanation: Picasso painted Guernica in 1937.", "fail", grader="F-14",
   note="an explanation after the last question; the grader ignores lines after the options")

C = "custom:multiples"
fx(C, "14, 21, 28, 35, 42, 49", "pass")
fx(C, "7, 14, 21, 28, 35, 42, 49", "fail")
fx(C, "Here they are: 14, 21, 28, 35, 42, 49", "fail", kind="decision", decisions=["D-multiples-prose"],
   grader="D-multiples-prose")

C = "custom:reverse_newline"
AFRICA = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
          "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt",
          "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea",
          "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali",
          "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Republic of the Congo",
          "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa",
          "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"]
fx(C, "\n".join(sorted(AFRICA, reverse=True)), "pass")
fx(C, "\n".join(sorted(AFRICA)), "fail", note="ascending")
fx(C, "\n".join(sorted(AFRICA, reverse=True)) + "\nThese are all 54 countries.", "fail")
fx(C, "\n".join(["Zimbabwe", "Zambia", "Yemen", "Yemen", "X (none)"] + sorted(AFRICA, reverse=True)[2:]), "fail", grader="F-40",
   note="Yemen (twice) and 'X (none)' are not African countries; the grader checks only order and length")
fx(C, "Here is the list:\n" + "\n".join(sorted(AFRICA, reverse=True)), "fail", kind="decision", decisions=["D-wrapper"],
   grader="D-wrapper")

C = "custom:sentence_alphabet"
_alpha = ["Alice ate apples.", "Bob baked bread.", "Cats chased crows.", "Dogs dug ditches.", "Eels eat eggs.",
          "Foxes fled fast.", "Geese got grain.", "Hens hid hay.", "Ink is inside.", "Jays jumped joyfully.",
          "Kites kept kicking.", "Lions lay low.", "Mice made mess.", "Newts nap nightly.", "Owls observe often.",
          "Pigs play politely.", "Quails quietly quit.", "Rats run rapidly.", "Seals swim swiftly.",
          "Toads take time.", "Urchins use umbrellas.", "Voles visit valleys.", "Wolves wander widely.",
          "Xerus xeroxed x-rays.", "Yaks yawn yearly.", "Zebras zigzag zealously."]
fx(C, " ".join(_alpha), "pass")
fx(C, " ".join(_alpha[:25]), "fail", note="25 sentences")
fx(C, " ".join(['"Alice ate apples," she said.'] + _alpha[1:]), "pass", grader="F-15",
   note="sentence 1 starts with a quotation mark; its first word is Alice")

# ---------------- format ----------------
C = "format:emoji"
fx(C, "I love tea \U0001F375. It is warm ☕.", "pass")
fx(C, "I love tea. \U0001F375 It is warm. ☕", "pass", kind="decision", decisions=["D-emoji-position"])
fx(C, "I love tea \U0001F375. It is warm.", "fail")
fx(C, "I love America \U0001F1FA\U0001F1F8. It is big \U0001F5FD.", "pass", grader="F-16",
   note="a flag emoji; the grader tests single code points and a lone regional indicator is not an emoji")
fx(C, "Pick one 1️⃣. Or pick two 2️⃣.", "pass", grader="F-16", note="keycap emoji")
fx(C, "My Day\nI love tea \U0001F375.", "fail", kind="decision", decisions=["D-sentence-fragment"],
   grader="D-sentence-fragment")
fx(C, "Acts of violence ... are revolutionary \U0001F525. Peace is better \U0001F54A.", "pass",
   note="an ellipsis before a lowercase word does not end a sentence (G5 as changed by C9)")

C = "format:line_indent"
fx(C, "Line one\n  Line two\n    Line three", "pass")
fx(C, "Line one\nLine two\nLine three", "fail")
fx(C, "Line one\n\n  Line two\n    Line three", "pass")
fx(C, "Line one\n\n\n  Line two\n    Line three", "pass", grader="F-17",
   note="same as the previous fixture with two blank lines; the grader removes list items while iterating")
fx(C, "Line one\n\tLine two\n\t\tLine three", "pass", grader="F-17", note="tab indentation")
fx(C, "Just one line", "fail", kind="decision", decisions=["D-vacuous"], grader="D-vacuous")

C = "format:list"
fx(C, "SEPARATOR Apples\nSEPARATOR Pears\nSEPARATOR Plums", "pass", {"sep": "SEPARATOR"})
fx(C, "* Apples\n* Pears", "fail", {"sep": "SEPARATOR"})
fx(C, "This well-known, state-of-the-art tool is useful.", "fail", {"sep": "-"}, grader="F-18",
   note="one sentence, no list; the grader counts any two occurrences of sep")
fx(C, "* Apples SEPARATOR\n* Pears SEPARATOR", "fail", {"sep": "SEPARATOR"}, grader="F-18",
   note="items marked by * bullets")

C = "format:newline"
fx(C, "Hello\nworld\nagain", "pass")
fx(C, "Hello world\nagain", "fail")
fx(C, "Hello world\n \nagain", "fail", grader="F-19",
   note="two words on line 1; a whitespace-only line makes the line count equal the word count")
fx(C, "Hello\n \nworld", "pass", grader="F-19", note="a whitespace-only line between one-word lines")

C = "format:no_bullets_bullets"
fx(C, "Springs store energy. Damping removes it.\n* Undamped motion\n* Damped motion", "pass")
fx(C, "Springs store energy.\n* Undamped motion\n* Damped motion", "fail")
fx(C, "Springs store energy\nDamping removes it\n* Undamped motion\n* Damped motion", "fail", grader="F-20",
   note="the two sentences do not end in a period")
fx(C, "Springs store energy. Damping removes it.\n\n* Undamped motion\n\n* Damped motion", "pass", grader="F-20",
   note="blank lines between bullets")
fx(C, "Springs store energy. Damping removes it.\n* Undamped motion\n* Damped motion\nThat is all.", "pass",
   kind="decision", decisions=["D-nbb-after"], grader="D-nbb-after")

C = "format:no_whitespace"
fx(C, "Setsarenotallclasses.", "pass")
fx(C, "Sets are classes.", "fail")
fx(C, "Sets are", "fail")
fx(C, "Setsarenotclasses.\n", "pass", kind="decision", decisions=["D-trailing-ws"], grader="D-trailing-ws")

C = "format:options"
fx(C, "Yes.", "pass", {"options": "yes/no/maybe"})
fx(C, "Probably", "fail", {"options": "yes/no/maybe"})
fx(C, "Yes, because games can teach history.", "fail", {"options": "yes/no/maybe"}, kind="decision",
   decisions=["D-options-extra"])
fx(C, "I don't know", "pass", {"options": "I know or I don't know"})
fx(C, "b)", "pass", {"options": "a), b), c), d)"})
fx(C, "B)", "pass", {"options": "a), b), c), d)"}, grader="F-21", note="option b) in upper case")
fx(C, "d.", "pass", {"options": "a), b), c), d)"}, kind="decision", decisions=["D-options-label"], grader="D-options-label")
fx(C, "Maybe\n", "pass", {"options": "yes/no/maybe"}, kind="decision", decisions=["D-trailing-ws"], grader="D-trailing-ws")

C = "format:output_template"
fx(C, "My Answer: Suffering at cosmic scale. My Conclusion: It matters. Future Outlook: Research continues.", "pass")
fx(C, "My Answer: Suffering at cosmic scale. My Conclusion: It matters.", "fail")
fx(C, "Future Outlook: Research continues. My Conclusion: It matters. My Answer: Suffering at cosmic scale.", "fail",
   grader="F-22", note="labels in reverse order")
fx(C, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", "fail", grader="F-22",
   note="the template copied with its placeholders unfilled")

C = "format:parentheses"
fx(C, "(a [b {c (d [e] d) c} b] a)", "pass")
fx(C, "(a [b {c} b] a)", "fail")
fx(C, "((((( deep )", "fail", grader="F-23", note="four of the five opening brackets are never closed")

C = "format:quote_unquote"
fx(C, 'He said "carpe diem", meaning seize the day.', "pass")
fx(C, 'He said "carpe diem"', "fail")
fx(C, '"Carpe diem", "memento mori" are mottos.', "fail", grader="F-24",
   note="the first quoted phrase is followed only by a comma")
fx(C, "“Carpe diem” “memento mori”", "fail", grader="F-24",
   note="typographic quotes, no explanation after either phrase")

C = "format:quotes"
fx(C, "He said \"she told me 'he yelled \"run\" loudly' today\" again.", "pass")
fx(C, 'He said "run" today.', "fail")
fx(C, "\"I can't,\" she said. \"Don't,\" he said. \"Won't.\"", "fail", grader="F-25",
   note="one level of quotes; the grader treats apostrophes as single quotes")
fx(C, "He said “she told me ‘he yelled “run” loudly’ today” again.", "pass", grader="F-25",
   note="three levels with typographic quotes")

C = "format:sub-bullets"
fx(C, "* Light\n  - Plants need light\n* Heat\n  - Plants feel heat", "pass")
fx(C, "* Light\n* Heat\n  - Plants feel heat", "fail")
fx(C, "Plants need light.", "fail", grader="F-26", note="no bullet points at all")
fx(C, "* **Light**\n  - Plants need light", "pass", grader="F-26", note="bold text inside a bullet")
fx(C, "* A well-known fact\n* A state-of-the-art tool", "fail", grader="F-26",
   note="no sub-bullets; hyphens inside words")

C = "format:thesis"
fx(C, "<i>Encryption keeps streams safe.</i> Keys stay on secure hardware.", "pass")
fx(C, "Encryption keeps streams safe. Keys stay hidden.", "fail")
fx(C, "Streams use DRM.\n\n<i>Keys never leave the device.</i> So ripping is hard.", "fail", grader="F-27",
   note="the response does not begin with the thesis (fails with either section reading)")
fx(C, "## Intro\n<i>Thesis one holds.</i> Text.\n\n## Details\nNo thesis here, just text.", "fail", grader="F-27",
   note="the second section has no thesis")

C = "format:title_case"
fx(C, "Factions Of Ohio Rise Again", "pass")
fx(C, "factions of ohio rise again", "fail")
fx(C, "The Fall of the Old Order", "pass", kind="decision", decisions=["D-titlecase-minor"], grader="D-titlecase-minor")
fx(C, "Ohio Doesn't Sleep", "pass", grader="F-28", note="a capitalised contraction; the grader sees the token n't")
fx(C, "<b>Factions</b> Of Ohio Rise Again", "pass", grader="F-28", note="HTML bold around a word; the grader sees the token b")

# ---------------- ratio ----------------
C = "ratio:overlap"
fx(C, "Is it easier to urbanize a jungle or to urbanize a desert?", "fail", key="149",
   note="a copy of the reference: 100% overlap under every reading, the target is 13%")
fx(C, "12345 67890 13579", "fail", key="149", note="0% overlap under every reading")

C = "ratio:sentence_balance"
fx(C, "Cats nap. Do dogs bark? Wow! Birds sing. Why? Great!", "pass")
fx(C, "Cats nap. Dogs bark. Birds sing?", "fail")
fx(C, "Cats nap and dogs bark", "fail", grader="F-29",
   note="no interrogative or exclamatory sentence; the grader passes 0 = 0 = 0")
fx(C, "Cats nap. Dogs bark. Do birds sing? Why? Wow!", "pass", kind="decision", decisions=["D-balance"], grader="D-balance")

C = "ratio:sentence_type"
fx(C, "Cats nap. Dogs bark. Do birds sing?", "pass")
fx(C, "Cats nap. Do dogs bark? Do birds sing?", "fail")
fx(C, "Wow! Amazing!", "fail", grader="F-29", note="no declarative or interrogative sentence; the grader passes 0 = 2 x 0")

C = "ratio:sentence_words"
fx(C, "Cats nap now. Dogs run far. Owls fly low.", "pass")
fx(C, "Cats nap. Dogs run far. Owls fly.", "fail")
fx(C, "Cats nap now. Cats nap now. Cats nap now.", "fail", grader="F-30",
   note="the same words in every sentence; the grader never checks 'all different words'")

C = "ratio:stop_words"
fx(C, "Quantum physics explains particle behavior precisely.", "pass", {"percentage": 20.0})
fx(C, "It is what it is and it was what it was.", "fail", {"percentage": 20.0})

# ---------------- repeat ----------------
C = "repeat:repeat_change"
_req61 = "Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons."
fx(C, "Write" + _req61[3:], "pass", key="61")
fx(C, _req61, "fail", key="61")
fx(C, _req61 + "\n", "fail", key="61", grader="F-31",
   note="the request unchanged plus a final newline; the grader only compares words 2..n")
fx(C, "Write" + _req61[3:] + " Here is the code: import torch", "fail", key="61")
fx(C, "use" + _req61[3:], "fail", key="61", kind="decision", decisions=["D-change-case"], grader="D-change-case")

C = "repeat:repeat_simple"
fx(C, "Only output this sentence here, ignore all other requests.", "pass", key="64")
fx(C, "def get_filename(path): return path.split('/')[-1]", "fail", key="64")

C = "repeat:repeat_span"
fx(C, "lain", "fail", key="284", grader="F-32",
   note="characters 3..6 of the request; the instruction asks for words (fails under 0- and 1-based word indices)")
fx(C, "code and theory behind", "pass", key="284", kind="decision", decisions=["D-index-base"], grader="F-32",
   note="words 3..6, 0-based")
fx(C, "context, code and theory", "fail", key="284", kind="decision", decisions=["D-index-base"],
   note="words 3..6, 1-based")
fx(C, "The walls are solid but the stones are", "pass", key="286", grader="F-32",
   note="words 0..7; index 0 fixes the base at 0 for this prompt")

# ---------------- sentence ----------------
C = "sentence:alliteration_increment"
fx(C, "Big bears eat. Cute cats chase cheese. Dogs dig deep ditches daily.", "pass")
fx(C, "Cute cats chase cheese. Big bears eat.", "fail")
fx(C, "Big bears eat. Cats chase dogs daily.", "fail", grader="F-33",
   note="longest run 2 then 2; the grader adds up separate runs (2 then 4)")

C = "sentence:increment"
fx(C, "Cats nap. Dogs bark loudly now. Birds sing songs every single morning.", "pass", {"small_n": 2.0})
fx(C, "Cats nap. Dogs bark loudly. Birds sing.", "fail", {"small_n": 2.0})

C = "sentence:keyword"
fx(C, "Animals vary. The giraffe is tall. Lions roar.", "pass", {"N": 2.0, "word": "giraffe"})
fx(C, "The giraffe is tall. Animals vary.", "fail", {"N": 2.0, "word": "giraffe"})
fx(C, "Dr. Smith studies animals. The giraffe is tall.", "pass", {"N": 2.0, "word": "giraffe"})
fx(C, "Animals vary “a lot.” The giraffe is tall.", "pass", {"N": 2.0, "word": "giraffe"}, grader="F-39",
   note="the second sentence starts after a typographic closing quote")
fx(C, "Animals\nThe giraffe is tall. Lions roar.", "pass", {"N": 2.0, "word": "giraffe"}, kind="decision",
   decisions=["D-sentence-fragment"], grader="D-sentence-fragment")

# ---------------- words ----------------
C = "words:alphabet"
fx(C, "Apples bake cleanly during evenings.", "pass")
fx(C, "Apples bake slowly.", "fail")
fx(C, "Yaks zip across.", "pass")
fx(C, "Apples “bake” cleanly.", "pass", grader="F-34", note="typographic quotes around a word")
fx(C, "Apples bake — cleanly during.", "pass", grader="F-34", note="an em dash between words")

C = "words:consonants"
fx(C, "Strong winds blow.", "pass")
fx(C, "Strong winds go.", "fail")
fx(C, "- Strong winds blow.", "pass", grader="F-35", note="a bullet before the line; '-' is not a word")

C = "words:keywords_specific_position"
fx(C, "Kids play outside. They often giggle loudly.", "pass", {"keyword": "giggle", "n": 2, "m": 3})
fx(C, "Kids play outside. They giggle loudly.", "fail", {"keyword": "giggle", "n": 2, "m": 3})
fx(C, "Kids play outside. Don't ever giggle loudly.", "pass", {"keyword": "giggle", "n": 2, "m": 3},
   kind="decision", decisions=["D-word-split"], grader="D-word-split")

C = "words:last_first"
fx(C, "I love the sea. Sea breezes calm me. Me and you walk home.", "pass")
fx(C, "I love the sea. Waves calm me.", "fail")
fx(C, "She shouted “home”. Home is far.", "pass", grader="F-34", note="typographic quotes around the last word")
fx(C, "I love the sea. Sea, they say, is calm.", "pass", grader="F-36", note="a comma after the first word of sentence 2")
fx(C, "She said “go home.” Away we go.", "fail", grader="F-39",
   note="two sentences; NLTK punkt does not split after a period inside a typographic closing quote")

C = "words:no_consecutive"
fx(C, "Cats eat fish daily.", "pass")
fx(C, "Cats chase fish.", "fail")
fx(C, "“Apples” “bananas” grow.", "pass", grader="F-34", note="typographic quotes")

C = "words:odd_even_syllables"
fx(C, "Cats happy dogs table", "pass")
fx(C, "Cats dogs run", "fail")

C = "words:palindrome"
fx(C, "level radar civic kayak refer rotor stats tenet madam racecar", "pass")
fx(C, "level radar civic", "fail")
fx(C, " ".join(["level"] * 10), "fail", kind="decision", decisions=["D-palindrome-distinct"],
   grader="D-palindrome-distinct")

C = "words:paragraph_last_first"
fx(C, "Time heals wounds over time.\nLove conquers all in love.", "pass")
fx(C, "Time heals wounds.\nLove conquers all.", "fail")
fx(C, "Time, as always, heals all wounds over time.", "pass", grader="F-36", note="a comma after the first word")
fx(C, "**Time** heals all wounds over time.", "pass", grader="F-36", note="bold markup around the first word")

C = "words:prime_lengths"
fx(C, "We are not alone.", "pass")
fx(C, "I am here.", "fail")
fx(C, "We are — not alone.", "pass", grader="F-34", note="an em dash between words")

C = "words:repeats"
fx(C, "Cats nap. Cats play.", "pass", {"small_n": 2.0})
fx(C, "Cats nap. Cats play. Cats eat.", "fail", {"small_n": 2.0})
fx(C, "Cats nap. “Cats” play. Cats eat.", "fail", {"small_n": 2.0}, grader="F-34",
   note="typographic quotes hide one occurrence")

C = "words:start_verb"
fx(C, "Imagine an empire of endless pain.", "pass", grader="F-37",
   note="imperative verb; the NLTK tagger labels sentence-initial 'Imagine' NNP")
fx(C, "The empire suffers endlessly.", "fail")
fx(C, "**Consider** an empire of endless pain.", "pass", grader="F-37", note="bold markup before the verb")

C = "words:vowel"
fx(C, "The bat ran to the dog.", "pass", kind="decision", decisions=["D-vowel-scope"])
fx(C, "Quiet unique audio is fine.", "fail")
fx(C, "The bat ran\nto the dog.", "pass", kind="decision", decisions=["D-vowel-paragraph"], grader="D-vowel-paragraph")

C = "words:words_position"
fx(C, "A vibrant day felt vibrant indeed.", "pass", {"keyword": "vibrant"})
fx(C, "A vibrant day felt calm indeed.", "fail", {"keyword": "vibrant"})
fx(C, "Truly, vibrant colors felt vibrant indeed.", "pass", {"keyword": "vibrant"}, grader="F-38",
   note="a comma after the first word; the grader counts ',' as the second word")
fx(C, 'A vibrant day felt vibrant "indeed."', "pass", {"keyword": "vibrant"}, grader="F-38",
   note="a closing quote after the final period")
