"""Recompute the replacement's verdicts (p, alt) for the rows of the given checks in panel_verdicts.jsonl.

Used once after fixing a crash in the replacement's count:pronouns reading C (a dict where a set
was meant made every count:pronouns row raise). Grader and reference columns are not touched.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/regrade_replacement_rows.py count:pronouns
"""
import json
import os
import sys
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "replacement"))
sys.path.insert(0, os.path.join(W, "audit", "scripts"))
import ifb  # noqa: E402

SRC = os.path.join(W, "audit", "work", "panel_verdicts.jsonl")


def job(args):
    import ifbench_contract as rep
    from grade_panel import ALT
    row, prompt, kw, resp, ef = args
    try:
        p = False if ef else rep.check(row["iid"], kw, prompt, resp)
        alt = {}
        for a in ALT.get(row["iid"], []):
            d, letter = a.split(":")
            alt[a] = False if ef else rep.check(row["iid"], kw, prompt, resp, {d: letter})
        err = None
    except Exception as e:  # noqa: BLE001
        p, alt, err = None, {}, f"{type(e).__name__}: {str(e)[:120]}"
    return p, alt, err


def main():
    checks = set(sys.argv[1:])
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    ds = {r["key"]: r for r in ifb.load_rows()}
    recs = {(c, run, rec["key"]): rec for c, run, i, rec in ifb.iter_panel()}
    idx = [i for i, r in enumerate(rows) if r["iid"] in checks]
    args = []
    for i in idx:
        r = rows[i]
        d = ds[r["key"]]
        rec = recs[(r["cfg"], r["run"], r["key"])]
        args.append((r, d["prompt"], d["kwargs"][r["j"]], rec["response"], r["extraction_failure"]))
    with Pool(16) as pool:
        res = pool.map(job, args, chunksize=20)
    for i, (p, alt, err) in zip(idx, res):
        rows[i]["p"] = p
        rows[i]["alt"] = alt
        rows[i]["err"] = {k: v for k, v in rows[i]["err"].items() if k != "replacement"}
        if err:
            rows[i]["err"]["replacement"] = err
    with open(SRC, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("recomputed", len(idx), "rows; errors", sum(1 for x in res if x[2]))


if __name__ == "__main__":
    main()
