"""Which checks flip a row's reward under fixes only (grader's reading kept where allowed)?

For each run and grader, counts the rows gained (grader 0 -> fixes-only 1) and lost (1 -> 0), and
for each such row the checks whose verdict changed.
"""
import collections
import json
import os

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language",
            "letters:letter_counting"}


def fix(c, g):
    if c[g] != c["R"] and any(v == c[g] for v in c["R_alt"].values()):
        return c[g]
    return c["R"]


out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for line in open(os.path.join(AUDIT, "work", "panel_verdicts.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    for g in ("A", "B"):
        cons = [c for c in r["constraints"] if g == "A" or c["iid"] not in SEMANTIC]
        before = all(c[g] for c in cons)
        after = (not r["extraction_failure"]) and all(fix(c, g) for c in cons)
        if before == after:
            continue
        key = "gained" if after else "lost"
        if r["extraction_failure"]:
            out[(r["run"], g)][key]["F-G1 extraction failure"] += 1
            continue
        for c in cons:
            if fix(c, g) != c[g]:
                out[(r["run"], g)][key][c["iid"]] += 1
for (run, g), d in sorted(out.items()):
    print(f"== {run} grader {g}")
    for key in ("gained", "lost"):
        print(f"   {key}: " + ", ".join(f"{k.split(':')[-1]} {v}" for k, v in d[key].most_common(8)))
