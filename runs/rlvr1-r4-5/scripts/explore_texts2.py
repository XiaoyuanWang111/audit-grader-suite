"""Instruction text per id: templates from numbered-list prompts, then coverage over all prompts."""
import collections
import json
import re

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
OUT = "<W>/audit/out/instruction_templates.json"

rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]


def templ_of(t, kw):
    templ = t
    for k, v in sorted((kw or {}).items(), key=lambda kv: -len(json.dumps(kv[1]))):
        if v is None:
            continue
        if isinstance(v, list):
            templ = templ.replace(str(v), "{%s}" % k)
            for j, x in enumerate(v):
                templ = templ.replace(str(x), "{%s[%d]}" % (k, j))
        else:
            templ = templ.replace(str(v), "{%s}" % k)
    return templ


texts = collections.defaultdict(collections.Counter)
for row in rows:
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    prompt = row["prompt"][0]["content"]
    ids, kws = rec["instruction_id_list"], rec["kwargs"]
    n = len(ids)
    lines = prompt.split("\n")
    # numbered list of exactly n items at the end
    tail = lines[-n:]
    if n >= 2 and all(re.match(r"^%d\. " % (i + 1), t) for i, t in enumerate(tail)):
        for iid, kw, t in zip(ids, kws, tail):
            texts[iid][templ_of(t.split(". ", 1)[1], kw)] += 1

out = {}
for iid, c in sorted(texts.items()):
    out[iid] = c.most_common()
    print(f"\n== {iid}: {len(c)} templates")
    for t, k in c.most_common(8):
        print(f"   [{k}] {t[:500]}")
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
