"""Replacement ToyQA judge pipeline: the contract in audit/CONTRACT.md (v1), clause by clause.

Same functions, arguments and output format as case/judge_pipeline.py, so the two can be swapped:

    python audit/replacement/toyqa_replacement.py [--judge recorded|fake] [--questions Q] [--responses R]
                                                  [--replies J] [--out labels.jsonl]

It keeps the judge model, the judge template and the judge back ends (case/judges.py) and changes only the
deterministic stages. It has no decision switches: every decision entry in the contract concerns the judge's grade
(clause K), which no deterministic stage decides. It was written from the contract, before the stored responses were
graded, and its sha256 is recorded in audit/ISSUE.md before step 5.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(ROOT, "case")
sys.path.insert(0, CASE)

from judges import FakeJudge, RecordedJudge  # noqa: E402

THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
MAX_PREDICTED_CHARS = 300
LABEL_OF_GRADE = {"A": "correct", "B": "incorrect", "C": "not_attempted"}
LABELS = ("correct", "incorrect", "not_attempted", "extraction_failure", "judge_error")
_PLACEHOLDER = re.compile(r"\{(question|target|predicted_answer)\}")
_ASCII_ALNUM = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_template(path=os.path.join(CASE, "judge_template.txt")):
    with open(path, encoding="utf-8") as f:
        return f.read()


def prompt_sha256(prompt):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def extract_graded_text(response):
    """E1-E5: text after the last </think>, stripped; None when <think> never closes."""
    if THINK_CLOSE in response:
        return response[response.rindex(THINK_CLOSE) + len(THINK_CLOSE):].strip()
    if THINK_OPEN in response:
        return None
    return response.strip()


def format_target(question):
    """R2."""
    if question.get("aliases"):
        return question["gold"] + " (also accepted: " + ", ".join(question["aliases"]) + ")"
    return question["gold"]


def fill(template, question_text, target, predicted):
    """R4: each value goes into its placeholder as text; values are never read for placeholders."""
    values = {"question": question_text, "target": target, "predicted_answer": predicted}
    out, pos = [], 0
    for m in _PLACEHOLDER.finditer(template):
        out.append(template[pos:m.start()])
        out.append(values[m.group(1)])
        pos = m.end()
    out.append(template[pos:])
    return "".join(out)


def render_prompt(template, question, graded_text):
    """R1-R4: the first 300 characters of the whole graded text, empty text included."""
    return fill(template, question["question"], format_target(question), graded_text[:MAX_PREDICTED_CHARS])


def parse_grade(reply):
    """P1-P2: the last A, B or C with no ASCII letter or digit directly before or after it, else None."""
    for i in range(len(reply) - 1, -1, -1):
        if reply[i] in "ABC":
            before = reply[i - 1] if i > 0 else ""
            after = reply[i + 1] if i + 1 < len(reply) else ""
            if before not in _ASCII_ALNUM and after not in _ASCII_ALNUM:
                return reply[i]
    return None


def call_judge(judge, prompt):
    """J2, P3: call 1, then call 2 only when call 1 gives no grade."""
    replies = []
    for call in (1, 2):
        reply = judge(prompt, call)
        replies.append(reply)
        grade = parse_grade(reply)
        if grade is not None:
            return grade, replies
    return None, replies


def grade_response(judge, template, question, response):
    """One response row: E, R, J, P and L."""
    graded = extract_graded_text(response)
    if graded is None:
        return {"label": "extraction_failure", "grade": None, "judge_calls": 0, "prompt_sha256": None}
    prompt = render_prompt(template, question, graded)
    grade, replies = call_judge(judge, prompt)
    label = LABEL_OF_GRADE[grade] if grade is not None else "judge_error"
    return {"label": label, "grade": grade, "judge_calls": len(replies), "prompt_sha256": prompt_sha256(prompt)}


def aggregate(rows, n_questions):
    """G1-G5, in the grader's output form: counts, and percentages rounded to 0.1."""
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
    ap = argparse.ArgumentParser(description="Run the replacement ToyQA judge pipeline.")
    ap.add_argument("--judge", choices=["recorded", "fake"], default="recorded")
    ap.add_argument("--questions", default=os.path.join(CASE, "questions.jsonl"))
    ap.add_argument("--responses", default=os.path.join(CASE, "responses.jsonl"))
    ap.add_argument("--replies", default=os.path.join(CASE, "judge_replies.jsonl"))
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
