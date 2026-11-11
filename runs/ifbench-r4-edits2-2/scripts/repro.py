"""Reproduce a verdict.

  repro.py FIXTURE_ID                      one fixture from audit/tests/fixtures.py
  repro.py --adhoc CHECK KWARGS_JSON TEXT  any response (TEXT is unescaped with
                                           unicode_escape, so \\n is a newline)
  repro.py --panel CFG RUN KEY             one stored panel response (all its checks)

Prints the grader's strict and loose verdicts, the reference's strict and loose verdicts,
and the replacement's verdict. Run from W:
  PYTHONDONTWRITEBYTECODE=1 NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe audit/scripts/repro.py ...
For panel responses only the first 300 characters are printed, and a completion whose
reasoning never closes is not printed at all.
"""
import codecs
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "tests"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import graders as G  # noqa: E402


def v(fn, *a, **k):
    try:
        return "pass" if fn(*a, **k) else "fail"
    except Exception as e:  # noqa: BLE001
        return f"EXCEPTION {type(e).__name__}: {e}"


def show(check, kw, resp, prompt=None, xfail=False):
    print("  grader strict    :", v(G.grade_grader, check, kw, resp, prompt=prompt))
    print("  grader loose     :", v(G.grade_grader, check, kw, resp, prompt=prompt, loose=True))
    print("  reference strict :", v(G.grade_reference, check, kw, resp, prompt=prompt))
    print("  reference loose  :", v(G.grade_reference, check, kw, resp, prompt=prompt, loose=True))
    if xfail:
        print("  replacement      : fail (extraction failure: reasoning never closes)")
    else:
        print("  replacement      :", v(G.grade_replacement, check, kw, resp, prompt=prompt))


if sys.argv[1] == "--panel":
    import pyarrow.parquet as pq
    cfg, run, key = sys.argv[2], sys.argv[3], sys.argv[4]
    rows = {x["key"]: x for x in pq.read_table(os.path.join(W, "case", "data", "train-00000-of-00001.parquet")).to_pylist()}
    row = rows[key]
    rec = next(json.loads(l) for l in open(os.path.join(W, "case", "panel", cfg, run + ".jsonl"), encoding="utf-8")
               if str(json.loads(l)["key"]) == key)
    xfail = "<think>" in rec["raw_response"] and "</think>" not in rec["raw_response"]
    print(f"panel {cfg}/{run} key {key} finish={rec['finish_reason']} response length={len(rec['response'])}")
    if xfail:
        print("response: [reasoning never closes; not printed]")
    else:
        print("response[:300] =", repr(rec["response"][:300]))
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        kw = {k: x for k, x in kw.items() if x is not None}
        print(f"check {iid} kwargs={json.dumps(kw, ensure_ascii=False)[:200]}")
        show(iid, kw, rec["response"], prompt=row["prompt"], xfail=xfail)
elif sys.argv[1] == "--adhoc":
    check, kw, text = sys.argv[2], json.loads(sys.argv[3]), codecs.decode(sys.argv[4], "unicode_escape")
    print(f"check {check} kwargs={kw}")
    print("response =", repr(text))
    show(check, kw, text)
else:
    from fixtures import FIXTURES
    f = next(x for x in FIXTURES if x["id"] == sys.argv[1])
    print(f"fixture {f['id']}  label (contract) = {f['label']}  tags = {f['tags']}")
    print("check    =", f["check"])
    print("kwargs   =", json.dumps(f["kwargs"], ensure_ascii=False))
    print("response =", repr(f["response"]))
    show(f["check"], f["kwargs"], f["response"])
