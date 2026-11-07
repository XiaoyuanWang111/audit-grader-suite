"""Grade ToyMath responses against the reference answers.

Usage:
    python grade.py [--problems problems.jsonl] [--responses responses.jsonl] [--out verdicts.jsonl]

Prints one row per model. With --out, also writes one JSON verdict per response.
"""

import argparse
import json
import os
import re
from collections import defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))

ANSWER_LINE = re.compile(r"^\s*Answer:(.*)$")
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
TOLERANCE = Decimal("0.01")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def extract_answer(response):
    """Return the number on the last Answer: line as a Decimal, or None."""
    answer_line = None
    for line in response.splitlines():
        m = ANSWER_LINE.match(line)
        if m:
            answer_line = m.group(1)
    if answer_line is None:
        return None
    m = NUMBER.search(answer_line)
    if m is None:
        return None
    return Decimal(m.group(0))


def is_correct(answer, reference):
    return abs(answer - reference) <= TOLERANCE * max(Decimal(1), abs(reference))


def grade(problems, responses):
    references = {p["problem_id"]: Decimal(p["answer"]) for p in problems}
    rows = []
    for r in responses:
        answer = extract_answer(r["response"])
        if answer is None:
            verdict = "no_answer"
        elif is_correct(answer, references[r["problem_id"]]):
            verdict = "correct"
        else:
            verdict = "incorrect"
        rows.append({
            "id": r["id"],
            "model": r["model"],
            "problem_id": r["problem_id"],
            "extracted": None if answer is None else str(answer),
            "verdict": verdict,
        })
    return rows


def summarize(rows):
    counts = defaultdict(lambda: {"correct": 0, "incorrect": 0, "no_answer": 0})
    for row in rows:
        counts[row["model"]][row["verdict"]] += 1
    table = {}
    for model in sorted(counts):
        c = counts[model]
        graded = c["correct"] + c["incorrect"]
        score = 100.0 * c["correct"] / graded if graded else 0.0
        table[model] = dict(c, score=round(score, 1))
    return table


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade ToyMath responses.")
    ap.add_argument("--problems", default=os.path.join(HERE, "problems.jsonl"))
    ap.add_argument("--responses", default=os.path.join(HERE, "responses.jsonl"))
    ap.add_argument("--out", help="write one JSON verdict per response to this file")
    args = ap.parse_args(argv)

    rows = grade(load_jsonl(args.problems), load_jsonl(args.responses))
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    table = summarize(rows)
    print(f"{'model':<12}{'correct':>9}{'incorrect':>11}{'no_answer':>11}{'score':>8}")
    for model, c in table.items():
        print(f"{model:<12}{c['correct']:>9}{c['incorrect']:>11}{c['no_answer']:>11}{c['score']:>8.1f}")


if __name__ == "__main__":
    main()
