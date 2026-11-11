"""Step 4: metamorphic tests.

Ignored edits (the contract's verdict must not change) are applied to every passing fixture
of every check whose contract ignores the edit; word edits go on the first word and on the
last word of the response. Forbidden edits (the verdict must become fail) are applied where
a simple one exists. Grades with the grader, the reference and the replacement, and writes
audit/work/metamorphic.json plus a summary on stdout.
"""
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import graders as G  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")

WORD_CHECKS = {
    "count:conjunctions", "count:keywords_multiple", "count:person_names", "count:pronouns",
    "count:unique_word_count", "count:word_count_range", "count:numbers",
    "sentence:alliteration_increment", "sentence:increment", "sentence:keyword",
    "words:alphabet", "words:consonants", "words:keywords_specific_position", "words:last_first",
    "words:no_consecutive", "words:odd_even_syllables", "words:palindrome", "words:paragraph_last_first",
    "words:prime_lengths", "words:repeats", "words:start_verb", "words:vowel", "words:words_position",
    "ratio:sentence_balance", "ratio:sentence_type", "ratio:stop_words", "ratio:overlap",
    "format:emoji", "format:title_case", "format:newline", "format:list", "format:sub-bullets",
    "format:no_bullets_bullets", "format:thesis", "format:line_indent", "format:parentheses",
    "format:quotes", "format:quote_unquote", "format:no_whitespace", "format:output_template",
}
LINE_LABEL_OK = {c for c in WORD_CHECKS if c not in {
    "count:numbers", "format:list", "format:sub-bullets", "format:no_bullets_bullets", "format:thesis",
    "format:line_indent", "format:output_template", "format:no_whitespace", "format:newline"}}
BULLET_OK = LINE_LABEL_OK | {"count:numbers"}
BLANK_LINE_OK = {c for c in WORD_CHECKS if c not in {"format:thesis", "format:no_whitespace", "words:vowel"}} | {
    "custom:mcq_count_length", "custom:reverse_newline", "repeat:repeat_change", "repeat:repeat_span",
    "repeat:repeat_simple"}
TYPO_QUOTE_OK = WORD_CHECKS - {"format:quotes", "format:quote_unquote", "ratio:sentence_words"}
APOS_OK = WORD_CHECKS | {"count:punctuation", "format:options"}
PUNCT_AFTER_OK = WORD_CHECKS - {"format:newline", "format:no_whitespace"}
MARKUP_OK = WORD_CHECKS - {"format:no_whitespace"}
HTML_OK = MARKUP_OK - {"format:newline"}
TRAILING_NL_OK = None  # every check


def _word_spans(text):
    """Word spans outside HTML tags, skipping pure-digit words (an edit must not split a number)."""
    tags = [(m.start(), m.end()) for m in re.finditer(r"<[^<>]*>", text)]
    out = []
    for m in WORD.finditer(text):
        if any(a <= m.start() < b for a, b in tags) or m.group(0).isdigit():
            continue
        out.append((m.start(), m.end()))
    return out


def wrap_word(text, which, left, right):
    sp = _word_spans(text)
    if not sp:
        return None
    a, b = sp[0] if which == "first" else sp[-1]
    return text[:a] + left + text[a:b] + right + text[b:]


def punct_after(text, which):
    sp = _word_spans(text)
    if not sp:
        return None
    a, b = sp[0] if which == "first" else sp[-1]
    if b < len(text) and not text[b].isspace():
        return None  # already followed by punctuation
    return text[:b] + "," + text[b:]


def per_line(text, fn):
    lines = text.split("\n")
    out, k = [], 0
    for l in lines:
        if l.strip():
            k += 1
            out.append(fn(k, l))
        else:
            out.append(l)
    return "\n".join(out)


def typo_apostrophe(text):
    if not re.search(r"[^\W_]'[^\W_]", text):
        return None
    return re.sub(r"(?<=[^\W_])'(?=[^\W_])", "’", text)


EDITS = {
    "numbered_label": (LINE_LABEL_OK, lambda t: per_line(t, lambda k, l: f"{k}. {l}")),
    "bullet_dash": (BULLET_OK, lambda t: per_line(t, lambda k, l: f"- {l}")),
    "bold_first": (MARKUP_OK, lambda t: wrap_word(t, "first", "**", "**")),
    "bold_last": (MARKUP_OK, lambda t: wrap_word(t, "last", "**", "**")),
    "italic_first": (MARKUP_OK, lambda t: wrap_word(t, "first", "*", "*")),
    "italic_last": (MARKUP_OK, lambda t: wrap_word(t, "last", "*", "*")),
    "html_first": (HTML_OK, lambda t: wrap_word(t, "first", "<b>", "</b>")),
    "html_last": (HTML_OK, lambda t: wrap_word(t, "last", "<b>", "</b>")),
    "typo_quotes_first": (TYPO_QUOTE_OK, lambda t: wrap_word(t, "first", "“", "”")),
    "typo_quotes_last": (TYPO_QUOTE_OK, lambda t: wrap_word(t, "last", "“", "”")),
    "typo_apostrophe": (APOS_OK, typo_apostrophe),
    "comma_after_first": (PUNCT_AFTER_OK, lambda t: punct_after(t, "first")),
    "comma_after_last": (PUNCT_AFTER_OK, lambda t: punct_after(t, "last")),
    "blank_line_between": (BLANK_LINE_OK, lambda t: t.replace("\n", "\n\n") if "\n" in t.strip() else None),
    "trailing_newline": (None, lambda t: t + "\n"),
}

# (check, edit) pairs where the edit changes what the contract reads, so it is not ignored
SKIP = {
    ("format:output_template", "html_first"), ("format:output_template", "typo_quotes_first"),
    ("format:output_template", "comma_after_first"),
    ("count:keywords_multiple", "numbered_label"),  # labels add no keyword
    ("words:alphabet", "numbered_label"), ("words:alphabet", "bullet_dash"),
}

# forbidden edits: (check, function) -> the edited response must FAIL
FORBIDDEN = {
    "count:word_count_range": lambda t, kw: t + " " + " ".join(["extra"] * (int(kw["max_words"]) + 1)),
    "count:numbers": lambda t, kw: t + " 77",
    "count:unique_word_count": lambda t, kw: " ".join([WORD.findall(t)[0]] * 3),
    "count:conjunctions": lambda t, kw: re.sub(r"(?i)\b(and|but|or|so|for|nor|yet)\b", "with", t),
    "format:no_whitespace": lambda t, kw: t[:1] + " " + t[1:],
    "format:title_case": lambda t, kw: re.sub(r"\bRise\b", "rise", t) if "Rise" in t else None,
    "format:options": lambda t, kw: t + " because it is clear.",
    "format:output_template": lambda t, kw: "Intro text. " + t,
    "format:emoji": lambda t, kw: t + " One more sentence.",
    "format:line_indent": lambda t, kw: t + "\nback to the margin",
    "format:newline": lambda t, kw: t + "\ntwo words",
    "format:sub-bullets": lambda t, kw: t + "\n* bullet without sub-bullet",
    "format:list": lambda t, kw: t + "\n* a starred item",
    "format:quote_unquote": lambda t, kw: t + ' "a final quote"',
    "words:repeats": lambda t, kw: t + " " + " ".join(["again"] * (int(kw["small_n"]) + 1)),
    "words:prime_lengths": lambda t, kw: t + " I",
    "words:consonants": lambda t, kw: t + " a",
    "words:no_consecutive": lambda t, kw: t + " zebra zoo",
    "words:palindrome": lambda t, kw: " ".join(t.split()[:9]),
    "words:vowel": lambda t, kw: t + " Our unique union.",
    "words:words_position": lambda t, kw: t + " extra words here",
    "words:start_verb": lambda t, kw: "The " + t,
    "sentence:keyword": lambda t, kw: "Opening sentence here. " + t,
    "sentence:increment": lambda t, kw: t + " One.",
    "ratio:stop_words": lambda t, kw: t + " " + " ".join(["the of and to in"] * 10),
    "ratio:sentence_type": lambda t, kw: t + " Is it?",
    "ratio:sentence_balance": lambda t, kw: t + " Indeed it is.",
    "repeat:repeat_simple": lambda t, kw: t + " Done.",
    "repeat:repeat_change": lambda t, kw: t + " Here is the answer.",
    "custom:multiples": lambda t, kw: t + ", 56",
    "custom:date_format_list": lambda t, kw: t + ", 1805/12/02",
    "custom:csv_city": lambda t, kw: (t[:t.rstrip().rfind("```")] + "9,Peru,Lima,2020,5\n```"
                                      if t.rstrip().endswith("```") else t + "\n9,Peru,Lima,2020,5"),
}


def g(fn, f, resp):
    try:
        return "pass" if fn(f["check"], f["kwargs"], resp) else "fail"
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__


rows = []
for f in FIXTURES:
    if f["label"] != "pass":
        continue
    for name, (ok, fn) in EDITS.items():
        if (ok is not None and f["check"] not in ok) or (f["check"], name) in SKIP:
            continue
        t2 = fn(f["response"])
        if t2 is None or t2 == f["response"]:
            continue
        rows.append({"kind": "ignored", "edit": name, "fixture": f["id"], "check": f["check"],
                     "expect": "pass", "edited": t2,
                     "grader_orig": g(G.grade_grader, f, f["response"]), "reference_orig": g(G.grade_reference, f, f["response"]),
                     "grader": g(G.grade_grader, f, t2), "reference": g(G.grade_reference, f, t2),
                     "replacement": g(G.grade_replacement, f, t2)})
    if f["check"] in FORBIDDEN:
        t2 = FORBIDDEN[f["check"]](f["response"], f["kwargs"])
        if t2 is not None and t2 != f["response"]:
            rows.append({"kind": "forbidden", "edit": "forbidden", "fixture": f["id"], "check": f["check"],
                         "expect": "fail", "edited": t2,
                         "grader_orig": g(G.grade_grader, f, f["response"]), "reference_orig": g(G.grade_reference, f, f["response"]), "reference_orig": g(G.grade_reference, f, f["response"]),
                         "grader": g(G.grade_grader, f, t2), "reference": g(G.grade_reference, f, t2),
                         "replacement": g(G.grade_replacement, f, t2)})

json.dump(rows, open(os.path.join(W, "audit", "work", "metamorphic.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for who in ["grader", "reference", "replacement"]:
    # a flip counts only when the grader under test passed (ignored) / handled the original correctly
    orig_key = {"grader": "grader_orig", "reference": "reference_orig", "replacement": None}[who]
    bad = [r for r in rows if r[who] != r["expect"] and (orig_key is None or r[orig_key] == "pass")]
    print(f"== {who}: {len(bad)} wrong of {len(rows)} edited responses")
    by = {}
    for r in bad:
        by.setdefault((r["check"], r["edit"]), []).append(r)
    if "-v" in sys.argv or who != "reference":
        for (c, e), rs in sorted(by.items()):
            print(f"   {c:36s} {e:20s} {len(rs)}  e.g. {rs[0]['fixture']}: {rs[0]['edited'][:70]!r}")
