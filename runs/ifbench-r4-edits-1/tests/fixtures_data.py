"""Labeled fixtures for the 58 IFBench checks.

Labels come from audit/CONTRACTS.md alone; they were written before the checker
code (case/grader/IFBench/instructions*.py) was read. Each fixture:

    check     instruction id
    key       dataset row whose kwargs and prompt the fixture uses
    kw        kwargs overrides (optional)
    response  the graded text
    label     "pass" or "fail" under the contract's proposed readings
    dec       decision entries the label depends on ([] = the contract is
              unambiguous for this input, so a wrong verdict is a finding)
    note      what the fixture probes

The fixture id is "<check>#<sha256(response)[:8]>" (stable across edits of
other fixtures).
"""
import hashlib

FIX = []


def F(check, key, response, label, dec=(), note="", kw=None):
    FIX.append(dict(check=check, key=str(key), response=response, label=label,
                    dec=list(dec), note=note, kw=kw or {}))


# ---------------------------------------------------------------- count
C = "count:conjunctions"  # key 9: N=4
F(C, 9, "I came early and stayed late, but the doors were closed, so I waited, yet nobody arrived.", "pass", note="and but so yet = 4")
F(C, 9, "I came early and stayed late and then left.", "fail", note="1 distinct")
F(C, 9, "I came early and stayed late, but nobody came, so I left.", "fail", note="near miss: 3 distinct")
F(C, 9, "And I came. But nobody came. So I left. Yet I returned.", "pass", note="sentence-initial capitals")
F(C, 9, "Tea or coffee, cheap but good, and fine, yet warm.", "pass", note="punctuation attached: or but and yet")
F(C, 9, "For example, so many people came and stayed, but left.", "pass", dec=["D-conj-role"], note="for/so used as preposition/adverb count by form")

C = "count:keywords_multiple"  # key 1: meridian gossamer eclipse threshold cascade
_kwm = ("The meridian glowed. Gossamer threads, gossamer light. An eclipse, an eclipse, an eclipse. "
        "Threshold one, threshold two, threshold three, threshold four, threshold five. "
        "Cascade cascade cascade cascade cascade cascade cascade.")
F(C, 1, _kwm, "pass", note="exact 1,2,3,5,7")
F(C, 1, _kwm.replace("Cascade cascade", "Cascade", 1), "fail", note="cascade 6")
F(C, 1, _kwm + " One more cascade.", "fail", dec=["D-count-exact"], note="cascade 8 (over)")
F(C, 1, _kwm + " Eclipses happen.", "pass", dec=["D-keyword-match"], note="plural eclipses is not the keyword")
F(C, 1, _kwm.replace("The meridian", "MERIDIAN"), "pass", note="upper-case keyword")
F(C, 1, "meridian", "fail", note="only one keyword present")

C = "count:numbers"  # key 17: N=2
F(C, 17, "Between 1990 and 2005 the town grew.", "pass", note="2 numbers")
F(C, 17, "In 1990, 2005 and 2010 it grew.", "fail", note="3 numbers")
F(C, 17, "It grew in 1990.", "fail", note="1 number")
F(C, 17, "The rate rose from 3.5 to 4.25 percent.", "pass", dec=["D-number"], note="decimals are one number each")
F(C, 17, "About 1,000 people and 25 dogs came.", "pass", dec=["D-number"], note="thousands separator")
F(C, 17, "Two cats, 3 dogs and 4 birds.", "pass", dec=["D-number"], note="number words do not count")
F(C, 17, "Hardship can help. Studies from 2010 and 2015 agree.", "pass", note="plain prose 2 numbers")

C = "count:person_names"  # key 27: N=3
F(C, 27, "Emma, Liam and Sophia met at noon.", "pass", note="3 names")
F(C, 27, "Emma and Liam met at noon.", "fail", note="2 names")
F(C, 27, "Emma met Emma and Liam.", "fail", note="2 distinct")
F(C, 27, "With grace, Emma and Liam left.", "fail", dec=["D-name-case"], note="lower-case grace is not a name")
F(C, 27, "Emma's dog met Liam's cat and Sophia's bird.", "pass", note="possessives")
F(C, 27, "John, Emma and Liam met.", "fail", note="John not in list")

C = "count:pronouns"  # key 33: N=5
F(C, 33, "I told her that we would meet them at my house.", "pass", note="I her we them my = 5")
F(C, 33, "The cat sat on the mat.", "fail", note="0")
F(C, 33, "I saw her. We met them. This is that.", "fail", dec=["D-pronoun-set"], note="4 personal + demonstratives")
F(C, 33, "She said he and they and we and you agreed.", "pass", note="5 personal")
F(C, 33, "I, me, myself: we know it.", "pass", note="punctuation attached, 5")

C = "count:punctuation"  # key 39
_punct_all = 'Wait?! Really... yes; no: maybe, "it\'s" fine — truly (well) [sic] a well-known fact. Is it? Wow!'
F(C, 39, _punct_all, "pass", note="all 14 marks + ?!")
F(C, 39, "Hello, world.", "fail", note="few marks")
F(C, 39, _punct_all.replace(";", ","), "fail", note="near miss: no semicolon (explicitly required)")
F(C, 39, _punct_all.replace("?!", "?"), "fail", note="near miss: no interrobang (explicitly required)")
F(C, 39, _punct_all.replace("[sic]", "sic"), "fail", dec=["D-punct-set"], note="no square brackets")
F(C, 39, _punct_all.replace("?!", "‽"), "pass", dec=["D-punct-set"], note="interrobang as U+203D")
F(C, 39, _punct_all.replace("—", "--"), "pass", dec=["D-punct-set"], note="dash as --")
F(C, 39, _punct_all.replace('"it\'s"', "“it’s”"), "pass", dec=["D-punct-set"], note="typographic quotes and apostrophe")

C = "count:unique_word_count"  # key 24: N=36
_w36 = ("apple banana cherry delta echo forest garden harbor island jungle kettle lemon meadow "
        "nickel orange pepper quartz river silver tunnel umbrella valley willow yellow zebra "
        "anchor bridge candle desert engine falcon glacier hammer igloo jacket kitten").split()
assert len(set(_w36)) == 36
F(C, 24, " ".join(_w36) + ".", "pass", note="36 distinct")
F(C, 24, " ".join(_w36[:35]) + ".", "fail", note="35 distinct")
F(C, 24, " ".join(_w36[:35]) + " " + _w36[0].capitalize() + ".", "fail", dec=["D-unique-case"], note="Apple/apple same word")
F(C, 24, ", ".join(_w36[:35]) + ", " + _w36[0] + ".", "fail", dec=["D-word"], note="apple, and apple same word")
F(C, 24, " ".join(_w36[:35]) + " - " + "* " + ".", "fail", dec=["D-word"], note="markup tokens are not words")

C = "count:word_count_range"  # key 42: 57..61
_w = ("alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa "
      "quebec romeo sierra tango uniform victor whiskey xray yankee zulu").split()


def _words(n):
    return " ".join((_w * 5)[:n]) + "."


F(C, 42, _words(59), "pass", note="59 words")
F(C, 42, _words(40), "fail", note="40 words")
F(C, 42, _words(57), "pass", dec=["D-between"], note="lower bound")
F(C, 42, _words(61), "pass", dec=["D-between"], note="upper bound")
F(C, 42, _words(62), "fail", note="62 words")
F(C, 42, _words(56), "fail", note="56 words")
F(C, 42, _words(56)[:-1] + " - - .", "fail", dec=["D-word"], note="56 words + standalone dashes")
F(C, 42, " ".join((_w * 5)[:57]).replace("alpha", "well-known", 1) + ".", "pass", note="57 words with one hyphenated (57 or 58 under any reading)")

C = "count:words_japanese"  # key 47: N=5
F(C, 47, "This is a nice 日本 day for all of 学校 us.", "pass", note="words 5 and 10 Japanese")
F(C, 47, "This is a nice sunny day for all of the class.", "fail", note="no Japanese")
F(C, 47, "This is a nice 日本 day for all of the class.", "fail", note="10th word English")
F(C, 47, "This is a nice 日本, day for all of 学校.", "pass", dec=["D-word"], note="punctuation attached to Japanese word")
F(C, 47, "This is a nice ひらがな day for all of カタカナ us.", "pass", note="kana words")
F(C, 47, "Hi there.", "pass", dec=["D-vacuous"], note="fewer than N words")
F(C, 47, "This is a nice nihongo day for all of gakkou us.", "fail", dec=["D-japanese-script"], note="romaji")

# ---------------------------------------------------------------- custom
C = "custom:character_reverse"  # key 273
F(C, 273, ".elgae dlab eht si SU eht fo lobmys lanoitan ehT", "pass", note="letter reversal")
F(C, 273, "The national symbol of the US is the bald eagle.", "fail", note="forward")
F(C, 273, "eagle. bald the is US the of symbol national The", "fail", note="word reversal")
F(C, 273, ".elgae dlab eht si SU eht fo lobmys lanoitan ehT\n\n(The national symbol of the US is the bald eagle.)", "fail", dec=["D-reverse-extra"], note="reversed + forward copy")
F(C, 273, ".tac a si tI", "fail", dec=["D-reverse-answer"], note="reversed non-answer")
F(C, 273, "Elgae dlab eht si su eht fo lobmys lanoitan eht.", "pass", dec=["D-reverse-case"], note="re-capitalized reversal")

C = "custom:word_reverse"  # key 283
F(C, 283, "eagle. bald the is US the of symbol national The", "pass", note="word reversal")
F(C, 283, "Eagle bald the is US the of symbol national the.", "pass", dec=["D-reverse-case"], note="re-capitalized, period moved")
F(C, 283, "The national symbol of the US is the bald eagle.", "fail", note="forward")
F(C, 283, ".elgae dlab eht si SU eht fo lobmys lanoitan ehT", "fail", note="letter reversal")
F(C, 283, "eagle bald the is symbol national The\n\nThe bald eagle is the national symbol.", "fail", dec=["D-reverse-extra"], note="reversal + forward")

C = "custom:csv_city"  # key 274
_hdr = "ID,Country,City,Year,Count"
_rows = ["1,France,Paris,2020,150", "2,Japan,Tokyo,2021,230", "3,Brazil,Rio,2019,120", "4,Kenya,Nairobi,2022,80",
         "5,Canada,Toronto,2018,95", "6,India,Delhi,2020,310", "7,Spain,Madrid,2021,140", "8,Peru,Lima,2017,60"]
F(C, 274, "\n".join([_hdr] + _rows[:7]), "pass", note="header + 7 rows")
F(C, 274, "Here is the data:\n```csv\n" + "\n".join([_hdr] + _rows[:7]) + "\n```", "pass", dec=["D-csv-wrapper"], note="fenced with intro")
F(C, 274, "\n".join([_hdr] + _rows[:6]), "fail", dec=["D-csv-rows"], note="header + 6 rows")
F(C, 274, "\n".join([_hdr] + _rows[:8]), "fail", note="8 rows")
F(C, 274, "\n".join([_hdr.replace(",", ";")] + [r.replace(",", ";") for r in _rows[:7]]), "fail", note="semicolon delimited")
F(C, 274, "\n".join([_hdr] + _rows[:6] + ["7,Spain,Madrid,2021"]), "fail", note="a row with 4 fields")
F(C, 274, "\n".join(['"ID","Country","City","Year","Count"'] + _rows[:7]), "pass", note="quoted header fields")
F(C, 274, "\n".join(["ID,Country,City,Year"] + [r.rsplit(",", 1)[0] for r in _rows[:7]]), "fail", note="missing Count column")

C = "custom:csv_quotes"  # key 275
_qh = '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"'
_qr = ['"S1"\t"Math"\t"A"\t"Fall"\t"95"', '"S2"\t"Art"\t"B"\t"Spring"\t"85"', '"S3"\t"Biology"\t"C"\t"Fall"\t"75"', '"S4"\t"Music"\t"A"\t"Fall"\t"91"']
F(C, 275, "\n".join([_qh] + _qr[:3]), "pass", note="tab, quoted, 3 rows")
F(C, 275, "\n".join([_qh.replace("\t", ",")] + [r.replace("\t", ",") for r in _qr[:3]]), "fail", note="comma delimited")
F(C, 275, "\n".join([_qh.replace('"', "")] + _qr[:3]), "fail", dec=["D-csv-header-quoted"], note="header unquoted")
F(C, 275, "\n".join([_qh] + _qr[:2] + ['"S3"\t"Biology"\tC\t"Fall"\t"75"']), "fail", note="one data field unquoted")
F(C, 275, "\n".join([_qh] + _qr[:4]), "fail", note="4 rows")
F(C, 275, "\n".join([_qh] + _qr[:2]), "fail", note="2 rows")

C = "custom:csv_special_character"  # key 276
_sh = "ProductID,Category,Brand,Price,Stock"
_sr = [f"P{i:02d},Tools,Acme,{10 + i}.99,{i * 3}" for i in range(1, 16)]
_sp = list(_sr)
_sp[4] = 'P05,Tools,"Smith & Sons",14.99,15'
F(C, 276, "\n".join([_sh] + _sp[:14]), "pass", note="14 rows, one quoted field with &")
F(C, 276, "\n".join([_sh] + _sr[:14]), "fail", note="no quoted field")
_sq = list(_sr)
_sq[4] = 'P05,Tools,"Acme",14.99,15'
F(C, 276, "\n".join([_sh] + _sq[:14]), "fail", note="quoted field without special character")
F(C, 276, "\n".join([_sh] + _sp[:13]), "fail", note="13 rows")
F(C, 276, "\n".join([_sh] + _sp[:15]), "fail", note="15 rows")
_su = list(_sr)
_su[4] = "P05,Tools,Smith & Sons,14.99,15"
F(C, 276, "\n".join([_sh] + _su[:14]), "fail", note="special character but unquoted")

C = "custom:date_format_list"  # key 277
F(C, 277, "1796-04-12, 1796-05-10, 1798-07-21, 1805-12-02", "pass", note="ISO dates, commas")
F(C, 277, "1796-04-12,1796-05-10,1798-07-21,1805-12-02", "pass", note="no spaces")
F(C, 277, "April 12, 1796; May 10, 1796", "fail", note="wrong format")
F(C, 277, "Here are the dates: 1796-04-12, 1796-05-10, 1805-12-02", "fail", dec=["D-date-extra"], note="intro text")
F(C, 277, "1796-04-12, 10-05-1796, 1805-12-02", "fail", note="one DD-MM-YYYY")
F(C, 277, "1796-04-12, 1805-13-02", "fail", note="invalid month")
F(C, 277, "1796-04-12\n1796-05-10\n1805-12-02", "fail", note="newline separated, no commas")
F(C, 277, "1796-04-12 (Montenotte), 1805-12-02 (Austerlitz)", "fail", dec=["D-date-extra"], note="battle names")

C = "custom:european_capitals_sort"  # key 278
_caps = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
         "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
         "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
F(C, 278, ", ".join(_caps), "pass", note="contract list incl. Kyiv (50.45N); any reading that keeps Moscow, as the grader key does, needs Kyiv")
_sw = list(_caps)
_sw[1], _sw[2] = _sw[2], _sw[1]
F(C, 278, ", ".join(_sw), "fail", note="Oslo before Helsinki")
F(C, 278, ", ".join(_caps + ["Rome"]), "fail", note="adds Rome (41.9N)")
F(C, 278, ", ".join(f"{c} (X)" if i == 0 else c for i, c in enumerate(_caps)).replace("(X)", "(Iceland)"), "fail", note="country name")
F(C, 278, ", ".join(c for c in _caps if c != "Moscow"), "fail", dec=["D-capitals-set", "D-capitals-complete"], note="Moscow missing")
F(C, 278, ", ".join(sorted(_caps)), "fail", note="alphabetical order")
F(C, 278, "Paris, Rome, Madrid", "fail", note="wrong set and order")

C = "custom:mcq_count_length"  # key 279
_opts = "A) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock"
_q = ["Question 1: Who painted Guernica?",
      "Question 2: Which artist led the Pop Art movement?",
      "Question 3: Which painter is best known for drip paintings made on the floor?",
      "Question 4: Which Spanish surrealist painted melting clocks in the famous 1931 work The Persistence of Memory?"]
F(C, 279, "\n\n".join(q + "\n" + _opts for q in _q), "pass", note="4 questions, 5 options, longer each time (under every length measure)")
F(C, 279, "\n\n".join(q + "\n" + _opts for q in _q[:3]), "fail", note="3 questions")
F(C, 279, "\n\n".join(q + "\n" + _opts for q in [_q[0], _q[2], _q[1], _q[3]]), "fail", note="not progressively longer")
F(C, 279, "\n\n".join(q + "\n" + (_opts.rsplit("\n", 1)[0] if i == 2 else _opts) for i, q in enumerate(_q)), "fail", note="one question with 4 options")
F(C, 279, "\n\n".join(q.replace("Question", "Q") + "\n" + _opts for q in _q), "fail", note="label Q instead of Question")
F(C, 279, "\n\n".join(q + "\n" + _opts for q in _q) + "\n\nExplanation: these test core knowledge.", "fail", note="explanation added")

C = "custom:multiples"  # key 280
F(C, 280, "14, 21, 28, 35, 42, 49", "pass", note="exact")
F(C, 280, "14\n21\n28\n35\n42\n49", "pass", note="newline separated")
F(C, 280, "10, 14, 21, 28, 35, 42, 49", "fail", note="extra 10")
F(C, 280, "14, 21, 28, 35, 42", "fail", note="missing 49")
F(C, 280, "7, 14, 21, 28, 35, 42, 49", "fail", note="extra 7")
F(C, 280, "Multiples: 14, 21, 28, 35, 42, 49.", "pass", dec=["D-multiples-extra"], note="word prefix")
F(C, 280, "Here are the multiples of 7 between 10 and 50: 14, 21, 28, 35, 42, 49", "fail", dec=["D-multiples-extra"], note="intro with range numbers")
F(C, 280, "14, 28, 21, 35, 42, 49", "fail", note="out of order")
F(C, 280, "14, 21, 28, 35, 42, 49, 56", "fail", note="extra 56")

C = "custom:reverse_newline"  # key 281
_af = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon",
       "Central African Republic", "Chad", "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt",
       "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau",
       "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania",
       "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Republic of the Congo", "Rwanda",
       "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan",
       "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"]
assert len(_af) == 54 and _af == sorted(_af)
_rev = list(reversed(_af))
F(C, 281, "\n".join(_rev), "pass", note="54 in reverse order")
F(C, 281, "\n".join(_af), "fail", note="forward order")
_rs = list(_rev)
_rs[0], _rs[1] = _rs[1], _rs[0]
F(C, 281, "\n".join(_rs), "fail", note="Zambia before Zimbabwe")
F(C, 281, "\n".join(c for c in _rev if c != "Kenya"), "fail", dec=["D-africa-complete"], note="Kenya missing")
F(C, 281, "Here are the countries of Africa in reverse alphabetical order:\n" + "\n".join(_rev), "fail", dec=["D-list-intro"], note="intro line")
F(C, 281, "\n".join(f"{i}. {c}" for i, c in enumerate(_rev, 1)), "pass", note="numbered lines")
F(C, 281, ", ".join(_rev), "fail", note="one line, comma separated")
F(C, 281, "\n".join(_rev[:3] + ["France"] + _rev[3:]), "fail", note="non-African country inserted")

C = "custom:sentence_alphabet"  # key 282
_abc = ["Alice awoke early.", "Birds sang outside.", "Coffee brewed slowly.", "Dogs barked twice.", "Every neighbor waved.",
        "Fog covered town.", "Grandma baked bread.", "Her kitchen smelled sweet.", "Its warmth spread.", "Joy filled hearts.",
        "Kids ran around.", "Laughter echoed loudly.", "Mothers chatted happily.", "Nobody felt lonely.", "Old friends arrived.",
        "Puppies played nearby.", "Quiet returned later.", "Rain began falling.", "Soon everyone left.", "The house grew still.",
        "Under blankets, Alice read.", "Very late, she slept.", "Wind howled softly.", "Xylophones chimed in dreams.",
        "Yesterday faded away.", "Zebras danced in her sleep."]
assert len(_abc) == 26 and all(s[0] == chr(65 + i) for i, s in enumerate(_abc))
F(C, 282, " ".join(_abc), "pass", note="26 sentences A..Z")
F(C, 282, " ".join(_abc[:25]), "fail", note="25 sentences")
_abs = list(_abc)
_abs[3], _abs[4] = _abs[4], _abs[3]
F(C, 282, " ".join(_abs), "fail", note="D and E swapped")
F(C, 282, "The Alphabet Day\n" + " ".join(_abc), "fail", dec=["D-sentence"], note="title line counts as sentence")
F(C, 282, " ".join(_abc[:5] + ["fog covered town."] + _abc[6:]), "pass", note="lower-case initial")
F(C, 282, " ".join(_abc + ["And then it ended."]), "fail", note="27 sentences")

# ---------------------------------------------------------------- format
C = "format:emoji"  # key 70
F(C, 70, "Light is fast \U0001F680. Nothing beats it \U0001F60A.", "pass", note="emoji before period")
F(C, 70, "Light is fast. \U0001F680 Nothing beats it. \U0001F60A", "pass", dec=["D-emoji-position"], note="emoji after period")
F(C, 70, "Light is fast. Nothing beats it.", "fail", note="no emoji")
F(C, 70, "Light is fast. Nothing beats it \U0001F60A.", "fail", note="first sentence lacks emoji")
F(C, 70, "Relativity\nLight is fast \U0001F680.", "fail", dec=["D-sentence"], note="heading without emoji")
F(C, 70, "Science is fun ❤️. Scientists rock \U0001F469‍\U0001F52C.", "pass", note="emoji with VS16 and ZWJ")
F(C, 70, "Light is fast \U0001F680! Is it? \U0001F914", "pass", dec=["D-emoji-position"], note="! and ? sentences")
F(C, 70, "Light is fast \U0001F680. Nothing beats it.", "fail", note="last sentence lacks emoji")

C = "format:line_indent"  # key 74
F(C, 74, "Step one\n  Step two\n    Step three\n      Step four", "pass", note="stairs")
F(C, 74, "Step one\nStep two\nStep three", "fail", note="no indent")
F(C, 74, "Step one\n  Step two\n  Step three", "fail", note="equal indent")
F(C, 74, "Step one\n  Step two\n    Step three\n  Step four", "fail", note="decrease")
F(C, 74, "Step one\n\n  Step two\n\n    Step three", "pass", note="blank lines ignored")
F(C, 74, "Step one\n Step two\n     Step three", "pass", dec=["D-indent-step"], note="uneven increase")
F(C, 74, "Step one", "fail", dec=["D-indent-min"], note="single line")
F(C, 74, "Step one\n\tStep two\n\t\tStep three", "pass", note="tabs")

C = "format:list"  # key 83: "!?!?"
F(C, 83, "!?!? Preludes are short pieces.\n!?!? Caprichos are lively.\n!?!? Romances are lyrical.", "pass", note="prefix items")
F(C, 83, "Preludes are short !?!? Caprichos are lively !?!? Romances are lyrical", "pass", dec=["D-list-sep"], note="inline separator")
F(C, 83, "* Preludes are short pieces.\n* Caprichos are lively.\n* Romances are lyrical.", "fail", note="ordinary bullets")
F(C, 83, "!?!? Preludes are short pieces.", "fail", note="one item")
F(C, 83, "!?!? Preludes are short.\n* Caprichos are lively.\n!?!? Romances are lyrical.", "fail", note="one item uses *")
F(C, 83, "Definitions:\n!?!? Preludes are short.\n!?!? Caprichos are lively.", "pass", dec=["D-list-intro"], note="intro line")
F(C, 83, "Preludes are short pieces, caprichos are lively, and romances are lyrical.", "fail", note="no separator")
F(C, 86, "- Entanglement links particles.\n- It does not explain parallel worlds.", "pass", note="sep '-'")
F(C, 86, "* Entanglement links particles.\n* It does not explain parallel worlds.", "fail", note="sep '-' but * used")
F(C, 82, "SEPARATOR Save nothing.\nSEPARATOR Consume 10,000 each year.", "pass", note="sep SEPARATOR")

C = "format:newline"  # key 90
F(C, 90, "Alpha\nand\nOmega\nremake.", "pass", note="one word per line")
F(C, 90, "Alpha and Omega remake.", "fail", note="one line")
F(C, 90, "Alpha\nand Omega\nremake.", "fail", note="one line with two words")
F(C, 90, "well-known\nfilm", "pass", dec=["D-word"], note="hyphenated word")
F(C, 90, "Alpha\n-\nOmega", "pass", dec=["D-word"], note="line with only a dash")
F(C, 90, "Alpha\n\nOmega", "pass", note="blank line between")
F(C, 90, "**Alpha**\nOmega", "pass", dec=["D-word"], note="markup around word")
F(C, 90, "Alpha,\nOmega.", "pass", note="punctuation attached")

C = "format:no_bullets_bullets"  # key 98
F(C, 98, "Deism is weak. It ignores revelation.\n* Point one\n* Point two", "pass", note="2 sentences then 2 bullets")
F(C, 98, "* Point one\n* Point two", "fail", note="bullets only")
F(C, 98, "Deism is weak.\n* Point one\n* Point two", "fail", note="one sentence")
F(C, 98, "Deism is weak. It ignores revelation.\n* Point one", "fail", note="one bullet")
F(C, 98, "Deism is weak! It ignores revelation!\n* Point one\n* Point two", "fail", note="sentences end in !")
F(C, 98, "Deism is weak. It ignores revelation.\n- Point one\n- Point two", "fail", dec=["D-bullet-marker"], note="- bullets")
F(C, 98, "* Point one\n* Point two\nDeism is weak. It ignores revelation.", "fail", note="bullets before sentences")
F(C, 98, "Deism is weak. It ignores revelation.\n\n* Point one\n* Point two\n\nIn sum, deism fails.", "pass", note="content after bullets")

C = "format:no_whitespace"  # key 298
F(C, 298, "Piousegoistsmeansselfish.", "pass", note="no whitespace")
F(C, 298, "Pious egoists.", "fail", note="space")
F(C, 298, "Pious egoists", "fail", dec=["D-whitespace-set"], note="no-break space")
F(C, 298, "Pious\tegoists", "fail", note="tab")
F(C, 298, "Pious\negoists", "fail", note="newline")
F(C, 298, "Piousegoists\n", "pass", dec=["D-strip-ends"], note="trailing newline")
F(C, 298, "Pious　egoists", "fail", dec=["D-whitespace-set"], note="ideographic space")

C = "format:options"
F(C, 100, "Yes", "pass", note="yes")
F(C, 100, "yes.", "pass", note="lower-case with period")
F(C, 100, "Maybe", "pass", note="maybe")
F(C, 100, "No", "pass", note="no")
F(C, 100, "**Maybe**", "pass", note="bold")
F(C, 100, "Yes, because games teach empathy.", "fail", note="explanation")
F(C, 100, "Yes/No", "fail", note="two options")
F(C, 100, "Absolutely", "fail", note="not an option")
F(C, 100, "The answer is maybe.", "fail", note="extra words")
F(C, 101, "I know", "pass", note="I know")
F(C, 101, "I don't know", "pass", note="I don't know")
F(C, 101, "I don't know.", "pass", note="with period")
F(C, 101, "I know that this is right.", "fail", note="extra words")
F(C, 101, "I don’t know", "pass", note="typographic apostrophe")
F(C, 102, "c)", "pass", note="c)")
F(C, 102, "C)", "pass", dec=["D-options-text"], note="upper-case (v4: letter form is part of D-options-text)")
F(C, 102, "c", "pass", dec=["D-options-text"], note="letter without paren")
F(C, 102, "c) Inadmissible because D has not put his character for peacefulness into issue.", "pass", dec=["D-options-text"], note="label + option text")
F(C, 102, "The answer is c).", "fail", note="extra words")
F(C, 102, "c) because the prior act shows propensity.", "fail", note="label + explanation")

C = "format:output_template"  # key 292
F(C, 292, "My Answer: Suffering at cosmic scale.\nMy Conclusion: It matters.\nFuture Outlook: Research grows.", "pass", note="plain template")
F(C, 292, "My Answer: Suffering at cosmic scale. My Conclusion: It matters. Future Outlook: Research grows.", "pass", note="one line")
F(C, 292, "**My Answer:** X is bad.\n**My Conclusion:** Y.\n**Future Outlook:** Z.", "pass", dec=["D-template-markup"], note="bold labels")
F(C, 292, "Astronomical suffering is suffering at cosmic scale.", "fail", note="free text")
F(C, 292, "My Answer: X.\nMy Conclusion: Y.", "fail", note="missing Future Outlook")
F(C, 292, "Sure, here it is.\nMy Answer: X.\nMy Conclusion: Y.\nFuture Outlook: Z.", "fail", note="text before template")
F(C, 292, "My Conclusion: Y.\nMy Answer: X.\nFuture Outlook: Z.", "fail", note="order swapped")
F(C, 292, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", "fail", note="literal placeholders")
F(C, 292, "My Answer: X.\nMy Conclusion: Y.\nFuture Outlook: Z.\nMy Answer: W.", "fail", note="label repeated")

C = "format:parentheses"  # key 110
F(C, 110, "AI (study [of {minds (and [machines])}]) grows.", "pass", note="depth 5 mixed")
F(C, 110, "((((( deep )))))", "pass", dec=["D-paren-types"], note="depth 5 parentheses only")
F(C, 110, "AI (study [of minds]) grows.", "fail", note="depth 2")
F(C, 110, "AI (a [b {c (d)}]) grows.", "fail", note="depth 4")
F(C, 110, "AI ( [ { ( [ x", "fail", note="unclosed")
F(C, 110, "(a) [b] {c} (d) [e]", "fail", note="five separate pairs")
F(C, 110, "x ( a ] b ( c ) d", "fail", note="mismatched")

C = "format:quote_unquote"  # key 116
F(C, 116, 'He said "neurons connect" which means links exist.', "pass", note="quote then explanation")
F(C, 116, 'He said "neurons connect" "all nodes"', "fail", note="quote followed by quote/end")
F(C, 116, 'The claim is "false"', "fail", note="quote at end")
F(C, 116, 'The claim is "false".', "fail", note="quote followed only by period")
F(C, 116, "No quotes here.", "pass", dec=["D-vacuous"], note="no quoted phrase")
F(C, 116, "“Each neuron connects” means dense layers.", "pass", note="typographic quotes")
F(C, 116, "It's the network's design, which isn't universal.", "pass", dec=["D-vacuous"], note="apostrophes only")
F(C, 116, 'First "dense" means full, and "sparse" means few.', "pass", note="two quotes each explained")

C = "format:quotes"  # key 120
F(C, 120, 'He said, "She told me, \'They whispered, "Wait," yesterday,\' today," and left.', "pass", note="double-single-double")
F(C, 120, "“She said ‘He wrote “yes” there’ again”", "pass", note="typographic 3 levels")
F(C, 120, "No quotes at all.", "fail", note="none")
F(C, 120, '"She said \'hi\' then"', "fail", note="depth 2")
F(C, 120, "“a “b “c” b” a”", "fail", note="3 levels, no alternation")
F(C, 120, "'She said \"He wrote 'yes' there\" again'", "pass", dec=["D-quotes-start"], note="single outermost")

C = "format:sub-bullets"  # key 132
F(C, 132, "* Memorization\n  - Copying training data\n* Why care\n  - Privacy risk", "pass", note="indented subs")
F(C, 132, "* Memorization\n- Copying training data\n* Why care\n- Privacy risk", "pass", dec=["D-subbullet-indent"], note="unindented subs")
F(C, 132, "* Memorization\n* Why care", "fail", note="no subs")
F(C, 132, "* Memorization\n  - Copying training data\n* Why care", "fail", note="second bullet lacks sub")
F(C, 132, "**Overview**\n* Memorization\n  - Copying\n* Why care\n  - Privacy", "pass", note="bold heading is not a bullet")
F(C, 132, "- Memorization\n  * Copying training data", "fail", note="markers swapped")
F(C, 132, "* Memorization\n  - Copying training data", "pass", dec=["D-plural"], note="one bullet")
F(C, 132, "Memorization is copying.", "fail", note="no bullets")

C = "format:thesis"  # key 142
F(C, 142, "<i>The party is conservative.</i> It favors tradition.\n\n<i>Its economics are liberal.</i> It cuts taxes.", "pass", note="paragraph sections")
F(C, 142, "## Ideology\n<i>The party is conservative.</i> Text.\n\n## Economics\n<i>It is pro-market.</i> Text.", "pass", note="headed sections")
F(C, 142, "The party is conservative. It favors tradition.", "fail", note="no italics")
F(C, 142, "*The party is conservative.* It favors tradition.", "fail", note="markdown italics")
F(C, 142, "<i>The party is conservative.</i> It favors tradition.\n\nIts economics are liberal. It cuts taxes.", "fail", dec=["D-section"], note="second paragraph lacks thesis")
F(C, 142, "<em>The party is conservative.</em> It favors tradition.", "pass", dec=["D-italic-tag"], note="<em>")
F(C, 142, "It favors tradition, <i>the party is conservative</i>.", "fail", note="italics not at start")

C = "format:title_case"  # key 291
F(C, 291, "The Liberal Democratic Party Of Japan Is Conservative.", "pass", note="every word capitalized")
F(C, 291, "The Party of Japan Is Conservative and Pro-Business.", "pass", dec=["D-title-minor"], note="minor words lower-case")
F(C, 291, "The party is conservative.", "fail", note="sentence case")
F(C, 291, "The Liberal Democratic party Of Japan.", "fail", note="one major word lower-case")
F(C, 291, "# The Party\n\n* Strong Economy\n* Close Ties With America", "pass", dec=["D-title-minor"], note="markdown, 'With' capitalized")
F(C, 291, "The Party Supports 3 Key Policies.", "pass", note="number token ignored")

# ---------------------------------------------------------------- ratio
C = "ratio:overlap"  # key 152: 11%, reference 'Describe eternal asteroid made of nuclearly locked astatines'
F(C, 152, "An asteroid made of astatine would decay within hours, scientists say.", "pass", dec=["D-overlap-def"], note="1/9 response trigrams = 11.1%")
F(C, 152, "Astatine is too radioactive to form any stable body in space.", "fail", note="0% overlap")
F(C, 152, "Describe eternal asteroid made of nuclearly locked astatines", "fail", note="100% overlap (copy)")
F(C, 152, "An asteroid made of astatine would decay quickly because astatine is highly radioactive and short lived.", "fail", dec=["D-overlap-def"], note="1/14 = 7.1%")

C = "ratio:sentence_balance"  # key 155
F(C, 155, "Copernicus had critics. Who were they? Many objected loudly!", "pass", note="1:1:1")
F(C, 155, "Copernicus had critics. Who were they? Many objected loudly! Luther mocked him.", "pass", dec=["D-balanced"], note="2:1:1")
F(C, 155, "Copernicus had critics. Many objected. Some agreed.", "fail", note="3:0:0")
F(C, 155, "Copernicus had critics. Who were they? Luther was one.", "fail", note="no exclamatory")
F(C, 155, "A was here. B was here. C was here. Who? Wow!", "fail", dec=["D-balanced"], note="3:1:1")
F(C, 155, "Copernicus had critics. Luther mocked. Who were they? Why? Wow! Amazing!", "pass", note="2:2:2")

C = "ratio:sentence_type"  # key 163
F(C, 163, "Paraphrasing changes form. It keeps meaning. What is it called?", "pass", note="2:1")
F(C, 163, "It is paraphrasing.", "fail", note="1:0")
F(C, 163, "It changes form. It keeps meaning. It is common. What is it called?", "fail", dec=["D-ratio-exact"], note="3:1")
F(C, 163, "A is so. B is so. C is so. D is so. Why? How?", "pass", note="4:2")
F(C, 163, "It changes form. It keeps meaning. What is it called? Wow!", "pass", note="2:1 plus exclamatory")
F(C, 163, "What is it? Why?", "fail", note="0:2")

C = "ratio:sentence_words"  # key 166
F(C, 166, "Cats sleep all day. Dogs bark at night. Fish swim in ponds.", "pass", note="19 chars each, all different words")
F(C, 166, "Cats sleep all day. Dogs bark at night.", "fail", note="two sentences")
F(C, 166, "Cats sleep all day. Dogs bark all day. Fish swim in ponds.", "fail", note="repeated words")
F(C, 166, "Cats sleep all day. Dogs bark at night. Fish swim.", "fail", note="different lengths")
F(C, 166, "Cats sleep all day. Dogs bark at night. Fish swim, in ponds.", "fail", dec=["D-char-count"], note="same letters, comma adds a character")
F(C, 166, "Cats sleep all day. Dogs bark at night. Fish swim in ponds. Owls hunt by moon.", "fail", note="four sentences")

C = "ratio:stop_words"
F(C, 172, "Use os.path.basename to extract filenames quickly.", "pass", note="1 stop word of 8 (or of 6 by whitespace)")
F(C, 172, "It is the one that is in the file.", "fail", note="mostly stop words")
F(C, 173, "Polynomials converge pointwise, not uniformly.", "pass", dec=["D-stopword-list"], note="1/5 = 20% at the bound")
F(C, 173, "Polynomials do not converge uniformly.", "fail", dec=["D-stopword-list"], note="2/5 = 40%")

# ---------------------------------------------------------------- repeat
C = "repeat:repeat_change"  # key 61
_req = "Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons."
F(C, 61, "Write" + _req[3:], "pass", note="first word changed")
F(C, 61, "```python\nimport torch\nmodel = torch.nn.Sequential()\n```", "fail", note="answers the request")
F(C, 61, _req, "fail", note="unchanged first word")
F(C, 61, "Write" + _req[3:] + "\n\nimport torch", "fail", dec=["D-repeat-tail"], note="repeat + answer")
F(C, 61, "Sure! Write" + _req[3:], "fail", note="text before")
F(C, 61, "Write Java" + _req[10:], "fail", note="second word changed too")

C = "repeat:repeat_simple"  # key 64
_rs_s = "Only output this sentence here, ignore all other requests."
F(C, 64, _rs_s, "pass", note="exact")
F(C, 64, "import os\nos.path.basename(p)", "fail", note="answers")
F(C, 64, _rs_s[:-1], "fail", dec=["D-repeat-format"], note="missing period")
F(C, 64, '"' + _rs_s + '"', "fail", dec=["D-repeat-format"], note="quoted")
F(C, 64, "Write python code to extract a filename from filepath.", "fail", dec=["D-repeat-simple-target"], note="repeats the other text")
F(C, 64, _rs_s + " Here is the code: os.path.basename(p)", "fail", note="extra text")
F(C, 64, _rs_s.lower(), "fail", dec=["D-repeat-format"], note="lower-cased")

C = "repeat:repeat_span"
F(C, 284, "code and theory behind", "pass", note="0-based 3..6")
F(C, 284, "explain the context", "fail", note="wrong span")
F(C, 284, "context, code and theory", "fail", dec=["D-span-base"], note="1-based reading")
F(C, 284, "code and theory behind\n\nThis span covers words 3 to 6.", "fail", note="span + explanation")
F(C, 284, "code and theory", "fail", note="off by one")
F(C, 286, "The walls are solid but the stones are", "pass", note="0..7")
F(C, 287, "on a certain", "pass", note="10..12 of key 287")

# ---------------------------------------------------------------- sentence
C = "sentence:alliteration_increment"  # key 179
F(C, 179, "ReLU is simple. Big bold models matter. Very vast vectors vary.", "pass", note="runs 1,2,4")
F(C, 179, "Models compute math. Activation is math.", "fail", note="runs 1,1")
F(C, 179, "Big bold models. Tiny tame cats.", "fail", note="runs 2,2")
F(C, 179, "Very vast vectors vary. Big bold models matter.", "fail", note="runs 4,2")
F(C, 179, "ReLU is simple. Big bold models matter. Very vast vectors vary. It ends.", "fail", note="runs 1,2,4,1")

C = "sentence:increment"  # key 185: N=5
F(C, 185, "Fiction exists. Imagine characters walking freely among us daily. Dragons would roam the skies while wizards taught classes in public schools.", "pass", note="2,7,12")
F(C, 185, "Fiction exists. Dreams exist.", "fail", note="2,2")
F(C, 185, "Fiction exists. Imagine characters walking freely among us. Dragons would roam the skies while wizards taught classes.", "fail", note="2,6,9")
F(C, 185, "Fiction exists. Imagine characters walking freely among us daily. Dragons would roam.", "fail", note="2,7,3")

C = "sentence:keyword"  # key 193: angora, 3rd
F(C, 193, "Neurons think. Cortex helps. An angora rabbit has neurons too.", "pass", note="in sentence 3")
F(C, 193, "Neurons think. Cortex helps. A rabbit has neurons too.", "fail", note="absent")
F(C, 193, "Neurons think. An angora helps. A rabbit has neurons too.", "fail", note="in sentence 2")
F(C, 193, "Neurons think. Cortex helps. Angoras have neurons too.", "fail", dec=["D-keyword-match"], note="plural")
F(C, 193, "Neurons think. Cortex helps. Angora rabbits have neurons too.", "pass", note="capitalized")
F(C, 193, "Dr. Smith studies brains. Cortex helps. An angora rabbit thinks.", "pass", dec=["D-sentence"], note="abbreviation")
F(C, 193, "Overview\nNeurons think. An angora rabbit thinks.", "pass", dec=["D-sentence"], note="heading counts as sentence 1")

# ---------------------------------------------------------------- words
C = "words:alphabet"  # key 202
F(C, 202, "A big computer does everything.", "pass", note="a b c d e")
F(C, 202, "Big computers do every function.", "pass", dec=["D-alphabet-start"], note="starts at b")
F(C, 202, "You zoom around.", "pass", dec=["D-alphabet-start"], note="wraps z to a")
F(C, 202, "Small computers exist.", "fail", note="no sequence")
F(C, 202, "A big computer does tasks.", "fail", note="one break")
F(C, 202, "A big computer 2 does everything.", "pass", dec=["D-word-numbers"], note="number ignored")

C = "words:consonants"  # key 209
F(C, 209, "Strong scaling laws drop.", "pass", note="all clusters")
F(C, 209, "It is a law.", "fail", note="no clusters")
F(C, 209, "Strong scaling is crucial.", "fail", note="'is' lacks a cluster")
F(C, 209, "Gym trends.", "pass", dec=["D-consonant-y"], note="y as consonant")
F(C, 209, "Strong 2024 trends.", "pass", dec=["D-word-numbers"], note="number ignored")

C = "words:keywords_specific_position"  # key 10 with n=2, m=3
_ksp = {"n": 2, "m": 3}
F(C, 10, "Models vary. They often giggle at prompts.", "pass", kw=_ksp, note="sentence 2 word 3")
F(C, 10, "Models vary. They often laugh at prompts.", "fail", kw=_ksp, note="absent")
F(C, 10, "Models vary. They giggle at prompts.", "fail", kw=_ksp, note="word 2")
F(C, 10, "Models often giggle. They vary.", "fail", kw=_ksp, note="sentence 1")
F(C, 10, "Models vary. They often giggle, laughing.", "pass", kw=_ksp, note="comma attached")
F(C, 10, "Models vary. They often Giggle at prompts.", "pass", kw=_ksp, note="capitalized keyword")

C = "words:last_first"  # key 220
F(C, 220, "Saturn has clouds. Clouds can freeze. Freeze points vary.", "pass", note="chain")
F(C, 220, "Saturn has clouds. Rogue planets exist.", "fail", note="broken")
F(C, 220, "Saturn has clouds. Clouds can freeze. Rogue planets exist.", "fail", note="second pair broken")
F(C, 220, "Saturn has clouds. clouds can freeze!", "pass", note="case and punctuation")
F(C, 220, "Saturn has clouds.", "pass", dec=["D-vacuous"], note="single sentence")

C = "words:no_consecutive"  # key 225
F(C, 225, "Honest talks build trust.", "pass", note="h t b t")
F(C, 225, "Constructive conversations create change.", "fail", note="all c")
F(C, 225, "Honest talks build. Bridges form.", "fail", note="across sentence boundary")
F(C, 225, "Honest Talks Trust.", "fail", note="case-insensitive")
F(C, 225, "A constructive dialogue can pave", "pass", note="a c d c p")

C = "words:odd_even_syllables"  # key 231
F(C, 231, "Light travels fast, maybe.", "pass", note="1,2,1,2")
F(C, 231, "Light is fast.", "fail", note="1,1,1")
F(C, 231, "Light travels fast, maybe never.", "fail", note="1,2,1,2,2")
F(C, 231, "Water flows.", "pass", note="2,1")

C = "words:palindrome"  # key 237
_pal = "level radar civic kayak refer rotor madam stats tenet racecar".split()
F(C, 237, "We saw " + ", ".join(_pal) + " today.", "pass", note="10 distinct")
F(C, 237, "A step function is integrable.", "fail", note="none")
F(C, 237, "We saw " + ", ".join(_pal[:9]) + " today.", "fail", note="9")
F(C, 237, "We saw " + ", ".join(["level"] * 10) + " today.", "fail", dec=["D-palindrome-distinct"], note="one palindrome 10 times")
F(C, 237, "noon deed peep toot sees wow pop dad mom bob", "fail", note="all shorter than 5")
F(C, 237, "We saw " + ", ".join(p.capitalize() for p in _pal) + " today.", "pass", note="capitalized")

C = "words:paragraph_last_first"  # key 246
F(C, 246, "Banks lend money, trusting banks\nDeposits stay put as deposits", "pass", note="line paragraphs")
F(C, 246, "Trust keeps reserves working, so trust.\n\nLiquidity matters for liquidity.", "pass", note="blank-line paragraphs with periods")
F(C, 246, "Banks lend money.\nDeposits stay.", "fail", note="none match")
F(C, 246, "Trust keeps reserves working, so trust.\n\nLiquidity matters.", "fail", note="second fails")
F(C, 246, "Trust keeps reserves\nworking, so trust.", "fail", dec=["D-paragraph-newline"], note="newline splits paragraph")
F(C, 246, "**Trust** keeps reserves working, so trust.", "pass", dec=["D-word"], note="markup around first word")

C = "words:prime_lengths"  # key 250
F(C, 250, "It is an organ we use.", "pass", note="2,2,2,5,2,3")
F(C, 250, "This is it.", "fail", note="This=4")
F(C, 250, "A cat is here.", "fail", note="a=1")
F(C, 250, "We don't see it.", "fail", dec=["D-word-length"], note="don't = 4 letters")
F(C, 250, "We see 1000 cells.", "pass", dec=["D-word-numbers"], note="number ignored")

C = "words:repeats"  # key 256: N=3
F(C, 256, "Gordon saw Alyx. Gordon saw Alyx again. Gordon left.", "pass", note="max 3")
F(C, 256, "Alyx Alyx Alyx Alyx Alyx.", "fail", note="5 times")
F(C, 256, "Gordon saw Alyx. Gordon saw Alyx. Gordon left. Gordon stayed.", "fail", dec=["D-repeats-count"], note="4 = N+1")
F(C, 256, "The cat. the dog. THE bird. the end.", "fail", dec=["D-repeats-count"], note="case variants 4")

C = "words:start_verb"  # key 258
F(C, 258, "Explore Galois theory through symmetry.", "pass", note="imperative")
F(C, 258, "Galois theory studies symmetry.", "fail", note="noun first")
F(C, 258, "**Consider** the field extension.", "pass", note="bold verb")
F(C, 258, "# Galois Theory\nConsider the field.", "fail", note="heading first")
F(C, 258, "Picture a field extension.", "pass", dec=["D-verb-context"], note="noun/verb word used as verb")
F(C, 258, "Understanding Galois theory requires groups.", "fail", dec=["D-verb-context"], note="gerund subject")
F(C, 258, "Is Galois theory hard? Yes.", "pass", note="auxiliary verb")

C = "words:vowel"  # key 264
F(C, 264, "Narratives shape minds.", "pass", note="a e i")
F(C, 264, "Our human mind is shaped by stories.", "fail", note="5 vowels")
F(C, 264, "Narratives shape minds and hearts of people.", "fail", note="adds o")
F(C, 264, "Cats eat fish on rugs.", "fail", dec=["D-vowel-scope"], note="per word <=3 types, total 5")
F(C, 264, "Narratives shape minds.\n\nMinds shape narratives.", "fail", dec=["D-vowel-paragraph"], note="two paragraphs")

C = "words:words_position"  # key 16: despite
F(C, 16, "Art despite war grew despite everything.", "pass", note="2nd and 2nd-last")
F(C, 16, "Art grew during war.", "fail", note="absent")
F(C, 16, "Art despite war grew in everything.", "fail", note="2nd-last wrong")
F(C, 16, "Art, despite war, grew despite everything.", "pass", note="commas attached")
F(C, 16, "**Art** despite war grew despite everything.", "pass", dec=["D-word"], note="markup around first word")


# ======================================================================
# Second block: fixtures written AFTER reading the checker code (2026-11-10
# ~22:30 UTC). Labels still come from audit/CONTRACTS.md (v3) alone.
# ======================================================================
F("count:conjunctions", 9, "Tea and cake, and jam. And milk. AND bread.", "fail", note="POST: one conjunction in four spellings")
_kwm2 = ("A door. Bread and bread. Blue, blue, blue. Lamp lamp lamp lamp lamp. "
         "River river river river river river river.")
F("count:keywords_multiple", 2, _kwm2, "pass", note="POST: exact counts")
F("count:keywords_multiple", 2, _kwm2 + " The driver waved.", "pass", note="POST: 'river' inside 'driver' is not the keyword (v3)")
F("count:numbers", 17, "From 1990-2005 the town grew.", "pass", note="POST: a hyphenated range holds two numbers")
F("count:word_count_range", 42, " ".join((_w * 5)[:52]) + " don't can't won't isn't aren't.", "pass", note="POST: 57 words incl. 5 contractions")
F("ratio:stop_words", 175, "Cats don't bark loudly.", "pass", note="POST: 1 stop word of 4 words = 25% <= 39%")
F("ratio:sentence_type", 163, "Wow! Amazing!", "fail", note="POST: 0 declarative, 0 interrogative")
F("ratio:sentence_type", 163, 'It is so. It is "true." Why?', "pass", note="POST: 2:1 with a closing quote after a period")
F("ratio:sentence_balance", 155, "Copernicus had critics", "fail", dec=["D-sentence-type", "D-vacuous"], note="POST: one unterminated sentence")
F("ratio:sentence_balance", 155, 'He had critics. "Why?" "Stop!"', "pass", note="POST: 1:1:1, quoted sentences")
F("ratio:sentence_words", 166, "Cats sleep all day. Dogs sleep all day. Fish swim in ponds.", "fail", note="POST: equal lengths, repeated words")
F("format:line_indent", 74, "Step one\n\n\n  Step two\n    Step three", "pass", note="POST: two consecutive blank lines")
F("format:newline", 90, "Alpha Beta\n \nGamma", "fail", note="POST: two words on a line, whitespace-only line")
F("format:newline", 90, "Alpha\n \nGamma", "pass", note="POST: whitespace-only line between words")
F("format:list", 86, "Entanglement is a well-known effect in state-of-the-art physics.", "fail", note="POST: no list, hyphens inside words")
F("format:no_bullets_bullets", 98, "Deism is weak. It ignores revelation.\n* Point one\n* Point two\n", "pass", note="POST: trailing newline")
F("format:no_bullets_bullets", 98, "Deism is weak. It ignores revelation.\n* Point one\n\n* Point two", "pass", note="POST: blank line between bullets")
F("format:options", 100, "Yes\n", "pass", note="POST: trailing newline (G10)")
F("format:options", 102, "c)\n", "pass", note="POST: trailing newline (G10)")
F("format:quote_unquote", 116, '"a", "b" means x', "fail", note="POST: first quote followed only by a comma")
F("format:quote_unquote", 116, "The claim is \u201cfalse\u201d", "fail", note="POST: typographic quote at the end (G10)")
F("format:sub-bullets", 132, "* A well-known fact\n* Another long-term view", "fail", note="POST: hyphens inside words, no sub-bullets")
F("format:thesis", 142, "<i>The party is conservative.</i>", "pass", note="POST: one section that is only its thesis")
F("format:title_case", 291, "Don't Stop Believing.", "pass", note="POST: contraction")
F("format:title_case", 291, "The Party of Japan", "pass", note="POST: 'of' lower-case (minor under every style)")
F("format:parentheses", 110, "((((( x )", "fail", note="POST: only the innermost pair is closed")
F("custom:european_capitals_sort", 278, ", ".join(c for c in _caps if c != "Kyiv"), "fail", dec=["D-capitals-complete"], note="POST: grader key (no Kyiv)")
_abq = list(_abc)
_abq[2] = '"Coffee brewed slowly," she said.'
F("custom:sentence_alphabet", 282, " ".join(_abq), "pass", note="POST: sentence 3 opens with a quotation mark")
_sx = [_sh, 'P01,Tools,"Smith & Sons",11.99,3'] + [f"P{i:02d},Tools,Acme" for i in range(2, 15)]
F("custom:csv_special_character", 276, "\n".join(_sx), "fail", note="POST: rows 2-14 have 3 fields")
F("custom:csv_quotes", 275, "\n".join([_qh, '"S1"\t\t"A"\t"Fall"\t"95"'] + _qr[1:3]), "fail", note="POST: an empty unquoted field")
F("custom:date_format_list", 277, "1796-00-00, 1805-12-02", "fail", note="POST: month 00 and day 00")
F("custom:mcq_count_length", 279, "\n\n".join(q.replace("Question", "**Question", 1).replace(":", ":**", 1) + "\n" + _opts for q in _q), "pass", note="POST: bold labels")
F("repeat:repeat_change", 61, _req + "\n", "fail", note="POST: unchanged request + trailing newline")
F("repeat:repeat_change", 61, _req.replace(" ", "  ", 1), "fail", note="POST: unchanged request, double space")
F("sentence:alliteration_increment", 179, "Very vast vectors. Big bold cats, tiny tame dogs, red rats.", "fail", note="POST: longest runs 3 then 2 (total 3 then 6)")
F("words:paragraph_last_first", 246, "Banks, unlike others, lend to banks.", "pass", dec=["D-word"], note="POST: comma after first word")
F("count:words_japanese", 47, "This is a nice 2024 day for all of \u5b66\u6821 us.", "fail", dec=["D-word-numbers"], note="POST: number at position 5")
F("words:vowel", 264, "Narratives shape\nminds.", "pass", dec=["D-paragraph"], note="POST: line break inside one paragraph")

F("count:conjunctions", 9, "Tea and cake and, jam. And milk. AND bread.", "fail", note="POST: one conjunction in four spellings (and, and, And, AND)")
F("count:person_names", 27, "Emma, _Liam_ and Sophia met at noon.", "pass", note="POST: markdown italics around a name (G3)")
F("words:no_consecutive", 225, "Honest <b>talks</b> build trust.", "pass", note="POST: HTML tag around a word (G3)")
# Added after the panel (2026-11-10 ~22:56 UTC), found while checking a non-held-out disagreement.
F("format:no_bullets_bullets", 98, "Deism is weak.\n\nIt ignores revelation.\n* Point one\n* Point two", "pass", note="POST-PANEL: blank line between the opening sentences")


def fid(f):
    return f["check"] + "#" + hashlib.sha256(f["response"].encode("utf-8")).hexdigest()[:8]


for f in FIX:
    f["id"] = fid(f)
_ids = [f["id"] for f in FIX]
assert len(_ids) == len(set(_ids)), [i for i in _ids if _ids.count(i) > 1]
