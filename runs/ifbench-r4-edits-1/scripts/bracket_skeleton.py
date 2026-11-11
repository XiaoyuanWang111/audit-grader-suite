"""Print the bracket skeleton of one panel response and its deepest properly closed group.

Usage: python audit/scripts/bracket_skeleton.py <folder> <run> <key>
"""
import json
import sys

import common

folder, run, key = sys.argv[1:4]
order = common.row_list()
rec = json.loads((common.CASE / "panel" / folder / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()[order.index(key)])
t = rec["response"]
sk = "".join(c for c in t if c in "()[]{}")
print("skeleton:", sk[:300])
pairs = {")": "(", "]": "[", "}": "{"}
stack, best, maxopen = [], 0, 0
for c in t:
    if c in "([{":
        stack.append([c, 0])
        maxopen = max(maxopen, len(stack))
    elif c in pairs:
        if stack and stack[-1][0] == pairs[c]:
            _, inner = stack.pop()
            best = max(best, inner + 1)
            if stack:
                stack[-1][1] = max(stack[-1][1], inner + 1)
        else:
            stack = []
print("max open depth", maxopen, "deepest properly closed group", best)
