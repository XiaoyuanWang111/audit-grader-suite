"""Step 1: one sha256 per dataset row (canonical JSON of key, prompt, instruction_id_list, non-null kwargs)."""
import hashlib
import json

import pandas as pd

DATA = "<W>/case/data/train-00000-of-00001.parquet"
OUT = "<W>/audit/frozen/dataset_row_hashes.tsv"


def plain(v):
    if hasattr(v, "tolist"):
        v = v.tolist()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


df = pd.read_parquet(DATA)
lines = []
for _, r in df.iterrows():
    row = {
        "key": r["key"],
        "prompt": r["prompt"],
        "instruction_id_list": list(r["instruction_id_list"]),
        "kwargs": [{k: plain(v) for k, v in d.items() if v is not None} for d in r["kwargs"]],
    }
    s = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    lines.append(f"{r['key']}\t{hashlib.sha256(s.encode('utf-8')).hexdigest()}")
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("key\tsha256_canonical_json\n")
    f.write("\n".join(lines) + "\n")
print(len(lines), "rows ->", OUT)
