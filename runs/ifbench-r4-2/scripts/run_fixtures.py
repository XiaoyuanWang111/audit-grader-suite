"""Run every fixture against the grader, the reference and (if present) the
replacement; print a table and write audit/out/fixture_results.tsv."""
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "tests"))
sys.path.insert(0, str(W / "audit" / "replacement"))
import harness as H  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

try:
    import ifbench_fixed as RF  # noqa: E402
except ImportError:
    RF = None

checks = set()
rows = []
for f in FIXTURES:
    checks.add(f["check"])
    g = H.check_one(f["check"], f["kwargs"], f["response"], which="grader", prompt=f["prompt"])
    r = H.check_one(f["check"], f["kwargs"], f["response"], which="reference", prompt=f["prompt"])
    if RF is not None:
        try:
            x = RF.check(f["check"], f["kwargs"], f["response"], prompt=f["prompt"] or "PROMPT", opts=RF.FIX)
            p = RF.check(f["check"], f["kwargs"], f["response"], prompt=f["prompt"] or "PROMPT", opts=RF.PROPOSED)
        except Exception as e:  # noqa: BLE001
            x = p = "EXC:" + type(e).__name__
    else:
        x = p = "-"
    rows.append((f["id"], f["label"], g, r, x, p, ",".join(f["dec"]), f["finding"] or "", f["note"]))

with open(W / "audit" / "out" / "fixture_results.tsv", "w", newline="\n", encoding="utf-8") as fh:
    fh.write("id\tlabel\tgrader\treference\trepl_fix\trepl_proposed\tdec\tfinding\tnote\n")
    for row in rows:
        fh.write("\t".join(str(c) for c in row) + "\n")

n = len(rows)
gw = [r for r in rows if r[2] != r[1]]
print(f"fixtures={n} checks_covered={len(checks)}")
print(f"grader_wrong={len(gw)} (unambiguous {sum(1 for r in gw if not r[6])}, decision {sum(1 for r in gw if r[6])})")
print(f"reference_wrong={sum(1 for r in rows if r[3] != r[1])}")
if RF is not None:
    print(f"repl_proposed_wrong={sum(1 for r in rows if r[5] != r[1])}")
    print(f"repl_fix_wrong_unambiguous={sum(1 for r in rows if r[4] != r[1] and not r[6])}")
for r in rows:
    flag = []
    if r[2] != r[1]:
        flag.append("G")
    if r[3] != r[1]:
        flag.append("R")
    if RF is not None and r[5] != r[1]:
        flag.append("P")
    if RF is not None and r[4] != r[1] and not r[6]:
        flag.append("X")
    if flag:
        print(f"{''.join(flag):4s} {r[0]:45s} label={r[1]!s:5s} g={r[2]!s:5s} r={r[3]!s:5s} fix={r[4]!s:5s} prop={r[5]!s:5s} dec={r[6]} {r[7]}")
