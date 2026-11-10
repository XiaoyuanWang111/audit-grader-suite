"""Add the replacement grader's strict verdict (column x, G1 applied: unclosed reasoning fails) to
every audit/out/panel/*.tsv. Usage: python step5_add_replacement.py [--workers N]"""
import csv
import glob
import json
import os
import sys
from multiprocessing import Pool

W = "<W>"


def add(path):
    sys.path.insert(0, f"{W}/audit/lib")
    sys.path.insert(0, f"{W}/audit")
    import harness as H
    from replacement import grader as X
    base = os.path.basename(path)[:-4]
    cfg, run = base.rsplit("__", 1)
    recs = [json.loads(l) for l in open(f"{W}/case/panel/{cfg}/{run}.jsonl", encoding="utf-8")]
    raw_by_key = {r["key"]: r["raw_response"] for r in recs}
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    fields = [k for k in rows[0].keys() if k not in ("x", "xg")] + ["x", "xg"]
    # xg: every decision switch set to the grader's reading, G1 not applied (graded text = the
    # stored response, as the grader gets it), so that gi != xg isolates defects (findings)
    grader_reading = {k: ("grader" if k not in ("D-unique", "D-punct-set", "D-count-exact", "D-africa-set") else
                          {"D-africa-set": "order"}.get(k, "proposed")) for k in X.SWITCHES}
    resp_by_key = {r["key"]: r["response"] for r in recs}
    for r in rows:
        kw = H.kwargs_for(r["key"], r["check"], int_cast=True)
        prompt = H.row(r["key"])["prompt"]
        for col, fn in (("x", lambda: X.grade_completion(r["check"], raw_by_key[r["key"]], kw, prompt)),
                        ("xg", lambda: X.grade(r["check"], resp_by_key[r["key"]], kw, prompt, switches=grader_reading))):
            try:
                r[col] = fn()
            except Exception as e:  # noqa: BLE001
                r[col] = f"EXC:{type(e).__name__}"
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})
    os.replace(tmp, path)
    return base


if __name__ == "__main__":
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    files = sorted(glob.glob(f"{W}/audit/out/panel/*.tsv"))
    with Pool(workers) as pool:
        for n, b in enumerate(pool.imap_unordered(add, files), 1):
            print(f"[{n}/{len(files)}] {b}", flush=True)
