"""Run every fixture against the grader (and, when importable, the reference and
the replacement grader). Prints disagreements with the contract label and
writes audit/work/fixture_results.json.

Usage: python audit/scripts/run_fixtures.py [grader|reference|replacement ...]
"""
import json
import sys
import traceback

import common  # noqa: F401  (sets paths)
from tests.fixtures_data import FIX

GRADERS = sys.argv[1:] or ["grader"]


def get_fn(name):
    if name == "grader":
        return common.grade_grader
    if name == "reference":
        import ref_runner
        return ref_runner.grade_reference
    if name == "replacement":
        import replacement
        return replacement.grade
    raise SystemExit(name)


res = []
for name in GRADERS:
    fn = get_fn(name)
    for f in FIX:
        kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
        try:
            v = "pass" if fn(f["check"], kw, prompt, f["response"]) else "fail"
        except Exception as e:  # noqa: BLE001
            v = "error:" + type(e).__name__ + ":" + str(e)[:80]
        res.append(dict(grader=name, id=f["id"], check=f["check"], label=f["label"], verdict=v, dec=f["dec"], note=f["note"]))

out = common.W / "audit" / "work" / ("fixture_results_" + "_".join(GRADERS) + ".json")
out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
for name in GRADERS:
    rs = [r for r in res if r["grader"] == name]
    wrong = [r for r in rs if r["verdict"] != r["label"]]
    print(f"== {name}: {len(rs)} fixtures, {len(wrong)} differ from label "
          f"({sum(1 for r in wrong if not r['dec'])} with no decision involved)")
    for r in wrong:
        tag = "FINDING?" if not r["dec"] else "DECISION " + ",".join(r["dec"])
        print(f"  {r['id']:<50} label={r['label']:<4} got={r['verdict']:<6} {tag} | {r['note']}")
