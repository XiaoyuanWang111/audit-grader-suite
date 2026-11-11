"""Step 4: content-free responses on every row.

Responses: empty text; one word repeated ("data " x 300); the row's requirement text restated
(the prompt's text after its requirement-list header, or the whole prompt when no header is
found); a single period.
For each response and grader (SkyRL, curation gate, replacement under proposed readings), count
per check how many constraints pass, and how many rows get full reward / pass the gate.

Writes audit/out/step4_content_free.json and prints a summary.
"""
import collections
import json
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402

HEADERS = re.compile(
    r"(Please follow these instructions in your response:|When answering, please adhere to these constraints:|"
    r"Make sure to follow these requirements when responding:|Your response should comply with these constraints:|"
    r"Your response should satisfy these conditions:|Make sure to adhere to these requirements:|"
    r"Please ensure your response follows these guidelines:|Please ensure your answer follows these guidelines:|"
    r"Make sure your response satisfies these conditions:|Please follow these rules when answering:|"
    r"[A-Z][^\n:]{10,80} these (?:requirements|constraints|conditions|guidelines|rules|instructions)[^\n:]*:)"
)


def restatement(prompt: str) -> str:
    m = HEADERS.search(prompt)
    return prompt[m.end():].strip() if m else prompt


def main():
    rows = harness.load_rows()
    kinds = ["empty", "repeat", "restate", "period"]
    per_check = {k: {g: collections.Counter() for g in ("skyrl", "gate", "repl")} for k in kinds}
    totals = collections.Counter()
    full = {k: collections.Counter() for k in kinds}
    examples = {}
    for row in rows:
        rec = harness.record_of(row)
        prompt = row["prompt"][0]["content"]
        texts = {"empty": "", "repeat": "data " * 300, "restate": restatement(prompt), "period": "."}
        for iid in rec["instruction_id_list"]:
            totals[iid] += 1
        for kind, text in texts.items():
            reward, sk, errs, _ = harness.skyrl_grade(text, rec, extract=False)
            gate, gv, _ = harness.curation_gate(text, rec, extract=False)
            rr, rv = rp.grade_row(text, rec, prompt=prompt)
            for iid, a, b, c in zip(rec["instruction_id_list"], sk, gv, rv):
                per_check[kind]["skyrl"][iid] += bool(a)
                if b is not None:
                    per_check[kind]["gate"][iid] += bool(b)
                per_check[kind]["repl"][iid] += bool(c)
            full[kind]["skyrl_reward_1"] += reward == 1.0
            full[kind]["skyrl_reward_1_no_error"] += reward == 1.0 and not any(errs)
            full[kind]["gate_passed"] += gate
            full[kind]["repl_reward_1"] += rr == 1.0
            full[kind]["skyrl_any_error"] += any(e is not None for e in errs)
            if kind == "empty" and reward == 1.0 and "empty" not in examples:
                examples["empty"] = rec["uuid"]
            if kind == "restate" and reward == 1.0 and "restate" not in examples:
                examples["restate"] = rec["uuid"]
    out = {"rows": len(rows), "totals": totals, "full": full, "per_check": per_check, "examples": examples}
    (W / "audit" / "out" / "step4_content_free.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("rows", len(rows))
    for kind in kinds:
        print(f"\n== {kind}: rows with SkyRL reward 1.0: {full[kind]['skyrl_reward_1']} "
              f"(of which checker errors: {full[kind]['skyrl_reward_1'] - full[kind]['skyrl_reward_1_no_error']}); "
              f"gate passed: {full[kind]['gate_passed']}; replacement reward 1.0: {full[kind]['repl_reward_1']}; "
              f"rows with a SkyRL checker exception: {full[kind]['skyrl_any_error']}")
        for iid in sorted(totals):
            s, g, r = per_check[kind]["skyrl"][iid], per_check[kind]["gate"][iid], per_check[kind]["repl"][iid]
            if s or g or r:
                gs = "-" if iid in harness.SEMANTIC else f"{g}"
                print(f"   {iid}: n={totals[iid]} skyrl_pass={s} gate_pass={gs} replacement_pass={r}")
    print("examples", examples)


if __name__ == "__main__":
    main()
