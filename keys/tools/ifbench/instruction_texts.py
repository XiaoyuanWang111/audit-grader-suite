"""Write the instruction text of each of the 58 IFBench checks, built by the grader from the first dataset row that
uses the check.

The workspace is a folder that holds `case/` (rebuilt as `cases/ifbench/SOURCES.md` describes) and `audit/` (a copy
of `runs/ifbench-r3/`). Reads the workspace only and writes the output file. Run it with the case's Python
environment.

Usage: <python> -B -X utf8 keys/tools/ifbench/instruction_texts.py <workspace> <output file>
"""

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 3:
    sys.exit(__doc__)
W, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(W / "audit/lib"))
os.chdir(W)

import ifb

ifb.verify_pins()
rows = ifb.load_rows()
first = {}
count = {}
for row in rows:
    for iid, kwargs in zip(row["instruction_id_list"], row["kwargs"], strict=False):
        count[iid] = count.get(iid, 0) + 1
        first.setdefault(iid, (row["key"], kwargs or {}, row["prompt"]))
lines = []
for iid in sorted(first):
    key, kwargs, prompt = first[iid]
    clean = {k: v for k, v in kwargs.items() if v is not None}
    inst = ifb._instance("grader", iid, clean, prompt)
    text = getattr(inst, "_description_pattern", None)
    try:
        built = inst.build_description(**clean)
    except Exception as exc:
        built = f"<build_description raised {type(exc).__name__}: {exc}>"
    lines.append(f"## {iid}  (instances {count[iid]}, first key {key}, kwargs {clean})")
    lines.append(str(built if built else text))
    lines.append("")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
print(f"{len(first)} checks, {sum(count.values())} instances -> {OUT}")
