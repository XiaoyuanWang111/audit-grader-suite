"""Copy the grader and the reference into audit/work/ byte for byte, and verify them.

Importing either package creates a `.nltk_data` directory and `__pycache__` next to
its modules; running from a copy keeps case/ unchanged. `verify()` checks that every
copied file still matches case/MANIFEST.sha256 (call it before and after each run).

Usage: python audit/scripts/make_work_copy.py      (copy if missing, then verify)
"""
import hashlib
import os
import shutil
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")
WORK = os.path.join(W, "audit", "work")

# (source relative to case/, destination relative to audit/work/)
COPIES = [
    ("grader/IFBench/__init__.py", "grader/IFBench/__init__.py"),
    ("grader/IFBench/grader.py", "grader/IFBench/grader.py"),
    ("grader/IFBench/instructions.py", "grader/IFBench/instructions.py"),
    ("grader/IFBench/instructions_registry.py", "grader/IFBench/instructions_registry.py"),
    ("grader/IFBench/instructions_util.py", "grader/IFBench/instructions_util.py"),
    ("grader/IFBench/eval_instruct.py", "grader/IFBench/eval_instruct.py"),
    ("reference/IFBench/ifbench/__init__.py", "reference/ifbench/__init__.py"),
    ("reference/IFBench/ifbench/classic_instructions.py", "reference/ifbench/classic_instructions.py"),
    ("reference/IFBench/ifbench/instructions.py", "reference/ifbench/instructions.py"),
    ("reference/IFBench/ifbench/instructions_registry.py", "reference/ifbench/instructions_registry.py"),
    ("reference/IFBench/ifbench/instructions_util.py", "reference/ifbench/instructions_util.py"),
    ("reference/IFBench/ifbench/data/IFBench_test.jsonl", "reference/ifbench/data/IFBench_test.jsonl"),
    ("reference/IFBench/evaluation_lib.py", "reference/evaluation_lib.py"),
    ("reference/IFBench/run_eval.py", "reference/run_eval.py"),
    ("reference/IFBench/instructions_test.py", "reference/instructions_test.py"),
    ("reference/IFBench/data/IFBench_test.jsonl", "reference/data/IFBench_test.jsonl"),
]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def manifest():
    m = {}
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d, rel = line.rstrip("\n").split("  ", 1)
                m[rel] = d
    return m


def verify(quiet=False):
    m = manifest()
    bad = []
    for src, dst in COPIES:
        p = os.path.join(WORK, dst)
        if not os.path.exists(p) or sha(p) != m[src]:
            bad.append(dst)
    if not quiet:
        print("work copy:", "OK" if not bad else f"MISMATCH {bad}")
    return not bad


def main():
    for src, dst in COPIES:
        p = os.path.join(WORK, dst)
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(os.path.join(CASE, src), p)
    ok = verify()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
