"""Grade content-free responses on every row (step 4): the empty text, repeated text, and a
restatement of the prompt (the row's own user message). Graders A, B (gate) and the replacement R.

Writes audit/out/content_free.json and prints, per response kind, the rows each grader passes and
the checks that pass most often.
"""
import collections
import json
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402

KINDS = {
    "empty": lambda row: "",
    "repeated": lambda row: " ".join(["the"] * 300),
    "restatement": lambda row: row["prompt"],
}


def main():
    random.seed(0)
    rows = gu.load_rows()
    out = {}
    for kind, make in KINDS.items():
        per_check = collections.defaultdict(lambda: collections.Counter())
        row_pass = collections.Counter()
        for row in rows:
            rec, text = row["record"], make(row)
            random.seed(0)
            a_reward, a_detail = gu.reward_a(text, rec)
            a_err = any(a_detail["instruction_errors"])
            b_pass, b_res = gu.gate_b(text, rec)
            r_reward, r_ver, _ = cg.grade_row(rec, text, row["prompt"], reasoning_model=False)
            row_pass["A_reward1"] += a_reward == 1.0
            row_pass["A_infra_error"] += a_err
            row_pass["B_gate_pass"] += b_pass
            row_pass["R_pass"] += r_reward == 1.0
            row_pass["rows"] += 1
            b_map = dict(b_res)
            for i, (iid, kw) in enumerate(zip(rec["instruction_id_list"], rec["kwargs"])):
                c = per_check[iid]
                c["n"] += 1
                c["A"] += a_detail["follow_instruction_list"][i] is True
                c["A_err"] += a_detail["instruction_errors"][i] is not None
                if iid in b_map:
                    c["B_n"] += 1
                    c["B"] += b_map[iid] is True
                c["R"] += r_ver[i] is True
        out[kind] = {"rows": dict(row_pass), "per_check": {k: dict(v) for k, v in sorted(per_check.items())}}
        print(f"== {kind}: rows {row_pass['rows']}, grader A reward 1.0 on {row_pass['A_reward1']} "
              f"(instruction errors on {row_pass['A_infra_error']}), grader B gate passes {row_pass['B_gate_pass']}, "
              f"replacement passes {row_pass['R_pass']}")
        for iid, c in sorted(per_check.items(), key=lambda kv: -max(kv[1]["A"], kv[1]["B"]) / kv[1]["n"]):
            if c["A"] or c["B"] or c["R"]:
                print(f"   {iid:<45} n={c['n']:4d} A={c['A']:4d} A_err={c['A_err']:4d} B={c['B']:4d}/{c['B_n']:4d} R={c['R']:4d}")
    (W / "audit" / "out" / "content_free.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
