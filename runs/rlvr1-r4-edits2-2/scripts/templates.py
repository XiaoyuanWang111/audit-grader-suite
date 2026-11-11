"""Find the instruction text of every constraint in its prompt, as a template.

For each constraint, substitute its kwargs values in candidate templates (learned from rows whose
instruction block parses into one line per constraint) and look for the text in the prompt.
Prints the distinct templates per instruction id with counts, and the constraints whose text was not found.
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")
OUT = os.path.join(ROOT, "audit", "scripts", "out")

rows = [json.loads(l) for l in open(DATA, encoding="utf-8")]


def to_template(line, kw):
    t = re.sub(r"^(\d+\.|-|\*|•)\s*", "", line.strip())
    # replace values longest first
    items = sorted(((k, v) for k, v in (kw or {}).items() if v is not None), key=lambda kv: -len(str(kv[1])))
    for k, v in items:
        if isinstance(v, list):
            s = str(v)
            if s in t:
                t = t.replace(s, "{" + k + "}")
                continue
            s = ", ".join(v)
            if s in t:
                t = t.replace(s, "{" + k + "}")
            continue
        s = str(v)
        if not s:
            continue
        # whole-word replacement for short numeric values
        if re.fullmatch(r"\d+", s):
            t2 = re.sub(r"(?<![\w-])" + re.escape(s) + r"(?![\w])", "{" + k + "}", t, count=1)
            t = t2
        else:
            t = t.replace(s, "{" + k + "}", 1)
    return t


templates = collections.defaultdict(collections.Counter)
for row in rows:
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    content = rec["prompt"]
    m = re.search(r"\n\n([^\n]*:)\n((?:(?:\d+\.|-|\*|•)[^\n]*(?:\n|$))+)\s*$", content)
    if not m:
        continue
    lines = [l for l in m.group(2).split("\n") if l.strip()]
    if len(lines) != len(rec["instruction_id_list"]):
        continue
    for iid, kw, line in zip(rec["instruction_id_list"], rec["kwargs"], lines):
        templates[iid][to_template(line, kw)] += 1

# Now search every constraint in every prompt
found = collections.Counter()
notfound = collections.defaultdict(list)
found_templates = collections.defaultdict(collections.Counter)


def render(t, kw):
    out = t
    for k, v in (kw or {}).items():
        if v is None:
            continue
        out = out.replace("{" + k + "}", str(v))
    return out


for row in rows:
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    content = rec["prompt"]
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        hit = None
        for t, _ in templates[iid].most_common():
            r = render(t, kw).strip()
            if r and r in content:
                hit = t
                break
            # also try the list-joined form
            if kw:
                r2 = t
                for k, v in kw.items():
                    if isinstance(v, list):
                        r2 = r2.replace("{" + k + "}", ", ".join(v))
                    elif v is not None:
                        r2 = r2.replace("{" + k + "}", str(v))
                if r2.strip() and r2.strip() in content:
                    hit = t + "  [list joined]"
                    break
        if hit:
            found[iid] += 1
            found_templates[iid][hit] += 1
        else:
            notfound[iid].append((row["extra_info"]["nemotron_ultra"]["uuid"], kw))

for iid in sorted(set(templates) | set(notfound) | set(found)):
    print(f"\n== {iid}: found {found[iid]}, not found {len(notfound[iid])}")
    for t, c in found_templates[iid].most_common(12):
        print(f"   [{c}] {t[:300]!r}")
    if len(found_templates[iid]) > 12:
        print(f"   ... {len(found_templates[iid]) - 12} more templates")
    for u, kw in notfound[iid][:3]:
        print("   NOT FOUND", u, json.dumps(kw, ensure_ascii=False)[:150])

json.dump({k: dict(v) for k, v in templates.items()}, open(os.path.join(OUT, "templates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({k: v for k, v in notfound.items()}, open(os.path.join(OUT, "notfound.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
