"""Step 4 metamorphic tests: ignored edits must keep a pass; the forbidden edit must give a fail.

Writes audit/work/metamorphic_results.json; prints every wrong verdict.
"""
import json
import sys
from collections import Counter
from pathlib import Path

A = Path("<W>/audit")
sys.path.insert(0, str(A / "lib"))

from metamorphic_specs import SPECS, apply_edit  # noqa: E402
from verdicts import fixture_id, verdicts  # noqa: E402

results = []
flips = Counter()
for iid, kwargs, base, target, ignored, (find, repl) in SPECS:
    base_v = verdicts(iid, kwargs, base)
    rec = {"instruction_id": iid, "kwargs": kwargs, "base": base, "base_verdicts": base_v, "edits": []}
    if base_v["replacement"] != "pass":
        print("REPLACEMENT FAILS BASE", iid)
    for edit in ignored:
        text = apply_edit(base, target, edit)
        v = verdicts(iid, kwargs, text)
        wrong = [g for g in ("skyrl", "gate", "replacement") if v[g] is not None and base_v[g] == "pass" and v[g] == "fail"]
        rec["edits"].append({"edit": edit, "response": text, "label": "pass", "verdicts": v, "flipped": wrong,
                             "id": fixture_id(iid, kwargs, text)})
        for g in wrong:
            flips[(g, edit)] += 1
            print(f"FLIP {g:<11} {iid:<45} {edit:<16} {text[:70]!r}")
    if not base.count(find):
        raise ValueError(f"forbidden edit target missing for {iid}")
    bad = base.replace(find, repl, 1)
    v = verdicts(iid, kwargs, bad)
    wrong = [g for g in ("skyrl", "gate", "replacement") if v[g] == "pass"]
    rec["forbidden"] = {"response": bad, "label": "fail", "verdicts": v, "wrong": wrong, "id": fixture_id(iid, kwargs, bad)}
    for g in wrong:
        print(f"FORBIDDEN-PASS {g:<11} {iid:<45} {bad[:70]!r}")
    not_pass = [g for g in ("skyrl", "gate") if base_v[g] == "fail"]
    if not_pass:
        print(f"BASE-FAIL {','.join(not_pass):<11} {iid:<45} {base[:70]!r}")
    results.append(rec)
(A / "work" / "metamorphic_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print("flip counts (grader, edit):")
for k, n in sorted(flips.items()):
    print(" ", k, n)
