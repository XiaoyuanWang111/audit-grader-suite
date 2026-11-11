"""Step 5: grade every stored panel response with grader (strict, loose), reference (strict, loose)
and the replacement (proposal readings, plus each decision switch's alternative on the checks it affects).

Output: audit/work/panel/<config>__<run>.tsv, one line per (prompt, instruction).
Usage: python run_panel.py [n_procs]
"""
import json
import multiprocessing as mp
import os
import sys
import time

W = "<W>"
PANEL = W + "/case/panel"
OUT = W + "/audit/work/panel"

ALT = {  # switch -> (alternative value, checks it affects)
    "d_vacuous": ("pass", ["count:words_japanese", "format:quote_unquote", "format:line_indent", "sentence:increment",
                           "sentence:alliteration_increment", "words:last_first", "format:emoji", "format:thesis"]),
    "d_keyword_form": ("substring", ["count:keywords_multiple", "sentence:keyword"]),
    "d_count_exact": (False, ["count:keywords_multiple"]),
    "d_punct_set": ("narrow", ["count:punctuation"]),
    "d_punct_separate": (True, ["count:punctuation"]),
    "d_overlap_unit": ("char", ["ratio:overlap"]),
    "d_overlap_side": ("reference", ["ratio:overlap"]),
    "d_balance": ("near", ["ratio:sentence_balance"]),
    "d_list_inline": (True, ["format:list"]),
    "d_nows_trailing": (False, ["format:no_whitespace"]),
    "d_options_whitespace": (False, ["format:options"]),
    "d_template_outside": (True, ["format:output_template"]),
    "d_csv_wrapper": (False, ["custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"]),
    "d_palin_distinct": (False, ["words:palindrome"]),
    "d_vowel_paragraph": ("newline", ["words:vowel"]),
    "d_vowel": ("word", ["words:vowel"]),
    "d_span_base": (1, ["repeat:repeat_span"]),
    "d_europe_moscow": (False, ["custom:european_capitals_sort"]),
    "d_africa_complete": (False, ["custom:reverse_newline"]),
    "d_indent_blank": (False, ["format:line_indent"]),
    "d_section": ("heading", ["format:thesis"]),
    "d_typographic": (False, ["format:quotes", "format:quote_unquote", "count:punctuation", "format:options",
                              "repeat:repeat_change", "repeat:repeat_span", "repeat:repeat_simple"]),
}


def load_dataset_rows():
    from datasets import load_dataset
    ds = load_dataset("parquet", data_files=W + "/case/data/train-00000-of-00001.parquet", split="train")
    return [dict(key=r["key"], prompt=r["prompt"], ids=list(r["instruction_id_list"]),
                 kwargs=[{k: v for k, v in d.items() if v is not None} for d in r["kwargs"]]) for r in ds]


def v(x):
    return "1" if x is True else "0" if x is False else x


def grade_file(args):
    config, run, rows = args
    sys.path.insert(0, W + "/audit/scripts")
    import graders
    out_path = f"{OUT}/{config}__{run}.tsv"
    if os.path.exists(out_path):
        return out_path, 0, "skip"
    thinking = config.endswith("__thinking")
    lines = [json.loads(x) for x in open(f"{PANEL}/{config}/{run}.jsonl", encoding="utf-8")]
    assert len(lines) == 300, (config, run, len(lines))
    buf = []
    t0 = time.time()
    for row, rec in zip(rows, lines):
        aligned = str(rec["key"]) == str(row["key"]) and rec["prompt"] == row["prompt"]
        resp = rec["response"]
        rawr = rec["raw_response"]
        closed = "</think>" in rawr
        extraction_failure = thinking and not closed
        for idx, (iid, kw) in enumerate(zip(row["ids"], row["kwargs"])):
            gs = graders.grader_strict(iid, kw, row["prompt"], resp)
            gl = graders.grader_loose(iid, kw, row["prompt"], resp)
            rs = graders.reference_strict(iid, kw, row["prompt"], resp)
            rl = graders.reference_loose(iid, kw, row["prompt"], resp)
            if extraction_failure:
                rep = False
                alts = {}
            else:
                rep = graders.replacement(iid, kw, row["prompt"], resp)
                alts = {sw: v(graders.replacement(iid, kw, row["prompt"], resp, **{sw: alt}))
                        for sw, (alt, checks) in ALT.items() if iid in checks}
            buf.append("\t".join([config, run, str(row["key"]), str(idx), iid, rec.get("finish_reason") or "",
                                  str(rec.get("num_tokens")), "1" if closed else "0", "1" if extraction_failure else "0",
                                  "1" if aligned else "0", "1" if resp.strip() == "" else "0",
                                  v(gs), v(gl), v(rs), v(rl), v(rep), json.dumps(alts, separators=(",", ":"))]))
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(buf) + "\n")
    os.replace(tmp, out_path)
    return out_path, time.time() - t0, "done"


COLS = ["config", "run", "key", "idx", "iid", "finish", "ntok", "think_closed", "extraction_failure", "aligned",
        "empty", "gs", "gl", "rs", "rl", "rep", "alts"]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rows = load_dataset_rows()
    jobs = []
    for config in sorted(os.listdir(PANEL)):
        if not os.path.isdir(f"{PANEL}/{config}"):
            continue
        for fn in sorted(os.listdir(f"{PANEL}/{config}")):
            if fn.endswith(".jsonl"):
                jobs.append((config, fn[:-6], rows))
    print(len(jobs), "run files", flush=True)
    t0 = time.time()
    with mp.Pool(n) as pool:
        for k, (path, dt, status) in enumerate(pool.imap_unordered(grade_file, jobs)):
            print(f"[{k + 1}/{len(jobs)}] {status} {os.path.basename(path)} {dt:.0f}s elapsed {time.time() - t0:.0f}s", flush=True)
    print("ALL DONE", flush=True)
