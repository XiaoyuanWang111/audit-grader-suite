"""Tabulate the RLVR1 fixture battery of several runs (outputs of key_battery.py).

For each grader: defect fixtures on which the run's replacement gives the earlier label; instruction ids with a defect
fixture whose defect fixtures the replacement corrects all / some / none of; fixtures the grader gets right that the
replacement keeps right; replacement exceptions.

Usage: python -X utf8 battery_table.py <folder with battery_<record>.json> <record> [<record> ...]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
FOLDER, RECORDS = Path(sys.argv[1]), sys.argv[2:]
data = {r: json.loads((FOLDER / f"battery_{r}.json").read_text(encoding="utf-8")) for r in RECORDS}

lines = []
for grader in ("nvidia", "verifyit"):
    col = f"replacement_for_{grader}"
    cells = {}
    for record, rows in data.items():
        defect = [r for r in rows if r[f"defect_{grader}"]]
        right = [r for r in rows if r[f"{grader}_stored"] is r["expected"]]
        by_id = defaultdict(list)
        for r in defect:
            by_id[r["instruction_id"]].append(r[col] is r["expected"])
        full = sum(all(v) for v in by_id.values())
        none = sum(not any(v) for v in by_id.values())
        cells[record] = {
            "defect": f"{sum(r[col] is r['expected'] for r in defect)} of {len(defect)}",
            "ids": f"{full} / {len(by_id) - full - none} / {none} (of {len(by_id)})",
            "right": f"{sum(r[col] is r['expected'] for r in right)} of {len(right)}",
            "exceptions": str(sum(isinstance(r[col], str) for r in rows)),
        }
    lines.append(f"## {grader}")
    lines.append("| | " + " | ".join(RECORDS) + " |")
    lines.append("|---|" + "---|" * len(RECORDS))
    for key, label in (("defect", "defect fixtures corrected"), ("ids", "ids all / some / none"),
                       ("right", "right fixtures kept"), ("exceptions", "replacement raised")):
        lines.append(f"| {label} | " + " | ".join(cells[r][key] for r in RECORDS) + " |")
    lines.append("")
print("\n".join(lines))
