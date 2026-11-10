"""Dump the IFBench_test prompts grouped by instruction id (data only, no grader code)."""
import collections
import json
import sys

import pandas as pd

df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
by_id = collections.defaultdict(list)
n_multi = 0
for _, row in df.iterrows():
    ids = list(row["instruction_id_list"])
    if len(ids) > 1:
        n_multi += 1
    for iid, kw in zip(ids, row["kwargs"]):
        kw = {k: v for k, v in kw.items() if v is not None}
        by_id[iid].append((row["key"], kw, row["prompt"]))
print("rows", len(df), "multi-instruction rows", n_multi, "instruction ids", len(by_id))
with open("audit/work/dataset_by_id.txt", "w", encoding="utf-8", newline="\n") as f:
    for iid in sorted(by_id):
        items = by_id[iid]
        f.write(f"=== {iid}  n={len(items)}\n")
        for key, kw, prompt in items:
            f.write(f"--- key={key} kwargs={json.dumps(kw, ensure_ascii=False, default=str)}\n")
            f.write(prompt + "\n")
for iid in sorted(by_id):
    print(f"{len(by_id[iid]):3d} {iid}")
