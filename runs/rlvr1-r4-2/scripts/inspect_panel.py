"""Show unexplained disagreements between a grader and the replacement on non-held-out panel responses.

Usage: python inspect_panel.py <A|B> <check id> [n] [max_chars]
Prints the kwargs, the verdicts and a short excerpt of the graded text (never a reasoning block).
"""
import hashlib
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402

grader, check = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
width = int(sys.argv[4]) if len(sys.argv) > 4 else 300
rows = {r["uuid"]: r for r in gu.load_rows()}
raw_cache = {}


def raw_of(rec):
    key = rec["file"]
    if key not in raw_cache:
        raw_cache[key] = (W / "case" / "panel" / key).read_text(encoding="utf-8").splitlines()
    return json.loads(raw_cache[key][rec["line"] - 1])["raw_response"]


shown = 0
for line in (W / "audit" / "out" / "panel_verdicts.jsonl").open(encoding="utf-8"):
    rec = json.loads(line)
    if hashlib.sha256(rec["uuid"].encode()).hexdigest()[0] in "012":
        continue
    if rec["extraction_differs_" + grader]:
        continue
    for i, c in enumerate(rec["cons"]):
        if c["id"] != check or c[grader] is None or c[grader] is c["R"]:
            continue
        if c.get(grader + "_explained") or c.get(grader + "_explained_all_used"):
            continue
        text = cg.graded_text(raw_of(rec), rec["reasoning"]).strip()
        kw = rows[rec["uuid"]]["record"]["kwargs"][i]
        print(f"--- {rec['file']}:{rec['line']} {grader}={c[grader]} R={c['R']} kwargs={kw} len={len(text)}")
        print("   ", repr(text[:width]))
        if len(text) > width:
            print("    ...", repr(text[-150:]))
        shown += 1
        break
    if shown >= n:
        break
