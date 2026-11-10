"""Labeled fixtures for the 58 IFBench checks (step 3).

Every label comes from audit/CONTRACT.md under its proposed readings, never from a grader.
`decisions` names the decision entries whose other readings would flip the label (empty: the
contract is unambiguous for this fixture). `grader` and `reference` record why that grader's
verdict differs from the label: a finding id (F-...) when no combination of readings makes the
verdict right, or the decision ids that do; an empty string means the grader agrees. Tests mark
a disagreement with pytest.mark.xfail(strict=True), so a fix must remove the mark.

Fixture id = check + first 8 hex of sha256 over the kwargs and the response.
"""
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import ifb  # noqa: E402


@dataclass
class Fx:
    check: str
    label: str
    kind: str
    response: str
    key: str = ""
    note: str = ""
    decisions: tuple = ()
    grader: str = ""
    reference: str = ""
    kwargs: dict = field(default_factory=dict)
    prompt: str = ""
    id: str = ""


ROWS = {r["key"]: r for r in ifb.load_rows()}
FIRST_KEY = {}
for _k, _r in ROWS.items():
    for _iid in _r["instruction_id_list"]:
        FIRST_KEY.setdefault(_iid, _k)

# ---------------------------------------------------------------- builders
W60 = ("alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november "
       "oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu apple banana "
       "cherry date elder fig grape hazel iris jade kiwi lemon mango nectar olive peach quince "
       "raisin sage thyme umber vanilla walnut yam zest amber bronze copper denim ebony flax garnet harbor indigo").split()
assert len(W60) == len(set(W60)) == 60


def words(n, start=0):
    return " ".join(W60[start:start + n])


def sentence_words(n):
    """A sentence of exactly n words (n >= 1), no contractions, ends with a period."""
    return (" ".join(W60[:n])).capitalize() + "."


def position_text(n_sent, m_word, keyword, contraction=False, sentence_index=None):
    """n_sent-1 short sentences, then a sentence whose m_word-th word is keyword."""
    target = sentence_index or n_sent
    out = []
    for i in range(1, max(n_sent, target) + 1):
        if i == target:
            filler = W60[: m_word - 1]
            if contraction:
                filler = filler[:-1] + ["don't"]
            out.append(" ".join(filler + [keyword, "today"]).capitalize() + ".")
        else:
            out.append(f"Sentence {W60[i % 60]} stays short.")
    return " ".join(out)


AFRICA = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cape Verde", "Cameroon",
          "Central African Republic", "Chad", "Comoros", "Republic of the Congo",
          "Democratic Republic of the Congo", "Ivory Coast", "Djibouti", "Egypt", "Equatorial Guinea",
          "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya",
          "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco",
          "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "Senegal",
          "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo",
          "Tunisia", "Uganda", "Zambia", "Zimbabwe"]
assert len(AFRICA) == 54
AFRICA_REV = sorted(AFRICA, reverse=True)

CAPS27 = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius",
          "Minsk", "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Prague", "Luxembourg",
          "Paris", "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
CAPS28 = CAPS27[:16] + ["Kyiv"] + CAPS27[16:]  # Kyiv 50.45 N lies between Brussels 50.85 and Prague 50.08

MCQ = [("Who painted Guernica?", ["Picasso", "Dali", "Miro", "Matisse", "Braque"]),
       ("Which movement did Salvador Dali belong to?", ["Surrealism", "Cubism", "Fauvism", "Dada", "Pop Art"]),
       ("Which artist is best known for the drip paintings made in the late 1940s?",
        ["Jackson Pollock", "Mark Rothko", "Willem de Kooning", "Franz Kline", "Lee Krasner"]),
       ("Which German art school, founded in 1919 by Walter Gropius, joined crafts and the fine arts in one program?",
        ["Bauhaus", "Black Mountain", "De Stijl", "Vkhutemas", "Cranbrook"])]


def mcq(label=lambda i: f"Question {i}:", order=(0, 1, 2, 3), n_opts=5):
    blocks = []
    for n, qi in enumerate(order, start=1):
        q, opts = MCQ[qi]
        lines = [f"{label(n)} {q}"] + [f"{'ABCDE'[j]}) {o}" for j, o in enumerate(opts[:n_opts])]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


CSV_CITY = ("ID,Country,City,Year,Count\n1,USA,New York,2020,150\n2,Canada,Toronto,2021,120\n"
            "3,UK,London,2019,200\n4,France,Paris,2022,180\n5,Germany,Berlin,2020,160\n6,Japan,Tokyo,2021,210\n"
            "7,Italy,Rome,2018,130")
CSV_QUOTES = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t"Math"\t"A"\t"Fall"\t"95"\n'
              '"2"\t"Science"\t"B"\t"Spring"\t"85"\n"3"\t"History"\t"A"\t"Fall"\t"92"')


def csv_special(rows=14, special_rows=(1,), bad_row=None):
    out = ["ProductID,Category,Brand,Price,Stock"]
    for i in range(1, rows + 1):
        brand = '"Tom & Jerry"' if i in special_rows else f"Brand{i}"
        row = [f"P{i:03d}", "Toys", brand, str(10 + i), str(100 + i)]
        if i == bad_row:
            row.append("extra")
        out.append(",".join(row))
    return "\n".join(out)


PUNCT_ALL = ("Wait?! The plan (draft [v2] {final}) is ready: it isn't \"done\" -- yet; it is well-known... "
             "sure, really! Is it? Yes.")

# ---------------------------------------------------------------- fixtures
F = []


def fx(check, label, kind, response, key="", **kw):
    F.append(Fx(check=check, label=label, kind=kind, response=response, key=key or FIRST_KEY[check], **kw))


# count:conjunctions
fx("count:conjunctions", "pass", "pass", "I like tea and coffee, but I drink water.", key="6")
fx("count:conjunctions", "fail", "fail", "I like tea. I drink water.", key="6")
fx("count:conjunctions", "fail", "near-miss", "Cats and dogs play, but birds sing.", key="7")
fx("count:conjunctions", "fail", "defect", "Cats and dogs. And birds and, fish.", key="7",
   note="only 'and' in three surface forms (case, trailing comma)", grader="F-conj-surface-forms",
   reference="F-conj-surface-forms")
fx("count:conjunctions", "fail", "decision", "We rest and eat, but we work, or we play, so we win, for example.",
   key="5", note="'for' is a preposition here", decisions=("D-conj",), grader="D-conj", reference="D-conj")

# count:keywords_multiple (door 1, bread 2, blue 3, lamp 5, river 7)
_KW_PASS = ("The door is blue. Bread and bread. Blue blue. Lamp lamp lamp lamp lamp. "
            "River river river river river river river.")
fx("count:keywords_multiple", "pass", "pass", _KW_PASS, key="2")
fx("count:keywords_multiple", "fail", "fail", _KW_PASS.replace("River river river river river river river.",
                                                               "River river river river river river."), key="2")
fx("count:keywords_multiple", "fail", "near-miss", _KW_PASS.replace("river river.", "river rivers."), key="2",
   note="one of the seven is the plural 'rivers'", decisions=("D-match",), grader="D-match")
fx("count:keywords_multiple", "pass", "decision", _KW_PASS.replace("The door is blue.", "The door by the doorway is blue."),
   key="2", note="'doorway' contains 'door' as a substring", decisions=("D-match",), grader="D-match")
fx("count:keywords_multiple", "fail", "near-miss", _KW_PASS.replace("The door is blue.", "The door, the door, is blue."),
   key="2", note="door twice", decisions=("D-keyword-count",))

# count:numbers (key 17: N=2)
fx("count:numbers", "pass", "pass", "In 2020 the team had 15 players.", key="17")
fx("count:numbers", "fail", "fail", "In 2020 the team had 15 players and 3 coaches.", key="17")
fx("count:numbers", "fail", "near-miss", "In 2020 the team had fifteen players.", key="17", decisions=("D-number",))
fx("count:numbers", "pass", "pass", "Pi is about 3.14 and e is about 2.72.", key="17")
fx("count:numbers", "pass", "defect", "The meeting runs 9-11 today.", key="17",
   note="two numbers joined by a hyphen", grader="F-numbers-joined", reference="F-numbers-joined")
fx("count:numbers", "pass", "decision", "1. Alpha\n2. Beta", key="17", note="list markers", decisions=("D-number",))

# count:person_names (key 27: N=3)
fx("count:person_names", "pass", "pass", "Emma met Liam and Sophia at noon.", key="27")
fx("count:person_names", "fail", "fail", "Emma met Liam at noon.", key="27")
fx("count:person_names", "fail", "near-miss", "Emma met Liam and emma again.", key="27")
fx("count:person_names", "pass", "pass", "Emma's dog met Liam's cat and Noah.", key="27")
fx("count:person_names", "fail", "decision", "Emma and Liam showed grace.", key="27", decisions=("D-names-case",))

# count:pronouns (key 33: N=5)
fx("count:pronouns", "pass", "pass", "She told him that they would help us with it.", key="33")
fx("count:pronouns", "fail", "fail", "The cat sat on the mat today.", key="33")
fx("count:pronouns", "fail", "near-miss", "She told him they would help.", key="33")
fx("count:pronouns", "fail", "defect", "This book, that pen, these cups, those hats, and all bags are here.", key="33",
   note="five determiners, no pronoun", grader="F-pronouns-determiners", reference="F-pronouns-determiners")

# count:punctuation (key 36)
fx("count:punctuation", "pass", "pass", PUNCT_ALL, key="36")
fx("count:punctuation", "fail", "fail", PUNCT_ALL.replace(";", ","), key="36", note="no semicolon")
fx("count:punctuation", "fail", "near-miss", PUNCT_ALL.replace("Wait?!", "Wait!"), key="36", note="no interrobang")
fx("count:punctuation", "fail", "defect", "Really?! Yes, it works: it is fine; yes. Go! Why?", key="36",
   note="only . , ? ! ; : and ?!", grader="F-punct-six-marks", reference="F-punct-six-marks")
fx("count:punctuation", "fail", "decision", "Really?! Yes, it works: it's \"fine\"; well-known (yes). Go! Why?", key="36",
   note="core marks only", decisions=("D-punct-set",), grader="D-punct-set", reference="D-punct-set")

# count:unique_word_count (key 24: N=36)
fx("count:unique_word_count", "pass", "pass", words(36) + ".", key="24")
fx("count:unique_word_count", "fail", "fail", words(20) + ".", key="24")
fx("count:unique_word_count", "fail", "near-miss", words(35) + ".", key="24")
fx("count:unique_word_count", "fail", "decision", words(20) + " - " + words(15, 20) + ".", key="24",
   note="35 words and a standalone hyphen", decisions=("D-word",), grader="D-word", reference="D-word")
fx("count:unique_word_count", "pass", "pass", "The the THE " + words(35) + ".", key="24", decisions=("D-unique",))

# count:word_count_range (key 43: 24..28)
_WC26 = sentence_words(13) + " " + sentence_words(13)
fx("count:word_count_range", "pass", "pass", _WC26, key="43")
fx("count:word_count_range", "fail", "fail", sentence_words(20) + " " + sentence_words(20), key="43")
fx("count:word_count_range", "fail", "near-miss", sentence_words(15) + " " + sentence_words(14), key="43", note="29 words")
fx("count:word_count_range", "pass", "near-miss", sentence_words(12) + " " + sentence_words(12), key="43", note="24 words",
   decisions=("D-between",))
fx("count:word_count_range", "pass", "defect", "We don't know and it isn't clear. " + sentence_words(20), key="43",
   note="27 words, two contractions", grader="F-wordcount-contractions", reference="F-wordcount-contractions")

# count:words_japanese (key 47: N=5)
fx("count:words_japanese", "pass", "pass", "One two three four 日本 six seven eight nine 東京", key="47")
fx("count:words_japanese", "fail", "fail", "One two three four five six seven eight nine 東京", key="47")
fx("count:words_japanese", "fail", "near-miss", "One two three four 日本 six seven eight nine Tokyo", key="47",
   decisions=("D-japanese",))
fx("count:words_japanese", "fail", "defect", "One two three four - five six seven eight 日本", key="47",
   note="a standalone hyphen holds position 5 and is skipped", grader="F-japanese-skip-tokens",
   reference="F-japanese-skip-tokens")
fx("count:words_japanese", "fail", "decision", "Short reply here.", key="47", note="fewer than N words",
   decisions=("D-vacuous",), grader="D-vacuous", reference="D-vacuous")

# custom:character_reverse
fx("custom:character_reverse", "pass", "pass", ".elgae dlab eht si lobmys lanoitan s'SU ehT")
fx("custom:character_reverse", "fail", "fail", "The bald eagle is the national symbol of the US.")
fx("custom:character_reverse", "fail", "near-miss", "ehT dlab elgae si eht lanoitan lobmys", decisions=("D-char-reverse",))
fx("custom:character_reverse", "fail", "defect", "The answer is the bald eagle. Reversed: .elgae dlab eht si rewsna ehT",
   note="normal-order answer plus a reversed copy", grader="F-charrev-substring", reference="F-charrev-substring")

# custom:csv_city
fx("custom:csv_city", "pass", "pass", CSV_CITY)
fx("custom:csv_city", "fail", "fail", CSV_CITY.rsplit("\n", 1)[0])
fx("custom:csv_city", "fail", "near-miss", CSV_CITY.replace(",", ";"))
fx("custom:csv_city", "pass", "decision", "```csv\n" + CSV_CITY + "\n```", decisions=("D-csv",), grader="D-csv",
   reference="D-csv")

# custom:csv_quotes
fx("custom:csv_quotes", "pass", "pass", CSV_QUOTES)
fx("custom:csv_quotes", "fail", "fail", CSV_QUOTES.replace("\t", ","))
fx("custom:csv_quotes", "fail", "near-miss", CSV_QUOTES.replace('"Math"', "Math"))
fx("custom:csv_quotes", "fail", "decision", CSV_QUOTES.replace('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"',
                                                                "StudentID\tSubject\tGrade\tSemester\tScore"),
   note="header unquoted", decisions=("D-csv",))

# custom:csv_special_character
fx("custom:csv_special_character", "pass", "pass", csv_special())
fx("custom:csv_special_character", "fail", "fail", csv_special(rows=13))
fx("custom:csv_special_character", "fail", "near-miss", csv_special().replace('"Tom & Jerry"', "Tom & Jerry"))
fx("custom:csv_special_character", "fail", "decision", csv_special(special_rows=(1, 2)), note="two special fields",
   decisions=("D-csv",), grader="D-csv", reference="D-csv")
fx("custom:csv_special_character", "fail", "defect", csv_special(bad_row=5), note="row 5 has six fields",
   grader="F-csvspecial-early-return", reference="F-csvspecial-early-return")

# custom:date_format_list
fx("custom:date_format_list", "pass", "pass", "1796-04-12, 1805-12-02, 1815-06-18")
fx("custom:date_format_list", "fail", "fail", "April 12, 1796; December 2, 1805")
fx("custom:date_format_list", "fail", "near-miss", "1796-04-12, 1805-12-02\nThese are the battle dates.")
fx("custom:date_format_list", "fail", "defect", "1805-00-00, 1796-04-12", note="month 00 and day 00",
   grader="F-dates-invalid", reference="F-dates-invalid")
fx("custom:date_format_list", "pass", "decision", "1900-01-01, 1950-05-05", decisions=("D-custom-facts",),
   grader="D-custom-facts", reference="D-custom-facts")

# custom:european_capitals_sort
fx("custom:european_capitals_sort", "pass", "pass", ", ".join(CAPS28), grader="F-capitals-kyiv", reference="F-capitals-kyiv",
   note="all capitals north of 45 N, Kyiv included")
fx("custom:european_capitals_sort", "fail", "fail", ", ".join(sorted(CAPS28)))
fx("custom:european_capitals_sort", "fail", "near-miss", ", ".join(CAPS27), note="Kyiv missing",
   decisions=("D-custom-facts",), grader="D-custom-facts", reference="D-custom-facts")
fx("custom:european_capitals_sort", "fail", "decision", "Here are the capitals: " + ", ".join(CAPS28),
   decisions=("D-custom-extra-text",))

# custom:mcq_count_length
fx("custom:mcq_count_length", "pass", "pass", mcq())
fx("custom:mcq_count_length", "fail", "fail", mcq(order=(0, 1, 2)))
fx("custom:mcq_count_length", "fail", "near-miss", mcq(order=(0, 2, 1, 3)), note="question 3 shorter than question 2")
fx("custom:mcq_count_length", "pass", "defect", mcq(label=lambda i: "Question:"), note="label without a number",
   grader="F-mcq-label-number", reference="F-mcq-label-number")
fx("custom:mcq_count_length", "fail", "near-miss", mcq(n_opts=4), note="four options each")

# custom:multiples
fx("custom:multiples", "pass", "pass", "14, 21, 28, 35, 42, 49")
fx("custom:multiples", "fail", "fail", "7, 14, 21, 28, 35, 42, 49")
fx("custom:multiples", "fail", "near-miss", "14, 21, 28, 35, 42")
fx("custom:multiples", "pass", "pass", "Multiples: 14, 21, 28, 35, 42, 49", decisions=("D-custom-extra-text",))
fx("custom:multiples", "fail", "decision", "Here are the multiples of 7 between 10 and 50: 14, 21, 28, 35, 42, 49",
   decisions=("D-custom-extra-text",))

# custom:reverse_newline
fx("custom:reverse_newline", "pass", "pass", "\n".join(AFRICA_REV))
fx("custom:reverse_newline", "fail", "fail", "\n".join(sorted(AFRICA)))
_swap = AFRICA_REV[:]
_swap[10], _swap[11] = _swap[11], _swap[10]
fx("custom:reverse_newline", "fail", "near-miss", "\n".join(_swap))
fx("custom:reverse_newline", "pass", "defect", "\n".join(f"{i}. {c}" for i, c in enumerate(AFRICA_REV, 1)),
   note="numbered list", grader="F-africa-numbering", reference="F-africa-numbering")
fx("custom:reverse_newline", "fail", "decision", "\n".join(["Zimbabwe"] + [f"Y{chr(122 - i // 26)}{chr(122 - i % 26)}land"
                                                                         for i in range(52)]),
   note="52 made-up names in reverse order after Zimbabwe", decisions=("D-custom-facts",), grader="D-custom-facts",
   reference="D-custom-facts")

# custom:sentence_alphabet
_ALPHA26 = ("A cat sat. Birds sang. Cows mooed. Dogs barked. Eagles soared. Foxes ran. Geese honked. Horses neighed. "
            "Insects buzzed. Jays chirped. Kids laughed. Lions roared. Mice squeaked. Nobody slept. Owls hooted. "
            "Pigs grunted. Quails called. Rabbits hopped. Snakes hissed. Turtles crawled. Unicorns danced. Voles dug. "
            "Wolves howled. Xerus scurried. Yaks grazed. Zebras rested.")
fx("custom:sentence_alphabet", "pass", "pass", _ALPHA26)
fx("custom:sentence_alphabet", "fail", "fail", _ALPHA26.replace(" Zebras rested.", ""))
fx("custom:sentence_alphabet", "fail", "near-miss", _ALPHA26.replace("Cows mooed. Dogs barked.", "Dogs barked. Cows mooed."))
fx("custom:sentence_alphabet", "pass", "defect", _ALPHA26.replace("Birds sang.", "\"Birds sing,\" said Ann."),
   note="sentence 2 opens with a quotation mark", grader="F-alphabet-story-quote")

# custom:word_reverse
fx("custom:word_reverse", "pass", "pass", "eagle bald the is US the of symbol national The")
fx("custom:word_reverse", "fail", "fail", "The bald eagle is the national symbol of the US.")
fx("custom:word_reverse", "fail", "near-miss", ".SU eht fo lobmys lanoitan eht si elgae dlab ehT")
fx("custom:word_reverse", "fail", "defect", "The bald eagle is the answer. eagle bald the is US the of symbol national The",
   note="normal-order answer plus a reversed copy", grader="F-wordrev-mixed", reference="F-wordrev-mixed")

# format:emoji (key 70)
fx("format:emoji", "pass", "pass", "Light is fast. 🚀 Time slows down. ⏳ Mass grows. 📈")
fx("format:emoji", "fail", "fail", "Light is fast. Time slows down 🚀.")
fx("format:emoji", "fail", "near-miss", "Light is fast. 🚀 Time slows down. ⏳ Mass grows.")
fx("format:emoji", "pass", "decision", "Light is fast 🚀. Time slows down ⏳.", decisions=("D-emoji-position",))
fx("format:emoji", "pass", "decision", "# Physics\nLight is fast. 🚀", decisions=("D-sentence",))

# format:line_indent (key 74)
fx("format:line_indent", "pass", "pass", "Line one\n  Line two\n    Line three\n      Line four")
fx("format:line_indent", "fail", "fail", "Line one\nLine two\nLine three")
fx("format:line_indent", "fail", "near-miss", "Line one\n  Line two\n  Line three")
fx("format:line_indent", "pass", "pass", "Line one\n  Line two\n\n    Line three", decisions=("D-indent",))
fx("format:line_indent", "pass", "decision", "Line one\n  Line two\n\n\n    Line three", note="two blank lines",
   decisions=("D-indent",), grader="D-indent", reference="D-indent")
fx("format:line_indent", "pass", "defect", "Line one\n\tLine two\n\t\tLine three", note="tab indentation",
   grader="F-indent-tabs", reference="F-indent-tabs")

# format:list
fx("format:list", "pass", "pass", "!?!? Preludes are short pieces\n!?!? Caprichos are playful works\n!?!? Romances are lyrical songs",
   key="83")
fx("format:list", "fail", "fail", "* Preludes\n* Caprichos\n* Romances", key="83")
fx("format:list", "fail", "near-miss", "!?!? Preludes are short pieces", key="83")
fx("format:list", "fail", "defect", "Quantum entanglement is well-known, but its link to parallel worlds is far-fetched.",
   key="86", note="no list; two hyphenated words", grader="F-list-anywhere", reference="F-list-anywhere")
fx("format:list", "pass", "decision", "Preludes !?!? Caprichos !?!? Romances", key="83", decisions=("D-list",))

# format:newline (key 90)
fx("format:newline", "pass", "pass", "Remake\nwould\nfeature\nmodern\nanimation.")
fx("format:newline", "fail", "fail", "A remake would feature modern animation.")
fx("format:newline", "fail", "near-miss", "Remake\nwould feature\nmodern")
fx("format:newline", "fail", "defect", "Remake would\n \nfeature", note="a space-only line offsets a two-word line",
   grader="F-newline-blank-offset", reference="F-newline-blank-offset")
fx("format:newline", "pass", "pass", "Remake\n-\nwould")

# format:no_bullets_bullets (key 98)
_NBB = "Deism sees God as distant. This view has problems.\n* It ignores revelation.\n* It weakens prayer."
fx("format:no_bullets_bullets", "pass", "pass", _NBB)
fx("format:no_bullets_bullets", "fail", "fail", "* It ignores revelation.\n* It weakens prayer.")
fx("format:no_bullets_bullets", "fail", "near-miss", "Deism sees God as distant.\n* It ignores revelation.\n* It weakens prayer.")
fx("format:no_bullets_bullets", "pass", "defect", _NBB.replace("\n* It weakens", "\n\n* It weakens"),
   note="blank line between the bullets", grader="F-nbb-blank-line", reference="F-nbb-blank-line")
fx("format:no_bullets_bullets", "fail", "defect", "Is God distant? Many say so!\n* It ignores revelation.\n* It weakens prayer.",
   note="no sentence ends in a period", grader="F-nbb-period", reference="F-nbb-period")
fx("format:no_bullets_bullets", "pass", "defect", _NBB + "\nIn short, the view fails.", note="a closing sentence after the bullets",
   grader="F-nbb-trailing-text", reference="F-nbb-trailing-text")

# format:no_whitespace (key 298)
fx("format:no_whitespace", "pass", "pass", "Piousegoistsareself-servingbelievers.", key="298")
fx("format:no_whitespace", "fail", "fail", "Pious egoists", key="298")
fx("format:no_whitespace", "fail", "near-miss", "Piousegoists\n", key="298", decisions=("D-trailing-ws",))
fx("format:no_whitespace", "fail", "near-miss", "Pious egoists", key="298", note="no-break space")

# format:options
fx("format:options", "pass", "pass", "Maybe", key="100")
fx("format:options", "pass", "pass", "d)", key="102")
fx("format:options", "fail", "fail", "Yes and no.", key="100")
fx("format:options", "fail", "near-miss", "Maybe. It depends on the design.", key="100", decisions=("D-options",))
fx("format:options", "pass", "defect", "D)", key="102", note="upper-case option label", grader="F-options-case",
   reference="F-options-case")
fx("format:options", "pass", "defect", "Maybe\n", key="100", note="trailing newline", grader="F-options-whitespace",
   reference="F-options-whitespace")
fx("format:options", "pass", "defect", "d)\n", key="102", note="trailing newline", grader="F-options-whitespace",
   reference="F-options-whitespace")
fx("format:options", "pass", "defect", "I\ndon't\nknow", key="105", note="one word per line, as prompt 105 also asks",
   grader="F-options-whitespace", reference="F-options-whitespace")
fx("format:options", "pass", "decision", "d) Admissible character evidence.", key="102", decisions=("D-options",),
   grader="D-options", reference="D-options")

# format:output_template (key 292)
_TPL = "My Answer: Suffering on a cosmic scale.\nMy Conclusion: It is a thought experiment.\nFuture Outlook: More research is needed."
fx("format:output_template", "pass", "pass", _TPL)
fx("format:output_template", "fail", "fail", "Answer: x\nConclusion: y\nOutlook: z")
fx("format:output_template", "fail", "near-miss", _TPL.replace("My Conclusion:", "Conclusion:"))
fx("format:output_template", "fail", "defect", "Future Outlook: More research.\nMy Answer: Cosmic suffering.\nMy Conclusion: A thought experiment.",
   note="labels out of order", grader="F-template-presence-only", reference="F-template-presence-only")
fx("format:output_template", "fail", "defect", "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]",
   note="placeholders left in", grader="F-template-presence-only", reference="F-template-presence-only")
fx("format:output_template", "fail", "decision", "Here is my response.\n" + _TPL, decisions=("D-template",),
   grader="D-template", reference="D-template")

# format:parentheses (key 110)
fx("format:parentheses", "pass", "pass", "AI (artificial intelligence [machine learning {deep (neural [networks])}]) matters.", key="110")
fx("format:parentheses", "fail", "fail", "AI (artificial intelligence) matters.", key="110")
fx("format:parentheses", "fail", "near-miss", "AI ( [ { ( x ) } ] ) matters.", key="110")
fx("format:parentheses", "fail", "decision", "AI ((((( x ) matters.", key="110", note="five opened, one closed",
   decisions=("D-paren",), grader="D-paren", reference="D-paren")

# format:quote_unquote (key 116)
fx("format:quote_unquote", "pass", "pass", 'The phrase "fully connected" means each neuron links to every neuron in the next layer.', key="116")
fx("format:quote_unquote", "fail", "fail", 'The statement says "Each neuron connects to all nodes"', key="116")
fx("format:quote_unquote", "fail", "near-miss", '"Fully connected" "dense layer" both describe it.', key="116")
fx("format:quote_unquote", "fail", "defect", "The statement says “Each neuron connects to all nodes”", key="116",
   note="curly quotes, quote at the end", grader="F-quote-curly", reference="F-quote-curly")
fx("format:quote_unquote", "fail", "decision", "No quotes here at all.", key="116", decisions=("D-vacuous",),
   grader="D-vacuous", reference="D-vacuous")

# format:quotes (key 119)
fx("format:quotes", "pass", "pass", "He said, \"She told me, 'The sign read \"Closed\" today.'\"", key="119")
fx("format:quotes", "fail", "fail", 'He said, "The sign read Closed."', key="119")
fx("format:quotes", "fail", "near-miss", "He said, \"She read 'Closed' today.\"", key="119")
fx("format:quotes", "fail", "defect", "\"I can't\" and \"won't\" are contractions.", key="119",
   note="apostrophes taken as quote marks", grader="F-quotes-apostrophe", reference="F-quotes-apostrophe")
fx("format:quotes", "pass", "defect", "He said, “She told me, ‘The sign read “Closed” today.’”", key="119",
   note="curly quotes", grader="F-quotes-curly", reference="F-quotes-curly")

# format:sub-bullets (key 126)
fx("format:sub-bullets", "pass", "pass", "* Light drops\n  - Photosynthesis slows\n* Temperature falls\n  - Growth pauses", key="126")
fx("format:sub-bullets", "fail", "fail", "Eclipses affect plants briefly.", key="126", note="no bullets at all",
   grader="F-subbullets-none", reference="F-subbullets-none")
fx("format:sub-bullets", "fail", "near-miss", "* Light drops\n  - Photosynthesis slows\n* Temperature falls", key="126")
fx("format:sub-bullets", "fail", "defect", "* Light drops\n  - Photosynthesis slows\n* Short-term cooling", key="126",
   note="second bullet has a hyphenated word, no sub-bullet", grader="F-subbullets-any-hyphen",
   reference="F-subbullets-any-hyphen")
fx("format:sub-bullets", "pass", "defect", "**Effects**\n* Light drops\n  - Photosynthesis slows", key="126",
   note="bold heading", grader="F-subbullets-bold", reference="F-subbullets-bold")
fx("format:sub-bullets", "fail", "decision", "* Light drops\n- Photosynthesis slows", key="126", decisions=("D-subbullet",),
   grader="D-subbullet", reference="D-subbullet")

# format:thesis (key 142)
fx("format:thesis", "pass", "pass", "<i>The party favors tradition.</i> It supports the emperor and stability.\n\n"
   "<i>Its economic policy is cautious.</i> It prefers low spending.", key="142")
fx("format:thesis", "fail", "fail", "The party favors tradition. It supports stability.", key="142")
fx("format:thesis", "fail", "near-miss", "*The party favors tradition.* It supports stability.", key="142")
fx("format:thesis", "fail", "defect", "The party has a long history.\n\nIt values order, and <i>tradition is central</i> to its program.",
   key="142", note="italics only inside the second paragraph", grader="F-thesis-anywhere", reference="F-thesis-anywhere")
fx("format:thesis", "fail", "decision", "<i>The party favors tradition.</i> It supports stability.\n\nIts economy is cautious.",
   key="142", decisions=("D-section",), grader="D-section", reference="D-section")

# format:title_case (key 291)
fx("format:title_case", "pass", "pass", "Liberal Democrats Govern Japan Today.", key="291")
fx("format:title_case", "fail", "fail", "the liberal democratic party governs japan.", key="291")
fx("format:title_case", "fail", "near-miss", "Liberal Democrats govern Japan Today.", key="291")
fx("format:title_case", "pass", "decision", "The Party of Japan Governs.", key="291", decisions=("D-title",),
   grader="D-title", reference="D-title")
fx("format:title_case", "pass", "defect", "Japan's Leaders Don't Rest.", key="291", note="contraction",
   grader="F-title-contraction", reference="F-title-contraction")

# ratio:overlap (key 149: 13%, reference "Is it easier to urbanize a jungle or to urbanize a desert?")
_OV = "Is it easier to urbanize a jungle " + words(33)
fx("ratio:overlap", "pass", "decision", _OV, key="149", note="5 of 38 distinct response word trigrams (13.2%) occur in the reference",
   decisions=("D-overlap",), grader="D-overlap")
fx("ratio:overlap", "fail", "decision", "Deserts lack water, so building there needs pipelines and cooling.", key="149",
   decisions=("D-overlap",))

# ratio:sentence_balance (key 155)
fx("ratio:sentence_balance", "pass", "pass", "Copernicus faced critics. Who opposed him? What a debate it was!", key="155")
fx("ratio:sentence_balance", "fail", "fail", "Copernicus faced critics. Many opposed him. Who were they?", key="155")
fx("ratio:sentence_balance", "fail", "near-miss", "Critics existed. Others agreed. Who opposed him? Why? What a debate!",
   key="155", note="2:2:1", decisions=("D-balance",))
fx("ratio:sentence_balance", "fail", "defect", "Luther called him \"a fool.\" Melanchthon called it \"absurd.\" Others asked, \"Is he right?\"",
   key="155", note="2:1:0, every sentence ends with a closing quote", grader="F-ratio-quote-endings",
   reference="F-ratio-quote-endings")
fx("ratio:sentence_balance", "fail", "decision", "Critics existed", key="155", note="no typed sentence",
   decisions=("D-vacuous",), grader="D-vacuous", reference="D-vacuous")

# ratio:sentence_type (key 163)
fx("ratio:sentence_type", "pass", "pass", "Restructuring keeps meaning. It is called paraphrasing. Is it hard?", key="163")
fx("ratio:sentence_type", "fail", "fail", "It is called paraphrasing. Is it hard? Why do it?", key="163")
fx("ratio:sentence_type", "fail", "near-miss", "Restructuring keeps meaning. It is called paraphrasing. It is common. Is it hard?", key="163")
fx("ratio:sentence_type", "fail", "defect", "Some call it \"paraphrasing.\" Others say \"rewording.\" Others say \"rephrasing.\"",
   key="163", note="3:0, closing quotes", grader="F-ratio-quote-endings", reference="F-ratio-quote-endings")
fx("ratio:sentence_type", "fail", "decision", "What a task!", key="163", decisions=("D-vacuous",), grader="D-vacuous",
   reference="D-vacuous")

# ratio:sentence_words (key 166)
fx("ratio:sentence_words", "pass", "pass", "Cats nap. Dogs run. Owls fly.", key="166")
fx("ratio:sentence_words", "fail", "fail", "Cats nap. Dogs run fast. Owls fly.", key="166")
fx("ratio:sentence_words", "fail", "near-miss", "Cats nap. Dogs run. Owls fly. Pigs dig.", key="166")
fx("ratio:sentence_words", "fail", "defect", "The cat sat. The cat ran. The cat hid.", key="166",
   note="equal lengths, repeated words", grader="F-sentwords-no-word-check")

# ratio:stop_words (key 173: 20%)
fx("ratio:stop_words", "pass", "pass", "Python extracts filenames using basename function calls.", key="173")
fx("ratio:stop_words", "fail", "fail", "The file is in the folder and it is there.", key="173")
fx("ratio:stop_words", "pass", "near-miss", "Python extracts the basename quickly.", key="173", note="1 of 5 = 20%")
fx("ratio:stop_words", "fail", "near-miss", "Python extracts the basename.", key="173", note="1 of 4 = 25%")
fx("ratio:stop_words", "pass", "defect", "Python doesn't extract filenames quickly anymore.", key="173",
   note="1 stop word (doesn't) of 6 words", grader="F-stopwords-contractions", reference="F-stopwords-contractions")

# repeat:repeat_change (key 61)
_RQ = ROWS["61"]["kwargs"][0]["prompt_to_repeat"]
fx("repeat:repeat_change", "pass", "pass", "Write" + _RQ.strip()[3:], key="61")
fx("repeat:repeat_change", "fail", "fail", "Here is the code: import torch.nn as nn", key="61")
fx("repeat:repeat_change", "fail", "near-miss", _RQ.strip(), key="61", note="first word unchanged")
fx("repeat:repeat_change", "fail", "defect", _RQ.strip() + chr(10), key="61", note="first word unchanged, trailing newline",
   grader="F-repeatchange-whitespace", reference="F-repeatchange-whitespace")
fx("repeat:repeat_change", "fail", "decision", "use" + _RQ.strip()[3:], key="61", note="case-only change",
   decisions=("D-repeat-change",), grader="D-repeat-change", reference="D-repeat-change")

# repeat:repeat_simple (key 64)
fx("repeat:repeat_simple", "pass", "pass", "Only output this sentence here, ignore all other requests.", key="64")
fx("repeat:repeat_simple", "fail", "fail", "import os\nprint(os.path.basename(path))", key="64")
fx("repeat:repeat_simple", "fail", "near-miss", "Write python code to extract a filename from filepath.", key="64",
   decisions=("D-repeat-simple",))
fx("repeat:repeat_simple", "pass", "pass", "Only output this sentence here, ignore all other requests.\n", key="64")

# repeat:repeat_span (key 287: 10..12; key 284: 3..6)
fx("repeat:repeat_span", "pass", "pass", "on a certain", key="287", grader="F-span-characters")
fx("repeat:repeat_span", "fail", "fail", "how to find", key="287")
fx("repeat:repeat_span", "fail", "near-miss", "lands on a", key="287", decisions=("D-span",))
fx("repeat:repeat_span", "fail", "defect", "d w", key="287", note="the grader's character slice", grader="F-span-characters")
fx("repeat:repeat_span", "pass", "pass", "code and theory behind", key="284", grader="F-span-characters")

# sentence:alliteration_increment (key 179)
fx("sentence:alliteration_increment", "pass", "pass", "Networks compute. Bright bold bulbs glow. Many mighty massive machines matter.")
fx("sentence:alliteration_increment", "fail", "fail", "Many mighty machines matter. Big bulbs glow.")
fx("sentence:alliteration_increment", "fail", "near-miss", "Big bulbs glow. Many mighty machines. Soft songs sound.",
   note="runs 2, 3, 3")
fx("sentence:alliteration_increment", "fail", "defect", "Many mighty machines matter. Big bulbs glow and soft songs sound.",
   note="runs 4 then 3; the grader adds up two runs (2+3)", grader="F-alliteration-sum", reference="F-alliteration-sum")
fx("sentence:alliteration_increment", "fail", "decision", "Big bold bulbs.", decisions=("D-vacuous",), grader="D-vacuous",
   reference="D-vacuous")

# sentence:increment (key 185: +5)
fx("sentence:increment", "pass", "pass", sentence_words(2) + " " + sentence_words(7) + " " + sentence_words(12), key="185")
fx("sentence:increment", "fail", "fail", sentence_words(2) + " " + sentence_words(4) + " " + sentence_words(6), key="185")
fx("sentence:increment", "fail", "near-miss", sentence_words(2) + " " + sentence_words(7) + " " + sentence_words(11), key="185")
fx("sentence:increment", "fail", "decision", sentence_words(9), key="185", decisions=("D-vacuous",), grader="D-vacuous",
   reference="D-vacuous")

# sentence:keyword (key 193: angora in sentence 3)
fx("sentence:keyword", "pass", "pass", "Cognitive dissonance is a conflict. It causes stress. Angora wool is soft, like a calm mind.", key="193")
fx("sentence:keyword", "fail", "fail", "Cognitive dissonance is a conflict. Angora wool is soft. It causes stress.", key="193")
fx("sentence:keyword", "fail", "near-miss", "Cognitive dissonance is a conflict. It causes stress.", key="193")
fx("sentence:keyword", "pass", "decision", "# Dissonance\nCognitive dissonance is a conflict. It causes stress. Angora wool is soft.",
   key="193", decisions=("D-sentence",))
fx("sentence:keyword", "pass", "decision", "Intro line\n- first item\n- second item angora", key="193",
   decisions=("D-sentence",), grader="D-sentence", reference="D-sentence")

# words:alphabet (key 202)
fx("words:alphabet", "pass", "pass", "Big cats dance every fine game.", decisions=("D-alphabet-start",))
fx("words:alphabet", "fail", "fail", "The cat sat.")
fx("words:alphabet", "fail", "near-miss", "Big cats dance every game.")
fx("words:alphabet", "pass", "pass", "Yellow zebras always bounce.", decisions=("D-alphabet-start",))
fx("words:alphabet", "pass", "decision", "Big cats dance — every fine game.", note="spaced em dash",
   decisions=("D-word",), grader="D-word", reference="D-word")

# words:consonants (key 211)
fx("words:consonants", "pass", "pass", "Strong winds blow.", key="211")
fx("words:consonants", "fail", "fail", "I am a cat.", key="211")
fx("words:consonants", "fail", "near-miss", "Strong winds blow at night.", key="211")
fx("words:consonants", "pass", "decision", "Strong winds sway my crops.", key="211", decisions=("D-y",))
fx("words:consonants", "pass", "decision", "Strong winds - dark clouds.", key="211", decisions=("D-word",), grader="D-word",
   reference="D-word")

# words:keywords_specific_position (key 11: beneath, sentence 23, word 34)
fx("words:keywords_specific_position", "pass", "pass", position_text(23, 34, "beneath"), key="11")
fx("words:keywords_specific_position", "fail", "fail", position_text(23, 33, "beneath"), key="11")
fx("words:keywords_specific_position", "fail", "near-miss", position_text(23, 34, "beneath", sentence_index=22), key="11")
fx("words:keywords_specific_position", "pass", "defect", position_text(23, 34, "beneath", contraction=True), key="11",
   note="a contraction before the keyword", grader="F-position-contractions", reference="F-position-contractions")

# words:last_first (key 220)
fx("words:last_first", "pass", "pass", "Saturn has clouds. Clouds form ice. Ice reflects light.", key="220")
fx("words:last_first", "fail", "fail", "Saturn has clouds. Gas giants roam.", key="220")
fx("words:last_first", "fail", "near-miss", "Saturn has clouds. Clouds form ice. Water reflects light.", key="220")
fx("words:last_first", "pass", "defect", "Saturn has \"clouds.\" Clouds form ice.", key="220", note="closing quote",
   grader="F-lastfirst-quotes", reference="F-lastfirst-quotes")
fx("words:last_first", "fail", "decision", "Saturn has clouds.", key="220", decisions=("D-vacuous",), grader="D-vacuous",
   reference="D-vacuous")

# words:no_consecutive (key 225)
fx("words:no_consecutive", "pass", "pass", "Open talk can heal deep rifts.", key="225")
fx("words:no_consecutive", "fail", "fail", "Constructive conversation can heal.", key="225")
fx("words:no_consecutive", "fail", "near-miss", "Open talk can create harmony.", key="225")
fx("words:no_consecutive", "pass", "defect", "Open talk on 10 11 topics helps.", key="225", note="adjacent numbers",
   grader="F-noconsec-digits", reference="F-noconsec-digits")

# words:odd_even_syllables (key 233)
fx("words:odd_even_syllables", "pass", "pass", "Models learn without examples.", key="233")
fx("words:odd_even_syllables", "fail", "fail", "Big red dogs run.", key="233")
fx("words:odd_even_syllables", "fail", "near-miss", "Models learn without any examples.", key="233")

# words:palindrome (key 237)
fx("words:palindrome", "pass", "pass", "Level radar civic kayak refer madam rotor racecar stats tenet appear in proofs.", key="237")
fx("words:palindrome", "fail", "fail", "Level radar civic appear in proofs.", key="237")
fx("words:palindrome", "fail", "near-miss", "Level radar civic kayak refer madam rotor racecar stats appear in proofs.", key="237")
fx("words:palindrome", "fail", "decision", " ".join(["level"] * 10) + ".", key="237", decisions=("D-palindrome",),
   grader="D-palindrome", reference="D-palindrome")
fx("words:palindrome", "fail", "decision", "aaaaa bbbbb ccccc ddddd eeeee fffff ggggg hhhhh iiiii jjjjj", key="237",
   decisions=("D-palindrome",), grader="D-palindrome", reference="D-palindrome")

# words:paragraph_last_first (key 241)
fx("words:paragraph_last_first", "pass", "pass", "Sets can be open sets\nOpen intervals stay open", key="241")
fx("words:paragraph_last_first", "fail", "fail", "Sets can be open\nOpen intervals stay open", key="241")
fx("words:paragraph_last_first", "fail", "near-miss", "Sets can be open sets\nOpen intervals stay closed", key="241")
fx("words:paragraph_last_first", "pass", "defect", "Sets, in topology, can be infinite sets.", key="241",
   note="comma after the first word", grader="F-paralastfirst-comma", reference="F-paralastfirst-comma")

# words:prime_lengths (key 247)
fx("words:prime_lengths", "pass", "pass", "We see signs, not truth.", key="247")
fx("words:prime_lengths", "fail", "fail", "Baudrillard means simulation.", key="247")
fx("words:prime_lengths", "fail", "near-miss", "We see a sign.", key="247")
fx("words:prime_lengths", "fail", "decision", "We can't see truth.", key="247", decisions=("D-prime-length",))

# words:repeats (key 256: 3)
fx("words:repeats", "pass", "pass", "Gordon saw Alyx. Gordon coped. Gordon survived.", key="256")
fx("words:repeats", "fail", "fail", "Gordon saw Alyx. Gordon coped. Gordon survived. Gordon slept. Gordon woke.", key="256")
fx("words:repeats", "fail", "near-miss", "Gordon saw Alyx. Gordon coped. Gordon survived. Gordon slept.", key="256",
   decisions=("D-repeat-count",))

# words:start_verb (key 257)
fx("words:start_verb", "pass", "pass", "Imagine an empire built on eternal suffering.", key="257",
   note="the tagger reads 'Imagine' as a proper noun", grader="F-startverb-tagger", reference="F-startverb-tagger")
fx("words:start_verb", "pass", "pass", "Consider an empire where minds suffer.", key="257")
fx("words:start_verb", "fail", "fail", "The empire suffers forever.", key="257")
fx("words:start_verb", "fail", "near-miss", "Empire of pain endures.", key="257")
fx("words:start_verb", "pass", "defect", "**Imagine** an empire built on suffering.", key="257", note="bold first word",
   grader="F-startverb-markup", reference="F-startverb-markup")
fx("words:start_verb", "pass", "defect", "Build an empire of endless pain.", key="257", note="tagger reads 'Build' as a proper noun",
   grader="F-startverb-tagger", reference="F-startverb-tagger")
fx("words:start_verb", "pass", "defect", "Explore the idea of an empire.", key="257", note="tagger reads 'Explore' as a preposition",
   grader="F-startverb-tagger", reference="F-startverb-tagger")

# words:vowel (key 269)
fx("words:vowel", "pass", "pass", "Cats nap at dawn and eat ham.", key="269")
fx("words:vowel", "fail", "fail", "Education is important for our future.", key="269")
fx("words:vowel", "fail", "near-miss", "Cats nap on hot beds in tents.", key="269", note="a, o, e, i")
fx("words:vowel", "fail", "decision", "Cats sleep on mats in huts.", key="269", decisions=("D-vowel",))
fx("words:vowel", "pass", "decision", "Cats nap at dawn.\nRats eat ham.", key="269", note="single line break",
   decisions=("D-paragraph",), grader="D-paragraph", reference="D-paragraph")

# words:words_position (key 16: despite)
fx("words:words_position", "pass", "pass", "Even despite the rain, we went out despite everything.", key="16")
fx("words:words_position", "fail", "fail", "We went out despite the rain.", key="16")
fx("words:words_position", "fail", "near-miss", "Even despite rain, we went despite it all.", key="16")
fx("words:words_position", "pass", "defect", "Yes, despite the rain, we went despite all.", key="16",
   note="comma after the first word", grader="F-wordspos-comma")

# ---------------------------------------------------------------- finalize
for f in F:
    row = ROWS[f.key]
    idx = row["instruction_id_list"].index(f.check)
    f.kwargs = dict(row["kwargs"][idx])
    f.prompt = row["prompt"]
    h = hashlib.sha256(json.dumps({"kwargs": f.kwargs, "response": f.response}, sort_keys=True,
                                  ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    f.id = f"{f.check}-{h}"

FIXTURES = F
assert len({f.id for f in F}) == len(F), "duplicate fixture ids"
CHECKS = sorted({i for r in ROWS.values() for i in r["instruction_id_list"]})
assert set(CHECKS) == {f.check for f in F}, set(CHECKS) - {f.check for f in F}
