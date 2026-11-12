"""Print development-part panel disagreements for one check (n < 300 in each run file only).

Usage: python panel_inspect.py CHECK GRADER(A|B) [k] [head] [tail]
Prints only short excerpts of the graded text (after the last </think>), never reasoning text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402

cg = fl.cg
check, grader = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
head = int(sys.argv[4]) if len(sys.argv) > 4 else 160
tail = int(sys.argv[5]) if len(sys.argv) > 5 else 80
DEV_N = 300

kwargs = {}
for idx, line in enumerate((W / "case/data/rlvr1_instruction_following.jsonl").open(encoding="utf-8")):
    rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
    kwargs[idx] = rec["kwargs"]
want = []
for line in (W / "audit/work/panel_verdicts.jsonl").open(encoding="utf-8"):
    r = json.loads(line)
    if r["n"] >= DEV_N or r["extraction_failure"]:
        continue
    for i, iid in enumerate(r["ids"]):
        if iid != check:
            continue
        gv = r["A"][i] if grader == "A" else r["B"][i]
        if gv is None or gv == r["R"][i]:
            continue
        want.append((r, i, gv))
print(len(want), "dev disagreements")
raws = {}
for r, i, gv in want[:k]:
    path = W / "case/panel" / r["file"]
    if r["file"] not in raws:
        raws[r["file"]] = path.read_text(encoding="utf-8").splitlines()
    raw = json.loads(raws[r["file"]][r["n"]])["raw_response"]
    text = cg.graded_text(raw, r["reasoning"]).strip()
    kw = kwargs[r["row"]][i]
    readings = fl.explain(check, kw, raw, gv, r["reasoning"])
    print(f"--- {r['file']} n={r['n']} kw={json.dumps(kw, ensure_ascii=False)[:80]} {grader}={gv} R={r['R'][i]} readings={readings}")
    print("   head:", repr(text[:head]))
    if len(text) > head and tail > 0:
        print("   tail:", repr(text[-tail:]))
