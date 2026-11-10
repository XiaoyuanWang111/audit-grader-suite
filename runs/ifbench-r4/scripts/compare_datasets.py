"""Compare the parquet rows with the reference repository's two IFBench_test.jsonl copies.

Prints, per copy: row count, rows whose prompt / instruction ids / non-null kwargs differ
from the parquet (matched by key), and duplicate prompts in the parquet.
"""
import json
import os
from collections import Counter

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]


def nn(kws):
    out = []
    for k in kws:
        d = {}
        for a, b in k.items():
            if b is None:
                continue
            if isinstance(b, float) and b.is_integer():
                b = int(b)
            d[a] = b
        out.append(d)
    return out


def main():
    dup = [p for p, c in Counter(r["prompt"] for r in ROWS).items() if c > 1]
    print("duplicate prompts in parquet:", len(dup))
    for rel in ("case/reference/IFBench/data/IFBench_test.jsonl", "case/reference/IFBench/ifbench/data/IFBench_test.jsonl"):
        ref = [json.loads(l) for l in open(os.path.join(W, rel), encoding="utf-8") if l.strip()]
        by = {str(r["key"]): r for r in ref}
        dp = di = dk = missing = 0
        floats = Counter()
        for r in ROWS:
            x = by.get(str(r["key"]))
            if x is None:
                missing += 1
                continue
            dp += x["prompt"] != r["prompt"]
            di += x["instruction_id_list"] != r["instruction_id_list"]
            if nn(x["kwargs"]) != nn(r["kwargs"]):
                dk += 1
                if dk <= 3:
                    print("   kwargs differ key", r["key"], nn(x["kwargs"]), "| parquet", nn(r["kwargs"]))
            for k in x["kwargs"]:
                for a, b in k.items():
                    if isinstance(b, float):
                        floats[a] += 1
        print(f"{rel}: rows={len(ref)} missing_keys={missing} prompt_diff={dp} ids_diff={di} kwargs_diff={dk} float_kwargs_in_ref={dict(floats)}")
    pf = Counter()
    for r in ROWS:
        for k in r["kwargs"]:
            for a, b in k.items():
                if isinstance(b, float):
                    pf[a] += 1
    print("float-typed kwargs in parquet rows:", dict(pf))


if __name__ == "__main__":
    main()
