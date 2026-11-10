p = "audit/scripts/pin_inputs.py"
s = open(p, encoding="utf-8").read()
old = '''df = pd.read_parquet(os.path.join(CASE, "data/train-00000-of-00001.parquet"))
lines = []
for _, r in df.iterrows():
    obj = {"key": r["key"], "prompt": r["prompt"], "instruction_id_list": list(r["instruction_id_list"]),
           "kwargs": [{k: v for k, v in kw.items() if v is not None} for kw in r["kwargs"]]}'''
new = '''import pyarrow.parquet as pq
df = pq.read_table(os.path.join(CASE, "data/train-00000-of-00001.parquet")).to_pylist()  # native types, as datasets gives them
lines = []
for r in df:
    obj = {"key": r["key"], "prompt": r["prompt"], "instruction_id_list": list(r["instruction_id_list"]),
           "kwargs": [{k: v for k, v in kw.items() if v is not None} for kw in r["kwargs"]]}'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
