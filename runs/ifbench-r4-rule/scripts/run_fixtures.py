"""Run every fixture against the grader (as-loaded float kwargs, and int-cast) and the reference.

Writes audit/out/fixture_results.tsv and prints the fixtures where the grader's verdict differs
from the contract label. Used to set the xfail marks in audit/tests/xfail.json.
"""
import collections
import json
import sys

W = "<W>"
sys.path.insert(0, f"{W}/audit/lib")
sys.path.insert(0, f"{W}/audit/tests")
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

rows = []
checks = collections.Counter()
for f in FIXTURES:
    kw = dict(key=f.get("key"), kwargs=f.get("kwargs"))
    g = H.grade(f["check"], f["response"], **kw)
    gi = H.grade(f["check"], f["response"], int_cast=True, **kw)
    r = H.grade(f["check"], f["response"], impl="reference", **kw)
    rows.append((f["id"], f["check"], f["kind"], f.get("decision") or "", f["label"], g, gi, r, f.get("note", "")))
    checks[f["check"]] += 1

with open(f"{W}/audit/out/fixture_results.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("id\tcheck\tkind\tdecision\tlabel\tgrader\tgrader_intcast\treference\tnote\n")
    for r in rows:
        out.write("\t".join(str(x) for x in r) + "\n")

print(f"{len(rows)} fixtures over {len(checks)} checks")
wrong = [r for r in rows if r[5] != r[4]]
print(f"grader verdict != label: {len(wrong)}")
for r in wrong:
    print(f"  {r[0]:45s} kind={r[2]:4s} dec={r[3]:22s} label={r[4]!s:5s} grader={r[5]!s:16s} int={r[6]!s:6s} ref={r[7]!s:16s} {r[8]}")
ref_wrong = [r for r in rows if r[7] != r[4]]
print(f"reference verdict != label: {len(ref_wrong)}")
