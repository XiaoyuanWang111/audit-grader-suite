"""Step 4 metamorphic tests: edits the contract ignores, applied to every
passing fixture of every check whose contract ignores that edit.

For each (fixture labeled pass, edit) with the edit ignored by the check's
contract, grade original and edited response with grader, reference and
replacement. A verdict that changes is a wrong verdict on one of the two.
Writes audit/work/metamorphic.json and prints a summary.
"""
import collections
import json
import re

import common
import ref_runner
import replacement
from tests.fixtures_data import FIX


def _second_word_wrap(t, a, b):
    toks = re.split(r"(\s+)", t)
    idx = [i for i, x in enumerate(toks) if x.strip() and re.search(r"[^\W_]", x)]
    if len(idx) < 2:
        return None
    i = idx[1]
    m = re.match(r"^(\W*)([\w'\-]+)(\W*)$", toks[i])
    if not m:
        return None
    toks[i] = m.group(1) + a + m.group(2) + b + m.group(3)
    return "".join(toks)


def _typo(t):
    if "'" not in t and '"' not in t:
        return None
    out, open_d = [], True
    for i, c in enumerate(t):
        if c == '"':
            out.append("“" if open_d else "”")
            open_d = not open_d
        elif c == "'":
            prev = t[i - 1] if i else " "
            out.append("’" if prev.isalnum() else "‘")
        else:
            out.append(c)
    return "".join(out)


def _punct_after(t):
    return _second_word_wrap(t, "", ",") if not re.search(r"^\S+\s+\S+[,.;:!?]", t) else None


def _blank(t):
    if "\n" not in t.strip():
        return None
    i = t.index("\n")
    return t[:i] + "\n" + t[i:]


EDITS = {
    "label": lambda t: None if re.match(r"^\s*(?:[-*]|\d+[.)])\s", t) else "- " + t,
    "bold": lambda t: _second_word_wrap(t, "**", "**"),
    "italic": lambda t: _second_word_wrap(t, "_", "_"),
    "html": lambda t: _second_word_wrap(t, "<b>", "</b>"),
    "typo_quotes": _typo,
    "punct_after": _punct_after,
    "blank_line": _blank,
    "trailing_newline": lambda t: t + "\n",
}

# Checks whose contract does NOT ignore an edit (or where it is ambiguous): skipped for that edit.
STRUCT = {"format:sub-bullets", "format:no_whitespace", "format:options", "format:output_template", "format:thesis",
          "repeat:repeat_change", "repeat:repeat_simple", "repeat:repeat_span", "custom:csv_city", "custom:csv_quotes",
          "custom:csv_special_character", "custom:date_format_list", "custom:european_capitals_sort",
          "custom:mcq_count_length", "custom:character_reverse", "custom:word_reverse", "ratio:sentence_words",
          "format:no_bullets_bullets", "format:list"}
SKIP = {
    "label": STRUCT | {"format:line_indent"},
    "bold": STRUCT | {"format:parentheses", "format:quotes", "format:quote_unquote", "ratio:overlap",
                      "count:punctuation", "format:title_case"} - {"format:no_bullets_bullets", "format:list"},
    "italic": STRUCT | {"count:punctuation", "ratio:overlap"} - {"format:no_bullets_bullets", "format:list"},
    "html": STRUCT | {"count:punctuation", "format:parentheses", "ratio:overlap"} - {"format:no_bullets_bullets", "format:list"},
    "typo_quotes": {"custom:csv_city", "custom:csv_quotes", "custom:csv_special_character", "repeat:repeat_change",
                    "repeat:repeat_span", "ratio:sentence_words"},
    "punct_after": STRUCT | {"count:punctuation", "ratio:sentence_words", "count:numbers", "format:newline"} - {"format:no_bullets_bullets", "format:list"},
    "blank_line": {"format:no_whitespace", "format:thesis", "words:vowel", "custom:csv_city", "custom:csv_quotes",
                   "custom:csv_special_character", "repeat:repeat_simple", "custom:character_reverse",
                   "custom:word_reverse", "custom:date_format_list", "custom:european_capitals_sort"},
    "trailing_newline": set(),
}
DECISION_EDITS = {("trailing_newline", "format:no_whitespace"): "D-strip-ends",
                  ("blank_line", "custom:mcq_count_length"): None}

graders = {"grader": common.grade_grader, "reference": ref_runner.grade_reference, "replacement": replacement.grade}
rows = []
for f in FIX:
    if f["label"] != "pass":
        continue
    kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
    for en, fn in EDITS.items():
        if f["check"] in SKIP[en]:
            continue
        e = fn(f["response"])
        if e is None or e == f["response"]:
            continue
        for gn, g in graders.items():
            try:
                v0 = g(f["check"], kw, prompt, f["response"])
                v1 = g(f["check"], kw, prompt, e)
            except Exception as ex:  # noqa: BLE001
                v0, v1 = "err", "error:" + type(ex).__name__
            if v0 is True and v1 is not True:
                rows.append(dict(grader=gn, check=f["check"], fixture=f["id"], edit=en, original=f["response"],
                                 edited=e, after=str(v1), decision=DECISION_EDITS.get((en, f["check"]))))
(common.W / "audit" / "work" / "metamorphic.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False),
                                                              encoding="utf-8", newline="\n")
by = collections.defaultdict(set)
for r in rows:
    by[(r["grader"], r["edit"])].add(r["check"])
for (g, e), cs in sorted(by.items()):
    print(f"{g:<12} {e:<17} {len(cs):>2} checks: {', '.join(sorted(cs))}")
