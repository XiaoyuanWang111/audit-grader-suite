"""Behaviour the task text does not specify (contract, end of section G): report it, assert nothing.

Each probe runs every pipeline's CLI on a small response file with the fake judge, or with the recorded judge for
the unrecorded-prompt probe, and prints the exit status and the model's printed accuracy.

    python -I audit/scripts/unspecified.py
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import CASE, ROOT, WORK  # noqa: E402

TMP = WORK / "unspecified"
PY = [sys.executable, "-I"]

PROBES = {
    "duplicate_row": ([("d01", "q01", "Canberra"), ("d02", "q01", "Canberra")] +
                      [(f"d{i:02d}", f"q{i - 1:02d}", "x") for i in range(3, 14)], "fake"),
    "unknown_question_id": ([("u01", "q01", "Canberra"), ("u02", "q99", "Canberra")], "fake"),
    "null_response": ([("n01", "q01", "Canberra"), ("n02", "q02", None)], "fake"),
    "unrecorded_prompt": ([("r01", "q01", "Canberra."), ("r02", "q01", "Canberra, of course.")], "recorded"),
}


def commands(responses, out, judge):
    return {
        "grader": PY + [str(CASE / "judge_pipeline.py"), "--judge", judge, "--responses", str(responses),
                        "--out", str(out)],
        "reference": PY + [str(CASE / "reference" / "pipeline_ref.py"), str(CASE / "questions.jsonl"),
                           str(responses), judge, str(out)],
        "replacement": PY + [str(ROOT / "audit" / "replacement" / "toyqa_replacement.py"), "--judge", judge,
                             "--responses", str(responses), "--out", str(out)],
    }


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    for name, (rows, judge) in PROBES.items():
        path = TMP / f"{name}.jsonl"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for rid, qid, text in rows:
                f.write(json.dumps({"id": rid, "model": "m", "question_id": qid, "response": text}) + "\n")
        for impl, cmd in commands(path, TMP / f"{name}.{judge}.out.jsonl", judge).items():
            p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
            lines = [l.split() for l in p.stdout.splitlines() if l.strip()]
            acc = None
            if len(lines) >= 2:
                header = lines[0][1:]
                acc = dict(zip(header, lines[1][1:])).get("accuracy")
            err = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
            print(f"{name:<20} {impl:<12} exit {p.returncode}  accuracy {acc}  {err[:70]}")


if __name__ == "__main__":
    main()
