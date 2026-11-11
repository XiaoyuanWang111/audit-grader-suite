"""Step 1: pin inputs that the run records, configuration and lockfiles show.

Writes audit/frozen/dataset_row_hashes.tsv and audit/work/pins.json, prints a summary.
Reads no grader or reference code.
"""
import hashlib
import importlib.metadata as md
import json
import pathlib
import sys

import pandas as pd

W = pathlib.Path(__file__).resolve().parents[2]
C = W / "case"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def conv(v):
    try:
        return v.tolist()
    except AttributeError:
        return v


pins = {}
pins["python"] = sys.version
import pyarrow.parquet as pq
rows = []
for r in pq.read_table(C / "data/train-00000-of-00001.parquet").to_pylist():
    obj = {
        "key": r["key"],
        "prompt": r["prompt"],
        "instruction_id_list": list(r["instruction_id_list"]),
        "kwargs": [dict(kw) for kw in r["kwargs"]],
    }
    canon = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    rows.append((r["key"], hashlib.sha256(canon.encode("utf-8")).hexdigest()))
out = W / "audit/frozen/dataset_row_hashes.tsv"
out.write_text("key\tsha256_canonical_json\n" + "".join(f"{k}\t{h}\n" for k, h in rows), encoding="utf-8", newline="\n")
pins["dataset_parquet_sha256"] = sha(C / "data/train-00000-of-00001.parquet")
pins["dataset_row_hashes_file_sha256"] = sha(out)
pins["dataset_rows"] = len(rows)

# Installed packages vs lockfile
lock = {}
for line in (C / "deps/requirements.lock.txt").read_text().splitlines():
    if "==" in line:
        n, v = line.strip().split("==")
        lock[n.lower().replace("_", "-")] = v
installed = {d.metadata["Name"].lower().replace("_", "-"): d.version for d in md.distributions()}
mism = {n: (v, installed.get(n)) for n, v in lock.items() if installed.get(n) != v}
extra = sorted(set(installed) - set(lock))
pins["lock_mismatches"] = mism
pins["installed_not_in_lock"] = extra

# NLTK data tree hash
nl = C / "deps/nltk_data"
files = sorted(p for p in nl.rglob("*") if p.is_file())
h = hashlib.sha256()
for p in files:
    h.update(str(p.relative_to(nl)).replace("\\", "/").encode() + b"\0" + sha(p).encode() + b"\n")
pins["nltk_data_files"] = len(files)
pins["nltk_data_tree_sha256"] = h.hexdigest()
pins["nltk_data_top"] = sorted({str(p.relative_to(nl)).replace("\\", "/").split("/")[0] + "/" + str(p.relative_to(nl)).replace("\\", "/").split("/")[1] for p in files if len(p.relative_to(nl).parts) > 1})
pins["manifest_sha256"] = sha(C / "MANIFEST.sha256")
(W / "audit/work/pins.json").write_text(json.dumps(pins, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(pins, indent=1))
