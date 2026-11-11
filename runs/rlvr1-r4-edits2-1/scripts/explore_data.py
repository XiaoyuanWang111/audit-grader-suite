"""Explore the data rows: structure, instruction ids, kwargs keys (no grader code)."""
import json
import sys
from collections import Counter, defaultdict

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))
print("rows", len(rows))
r0 = rows[0]
print("columns", list(r0.keys()))
print("data_source", r0["data_source"], "env_class", r0["env_class"])
print("reward_model", json.dumps(r0["reward_model"])[:300])
ei = r0["extra_info"]
print("extra_info keys", list(ei.keys()))
nu = ei["nemotron_ultra"]
print("nemotron_ultra keys", list(nu.keys()))
for k, v in nu.items():
    s = v if isinstance(v, str) else json.dumps(v)
    print(" ", k, ":", s[:300])
rec = json.loads(nu["record_json"])
print("record keys", list(rec.keys()))
for k, v in rec.items():
    print("  rec", k, ":", json.dumps(v)[:300])
print("prompt type", type(r0["prompt"]), json.dumps(r0["prompt"])[:600])

ids = Counter()
kw = defaultdict(Counter)
rows_per_id = Counter()
ncons = Counter()
other_keys = Counter()
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    for k in rec:
        other_keys[k] += 1
    ncons[len(rec["instruction_id_list"])] += 1
    seen = set()
    for iid, args in zip(rec["instruction_id_list"], rec["kwargs"]):
        ids[iid] += 1
        seen.add(iid)
        for k, v in (args or {}).items():
            if v is not None:
                kw[iid][k] += 1
    for s in seen:
        rows_per_id[s] += 1
print("record key counts", dict(other_keys))
print("constraints per row", sorted(ncons.items()))
print("total constraints", sum(ids.values()), "ids", len(ids))
for iid, c in sorted(ids.items()):
    print(f"{iid:45s} {c:6d} rows={rows_per_id[iid]:6d} kwargs={dict(kw[iid])}")
