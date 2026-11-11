"""Grade the earlier RLVR1 audit's 625 fixtures with one run's replacement grader, and save the verdicts.

The key is the earlier audit's fixture matrix (not published): a fixture on which a grader is wrong and no decision
entry explains the verdict is a defect fixture of that grader (NVIDIA 39, verifyit 65). For those fixtures the label
does not depend on any reading, so a run corrects one when its replacement gives the label.

Run it with the run's own interpreter; it changes into the run's folder and imports the run's replacement grader.

Usage: <workspace python> -B -X utf8 key_battery.py <record> <workspace> <key folder> <out.json>
records: rlvr1-r4-1, rlvr1-r4-2, rlvr1-r4-edits2-1, rlvr1-r4-edits2-2
"""

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
RECORD, W, KEY, OUT = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
fixtures = {}
for name in ("fixtures_a.jsonl", "fixtures_b.jsonl", "fixtures_findings.jsonl", "fixtures_review.jsonl"):
    for line in (KEY / "fixtures" / name).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            fixtures[row["fixture_id"]] = row
matrix = json.loads((KEY / "results" / "fixture_matrix.json").read_text(encoding="utf-8"))
stored = {row["fixture_id"]: row for row in matrix["matrix"]}
defects = {
    grader: {item["fixture_id"] for items in matrix["wrong"][grader].values() for item in items if not item["explained_by"]}
    for grader in ("nvidia", "verifyit")
}
assert (len(defects["nvidia"]), len(defects["verifyit"])) == (39, 65), {k: len(v) for k, v in defects.items()}
os.chdir(W)


def no_none(kwargs: dict) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


# Each run wrote one replacement for both graders: (folder, module, function).
ENTRY = {
    "rlvr1-r4-1": ("audit", "replacement", "check_constraint"),
    "rlvr1-r4-2": ("audit/lib", "contract_grader", "check"),
    "rlvr1-r4-edits2-1": ("audit/lib", "contracts_grader", "check"),
    "rlvr1-r4-edits2-2": ("audit", "replacement", "check"),
}
if RECORD not in ENTRY:
    sys.exit(f"unknown record {RECORD}; known: {sorted(ENTRY)}")
folder, module, function = ENTRY[RECORD]
sys.path.insert(0, str(W / folder))
check = getattr(__import__(module), function)


def safe(iid, kwargs, text):
    try:
        return bool(check(iid, no_none(kwargs), text))
    except Exception as exc:  # noqa: BLE001
        return f"EXC {type(exc).__name__}: {str(exc)[:60]}"


rows = []
for fid, f in fixtures.items():
    verdict = safe(f["instruction_id"], dict(f.get("kwargs") or {}), f["response"])
    rows.append({
        "fixture_id": fid, "instruction_id": f["instruction_id"], "label": f["label"],
        "expected": f["label"] == "pass", "nvidia_stored": stored[fid]["nvidia"], "verifyit_stored": stored[fid]["verifyit"],
        "defect_nvidia": fid in defects["nvidia"], "defect_verifyit": fid in defects["verifyit"],
        "replacement_for_nvidia": verdict, "replacement_for_verifyit": verdict,
    })
OUT.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
for grader, column in (("nvidia", "replacement_for_nvidia"), ("verifyit", "replacement_for_verifyit")):
    d = [r for r in rows if r[f"defect_{grader}"]]
    ok = sum(r[column] is r["expected"] for r in d)
    right = [r for r in rows if r[f"{grader}_stored"] is r["expected"]]
    keep = sum(r[column] is r["expected"] for r in right)
    exc = sum(isinstance(r[column], str) for r in rows)
    print(f"{RECORD} {grader}: replacement gives the earlier label on {ok} of {len(d)} defect fixtures, and on {keep} "
          f"of {len(right)} fixtures the grader gets right; raises on {exc}")
