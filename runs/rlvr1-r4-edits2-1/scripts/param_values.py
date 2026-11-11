"""Distribution of kwargs values per instruction id (data only)."""
import json
import re
from collections import Counter, defaultdict

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]
vals = defaultdict(Counter)
combos = Counter()
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    ids = rec["instruction_id_list"]
    combos[len(set(ids)) != len(ids)] += 1
    for iid, args in zip(ids, rec["kwargs"]):
        for k, v in (args or {}).items():
            if v is None:
                continue
            key = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            vals[(iid, k)][key] += 1
    if "count:counting_composition" in ids:
        p = rec["prompt"]
        i = p.find("each sentence")
        print("COUNTING_COMPOSITION:", repr(p[max(0, i - 400): i + 40]))
print("rows with a repeated id:", combos)
for (iid, k), c in sorted(vals.items()):
    items = c.most_common()
    print(f"{iid} {k}: {len(items)} distinct;", "; ".join(f"{v!s}x{n}" for v, n in items[:25])[:900])
