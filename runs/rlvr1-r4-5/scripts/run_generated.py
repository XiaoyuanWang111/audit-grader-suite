"""Grade the generated fixtures in audit/fixtures.jsonl (property, metamorphic, fuzz, content-free)
with NV, VS, VG and R, and write tests/expected_wrong_generated.json (pairs to mark xfail strict)."""
import json
import random
import sys

sys.path.insert(0, "<W>/audit")
import harness as h  # noqa: E402

A = "<W>/audit"
SEED = 20261112


def verdict(g, iid, kw, resp):
    random.seed(SEED)
    if g == "NV":
        return h.nv_check(iid, kw, resp)[0]
    if g == "VS":
        return h.vs_check(iid, kw, resp)[0]
    if g == "VG":
        return h.vg_check(iid, kw, resp)[0]
    return h.R.check(iid, kw, resp)


wrong = []
counts = {}
for line in open(f"{A}/fixtures.jsonl", encoding="utf-8"):
    d = json.loads(line)
    if d["source"].startswith("hand-written"):
        continue
    for g in ("NV", "VS", "VG", "R"):
        v = verdict(g, d["instruction_id"], d["kwargs"], d["response"])
        if v is None:
            continue
        ok = ("pass" if v else "fail") == d["label"]
        counts[(g, ok)] = counts.get((g, ok), 0) + 1
        if not ok:
            wrong.append([d["id"], g])
json.dump(sorted(wrong), open(f"{A}/tests/expected_wrong_generated.json", "w", encoding="utf-8"), indent=0)
print({f"{g} {'ok' if ok else 'wrong'}": n for (g, ok), n in sorted(counts.items())})
