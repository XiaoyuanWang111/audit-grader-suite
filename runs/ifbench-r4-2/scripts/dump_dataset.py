"""Dump the IFBench_test rows grouped by instruction id: kwargs and prompt tails.

Reads only case/data. Writes audit/out/dataset_by_instruction.txt and
audit/out/row_hashes.tsv (one sha256 per row over key, prompt, ids, kwargs).
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[2]
df = pd.read_parquet(W / "case/data/train-00000-of-00001.parquet")

def clean_kwargs(kw):
    return {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in kw.items() if v is not None}

by_id = defaultdict(list)
rows_out = []
for _, r in df.iterrows():
    ids = list(r["instruction_id_list"])
    kws = [clean_kwargs(k) for k in r["kwargs"]]
    canon = json.dumps({"key": r["key"], "prompt": r["prompt"], "instruction_id_list": ids, "kwargs": kws},
                       sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    rows_out.append((r["key"], h, ",".join(ids)))
    for i, k in zip(ids, kws):
        by_id[i].append((r["key"], k, r["prompt"]))

with open(W / "audit/out/row_hashes.tsv", "w", newline="\n", encoding="utf-8") as f:
    f.write("key\tsha256\tinstruction_ids\n")
    for row in rows_out:
        f.write("\t".join(row) + "\n")

with open(W / "audit/out/dataset_by_instruction.txt", "w", newline="\n", encoding="utf-8") as f:
    f.write(f"rows={len(df)} instruction_types={len(by_id)} instruction_instances={sum(len(v) for v in by_id.values())}\n")
    multi = sum(1 for _, r in df.iterrows() if len(r['instruction_id_list']) > 1)
    f.write(f"rows_with_more_than_one_instruction={multi}\n\n")
    for iid in sorted(by_id):
        items = by_id[iid]
        f.write(f"=== {iid}  n={len(items)}\n")
        for key, k, p in items[:3]:
            tail = p[-450:].replace("\n", "\\n")
            f.write(f"  key={key} kwargs={json.dumps(k, ensure_ascii=False)}\n    tail: ...{tail}\n")
        f.write("\n")
print("ok", len(by_id))
