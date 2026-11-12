"""Step 4 property and metamorphic fixtures.

Ignored edits (label stays pass) are applied to every passing hand fixture of each check whose
contract ignores the edit; forbidden edits (label becomes fail) to the checks whose contract they
break. Writes audit/work/property_fixtures.jsonl for build_fixtures.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(W / "audit" / "tests"))
from fixture_defs import FIXTURES  # noqa: E402
sys.path.insert(0, str(HERE))
from fixture_lib import fixture_id  # noqa: E402

OUT = W / "audit" / "work" / "property_fixtures.jsonl"

ALL = sorted({f[0] for f in FIXTURES})
KEYWORDISH = {"keywords:existence", "keywords:forbidden_words", "keywords:frequency", "keywords:word_once",
              "keywords:word_count_different_numbers", "keywords:letter_frequency", "letters:letter_counting2",
              "change_case:capital_word_frequency", "detectable_content:number_placeholders",
              "detectable_format:title", "punctuation:no_comma", "punctuation:punctuation_exclamation"}
SENTENCEISH = {"first_word:first_word_sent", "last_word:last_word_sent", "length_constraints:number_sentences",
               "keywords:keyword_specific_position"}
WORDISH = {"first_word:first_word_answer", "last_word:last_word_answer", "length_constraints:number_words",
           "count:count_unique", "keywords:no_adjacent_consecutive", "keywords:palindrome",
           "count:lowercase_counting", "letters:letter_counting"}

# Which ignored edit applies to which check (contract reasoning in the comments).
APPLIES = {
    # D-strip (proposed): trailing whitespace is not part of the answer.
    "trailing_newline": set(ALL),
    # Blank lines between lines: only paragraph- and line-layout checks read them.
    "blank_lines": set(ALL) - {"paragraphs:paragraphs2", "length_constraints:nth_paragraph_first_word",
                               "detectable_format:sentence_hyphens", "detectable_content:postscript",
                               "count:counting_composition", "combination:two_responses",
                               "detectable_format:json_format", "startend:quotation"},
    # A "- " bullet is neither a word nor a letter.
    "bullet_prefix": KEYWORDISH | SENTENCEISH | WORDISH | {"punctuation:punctuation_dot",
                                                           "startend:end_checker", "change_case:english_lowercase",
                                                           "change_case:english_capital", "keywords:start_end"},
    # A "1." list label is neither a letter nor part of a sentence; it adds a digit word and a dot.
    "number_prefix": (KEYWORDISH | {"first_word:first_word_sent", "last_word:last_word_sent",
                                    "keywords:keyword_specific_position", "last_word:last_word_answer",
                                    "keywords:no_adjacent_consecutive", "count:lowercase_counting",
                                    "letters:letter_counting", "startend:end_checker"}),
    # Markup around the first and the last word (bold, italics, HTML tag).
    "markup_first": (KEYWORDISH | SENTENCEISH | WORDISH | {"first_word:first_word_answer"}) - {"keywords:palindrome", "detectable_format:title"},
    "markup_last": (KEYWORDISH | {"last_word:last_word_answer", "length_constraints:number_words",
                                  "count:count_unique", "keywords:no_adjacent_consecutive",
                                  "count:lowercase_counting", "letters:letter_counting",
                                  "first_word:first_word_answer"}) - {"detectable_format:title"},
    # Typographic quotation marks around the first word, typographic apostrophe in a word.
    "typo_quotes_first": KEYWORDISH | SENTENCEISH | WORDISH | {"first_word:first_word_answer"},
    "typo_apostrophe": set(ALL) - {"startend:quotation", "detectable_format:json_format",
                                   "detectable_format:constrained_response", "startend:end_checker",
                                   "copy:repeat_phrase", "letters:letter_counting"},
    # Punctuation directly after the first word.
    "punct_after_first": {"first_word:first_word_answer", "first_word:first_word_sent",
                          "keywords:existence", "keywords:frequency", "keywords:word_once",
                          "keywords:keyword_specific_position", "length_constraints:number_words",
                          "keywords:letter_frequency", "letters:letter_counting2",
                          "keywords:no_adjacent_consecutive", "count:count_unique"},
}

FIRST = re.compile(r"^(\W*?)([^\W_]+(?:['’\-][^\W_]+)*)")
LAST = re.compile(r"([^\W_]+(?:['’\-][^\W_]+)*)(\W*)$")


def per_line(text, prefix_fn):
    lines = text.split("\n")
    return "\n".join(prefix_fn(i) + line if line.strip() else line for i, line in enumerate(lines))


def wrap_first(text, left, right):
    m = FIRST.match(text)
    if not m:
        return None
    return text[: m.start(2)] + left + m.group(2) + right + text[m.end(2):]


def wrap_last(text, left, right):
    m = LAST.search(text)
    if not m:
        return None
    return text[: m.start(1)] + left + m.group(1) + right + text[m.end(1):]


def edits(text):
    yield "trailing_newline", text + "\n"
    if "\n" in text:
        yield "blank_lines", text.replace("\n", "\n\n")
    yield "bullet_prefix", per_line(text, lambda i: "- ")
    yield "number_prefix", per_line(text, lambda i: f"{i + 1}. ")
    for name, left, right in (("bold", "**", "**"), ("italic", "*", "*"), ("html", "<b>", "</b>")):
        e = wrap_first(text, left, right)
        if e:
            yield "markup_first", e
        e = wrap_last(text, left, right)
        if e:
            yield "markup_last", e
    e = wrap_first(text, "“", "”")
    if e:
        yield "typo_quotes_first", e
    if "'" in text:
        yield "typo_apostrophe", text.replace("'", "’")
    m = FIRST.match(text)
    if m and not text[m.end(2):m.end(2) + 1] in (",", ".", ";", ":", "!", "?"):
        yield "punct_after_first", text[: m.end(2)] + "," + text[m.end(2):]


# Forbidden edits: (check, function on text) -> the edited response breaks the contract.
FORBIDDEN = {
    "punctuation:no_comma": lambda t: t + " Yes, really",
    "punctuation:punctuation_dot": lambda t: t + " See 3.5",
    "punctuation:punctuation_exclamation": lambda t: t + " Wow!",
    "startend:end_checker": lambda t: t + " Thanks.",
    "startend:quotation": lambda t: t.strip()[:-1],
    "first_word:first_word_answer": lambda t: "Well " + t,
    "last_word:last_word_answer": lambda t: t + " Goodbye.",
    "change_case:english_capital": lambda t: t + " ok",
    "change_case:english_lowercase": lambda t: t + " OK",
    "keywords:start_end": lambda t: t + ".",
    "detectable_format:title": lambda t: t.replace("<<", "").replace(">>", ""),
    "detectable_format:square_brackets": lambda t: t + " extra",
    "detectable_format:constrained_response": lambda t: t + " Maybe.",
    "detectable_format:json_format": lambda t: t + " trailing",
    "length_constraints:number_words": lambda t: " ".join(t.split()[:-1]),
}


def main():
    rows = []
    for iid, kw, resp, label, note in FIXTURES:
        if label != "pass":
            continue
        for name, edited in edits(resp):
            if iid in APPLIES[name] and edited != resp:
                rows.append({"source": "property", "instruction_id": iid, "kwargs": kw, "response": edited,
                             "label": "pass", "note": f"ignored edit {name} of: {note}", "reasoning_model": False,
                             "base_id": fixture_id(iid, kw, resp), "edit": name})
        if iid in FORBIDDEN:
            edited = FORBIDDEN[iid](resp)
            if edited != resp:
                rows.append({"source": "property", "instruction_id": iid, "kwargs": kw, "response": edited,
                             "label": "fail", "note": f"forbidden edit of: {note}", "reasoning_model": False,
                             "base_id": fixture_id(iid, kw, resp), "edit": "forbidden"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(rows), "property fixtures")


if __name__ == "__main__":
    main()
