"""Explore the data: per instruction id, count constraints, kwargs keys, and instruction lines in prompts.

Reads only case/data. Prints a summary and writes audit/scripts/out/instruction_texts.json.
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")
OUT = os.path.join(ROOT, "audit", "scripts", "out")
os.makedirs(OUT, exist_ok=True)

rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))
print("rows", len(rows))

count = collections.Counter()
keys = collections.defaultdict(collections.Counter)
values = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
examples = collections.defaultdict(list)
headers = collections.Counter()
prompt_mismatch = 0
n_lines_mismatch = 0
other_fields = collections.Counter()
grading_modes = collections.Counter()
n_messages = collections.Counter()
for row in rows:
    nu = row["extra_info"]["nemotron_ultra"]
    rec = json.loads(nu["record_json"])
    for k in rec:
        other_fields[k] += 1
    grading_modes[rec.get("grading_mode")] += 1
    n_messages[len(row["prompt"])] += 1
    content = row["prompt"][-1]["content"]
    if content != rec.get("prompt"):
        prompt_mismatch += 1
    ids = rec["instruction_id_list"]
    kws = rec["kwargs"]
    # find the instruction block: last paragraph with list items
    m = re.search(r"\n\n([^\n]*:)\n((?:(?:\d+\.|-|\*|•)[^\n]*(?:\n|$))+)\s*$", content)
    lines = None
    if m:
        headers[m.group(1)] += 1
        lines = [l for l in m.group(2).split("\n") if l.strip()]
        if len(lines) != len(ids):
            n_lines_mismatch += 1
            lines = None
    for i, (iid, kw) in enumerate(zip(ids, kws)):
        count[iid] += 1
        kw = kw or {}
        keys[iid][tuple(sorted(k for k, v in kw.items() if v is not None))] += 1
        for k, v in kw.items():
            if v is not None:
                values[iid][k][json.dumps(v, ensure_ascii=False)[:60]] += 1
        if lines is not None and len(examples[iid]) < 400:
            examples[iid].append({"line": lines[i], "kwargs": kw, "uuid": nu["uuid"]})

print("prompt == record prompt mismatches", prompt_mismatch)
print("instruction block not parsed into one line per constraint", n_lines_mismatch)
print("record fields", dict(other_fields))
print("grading_mode", dict(grading_modes))
print("messages per prompt", dict(n_messages))
print("headers", headers.most_common(40))
print("total constraints", sum(count.values()), "ids", len(count))
for iid, c in sorted(count.items()):
    print(f"\n== {iid}: {c}")
    print("   keys:", dict(keys[iid]))
    for k, vc in values[iid].items():
        print(f"   {k}: {len(vc)} distinct; top {vc.most_common(8)}")
    for ex in examples[iid][:3]:
        print("   ex:", ex["line"][:220])
with open(os.path.join(OUT, "instruction_texts.json"), "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=1)
