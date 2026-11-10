"""Step 5: grade every stored panel response with every grader.

For each run file, writes audit/out/panel/<config>__<run>.tsv with one line per (row, check):
  key, check index, check, finish_reason, flags, and verdicts
  g  = grader strict, kwargs as loaded from the HF parquet (floats)   -> True/False/EXC:...
  gi = grader strict, int-cast kwargs
  gl = grader loose, as loaded;  gli = grader loose, int-cast
  r  = reference strict (its own evaluation_lib, int kwargs);  rl = reference loose
  x  = replacement strict (audit/replacement), added when the module exists
The graded text is the stored `response` field (text after the last </think>, as CONFIGS.md says).
flags: U = unclosed reasoning (extraction failure under the contract), T = truncated (length),
E = empty response.

Usage: python step5_grade_panel.py [--workers N] [--only-missing] [--with-replacement]
"""
import glob
import json
import os
import sys
from multiprocessing import Pool

W = "<W>"
OUT = f"{W}/audit/out/panel"


def grade_file(args):
    path, with_repl = args
    sys.path.insert(0, f"{W}/audit/lib")
    import harness as H
    repl = None
    if with_repl:
        sys.path.insert(0, f"{W}/audit")
        from replacement import grader as repl  # noqa: F811
    cfg = os.path.basename(os.path.dirname(path))
    run = os.path.basename(path)[:-6]
    dest = f"{OUT}/{cfg}__{run}.tsv"
    lines = [json.loads(l) for l in open(path, encoding="utf-8")]
    out = []
    for i, rec in enumerate(lines):
        r = H.dataset()[i]
        assert r["key"] == rec["key"]
        resp, raw = rec["response"], rec["raw_response"]
        flags = ""
        if "<think>" in raw and "</think>" not in raw:
            flags += "U"
        if rec["finish_reason"] == "length":
            flags += "T"
        if not resp.strip():
            flags += "E"
        for j, iid in enumerate(r["instruction_id_list"]):
            g = H.grade(iid, resp, key=r["key"])
            gi = H.grade(iid, resp, key=r["key"], int_cast=True)
            gl = H.grade(iid, resp, key=r["key"], mode="loose")
            gli = H.grade(iid, resp, key=r["key"], mode="loose", int_cast=True)
            rs = H.grade(iid, resp, key=r["key"], impl="reference")
            rl = H.grade(iid, resp, key=r["key"], impl="reference", mode="loose")
            row = [rec["key"], j, iid, rec["finish_reason"], flags, g, gi, gl, gli, rs, rl]
            if repl is not None:
                row.append(repl.grade(iid, resp, H.kwargs_for(r["key"], iid, int_cast=True), r["prompt"]))
            out.append("\t".join(str(x) for x in row))
    hdr = "key\tj\tcheck\tfinish\tflags\tg\tgi\tgl\tgli\tr\trl" + ("\tx" if repl is not None else "")
    tmp = dest + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(hdr + "\n" + "\n".join(out) + "\n")
    os.replace(tmp, dest)
    return dest


if __name__ == "__main__":
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    with_repl = "--with-replacement" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(f"{W}/case/panel/*/*.jsonl"))
    if "--only-missing" in sys.argv:
        files = [p for p in files if not os.path.exists(
            f"{OUT}/{os.path.basename(os.path.dirname(p))}__{os.path.basename(p)[:-6]}.tsv")]
    print(f"{len(files)} files, {workers} workers", flush=True)
    with Pool(workers) as pool:
        for n, d in enumerate(pool.imap_unordered(grade_file, [(p, with_repl) for p in files]), 1):
            print(f"[{n}/{len(files)}] {os.path.basename(d)}", flush=True)
