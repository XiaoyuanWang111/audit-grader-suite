"""Write the minimal reproduction inputs under audit/repro/ (one JSONL per finding).

Run from W:  python -B audit/scripts/make_repro.py
Each file is a response file in the format TASK.md gives (id, model, problem_id, response).
"""
import json
import pathlib

W = pathlib.Path(__file__).resolve().parents[2]
REPRO = W / "audit" / "repro"

REFS = {}
for line in (W / "case" / "problems.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        p = json.loads(line)
        REFS[p["problem_id"]] = p["answer"]
PIDS = sorted(REFS)


def row(i, model, pid, response):
    return {"id": i, "model": model, "problem_id": pid, "response": response}


FILES = {
    "F1_commas.jsonl": [row("F1-a", "m1", "p03", "Answer: 2,250"),
                        row("F1-b", "m1", "p07", "Answer: 15,000")],
    "F2_tolerance.jsonl": [row("F2-a", "m1", "p07", "Answer: 15100"),
                           row("F2-b", "m1", "p09", "Answer: 29")],
    "F3_denominator.jsonl": (
        [row("F3-a01", "abstainer", "p01", "Answer: 3.5")]
        + [row(f"F3-a{k:02d}", "abstainer", pid, "I am not sure how to solve this.")
           for k, pid in enumerate(PIDS[1:], start=2)]
        + [row(f"F3-b{k:02d}", "partial", pid, f"Answer: {REFS[pid]}")
           for k, pid in enumerate(PIDS[:11], start=1)]),
    "F4_precision.jsonl": [row("F4-a", "m1", "p06", "Answer: 0.010000000000000000000000000001")],
    "F5_unknown_problem.jsonl": [row("F5-a", "m1", "p01", "Answer: 3.5"),
                                 row("F5-b", "m1", "p13", "Answer: 1")],
    "F5_null_response.jsonl": [row("F5-c", "m1", "p01", "Answer: 3.5"),
                               row("F5-d", "m1", "p02", None)],
    "F6_duplicate.jsonl": ([row(f"F6-{k:02d}", "dup", pid, f"Answer: {REFS[pid]}") for k, pid in enumerate(PIDS, start=1)]
                           + [row("F6-13", "dup", "p01", "Answer: 3.5")]),
    "R1_double_comma.jsonl": [row("R1-a", "m1", "p02", "Answer: 4,,86")],
    "decisions.jsonl": [
        row("D-leading-whitespace", "d1", "p05", "\u00a0Answer: 72"),
        row("D-digits", "d2", "p05", "Answer: \uff17\uff12"),
        row("D-surrounding-text", "d3", "p01", "Answer: $3.50"),
        row("D-multiple-numbers", "d4", "p01", "Answer: 6 muffins cost 16.50, so 3.50"),
        row("D-tolerance-boundary", "d5", "p06", "Answer: 0.01"),
        row("D-no-number-label", "d6", "p02", "Answer: unknown"),
    ],
}


def main():
    REPRO.mkdir(parents=True, exist_ok=True)
    (REPRO / "out").mkdir(exist_ok=True)
    for name, rows in FILES.items():
        with open(REPRO / name, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")
        print(f"wrote audit/repro/{name} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
