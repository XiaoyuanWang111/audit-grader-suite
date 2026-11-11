"""Run every fixture through grader (strict, loose), reference (strict, loose) and the replacement.

Writes audit/work/fixture_results.tsv and prints the fixtures where a grader's strict verdict
differs from the contract label.
"""
import json
import os
import sys

sys.path.insert(0, "<W>/audit/scripts")
sys.path.insert(0, "<W>/audit/tests")
import graders  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

OUT = "<W>/audit/work/fixture_results.tsv"
use_rep = os.path.exists("<W>/audit/scripts/replacement.py")
rows = []
for f in FIXTURES:
    prompt = "fixture prompt"
    r = {name: fn(f["check"], f["kwargs"], prompt, f["response"]) for name, fn in graders.GRADERS.items()}
    if use_rep:
        r["replacement"] = graders.replacement(f["check"], f["kwargs"], prompt, f["response"])
    rows.append((f, r))


def v(x):
    return "pass" if x is True else "fail" if x is False else str(x)


with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    cols = ["grader_strict", "grader_loose", "reference_strict", "reference_loose"] + (["replacement"] if use_rep else [])
    fh.write("\t".join(["id", "label", "kind", "decisions"] + cols) + "\n")
    for f, r in rows:
        fh.write("\t".join([f["id"], f["label"], f["kind"], ",".join(f["decisions"])] + [v(r[c]) for c in cols]) + "\n")

for name in ["grader_strict", "reference_strict"] + (["replacement"] if use_rep else []):
    wrong = [(f, r) for f, r in rows if v(r[name]) != f["label"]]
    print(f"\n=== {name}: {len(wrong)} of {len(rows)} fixtures differ from the label")
    for f, r in wrong:
        tag = "DECISION " + ",".join(f["decisions"]) if f["decisions"] else "NO-DECISION"
        print(f"  {f['id']}  label={f['label']} got={v(r[name])}  [{tag}] {f['note']}")
