"""Compare the HF parquet (the run's dataset) with the reference repo's two JSONL copies.

Prints per-row differences in prompt, instruction ids and kwargs (after dropping null kwargs and
casting integral floats), and the value types the parquet gives the grader.
"""
import json

import pandas as pd

W = "<W>"
df = pd.read_parquet(f"{W}/case/data/train-00000-of-00001.parquet")


def norm_kw(kw):
    out = {}
    for k, v in kw.items():
        if v is None:
            continue
        if hasattr(v, "tolist"):
            v = v.tolist()
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        out[k] = v
    return out


pq = {}
types = set()
for _, r in df.iterrows():
    for kw in r["kwargs"]:
        for k, v in kw.items():
            if v is not None:
                types.add((k, type(v).__name__))
    pq[r["key"]] = (r["prompt"], list(r["instruction_id_list"]), [norm_kw(k) for k in r["kwargs"]])
print("parquet kwarg value types:", sorted(types))

for path in ["case/reference/IFBench/data/IFBench_test.jsonl", "case/reference/IFBench/ifbench/data/IFBench_test.jsonl"]:
    rows = [json.loads(l) for l in open(f"{W}/{path}", encoding="utf-8") if l.strip()]
    jtypes = set()
    for r in rows:
        for kw in r["kwargs"]:
            for k, v in kw.items():
                if v is not None:
                    jtypes.add((k, type(v).__name__))
    print(f"\n{path}: {len(rows)} rows; kwarg types: {sorted(jtypes)}")
    keys = {str(r["key"]): r for r in rows}
    print("  keys only in parquet:", sorted(set(pq) - set(keys), key=int))
    print("  keys only in jsonl:", sorted(set(keys) - set(pq), key=int))
    for k in sorted(set(pq) & set(keys), key=int):
        p, ids, kws = pq[k]
        r = keys[k]
        rk = [norm_kw(x) for x in r["kwargs"]]
        diffs = []
        if r["prompt"] != p:
            i = next((j for j in range(min(len(p), len(r["prompt"]))) if p[j] != r["prompt"][j]), min(len(p), len(r["prompt"])))
            diffs.append(f"prompt differs at char {i}: parquet {p[i-20:i+30]!r} vs jsonl {r['prompt'][i-20:i+30]!r}")
        if r["instruction_id_list"] != ids:
            diffs.append(f"ids {ids} vs {r['instruction_id_list']}")
        if rk != kws:
            diffs.append(f"kwargs {json.dumps(kws, ensure_ascii=False)[:200]} vs {json.dumps(rk, ensure_ascii=False)[:200]}")
        if diffs:
            print(f"  key {k}: " + " | ".join(diffs))
