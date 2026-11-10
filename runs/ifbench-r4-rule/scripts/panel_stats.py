"""Stored-record counts for the panel (step 1 and step 5 start).

Per configuration: responses, finish_reason=length, raw with <think>, raw with </think>,
unclosed reasoning (<think> without </think>), empty response, response != extraction rule,
prompt/key mismatches against the dataset. Prints counts only, never response text.
"""
import collections
import glob
import json
import os

import pandas as pd

W = "<W>"
df = pd.read_parquet(f"{W}/case/data/train-00000-of-00001.parquet")
keys = list(df["key"])
prompts = list(df["prompt"])


def extract(raw):
    i = raw.rfind("</think>")
    if i < 0:
        return raw
    return raw[i + len("</think>"):].lstrip()


rows = []
fields_seen = collections.Counter()
for folder in sorted(glob.glob(f"{W}/case/panel/*/")):
    cfg = os.path.basename(folder.rstrip("/\\"))
    c = collections.Counter()
    runs = sorted(glob.glob(folder + "*.jsonl"))
    for path in runs:
        run = os.path.basename(path)[:-6]
        with open(path, encoding="utf-8") as f:
            lines = [json.loads(l) for l in f]
        c["runs"] += 1
        if len(lines) != 300:
            c["bad_len_files"] += 1
        for i, r in enumerate(lines):
            fields_seen[tuple(sorted(r))] += 1
            c["n"] += 1
            raw, resp = r["raw_response"], r["response"]
            if r["key"] != keys[i]:
                c["key_mismatch"] += 1
            if r["prompt"] != prompts[i]:
                c["prompt_mismatch"] += 1
            if r["run"] != run:
                c["run_field_mismatch"] += 1
            if r["finish_reason"] == "length":
                c["length"] += 1
            elif r["finish_reason"] != "stop":
                c["finish_" + str(r["finish_reason"])] += 1
            has_open = "<think>" in raw
            has_close = "</think>" in raw
            c["raw_has_open"] += has_open
            c["raw_has_close"] += has_close
            if has_open and not has_close:
                c["unclosed"] += 1
                if r["finish_reason"] == "length":
                    c["unclosed_and_length"] += 1
            if not has_open and has_close:
                c["close_without_open"] += 1
            if raw.count("</think>") > 1:
                c["multi_close"] += 1
            if resp.strip() == "":
                c["empty_response"] += 1
            if resp != extract(raw):
                c["response_ne_rule"] += 1
            if "<think>" in resp or "</think>" in resp:
                c["think_tag_in_response"] += 1
            if r["finish_reason"] == "length" and has_close:
                c["length_after_close"] += 1
    rows.append((cfg, dict(c)))

cols = ["runs", "n", "length", "raw_has_open", "raw_has_close", "unclosed", "unclosed_and_length",
        "length_after_close", "close_without_open", "multi_close", "empty_response", "response_ne_rule",
        "think_tag_in_response", "key_mismatch", "prompt_mismatch", "run_field_mismatch", "bad_len_files"]
print("| config | " + " | ".join(cols) + " | other |")
print("|---" * (len(cols) + 2) + "|")
tot = collections.Counter()
for cfg, c in rows:
    other = {k: v for k, v in c.items() if k not in cols}
    print(f"| {cfg} | " + " | ".join(str(c.get(k, 0)) for k in cols) + f" | {other or ''} |")
    tot.update(c)
print("| TOTAL | " + " | ".join(str(tot.get(k, 0)) for k in cols) + " | |")
print("field sets:", dict(fields_seen))
