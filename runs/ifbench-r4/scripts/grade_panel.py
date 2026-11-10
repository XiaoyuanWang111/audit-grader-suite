"""Grade every stored panel response with every grader (step 5).

Graded text:
  G, R (and their loose variants): the stored `response` field, as the pipeline grades it.
  X: contract rule G1: a completion whose `<think>` never closes is an extraction failure
     and fails every check; otherwise the stored `response`.
Per instruction instance it records:
  G   grader strict          GL  grader loose      GV  first loose variant that passed (0-7, -1 none)
  R   reference strict       RL  reference loose
  X   replacement, as-is     XP  replacement, proposed readings
  XS  {switch: verdict} replacement with that one decision at its proposed reading (only
      for the checks the switch touches; elsewhere it equals X)
An exception is recorded as the string "EXC:<type>" in place of a verdict.

Usage: python audit/scripts/grade_panel.py [--workers N] [--only CFG/RUN ...]
Writes audit/frozen/panel_verdicts/<cfg>/<run>.jsonl
"""
import json
import os
import sys
import time
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(W, "case", "panel")
OUT = os.path.join(W, "audit", "frozen", "panel_verdicts")

SWITCH_CHECKS = {
    "D-trim": {"format:no_whitespace", "format:options"},
    "D-sentence": {"format:emoji", "format:no_bullets_bullets", "ratio:sentence_balance", "ratio:sentence_type",
                   "ratio:sentence_words", "sentence:alliteration_increment", "words:keywords_specific_position",
                   "words:last_first", "sentence:keyword", "sentence:increment", "custom:sentence_alphabet",
                   "custom:word_reverse"},
    "D-punct-set": {"count:punctuation"},
    "D-this-sentence": {"repeat:repeat_simple"},
    "D-options-exact": {"format:options"},
    "D-nbb-order": {"format:no_bullets_bullets"},
    "D-palindrome-distinct": {"words:palindrome"},
    "D-vowel-paragraph": {"words:vowel"},
    "D-japanese-digits": {"count:words_japanese"},
    "D-csv-wrapper": {"custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"},
    "D-list-sep": {"format:list"},
    "D-word": {"words:consonants", "words:prime_lengths", "words:repeats", "words:no_consecutive", "words:alphabet"},
    "D-verb": {"words:start_verb"},
    "D-explanation": {"format:quote_unquote"},
    "D-section": {"format:thesis"},
    "D-template-repeat": {"format:output_template"},
}

_init = False


def _setup():
    global A, X, _init
    if not _init:
        sys.path.insert(0, os.path.join(W, "audit", "lib"))
        import ifbaudit as A  # noqa: F401
        import replacement as X  # noqa: F401
        globals()["A"], globals()["X"] = A, X
        _init = True


def _v(fn, *a):
    try:
        return bool(fn(*a))
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__


def grade_record(row, rec):
    resp = rec["response"]
    raw = rec["raw_response"]
    extraction_failure = "<think>" in raw and "</think>" not in raw
    out = {"row": row["key"], "fin": rec["finish_reason"], "xf": extraction_failure, "inst": []}
    variants = A.loose_variants(resp) if resp is not None else []
    for j, iid in enumerate(row["instruction_id_list"]):
        kw = A.nonnull(row["kwargs"][j])
        prompt = row["prompt"]
        g = _v(A.check_G, iid, kw, resp, prompt)
        r = _v(A.check_R, iid, kw, resp, prompt)
        gv, gl = -1, False
        for k, cand in enumerate(variants):
            res = _v(A.check_G, iid, kw, cand, prompt)
            if res is True:
                gv, gl = k, True
                break
            if isinstance(res, str):
                gl = res
                break
        rl = False
        for cand in variants:
            res = _v(A.check_R, iid, kw, cand, prompt)
            if res is True or isinstance(res, str):
                rl = res
                break
        if extraction_failure:
            x = xp = False
            xs = {s: False for s, cs in SWITCH_CHECKS.items() if iid in cs}
        else:
            x = _v(X.check, iid, kw, resp, prompt)
            xp = _v(X.check, iid, kw, resp, prompt, X.PROPOSED)
            xs = {s: _v(X.check, iid, kw, resp, prompt, {s: True}) for s, cs in SWITCH_CHECKS.items() if iid in cs}
        out["inst"].append({"id": iid, "G": g, "GL": gl, "GV": gv, "R": r, "RL": rl, "X": x, "XP": xp, "XS": xs})
    return out


def grade_file(rel):
    _setup()
    cfg, fn = rel.split("/")
    src = os.path.join(PANEL, cfg, fn)
    dst = os.path.join(OUT, cfg, fn)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    t0 = time.time()
    recs = [json.loads(l) for l in open(src, encoding="utf-8")]
    with open(dst + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        for i, rec in enumerate(recs):
            f.write(json.dumps(grade_record(A.ROWS[i], rec), ensure_ascii=False) + "\n")
    os.replace(dst + ".tmp", dst)
    return rel, time.time() - t0


def main(argv):
    workers = 16
    only = None
    if "--workers" in argv:
        workers = int(argv[argv.index("--workers") + 1])
    if "--only" in argv:
        only = argv[argv.index("--only") + 1:]
    rels = []
    for cfg in sorted(os.listdir(PANEL)):
        d = os.path.join(PANEL, cfg)
        if os.path.isdir(d):
            rels += [f"{cfg}/{fn}" for fn in sorted(os.listdir(d)) if fn.endswith(".jsonl")]
    if only:
        rels = [r for r in rels if r in only]
    todo = [r for r in rels if not os.path.exists(os.path.join(OUT, r))]
    print(f"files={len(rels)} todo={len(todo)} workers={workers}", flush=True)
    t0 = time.time()
    with Pool(workers) as pool:
        for k, (rel, dt) in enumerate(pool.imap_unordered(grade_file, todo), 1):
            print(f"[{k}/{len(todo)}] {rel} {dt:.0f}s elapsed={time.time() - t0:.0f}s", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
