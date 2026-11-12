"""Mine the instruction texts the model sees, per instruction id, from the prompts.

Data only; reads no grader code. For each id, kwarg values in the prompt are
replaced by {key} placeholders, the prompt is cut into clauses, and clauses that
occur in many rows of this id and rarely elsewhere are printed with counts.
"""
import collections
import json
import re
import sys

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

rows = []
with open(DATA, encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        rows.append(rec)

SPLIT = re.compile(r"\n+|(?<=[.:])\s+(?=[A-Z])|,\s+(?:and\s+)?(?=[A-Z])|\s+and\s+(?=[A-Z])")


def clauses(text):
    return [c.strip(" -*0123456789.\t") for c in SPLIT.split(text) if c and c.strip()]


def placeholderize(prompt, ids, kwargs):
    text = prompt
    for iid, kw in zip(ids, kwargs):
        for k, v in sorted((kw or {}).items(), key=lambda kv: -len(str(kv[1]))):
            if v is None:
                continue
            if isinstance(v, list):
                text = text.replace(str(v), "{" + k + "}")
                for item in v:
                    text = re.sub(r"\b" + re.escape(str(item)) + r"\b", "{" + k + "_item}", text)
            else:
                sv = str(v)
                if len(sv) >= 1:
                    text = re.sub(r"(?<![\w{])" + re.escape(sv) + r"(?![\w}])", "{" + k + "}", text)
    return text


by_id = collections.defaultdict(collections.Counter)
global_counts = collections.Counter()
id_rows = collections.Counter()
for rec in rows:
    text = placeholderize(rec["prompt"], rec["instruction_id_list"], rec["kwargs"])
    cs = set(clauses(text))
    for c in cs:
        global_counts[c] += 1
    for iid in set(rec["instruction_id_list"]):
        id_rows[iid] += 1
        for c in cs:
            by_id[iid][c] += 1

want = sys.argv[1:] or sorted(id_rows)
for iid in want:
    n = id_rows[iid]
    print(f"##### {iid} rows={n}")
    shown = 0
    for c, k in by_id[iid].most_common(400):
        if k < max(3, 0.01 * n):
            break
        # specificity: share of the clause's occurrences that are in rows of this id
        spec = k / global_counts[c]
        if spec < 0.8:
            continue
        print(f"  {k:5d} {spec:4.2f} {c[:260]}")
        shown += 1
        if shown >= 14:
            break
