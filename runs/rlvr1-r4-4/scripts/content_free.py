"""Step 4: grade content-free responses on all 11,817 rows with A, B and R.

Responses: the empty string, a repeated token ("ok " x 50), and a restatement of the instructions
(the row's own prompt). Prints, per response kind, the rows that each grader rewards and the share
of each check's constraints that pass. Writes audit/work/content_free.json.
"""
import collections
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
import harness as H  # noqa: E402

rows = H.load_rows()
kinds = {"empty": lambda rec: "", "repeated": lambda rec: ("ok " * 50).strip(), "restatement": lambda rec: rec["prompt"]}
res = {}
for kind, make in kinds.items():
    row_pass = collections.Counter()
    check_pass = collections.defaultdict(collections.Counter)
    errors = collections.Counter()
    for uuid, rec in rows.items():
        text = make(rec)
        random.seed(0)
        a_all = b_all = r_all = True
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            a, err = H.a_check(iid, kw, H.extract_a(text))
            b, _ = H.b_check(iid, kw, H.extract_b(text))
            r = H.r_check(iid, kw, text)
            if err:
                errors[(iid, err.split(":")[0])] += 1
            check_pass[iid]["n"] += 1
            check_pass[iid]["A"] += a
            check_pass[iid]["B"] += b
            check_pass[iid]["R"] += r
            a_all &= a
            r_all &= r
            if iid not in H.SEMANTIC:
                b_all &= b
        row_pass["A"] += a_all
        row_pass["B"] += b_all
        row_pass["R"] += r_all
    res[kind] = {"rows": len(rows), "rows_rewarded": dict(row_pass),
                 "checks": {k: dict(v) for k, v in check_pass.items()},
                 "errors": {f"{k[0]}|{k[1]}": v for k, v in errors.items()}}
    print(f"== {kind}: rows rewarded A={row_pass['A']} B(gate)={row_pass['B']} R={row_pass['R']} of {len(rows)}; errors {dict(errors)}")
    for iid, c in sorted(check_pass.items()):
        if c["A"] or c["B"] or c["R"]:
            print(f"   {iid:<46} n={c['n']:>4} A={c['A']:>4} B={c['B']:>4} R={c['R']:>4}")
with open(os.path.join(AUDIT, "work", "content_free.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1)
