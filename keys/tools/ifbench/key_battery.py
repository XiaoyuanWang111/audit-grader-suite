"""Grade the earlier IFBench audit's 143 public fixtures with one blind run's replacement grader and with the grader
under audit, and save the verdicts. A run "has" a behavior of the earlier audit when its replacement, written from its
own contracts, gives the label that the earlier audit's contract gives.

The fixtures are `data/fixtures.jsonl` of the Hugging Face dataset xiaoyuanwang/ifbench-audit. The workspace is the
run's: a folder that holds `case/` and the run's `audit/` (`run1` is runs/ifbench-r3, `armA` runs/ifbench-r4, `armB`
runs/ifbench-r4-rule, each with the work copies that RUNNER.md describes; for `armB`, `audit/lib/harness.py` and
`audit/replacement/grader.py` must name the workspace in place of `<W>`). The script runs with the case's Python
environment, changes into the workspace and reads it only.

Usage: <python> -B -X utf8 keys/tools/ifbench/key_battery.py <run1|armA|armB> <workspace> <fixtures.jsonl> <out.json>
"""

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 5:
    sys.exit(__doc__)
KIND, W, FIXTURES, OUT = (
    sys.argv[1],
    Path(sys.argv[2]).resolve(),
    Path(sys.argv[3]).resolve(),
    Path(sys.argv[4]).resolve(),
)
os.chdir(W)

if KIND == "run1":
    for sub in ("audit/tests", "audit/lib", "audit/replacement"):
        sys.path.insert(0, str(W / sub))
    import ifb
    import ifbench_contract as rep

    def grader(iid, kwargs, response):
        verdict, error = ifb.verdict("grader", iid, kwargs, "", response)
        return verdict if error is None else f"EXC {error[:60]}"

    def replacement(iid, kwargs, response):
        return bool(rep.check(iid, kwargs, "", response))
elif KIND == "armA":
    sys.path.insert(0, str(W / "audit" / "lib"))
    import ifbaudit as A
    import replacement as X

    def grader(iid, kwargs, response):
        return A.check_G(iid, kwargs, response, "")

    def replacement(iid, kwargs, response):
        return bool(X.check(iid, kwargs, response, "", sw=X.PROPOSED))
elif KIND == "armB":
    sys.path.insert(0, str(W / "audit"))
    sys.path.insert(0, str(W / "audit" / "lib"))
    import harness
    from replacement import grader as XB

    def grader(iid, kwargs, response):
        return harness.grade(iid, response, kwargs=kwargs, prompt="", impl="grader")

    def replacement(iid, kwargs, response):
        return bool(XB.grade(iid, response, kwargs, ""))
else:
    sys.exit("kind must be run1, armA or armB")


def safe(function, *args):
    try:
        value = function(*args)
    except Exception as exc:
        return f"EXC {type(exc).__name__}: {str(exc)[:60]}"
    return value if isinstance(value, (bool, str)) else bool(value)


rows = []
for line in FIXTURES.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    f = json.loads(line)
    kwargs = json.loads(f["kwargs_json"]) if f.get("kwargs_json") else {}
    rows.append(
        {
            "id": f["id"],
            "check": f["instruction_id"],
            "finding": f["finding"],
            "decision": f["decision"],
            "expected": f["expected"] in (True, "True"),
            "name": f["name"],
            "grader": safe(grader, f["instruction_id"], kwargs, f["response"]),
            "replacement": safe(replacement, f["instruction_id"], kwargs, f["response"]),
        }
    )
OUT.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
ok = sum(r["replacement"] == r["expected"] for r in rows)
exc = sum(isinstance(r["replacement"], str) for r in rows)
gw = sum(r["grader"] != r["expected"] for r in rows)
print(
    f"{KIND}: {len(rows)} fixtures; replacement gives the earlier label on {ok}, raises on {exc}; "
    f"grader differs from the label on {gw}"
)
