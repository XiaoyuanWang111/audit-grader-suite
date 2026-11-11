"""Run every fixture against the grader (strict), the reference (strict) and, if present,
the replacement; print the fixtures each one gets wrong and write
audit/work/fixture_results.json."""
import json
import os
import sys
import traceback

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
import graders as G  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

HAVE_REP = os.path.exists(os.path.join(W, "audit", "replacement", "ifb_replacement.py"))


def verdict(fn, f):
    try:
        return "pass" if fn(f["check"], f["kwargs"], f["response"]) else "fail"
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__ + ":" + str(e)[:80]


res = []
for f in FIXTURES:
    row = {"id": f["id"], "check": f["check"], "label": f["label"], "tags": f["tags"], "note": f["note"],
           "grader": verdict(G.grade_grader, f), "reference": verdict(G.grade_reference, f)}
    if HAVE_REP:
        row["replacement"] = verdict(G.grade_replacement, f)
    res.append(row)

json.dump(res, open(os.path.join(W, "audit", "work", "fixture_results.json"), "w", encoding="utf-8"), indent=1)
for who in ["grader", "reference"] + (["replacement"] if HAVE_REP else []):
    wrong = [r for r in res if r[who] != r["label"]]
    print(f"== {who}: {len(wrong)} of {len(res)} fixtures wrong")
    if "-q" in sys.argv:
        continue
    for r in wrong:
        f = next(x for x in FIXTURES if x["id"] == r["id"])
        print(f"  {r['id']:52s} label={r['label']} got={r[who]} tags={r['tags']} note={r['note']}")
        print(f"      response={f['response'][:110]!r}")
