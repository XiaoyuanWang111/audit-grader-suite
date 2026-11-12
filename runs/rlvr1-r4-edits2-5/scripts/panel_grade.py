"""Step 5: grade every stored panel response with grader A (SkyRL), grader B (task-curation gate)
and the replacement (proposed readings). Writes audit/work/panel_verdicts.jsonl, one line per
response: run file, uuid, row index, finish reason, extraction flags, and per-constraint verdicts.

Usage: python panel_grade.py [limit_per_file]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
import graders as g  # noqa: E402

cg = fl.cg
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
PANEL = W / "case" / "panel"
OUT = W / "audit" / "work" / "panel_verdicts.jsonl"
MARKERS = ("<think>", "<thinking>", "<|start_think|>")


def load_rows():
    rows = {}
    for idx, line in enumerate(DATA.open(encoding="utf-8")):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        rows[rec["uuid"]] = (idx, rec)
    return rows


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = load_rows()
    files = sorted(PANEL.glob("*/*.jsonl"))
    start = time.time()
    with OUT.open("w", encoding="utf-8", newline="\n") as out:
        for path in files:
            folder = path.parent.name
            reasoning = folder.endswith("__thinking")
            for n, line in enumerate(path.open(encoding="utf-8")):
                if limit is not None and n >= limit:
                    break
                resp = json.loads(line)
                idx, rec = rows[resp["uuid"]]
                raw = resp["raw_response"]
                a = g.skyrl_row(raw, rec)
                b = g.curation_row(raw, rec)
                r_text = cg.graded_text(raw, reasoning)
                r = [cg.grade_constraint(i, k, r_text) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
                out.write(json.dumps({
                    "file": f"{folder}/{path.name}", "n": n, "uuid": resp["uuid"], "row": idx,
                    "finish": resp["finish_reason"], "reasoning": reasoning,
                    "extraction_failure": r_text is None,
                    "literal_marker": (not reasoning) and any(m in raw for m in MARKERS),
                    "a_text_empty": not a["text"].strip(), "r_text_empty": r_text is not None and not r_text.strip(),
                    "ids": rec["instruction_id_list"],
                    "A": [bool(v) for v in a["verdicts"]], "A_err": [e for e in a["errors"]],
                    "A_reward": a["reward"], "A_infra": a["infra_error"],
                    "B": b["verdicts"], "B_err": b["errors"], "B_gate": b["gate_passed"], "B_has_gate": b["has_gate"],
                    "R": r,
                }) + "\n")
            print(f"{path.parent.name}/{path.name} done at {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
