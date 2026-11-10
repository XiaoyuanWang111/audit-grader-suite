"""Reproduce each finding's counterexample: prints the grader's verdict, the reference's verdict
and the contract's label for the exact input.

Usage (Git Bash, from W = <W>):
  NLTK_DATA=case/deps/nltk_data PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe audit/repro.py F03
  ... audit/repro.py all
"grader" uses kwargs exactly as eval_instruct.load_questions builds them from the HF parquet
(floats); "grader_int" casts them to int. A key=K argument takes kwargs and prompt from dataset row K.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, os.path.join(HERE, "tests"))
import harness as H  # noqa: E402
from fixtures_data import AFRICA_REV, CAPITALS, CAPITALS_NO_KYIV, CSV_QUOTES_EMPTY_FIELD, CSV_SPECIAL_SHORT_ROWS, KW_DOOR_DOORWAY, KW_OUTDOOR_ONLY  # noqa: E402,E501

# finding: [(check, key, kwargs, response, contract label, mode)]
CASES = {
    "F01": [("repeat:repeat_span", 284, None, "code and theory behind", True, "strict"),
            ("words:keywords_specific_position", None, {"keyword": "giggle", "n": 2.0, "m": 3.0}, "I sat. Then we giggle loudly.", True, "strict")],
    "F02": [("repeat:repeat_span", 284, None, "code and theory behind", True, "strict"),
            ("repeat:repeat_span", 284, None, "lain", False, "strict")],
    "F03": [("count:keywords_multiple", 2, None, KW_DOOR_DOORWAY, True, "strict"),
            ("count:keywords_multiple", 2, None, KW_OUTDOOR_ONLY, False, "strict")],
    "F04": [("ratio:sentence_words", None, {}, "Cats nap. Cats nap. Cats nap.", False, "strict")],
    "F05": [("words:words_position", None, {"keyword": "vibrant"}, "Truly, vibrant cities have vibrant streets.", True, "strict")],
    "F06": [("custom:sentence_alphabet", 282, None, None, True, "strict")],  # response built below
    "F07": [("format:title_case", None, {}, "The Lord of the Rings Is a Great Book", True, "strict"),
            ("format:title_case", None, {}, "Don't Stop Believing", True, "strict")],
    "F08": [("format:sub-bullets", None, {}, "Plain text without bullets.", False, "strict"),
            ("format:sub-bullets", None, {}, "* **Fruit**\n  - Apple\n* Veg\n  - Leek", True, "strict"),
            ("format:sub-bullets", None, {}, "* A well-known fruit\n* A self-made veg", False, "strict")],
    "F09": [("format:list", None, {"sep": "-"}, "A well-known, state-of-the-art plan.", False, "strict"),
            ("format:list", None, {"sep": "SEPARATOR"}, "* SEPARATOR apples\n* SEPARATOR pears", False, "strict")],
    "F10": [("format:output_template", None, {}, "My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]", False, "strict"),
            ("format:output_template", None, {}, "Future Outlook: It will grow. My Conclusion: It matters. My Answer: It is vast.", False, "strict")],
    "F11": [("format:thesis", None, {}, "Cats purr a lot. <i>Cats are the best pets.</i> More text.", False, "strict"),
            ("format:thesis", None, {}, "## One\n<i>Thesis one.</i> Text.\n## Two\nNo thesis here.", False, "strict"),
            ("format:thesis", None, {}, "<i>Cats rule.</i>", True, "strict"),
            ("format:thesis", None, {}, "<em>Cats rule.</em>", True, "strict")],
    "F12": [("count:punctuation", None, {}, "Wait?! Really; yes: go, now. Why? Stop!", False, "strict")],
    "F13": [("count:conjunctions", None, {"small_n": 3.0}, "I came and saw. And I stayed and, sadly, left.", False, "strict")],
    "F14": [("count:pronouns", None, {"N": 5.0}, "This book and that pen sit on each desk, with all chairs and some tables.", False, "strict")],
    "F15": [("count:numbers", None, {"N": 2.0}, "It takes 5-7 days.", True, "strict")],
    "F16": [("count:unique_word_count", None, {"N": 5.0}, "Red green blue yellow - red", False, "strict"),
            ("count:unique_word_count", None, {"N": 5.0}, "\u201cRed\u201d red green blue yellow", False, "strict")],
    "F17": [("count:words_japanese", None, {"N": 2.0}, "Hello 2024 good \u65e5\u672c", False, "strict"),
            ("count:words_japanese", None, {"N": 2.0}, "Hello - \u4e16\u754c good \u65e5\u672c", True, "strict")],
    "F18": [("custom:character_reverse", 273, None, "The national symbol of the US is the elgae dlab.", False, "strict"),
            ("custom:word_reverse", 283, None, "The national symbol of the US is the eagle bald.", False, "strict")],
    "F19": [("custom:european_capitals_sort", 278, None, ", ".join(CAPITALS), True, "strict"),
            ("custom:european_capitals_sort", 278, None, ", ".join(CAPITALS_NO_KYIV), False, "strict")],
    "F20": [("custom:reverse_newline", 281, None, "\n".join(["Zimbabwe"] * 52), False, "strict")],
    "F21": [("custom:csv_special_character", 276, None, CSV_SPECIAL_SHORT_ROWS, False, "strict")],
    "F22": [("custom:csv_quotes", 275, None, CSV_QUOTES_EMPTY_FIELD, False, "strict")],
    "F23": [("custom:date_format_list", 277, None, "1796-00-12, 1805-12-00", False, "strict")],
    "F24": [("custom:mcq_count_length", 279, None, None, True, "strict")],  # built below
    "F25": [("format:emoji", None, {}, "Count 1\ufe0f\u20e3. Then 2\ufe0f\u20e3.", True, "strict"),
            ("format:emoji", None, {}, "Hello \U0001F1FA\U0001F1F8. Bye \U0001F1FA\U0001F1F8.", True, "strict")],
    "F26": [("format:line_indent", None, {}, "A\n\tB\n\t\tC", True, "strict"),
            ("format:line_indent", None, {}, "A\n B\n\n\n  C", True, "strict")],
    "F27": [("format:newline", None, {}, "Hello world\n \nagain", False, "strict")],
    "F28": [("format:no_bullets_bullets", None, {}, "This is one. This is two.\n\n* first\n\n* second", True, "strict"),
            ("format:no_bullets_bullets", None, {}, "This is one. This is two.\n* first\n* second\n", True, "strict"),
            ("format:no_bullets_bullets", None, {}, "Why not? Because!\n* first\n* second", False, "strict")],
    "F29": [("format:options", 102, None, "c)\n", True, "strict"),
            ("format:options", 100, None, "Yes\n", True, "strict")],
    "F31": [("format:quote_unquote", None, {}, "\"Apple\", \"Banana\", and \"Cherry\" are fruits.", False, "strict"),
            ("format:quote_unquote", None, {}, "He said \u201chello\u201d", False, "strict")],
    "F32": [("format:quotes", None, {}, "He said, \u201cShe told me, \u2018He yelled \u201cstop\u201d loudly\u2019 today\u201d again.", True, "strict")],
    "F33": [("ratio:sentence_balance", None, {}, "Rain falls \U0001F600", False, "strict"),
            ("ratio:sentence_type", None, {}, "Wow! Amazing!", False, "strict"),
            ("ratio:sentence_type", None, {}, "He said \"go.\" She said \"stop.\" Why?", True, "strict")],
    "F34": [("repeat:repeat_change", 60, None, "Write a python program to implement a simple JPEG compression algorithm without  any errors.", False, "strict")],
    "F35": [("sentence:alliteration_increment", None, {}, "Big bears bite fish. Red roses and tall trees grow.", False, "strict")],
    "F36": [("sentence:increment", None, {"small_n": 2.0}, "Cats nap. Cats nap \u2014 all day.", True, "strict"),
            ("words:alphabet", None, {}, "Apples bake \u2014 carefully daily.", True, "strict"),
            ("words:consonants", None, {}, "Strong stars \u2014 bright.", True, "strict"),
            ("words:no_consecutive", None, {}, "\u201cCats\u201d \u201clike\u201d mice.", True, "strict"),
            ("words:prime_lengths", None, {}, "We don\u2019t go.", False, "strict"),
            ("words:repeats", None, {"small_n": 2.0}, "Cats nap \u2014 dogs run \u2014 birds fly \u2014 fish swim.", True, "strict"),
            ("words:odd_even_syllables", None, {}, "Cat apple \u2014 dog.", True, "strict")],
    "F37": [("words:paragraph_last_first", None, {}, "Time, they say, heals all wounds over time.", True, "strict")],
    "F38": [("words:odd_even_syllables", None, {}, "Cat naive dog.", True, "strict")],
    "F42": [("format:sub-bullets", None, {}, "* Apples\n* Pears", False, "loose"),
            ("format:no_whitespace", None, {}, "Sure!\nabc", False, "loose"),
            ("words:start_verb", None, {}, "Here is my answer:\nImagine a world of peace.", False, "loose")],
}


def _build():
    from fixtures_data import ALPHA26, MCQ_NO_NUMBER
    CASES["F06"][0] = ("custom:sentence_alphabet", 282, None, " ".join(ALPHA26[:2] + ['"Cats chased crows."'] + ALPHA26[3:]), True, "strict")
    CASES["F24"][0] = ("custom:mcq_count_length", 279, None, MCQ_NO_NUMBER, True, "strict")


def run_f43():
    """F43: a stored completion whose reasoning never closes; the stored `response` (the whole
    completion, per CONFIGS.md) reaches the grader and passes a check. Prints counts, not the text."""
    path = os.path.join(os.path.dirname(HERE), "case", "panel", "Qwen__Qwen3-8B__thinking", "greedy.jsonl")
    rec = json.loads(open(path, encoding="utf-8").readlines()[8])
    resp, raw = rec["response"], rec["raw_response"]
    print(f"F43 count:conjunctions [strict] key=8 panel=Qwen__Qwen3-8B__thinking/greedy.jsonl line 9: "
          f"finish_reason={rec['finish_reason']} num_tokens={rec['num_tokens']} '<think>' in raw={'<think>' in raw} "
          f"'</think>' in raw={'</think>' in raw} response==raw={resp == raw}")
    g = H.grade("count:conjunctions", resp, key=8)
    r = H.grade("count:conjunctions", resp, key=8, impl="reference")
    print(f"    grader={g}  reference={r}  contract=False (G1: unclosed reasoning is an extraction failure)")


def run(fid):
    if fid == "F43":
        return run_f43()
    for check, key, kwargs, resp, label, mode in CASES[fid]:
        g = H.grade(check, resp, key=key, kwargs=kwargs, mode=mode)
        gi = H.grade(check, resp, key=key, kwargs=kwargs, mode=mode, int_cast=True)
        r = H.grade(check, resp, key=key, kwargs=kwargs, mode=mode, impl="reference")
        src = f"key={key}" if key is not None else f"kwargs={json.dumps(kwargs)}"
        shown = resp if len(resp) <= 120 else resp[:117] + "..."
        print(f"{fid} {check} [{mode}] {src} response={shown!r}")
        print(f"    grader={g}  grader_int={gi}  reference={r}  contract={label}")


if __name__ == "__main__":
    _build()
    ids = list(CASES) + ["F43"] if sys.argv[1:] in ([], ["all"]) else sys.argv[1:]
    for fid in ids:
        run(fid)
