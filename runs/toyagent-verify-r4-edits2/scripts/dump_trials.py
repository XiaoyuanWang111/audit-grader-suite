"""Print one row per stored trial: record fields and the files in its workspace (as bytes reprs).

Usage: python -B audit/scripts/dump_trials.py [CASE_DIR]
"""

import json
import os
import sys

CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "case")
TRIALS = os.path.join(CASE, "trials")

for name in sorted(os.listdir(TRIALS)):
    d = os.path.join(TRIALS, name)
    with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
        r = json.load(f)
    print(f"== {name} keys={sorted(r)}")
    for k in ("trial_id", "task", "config", "agent_status", "agent_error", "agent_steps",
              "verifier_exit_code", "verifier_output"):
        print(f"   {k}: {r.get(k)!r}")
    ws = os.path.join(d, "workspace")
    if not os.path.isdir(ws):
        print("   workspace: <none>")
        continue
    for root, dirs, files in os.walk(ws):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, ws).replace(os.sep, "/")
            with open(p, "rb") as f:
                data = f.read()
            shown = data if len(data) <= 120 else data[:120] + b"..."
            print(f"   file {rel} ({len(data)} B): {shown!r}")
