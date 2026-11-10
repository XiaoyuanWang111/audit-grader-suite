"""Pin the IFBench_test parquet: schema, one sha256 per row, instruction-id counts.

Writes audit/frozen/dataset_rows.tsv (row index, key, sha256 of the row's canonical JSON)
and audit/frozen/dataset_rows.jsonl (the rows as JSON, for later scripts).
"""
import hashlib
import json
import os
from collections import Counter

import pyarrow.parquet as pq

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(W, "case", "data", "train-00000-of-00001.parquet")


def canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main():
    t = pq.read_table(P)
    print("schema:")
    print(t.schema)
    rows = t.to_pylist()
    print("rows:", len(rows))
    out_tsv = os.path.join(W, "audit", "frozen", "dataset_rows.tsv")
    out_jsonl = os.path.join(W, "audit", "frozen", "dataset_rows.jsonl")
    c = Counter()
    nper = Counter()
    with open(out_tsv, "w", encoding="utf-8", newline="\n") as ft, open(out_jsonl, "w", encoding="utf-8", newline="\n") as fj:
        ft.write("row\tkey\tsha256\n")
        for i, r in enumerate(rows):
            h = hashlib.sha256(canon(r).encode("utf-8")).hexdigest()
            ft.write(f"{i}\t{r.get('key')}\t{h}\n")
            fj.write(canon(r) + "\n")
            ids = r["instruction_id_list"]
            nper[len(ids)] += 1
            for x in ids:
                c[x] += 1
    print("instructions per prompt:", dict(nper))
    print("distinct instruction ids:", len(c))
    for k, v in sorted(c.items()):
        print(f"  {k}\t{v}")


if __name__ == "__main__":
    main()
