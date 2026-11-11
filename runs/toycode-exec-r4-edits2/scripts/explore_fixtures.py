"""Grade every fixture with the grader, the reference and the replacement; print a table (exploration only)."""

import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
import harness  # noqa: E402
from fixtures import FIXTURES, ROBUSTNESS  # noqa: E402


def grade_one(fx):
    out = {}
    for kind in ("grader", "reference", "replacement"):
        r = harness.run(kind, [harness.row("x", fx["task"], fx["response"])])
        out[kind] = r["verdicts"].get("x", f"NONE(rc={r['returncode']})")
    for dec, (sw, alt_label) in fx["alt"].items():
        r = harness.run("replacement", [harness.row("x", fx["task"], fx["response"])], switches=sw)
        out[dec] = (r["verdicts"].get("x"), alt_label)
    return fx, out


with ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(grade_one, FIXTURES + ROBUSTNESS))

for fx, out in results:
    flags = []
    for kind, okkey in (("grader", "grader_ok"), ("reference", "reference_ok")):
        ok = out[kind] == fx["label"]
        if ok != fx[okkey]:
            flags.append(f"{kind}-flag-mismatch")
    if out["replacement"] != fx["label"]:
        flags.append("REPLACEMENT-WRONG")
    for dec in fx["alt"]:
        got, want = out[dec]
        if got != want:
            flags.append(f"ALT-{dec}-WRONG({got})")
    print(f"{fx['id']:<24} {fx['task']} label={fx['label']:<4} g={out['grader']:<12} r={out['reference']:<12} "
          f"x={out['replacement']:<5} {' '.join(flags)}  # {fx['note']}")
