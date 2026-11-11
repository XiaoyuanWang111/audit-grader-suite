"""Extract each instruction id's text as the model sees it, from numbered/bulleted lists in prompts.

Data only; no grader code is read. Items are matched to ids by list order, then the kwargs
values are replaced by placeholders to get templates.
"""
import json
import re
import sys
from collections import Counter, defaultdict

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]

templates = defaultdict(Counter)
examples = {}
matched_rows = 0
for r in rows:
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    p = rec["prompt"]
    ids = rec["instruction_id_list"]
    kws = rec["kwargs"]
    n = len(ids)
    items = None
    for style in ("num", "dash"):
        if style == "num":
            pat = r"\n1\. "
        else:
            pat = r"\n- "
        m = re.search(r":" + pat, p)
        if not m:
            continue
        start = m.start() + 1
        lines = p[start:].split("\n")[1:]
        # collect items: lines starting with k. or -, continuation lines attached
        its = []
        for ln in lines:
            if style == "num" and re.match(r"^%d\. " % (len(its) + 1), ln) and len(its) < n:
                its.append(ln[len("%d. " % (len(its) + 1)):])
            elif style == "dash" and ln.startswith("- ") and len(its) < n:
                its.append(ln[2:])
            elif its and len(its) <= n and ln.strip() and not re.match(r"^(\d+\. |- )", ln) and len(its) < n + 1:
                # continuation (e.g. SECTION examples) only while inside the list
                if len(its) == n and ln.strip() == "":
                    break
                its[-1] += "\n" + ln
            else:
                if len(its) == n:
                    break
        if len(its) == n:
            items = its
            break
    if items is None:
        continue
    matched_rows += 1
    for iid, args, text in zip(ids, kws, items):
        t = text
        for k, v in sorted((args or {}).items(), key=lambda kv: -len(str(kv[1]))):
            if v is None:
                continue
            if isinstance(v, list):
                sv = str(v)
            else:
                sv = str(v)
            if sv and sv in t:
                t = t.replace(sv, "{" + k + "}")
        templates[iid][t] += 1
        examples.setdefault((iid, t), (rec["uuid"], text, args))

print("rows with list parsed", matched_rows)
for iid in sorted(templates):
    print("=" * 20, iid)
    for t, c in templates[iid].most_common(8):
        print(f"  [{c}] {t!r}"[:700])
