"""Reproduce the IFBench rerun's F-csvquotes-indexerror on the grader and the reference: an empty tab-separated field.

The workspace is a folder that holds `case/` (rebuilt as `cases/ifbench/SOURCES.md` describes) and `audit/` (a copy
of `runs/ifbench-r3/`). Reads the workspace only. Run it with the case's Python environment.

Usage: <python> -B -X utf8 keys/tools/ifbench/probe_csvquotes.py <workspace>
"""

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit(__doc__)
W = Path(sys.argv[1]).resolve()
for sub in ("audit/tests", "audit/lib", "audit/replacement"):
    sys.path.insert(0, str(W / sub))
os.chdir(W)

import ifb

ifb.verify_pins()
import ifbench_contract as rep

row = next(r for r in ifb.load_rows() if "custom:csv_quotes" in r["instruction_id_list"])
j = row["instruction_id_list"].index("custom:csv_quotes")
kwargs = {k: v for k, v in (row["kwargs"][j] or {}).items() if v is not None}
header = "\t".join(f'"{name}"' for name in ("StudentID", "Subject", "Grade", "Semester", "Score"))
cases = {
    "three full rows": [header] + ["\t".join(f'"{v}"' for v in (i, "Math", "A", "Fall", 90 + i)) for i in range(1, 4)],
    "one empty field": [
        header,
        '"1"\t\t"A"\t"Fall"\t"91"',
        '"2"\t"Math"\t"B"\t"Fall"\t"92"',
        '"3"\t"Art"\t"A"\t"Fall"\t"93"',
    ],
}
for name, lines in cases.items():
    response = "\n".join(lines)
    out = []
    for grader in ("grader", "reference"):
        verdict, error = ifb.verdict(grader, "custom:csv_quotes", kwargs, row["prompt"], response)
        out.append(f"{grader}={'EXC ' + str(error)[:80] if verdict is None else ('pass' if verdict else 'fail')}")
    try:
        out.append(
            f"replacement={'pass' if rep.check('custom:csv_quotes', kwargs, row['prompt'], response) else 'fail'}"
        )
    except Exception as exc:
        out.append(f"replacement=EXC {type(exc).__name__}")
    print(f"{name:18s} key {row['key']} " + " ".join(out))
