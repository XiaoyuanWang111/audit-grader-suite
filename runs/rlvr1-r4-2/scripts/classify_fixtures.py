"""Classify every wrong fixture verdict of graders A and B as a finding or a decision; write known_wrong.py.

A wrong verdict is a decision when the fixture's `flip` entries (the decisions whose non-proposed
reading flips the label) make it correct; otherwise it is a finding, assigned by (check, grader).
For each finding verdict the script also grades the fixture with the replacement under every single
non-proposed reading and under all of them together, and reports any reading that would explain
the grader's verdict (none should).
"""
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
sys.path.insert(0, str(W / "audit" / "tests"))

import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

RULES = {
    ("A", "keywords:existence"): "F1", ("A", "keywords:frequency"): "F1",
    ("A", "keywords:word_count_different_numbers"): "F3", ("B", "keywords:word_count_different_numbers"): "F3",
    ("B", "keywords:word_once"): "F2",
    ("A", "copy:repeat_phrase"): "F4", ("B", "copy:repeat_phrase"): "F5",
    ("A", "detectable_content:postscript"): "F6",
    ("A", "detectable_format:constrained_response"): "F7",
    ("A", "detectable_format:multiple_sections"): "F8", ("B", "detectable_format:multiple_sections"): "F8",
    ("A", "detectable_format:number_bullet_lists"): "F9", ("B", "detectable_format:number_bullet_lists"): "F9",
    ("A", "detectable_format:number_highlighted_sections"): "F10", ("B", "detectable_format:number_highlighted_sections"): "F10",
    ("A", "first_word:first_word_answer"): "F11", ("A", "first_word:first_word_sent"): "F11",
    ("A", "keywords:keyword_specific_position"): "F12",
    ("A", "count:count_unique"): "F13",
    ("A", "keywords:start_end"): "F14", ("B", "keywords:start_end"): "F14",
    ("A", "keywords:no_adjacent_consecutive"): "F15", ("B", "keywords:no_adjacent_consecutive"): "F16",
    ("A", "keywords:palindrome"): "F17", ("B", "keywords:palindrome"): "F17",
    ("A", "language:response_language"): "F18",
    ("A", "last_word:last_word_answer"): "F19",
    ("A", "length_constraints:number_paragraphs"): "F20", ("A", "paragraphs:paragraphs"): "F20",
    ("B", "length_constraints:number_paragraphs"): "F21",
    ("B", "paragraphs:paragraphs"): "F22", ("B", "paragraphs:paragraphs2"): "F22",
    ("A", "length_constraints:number_words"): "F23", ("B", "length_constraints:number_words"): "F24",
    ("A", "letters:letter_counting"): "F25",
    ("A", "detectable_content:number_placeholders"): "F26",
    ("A", "detectable_format:bigram_wrapping"): "F27",
    ("A", "count:counting_composition"): "F28", ("B", "count:counting_composition"): "F28",
    ("A", "combination:two_responses"): "F30", ("B", "combination:two_responses"): "F30",
    ("B", "count:lowercase_counting"): "F31",
    ("B", "detectable_format:square_brackets"): "F32",
    ("B", "detectable_format:sentence_hyphens"): "F33",
    ("B", "startend:quotation"): "F34",
    ("B", "detectable_format:title"): "F35",
    ("B", "length_constraints:number_sentences"): "F36",
    # added after the first panel run
    ("A", "count:lowercase_counting"): "F37",
    ("A", "detectable_format:square_brackets"): "F38",
    ("A", "last_word:last_word_sent"): "F39",
    ("A", "change_case:capital_word_frequency"): "F23",
    ("A", "length_constraints:nth_paragraph_first_word"): "F29",
    ("A", "length_constraints:number_sentences"): "F39", ("A", "detectable_format:sentence_hyphens"): "F39",
    ("B", "detectable_content:postscript"): "F40",
    ("B", "change_case:capital_word_frequency"): "F24", ("B", "last_word:last_word_answer"): "F24",
    ("B", "first_word:first_word_answer"): "F24", ("B", "last_word:last_word_sent"): "F24",
    ("B", "first_word:first_word_sent"): "F24", ("B", "keywords:keyword_specific_position"): "F24",
}


def word_once_rule(f):
    return "F2" if f["response"].lower().count("beer") >= 2 else "F1"


def main():
    known = {}
    unexplained = []
    for f in FIXTURES:
        verdicts = {
            "A": gu.check_a(f["check"], f["kwargs"], gu.extract_a(f["response"])),
            "B": gu.check_b(f["check"], f["kwargs"], gu.extract_b(f["response"])),
        }
        for g, v in verdicts.items():
            if v is None or v is f["label"]:
                continue
            if f["flip"] and v is (not f["label"]):
                known.setdefault(f["id"], {})[g] = "+".join(f["flip"])
                continue
            if f.get("finding", {}).get(g):
                fid = f["finding"][g]
            elif g == "A" and f["check"] == "keywords:word_once":
                fid = word_once_rule(f)
            else:
                fid = RULES.get((g, f["check"]))
            if fid is None:
                unexplained.append((f["id"], g, f["check"], f["response"][:60], v))
                fid = "UNASSIGNED"
            known.setdefault(f["id"], {})[g] = fid
            if isinstance(v, bool):
                singles = [d for d in cg.DECISIONS if cg.check(f["check"], f["kwargs"], f["response"], {d: "B"}, f["ctx"]) is v]
                every = cg.check(f["check"], f["kwargs"], f["response"], {d: "B" for d in cg.DECISIONS}, f["ctx"]) is v
                if singles or every:
                    print("CHECK", f["id"], g, f["check"], repr(f["response"][:50]), "explained by", singles, "all-B" if every else "")
    out = W / "audit" / "tests" / "known_wrong.py"
    lines = ['"""Generated by audit/scripts/classify_fixtures.py: fixture id -> {grader: finding or decision id}."""', "",
             "KNOWN_WRONG = {"]
    for fid in sorted(known):
        lines.append(f"    {fid!r}: {known[fid]!r},")
    lines.append("}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    n_find = sum(1 for d in known.values() for v in d.values() if v.startswith("F"))
    n_dec = sum(1 for d in known.values() for v in d.values() if v.startswith("D-"))
    print("wrong verdicts:", n_find + n_dec, "findings:", n_find, "decisions:", n_dec, "unassigned:", unexplained)


if __name__ == "__main__":
    main()
