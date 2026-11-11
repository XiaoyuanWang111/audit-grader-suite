"""Copy the grader and the reference into audit/run/ byte for byte and check them against case/MANIFEST.sha256.

Both packages create a `.nltk_data` directory next to instructions.py on import, and
instructions_util downloads NLTK data when a resource is missing. Running them from
copies keeps case/ unmodified; graders.py blocks nltk.download so nothing reaches the network.
"""
import hashlib
import os
import shutil

W = "<W>"
CASE = W + "/case"
RUN = W + "/audit/run"

manifest = {}
for line in open(CASE + "/MANIFEST.sha256", encoding="utf-8"):
    h, p = line.rstrip("\n").split("  ", 1)
    manifest[p] = h

COPIES = {
    "grader/IFBench/__init__.py": "grader/IFBench/__init__.py",
    "grader/IFBench/instructions.py": "grader/IFBench/instructions.py",
    "grader/IFBench/instructions_registry.py": "grader/IFBench/instructions_registry.py",
    "grader/IFBench/instructions_util.py": "grader/IFBench/instructions_util.py",
    "grader/IFBench/grader.py": "grader/IFBench/grader.py",
    "reference/IFBench/ifbench/__init__.py": "reference/ifbench/__init__.py",
    "reference/IFBench/ifbench/instructions.py": "reference/ifbench/instructions.py",
    "reference/IFBench/ifbench/classic_instructions.py": "reference/ifbench/classic_instructions.py",
    "reference/IFBench/ifbench/instructions_registry.py": "reference/ifbench/instructions_registry.py",
    "reference/IFBench/ifbench/instructions_util.py": "reference/ifbench/instructions_util.py",
    "reference/IFBench/evaluation_lib.py": "reference/evaluation_lib.py",
    "reference/IFBench/instructions_test.py": "reference/instructions_test.py",
}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


for src, dst in COPIES.items():
    s = CASE + "/" + src
    d = RUN + "/" + dst
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copyfile(s, d)
    assert sha(s) == manifest[src], src
    assert sha(d) == manifest[src], dst
    print("ok", manifest[src][:12], dst)
