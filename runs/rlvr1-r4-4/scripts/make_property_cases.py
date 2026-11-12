"""Step 4: build metamorphic and forbidden-edit cases from the hand-written fixtures.

Metamorphic edits that the contract ignores (label = the source fixture's label):
  M-spaces    every single space inside a line becomes two spaces
  M-curly     straight apostrophes become curly ones (don't -> don’t)
  M-case      for checks that compare words case-insensitively, the response in upper case
Edits that the contract forbids (applied to fixtures labeled pass; label = fail):
  one edit per check, listed in EDITS below.
Writes audit/tests/property_cases.json.
"""
import hashlib
import json
import os
import sys

import regex as re

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AUDIT, "tests"))
from fixtures_data import FIXTURES  # noqa: E402

EXACT_PHRASE = {"detectable_format:constrained_response", "startend:end_checker"}  # spacing is part of an exact phrase
CASE_INSENSITIVE = {"keywords:existence", "keywords:forbidden_words", "keywords:frequency", "keywords:word_once",
                    "keywords:word_count_different_numbers", "first_word:first_word_answer", "first_word:first_word_sent",
                    "last_word:last_word_answer", "last_word:last_word_sent", "keywords:keyword_specific_position",
                    "keywords:start_end", "copy:repeat_phrase", "length_constraints:nth_paragraph_first_word",
                    "keywords:letter_frequency", "letters:letter_counting2"}


def kw_remove(resp, kw):
    for k in kw.get("keywords", [kw.get("keyword")]):
        resp = re.sub(r"(?i)(?<![\p{L}\p{N}_])" + re.escape(k) + r"(?![\p{L}\p{N}_])", "thing", resp)
    return resp


EDITS = {
    "punctuation:no_comma": lambda r, kw: r + " Also, yes",
    "punctuation:punctuation_dot": lambda r, kw: r + " v1.2",
    "punctuation:punctuation_exclamation": lambda r, kw: r + " Wow!",
    "keywords:forbidden_words": lambda r, kw: r + " " + kw["forbidden_words"][0],
    "startend:quotation": lambda r, kw: r + " Extra",
    "startend:end_checker": lambda r, kw: r + " Thanks",
    "change_case:english_lowercase": lambda r, kw: r + " NASA",
    "change_case:english_capital": lambda r, kw: r + " ok",
    "keywords:start_end": lambda r, kw: r + ".",
    "combination:two_responses": lambda r, kw: r + "\n******\nThird answer.",
    "detectable_format:number_bullet_lists": lambda r, kw: r + "\n* Extra point.",
    "detectable_format:json_format": lambda r, kw: r + " trailing",
    "detectable_format:title": lambda r, kw: r.replace("<<", "").replace(">>", ""),
    "detectable_format:square_brackets": lambda r, kw: r + " unbracketed",
    "keywords:word_once": lambda r, kw: kw_remove(r, kw),
    "keywords:existence": lambda r, kw: kw_remove(r, kw),
    "length_constraints:number_paragraphs": lambda r, kw: r + "\n***\nExtra paragraph.",
    "paragraphs:paragraphs": lambda r, kw: r + "\n***\nExtra paragraph.",
    "paragraphs:paragraphs2": lambda r, kw: r + "\n\nThird paragraph.",
    "detectable_format:multiple_sections": lambda r, kw: r + "\n" + kw["section_spliter"] + " 9\nExtra.",
    "detectable_format:constrained_response": lambda r, kw: r + (" My answer is no." if "My answer is no." not in r else " My answer is yes."),
    "count:lowercase_counting": lambda r, kw: r + " zzz" * (kw["N"] + 1),
    "count:count_unique": lambda r, kw: r + " " + r.split()[0],
    "first_word:first_word_answer": lambda r, kw: "Well, " + r,
    "last_word:last_word_answer": lambda r, kw: r + " indeed.",
    "detectable_format:sentence_hyphens": lambda r, kw: r + " Another sentence follows.",
    "keywords:no_adjacent_consecutive": lambda r, kw: r + " a b",
    "detectable_content:postscript": lambda r, kw: re.sub(r"(?i)p\.\s?(p\.\s?)?s\.?", "Note", r),
}


def cid(kind, iid, kw, resp):
    h = hashlib.sha256(json.dumps([kind, iid, kw, resp], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return f"{kind}:{iid.split(':')[1]}:{h[:12]}"


cases = []
for fx in FIXTURES:
    iid, kw, resp, label = fx["instruction_id"], fx["kwargs"], fx["response"], fx["label"]
    variants = []
    if "  " not in resp and " " in resp and iid not in EXACT_PHRASE:
        variants.append(("M-spaces", re.sub(r"(?<=\S) (?=\S)", "  ", resp)))
    if "'" in resp:
        variants.append(("M-curly", resp.replace("'", "’")))
    if iid in CASE_INSENSITIVE and resp.upper() != resp:
        variants.append(("M-case", resp.upper()))
    for kind, new in variants:
        if new != resp:
            cases.append({"id": cid(kind, iid, kw, new), "kind": kind, "source": fx["id"], "instruction_id": iid,
                          "kwargs": kw, "response": new, "label": label, "decisions": fx["decisions"]})
    if label == "pass" and iid in EDITS:
        new = EDITS[iid](resp, kw or {})
        if new != resp:
            cases.append({"id": cid("E", iid, kw, new), "kind": "E-forbidden-edit", "source": fx["id"], "instruction_id": iid,
                          "kwargs": kw, "response": new, "label": "fail", "decisions": fx["decisions"]})
seen = set()
uniq = []
for c in cases:
    if c["id"] not in seen:
        seen.add(c["id"])
        uniq.append(c)
with open(os.path.join(AUDIT, "tests", "property_cases.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(uniq, f, ensure_ascii=False, indent=1)
print(len(uniq), "property cases")
