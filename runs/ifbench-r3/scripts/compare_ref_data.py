"""Compare the reference repository's test-data copies with the pinned parquet (data only)."""
import json, math
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
pq = {}
for _, r in df.iterrows():
    pq[str(r["key"])] = (r["prompt"], list(r["instruction_id_list"]),
                         [{k: v for k, v in kw.items() if v is not None} for kw in r["kwargs"]])
def norm_kw(kw):
    out = {}
    for k, v in kw.items():
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        if isinstance(v, int) and not isinstance(v, bool):
            v = float(v)
        out[k] = v
    return out
for path in ["case/reference/IFBench/data/IFBench_test.jsonl", "case/reference/IFBench/ifbench/data/IFBench_test.jsonl"]:
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    print(path, "records", len(recs), "fields", sorted(recs[0].keys()))
    diffs = 0
    for rec in recs:
        k = str(rec["key"])
        if k not in pq:
            print("  key not in parquet", k); diffs += 1; continue
        p, ids, kws = pq[k]
        if rec["prompt"] != p: print("  prompt differs", k); diffs += 1
        if list(rec["instruction_id_list"]) != ids: print("  ids differ", k, rec["instruction_id_list"], ids); diffs += 1
        a = [norm_kw(x) for x in rec["kwargs"]]; b = [norm_kw(x) for x in kws]
        if a != b:
            diffs += 1
            if diffs < 8: print("  kwargs differ", k, a, b)
    print("  differing records:", diffs, "; keys missing from file:", sorted(set(pq) - {str(r['key']) for r in recs})[:10])
