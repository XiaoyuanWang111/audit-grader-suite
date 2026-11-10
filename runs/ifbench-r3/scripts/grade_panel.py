"""Step 5: grade every stored panel response with the grader, the reference and the replacement.

One row per instruction instance (228 run files x 344 instructions = 78,432 rows) in
audit/work/panel_verdicts.jsonl with fields:
  cfg, run, key, j (index of the instruction in the prompt), iid, heldout, extraction_failure,
  finish, g, gl, glw (grader strict, loose, index of the loose variant that passed), r, rl, rlw
  (reference), p (replacement, proposed readings; extraction failures fail per G1),
  alt {"D-x:B": verdict} (replacement with one decision switched), err {grader: message}.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/grade_panel.py [--workers N]
"""
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "replacement"))
import ifb  # noqa: E402

ALT = {
    "count:conjunctions": ["D-conj:B"],
    "count:keywords_multiple": ["D-match:B", "D-match:C", "D-keyword-count:B"],
    "count:numbers": ["D-number:B", "D-number:C"],
    "count:person_names": ["D-names-case:B"],
    "count:pronouns": ["D-pronoun:B", "D-pronoun:C"],
    "count:punctuation": ["D-punct-set:B"],
    "count:unique_word_count": ["D-unique:B", "D-unique:C", "D-word:B", "D-word:C"],
    "count:word_count_range": ["D-between:B", "D-word:B", "D-word:C"],
    "count:words_japanese": ["D-vacuous:B", "D-japanese:C", "D-word:C"],
    "custom:character_reverse": ["D-char-reverse:B", "D-custom-facts:B"],
    "custom:csv_city": ["D-csv:B", "D-csv:C"],
    "custom:csv_quotes": ["D-csv:B", "D-csv:C", "D-csv:D"],
    "custom:csv_special_character": ["D-csv:B", "D-csv:C", "D-csv:E"],
    "custom:date_format_list": ["D-custom-facts:C", "D-custom-extra-text:B"],
    "custom:european_capitals_sort": ["D-custom-facts:B", "D-custom-extra-text:B"],
    "custom:mcq_count_length": ["D-mcq:B"],
    "custom:multiples": ["D-custom-extra-text:B", "D-custom-extra-text:C"],
    "custom:reverse_newline": ["D-custom-facts:B", "D-custom-extra-text:B"],
    "custom:sentence_alphabet": ["D-sentence:B", "D-sentence:C"],
    "custom:word_reverse": ["D-custom-facts:B"],
    "format:emoji": ["D-emoji-position:B", "D-sentence:B", "D-sentence:C"],
    "format:line_indent": ["D-indent:B", "D-indent:C"],
    "format:list": ["D-list:B", "D-list:C", "D-list:D"],
    "format:newline": ["D-word:C"],
    "format:no_bullets_bullets": ["D-sentence:B"],
    "format:no_whitespace": ["D-trailing-ws:B"],
    "format:options": ["D-options:B", "D-options:C", "D-options:D"],
    "format:output_template": ["D-template:B", "D-template:C"],
    "format:parentheses": ["D-paren:B", "D-paren:C"],
    "format:quote_unquote": ["D-vacuous:B"],
    "format:sub-bullets": ["D-subbullet:B"],
    "format:thesis": ["D-section:B"],
    "format:title_case": ["D-title:B", "D-title:C"],
    "ratio:overlap": ["D-overlap:B", "D-overlap:C", "D-overlap:D", "D-overlap:E"],
    "ratio:sentence_balance": ["D-balance:B", "D-sentence:B", "D-vacuous:B"],
    "ratio:sentence_type": ["D-balance:B", "D-sentence:B", "D-vacuous:B"],
    "ratio:sentence_words": ["D-char-count:B", "D-char-count:C", "D-different-words:B", "D-sentence:B"],
    "ratio:stop_words": ["D-word:B", "D-word:C"],
    "repeat:repeat_change": ["D-repeat-change:B", "D-repeat-change:C"],
    "repeat:repeat_simple": ["D-repeat-simple:B"],
    "repeat:repeat_span": ["D-span:B", "D-span:C"],
    "sentence:alliteration_increment": ["D-alliteration:C", "D-sentence:B", "D-vacuous:B"],
    "sentence:increment": ["D-sentence:B", "D-sentence:C", "D-vacuous:B"],
    "sentence:keyword": ["D-sentence:B", "D-sentence:C", "D-match:B"],
    "words:alphabet": ["D-alphabet-start:B", "D-word:C", "D-word-numbers:B"],
    "words:consonants": ["D-y:B", "D-word:C", "D-word-numbers:B"],
    "words:keywords_specific_position": ["D-sentence:B", "D-sentence:C", "D-word:C"],
    "words:last_first": ["D-sentence:B", "D-vacuous:B"],
    "words:no_consecutive": ["D-word:C"],
    "words:odd_even_syllables": ["D-word:C"],
    "words:palindrome": ["D-palindrome:B", "D-palindrome:C"],
    "words:paragraph_last_first": ["D-paragraph:B"],
    "words:prime_lengths": ["D-prime-length:B", "D-word:C", "D-word-numbers:B"],
    "words:repeats": ["D-repeat-count:B", "D-word:C"],
    "words:start_verb": ["D-verb:B"],
    "words:vowel": ["D-vowel:B", "D-vowel:D", "D-paragraph:C"],
    "words:words_position": ["D-word:C"],
}


def strict_loose(which, iid, kw, prompt, resp):
    """(strict, loose, winner, error) with the same semantics as ifb.verdict."""
    try:
        inst = ifb._instance(which, iid, kw, prompt)
        strict = bool(resp and resp.strip() and inst.check_following(resp))
        if strict:
            return True, True, 0, None
        for i, cand in enumerate(ifb.loose_variants(resp)):
            if i and cand.strip() and inst.check_following(cand):
                return False, True, i, None
        return False, False, None, None
    except Exception as e:  # noqa: BLE001
        return None, None, None, f"{type(e).__name__}: {str(e)[:120]}"


def grade_file(path):
    import ifbench_contract as rep
    rows = ifb.load_rows()
    held = ifb.heldout()
    cfg = os.path.basename(os.path.dirname(path))
    run = os.path.basename(path)[:-6]
    out = []
    with open(path, encoding="utf-8") as fh:
        recs = [json.loads(l) for l in fh]
    for i, rec in enumerate(recs):
        row = rows[i]
        assert rec["key"] == row["key"]
        ef = ifb.extraction_failure(rec)
        resp = rec["response"]
        for j, (iid, kw) in enumerate(zip(row["instruction_id_list"], row["kwargs"])):
            g, gl, glw, ge = strict_loose("grader", iid, kw, row["prompt"], resp)
            r, rl, rlw, re_ = strict_loose("reference", iid, kw, row["prompt"], resp)
            perr = None
            try:
                p = False if ef else rep.check(iid, kw, row["prompt"], resp)
                alt = {}
                for a in ALT.get(iid, []):
                    d, letter = a.split(":")
                    alt[a] = False if ef else rep.check(iid, kw, row["prompt"], resp, {d: letter})
            except Exception as e:  # noqa: BLE001
                p, alt, perr = None, {}, f"{type(e).__name__}: {str(e)[:120]}"
            err = {k: v for k, v in (("grader", ge), ("reference", re_), ("replacement", perr)) if v}
            out.append({"cfg": cfg, "run": run, "key": row["key"], "j": j, "iid": iid,
                        "heldout": held.get(cfg) == run, "extraction_failure": ef, "finish": rec["finish_reason"],
                        "g": g, "gl": gl, "glw": glw, "r": r, "rl": rl, "rlw": rlw, "p": p, "alt": alt, "err": err})
    return path, out


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 16
    ifb.verify_pins()
    files = sorted(glob.glob(os.path.join(ifb.CASE, "panel", "*", "*.jsonl")))
    t0 = time.time()
    dst = os.path.join(W, "audit", "work", "panel_verdicts.jsonl")
    n = 0
    with Pool(workers) as pool, open(dst, "w", encoding="utf-8", newline="\n") as fh:
        for k, (path, out) in enumerate(pool.imap_unordered(grade_file, files), 1):
            for o in out:
                fh.write(json.dumps(o, ensure_ascii=False) + "\n")
            n += len(out)
            if k % 20 == 0:
                print(f"{k}/{len(files)} files, {n} rows, {time.time() - t0:.0f}s", flush=True)
    ifb.verify_pins()
    print(f"done: {n} rows in {time.time() - t0:.0f}s -> {dst}")


if __name__ == "__main__":
    main()
