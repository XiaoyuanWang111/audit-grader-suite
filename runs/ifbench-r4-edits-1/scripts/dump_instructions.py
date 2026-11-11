"""Dump each instruction type with its non-null kwargs and the prompt tail.

Reads only the dataset (the text the model sees plus the kwargs); no grader code.
Writes audit/work/instructions_by_type.txt.
"""
import collections
import json
import pathlib

import pandas as pd

W = pathlib.Path(__file__).resolve().parents[2]
df = pd.read_parquet(W / "case/data/train-00000-of-00001.parquet")

by_type = collections.defaultdict(list)
n_instr = collections.Counter()
for _, r in df.iterrows():
    ids = list(r["instruction_id_list"])
    n_instr[len(ids)] += 1
    for iid, kw in zip(ids, r["kwargs"]):
        kw = {k: v for k, v in kw.items() if v is not None}
        by_type[iid].append((r["key"], kw, r["prompt"]))

out = []
out.append(f"rows={len(df)} instructions-per-row={dict(n_instr)} types={len(by_type)}")
for iid in sorted(by_type):
    rows = by_type[iid]
    out.append("=" * 100)
    out.append(f"{iid}  n={len(rows)}")
    for key, kw, prompt in rows:
        def conv(v):
            try:
                return v.tolist()
            except AttributeError:
                return v
        kw = {k: conv(v) for k, v in kw.items()}
        out.append(f"-- key={key} kwargs={json.dumps(kw, ensure_ascii=False)}")
        tail = prompt[-700:] if len(prompt) > 700 else prompt
        out.append("   TAIL: " + tail.replace("\n", "\\n"))
(W / "audit/work/instructions_by_type.txt").write_text("\n".join(out), encoding="utf-8", newline="\n")
print(out[0])
for iid in sorted(by_type):
    print(iid, len(by_type[iid]))
