"""Post-label: print short excerpts of disagreements that no decision reading explains, for one check.

Reads audit/work/regrade_disagreements.jsonl (class "none") and prints, for non-held-out runs only
(so that held-out responses stay unused for a later review round), the grader and replacement
verdicts and the first characters of the response as a Python literal.
Run from W:
  .venv/Scripts/python.exe -B audit/scripts/show_residuals.py <check> [max_rows] [chars] [pass|fail] [key]
The optional pass or fail keeps only rows with that grader verdict; key keeps one dataset prompt.
"""
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    iid = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    chars = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    want = {"pass": True, "fail": False}.get(sys.argv[4]) if len(sys.argv) > 4 else None
    key = sys.argv[5] if len(sys.argv) > 5 else None
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows = [json.loads(l) for l in open(os.path.join(W, "audit", "work", "regrade_disagreements.jsonl"), encoding="utf-8")]
    rows = [r for r in rows if r["iid"] == iid and r["class"] == "none" and not r["heldout"]
            and (want is None or r["g"] == want) and (key is None or r["key"] == key)]
    print(f"{iid}: {len(rows)} unexplained disagreements in non-held-out runs")
    for r in rows[:k]:
        with open(os.path.join(W, "case", "panel", r["cfg"], r["run"] + ".jsonl"), encoding="utf-8") as fh:
            rec = next(x for x in map(json.loads, fh) if str(x["key"]) == r["key"])
        resp = rec["response"]
        print(f"- {r['cfg']}/{r['run']} key {r['key']} j {r['j']}: grader {r['g']}, replacement {r['p']}, {len(resp)} chars")
        print(f"  {resp[:chars]!r}")


if __name__ == "__main__":
    main()
