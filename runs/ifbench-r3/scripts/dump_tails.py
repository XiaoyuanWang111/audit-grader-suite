import collections, json, sys
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
by_id = collections.defaultdict(list)
for _, row in df.iterrows():
    for iid, kw in zip(list(row["instruction_id_list"]), row["kwargs"]):
        kw = {k: v for k, v in kw.items() if v is not None}
        by_id[iid].append((row["key"], list(row["instruction_id_list"]), kw, row["prompt"]))
sel = sys.argv[1:]  # prefixes
first_n = 420
rest_n = 170
for iid in sorted(by_id):
    if sel and not any(iid.startswith(s) for s in sel):
        continue
    print(f"=== {iid} n={len(by_id[iid])}")
    for i, (key, ids, kw, prompt) in enumerate(by_id[iid]):
        n = first_n if i == 0 else rest_n
        other = [x for x in ids if x != iid]
        tail = prompt[-n:].replace("\n", "\n")
        print(f"[{key}] {json.dumps(kw, ensure_ascii=False, default=str)}" + (f" +{other}" if other else ""))
        print("   ..." + tail)
