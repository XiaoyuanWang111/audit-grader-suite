"""Rows whose constraints no response can satisfy under the contract's proposed readings (a lower
bound: only the pairings below are checked). Every correct grader gives these rows reward 0.0.
Writes audit/out/unsatisfiable.json.
"""
import collections
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402

OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")
SEPARATED = {"length_constraints:nth_paragraph_first_word", "paragraphs:paragraphs2", "paragraphs:paragraphs",
             "length_constraints:number_paragraphs", "detectable_format:multiple_sections", "combination:two_responses"}


def reasons(rec, prompt):
    ids = rec["instruction_id_list"]
    kw = dict(zip(ids, rec["kwargs"]))
    s = set(ids)
    out = []
    if {"change_case:english_capital", "change_case:english_lowercase"} <= s:
        out.append("english_capital + english_lowercase")
    if "language:response_language" in s and kw["language:response_language"]["language"] != "en" and (
            s & {"change_case:english_capital", "change_case:english_lowercase"}):
        out.append("non-English language + English case")
    if "punctuation:punctuation_dot" in s and "detectable_content:postscript" in s:
        out.append("no dots + postscript marker with dots")
    if "punctuation:punctuation_dot" in s and "detectable_format:constrained_response" in s:
        out.append("no dots + option ending with a dot")
    if "keywords:start_end" in s and "startend:end_checker" in s:
        out.append("start_end (no punctuation at the end) + end phrase ending with ?")
    if "keywords:start_end" in s and "startend:quotation" in s:
        out.append("start_end (no punctuation at the end) + closing quotation mark")
    k = kw.get("length_constraints:nth_paragraph_first_word")
    if k and k["nth_paragraph"] > k["num_paragraphs"]:
        out.append("nth_paragraph > num_paragraphs")
    if "paragraphs:paragraphs" in s and "length_constraints:number_paragraphs" in s and kw["length_constraints:number_paragraphs"]["num_paragraphs"] != 2:
        out.append("2 *** paragraphs + N != 2 *** paragraphs")
    if "paragraphs:paragraphs2" in s and k and k["num_paragraphs"] != 2:
        out.append("2 blank-line paragraphs + N != 2 blank-line paragraphs")
    def needs_break(i):
        a = kw.get(i) or {}
        return (i in ("paragraphs:paragraphs", "paragraphs:paragraphs2")
                or (i == "length_constraints:number_paragraphs" and a.get("num_paragraphs", 0) >= 2)
                or (i == "length_constraints:nth_paragraph_first_word" and a.get("num_paragraphs", 0) >= 2)
                or (i == "detectable_format:multiple_sections" and a.get("num_sections", 0) >= 2))
    if "detectable_format:sentence_hyphens" in s and any(needs_break(i) for i in s):
        out.append("sentence_hyphens (no whitespace between sentences) + paragraph or section breaks")
    if "detectable_format:constrained_response" in s:
        others = [(i, a) for i, a in zip(ids, rec["kwargs"]) if i != "detectable_format:constrained_response"]
        ok = False
        for o in OPTIONS:
            ctx = {}
            if all(cg.check(i, a, o, None, {"shown_marker": cg.shown_postscript_marker(prompt, a["postscript_marker"])}
                            if i == "detectable_content:postscript" else ctx) for i, a in others):
                ok = True
        if others and not ok:
            out.append("constrained_response (exact option) + a constraint no option meets")
    if "count:count_unique" in s and ("copy:repeat_phrase" in s or (
            "keywords:frequency" in s and kw["keywords:frequency"]["relation"] == "at least" and kw["keywords:frequency"]["frequency"] >= 2) or (
            "keywords:word_count_different_numbers" in s and kw["keywords:word_count_different_numbers"]["frequency"] >= 2)):
        out.append("count_unique + a repeated word")
    lc = kw.get("letters:letter_counting")
    if lc and lc["relation"] == "less than" and s & {"keywords:existence", "keywords:word_once", "first_word:first_word_answer",
                                                     "last_word:last_word_answer", "keywords:keyword_specific_position", "copy:repeat_phrase"}:
        out.append("fewer than N<=3 letters + a required word")
    return out


def main():
    rows = gu.load_rows()
    by_reason = collections.Counter()
    unsat = []
    for row in rows:
        rs = reasons(row["record"], row["prompt"])
        if rs:
            unsat.append(row["uuid"])
            for r in rs:
                by_reason[r] += 1
    print("rows that no response can pass (lower bound):", len(unsat), "of", len(rows))
    for r, n in by_reason.most_common():
        print(f"  {n:5d}  {r}")
    (W / "audit" / "out" / "unsatisfiable.json").write_text(json.dumps({"rows": unsat, "by_reason": by_reason}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
