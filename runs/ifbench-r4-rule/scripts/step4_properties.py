"""Step 4 property tests: apply each contract-ignored transform to every passing fixture of the
checks where it must not change the verdict; record grader and reference verdict flips.

Writes audit/out/property_results.tsv and audit/tests/property_xfail.json.
"""
import collections
import json
import sys

W = "<W>"
sys.path.insert(0, f"{W}/audit/lib")
sys.path.insert(0, f"{W}/audit/tests")
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402
from properties import TRANSFORMS  # noqa: E402

rows, xfail = [], {}
by = collections.Counter()
for f in FIXTURES:
    if f["label"] is not True:
        continue
    kw = dict(key=f.get("key"), kwargs=f.get("kwargs"))
    base_g = H.grade(f["check"], f["response"], int_cast=True, **kw)
    base_r = H.grade(f["check"], f["response"], impl="reference", **kw)
    for name, (fn, ok) in TRANSFORMS.items():
        if not ok(f["check"]):
            continue
        t = fn(f["response"])
        if t == f["response"]:
            continue
        g = H.grade(f["check"], t, int_cast=True, **kw)
        r = H.grade(f["check"], t, impl="reference", **kw)
        pid = f"{f['id']}|{name}"
        rows.append((pid, f["check"], name, base_g, g, base_r, r))
        # a flip: the grader passed the original but not the transformed text
        if base_g is True and g is not True:
            xfail[pid] = {"check": f["check"], "transform": name, "grader": str(g)}
            by[(f["check"], name)] += 1

with open(f"{W}/audit/out/property_results.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("pid\tcheck\ttransform\tgrader_before\tgrader_after\treference_before\treference_after\n")
    for r in rows:
        out.write("\t".join(str(x) for x in r) + "\n")
json.dump(xfail, open(f"{W}/audit/tests/property_xfail.json", "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
print(f"{len(rows)} transformed cases; grader flips (pass -> not pass): {len(xfail)}")
for (c, t), n in sorted(by.items()):
    refflip = sum(1 for r in rows if r[1] == c and r[2] == t and r[5] is True and r[6] is not True)
    print(f"  {c:36s} {t:22s} grader flips {n}  reference flips {refflip}")
