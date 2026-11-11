"""Compare blind runs on the earlier IFBench audit's public fixtures, from the files that `key_battery.py` writes.

Prints how many fixtures the grader gets wrong, and for each run how many of them its replacement grader corrects and
how many of the others it keeps right; then, per earlier finding, how many of the finding's fixtures each run's
replacement corrects, and per run how many findings it corrects fully, in part or not at all. Each file is named
`battery_<kind>.json`, and the kind labels its column. Read-only.

Usage: python -B keys/tools/ifbench/battery_table.py <battery_run1.json> <battery_armA.json> [...]
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 3:
    sys.exit(__doc__)
kinds = tuple(Path(path).stem.removeprefix("battery_") for path in sys.argv[1:])
base = kinds[0]


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


R = {k: {r["id"]: r for r in load(path)} for k, path in zip(kinds, sys.argv[1:], strict=True)}


def norm(v):
    return "EXC" if isinstance(v, str) else v


ids = list(R[base])
assert all(norm(R[k][i]["grader"]) == norm(R[base][i]["grader"]) for k in kinds for i in ids)
none = (None, "None")
gw = [i for i in ids if norm(R[base][i]["grader"]) != R[base][i]["expected"]]
print(
    "fixtures",
    len(ids),
    "| grader wrong",
    len(gw),
    "| with a finding id:",
    sum(R[base][i]["finding"] not in none for i in gw),
    "| decision only:",
    sum(R[base][i]["finding"] in none and R[base][i]["decision"] not in none for i in gw),
    "| neither:",
    sum(R[base][i]["finding"] in none and R[base][i]["decision"] in none for i in gw),
)
ctrl = [i for i in ids if i not in gw]
for k in kinds:
    fixed = sum(R[k][i]["replacement"] == R[k][i]["expected"] for i in gw)
    right = sum(R[k][i]["replacement"] == R[k][i]["expected"] for i in ctrl)
    print(
        f"{k}: gives the earlier label on {fixed} of {len(gw)} fixtures the grader gets wrong, "
        f"and on {right} of {len(ctrl)} it gets right"
    )
by = collections.defaultdict(list)
for i in gw:
    f = R[base][i]["finding"]
    by[f if f not in none else "D:" + str(R[base][i]["decision"])].append(i)


def key(s):
    m = re.match(r"F(\d+)", s)
    return (0, int(m.group(1)), s) if m else (1, 0, s)


print(f"{'earlier finding':26s} {'n':>2s}  " + " ".join(f"{k:>5s}" for k in kinds) + "  checks")
tot = collections.Counter()
for f in sorted(by, key=key):
    row = by[f]
    cells = []
    for k in kinds:
        n = sum(R[k][i]["replacement"] == R[k][i]["expected"] for i in row)
        cells.append(f"{n}/{len(row)}")
        if f.startswith("F"):
            tot[k, "all"] += n == len(row)
            tot[k, "some"] += 0 < n < len(row)
            tot[k, "none"] += n == 0
    print(
        f"{f[:26]:26s} {len(row):2d}  "
        + " ".join(f"{c:>5s}" for c in cells)
        + f"  {','.join(sorted({R[base][i]['check'] for i in row}))[:64]}"
    )
nf = sum(1 for f in by if f.startswith("F"))
print("earlier findings with a grader-wrong fixture:", nf)
for k in kinds:
    print(f"  {k}: all fixtures corrected {tot[k, 'all']}, some {tot[k, 'some']}, none {tot[k, 'none']}")
