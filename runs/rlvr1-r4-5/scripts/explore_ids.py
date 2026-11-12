"""Survey instruction ids, kwargs and prompt layouts in the data (no grader code read)."""
import collections
import json
import re
import sys

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

ids = collections.Counter()
kw_keys = collections.defaultdict(collections.Counter)
kw_vals = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
n_per_row = collections.Counter()
datasets = collections.Counter()
grading = collections.Counter()
other_keys = collections.Counter()
prompt_eq = 0
user_eq = 0
for row in rows:
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    other_keys.update(rec.keys())
    datasets[rec.get("dataset")] += 1
    grading[rec.get("grading_mode")] += 1
    n_per_row[len(rec["instruction_id_list"])] += 1
    if rec.get("prompt") == row["prompt"][0]["content"]:
        prompt_eq += 1
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        ids[iid] += 1
        kw = kw or {}
        kw_keys[iid][tuple(sorted(k for k, v in kw.items() if v is not None))] += 1
        for k, v in kw.items():
            if v is None:
                continue
            kw_vals[iid][k][json.dumps(v, ensure_ascii=False)[:60]] += 1

print("rows", len(rows), "constraints", sum(ids.values()), "ids", len(ids))
print("record keys", dict(other_keys))
print("datasets", dict(datasets))
print("grading_mode", dict(grading))
print("constraints per row", dict(sorted(n_per_row.items())))
print("record prompt == user message:", prompt_eq)
for iid, n in sorted(ids.items()):
    print(f"\n== {iid}  n={n}")
    for keys, c in kw_keys[iid].most_common():
        print("   keys", keys, c)
    for k, cnt in kw_vals[iid].items():
        top = cnt.most_common(8)
        print(f"   {k}: {len(cnt)} distinct; top {top}")
