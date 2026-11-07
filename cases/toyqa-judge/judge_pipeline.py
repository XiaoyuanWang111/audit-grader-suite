"""ToyQA judge pipeline: graded-text extraction, judge-prompt rendering, the judge call, reply parsing, label
mapping and aggregation.

Usage:
    python judge_pipeline.py [--judge recorded|fake] [--questions questions.jsonl] [--responses responses.jsonl]
                             [--out labels.jsonl]

Prints one row per model; with --out, also writes one JSON line per response.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from judges import FakeJudge, RecordedJudge, prompt_sha256  # noqa: E402

MAX_PREDICTED_CHARS = 300
MAX_CALLS = 2
LETTER = re.compile(r"[ABC]")
LABEL_OF_GRADE = {"A": "correct", "B": "incorrect", "C": "not_attempted"}
LABELS = ("correct", "incorrect", "not_attempted", "extraction_failure", "judge_error")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_template(path=os.path.join(HERE, "judge_template.txt")):
    with open(path, encoding="utf-8") as f:
        return f.read()


def extract_graded_text(response):
    """Return the text to grade, or None when the response's reasoning never closed."""
    if "<think>" in response and "</think>" not in response:
        return None
    if "</think>" in response:
        response = response.rsplit("</think>", 1)[1]
    return response.strip()


def format_target(question):
    target = question["gold"]
    if question.get("aliases"):
        target += " (also accepted: " + ", ".join(question["aliases"]) + ")"
    return target


def render_prompt(template, question, graded_text):
    predicted = graded_text.splitlines()[0][:MAX_PREDICTED_CHARS]
    return template.format(question=question["question"], target=format_target(question),
                           predicted_answer=predicted)


def parse_grade(reply):
    m = LETTER.search(reply)
    return m.group(0) if m else None


def call_judge(judge, prompt):
    replies = []
    for call in range(1, MAX_CALLS + 1):
        reply = judge(prompt, call)
        replies.append(reply)
        grade = parse_grade(reply)
        if grade is not None:
            return grade, replies
    return None, replies


def grade_response(judge, template, question, response):
    graded = extract_graded_text(response)
    if graded is None:
        return {"label": "not_attempted", "grade": None, "judge_calls": 0, "prompt_sha256": None}
    prompt = render_prompt(template, question, graded)
    grade, replies = call_judge(judge, prompt)
    label = LABEL_OF_GRADE[grade] if grade is not None else "judge_error"
    return {"label": label, "grade": grade, "judge_calls": len(replies), "prompt_sha256": prompt_sha256(prompt)}


def aggregate(rows, n_questions):
    table = {}
    for model in sorted({r["model"] for r in rows}):
        c = Counter(r["label"] for r in rows if r["model"] == model)
        accuracy = c["correct"] / n_questions
        attempted = c["correct"] + c["incorrect"]
        cga = c["correct"] / attempted if attempted else 0.0
        f = 2 * accuracy * cga / (accuracy + cga) if accuracy + cga else 0.0
        table[model] = {**{label: c[label] for label in LABELS},
                        "accuracy": round(100 * accuracy, 1),
                        "correct_given_attempted": round(100 * cga, 1),
                        "f_score": round(100 * f, 1),
                        "not_attempted_rate": round(100 * c["not_attempted"] / n_questions, 1)}
    return table


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the ToyQA judge pipeline.")
    ap.add_argument("--judge", choices=["recorded", "fake"], default="recorded")
    ap.add_argument("--questions", default=os.path.join(HERE, "questions.jsonl"))
    ap.add_argument("--responses", default=os.path.join(HERE, "responses.jsonl"))
    ap.add_argument("--replies", default=os.path.join(HERE, "judge_replies.jsonl"))
    ap.add_argument("--out", help="write one JSON line per response to this file")
    args = ap.parse_args(argv)

    judge = RecordedJudge(args.replies) if args.judge == "recorded" else FakeJudge()
    template = load_template()
    questions = {q["question_id"]: q for q in load_jsonl(args.questions)}

    rows = []
    for r in load_jsonl(args.responses):
        result = grade_response(judge, template, questions[r["question_id"]], r["response"])
        rows.append({"id": r["id"], "model": r["model"], "question_id": r["question_id"], **result})

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    table = aggregate(rows, len(questions))
    cols = [("correct", "correct"), ("incorrect", "incorrect"), ("not_att", "not_attempted"),
            ("extr_fail", "extraction_failure"), ("judge_err", "judge_error"), ("accuracy", "accuracy"),
            ("cga", "correct_given_attempted"), ("f_score", "f_score"), ("not_att_%", "not_attempted_rate")]
    print("model".ljust(16) + "".join(short.rjust(10) for short, _ in cols))
    for model, t in table.items():
        print(model.ljust(16) + "".join(str(t[key]).rjust(10) for _, key in cols))


if __name__ == "__main__":
    main()
