"""Print the first 70 characters of each line of one panel response (graded text).

Usage: python audit/scripts/show_lines.py <folder> <run> <key> [max_lines]
"""
import json
import sys

import common

folder, run, key = sys.argv[1], sys.argv[2], sys.argv[3]
mx = int(sys.argv[4]) if len(sys.argv) > 4 else 40
order = common.row_list()
rec = json.loads((common.CASE / "panel" / folder / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()[order.index(key)])
lines = rec["response"].split("\n")
print(f"{len(lines)} lines, {len(rec['response'])} chars, finish_reason={rec['finish_reason']}")
for i, ln in enumerate(lines[:mx]):
    print(f"{i:>3}: {ascii(ln[:70])}")
