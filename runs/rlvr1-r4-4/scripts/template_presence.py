"""Check that every row's prompt contains its instruction text (template with kwargs filled in).

Reports, per instruction id, how many constraints have their text in the prompt, and prints
short excerpts of misses. Also prints the text of count:counting_composition.
"""
import collections
import json
import os
import re

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl")
T = json.load(open(os.path.join(W, "audit", "work", "instruction_templates.json"), encoding="utf-8"))


def fill(t, kw):
    out = t
    for k, v in (kw or {}).items():
        if v is None:
            continue
        out = out.replace("{" + k + "}", str(v))
    return out


def stem(s):
    # compare without final period and case of the first letter
    s = s.strip().rstrip(".")
    return s[:1].lower() + s[1:]


hits = collections.Counter()
miss = collections.Counter()
miss_ex = collections.defaultdict(list)
with open(DATA, encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        c = rec["prompt"]
        lc = c[:1].lower() + c[1:]
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            temps = [t for t, k in T.get(iid, {}).items() if k >= 2] or list(T.get(iid, {}).keys())[:1]
            ok = False
            for t in temps:
                s = stem(fill(t, kw))
                # first sentence only for multi-line templates
                s1 = s.split("\n")[0]
                s1 = s1[:1].lower() + s1[1:]
                if s1 in c or s1 in lc or (s1[:1].upper() + s1[1:]) in c:
                    ok = True
                    break
            if ok:
                hits[iid] += 1
            else:
                miss[iid] += 1
                if len(miss_ex[iid]) < 3:
                    miss_ex[iid].append((json.dumps(kw, ensure_ascii=False), c[-300:]))
for iid in sorted(set(hits) | set(miss)):
    print(iid, "present", hits[iid], "missing", miss[iid])
for iid, exs in miss_ex.items():
    print("== MISSES", iid)
    for kw, tail in exs:
        print("  ", kw, repr(tail))
