"""Count what the stored panel records show: rows, finish reasons, reasoning markers, empty responses."""
import collections
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")
uuids = set()
for line in open(DATA, encoding="utf-8"):
    uuids.add(json.loads(line)["extra_info"]["nemotron_ultra"]["uuid"])

for path in sorted(glob.glob(os.path.join(ROOT, "case", "panel", "*", "*.jsonl"))):
    name = os.path.relpath(path, os.path.join(ROOT, "case", "panel")).replace(os.sep, "/")
    c = collections.Counter()
    fields = collections.Counter()
    seen = set()
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        for k in r:
            fields[k] += 1
        c["n"] += 1
        c["finish_" + r["finish_reason"]] += 1
        if r["uuid"] not in uuids:
            c["uuid_not_in_data"] += 1
        if r["uuid"] in seen:
            c["dup_uuid"] += 1
        seen.add(r["uuid"])
        t = r["raw_response"]
        if not t.strip():
            c["empty"] += 1
        o, cl = t.count("<think>"), t.count("</think>")
        if o:
            c["has_<think>"] += 1
        if cl:
            c["has_</think>"] += 1
        if cl > 1:
            c["multiple_</think>"] += 1
        if o and not cl:
            c["<think>_unclosed"] += 1
        if cl and not t.split("</think>")[-1].strip():
            c["empty_after_last_</think>"] += 1
        if r["finish_reason"] == "length" and not cl:
            c["length_and_no_</think>"] += 1
        if r["num_tokens"] >= r["max_tokens"]:
            c["num_tokens>=max_tokens"] += 1
    print(name, dict(c))
    print("   fields", dict(fields))
