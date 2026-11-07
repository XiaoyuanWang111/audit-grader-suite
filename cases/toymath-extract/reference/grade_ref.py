"""ToyMath reference grader, as released by the benchmark authors (toymath 1.0).

Usage:
    python grade_ref.py PROBLEMS_JSONL RESPONSES_JSONL [VERDICTS_OUT_JSONL]
"""

import json
import re
import sys
from decimal import Decimal

PREFIX = "Answer:"
NUMBER = re.compile(r"-?\d+(\.\d+)?")


def read_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def final_answer(text):
    finals = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(PREFIX):
            finals.append(line[len(PREFIX):].strip())
    if not finals:
        return None
    value = finals[-1].replace(",", "")
    if NUMBER.fullmatch(value) is None:
        return None
    return Decimal(value)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    problems = read_jsonl(sys.argv[1])
    responses = read_jsonl(sys.argv[2])
    gold = {p["problem_id"]: Decimal(p["answer"]) for p in problems}

    verdicts = []
    for r in responses:
        answer = final_answer(r["response"])
        ok = answer is not None and abs(answer - gold[r["problem_id"]]) <= Decimal("0.01")
        verdicts.append({"id": r["id"], "model": r["model"], "problem_id": r["problem_id"],
                         "answer": None if answer is None else str(answer),
                         "verdict": "correct" if ok else "incorrect"})

    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
            for v in verdicts:
                f.write(json.dumps(v) + "\n")

    models = sorted({v["model"] for v in verdicts})
    print("model        correct  of  score")
    for m in models:
        n_correct = sum(1 for v in verdicts if v["model"] == m and v["verdict"] == "correct")
        print(f"{m:<12} {n_correct:>7} {len(problems):>3} {100.0 * n_correct / len(problems):>6.1f}")


if __name__ == "__main__":
    main()
