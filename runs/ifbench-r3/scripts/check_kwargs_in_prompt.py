"""Check that every kwarg value of every instruction appears in the prompt text the model sees."""
import json
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
for _, row in df.iterrows():
    p = row["prompt"]
    for iid, kw in zip(list(row["instruction_id_list"]), row["kwargs"]):
        for k, v in kw.items():
            if v is None:
                continue
            if isinstance(v, float):
                vs = str(int(v)) if v.is_integer() else str(v)
                exact_float = str(v)
                if exact_float in p and v.is_integer():
                    print(f"key={row['key']} {iid} {k}={v!r}: prompt shows float form {exact_float!r}")
            else:
                vs = str(v)
            if vs not in p:
                print(f"key={row['key']} {iid} {k}={vs[:120]!r}: NOT FOUND in prompt")
