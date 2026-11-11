"""Write audit/panel/regraded_trials/tNN/result.json: each stored record with the replacement verifier's exit status
and output (from audit/panel/panel_verdicts.json) in place of the stored ones, so that a scorer can score it.

Usage: python -B audit/scripts/regrade_trials.py
Then:  python -B audit/replacement/score_trials.py audit/panel/regraded_trials
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import harness  # noqa: E402

PANEL = os.path.join(harness.AUDIT, "panel", "panel_verdicts.json")
OUT = os.path.join(harness.AUDIT, "panel", "regraded_trials")

with open(PANEL, encoding="utf-8") as f:
    rows = json.load(f)["rows"]
for row in rows:
    with open(os.path.join(harness.CASE, "trials", row["trial"], "result.json"), encoding="utf-8") as f:
        rec = json.load(f)
    rec["verifier_exit_code"] = row["replacement_exit"]
    rec["verifier_output"] = row["replacement_output"]
    d = os.path.join(OUT, row["trial"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, sort_keys=True)
        f.write("\n")
print(f"wrote {len(rows)} records under {os.path.relpath(OUT, harness.ROOT)}")
