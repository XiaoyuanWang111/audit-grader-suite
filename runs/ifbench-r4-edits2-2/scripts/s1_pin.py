"""Step 1: pin inputs. Verify MANIFEST, hash dataset rows, summarize panel records.

Run from W:  .venv/Scripts/python.exe audit/scripts/s1_pin.py
Writes audit/frozen/dataset_row_hashes.tsv and audit/frozen/panel_summary.json.
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_manifest():
    bad, n = [], 0
    listed = set()
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, path = line.split("  ", 1)
            listed.add(path)
            n += 1
            if sha256_file(os.path.join(CASE, path)) != digest:
                bad.append(path)
    unlisted = []
    for root, _, files in os.walk(CASE):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), CASE).replace(os.sep, "/")
            if rel != "MANIFEST.sha256" and rel not in listed:
                unlisted.append(rel)
    return n, bad, sorted(unlisted)


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def row_hashes():
    import pyarrow.parquet as pq
    import pandas as pd

    rows = pq.read_table(os.path.join(CASE, "data", "train-00000-of-00001.parquet")).to_pylist()
    df = pd.DataFrame(rows)  # object columns; kwargs keep the parquet types (int64 stays int)
    out = []
    for r in rows:
        kw = [{k: v for k, v in d.items() if v is not None} for d in r["kwargs"]]
        row = {"key": r["key"], "prompt": r["prompt"],
               "instruction_id_list": list(r["instruction_id_list"]), "kwargs": kw}
        out.append((r["key"], hashlib.sha256(canon(row).encode("utf-8")).hexdigest(),
                    hashlib.sha256(r["prompt"].encode("utf-8")).hexdigest()))
    return df, out


def compare_reference_jsonl(df):
    p = os.path.join(CASE, "reference", "IFBench", "data", "IFBench_test.jsonl")
    ref = [json.loads(l) for l in open(p, encoding="utf-8")]
    diffs = []
    if len(ref) != len(df):
        diffs.append(f"row count {len(ref)} vs {len(df)}")
    for i, (r, (_, d)) in enumerate(zip(ref, df.iterrows())):
        if str(r.get("key")) != str(d["key"]):
            diffs.append(f"row {i}: key {r.get('key')} vs {d['key']}")
        if r.get("prompt") != d["prompt"]:
            diffs.append(f"row {i}: prompt differs")
        if list(r.get("instruction_id_list")) != list(d["instruction_id_list"]):
            diffs.append(f"row {i}: ids differ")
        kw_d = [{k: v for k, v in x.items() if v is not None} for x in d["kwargs"]]
        kw_r = [{k: v for k, v in x.items() if v is not None} for x in r.get("kwargs")]
        if canon(kw_d) != canon(kw_r):
            diffs.append(f"row {i}: kwargs differ")
    return len(ref), diffs


def panel_summary(df):
    keys = list(df["key"])
    prompts = list(df["prompt"])
    summ = {}
    panel = os.path.join(CASE, "panel")
    for folder in sorted(os.listdir(panel)):
        fp = os.path.join(panel, folder)
        if not os.path.isdir(fp):
            continue
        for fn in sorted(os.listdir(fp)):
            if not fn.endswith(".jsonl"):
                continue
            lines = [json.loads(l) for l in open(os.path.join(fp, fn), encoding="utf-8")]
            c = Counter()
            c["lines"] = len(lines)
            models, revs, runs = set(), set(), set()
            for i, rec in enumerate(lines):
                models.add(rec["model"]); revs.add(rec["revision"]); runs.add(rec["run"])
                if i >= len(keys) or str(rec["key"]) != str(keys[i]):
                    c["key_order_mismatch"] += 1
                if i < len(prompts) and rec["prompt"] != prompts[i]:
                    c["prompt_mismatch"] += 1
                raw, resp = rec["raw_response"], rec["response"]
                c["finish_" + str(rec["finish_reason"])] += 1
                has_close = "</think>" in raw
                has_open = "<think>" in raw
                if has_close:
                    c["has_close_think"] += 1
                if has_open and not has_close:
                    c["open_think_never_closed"] += 1
                if "<think>" in resp or "</think>" in resp:
                    c["think_tag_in_response"] += 1
                expected = raw.rsplit("</think>", 1)[1].lstrip() if has_close else raw
                if expected != resp:
                    c["response_extraction_mismatch"] += 1
                if not resp.strip():
                    c["empty_response"] += 1
            summ[f"{folder}/{fn[:-6]}"] = {"counts": dict(c), "model": sorted(models),
                                          "revision": sorted(revs), "run": sorted(runs)}
    return summ


def main():
    n, bad, unlisted = verify_manifest()
    print(f"manifest entries {n}; mismatches {len(bad)}: {bad[:10]}; unlisted files {len(unlisted)}: {unlisted[:20]}")
    df, rh = row_hashes()
    os.makedirs(os.path.join(W, "audit", "frozen"), exist_ok=True)
    with open(os.path.join(W, "audit", "frozen", "dataset_row_hashes.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("key\trow_sha256\tprompt_sha256\n")
        for k, h, ph in rh:
            f.write(f"{k}\t{h}\t{ph}\n")
    nref, diffs = compare_reference_jsonl(df)
    print(f"reference IFBench_test.jsonl rows {nref}; differences vs parquet: {len(diffs)} {diffs[:5]}")
    summ = panel_summary(df)
    with open(os.path.join(W, "audit", "frozen", "panel_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summ, f, indent=1, sort_keys=True)
    tot = Counter()
    for v in summ.values():
        tot.update(v["counts"])
    print("run files", len(summ), "totals", dict(tot))
    per_cfg = defaultdict(Counter)
    for k, v in summ.items():
        per_cfg[k.split("/")[0]].update(v["counts"])
    for cfg, c in per_cfg.items():
        print(cfg, {k: c[k] for k in sorted(c) if k != "lines"}, "lines", c["lines"])


if __name__ == "__main__":
    main()
