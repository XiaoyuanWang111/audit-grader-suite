"""Print short excerpts of grader/replacement disagreements for one check, development runs only
(Qwen3-4B folders; the Qwen2.5-7B and OLMo-2 runs are held out from inspection).

usage: inspect_cells.py <instruction_id> <grader skyrl|gate> <pass|fail = grader verdict> [n]
"""
import json
import sys
from pathlib import Path

A = Path("<W>/audit")
CASE = A.parent / "case"
sys.path.insert(0, str(A / "lib"))
import harness as h  # noqa: E402

iid, grader, gv = sys.argv[1], sys.argv[2], sys.argv[3] == "pass"
n = int(sys.argv[4]) if len(sys.argv) > 4 else 6
dev = ("Qwen__Qwen3-4B-Instruct-2507", "Qwen__Qwen3-4B-Thinking-2507__thinking")
rows = h.load_rows()
shown = 0
for line in open(A / "work" / "panel_verdicts.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["folder"] not in dev or iid not in r["ids"] or r["extraction_failure"]:
        continue
    j = r["ids"].index(iid)
    v = r["skyrl"][j] if grader == "skyrl" else r["gate"][j]
    if v is None or bool(v) != gv or bool(r["repl"][j]) == gv:
        continue
    path = CASE / "panel" / r["folder"] / f"{r['run']}.jsonl"
    with open(path, encoding="utf-8") as f:
        for i, l in enumerate(f):
            if i == r["i"]:
                raw = json.loads(l)["raw_response"]
                break
    g = h.skyrl_text(raw)
    kw = rows[r["uuid"]]["kwargs"][j]
    print(f"--- {r['folder']}/{r['run']}#{r['i']} kw={json.dumps(kw, ensure_ascii=False)[:90]} len={len(g)}")
    print("   HEAD:", repr(g[:160]))
    print("   TAIL:", repr(g[-160:]))
    shown += 1
    if shown >= n:
        break
