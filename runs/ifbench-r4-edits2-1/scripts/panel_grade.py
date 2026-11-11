"""Step 5: grade every stored panel response with the grader (strict, loose), the reference pipeline
(strict, loose) and the replacement (proposed readings, plus alternative readings per decision).

Output: audit/frozen/panel_verdicts.tsv.gz, one row per (response, instruction).
Usage: panel_grade.py [n_procs] [file_filter_substring]
"""
import csv
import gzip
import io
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))

# alternative readings measured per decision: (decision, alternative value, checks it can change)
ALTS = [
    ("D-trailing-ws", "count", None),
    ("D-sentence-fragment", "drop", None),
    ("D-word-split", "split", None),
    ("D-list-label", "word", None),
    ("D-vacuous", "fail", ["format:emoji", "words:alphabet"]),
    ("D-count-exact", "atleast", ["count:keywords_multiple"]),
    ("D-keyword-form", "prefix", ["count:keywords_multiple"]),
    ("D-punct-set", "six", ["count:punctuation"]),
    ("D-punct-set", "ascii", ["count:punctuation"]),
    ("D-unique", "hapax", ["count:unique_word_count"]),
    ("D-between", "exclusive", ["count:word_count_range"]),
    ("D-titlecase-minor", "all", ["format:title_case"]),
    ("D-overlap-def", "char_resp", ["ratio:overlap"]),
    ("D-overlap-def", "word_ref", ["ratio:overlap"]),
    ("D-overlap-def", "jaccard", ["ratio:overlap"]),
    ("D-balance", "equal", ["ratio:sentence_balance"]),
    ("D-different-words", "across", ["ratio:sentence_words"]),
    ("D-repeat-count", "n_plus_1", ["words:repeats"]),
    ("D-palindrome-distinct", "occurrences", ["words:palindrome"]),
    ("D-vowel-scope", "per_word_atmost3", ["words:vowel"]),
    ("D-vowel-scope", "response_exactly3", ["words:vowel"]),
    ("D-vowel-paragraph", "one_line", ["words:vowel"]),
    ("D-options-extra", "contains", ["format:options"]),
    ("D-multiples-prose", "prose_ok", ["custom:multiples"]),
    ("D-custom-content", "complete", ["custom:european_capitals_sort", "custom:reverse_newline"]),
    ("D-nbb-after", "forbidden", ["format:no_bullets_bullets"]),
    ("D-index-base", 1, ["repeat:repeat_span"]),
    ("D-change-case", "change", ["repeat:repeat_change"]),
    ("D-csv-space", "strict", ["custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"]),
    ("D-conjunction-role", "surface", ["count:conjunctions"]),
    ("D-section", "whole", ["format:thesis"]),
    ("D-wrapper-csv", "strict", ["custom:csv_city", "custom:csv_quotes", "custom:csv_special_character"]),
    ("D-wrapper-template", "ok", ["format:output_template"]),
    ("D-wrapper-list", "ok", ["custom:reverse_newline"]),
    ("D-indent-single", "pass", ["format:line_indent"]),
    ("D-options-label", "strict", ["format:options"]),
    ("D-japanese-mixed", "contains", ["count:words_japanese"]),
]
ALT_COLS = [f"alt:{d}={v}" for d, v, _ in ALTS]
COLS = ["config", "run", "key", "idx", "iid", "finish", "unclosed", "empty", "num_tokens",
        "g_strict", "g_loose", "r_strict", "r_loose", "rep"] + ALT_COLS


def _v(fn):
    try:
        return "1" if fn() else "0"
    except Exception as e:  # grading failure
        return "E:" + type(e).__name__


def grade_file(path_str):
    import harness as H
    from replacement import contract_grader as R

    path = Path(path_str)
    rows = {str(r["key"]): r for r in H.load_rows()}
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        row = rows[str(d["key"])]
        resp, raw = d["response"], d["raw_response"]
        unclosed = R.extraction_failure(raw)
        g_s = H.grader_modules()["grader"]
        # per-prompt harness calls (they build every checker for the prompt); exceptions caught per prompt
        def per_prompt(fn):
            try:
                return [("1" if x else "0") for x in fn()]
            except Exception as e:
                return None, type(e).__name__

        res = {}
        for name, fn in (("g_strict", lambda: H.grade_grader(row, resp, "strict")),
                         ("g_loose", lambda: H.grade_grader(row, resp, "loose")),
                         ("r_strict", lambda: H.grade_reference(row, resp, "strict")),
                         ("r_loose", lambda: H.grade_reference(row, resp, "loose"))):
            try:
                res[name] = ["1" if x else "0" for x in fn()]
            except Exception as e:
                # fall back to per-instruction grading to locate the failing check
                vals = []
                for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
                    one = {"key": row["key"], "prompt": row["prompt"], "instruction_id_list": [iid], "kwargs": [kw]}
                    if name.startswith("g_"):
                        vals.append(_v(lambda: H.grade_grader(one, resp, name[2:])[0]))
                    else:
                        vals.append(_v(lambda: H.grade_reference(one, resp, name[2:])[0]))
                res[name] = vals
        for idx, (iid, kw) in enumerate(zip(row["instruction_id_list"], row["kwargs"])):
            if unclosed:
                rep = "0"
            else:
                rep = _v(lambda: R.check(iid, kw, resp, row["prompt"]))
            alts = []
            for dname, val, checks in ALTS:
                if checks is not None and iid not in checks:
                    alts.append(rep)
                elif unclosed:
                    alts.append("0")
                else:
                    alts.append(_v(lambda: R.check(iid, kw, resp, row["prompt"], {dname: val})))
            out.append([path.parent.name, path.stem, str(d["key"]), str(idx), iid, str(d["finish_reason"]),
                        "1" if unclosed else "0", "1" if not resp.strip() else "0", str(d["num_tokens"]),
                        res["g_strict"][idx], res["g_loose"][idx], res["r_strict"][idx], res["r_loose"][idx], rep] + alts)
    return out


def main():
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    filt = sys.argv[2] if len(sys.argv) > 2 else ""
    import harness as H

    files = sorted(str(p) for p in (H.CASE / "panel").glob("*/*.jsonl") if filt in p.as_posix())
    t0 = time.time()
    outp = H.W / "audit/frozen" / ("panel_verdicts.tsv.gz" if not filt else f"panel_verdicts_{filt.replace('/', '_')}.tsv.gz")
    n = 0
    with gzip.open(outp, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLS)
        with mp.Pool(nproc) as pool:
            for k, rows in enumerate(pool.imap(grade_file, files)):
                w.writerows(rows)
                n += len(rows)
                if k % 10 == 0:
                    print(f"{k + 1}/{len(files)} files, {n} rows, {time.time() - t0:.0f}s", flush=True)
    print(f"done: {len(files)} files, {n} rows, {time.time() - t0:.0f}s -> {outp}")


if __name__ == "__main__":
    main()
