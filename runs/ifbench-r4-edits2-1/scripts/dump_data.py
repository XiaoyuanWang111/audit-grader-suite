"""Dump the IFBench_test parquet into JSONL with the value types that Hugging Face `datasets` returns.

pyarrow's to_pylist keeps int64 kwargs (n, m, n_start, n_end) as int and double kwargs as float,
as `datasets` does; pandas would turn the int64 columns with nulls into floats.
Also records per-row hashes and lists the instruction ids.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

W = Path(__file__).resolve().parents[2]
table = pq.read_table(W / "case/data/train-00000-of-00001.parquet")
rows = table.to_pylist()
print("columns:", table.column_names, "rows:", len(rows))

out = W / "audit/frozen/dataset_rows.jsonl"
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

hashes = W / "audit/frozen/dataset_row_sha256.tsv"
with open(hashes, "w", encoding="utf-8", newline="\n") as f:
    f.write("row\tkey\tsha256_of_canonical_json\n")
    for i, row in enumerate(rows):
        h = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        f.write(f"{i}\t{row.get('key')}\t{h}\n")

ids = Counter()
for row in rows:
    for iid in row["instruction_id_list"]:
        ids[iid] += 1
print("distinct instruction ids:", len(ids), "instances:", sum(ids.values()))
types = Counter()
for row in rows:
    for kw in row["kwargs"]:
        for k, v in kw.items():
            if v is not None:
                types[(k, type(v).__name__)] += 1
print("kwarg value types:", dict(types))
