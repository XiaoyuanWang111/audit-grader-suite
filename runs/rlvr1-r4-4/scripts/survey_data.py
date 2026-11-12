"""Survey the 11,817 rows: instruction ids, kwargs, prompt layouts, per-row hashes.

Writes audit/frozen/row_hashes.tsv and audit/work/survey.json. Reads only case/data.
"""
import collections
import hashlib
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl")
OUT = os.path.join(W, "audit", "work")
os.makedirs(OUT, exist_ok=True)

ids = collections.Counter()
kw_keys = collections.defaultdict(collections.Counter)
kw_vals = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
layouts = collections.Counter()
n_constraints = collections.Counter()
mismatch_prompt = 0
record_keys = collections.Counter()
other = collections.Counter()
hash_lines = []
grading_modes = collections.Counter()
examples = collections.defaultdict(list)
n_rows = 0
with open(DATA, encoding="utf-8") as f:
    for line in f:
        n_rows += 1
        row = json.loads(line)
        nu = row["extra_info"]["nemotron_ultra"]
        rec = json.loads(nu["record_json"])
        for k in rec:
            record_keys[k] += 1
        grading_modes[rec.get("grading_mode")] += 1
        msgs = row["prompt"]
        other[("n_msgs", len(msgs))] += 1
        other[("roles", tuple(m["role"] for m in msgs))] += 1
        other[("request_json", nu["request_json"])] += 1
        content = msgs[-1]["content"]
        if content != rec.get("prompt"):
            mismatch_prompt += 1
        ilist = rec["instruction_id_list"]
        kws = rec["kwargs"]
        n_constraints[len(ilist)] += 1
        for iid, kw in zip(ilist, kws):
            ids[iid] += 1
            for k, v in (kw or {}).items():
                kw_keys[iid][k] += 1
                kw_vals[iid][k][json.dumps(v, ensure_ascii=False)[:80]] += 1
        # layout of the requirement block
        m = re.search(r"\n\n([^\n]*?):\n1\. ", content)
        layouts[m.group(1)[:80] if m else "<none>"] += 1
        # row hash over uuid, prompt messages, instruction ids, kwargs
        h = hashlib.sha256(json.dumps({"uuid": nu["uuid"], "prompt": msgs, "instruction_id_list": ilist,
                                       "kwargs": kws}, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        hash_lines.append(f"{n_rows - 1}\t{nu['uuid']}\t{h}")
        for i, iid in enumerate(ilist):
            if len(examples[iid]) < 6:
                examples[iid].append({"uuid": nu["uuid"], "pos": i, "n": len(ilist), "kwargs": kws[i],
                                      "tail": content[-900:]})

with open(os.path.join(W, "audit", "frozen", "row_hashes.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("row_index\tuuid\tsha256(uuid,prompt,instruction_id_list,kwargs)\n")
    f.write("\n".join(hash_lines) + "\n")

survey = {
    "n_rows": n_rows,
    "n_constraints": sum(ids.values()),
    "ids": dict(ids.most_common()),
    "kw_keys": {k: dict(v) for k, v in kw_keys.items()},
    "kw_vals": {k: {kk: dict(vv.most_common(15)) for kk, vv in v.items()} for k, v in kw_vals.items()},
    "layouts": dict(layouts.most_common(30)),
    "n_constraints_per_row": dict(n_constraints),
    "mismatch_prompt": mismatch_prompt,
    "record_keys": dict(record_keys),
    "grading_modes": {str(k): v for k, v in grading_modes.items()},
    "other": {str(k): v for k, v in other.items()},
}
with open(os.path.join(OUT, "survey.json"), "w", encoding="utf-8") as f:
    json.dump(survey, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "examples.json"), "w", encoding="utf-8") as f:
    json.dump(examples, f, ensure_ascii=False, indent=1)
print(json.dumps({k: survey[k] for k in ["n_rows", "n_constraints", "ids", "layouts", "n_constraints_per_row",
                                          "mismatch_prompt", "record_keys", "grading_modes", "other"]},
                 ensure_ascii=False, indent=1))
