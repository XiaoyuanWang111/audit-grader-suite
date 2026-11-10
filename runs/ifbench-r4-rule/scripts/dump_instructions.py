"""Dump, per instruction id, the dataset rows that use it: kwargs and the prompt tail.

Reads only the dataset parquet (task text), never grader code.
"""
import collections
import json
import sys

import pandas as pd

W = "<W>"
df = pd.read_parquet(f"{W}/case/data/train-00000-of-00001.parquet")

by_id = collections.defaultdict(list)
for _, row in df.iterrows():
    ids = list(row["instruction_id_list"])
    for i, iid in enumerate(ids):
        kw = {k: v for k, v in row["kwargs"][i].items() if v is not None}
        by_id[iid].append((row["key"], len(ids), kw, row["prompt"]))

out = open(f"{W}/audit/out/instructions_dump.txt", "w", encoding="utf-8", newline="\n")
print(f"{len(by_id)} instruction ids; rows per id:", file=out)
for iid in sorted(by_id):
    print(f"  {iid}: {len(by_id[iid])}", file=out)
for iid in sorted(by_id):
    rows = by_id[iid]
    print("\n" + "=" * 100, file=out)
    print(f"{iid}  ({len(rows)} rows)", file=out)
    for key, nids, kw, prompt in rows[:3]:
        def conv(v):
            if hasattr(v, "tolist"):
                return v.tolist()
            return v
        kw = {k: conv(v) for k, v in kw.items()}
        print(f"-- key={key} n_instr={nids} kwargs={json.dumps(kw, ensure_ascii=False)[:600]}", file=out)
        tail = prompt[-700:]
        print("   PROMPT TAIL: " + tail.replace("\n", "\\n"), file=out)
    # all kwargs values summary
    allkw = collections.defaultdict(set)
    for key, nids, kw, prompt in rows:
        for k, v in kw.items():
            if hasattr(v, "tolist"):
                v = json.dumps(v.tolist(), ensure_ascii=False)
            allkw[k].add(str(v)[:80])
    print("   ALL KWARG VALUES: " + json.dumps({k: sorted(v)[:30] for k, v in allkw.items()}, ensure_ascii=False), file=out)
out.close()
print("ok")
