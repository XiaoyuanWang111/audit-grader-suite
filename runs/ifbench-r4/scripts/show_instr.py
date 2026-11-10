"""Print, for given instruction ids, each prompt's tail and the non-null kwargs.

Usage: python audit/scripts/show_instr.py [--tail N] id1 id2 ...
   or: python audit/scripts/show_instr.py --row R   (one full prompt)
"""
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]


def nn(kw):
    return {k: v for k, v in kw.items() if v is not None}


def main(argv):
    tail = 300
    if argv and argv[0] == "--tail":
        tail = int(argv[1])
        argv = argv[2:]
    if argv and argv[0] == "--row":
        r = ROWS[int(argv[1])]
        print(repr(r["prompt"]))
        print(r["instruction_id_list"], [nn(k) for k in r["kwargs"]])
        return
    for iid in argv:
        print("=" * 20, iid)
        for i, r in enumerate(ROWS):
            if iid in r["instruction_id_list"]:
                j = r["instruction_id_list"].index(iid)
                p = r["prompt"]
                print(f"--- row {i} ids={r['instruction_id_list']} kw={nn(r['kwargs'][j])}")
                print("   ...", repr(p[-tail:]))


if __name__ == "__main__":
    main(sys.argv[1:])
