"""Scan the stored panel records: structure, prompt match, extraction rule, truncation, reasoning markers."""
import collections, glob, json, os, re
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
keys = list(df["key"]); prompts = list(df["prompt"])
rows = []
for path in sorted(glob.glob("case/panel/*/*.jsonl")):
    cfg = os.path.basename(os.path.dirname(path)); run = os.path.basename(path)[:-6]
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f]
    st = collections.Counter()
    st["n"] = len(lines)
    for i, r in enumerate(lines):
        if set(r) != {"key","prompt","response","raw_response","model","revision","run","finish_reason","num_tokens"}:
            st["bad_fields"] += 1
        if r["key"] != keys[i]: st["key_mismatch"] += 1
        if r["prompt"] != prompts[i]: st["prompt_mismatch"] += 1
        if r["run"] != run: st["run_mismatch"] += 1
        raw = r["raw_response"]
        exp = raw.rsplit("</think>", 1)[1].lstrip() if "</think>" in raw else raw
        if r["response"] != exp: st["extract_rule_mismatch"] += 1
        if r["finish_reason"] == "length": st["length"] += 1
        elif r["finish_reason"] != "stop": st["finish_" + str(r["finish_reason"])] += 1
        if "</think>" in raw: st["has_close_think"] += 1
        if "<think>" in raw: st["has_open_think"] += 1
        if "</think>" not in raw and "<think>" in raw: st["open_no_close"] += 1
        if "<think>" in r["response"] or "</think>" in r["response"]: st["think_tag_in_response"] += 1
        if r["response"].strip() == "": st["empty_response"] += 1
        if r["response"] != r["response"].rstrip(): st["trailing_ws"] += 1
    rows.append(dict(cfg=cfg, run=run, model=lines[0]["model"], revision=lines[0]["revision"][:10], **st))
out = pd.DataFrame(rows).fillna(0)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 30)
num = [c for c in out.columns if c not in ("cfg","run","model","revision")]
out[num] = out[num].astype(int)
out.to_csv("audit/work/panel_scan.csv", index=False)
print(out.groupby("cfg")[num].sum())
print("TOTAL", out[num].sum().to_dict())
