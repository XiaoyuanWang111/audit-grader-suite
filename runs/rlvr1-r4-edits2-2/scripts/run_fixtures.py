"""Run every fixture on every grader; print the table and write audit/out/fixture_verdicts.json."""
import json
import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AUDIT, "tests"))
from fixtures_data import FIXTURES  # noqa: E402
from verdicts import GRADERS, nvidia_error, verdict  # noqa: E402

rows = []
for f in FIXTURES:
    out = {"id": f["id"], "ref": f["ref"], "label": f["label"]}
    for g in GRADERS:
        out[g] = verdict(g, f["check"], f["kwargs"], f["response"])
    out["nvidia_error"] = nvidia_error(f["check"], f["kwargs"], f["response"])
    rows.append(out)
    wrong = [g for g in GRADERS if out[g] is not None and out[g] != f["label"]]
    flag = ("WRONG: " + ",".join(wrong)) if wrong else ""
    print(f"{f['id']:62s} {f['ref']:24s} label={f['label']!s:5} nv={out['nvidia']!s:5} vi={out['verifyit']!s:5} "
          f"re={out['replacement']!s:5} {flag} {out['nvidia_error'] or ''}  {f['response'][:40]!r}")
os.makedirs(os.path.join(AUDIT, "out"), exist_ok=True)
with open(os.path.join(AUDIT, "out", "fixture_verdicts.json"), "w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=1)
n = len(rows)
for g in GRADERS:
    graded = [r for r in rows if r[g] is not None]
    print(g, "wrong", sum(1 for r in graded if r[g] != r["label"]), "of", len(graded))
