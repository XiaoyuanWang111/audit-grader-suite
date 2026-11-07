"""Step 6.1-6.2: draw and freeze the round-1 review sample from the stored run.

Population: the 48 verdicts of the stored run. Strata: whether the grader under audit and the replacement give
different labels. Round 1 takes every case of both strata (10 disagreements, 38 agreements): the population is
small enough for one review batch, and a full agreement stratum gives each grader's error rate the narrowest
interval this run allows. A seeded shuffle assigns the opaque case ids and each reviewer's reading order.

Writes, under audit/frozen/:
- round1_cases.jsonl  the case list, shown to the batch renderer: case id, question id, sha256 of the response row
                      (as in audit/pins/rows.sha256). No model, no verdict.
- round1_keys.jsonl   the keys: each case's response id, source model, stratum and every grader's label.
- round1_draw.json    seed, script hash, stratum sizes, reviewer orders and the two files' sha256.

    python -I audit/scripts/draw_sample.py
"""

import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import CASE, ROOT, WORK, contract_parse, load_jsonl  # noqa: E402

SEED = 61106
FROZEN = ROOT / "audit" / "frozen"
PANEL = WORK / "panel"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rows = load_jsonl(CASE / "responses.jsonl")
    labels = {name: {d["id"]: d["label"] for d in load_jsonl(PANEL / f"{name}.labels.jsonl")}
              for name in ("grader", "reference", "replacement")}
    per_row = {d["id"]: d for d in load_jsonl(PANEL / "per_row.jsonl")}
    row_hash = {}
    for line in (ROOT / "audit" / "pins" / "rows.sha256").read_text(encoding="utf-8").splitlines():
        digest, ref = line.split(None, 1)
        if ref.startswith("responses.jsonl:"):
            row_hash[ref.rsplit(":", 1)[1]] = digest

    strata = {"disagree": [], "agree": []}
    for r in rows:
        key = "disagree" if labels["grader"][r["id"]] != labels["replacement"][r["id"]] else "agree"
        strata[key].append(r["id"])
    rng = random.Random(SEED)
    sample = {k: sorted(rng.sample(v, len(v))) for k, v in strata.items()}   # round 1: every case of each stratum
    chosen = sample["disagree"] + sample["agree"]
    rng.shuffle(chosen)
    case_of = {rid: f"T{i + 1:02d}" for i, rid in enumerate(chosen)}
    order_b = [case_of[rid] for rid in chosen]
    random.Random(SEED + 1).shuffle(order_b)

    by_id = {r["id"]: r for r in rows}
    FROZEN.mkdir(parents=True, exist_ok=True)
    cases_path, keys_path = FROZEN / "round1_cases.jsonl", FROZEN / "round1_keys.jsonl"
    with open(cases_path, "w", encoding="utf-8", newline="\n") as f:
        for rid in chosen:
            f.write(json.dumps({"case_id": case_of[rid], "question_id": by_id[rid]["question_id"],
                                "response_row_sha256": row_hash[rid]}) + "\n")
    with open(keys_path, "w", encoding="utf-8", newline="\n") as f:
        for rid in chosen:
            d = per_row[rid]
            f.write(json.dumps({
                "case_id": case_of[rid], "response_id": rid, "model": by_id[rid]["model"],
                "question_id": by_id[rid]["question_id"],
                "stratum": "disagree" if rid in strata["disagree"] else "agree",
                "label_grader": labels["grader"][rid], "label_reference": labels["reference"][rid],
                "label_replacement": labels["replacement"][rid],
                "judge_grade_call1": contract_parse(d["reply_call1"]) if d["reply_call1"] is not None else None,
                "judge_grade_call2": contract_parse(d["reply_call2"]) if d["reply_call2"] is not None else None,
            }) + "\n")
    draw = {
        "round": 1, "seed": SEED, "script": "audit/scripts/draw_sample.py",
        "script_sha256": sha256_file(Path(__file__)),
        "population": {k: len(v) for k, v in strata.items()},
        "sample": {k: len(v) for k, v in sample.items()},
        "stratified_by": "label of case/judge_pipeline.py != label of audit/replacement/toyqa_replacement.py",
        "reviewer_A_order": [case_of[rid] for rid in chosen],
        "reviewer_B_order": order_b,
        "round1_cases.jsonl_sha256": sha256_file(cases_path),
        "round1_keys.jsonl_sha256": sha256_file(keys_path),
        "inputs": {p: sha256_file(PANEL / p) for p in ("grader.labels.jsonl", "reference.labels.jsonl",
                                                        "replacement.labels.jsonl", "per_row.jsonl")},
    }
    draw_path = FROZEN / "round1_draw.json"
    draw_path.write_text(json.dumps(draw, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: draw[k] for k in ("population", "sample", "round1_cases.jsonl_sha256",
                                           "round1_keys.jsonl_sha256")}))
    print("round1_draw.json sha256", sha256_file(draw_path))


if __name__ == "__main__":
    main()
