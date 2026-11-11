"""Print development-set disagreements for one check, with short excerpts of the graded answer.

python review.py <check> <grader nvidia|verifyit> <grader verdict True|False> [n] [seed] [split dev|held]
Prints the graded answer only (never reasoning text): the replacement's graded text, at most 400 characters
around its start and end. Responses whose reasoning never closes are skipped.
"""
import glob
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)
sys.path.insert(0, AUDIT)
import replacement as R  # noqa: E402

HELD_OUT = {"Qwen__Qwen2.5-7B-Instruct/sample0", "allenai__OLMo-2-1124-7B-Instruct/sample0"}
check, grader, gv = sys.argv[1], sys.argv[2], sys.argv[3] == "True"
n = int(sys.argv[4]) if len(sys.argv) > 4 else 5
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
split = sys.argv[6] if len(sys.argv) > 6 else "dev"

hits = []
for path in sorted(glob.glob(os.path.join(AUDIT, "out", "panel", "*.jsonl"))):
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if (r["run"] in HELD_OUT) != (split == "held") or r["repl_extraction_failure"]:
            continue
        for i, iid in enumerate(r["ids"]):
            if iid == check and r[grader][i] is not None and r[grader][i] == gv and r["replacement"][i] != gv:
                hits.append((r["run"], r["uuid"], i, r["kwargs"][i], r["repl_flips"].get(str(i), {})))
print(len(hits), "disagreements")
random.Random(seed).shuffle(hits)
raw = {}
for run, uuid, i, kw, flips in hits[:n]:
    folder, name = run.split("/")
    if run not in raw:
        raw[run] = {}
        for line in open(os.path.join(W, "case", "panel", folder, name + ".jsonl"), encoding="utf-8"):
            x = json.loads(line)
            raw[run][x["uuid"]] = x["raw_response"]
    text = R.graded_text(raw[run][uuid], folder.endswith("__thinking"))
    excerpt = text if len(text) <= 400 else text[:250] + " [...] " + text[-150:]
    print("-" * 80)
    print(run, uuid, kw, "flips:", flips)
    print(repr(excerpt))
