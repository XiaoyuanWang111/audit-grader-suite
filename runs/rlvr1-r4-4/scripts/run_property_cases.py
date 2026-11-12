"""Run audit/tests/property_cases.json against A, B and R; write tests/known_failures_props.json.

A case that the replacement gets wrong is printed: it means the edit was not as neutral (or as
forbidding) as intended under some reading, or that the replacement is wrong; such cases are
dropped from the test list and listed here for review.
"""
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
import harness as H  # noqa: E402

FINDING = {}
exec(open(os.path.join(AUDIT, "scripts", "make_known_failures.py"), encoding="utf-8").read().split("known = {}")[0]
     .split("FINDING = ", 1)[1].join(["FINDING = ", ""]) if False else "", {})
src = open(os.path.join(AUDIT, "scripts", "make_known_failures.py"), encoding="utf-8").read()
ns = {}
exec(src[src.index("FINDING = {"):src.index("known = {}")], ns)
FINDING = ns["FINDING"]

cases = json.load(open(os.path.join(AUDIT, "tests", "property_cases.json"), encoding="utf-8"))
known, kept, dropped = {}, [], []
viol = {"A": {}, "B": {}}
for c in cases:
    iid, kw, resp = c["instruction_id"], c["kwargs"], c["response"]
    r = "pass" if H.r_check(iid, kw, resp) else "fail"
    if r != c["label"]:
        dropped.append(c)
        continue
    kept.append(c)
    random.seed(0)
    a = "pass" if H.a_check(iid, kw, resp)[0] else "fail"
    b = None if iid in H.SEMANTIC else ("pass" if H.b_check(iid, kw, resp)[0] else "fail")
    for g, v in (("A", a), ("B", b)):
        if v is None or v == c["label"]:
            continue
        reason = " + ".join(c["decisions"]) if c["decisions"] else FINDING.get((g, iid), "F-new")
        known[f"{g}|{c['id']}"] = reason
        viol[g].setdefault(c["kind"], []).append((c["id"], reason))
with open(os.path.join(AUDIT, "tests", "property_cases.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(kept, f, ensure_ascii=False, indent=1)
with open(os.path.join(AUDIT, "tests", "known_failures_props.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(dict(sorted(known.items())), f, indent=1)
print(f"{len(kept)} cases kept, {len(dropped)} dropped (replacement disagrees with the intended label)")
for c in dropped:
    print("   dropped", c["id"], json.dumps(c["response"], ensure_ascii=False)[:100])
for g in ("A", "B"):
    for kind, items in sorted(viol[g].items()):
        print(f"{g} {kind}: {len(items)} violations: " + ", ".join(sorted({r for _, r in items})))
        for i, r in items:
            print("      ", i, r)

# The property view: a metamorphic edit must not change a grader's verdict; a forbidden edit must
# turn a grader's pass into a fail.
sys.path.insert(0, os.path.join(AUDIT, "tests"))
from fixtures_data import FIXTURES  # noqa: E402
src = {f["id"]: f for f in FIXTURES}
prop = {"A": collections.Counter() if False else {}, "B": {}}
import collections  # noqa: E402
prop = {"A": collections.defaultdict(list), "B": collections.defaultdict(list)}
for c in kept:
    s = src[c["source"]]
    for g in ("A", "B"):
        if g == "B" and c["instruction_id"] in H.SEMANTIC:
            continue
        random.seed(0)
        f = H.a_check if g == "A" else H.b_check
        before = f(s["instruction_id"], s["kwargs"], s["response"])[0]
        random.seed(0)
        after = f(c["instruction_id"], c["kwargs"], c["response"])[0]
        if c["kind"].startswith("M-") and before != after:
            prop[g][c["kind"]].append((c["id"], c["instruction_id"]))
        if c["kind"] == "E-forbidden-edit" and before and after:
            prop[g][c["kind"]].append((c["id"], c["instruction_id"]))
print("\nproperty violations (metamorphic: verdict changed; forbidden edit: still passes)")
for g in ("A", "B"):
    for kind, items in sorted(prop[g].items()):
        print(f"{g} {kind}: {len(items)}: " + ", ".join(sorted({i.split(':')[1] for _, i in items})))
        for cid_, _ in items:
            print("      ", cid_)
