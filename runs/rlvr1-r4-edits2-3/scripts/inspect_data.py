"""Inspect the data rows' structure (no grader code is read or imported)."""
import json
import collections
import sys

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(PATH, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))
print("rows", len(rows))
r0 = rows[0]
print("columns", list(r0.keys()))
print("data_source", r0["data_source"], "env_class", r0["env_class"])
print("reward_model", json.dumps(r0["reward_model"], ensure_ascii=False)[:600])
ei = r0["extra_info"]
print("extra_info keys", list(ei.keys()))
nu = ei["nemotron_ultra"]
print("nemotron_ultra keys", list(nu.keys()))
for k, v in nu.items():
    if k != "record_json":
        print(" ", k, "=", json.dumps(v, ensure_ascii=False)[:300])
rec = json.loads(nu["record_json"])
print("record keys", list(rec.keys()))
for k, v in rec.items():
    print(" rec", k, "=", json.dumps(v, ensure_ascii=False)[:400])
print("prompt type", type(r0["prompt"]), json.dumps(r0["prompt"], ensure_ascii=False)[:1500])

ids = collections.Counter()
kwkeys = collections.defaultdict(collections.Counter)
nrow_by_n = collections.Counter()
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    nrow_by_n[len(rec["instruction_id_list"])] += 1
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        ids[iid] += 1
        for k, v in (kw or {}).items():
            if v is not None:
                kwkeys[iid][k] += 1
print("constraints", sum(ids.values()), "ids", len(ids))
print("rows by n constraints", sorted(nrow_by_n.items()))
for iid, c in sorted(ids.items()):
    print(f"{c:6d} {iid} {dict(kwkeys[iid])}")
