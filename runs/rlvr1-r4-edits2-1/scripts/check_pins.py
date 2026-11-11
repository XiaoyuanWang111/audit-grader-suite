"""Check that every file the graders load matches its pinned copy (run before and after each panel run).

- installed verifiable_instructions and verifyit sources == the case copies (byte for byte);
- every case file listed in case/MANIFEST.sha256 matches its hash;
- the NLTK search path resolves punkt_tab to the pinned copy.
"""
import hashlib
import os
import sys

W = "<W>"
CASE = W + "/case"
SITE = W + "/.venv/Lib/site-packages"


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


problems = []
pairs = [(SITE + "/verifiable_instructions", CASE + "/reference/verifiable-instructions/verifiable_instructions"),
         (SITE + "/verifyit", CASE + "/grader/verifyit")]
n = 0
for installed, copy in pairs:
    for root, _, files in os.walk(copy):
        for name in files:
            if name.endswith(".pyc"):
                continue
            c = os.path.join(root, name)
            i = os.path.join(installed, os.path.relpath(c, copy))
            n += 1
            if not os.path.exists(i):
                problems.append(f"missing installed {i}")
            elif sha(i) != sha(c):
                problems.append(f"differs: {i}")
    for root, _, files in os.walk(installed):
        for name in files:
            if name.endswith(".pyc") or "__pycache__" in root:
                continue
            i = os.path.join(root, name)
            if not os.path.exists(os.path.join(copy, os.path.relpath(i, installed))):
                problems.append(f"extra installed file {i}")
m = 0
with open(CASE + "/MANIFEST.sha256", encoding="utf-8") as f:
    for line in f:
        h, p = line.rstrip("\n").split("  ", 1)
        m += 1
        if sha(os.path.join(CASE, p)) != h:
            problems.append(f"manifest mismatch {p}")
os.environ["NLTK_DATA"] = CASE + "/deps/nltk_data"
import nltk  # noqa: E402

found = str(nltk.data.find("tokenizers/punkt_tab/english"))
if os.path.normcase(os.path.abspath(found)).find(os.path.normcase(os.path.abspath(CASE + "/deps/nltk_data"))) != 0:
    problems.append(f"punkt_tab resolved outside the pinned copy: {found}")
pyc = [os.path.join(r, d) for r, ds, _ in os.walk(CASE + "/reference") for d in ds if d == "__pycache__"]
if pyc:
    problems.append(f"__pycache__ written under case/reference: {pyc}")
print(f"compared {n} installed files, {m} manifest entries; punkt_tab at {found}")
print("OK" if not problems else "PROBLEMS:\n" + "\n".join(problems))
sys.exit(1 if problems else 0)
