"""Step 5: grade every stored panel response with grader A, grader B and the replacement R.

Writes audit/work/panel_verdicts.jsonl (no response text): one line per response with, for each
constraint, A's verdict and error, B's verdict and error, R's verdict under the proposed readings,
and R's verdict under every non-empty subset of the decision entries relevant to that check.

Grader A's `build_instruction` draws from the global `random` state for the rows whose
nth_paragraph exceeds num_paragraphs; the script seeds `random` per response with
sha256(run + uuid) so the run is reproducible (finding G2 measures the spread separately).

Usage: python grade_panel.py [workers]
"""
import glob
import hashlib
import itertools
import json
import multiprocessing as mp
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
W = os.path.dirname(AUDIT)

RELEVANT = {
    "change_case:capital_word_frequency": ["D-word", "D-capital-single-letter"],
    "change_case:english_capital": ["D-english-part"],
    "change_case:english_lowercase": ["D-english-part"],
    "combination:two_responses": ["D-two-responses-edge"],
    "copy:repeat_phrase": ["D-repeat-original", "D-repeat-center"],
    "count:count_unique": ["D-word", "D-unique-case"],
    "count:counting_composition": ["D-divider-form", "D-divider-empty", "D-sentence"],
    "count:lowercase_counting": ["D-word", "D-lowercase-count", "D-lowercase-scope"],
    "detectable_content:number_placeholders": ["D-placeholder-kind"],
    "detectable_content:postscript": ["D-postscript-end", "D-postscript-case"],
    "detectable_format:bigram_wrapping": ["D-word", "D-bigram-odd"],
    "detectable_format:constrained_response": ["D-constrained-exact"],
    "detectable_format:json_format": ["D-json-toplevel"],
    "detectable_format:multiple_sections": ["D-sections-numbering", "D-sections-preamble", "D-sections-case"],
    "detectable_format:number_bullet_lists": ["D-bullet-marker", "D-bullet-nested"],
    "detectable_format:number_highlighted_sections": ["D-highlight-bold"],
    "detectable_format:sentence_hyphens": ["D-hyphen-dash"],
    "detectable_format:square_brackets": ["D-bracket-group"],
    "detectable_format:title": ["D-title-position"],
    "first_word:first_word_answer": ["D-word"],
    "first_word:first_word_sent": ["D-word", "D-sentence"],
    "keywords:existence": ["D-keyword-boundary"],
    "keywords:forbidden_words": ["D-keyword-boundary"],
    "keywords:frequency": ["D-keyword-boundary"],
    "keywords:keyword_specific_position": ["D-word", "D-sentence"],
    "keywords:letter_frequency": ["D-letter-case"],
    "keywords:no_adjacent_consecutive": ["D-word", "D-consecutive-order", "D-consecutive-script"],
    "keywords:palindrome": ["D-palindrome-length"],
    "keywords:start_end": ["D-word", "D-start-end-one-word"],
    "keywords:word_count_different_numbers": ["D-keyword-boundary", "D-appear-n-times"],
    "keywords:word_once": ["D-keyword-boundary"],
    "language:response_language": ["D-language-mixed"],
    "last_word:last_word_answer": ["D-word"],
    "last_word:last_word_sent": ["D-word", "D-sentence"],
    "length_constraints:nth_paragraph_first_word": ["D-word", "D-blank-run"],
    "length_constraints:number_paragraphs": ["D-divider-form", "D-divider-empty"],
    "length_constraints:number_sentences": ["D-sentence"],
    "length_constraints:number_words": ["D-word"],
    "letters:letter_counting": ["D-letters-unit"],
    "letters:letter_counting2": ["D-letter-case"],
    "paragraphs:paragraphs": ["D-divider-form", "D-divider-empty"],
    "paragraphs:paragraphs2": ["D-blank-run"],
    "punctuation:no_comma": ["D-comma-chars"],
    "punctuation:punctuation_dot": ["D-dot-chars"],
    "punctuation:punctuation_exclamation": ["D-excl-chars"],
    "startend:end_checker": ["D-end-trailing", "D-end-case"],
    "startend:quotation": ["D-quote-chars"],
}

_H = None
_ROWS = None


def _init():
    global _H, _ROWS
    os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.path.insert(0, AUDIT)
    import logging
    logging.disable(logging.CRITICAL)
    import harness
    _H = harness
    _ROWS = harness.load_rows()


def grade_one(item):
    run, line_no, rec = item
    H, R = _H, _H.R
    raw = rec["raw_response"]
    record = _ROWS[rec["uuid"]]
    reasoning = "Thinking" in rec["model"]
    random.seed(int(hashlib.sha256((run + rec["uuid"]).encode()).hexdigest()[:16], 16))
    ta = H.extract_a(raw)
    tb = H.extract_b(raw)
    tr = R.graded_text(raw, reasoning)
    tr_alt = R.graded_text(raw, reasoning, {**R.PROPOSED, "D-think-markup": "alt"}) if "<think>" in raw else tr
    cons = []
    for iid, kw in zip(record["instruction_id_list"], record["kwargs"]):
        a, a_err = H.a_check(iid, kw, ta)
        b, b_err = H.b_check(iid, kw, tb)
        r = R.check(iid, kw, tr)
        alts = {}
        rel = RELEVANT[iid]
        for k in range(1, len(rel) + 1):
            for subset in itertools.combinations(rel, k):
                v = R.check(iid, kw, tr, {d: "alt" for d in subset})
                alts["+".join(subset)] = v
        if tr_alt != tr:
            alts["D-think-markup"] = R.check(iid, kw, tr_alt)
        cons.append({"iid": iid, "A": a, "A_err": a_err, "B": b, "B_err": b_err, "R": r, "R_alt": alts})
    return {
        "run": run, "line": line_no, "uuid": rec["uuid"], "model": rec["model"], "finish_reason": rec["finish_reason"],
        "num_tokens": rec["num_tokens"], "reasoning_model": reasoning, "extraction_failure": tr is None,
        "a_text_empty": not ta.strip(), "b_text_empty": not tb.strip(), "constraints": cons,
    }


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    items = []
    for path in sorted(glob.glob(os.path.join(W, "case", "panel", "*", "*.jsonl"))):
        run = os.path.relpath(path, os.path.join(W, "case", "panel")).replace("\\", "/")
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                items.append((run, i, json.loads(line)))
    out_path = os.path.join(AUDIT, "work", "panel_verdicts.jsonl")
    t0 = time.time()
    n = 0
    with mp.Pool(workers, initializer=_init) as pool, open(out_path, "w", encoding="utf-8", newline="\n") as out:
        for res in pool.imap(grade_one, items, chunksize=20):
            out.write(json.dumps(res) + "\n")
            n += 1
            if n % 1000 == 0:
                print(f"{n}/{len(items)} {time.time() - t0:.0f}s", flush=True)
    print(f"done {n} responses in {time.time() - t0:.0f}s -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
