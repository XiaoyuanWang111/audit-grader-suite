import collections, json, sys
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
by_id = collections.defaultdict(list)
for _, row in df.iterrows():
    for iid, kw in zip(list(row["instruction_id_list"]), row["kwargs"]):
        kw = {k: v for k, v in kw.items() if v is not None}
        by_id[iid].append((row["key"], list(row["instruction_id_list"]), kw, row["prompt"]))
sel = sys.argv[1:]
for iid in sorted(by_id):
    if sel and not any(iid.startswith(s) for s in sel):
        continue
    items = sorted(by_id[iid], key=lambda t: len(t[3]))
    key, ids, kw, prompt = items[0]
    print(f"=== {iid} n={len(items)} shortest key={key} ids={ids}")
    print(f"    kwargs={json.dumps(kw, ensure_ascii=False, default=str)[:600]}")
    print("    PROMPT: " + prompt[:900].replace("\n", "\n") + (" [...]" if len(prompt) > 900 else ""))
