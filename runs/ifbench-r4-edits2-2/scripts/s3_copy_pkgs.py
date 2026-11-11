"""Copy the grader and the reference verbatim into audit/work/pkgs and verify each copy
against case/MANIFEST.sha256, so that importing them never writes into case/.

Layout:
  audit/work/pkgs/grader/IFBench/*.py            <- case/grader/IFBench/*.py
  audit/work/pkgs/reference/ifbench/...          <- case/reference/IFBench/ifbench/ (py + data/)
  audit/work/pkgs/reference/evaluation_lib.py    <- case/reference/IFBench/evaluation_lib.py
  audit/work/pkgs/reference/instructions_test.py <- case/reference/IFBench/instructions_test.py
"""
import hashlib
import os
import shutil
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")
DST = os.path.join(W, "audit", "work", "pkgs")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


manifest = {}
for line in open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8"):
    d, p = line.rstrip("\n").split("  ", 1)
    manifest[p] = d

pairs = []
for fn in sorted(os.listdir(os.path.join(CASE, "grader", "IFBench"))):
    if fn.endswith(".py"):
        pairs.append((f"grader/IFBench/{fn}", os.path.join(DST, "grader", "IFBench", fn)))
for root, _, files in os.walk(os.path.join(CASE, "reference", "IFBench", "ifbench")):
    for fn in files:
        if fn.endswith(".pyc"):
            continue
        rel = os.path.relpath(os.path.join(root, fn), CASE).replace(os.sep, "/")
        sub = os.path.relpath(os.path.join(root, fn), os.path.join(CASE, "reference", "IFBench"))
        pairs.append((rel, os.path.join(DST, "reference", sub)))
for fn in ["evaluation_lib.py", "instructions_test.py"]:
    pairs.append((f"reference/IFBench/{fn}", os.path.join(DST, "reference", fn)))

bad = 0
for rel, dst in pairs:
    src = os.path.join(CASE, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    if rel not in manifest or sha(dst) != manifest[rel]:
        print("MISMATCH", rel)
        bad += 1
print(f"copied {len(pairs)} files, {bad} mismatches against MANIFEST")
sys.exit(1 if bad else 0)
