"""Step 5: grade every stored panel response with every grader.

Writes audit/out/panel/<folder>__<run>.jsonl, one line per response:
  run, uuid, model, finish_reason, reasoning (thinking configuration), raw_has_think_open, raw_has_think_close,
  ids, kwargs,
  skyrl_text_len, skyrl_text_empty, nvidia (per constraint), nvidia_err, skyrl_reward, skyrl_infra,
  curation_text_len, verifyit (per constraint; null = judged, not gated), gate_pass,
  repl_extraction_failure, replacement (per constraint), repl_flips ({constraint index: {decision: verdict}} where
  the non-proposed reading changes the verdict).
SkyRL's reward draws from Python's global random state for nth_paragraph > num_paragraphs (finding N17); each
response is graded after random.seed(<first 8 bytes of sha256(run|uuid)>) so that the run is reproducible.

Usage (from the case folder): ../.venv/Scripts/python.exe ../audit/scripts/grade_panel.py [workers]
"""
import glob
import hashlib
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)
sys.path.insert(0, AUDIT)

DECISIONS_BY_CHECK = {
    "change_case:capital_word_frequency": ["D-capital-word", "D-word"],
    "combination:two_responses": ["D-two-responses"],
    "copy:repeat_phrase": ["D-repeat-center", "D-repeat-original"],
    "count:count_unique": ["D-count-unique-case", "D-word"],
    "count:counting_composition": ["D-sentence"],
    "count:lowercase_counting": ["D-lowercase-counting", "D-lowercase-total"],
    "detectable_content:number_placeholders": ["D-placeholder"],
    "detectable_content:postscript": ["D-postscript", "D-postscript-case", "D-postscript-line"],
    "detectable_format:bigram_wrapping": ["D-bigram-odd"],
    "detectable_format:constrained_response": ["D-constrained-exact"],
    "detectable_format:json_format": ["D-json-value"],
    "detectable_format:multiple_sections": ["D-sections-preamble", "D-sections-case", "D-sections-numbering"],
    "detectable_format:number_bullet_lists": ["D-bullets"],
    "detectable_format:number_highlighted_sections": ["D-highlight"],
    "detectable_format:sentence_hyphens": ["D-hyphens-single", "D-sentence"],
    "detectable_format:square_brackets": ["D-square-brackets"],
    "detectable_format:title": ["D-title"],
    "first_word:first_word_answer": ["D-first-last-case"],
    "first_word:first_word_sent": ["D-first-last-case", "D-sentence"],
    "keywords:existence": ["D-keyword-match"],
    "keywords:forbidden_words": ["D-keyword-match"],
    "keywords:frequency": ["D-keyword-match"],
    "keywords:keyword_specific_position": ["D-sentence", "D-word"],
    "keywords:letter_frequency": ["D-letter-case"],
    "keywords:no_adjacent_consecutive": ["D-consecutive-order", "D-word", "D-alphabet"],
    "keywords:palindrome": ["D-palindrome-length", "D-palindrome-phrase"],
    "keywords:start_end": ["D-start-end-lead", "D-first-last-case"],
    "keywords:word_count_different_numbers": ["D-word-count-exact", "D-keyword-match"],
    "keywords:word_once": ["D-keyword-match"],
    "last_word:last_word_answer": ["D-first-last-case"],
    "last_word:last_word_sent": ["D-first-last-case", "D-sentence"],
    "length_constraints:nth_paragraph_first_word": ["D-paragraph-separator", "D-first-last-case"],
    "length_constraints:number_paragraphs": ["D-divider"],
    "length_constraints:number_sentences": ["D-sentence"],
    "length_constraints:number_words": ["D-word"],
    "letters:letter_counting": ["D-letters-count"],
    "letters:letter_counting2": ["D-letter-case"],
    "paragraphs:paragraphs": ["D-divider"],
    "paragraphs:paragraphs2": ["D-paragraph-separator"],
    "punctuation:no_comma": ["D-punct-variants"],
    "punctuation:punctuation_dot": ["D-punct-variants"],
    "punctuation:punctuation_exclamation": ["D-punct-variants"],
    "startend:end_checker": ["D-end-phrase-markup", "D-end-phrase-case"],
    "startend:quotation": ["D-quotation-typographic"],
}

_DATA = None


def data():
    global _DATA
    if _DATA is None:
        _DATA = {}
        with open(os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                _DATA[row["extra_info"]["nemotron_ultra"]["uuid"]] = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    return _DATA


def grade_one(run_name, reasoning, rec_line):
    import harness
    import replacement as R

    harness.setup()
    r = json.loads(rec_line)
    record = data()[r["uuid"]]
    raw = r["raw_response"]
    ids, kws = record["instruction_id_list"], record["kwargs"]
    seed = int.from_bytes(hashlib.sha256(f"{run_name}|{r['uuid']}".encode()).digest()[:8], "big")
    random.seed(seed)
    sky = harness.skyrl_row(raw, record)
    cur = harness.verifyit_row(raw, record)
    text = R.graded_text(raw, reasoning)
    repl, flips = [], {}
    for i, (iid, kw) in enumerate(zip(ids, kws)):
        base = R.check(iid, kw, text)
        repl.append(base)
        f = {}
        for d in ["D-empty"] + DECISIONS_BY_CHECK.get(iid, []):
            v = R.check(iid, kw, text, {**R.DEFAULTS, d: "B"})
            if v != base:
                f[d] = v
        if not reasoning:
            v = R.check(iid, kw, R.graded_text(raw, reasoning, {**R.DEFAULTS, "D-literal-think": "B"}))
            if v != base:
                f["D-literal-think"] = v
        if f:
            flips[str(i)] = f
    return {
        "run": run_name, "uuid": r["uuid"], "model": r["model"], "finish_reason": r["finish_reason"],
        "reasoning": reasoning, "raw_has_think_open": "<think>" in raw, "raw_has_think_close": "</think>" in raw,
        "ids": ids, "kwargs": kws,
        "skyrl_text_len": len(sky["text"]), "skyrl_text_empty": not sky["text"].strip(),
        "nvidia": sky["results"], "nvidia_err": sky["errors"], "skyrl_reward": sky["reward"], "skyrl_infra": sky["infra_error"],
        "curation_text_len": len(cur["text"]), "verifyit": cur["results"], "gate_pass": cur["gate_pass"],
        "repl_extraction_failure": text is None, "replacement": repl, "repl_flips": flips,
    }


def grade_chunk(args):
    run_name, reasoning, lines = args
    return [grade_one(run_name, reasoning, line) for line in lines]


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    out_dir = os.path.join(AUDIT, "out", "panel")
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(W, "case", "panel", "*", "*.jsonl")))
    with ProcessPoolExecutor(workers) as pool:
        for path in files:
            folder = os.path.basename(os.path.dirname(path))
            run = os.path.splitext(os.path.basename(path))[0]
            run_name = f"{folder}/{run}"
            reasoning = folder.endswith("__thinking")
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
            chunks = [(run_name, reasoning, lines[i:i + 200]) for i in range(0, len(lines), 200)]
            out_path = os.path.join(out_dir, f"{folder}__{run}.jsonl")
            with open(out_path, "w", encoding="utf-8", newline="\n") as out:
                for result in pool.map(grade_chunk, chunks):
                    for rec in result:
                        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print("done", run_name, len(lines), flush=True)


if __name__ == "__main__":
    main()
