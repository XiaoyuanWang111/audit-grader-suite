"""Check AUDIT.md against the graders: every fixture id it names exists, and every
"`id` ... → X (Y)" claim in the grader-A and grader-B finding tables matches that grader's
verdict (X) and the fixture's contract label (Y). Prints mismatches; exit code 1 if any.
"""
import os
import random
import re
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "tests"))
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

FX = {f["id"]: f for f in FIXTURES}
text = open(os.path.join(AUDIT, "AUDIT.md"), encoding="utf-8").read()
bad = 0
ids = set(re.findall(r"`?([a-z_0-9]+:[0-9a-f]{16})`?", text))
for i in sorted(ids):
    if i not in FX:
        print("unknown fixture id", i)
        bad += 1
checked = 0
for line in text.splitlines():
    m = re.match(r"\| F-([AB])\d+ ", line)
    if not m:
        continue
    g = m.group(1)
    for fid, said, label in re.findall(r"`([a-z_0-9]+:[0-9a-f]{16})`[^→|]*?→ (pass|fail) \((pass|fail)\)", line):
        f = FX[fid]
        random.seed(0)
        v = (H.a_check if g == "A" else H.b_check)(f["instruction_id"], f["kwargs"], f["response"])[0]
        v = "pass" if v else "fail"
        checked += 1
        if v != said or f["label"] != label:
            print(f"mismatch {g} {fid}: report says {said} ({label}), grader {v}, label {f['label']}")
            bad += 1
print(f"{len(ids)} fixture ids named, {checked} verdict claims checked, {bad} problems")
sys.exit(1 if bad else 0)
