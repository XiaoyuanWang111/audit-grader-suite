"""Print short excerpts of panel disagreements for one check (development subset only).

Usage: show_cases.py <instruction_id> <A|B> <pass|fail|any> [k] [explained|unexplained|any]
Prints the graded answer only (never reasoning text): the first 300 and last 120 characters.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
W = os.path.dirname(AUDIT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(AUDIT, "replacement"))
from heldout import is_heldout  # noqa: E402
import contract_grader as R  # noqa: E402

iid, g, want = sys.argv[1], sys.argv[2], sys.argv[3]
k = int(sys.argv[4]) if len(sys.argv) > 4 else 5
which = sys.argv[5] if len(sys.argv) > 5 else "unexplained"

rows = {}
with open(os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
    for line in f:
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        rows[rec["uuid"]] = rec
raw_cache = {}


def raw_of(run, line_no):
    if run not in raw_cache:
        with open(os.path.join(W, "case", "panel", run), encoding="utf-8") as f:
            raw_cache[run] = [json.loads(x)["raw_response"] for x in f]
    return raw_cache[run][line_no]


shown = 0
with open(os.path.join(AUDIT, "work", "panel_verdicts.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if is_heldout(r["run"], r["uuid"]) or r["extraction_failure"]:
            continue
        for c in r["constraints"]:
            if c["iid"] != iid or c[g] == c["R"]:
                continue
            if want != "any" and c[g] != (want == "pass"):
                continue
            expl = any(v == c[g] for v in c["R_alt"].values())
            if which == "unexplained" and expl:
                continue
            if which == "explained" and not expl:
                continue
            rec = rows[r["uuid"]]
            kw = rec["kwargs"][rec["instruction_id_list"].index(iid)]
            text = R.graded_text(raw_of(r["run"], r["line"]), r["reasoning_model"])
            print(f"--- {r['run']} line {r['line']} uuid {r['uuid']} {g}={c[g]} R={c['R']} kwargs={json.dumps(kw, ensure_ascii=False)}")
            print("   HEAD:", json.dumps(text[:300], ensure_ascii=False))
            if len(text) > 300:
                print("   TAIL:", json.dumps(text[-120:], ensure_ascii=False))
            shown += 1
            if shown >= k:
                sys.exit(0)
