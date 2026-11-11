"""Print short excerpts of panel responses where the grader and the replacement disagree.

Usage: python audit/scripts/show_disagreements.py <check> [n] [gs-value: pass|fail] [held-out-ok]
Prints at most 160 characters from the start and 80 from the end of each graded text.
"""
import json
import random
import sys

import common

check = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
want = sys.argv[3] if len(sys.argv) > 3 else None
ex = json.load(open(common.W / "audit" / "work" / "panel_disagreement_examples.json", encoding="utf-8"))[check]
ex = [e for e in ex if not (e["run"] == "sample7" or (e["folder"].endswith("__thinking") and e["run"] == "greedy_repeat"))]
if want:
    ex = [e for e in ex if e["gs"] is (want == "pass")]
random.Random(1).shuffle(ex)
order = common.row_list()
for e in ex[:n]:
    lines = (common.CASE / "panel" / e["folder"] / f"{e['run']}.jsonl").read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[order.index(e["key"])])
    t = rec["response"]
    print(f"--- {e['folder']}/{e['run']} key={e['key']} grader={e['gs']} repl={e['rep']} ref={e['rs']} alts={e['alts']}")
    print("   START:", ascii(t[:160]))
    if len(t) > 240:
        print("   END:  ", ascii(t[-80:]))
