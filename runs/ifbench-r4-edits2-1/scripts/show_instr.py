"""Print, per instruction id, the non-null kwargs of each instance and the prompt tail of the first instances.

Usage: show_instr.py <id-prefix> [tail_chars] [n_tails]
"""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
rows = [json.loads(l) for l in open(W / "audit/frozen/dataset_rows.jsonl", encoding="utf-8")]
prefix = sys.argv[1]
tail = int(sys.argv[2]) if len(sys.argv) > 2 else 350
ntails = int(sys.argv[3]) if len(sys.argv) > 3 else 1

by = {}
for r in rows:
    for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
        if iid.startswith(prefix):
            by.setdefault(iid, []).append((r, {k: v for k, v in kw.items() if v is not None}))

for iid in sorted(by):
    print("=" * 10, iid, len(by[iid]))
    for j, (r, kw) in enumerate(by[iid]):
        multi = r["instruction_id_list"] if len(r["instruction_id_list"]) > 1 else ""
        print(f"  key={r['key']} kw={json.dumps(kw, ensure_ascii=False)} {multi}")
        if j < ntails:
            print("    TAIL:", repr(r["prompt"][-tail:]))
