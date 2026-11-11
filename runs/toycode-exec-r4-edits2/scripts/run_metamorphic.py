"""Grade the metamorphic suite with all three graders; print each grader's wrong verdicts per edit as JSON."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
import metamorphic  # noqa: E402

res = metamorphic.grade_all()
cases = metamorphic.cases()
misses = {}
for kind, r in res.items():
    assert r["returncode"] == 0, (kind, r["stderr"][-2000:])
    m = {}
    for c in cases:
        v = r["verdicts"].get(c["id"])
        if v != c["label"]:
            m.setdefault(c["edit"], []).append(c["task"])
    misses[kind] = m
print(json.dumps({"n_cases": len(cases), "misses": misses}, indent=1, sort_keys=True))
