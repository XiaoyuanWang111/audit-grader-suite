"""Count what the stored panel records show: finish reasons, reasoning markers, empties.

Prints counts only, never response text.
"""
import collections
import glob
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(W, "case", "panel")
uuids = set()
with open(os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
    for line in f:
        uuids.add(json.loads(line)["extra_info"]["nemotron_ultra"]["uuid"])

for path in sorted(glob.glob(os.path.join(PANEL, "*", "*.jsonl"))):
    c = collections.Counter()
    keys = collections.Counter()
    seen = collections.Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for k in r:
                keys[k] += 1
            seen[r["uuid"]] += 1
            raw = r["raw_response"]
            c["n"] += 1
            c["finish_" + str(r["finish_reason"])] += 1
            c["has_open_think"] += "<think>" in raw
            c["has_close_think"] += "</think>" in raw
            c["n_close_think>1"] += raw.count("</think>") > 1
            if "</think>" in raw:
                after = raw.rsplit("</think>", 1)[1]
                c["empty_after_close"] += after.strip() == ""
            c["empty_raw"] += raw.strip() == ""
            c["uuid_not_in_data"] += r["uuid"] not in uuids
            c["leading_ws"] += raw[:1].isspace() if raw else 0
            c["trailing_ws"] += raw[-1:].isspace() if raw else 0
            c["len_finish_and_close"] += (r["finish_reason"] == "length") and ("</think>" in raw)
            c["len_finish_no_close"] += (r["finish_reason"] == "length") and ("</think>" not in raw)
    c["dup_uuid"] = sum(1 for v in seen.values() if v > 1)
    print(os.path.relpath(path, PANEL), dict(c))
    print("   keys", dict(keys))
