"""Collect the requirement text the model sees for each instruction id (data only).

For rows whose requirements appear as a numbered or bulleted list after a lead-in
line, the list items follow instruction_id_list order. Each item is turned into a
template by replacing the constraint's kwargs values with {key} placeholders.
Writes audit/instruction_texts.json: id -> list of (template, count, example).
"""
import json
import collections
import re

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"
OUT = "<W>/audit/instruction_texts.json"

LEADS = [
    "Please follow these instructions in your response:",
    "Your response should comply with these constraints:",
    "Make sure to adhere to these requirements:",
    "Please ensure your answer follows these guidelines:",
    "Your response should satisfy these conditions:",
]

rows = []
with open(PATH, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))


def templatize(text, kw):
    t = text
    for k, v in sorted((kw or {}).items(), key=lambda kv: -len(str(kv[1]))):
        if v is None:
            continue
        if isinstance(v, list):
            for i, item in enumerate(v):
                t = t.replace(str(item), "{%s[%d]}" % (k, i), 1)
            continue
        s = str(v)
        if s and s in t:
            t = t.replace(s, "{%s}" % k, 1)
    return t


templates = collections.defaultdict(collections.Counter)
examples = {}
found = collections.Counter()
layouts = collections.Counter()
for r in rows:
    c = r["prompt"][0]["content"]
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    ids, kws = rec["instruction_id_list"], rec["kwargs"]
    items = None
    for lead in LEADS:
        idx = c.rfind(lead)
        if idx < 0:
            continue
        tail = c[idx + len(lead):]
        numbered = re.findall(r"\n(\d+)\. ([^\n]*)", tail)
        bullets = re.findall(r"\n- ([^\n]*)", tail)
        if len(numbered) >= len(ids) and len(ids) > 0:
            items = [t for _, t in numbered[: len(ids)]]
            layouts["numbered"] += 1
        elif len(bullets) >= len(ids):
            items = bullets[: len(ids)]
            layouts["bullets"] += 1
        break
    if items is None:
        layouts["other"] += 1
        continue
    for iid, kw, item in zip(ids, kws, items):
        t = templatize(item, kw)
        templates[iid][t] += 1
        found[iid] += 1
        examples.setdefault((iid, t), item)

print("layouts", dict(layouts))
out = {}
for iid in sorted(templates):
    lst = [(t, n, examples[(iid, t)]) for t, n in templates[iid].most_common()]
    out[iid] = lst
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
for iid in sorted(out):
    print("==", iid, "items", found[iid], "templates", len(out[iid]))
    for t, n, ex in out[iid][:4]:
        print(f"   {n:4d} {t[:300]!r}")
