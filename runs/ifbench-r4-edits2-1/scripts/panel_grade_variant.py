"""Grade the panel with the replacement under one decision set (default: the grader's readings).

This separates score changes into decision effects (replacement proposal vs replacement with the grader's
readings) and defect effects (grader vs replacement with the grader's readings).
Output: audit/frozen/panel_rep_<name>.tsv.gz with columns config, run, key, idx, iid, rep_<name>.
"""
import csv
import gzip
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))

GRADER_READINGS = {
    "D-trailing-ws": "count",
    "D-word-split": "split",
    "D-list-label": "word",
    "D-punct-set": "six",
    "D-titlecase-minor": "all",
    "D-overlap-def": "char_resp",
    "D-balance": "equal",
    "D-palindrome-distinct": "occurrences",
    "D-vowel-paragraph": "one_line",
    "D-multiples-prose": "prose_ok",
    "D-custom-content": "complete",
    "D-nbb-after": "forbidden",
    "D-change-case": "change",
    "D-csv-space": "strict",
    "D-conjunction-role": "surface",
    "D-section": "whole",
    "D-wrapper-csv": "strict",
    "D-wrapper-template": "ok",
    "D-wrapper-list": "ok",
    "D-indent-single": "pass",
    "D-options-label": "strict",
    "D-japanese-mixed": "contains",
}
VARIANTS = {"graderreadings": GRADER_READINGS}


def grade_file(args):
    path_str, name = args
    import harness as H
    from replacement import contract_grader as R

    dec = VARIANTS[name]
    rows = {str(r["key"]): r for r in H.load_rows()}
    out = []
    path = Path(path_str)
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        row = rows[str(d["key"])]
        unclosed = R.extraction_failure(d["raw_response"])
        for idx, (iid, kw) in enumerate(zip(row["instruction_id_list"], row["kwargs"])):
            if unclosed:
                v = "0"
            else:
                try:
                    v = "1" if R.check(iid, kw, d["response"], row["prompt"], dec) else "0"
                except Exception as e:  # noqa: BLE001
                    v = "E:" + type(e).__name__
            out.append([path.parent.name, path.stem, str(d["key"]), str(idx), iid, v])
    return out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "graderreadings"
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    import harness as H

    files = sorted(str(p) for p in (H.CASE / "panel").glob("*/*.jsonl"))
    outp = H.W / "audit/frozen" / f"panel_rep_{name}.tsv.gz"
    t0 = time.time()
    with gzip.open(outp, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["config", "run", "key", "idx", "iid", f"rep_{name}"])
        with mp.Pool(nproc) as pool:
            for rows in pool.imap(grade_file, [(f, name) for f in files]):
                w.writerows(rows)
    print(f"done {name}: {time.time() - t0:.0f}s -> {outp}")


if __name__ == "__main__":
    main()
