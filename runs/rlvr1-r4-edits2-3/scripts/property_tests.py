"""Step 4: metamorphic (ignored edits) and property (forbidden edits) tests on all three graders.

Bases are the hand fixtures labeled pass (audit/fixtures_src.py, not raw). Each ignored edit
is applied to the base of every check whose contract ignores it (EXPECT tables below); the
label stays pass. Each forbidden edit makes a base fail. Labels come from the contracts by
construction; the replacement must reproduce them (a mismatch is printed and is a bug in
this script or in the replacement, not a grader finding).

Writes the cases to audit/fixtures.jsonl (source "metamorphic" / "property"), updates
audit/tests/known_failures.json, and prints wrong verdicts grouped by (grader, check, edit).
"""

import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
sys.path.insert(0, HERE)

import harness as h  # noqa: E402
import contract_grader as cg  # noqa: E402
from fixtures_src import FIXTURES  # noqa: E402
from build_fixtures import explaining_decisions  # noqa: E402

FIX_PATH = os.path.join(AUDIT, "fixtures.jsonl")
KNOWN = os.path.join(AUDIT, "tests", "known_failures.json")
WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")


def _wrap_nth(text, which, left, right):
    ms = list(WORD.finditer(text))
    if not ms:
        return None
    m = ms[0] if which == "first" else ms[-1]
    return text[: m.start()] + left + m.group(0) + right + text[m.end():]


def _after_nth(text, which, punct):
    ms = list(WORD.finditer(text))
    if not ms:
        return None
    m = ms[0] if which == "first" else ms[-1]
    return text[: m.end()] + punct + text[m.end():]


def _prefix_lines(text, fn):
    out, k = [], 0
    for line in text.split("\n"):
        if line.strip():
            k += 1
            out.append(fn(k) + line)
        else:
            out.append(line)
    return "\n".join(out)


def _blank_between(text):
    lines = [ln for ln in text.split("\n")]
    if sum(1 for ln in lines if ln.strip()) < 2:
        return None
    return "\n\n".join(ln for ln in lines if ln.strip())


def _apostrophe(text):
    if not re.search(r"\w'\w", text):
        return None
    return re.sub(r"(?<=\w)'(?=\w)", "’", text)


EDITS = {
    "numbered_label": lambda t: _prefix_lines(t, lambda k: f"{k}. "),
    "bullet": lambda t: _prefix_lines(t, lambda k: "- "),
    "bold_first": lambda t: _wrap_nth(t, "first", "**", "**"),
    "bold_last": lambda t: _wrap_nth(t, "last", "**", "**"),
    "italic_first": lambda t: _wrap_nth(t, "first", "*", "*"),
    "italic_last": lambda t: _wrap_nth(t, "last", "*", "*"),
    "html_first": lambda t: _wrap_nth(t, "first", "<b>", "</b>"),
    "html_last": lambda t: _wrap_nth(t, "last", "<b>", "</b>"),
    "tquote_first": lambda t: _wrap_nth(t, "first", "“", "”"),
    "tquote_last": lambda t: _wrap_nth(t, "last", "“", "”"),
    "tapostrophe": _apostrophe,
    "comma_after_first": lambda t: _after_nth(t, "first", ","),
    "semicolon_after_last": lambda t: _after_nth(t, "last", ";"),
    "blank_line_between_lines": _blank_between,
    "trailing_newline": lambda t: t + "\n",
}

ALL = set(cg.CHECKS)
SKIP_ALWAYS = {"detectable_format:json_format", "detectable_format:constrained_response", "language:response_language"}
LINE_PREFIX_OK = {
    "first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer",
    "last_word:last_word_sent", "keywords:keyword_specific_position", "length_constraints:number_sentences",
    "keywords:existence", "keywords:forbidden_words", "keywords:frequency", "keywords:word_count_different_numbers",
    "keywords:word_once", "keywords:letter_frequency", "letters:letter_counting2", "change_case:capital_word_frequency",
    "count:lowercase_counting", "punctuation:no_comma", "punctuation:punctuation_exclamation", "startend:end_checker",
    "keywords:palindrome", "keywords:no_adjacent_consecutive", "length_constraints:nth_paragraph_first_word",
    "keywords:start_end", "detectable_format:title", "copy:repeat_phrase", "detectable_format:sentence_hyphens",
    "count:count_unique", "change_case:english_capital", "change_case:english_lowercase", "letters:letter_counting",
    "combination:two_responses", "paragraphs:paragraphs2",
}
NO_HTML = {"change_case:english_capital", "detectable_format:bigram_wrapping", "detectable_format:title",
           "keywords:letter_frequency", "letters:letter_counting2", "letters:letter_counting",
           "count:lowercase_counting", "keywords:no_adjacent_consecutive", "count:count_unique",
           "detectable_format:number_highlighted_sections"}
WRAP_SKIP = {"detectable_format:multiple_sections", "startend:quotation"}


def expected(iid, edit):
    """'pass' (ignored edit), 'fail' (forbidden edit) or None (not applied)."""
    if iid in SKIP_ALWAYS and edit != "trailing_newline":
        return None
    if edit == "trailing_newline":
        return "pass"
    if edit == "numbered_label":
        if iid == "punctuation:punctuation_dot":
            return "fail"
        return "pass" if iid in LINE_PREFIX_OK else None
    if edit == "bullet":
        if iid == "startend:quotation":
            return "fail"
        ok = LINE_PREFIX_OK | {"punctuation:punctuation_dot", "length_constraints:number_words",
                               "detectable_format:bigram_wrapping", "detectable_format:square_brackets"}
        return "pass" if iid in ok else None
    if edit == "blank_line_between_lines":
        if iid in {"paragraphs:paragraphs2", "length_constraints:nth_paragraph_first_word",
                   "detectable_format:sentence_hyphens"}:
            return None
        return "pass"
    if edit in ("comma_after_first",):
        if iid == "punctuation:no_comma":
            return "fail"
        if iid in WRAP_SKIP | {"detectable_format:square_brackets", "copy:repeat_phrase"}:
            return None
        return "pass"
    if edit == "semicolon_after_last":
        if iid in {"keywords:start_end", "startend:end_checker"}:
            return "fail"
        if iid in WRAP_SKIP | {"detectable_format:square_brackets", "copy:repeat_phrase",
                               "detectable_format:sentence_hyphens", "count:counting_composition",
                               "detectable_format:bigram_wrapping", "detectable_content:postscript"}:
            return None
        return "pass"
    if edit == "tapostrophe":
        return "pass"
    # word wraps
    if iid in WRAP_SKIP:
        return None
    if edit.startswith("html") and iid in NO_HTML:
        return None
    if edit.endswith("_last") and iid in {"keywords:start_end", "startend:end_checker"}:
        return "fail"
    if iid == "detectable_format:number_highlighted_sections" and edit.startswith(("bold", "italic")):
        return None  # wrapping an emphasized word makes bold-italic markup; not an ignored edit
    return "pass"


# forbidden, check-specific edits: (name, function) -> label fail
def _kw_word(kw):
    return kw.get("keyword") or (kw.get("keywords") or [None])[0]


FORBIDDEN = {
    "punctuation:no_comma": [("add_comma", lambda t, kw: t.replace(" ", ", ", 1))],
    "punctuation:punctuation_dot": [("add_dot", lambda t, kw: t + " v2.0")],
    "punctuation:punctuation_exclamation": [("add_exclamation", lambda t, kw: t + "!")],
    "startend:end_checker": [("words_after_phrase", lambda t, kw: t + " Thanks.")],
    "keywords:start_end": [("period_after_last", lambda t, kw: t + ".")],
    "startend:quotation": [("drop_closing_quote", lambda t, kw: t.rstrip()[:-1])],
    "first_word:first_word_answer": [("prepend_word", lambda t, kw: "So " + t)],
    "last_word:last_word_answer": [("append_word", lambda t, kw: t + " indeed")],
    "first_word:first_word_sent": [("append_sentence", lambda t, kw: t + " They left.")],
    "last_word:last_word_sent": [("append_sentence", lambda t, kw: t + " They left.")],
    "combination:two_responses": [("third_response", lambda t, kw: t + "\n******\nA third answer.")],
    "detectable_format:number_bullet_lists": [("extra_bullet", lambda t, kw: t + "\n* extra")],
    "paragraphs:paragraphs2": [("third_paragraph", lambda t, kw: t + "\n\nThird paragraph.")],
    "paragraphs:paragraphs": [("third_paragraph", lambda t, kw: t + "\n***\nThird paragraph.")],
    "length_constraints:number_paragraphs": [("extra_paragraph", lambda t, kw: t + "\n***\nAnother paragraph.")],
    "length_constraints:nth_paragraph_first_word": [("extra_paragraph", lambda t, kw: t + "\n\nAnother paragraph.")],
    "detectable_format:title": [("unwrap_title", lambda t, kw: t.replace("<<", "").replace(">>", ""))],
    "detectable_format:json_format": [("text_after", lambda t, kw: t + "\nHope this helps")],
    "detectable_format:constrained_response": [("other_option", lambda t, kw: t.replace("yes.", "perhaps."))],
    "detectable_content:postscript": [("block_after", lambda t, kw: t + "\n\nAnother block of text after it.")],
    "change_case:english_capital": [("one_lower_word", lambda t, kw: t.replace("ANSWER", "answer").replace("RESULT", "result"))],
    "change_case:english_lowercase": [("one_upper_word", lambda t, kw: t.replace("answer", "ANSWER"))],
    "keywords:existence": [("drop_keyword", lambda t, kw: re.sub(r"(?i)\briver\b", "brook", t))],
    "keywords:word_once": [("drop_keyword", lambda t, kw: re.sub(r"(?i)\bgarden\b", "yard", t))],
    "keywords:forbidden_words": [("add_forbidden", lambda t, kw: t + " The floor shook.")],
    "detectable_format:multiple_sections": [("extra_section", lambda t, kw: t + "\nSECTION 3\nExtra.")],
    "detectable_format:square_brackets": [("unbracketed_word", lambda t, kw: t + " extra")],
    "detectable_format:sentence_hyphens": [("space_join", lambda t, kw: t.replace(".-", ". "))],
    "keywords:no_adjacent_consecutive": [("adjacent_ab", lambda t, kw: t + " apple banana")],
    "count:count_unique": [("repeat_word", lambda t, kw: t + " " + WORD.findall(t)[0].lower())],
    "detectable_format:number_highlighted_sections": [("drop_highlights", lambda t, kw: t.replace("*", ""))],
    "detectable_content:number_placeholders": [("drop_brackets", lambda t, kw: t.replace("[", "").replace("]", ""))],
    "copy:repeat_phrase": [("third_variant", lambda t, kw: t + " Live each week to the fullest.")],
    "keywords:word_count_different_numbers": [("one_more", lambda t, kw: t + " One more tree.")],
    "length_constraints:number_words": [("more_words", lambda t, kw: t + " and then some more words"
                                         if kw.get("relation") == "less than" else t)],
    "count:lowercase_counting": [("repeat_lower", lambda t, kw: t + " the the the")],
    "keywords:letter_frequency": [("more_letters", lambda t, kw: t + " mmm" if kw.get("let_relation") == "less than" else t)],
}


def case_id(iid, kw, response, source):
    payload = json.dumps([iid, kw, response, "", False, False], ensure_ascii=False, sort_keys=True)
    return iid + ":" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def main():
    bases = [f for f in FIXTURES if f["label"] == "pass" and not f.get("raw") and not f.get("prompt") and f.get("source", "hand") == "hand"]
    # Bases whose first or last word is not a plain word for these edits: an existing list
    # label, a one-word response (first word = last word), an abbreviation before a period.
    bad = {"1. We run.\n2. We jump.", "Hello", "Dr. Smith arrived. He sat."}
    word_edits = {k for k in EDITS if k not in ("trailing_newline", "blank_line_between_lines")}
    bad |= {f["response"] for f in bases if re.search(r"[^\x00-\x7f]", f["response"])}  # word edits would split non-Latin words
    cases = []
    for f in bases:
        for name, fn in EDITS.items():
            label = expected(f["iid"], name)
            if label is None or (f["response"] in bad and name in word_edits):
                continue
            edited = fn(f["response"])
            if edited is None or edited == f["response"]:
                continue
            cases.append((f, name, edited, label, "metamorphic" if label == "pass" else "property"))
        for name, fn in FORBIDDEN.get(f["iid"], []):
            edited = fn(f["response"], f["kw"])
            if edited != f["response"]:
                cases.append((f, name, edited, "fail", "property"))
    records, problems = [], []
    known = {"skyrl": set(), "tc": set()}
    wrong = collections.defaultdict(list)
    base_ok = {}
    for f in bases:
        sky = h.skyrl_grade(f["response"], [f["iid"]], [f["kw"]])
        tcb = h.tc_gate(f["response"], [f["iid"]], [f["kw"]])["results"][0]
        base_ok[(f["iid"], f["response"])] = {
            "skyrl": (bool(sky["results"][0]) and not sky["infra_error"]) is True,
            "tc": tcb is None or tcb is True,
            "skyrl_v": bool(sky["results"][0]) and not sky["infra_error"],
            "tc_v": tcb,
        }
    for f, edit, resp, label, source in cases:
        fx = {"iid": f["iid"], "kw": f["kw"], "response": resp}
        rep = h.contract_check(resp, f["iid"], f["kw"])
        if rep != (label == "pass"):
            problems.append((f["iid"], edit, resp))
        sky = h.skyrl_grade(resp, [f["iid"]], [f["kw"]])
        sky_v = bool(sky["results"][0]) and not sky["infra_error"]
        tc_v = h.tc_gate(resp, [f["iid"]], [f["kw"]])["results"][0]
        cid = case_id(f["iid"], f["kw"], resp, source)
        rec = {"id": cid, "source": source, "edit": edit, "instruction_id": f["iid"], "kwargs": f["kw"],
               "response": resp, "label": label, "replacement": "pass" if rep else "fail",
               "skyrl": "pass" if sky_v else "fail", "skyrl_error": sky["errors"][0],
               "tc": None if tc_v is None else ("pass" if tc_v else "fail")}
        for grader, v in (("skyrl", sky_v), ("tc", tc_v)):
            if v is None or v == (label == "pass"):
                rec[grader + "_class"] = None if v is None else "correct"
                continue
            b = base_ok[(f["iid"], f["response"])]
            base_fx = {"iid": f["iid"], "kw": f["kw"], "response": f["response"]}
            also = [(base_fx, b[grader + "_v"])] if b[grader + "_v"] is not None else []
            why = explaining_decisions(fx, v, also)
            cls = "finding" if why is None else "decision: " + ", ".join(why)
            rec[grader + "_class"] = cls
            caused = b[grader]
            rec[grader + "_edit_caused"] = caused
            known[grader].add(cid)
            wrong[(grader, f["iid"], edit, cls, caused)].append(resp)
        records.append(rec)

    # dedupe by id, keep other sources
    with open(FIX_PATH, encoding="utf-8") as fh:
        others = [json.loads(line) for line in fh if line.strip()]
    others = [o for o in others if o.get("source") not in ("metamorphic", "property")]
    seen = {o["id"] for o in others}
    uniq = []
    for r in records:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        uniq.append(r)
    with open(FIX_PATH, "w", encoding="utf-8", newline="\n") as fh:
        for r in others + uniq:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(KNOWN, encoding="utf-8") as fh:
        kn = json.load(fh)
    hand_ids = {o["id"] for o in others}
    for g in known:
        kn[g] = sorted((set(kn.get(g, [])) & hand_ids) | {r["id"] for r in uniq if r[g + "_class"] not in (None, "correct")})
    with open(KNOWN, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(kn, fh, indent=1, sort_keys=True)

    print(f"cases {len(records)} (unique {len(uniq)}): metamorphic {sum(r['source'] == 'metamorphic' for r in uniq)}, "
          f"property {sum(r['source'] == 'property' for r in uniq)}")
    print(f"replacement/label mismatches: {len(problems)}")
    for p in problems[:40]:
        print("   MISMATCH", p[0], p[1], repr(p[2][:70]))
    for grader in ("skyrl", "tc"):
        keys = sorted(k for k in wrong if k[0] == grader)
        nf = sum(len(wrong[k]) for k in keys if k[3] == "finding")
        nd = sum(len(wrong[k]) for k in keys if k[3] != "finding")
        caused = [k for k in keys if k[4]]
        print(f"{grader}: wrong verdicts {nf + nd} (findings {nf}, decisions {nd}); "
              f"caused by the edit (grader right on the base): {sum(len(wrong[k]) for k in caused)}")
        for k in caused:
            print(f"   {k[1]:45s} {k[2]:26s} {k[3][:40]:40s} n={len(wrong[k])} e.g. {wrong[k][0][:70]!r}")
    summary = collections.Counter()
    for k, v in wrong.items():
        if k[4]:
            summary[(k[0], k[2], "finding" if k[3] == "finding" else "decision")] += len(v)
    with open(os.path.join(AUDIT, "property_summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"|".join(k): v for k, v in sorted(summary.items())}, fh, indent=1)


if __name__ == "__main__":
    main()
