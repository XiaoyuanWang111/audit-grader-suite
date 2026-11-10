"""Locate each instruction's text inside its prompts.

For an id with two or more rows, the longest common substring of the first two
prompts is taken as the template core; every row then prints the core's context
(PAD chars on each side). For an id with one row, the whole prompt is printed
when it is short, else its head and tail.

Usage: python audit/scripts/instr_text.py [--pad N] [--max-rows K] id ...   (no ids = all)
"""
import difflib
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]


def nn(kw):
    return {k: v for k, v in kw.items() if v is not None}


def core(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    m = sm.find_longest_match(0, len(a), 0, len(b))
    return a[m.a:m.a + m.size]


def main(argv):
    pad, maxrows = 120, 99
    while argv and argv[0].startswith("--"):
        if argv[0] == "--pad":
            pad = int(argv[1])
        elif argv[0] == "--max-rows":
            maxrows = int(argv[1])
        argv = argv[2:]
    ids = argv or sorted({x for r in ROWS for x in r["instruction_id_list"]})
    for iid in ids:
        rows = [(i, r) for i, r in enumerate(ROWS) if iid in r["instruction_id_list"]]
        print("=" * 10, iid, "rows:", [i for i, _ in rows])
        if len(rows) == 1:
            i, r = rows[0]
            p = r["prompt"]
            j = r["instruction_id_list"].index(iid)
            print(f"  row {i} kw={nn(r['kwargs'][j])}")
            print("  ", repr(p if len(p) < 1500 else p[:600] + " [...] " + p[-800:]))
            continue
        # template core: the common substring shared by the most rows
        best = ""
        for a in range(min(3, len(rows))):
            for b in range(a + 1, len(rows)):
                c = core(rows[a][1]["prompt"], rows[b][1]["prompt"])
                if len(c) > len(best):
                    best = c
        print("  core:", repr(best))
        for i, r in rows[:maxrows]:
            p = r["prompt"]
            j = r["instruction_id_list"].index(iid)
            k = p.find(best)
            if k < 0:
                snippet = "(core not found) tail: " + p[-2 * pad:]
            else:
                snippet = p[max(0, k - pad):k] + "<<" + best[:40] + "...>>" + p[k + len(best):k + len(best) + pad]
            print(f"  row {i} ids={r['instruction_id_list']} kw={nn(r['kwargs'][j])}")
            print("    ", repr(snippet))


if __name__ == "__main__":
    main(sys.argv[1:])
