"""Step 5: grade every stored panel response with every grader.

Usage: grade_panel.py OUT.jsonl RUNFILE [RUNFILE ...]   (RUNFILE relative to case/panel)

Per response it records each grader's per-constraint verdicts:
  nv  SkyRL default (final_answer_text + NVIDIA checkers); nv_err, nv_outcome
  vs  SkyRL with verifyit_enabled (in-process _evaluate_with_state); vs_status
  vg  task-curation gate (verifyit checks; None for semantic constraints)
  r   replacement, proposed readings; rf replacement with NVIDIA's side of each decision
  flips  {constraint index: {decision: replacement verdict with that one switch flipped}}
The global RNG is seeded per response (sha256 of run/uuid) so the run is reproducible; NVIDIA's
ParagraphFirstWordCheck draws from it for nth_paragraph > num_paragraphs.
"""
import hashlib
import json
import os
import random
import sys
import time

sys.path.insert(0, "<W>/audit")
import harness as h  # noqa: E402
from replacement import Replacement  # noqa: E402

W = "<W>"

AFFECTS = {
    "D-word": None, "D-word-cjk": None,  # word-based checks: computed for the checks listed below
    "D-keyword-case": {"keywords:existence", "keywords:forbidden_words", "keywords:frequency", "keywords:word_once",
                       "keywords:word_count_different_numbers", "keywords:keyword_specific_position", "copy:repeat_phrase"},
    "D-keyword-substring": {"keywords:existence", "keywords:forbidden_words", "keywords:frequency", "keywords:word_once",
                            "keywords:word_count_different_numbers"},
    "D-sentence-lines": {"first_word:first_word_sent", "last_word:last_word_sent", "length_constraints:number_sentences",
                         "keywords:keyword_specific_position", "detectable_format:sentence_hyphens", "count:counting_composition"},
    "D-first-last-markup": {"first_word:first_word_answer", "first_word:first_word_sent", "last_word:last_word_answer",
                            "last_word:last_word_sent", "length_constraints:nth_paragraph_first_word"},
    "D-allcaps-short": {"change_case:capital_word_frequency"},
    "D-case-scope": {"change_case:english_capital", "change_case:english_lowercase"},
    "D-two-sep": {"combination:two_responses"}, "D-two-different": {"combination:two_responses"},
    "D-repeat-center": {"copy:repeat_phrase"}, "D-repeat-copies": {"copy:repeat_phrase"},
    "D-unique-case": {"count:count_unique"}, "D-lowercase-scope": {"count:lowercase_counting"},
    "D-placeholder": {"detectable_content:number_placeholders"},
    "D-postscript-case": {"detectable_content:postscript"}, "D-postscript-dot": {"detectable_content:postscript"},
    "D-postscript-end": {"detectable_content:postscript"}, "D-bigram-odd": {"detectable_format:bigram_wrapping"},
    "D-constrained-extra": {"detectable_format:constrained_response"}, "D-json-scalar": {"detectable_format:json_format"},
    "D-sections-case": {"detectable_format:multiple_sections"}, "D-sections-number": {"detectable_format:multiple_sections"},
    "D-sections-preamble": {"detectable_format:multiple_sections"},
    "D-bullet-markers": {"detectable_format:number_bullet_lists"}, "D-bullet-nested": {"detectable_format:number_bullet_lists"},
    "D-highlight-bold": {"detectable_format:number_highlighted_sections"},
    "D-hyphens-single": {"detectable_format:sentence_hyphens"}, "D-brackets-per-word": {"detectable_format:square_brackets"},
    "D-title-position": {"detectable_format:title"}, "D-palindrome-min": {"keywords:palindrome"},
    "D-consecutive-order": {"keywords:no_adjacent_consecutive"}, "D-start-markup": {"keywords:start_end"},
    "D-start-end-single": {"keywords:start_end"}, "D-appear-n-times": {"keywords:word_count_different_numbers"},
    "D-letter-case": {"keywords:letter_frequency", "letters:letter_counting2"}, "D-letter-unit": {"letters:letter_counting"},
    "D-paragraph-blank": {"length_constraints:nth_paragraph_first_word", "paragraphs:paragraphs2"},
    "D-divider-line": {"length_constraints:number_paragraphs", "paragraphs:paragraphs"},
    "D-comma-variants": {"punctuation:no_comma"}, "D-dot-variants": {"punctuation:punctuation_dot"},
    "D-exclamation-variants": {"punctuation:punctuation_exclamation"},
    "D-end-trailing": {"startend:end_checker"}, "D-end-case": {"startend:end_checker"},
    "D-quote-curly": {"startend:quotation"},
    "D-hyphen-dash": {"detectable_format:sentence_hyphens"}, "D-two-sep-edge": {"combination:two_responses"},
    "D-consecutive-script": {"keywords:no_adjacent_consecutive"}, "D-postscript-line": {"detectable_content:postscript"},
}
WORD_CHECKS = {"length_constraints:number_words", "count:count_unique", "count:lowercase_counting",
               "change_case:capital_word_frequency", "keywords:no_adjacent_consecutive", "keywords:palindrome",
               "first_word:first_word_answer", "last_word:last_word_answer", "keywords:keyword_specific_position"}
AFFECTS["D-word"] = WORD_CHECKS | AFFECTS["D-keyword-substring"]
AFFECTS["D-word-cjk"] = WORD_CHECKS
FLIPPED = {d: Replacement(**{d: "alt"}) for d in AFFECTS}


def load_records():
    recs = {}
    with open(f"{W}/case/data/rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            recs[rec["uuid"]] = rec
    return recs


def main():
    out_path = sys.argv[1]
    recs = load_records()
    done = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    done.add((d["file"], d["uuid"]))
                except ValueError:
                    pass
    with open(out_path, "a", encoding="utf-8", newline="\n") as out:
        for runfile in sys.argv[2:]:
            folder = runfile.split("/")[0]
            thinking = folder.endswith("__thinking")
            t0 = time.time()
            n = 0
            for line in open(f"{W}/case/panel/{runfile}", encoding="utf-8"):
                resp = json.loads(line)
                if (runfile, resp["uuid"]) in done:
                    continue
                rec = recs[resp["uuid"]]
                raw = resp["raw_response"]
                ids, kws = rec["instruction_id_list"], rec["kwargs"]
                seed = int(hashlib.sha256(f"{runfile}/{resp['uuid']}".encode()).hexdigest()[:16], 16)
                random.seed(seed)
                nv = h.nv_row(raw, rec)
                random.seed(seed)
                try:
                    vsv = h.vs_row(h.final_answer_text(raw), rec)
                    vs_status = vsv["status"]
                    vs = vsv["detail"]["source_feedback"]["follow_instruction_list"] if vs_status == "scored" else None
                    vs_detail = None if vs_status == "scored" else vsv["detail"]
                except Exception as error:  # noqa: BLE001
                    vs, vs_status, vs_detail = None, "exception", repr(error)[:300]
                vg = h.vg_row(raw, rec)
                text = h.R.graded_text(raw, thinking)
                r = [h.R.check(i, k, text) for i, k in zip(ids, kws)]
                rf_text = h.RF.graded_text(raw, thinking)
                rf = [h.RF.check(i, k, rf_text) for i, k in zip(ids, kws)]
                flips = {}
                for j, (i, k) in enumerate(zip(ids, kws)):
                    fj = {}
                    for d, rep in FLIPPED.items():
                        if i in AFFECTS[d]:
                            fj[d] = rep.check(i, k, rep.graded_text(raw, thinking))
                    if fj:
                        flips[str(j)] = fj
                out.write(json.dumps({
                    "file": runfile, "folder": folder, "run": resp["run"], "uuid": resp["uuid"],
                    "finish_reason": resp["finish_reason"], "thinking": thinking,
                    "ids": ids,
                    "nv": nv["results"], "nv_err": nv["errors"], "nv_outcome": nv["outcome"], "nv_action_empty": nv["action_empty"],
                    "vs": vs, "vs_status": vs_status, "vs_detail": vs_detail,
                    "vg": vg["results"], "vg_err": vg["errors"], "vg_candidate_empty": vg["candidate_empty"],
                    "r": r, "r_extraction_failure": text is None, "rf": rf, "flips": flips,
                }, ensure_ascii=False) + "\n")
                n += 1
                if n % 500 == 0:
                    out.flush()
                    print(f"{runfile}: {n} in {time.time() - t0:.0f}s", flush=True)
            print(f"{runfile}: done {n} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
