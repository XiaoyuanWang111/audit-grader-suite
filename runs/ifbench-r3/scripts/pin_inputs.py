"""Step 1 pins: verify case/MANIFEST.sha256, hash dataset rows, check installed packages against the lock file.

Run from W:  .venv/Scripts/python.exe audit/scripts/pin_inputs.py [--write]
Exit code 1 if any pinned file or package differs.
"""
import hashlib, json, os, sys, importlib.metadata as md
import pandas as pd

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")
write = "--write" in sys.argv
bad = 0

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

# 1. manifest
listed = {}
with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
    for line in f:
        d, p = line.rstrip("\n").split("  ", 1)
        listed[p] = d
mism = [p for p, d in listed.items() if not os.path.exists(os.path.join(CASE, p)) or sha(os.path.join(CASE, p)) != d]
present = set()
for root, _, files in os.walk(CASE):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), CASE).replace(os.sep, "/")
        present.add(rel)
unlisted = sorted(present - set(listed) - {"MANIFEST.sha256"})
print(f"manifest entries {len(listed)}; mismatched or missing {len(mism)}; files present but unlisted {len(unlisted)}")
for p in mism[:20]: print("  MISMATCH", p)
for p in unlisted[:20]: print("  UNLISTED", p)
bad += len(mism) + len(unlisted)
print("MANIFEST.sha256 itself:", sha(os.path.join(CASE, "MANIFEST.sha256")))

# 2. dataset rows
import pyarrow.parquet as pq
df = pq.read_table(os.path.join(CASE, "data/train-00000-of-00001.parquet")).to_pylist()  # native types, as datasets gives them
lines = []
for r in df:
    obj = {"key": r["key"], "prompt": r["prompt"], "instruction_id_list": list(r["instruction_id_list"]),
           "kwargs": [{k: v for k, v in kw.items() if v is not None} for kw in r["kwargs"]]}
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    lines.append(f"{r['key']}\t{hashlib.sha256(s.encode('utf-8')).hexdigest()}")
blob = ("\n".join(lines) + "\n").encode("utf-8")
print("dataset rows", len(df), "row-hash list sha256", hashlib.sha256(blob).hexdigest())
if write:
    with open(os.path.join(W, "audit/frozen/dataset_row_hashes.tsv"), "wb") as f:
        f.write(blob)

# 3. installed packages vs lock
lock = {}
with open(os.path.join(CASE, "deps/requirements.lock.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            n, v = line.split("==")
            lock[n.lower().replace("_", "-")] = v
inst = {d.metadata["Name"].lower().replace("_", "-"): d.version for d in md.distributions()}
diff = {n: (v, inst.get(n)) for n, v in lock.items() if inst.get(n) != v}
extra = sorted(set(inst) - set(lock) - {"pip", "setuptools", "wheel"})
print(f"lock entries {len(lock)}; version mismatches {diff}; installed but not locked {extra}")
bad += len(diff)
print("python", sys.version.split()[0])
sys.exit(1 if bad else 0)
