"""Attribute each fuzz disagreement between the grader and the replacement (fixes only) to a finding.

Usage (from the audit run directory): python audit/scripts/fuzz_attribution.py
Re-grades audit/work/fuzz_cases.jsonl (written by stress.py) with both graders, writes audit/work/fuzz_verdicts.jsonl
and prints the count per cause. Causes, from the case's construction:
  F5 the grader raised; F3-tag the fence tag is py or empty; F3-first-block a usage block comes before the code block;
  F1 the function raises on every call or has another name.
"""

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import stress  # noqa: E402


def cause(case, g, fixes):
    if g.startswith("crash"):
        return "F5"
    if case["fence"] in ("py", "bare") and g == "fail" and fixes == "pass":
        return "F3-tag"
    if "Usage:" in case["response"] and g == "pass" and fixes == "fail":
        return "F3-first-block"
    if case["body"] in ("raises", "wrong_name") and g == "pass" and fixes == "fail":
        return "F1"
    return "unexplained"


def main():
    with open(os.path.join(ROOT, "audit", "work", "fuzz_cases.jsonl"), encoding="utf-8") as f:
        cases = [json.loads(l) for l in f if l.strip()]
    counts = collections.Counter()
    out = []
    for c in cases:
        g = stress.verdict("grader", c["task_id"], c["response"])
        fixes = stress.verdict("replacement", c["task_id"], c["response"], stress.FIXES_ONLY)
        why = cause(c, g, fixes) if g != fixes else "agree"
        counts[why] += 1
        out.append({"index": c["index"], "task_id": c["task_id"], "body": c["body"], "fence": c["fence"],
                    "crlf": c["crlf"], "grader": g, "fixes_only": fixes, "cause": why})
    with open(os.path.join(ROOT, "audit", "work", "fuzz_verdicts.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for row in out:
            f.write(json.dumps(row) + "\n")
    print(dict(counts))
    for row in out:
        if row["cause"] == "unexplained":
            print("unexplained:", row)


if __name__ == "__main__":
    main()
