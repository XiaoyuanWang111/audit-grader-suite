"""Collect the instruction text that the model sees for each instruction id (from prompts only)."""
import collections
import json
import re

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
OUT = "<W>/audit/out/instruction_texts.json"

rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]

layouts = collections.Counter()
texts = collections.defaultdict(collections.Counter)
unsplit = []
for row in rows:
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    prompt = row["prompt"][0]["content"]
    ids = rec["instruction_id_list"]
    kws = rec["kwargs"]
    n = len(ids)
    # find the trailing numbered list "1. ...\n2. ..."
    parts = prompt.rsplit("\n\n", 1)
    tail = parts[-1]
    lines = tail.split("\n")
    header = lines[0]
    items = lines[1:]
    if n == 1 and not re.match(r"^1\. ", items[0] if items else ""):
        layouts[("single", header[:60])] += 1
        texts_for = [tail]
    else:
        layouts[("list", header[:60])] += 1
        texts_for = []
        ok = len(items) == n and all(it.startswith(f"{i+1}. ") for i, it in enumerate(items))
        if not ok:
            unsplit.append(rec["uuid"])
            continue
        texts_for = [it.split(". ", 1)[1] for it in items]
    for iid, kw, t in zip(ids, kws, texts_for):
        templ = t
        for k, v in sorted((kw or {}).items(), key=lambda kv: -len(json.dumps(kv[1]))):
            if v is None:
                continue
            if isinstance(v, list):
                for j, x in enumerate(v):
                    templ = templ.replace(str(x), "{%s[%d]}" % (k, j))
            else:
                templ = templ.replace(str(v), "{%s}" % k)
        texts[iid][templ] += 1

print("layouts (top 40):")
for k, c in layouts.most_common(40):
    print(c, k)
print("layout kinds", len(layouts))
print("unsplit rows", len(unsplit), unsplit[:5])
out = {iid: c.most_common() for iid, c in sorted(texts.items())}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for iid, c in sorted(texts.items()):
    print(f"\n== {iid}: {len(c)} distinct templates")
    for t, k in c.most_common(6):
        print(f"   [{k}] {t[:400]}")
