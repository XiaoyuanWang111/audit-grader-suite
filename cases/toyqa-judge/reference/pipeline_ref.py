"""ToyQA reference pipeline, as released by the benchmark authors (toyqa 1.0).

Usage:
    python pipeline_ref.py QUESTIONS_JSONL RESPONSES_JSONL [recorded|fake] [LABELS_OUT_JSONL]

Uses the same judge back ends as the evaluation (../judges.py).
"""

import json
import os
import re
import sys

CASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CASE_DIR)

from judges import FakeJudge, RecordedJudge  # noqa: E402

THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
CUT = 300
TRIES = 2
STANDALONE_GRADE = re.compile(r"(?<![A-Za-z0-9])([ABC])(?![A-Za-z0-9])")
GRADE_LABEL = {"A": "correct", "B": "incorrect", "C": "not_attempted"}


class ToyQAGrader:
    def __init__(self, judge, template):
        self.judge = judge
        self.template = template

    @staticmethod
    def answer_text(response):
        if THINK_CLOSE in response:
            return response.split(THINK_CLOSE)[-1].strip()
        if THINK_OPEN in response:
            return None
        return response.strip()

    def prompt(self, q, answer):
        target = q["gold"]
        if q["aliases"]:
            target = f"{target} (also accepted: {', '.join(q['aliases'])})"
        return self.template.format(question=q["question"], target=target, predicted_answer=answer[:CUT])

    @staticmethod
    def grade_of(reply):
        found = STANDALONE_GRADE.findall(reply)
        return found[-1] if found else None

    def label(self, q, response):
        answer = self.answer_text(response)
        if answer is None:
            return "extraction_failure"
        prompt = self.prompt(q, answer)
        for call in range(1, TRIES + 1):
            grade = self.grade_of(self.judge(prompt, call))
            if grade:
                return GRADE_LABEL[grade]
        return "judge_error"


def metrics(labels, n):
    correct = labels.count("correct")
    attempted = correct + labels.count("incorrect")
    acc = correct / n
    cga = correct / attempted if attempted else 0.0
    f = 2 * acc * cga / (acc + cga) if acc + cga else 0.0
    return acc, cga, f, labels.count("not_attempted") / n


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    with open(argv[0], encoding="utf-8") as fh:
        questions = {q["question_id"]: q for q in (json.loads(l) for l in fh if l.strip())}
    with open(argv[1], encoding="utf-8") as fh:
        responses = [json.loads(l) for l in fh if l.strip()]
    judge = FakeJudge() if len(argv) > 2 and argv[2] == "fake" else RecordedJudge()
    with open(os.path.join(CASE_DIR, "judge_template.txt"), encoding="utf-8") as fh:
        grader = ToyQAGrader(judge, fh.read())

    out = [{"id": r["id"], "model": r["model"], "question_id": r["question_id"],
            "label": grader.label(questions[r["question_id"]], r["response"])} for r in responses]

    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8", newline="\n") as fh:
            for o in out:
                fh.write(json.dumps(o) + "\n")

    print("model            accuracy    cga  f_score  not_att_%  extr_fail  judge_err")
    for m in sorted({o["model"] for o in out}):
        labels = [o["label"] for o in out if o["model"] == m]
        acc, cga, f, na = metrics(labels, len(questions))
        print(f"{m:<16} {100 * acc:8.1f} {100 * cga:6.1f} {100 * f:8.1f} {100 * na:10.1f} "
              f"{labels.count('extraction_failure'):10d} {labels.count('judge_error'):10d}")


if __name__ == "__main__":
    main(sys.argv[1:])
