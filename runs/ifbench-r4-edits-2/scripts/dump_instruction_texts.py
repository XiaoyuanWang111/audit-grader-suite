"""Dump, per instruction id, the prompt tails and non-null kwargs from the dataset.

Used to write contracts from the text the model sees (step 2). Reads only the
dataset parquet.
"""
import collections
import json
import sys

import pandas as pd

DATA = "<W>/case/data/train-00000-of-00001.parquet"
OUT = "<W>/audit/work/instruction_texts.txt"

df = pd.read_parquet(DATA)
by_id = collections.defaultdict(list)
for _, r in df.iterrows():
    ids = list(r["instruction_id_list"])
    kws = [{k: v for k, v in d.items() if v is not None} for d in r["kwargs"]]
    for i, iid in enumerate(ids):
        by_id[iid].append((r["key"], ids, kws, r["prompt"]))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for iid in sorted(by_id):
        rows = by_id[iid]
        f.write(f"=== {iid} ({len(rows)} prompts)\n")
        for n, (key, ids, kws, prompt) in enumerate(rows):
            kw = kws[ids.index(iid)]
            kw = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in kw.items()}
            f.write(f"  key={key} ids={ids} kwargs={json.dumps(kw, ensure_ascii=False, default=str)}\n")
            tail = 500 if n < 2 or len(ids) > 1 else 0
            if tail:
                f.write("  TAIL: " + prompt[-tail:].replace("\n", "\\n") + "\n")
        f.write("\n")
print("wrote", OUT)
