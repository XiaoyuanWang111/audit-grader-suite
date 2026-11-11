"""Step 2 helper: dump, per instruction id, each prompt's tail and its kwargs (dataset only, no grader code)."""
import json
import os
import sys

import pandas as pd

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
df = pd.read_parquet(os.path.join(W, "case", "data", "train-00000-of-00001.parquet"))
TAIL = int(sys.argv[1]) if len(sys.argv) > 1 else 420
by_id = {}
for _, r in df.iterrows():
    for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
        kw = {k: v for k, v in kw.items() if v is not None}
        by_id.setdefault(iid, []).append((r["key"], list(r["instruction_id_list"]), kw, r["prompt"]))
os.makedirs(os.path.join(W, "audit", "work"), exist_ok=True)
with open(os.path.join(W, "audit", "work", "instr_texts.txt"), "w", encoding="utf-8", newline="\n") as f:
    for iid in sorted(by_id):
        f.write(f"===== {iid} ({len(by_id[iid])})\n")
        for key, ids, kw, prompt in by_id[iid]:
            f.write(f"--- key={key} ids={ids} kwargs={json.dumps(kw, ensure_ascii=False)}\n")
            tail = prompt[-TAIL:] if len(prompt) > TAIL else prompt
            f.write(("..." if len(prompt) > TAIL else "") + repr(tail) + "\n")
print("ok")
