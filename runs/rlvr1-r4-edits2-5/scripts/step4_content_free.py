"""Step 4 content-free responses: empty text, repeated text, and a restatement of the instructions.

1. Every one of the 11,817 rows is graded with the three responses by grader A (SkyRL row reward,
   through final_answer_text), grader B (task-curation gate) and the replacement. Per-check pass
   counts and row-level outcomes go to audit/work/content_free_summary.json.
2. One fixture per check and response kind (first row of each check) goes to
   audit/work/content_free_fixtures.jsonl, labeled by the contract (replacement, proposed readings).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
import graders as g  # noqa: E402

cg = fl.cg
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT = W / "audit" / "work" / "content_free_summary.json"
OUT_FX = W / "audit" / "work" / "content_free_fixtures.jsonl"
REPEATED = " ".join(["Hello world."] * 40)


def responses(rec):
    return {"empty": "", "repeated": REPEATED, "restatement": rec["prompt"]}


def main():
    per_check = collections.defaultdict(collections.Counter)
    rows = collections.Counter()
    examples = {}
    fixtures = {}
    for line in DATA.open(encoding="utf-8"):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        for kind, resp in responses(rec).items():
            a = g.skyrl_row(resp, rec)
            b = g.curation_row(resp, rec)
            r_text = cg.graded_text(resp, False)
            r = [cg.grade_constraint(i, k, r_text) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
            for idx, iid in enumerate(rec["instruction_id_list"]):
                c = per_check[(kind, iid)]
                c["n"] += 1
                c["skyrl_pass"] += bool(a["verdicts"][idx]) and not a["errors"][idx]
                c["skyrl_error"] += bool(a["errors"][idx])
                if b["verdicts"][idx] is not None:
                    c["curation_n"] += 1
                    c["curation_pass"] += bool(b["verdicts"][idx])
                c["replacement_pass"] += r[idx]
                key = (kind, iid)
                if key not in fixtures and kind != "restatement":
                    fixtures[key] = {"source": "content_free", "instruction_id": iid, "kwargs": rec["instruction_id_list"] and rec["kwargs"][idx],
                                     "response": resp, "label": "pass" if r[idx] else "fail",
                                     "note": f"content-free {kind}", "reasoning_model": False}
                if key not in fixtures and kind == "restatement":
                    # restate only this requirement: the prompt text is long; keep the whole prompt
                    fixtures[key] = {"source": "content_free", "instruction_id": iid, "kwargs": rec["kwargs"][idx],
                                     "response": resp, "label": "pass" if r[idx] else "fail",
                                     "note": "content-free restatement (the whole prompt)", "reasoning_model": False}
            rows[(kind, "rows")] += 1
            rows[(kind, "skyrl_reward_1")] += a["reward"] == 1.0
            rows[(kind, "skyrl_infra_error")] += a["infra_error"]
            if b["has_gate"]:
                rows[(kind, "gate_rows")] += 1
                rows[(kind, "gate_passed_to_judge")] += b["gate_passed"]
            else:
                rows[(kind, "no_gate_rows_judge_only")] += 1
            rows[(kind, "replacement_reward_1")] += all(r)
            if a["reward"] == 1.0 and (kind, "skyrl") not in examples:
                examples[(kind, "skyrl")] = rec["uuid"]
            if b["has_gate"] and b["gate_passed"] and (kind, "curation") not in examples:
                examples[(kind, "curation")] = rec["uuid"]
    summary = {
        "rows": {f"{k}|{m}": v for (k, m), v in sorted(rows.items())},
        "per_check": {f"{k}|{i}": dict(c) for (k, i), c in sorted(per_check.items())},
        "example_uuids": {f"{k}|{m}": v for (k, m), v in examples.items()},
        "repeated_text": REPEATED[:40] + "...",
    }
    OUT.write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
    with OUT_FX.open("w", encoding="utf-8", newline="\n") as f:
        for fx in fixtures.values():
            f.write(json.dumps(fx, ensure_ascii=False) + "\n")
    for k, v in sorted(rows.items()):
        print(k, v)


if __name__ == "__main__":
    main()
