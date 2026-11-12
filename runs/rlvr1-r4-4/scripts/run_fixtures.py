"""Grade every hand-written fixture with grader A (NVIDIA via SkyRL), grader B (verifyit) and R.

Prints each fixture whose verdict differs from its label, and writes audit/work/fixture_verdicts.json.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "tests"))
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

out = []
for fx in FIXTURES:
    iid, kw, resp, label = fx["instruction_id"], fx["kwargs"], fx["response"], fx["label"]
    random.seed(0)  # F-G2
    a, a_err = H.a_check(iid, kw, resp)
    b, b_err = H.b_check(iid, kw, resp)
    r = H.r_check(iid, kw, resp)
    rec = {**fx, "A": "pass" if a else "fail", "A_error": a_err, "B": "pass" if b else "fail", "B_error": b_err,
           "R": "pass" if r else "fail"}
    out.append(rec)
os.makedirs(os.path.join(AUDIT, "work"), exist_ok=True)
with open(os.path.join(AUDIT, "work", "fixture_verdicts.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
n = len(out)
for g in ("A", "B", "R"):
    wrong = [o for o in out if o[g] != o["label"] and not (g == "B" and o["instruction_id"] in H.SEMANTIC)]
    print(f"== {g}: {len(wrong)} of {n} fixtures differ from the label")
    for o in wrong:
        err = o.get(g + "_error") if g != "R" else None
        print(f"   {o['id']:<45} label={o['label']} {g}={o[g]} dec={o['decisions']} {('ERR ' + err) if err else ''}")
        print(f"        {json.dumps(o['kwargs'], ensure_ascii=False)[:80]} | {json.dumps(o['response'], ensure_ascii=False)[:110]}")
