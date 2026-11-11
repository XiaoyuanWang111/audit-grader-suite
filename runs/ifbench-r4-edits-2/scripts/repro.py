"""Reproduce every checker finding's counterexample (the exact inputs quoted in audit/AUDIT.md).

Usage (Git Bash, from W):
  NLTK_DATA=$PWD/case/deps/nltk_data .venv/Scripts/python.exe audit/scripts/repro.py [F04 ...]
Prints, per case: the grader's strict verdict, the reference's strict verdict, the contract label,
and OK when the grader's verdict is the one AUDIT.md reports.
"""
import hashlib
import json
import sys

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402

KW5 = {"keyword1": "quickly", "keyword2": "transform", "keyword3": "abundant", "keyword4": "bridge", "keyword5": "through"}
CAPS28 = ("Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, "
          "Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, "
          "Chisinau, Bern, Ljubljana, Zagreb")
REV_JUNK = "Zimbabwe\n" + "\n".join(f"Y{chr(122 - i // 26)}{chr(122 - i % 26)}" for i in range(51))
CSV_SPECIAL = "\n".join(["ProductID,Category,Brand,Price,Stock", '1,"Tools & Hardware",Acme,11.99,3']
                        + [f"{i},Tools,Acme,{10 + i}.99,{i * 3}" for i in range(2, 5)] + ["5,Tools,Acme"]
                        + [f"{i},Tools,Acme,{10 + i}.99,{i * 3}" for i in range(6, 15)])
CSV_QUOTES = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t\t"A"\t"Fall"\t"95"\n'
              '"2"\t"Art"\t"B"\t"Spring"\t"88"\n"3"\t"Music"\t"A"\t"Fall"\t"91"')
SPAN = {"prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. ", "n_start": 10, "n_end": 12}
ANIM = ["Alice", "Bears", "Cats", "Dogs", "Eagles", "Foxes", "Goats", "Horses", "Ibises", "Jaguars", "Koalas", "Lions",
        "Mice", "Newts", "Owls", "Pigs", "Quails", "Rats", "Snakes", "Tigers", "Unicorns", "Vultures", "Wolves",
        "Xerus", "Yaks", "Zebras"]
JPEG = "Write a python program to implement a simple JPEG compression algorithm without any errors."

# id: (instruction id, kwargs, response, grader verdict AUDIT.md reports, contract label)
CASES = {
    "F01a": ("repeat:repeat_span", SPAN, "d w", True, False),
    "F01b": ("repeat:repeat_span", SPAN, "on a certain", False, True),
    "F02": ("ratio:sentence_words", {}, "Cats nap daily. Dogs nap often. Fish swim fast.", True, False),
    "F03": ("count:keywords_multiple", KW5, "quickly. transform transform. abundant abundant abundant. bridge bridge "
            "bridge bridge bridge. through through through through through through throughout.", True, False),
    "F04": ("count:conjunctions", {"small_n": 3}, "Tea and, And coffee and.", True, False),
    "F05a": ("ratio:sentence_type", {}, "Wow! Amazing!", True, False),
    "F05b": ("ratio:sentence_balance", {}, "hello there", True, False),
    "F06": ("sentence:alliteration_increment", {}, "Silly snakes slither. Big bad dogs dig.", True, False),
    "F07": ("format:newline", {}, "Hello world\n \nfoo", True, False),
    "F08": ("format:line_indent", {}, "a\n\tb\n\t\tc", False, True),
    "F09a": ("format:quote_unquote", {}, "He said \u201ccarpe diem\u201d.", True, False),
    "F09b": ("format:quote_unquote", {}, "\"A\". \"B\" means b.", True, False),
    "F10": ("format:list", {"sep": "-"}, "I am well-known and up-to-date.", True, False),
    "F11": ("format:thesis", {}, "## A\n<i>Thesis one.</i> Body.\n\n## B\nNo thesis here.", True, False),
    "F12a": ("format:sub-bullets", {}, "Hello world.", True, False),
    "F12b": ("format:sub-bullets", {}, "* **Bold** point\n  - detail", False, True),
    "F13a": ("format:no_bullets_bullets", {}, "This is first! This is second!\n* one\n* two", True, False),
    "F13b": ("format:no_bullets_bullets", {}, "This is first.\n\nThis is second.\n* one\n* two", False, True),
    "F14": ("custom:character_reverse", {}, "The bald eagle (elgae dlab).", True, False),
    "F15": ("custom:reverse_newline", {}, REV_JUNK, True, False),
    "F16": ("custom:european_capitals_sort", {}, CAPS28, False, True),
    "F17": ("custom:csv_special_character", {}, CSV_SPECIAL, True, False),
    "F18a": ("custom:csv_quotes", {}, CSV_QUOTES, "ERR:IndexError", False),
    "F18b": ("custom:csv_city", {}, "a\rb", "ERR:Error", False),
    "F19": ("custom:date_format_list", {}, "1796-00-00, 1796-05-10", True, False),
    "F20a": ("format:title_case", {}, "War and Peace in the Valley", False, True),
    "F20b": ("format:title_case", {}, "It Doesn't Matter", False, True),
    "F21a": ("format:output_template", {}, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", True, False),
    "F21b": ("format:output_template", {}, "Future Outlook: Z My Conclusion: Y My Answer: X", True, False),
    "F22": ("repeat:repeat_change", {"prompt_to_repeat": JPEG}, JPEG.replace("Write a", "Write  a"), True, False),
    "F23": ("format:options", {"options": "a), b), c), d)"}, "B)", False, True),
    "F24": ("format:parentheses", {}, "((((()", True, False),
    "F25": ("words:prime_lengths", {}, "It is \u2014 an old oak.", False, True),
    "F26a": ("words:last_first", {}, "I like cats. Cats, they say, are great.", False, True),
    "F26b": ("words:paragraph_last_first", {}, "Open, she said, is open\nSets are sets", False, True),
    "F27": ("format:emoji", {}, "I love the USA \U0001F1FA\U0001F1F8. It is big \U0001F600.", False, True),
    "F28": ("words:start_verb", {}, "Imagine an empire of endless pain.", False, True),
    "F29": ("custom:sentence_alphabet", {}, '"' + " ".join(f"{a} walked home." for a in ANIM).replace("Alice walked home.", 'Alice walked home."', 1), False, True),
    "F30": ("words:words_position", {"keyword": "vibrant"}, "A vibrant day is vibrant today!)", False, True),
    "L1a": ("format:sub-bullets", {}, "* One\n* Two", False, False),
    "L1b": ("words:words_position", {"keyword": "vibrant"}, "Here is my answer:\nA vibrant scene with vibrant colors.", False, False),
}
LOOSE = {"L1a": True, "L1b": True}  # grader loose verdicts reported


def show(v):
    return v if not isinstance(v, str) else v.split(":")[0] + ":" + v.split(":")[1]


if __name__ == "__main__":
    want = sys.argv[1:] or list(CASES)
    bad = 0
    for cid in want:
        iid, kw, resp, expect, label = CASES[cid]
        g = graders.grader_strict(iid, kw, "p", resp)
        r = graders.reference_strict(iid, kw, "p", resp)
        ok = show(g) == expect
        extra = ""
        if cid in LOOSE:
            gl = graders.grader_loose(iid, kw, "p", resp)
            ok = ok and gl == LOOSE[cid]
            extra = f" grader_loose={gl}"
        bad += not ok
        h = hashlib.sha256(resp.encode("utf-8")).hexdigest()[:12]
        print(f"{cid:5s} {iid:31s} grader_strict={show(g)!s:15s} reference_strict={show(r)!s:15s} contract={'pass' if label else 'fail'}"
              f"{extra}  input_sha256={h}  {'OK' if ok else 'MISMATCH'}")
        if len(sys.argv) > 1:
            print("      kwargs:", json.dumps(kw), "\n      response:", json.dumps(resp, ensure_ascii=True))
    print("all reported verdicts reproduced" if not bad else f"{bad} MISMATCHES")
