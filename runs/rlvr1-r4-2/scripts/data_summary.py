"""Summarize the 11,817 rows: per instruction id, counts, kwargs shapes and example instruction lines.

Reads only the data file. Writes audit/out/data_summary.json and audit/out/instruction_texts.json.
"""
import collections
import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT = W / "audit" / "out"

rows = [json.loads(line) for line in DATA.open(encoding="utf-8")]
print("rows", len(rows))

count = collections.Counter()
rows_per_id = collections.Counter()
kw_keys = collections.defaultdict(collections.Counter)
kw_values = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
texts = collections.defaultdict(collections.Counter)
headers = collections.Counter()
mismatch_prompt = 0
n_constraints = 0
item_count_mismatch = 0
other = collections.Counter()

ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+(.*)$")

for row in rows:
    nu = row["extra_info"]["nemotron_ultra"]
    rec = json.loads(nu["record_json"])
    msgs = row["prompt"]
    other["n_messages_%d" % len(msgs)] += 1
    other["roles_" + ",".join(m["role"] for m in msgs)] += 1
    content = msgs[-1]["content"]
    if rec.get("prompt") != content:
        mismatch_prompt += 1
    other["grading_mode_" + str(rec.get("grading_mode"))] += 1
    other["request_" + nu["request_json"]] += 1
    other["record_keys_" + ",".join(sorted(rec))] += 1
    ids = rec["instruction_id_list"]
    kws = rec["kwargs"]
    if len(ids) != len(kws):
        other["len_mismatch"] += 1
    n_constraints += len(ids)
    for i in set(ids):
        rows_per_id[i] += 1
    if len(set(ids)) != len(ids):
        other["duplicate_id_in_row"] += 1
    for i, kw in zip(ids, kws):
        count[i] += 1
        if kw is None:
            kw_keys[i]["<None>"] += 1
            continue
        kw_keys[i][",".join(sorted(kw))] += 1
        for k, v in kw.items():
            vv = json.dumps(v, ensure_ascii=False)
            if len(vv) > 60:
                vv = vv[:60] + "..."
            kw_values[i][k][vv] += 1
    # instruction lines: everything after the last blank line that precedes a header-like line
    parts = content.split("\n\n")
    tail = parts[-1]
    lines = tail.split("\n")
    header = lines[0]
    items = [ITEM.match(l).group(1) for l in lines[1:] if ITEM.match(l)]
    if len(items) == len(ids) and len(lines) - 1 == len(ids):
        headers[header] += 1
        for i, t in zip(ids, items):
            texts[i][t] += 1
    else:
        item_count_mismatch += 1

print("constraints", n_constraints, "ids", len(count))
print("prompt != record prompt:", mismatch_prompt)
print("rows whose last block does not parse as header + one item per constraint:", item_count_mismatch)
for k, v in sorted(other.items()):
    print(" ", v, k[:200])
print("headers (top 30):")
for h, c in headers.most_common(30):
    print("  ", c, repr(h))
summary = {}
for i in sorted(count):
    summary[i] = {
        "constraints": count[i],
        "rows": rows_per_id[i],
        "kwarg_key_sets": dict(kw_keys[i]),
        "kwarg_values": {k: dict(c.most_common(25)) for k, c in kw_values[i].items()},
        "n_distinct_kwarg_values": {k: len(c) for k, c in kw_values[i].items()},
    }
(OUT / "data_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
inst = {}
for i in sorted(texts):
    inst[i] = {"n_distinct_texts": len(texts[i]), "examples": [t for t, _ in texts[i].most_common(6)]}
(OUT / "instruction_texts.json").write_text(json.dumps(inst, indent=1, ensure_ascii=False), encoding="utf-8")
for i in sorted(count):
    print(f"{count[i]:6d} {rows_per_id[i]:6d} {i}  keys={dict(kw_keys[i])}")
