"""Regenerate audit/tests/known_wrong.py from audit/out/fixture_results.tsv
(run audit/scripts/run_fixtures.py first)."""
import csv
from pathlib import Path

W = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(W / "audit/out/fixture_results.tsv", encoding="utf-8"), delimiter="\t"))
sets = {
    "GRADER": sorted(r["id"] for r in rows if r["grader"] != r["label"]),
    "REFERENCE": sorted(r["id"] for r in rows if r["reference"] != r["label"]),
    "REPL_PROPOSED": sorted(r["id"] for r in rows if r["repl_proposed"] != r["label"]),
    "REPL_FIX": sorted(r["id"] for r in rows if r["repl_fix"] != r["label"]),
}
with open(W / "audit/tests/known_wrong.py", "w", newline="\n", encoding="utf-8") as fh:
    fh.write('"""Fixture ids each implementation currently gets wrong (from audit/scripts/run_fixtures.py).\n'
             'A fix must remove the id; the tests use xfail(strict=True)."""\n')
    for k, v in sets.items():
        fh.write(f"{k} = {v!r}\n")
print({k: len(v) for k, v in sets.items()})
