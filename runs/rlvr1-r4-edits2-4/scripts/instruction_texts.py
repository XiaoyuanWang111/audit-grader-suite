"""Collect, per instruction id, the instruction texts the model sees in the prompts.

Reads only the data file (the task text). Writes:
  audit/work/instruction_texts.json : per id -> count, kwargs keys and values summary, templates with counts
  audit/work/row_hashes.tsv          : one sha256 per row over uuid, prompt, instruction ids, kwargs
Prints a summary.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

W = Path("<W>")
DATA = W / "case/data/rlvr1_instruction_following.jsonl"
OUT = W / "audit/work"
OUT.mkdir(parents=True, exist_ok=True)

HEADER_RE = re.compile(r"\n\n([^\n]*?):\n1\. ", re.S)

ids = Counter()
row_ids_count = Counter()
kw_keys = defaultdict(Counter)
kw_values = defaultdict(lambda: defaultdict(Counter))
templates = defaultdict(Counter)
headers = Counter()
unmatched_rows = 0
examples = {}
hash_lines = []
user_msgs = Counter()
roles = Counter()

def templatize(text, kwargs):
    t = text
    items = sorted(((k, v) for k, v in kwargs.items() if v is not None), key=lambda kv: -len(str(kv[1])))
    for k, v in items:
        if isinstance(v, list):
            for i, e in enumerate(v):
                s = str(e)
                if s:
                    t = t.replace(s, "{" + k + f"[{i}]" + "}")
            continue
        s = str(v)
        if s and s in t:
            t = t.replace(s, "{" + k + "}")
    return t

with open(DATA, encoding="utf-8") as f:
    for line_no, line in enumerate(f):
        row = json.loads(line)
        nu = row["extra_info"]["nemotron_ultra"]
        rec = json.loads(nu["record_json"])
        roles[tuple(m["role"] for m in row["prompt"])] += 1
        content = row["prompt"][0]["content"]
        h = hashlib.sha256(json.dumps({
            "uuid": nu["uuid"], "prompt": row["prompt"], "instruction_id_list": rec["instruction_id_list"],
            "kwargs": rec["kwargs"], "request_json": nu["request_json"],
        }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        hash_lines.append(f"{line_no}\t{nu['uuid']}\t{h}")
        if content != rec.get("prompt"):
            user_msgs["content != record.prompt"] += 1
        il = rec["instruction_id_list"]
        kws = rec["kwargs"]
        row_ids_count[len(il)] += 1
        for iid, kw in zip(il, kws):
            ids[iid] += 1
            for k, v in (kw or {}).items():
                kw_keys[iid][k] += 1
                if v is not None:
                    kw_values[iid][k][json.dumps(v, ensure_ascii=False)[:60]] += 1
        # Locate the numbered requirement list at the end.
        m = None
        for mm in HEADER_RE.finditer(content):
            m = mm
        if not m:
            unmatched_rows += 1
            if unmatched_rows <= 3:
                examples[f"unmatched_{unmatched_rows}"] = content[-400:]
            continue
        headers[m.group(1)] += 1
        tail = content[m.end() - 3:]
        parts = re.split(r"\n(?=\d+\. )", "\n" + tail.lstrip("\n"))
        parts = [p for p in parts if p.strip()]
        if len(parts) != len(il):
            unmatched_rows += 1
            continue
        for iid, kw, p in zip(il, kws, parts):
            p = re.sub(r"^\d+\. ", "", p.strip())
            templates[iid][templatize(p, kw or {})] += 1

summary = {}
for iid in sorted(ids):
    summary[iid] = {
        "count": ids[iid],
        "kwargs_keys": dict(kw_keys[iid]),
        "kwargs_values_top": {k: dict(c.most_common(12)) for k, c in kw_values[iid].items()},
        "n_distinct_values": {k: len(c) for k, c in kw_values[iid].items()},
        "templates": dict(templates[iid].most_common(15)),
        "n_templates": len(templates[iid]),
    }
(OUT / "instruction_texts.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "row_hashes.tsv").write_text("line\tuuid\tsha256\n" + "\n".join(hash_lines) + "\n", encoding="utf-8")
print("rows", len(hash_lines), "constraints", sum(ids.values()), "ids", len(ids))
print("constraints per row", dict(sorted(row_ids_count.items())))
print("roles", dict(roles))
print("headers", headers.most_common(10))
print("unmatched rows", unmatched_rows)
print("user msg vs record", dict(user_msgs))
for k, v in examples.items():
    print(k, repr(v[-300:]))
for iid in sorted(ids):
    print(f"{ids[iid]:6d} {iid}  templates={len(templates[iid])}")
