import collections, json
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
by_id = collections.defaultdict(list)
combos = collections.Counter()
for _, row in df.iterrows():
    ids = list(row["instruction_id_list"])
    if len(ids) > 1:
        combos[tuple(ids)] += 1
    for iid, kw in zip(ids, row["kwargs"]):
        kw = {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in kw.items() if v is not None}
        for k in ("reference_text", "prompt_to_repeat"):
            if k in kw:
                kw[k] = f"<{len(kw[k])} chars>"
        by_id[iid].append(f"{row['key']}:{json.dumps(kw, ensure_ascii=False)}")
for iid in sorted(by_id):
    if all(x.endswith(":{}") for x in by_id[iid]):
        print(f"{iid}: keys {[x.split(':')[0] for x in by_id[iid]]} (no kwargs)")
    else:
        print(f"{iid}: " + " | ".join(by_id[iid]))
print("combos:")
for c, n in combos.most_common():
    print(" ", n, c)
