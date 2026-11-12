"""Extract the instruction text that the model sees for each instruction id.

For rows whose requirements are a list ("1. ..." or "- ..." lines after a header ending in ':'),
line k is the text of instruction k. Kwarg values are replaced by {name} placeholders so the
templates can be counted. Then every row (list or inline) is checked for the presence of one of
its id's templates, with kwargs filled in.
Writes audit/work/instruction_templates.json.
"""
import collections
import json
import os
import re

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl")

templates = collections.defaultdict(collections.Counter)
rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        rows.append(rec)

list_re = re.compile(r"(?m)^[^\n]*:\n((?:(?:\d+\.|-) [^\n]*(?:\n(?!\d+\. |- |\n)[^\n]*)*\n?){1,})")


def placeholderize(text, kw):
    t = text
    for k, v in sorted((kw or {}).items(), key=lambda kv: -len(str(kv[1])) if kv[1] is not None else 0):
        if v is None:
            continue
        if isinstance(v, list):
            sv = str(v)
            t = t.replace(sv, "{" + k + "}")
            t = t.replace(", ".join(v), "{" + k + "}")
        else:
            sv = str(v)
            # whole-token replacement for numbers and words
            t = re.sub(r"(?<![A-Za-z0-9])" + re.escape(sv) + r"(?![A-Za-z0-9])", "{" + k + "}", t)
    return t


for rec in rows:
    c = rec["prompt"]
    ids = rec["instruction_id_list"]
    kws = rec["kwargs"]
    n = len(ids)
    # find a block of n list items
    lines = c.split("\n")
    for start in range(len(lines)):
        m = re.match(r"^(1\.|-) ", lines[start])
        if not m:
            continue
        if start == 0 or not lines[start - 1].rstrip().endswith(":"):
            continue
        marker = m.group(1)
        items = []
        cur = None
        j = start
        while j < len(lines):
            ln = lines[j]
            mm = re.match(r"^(\d+\.|-) (.*)$", ln)
            if mm and ((marker == "-" and mm.group(1) == "-") or (marker != "-" and mm.group(1) == f"{len(items) + 1}.")):
                if cur is not None:
                    items.append(cur)
                cur = mm.group(2)
            elif ln.strip() == "":
                break
            else:
                if cur is None:
                    break
                cur += "\n" + ln
            j += 1
        if cur is not None:
            items.append(cur)
        if len(items) == n:
            for iid, kw, text in zip(ids, kws, items):
                templates[iid][placeholderize(text, kw)] += 1
            break

out = {iid: dict(c.most_common()) for iid, c in sorted(templates.items())}
with open(os.path.join(W, "audit", "work", "instruction_templates.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
for iid, c in sorted(templates.items()):
    print("##", iid, sum(c.values()), "templates:", len(c))
    for t, k in c.most_common(4):
        print("   ", k, repr(t[:400]))
