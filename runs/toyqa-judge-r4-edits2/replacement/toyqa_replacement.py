"""Replacement ToyQA judge pipeline, written from audit/CONTRACT.md (C0-C6).

It keeps the judge model and the judge template and changes only the deterministic stages. One switch per decision
entry, defaults = the audit's proposed readings:

    whitespace        "unicode" (str.strip, proposed) | "ascii"                 D-whitespace
    reopened_think    "failure" (proposed) | "literal"                          D-reopened-think
    judge_window      "first300" (proposed) | "full"                            D-judge-window
    judge_exception   "judge_error" (proposed) | "raise"                        D-judge-exception
    D-missing-response: aggregate() always divides by n_questions (proposed reading; the other reading is
    n_responses, available as aggregate(..., per_response=True)).

Same function names and return shapes as case/judge_pipeline.py, so the same tests and scripts can drive both.
The reply parser is a character scan, not a regular expression, so it does not share code with either pipeline.
"""

import hashlib
from collections import Counter

THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
WINDOW = 300
MAX_CALLS = 2
LABEL_OF_GRADE = {"A": "correct", "B": "incorrect", "C": "not_attempted"}
LABELS = ("correct", "incorrect", "not_attempted", "extraction_failure", "judge_error")
ASCII_ALNUM = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
ASCII_WS = " \t\n\r\x0b\x0c"
DEFAULTS = {"whitespace": "unicode", "reopened_think": "failure", "judge_window": "first300",
            "judge_exception": "judge_error"}


def _opts(opts):
    o = dict(DEFAULTS)
    o.update(opts or {})
    return o


def prompt_sha256(prompt):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def extract_graded_text(response, opts=None):
    """C1. Return the graded text, or None for an extraction failure."""
    o = _opts(opts)
    if THINK_CLOSE in response:
        tail = response[response.rindex(THINK_CLOSE) + len(THINK_CLOSE):]
        if o["reopened_think"] == "failure" and THINK_OPEN in tail:
            return None
        text = tail
    elif THINK_OPEN in response:
        return None
    else:
        text = response
    return text.strip(ASCII_WS) if o["whitespace"] == "ascii" else text.strip()


def format_target(question):
    """C2. Gold target, plus ' (also accepted: X, Y)' when there are aliases."""
    aliases = question.get("aliases") or []
    if aliases:
        return question["gold"] + " (also accepted: " + ", ".join(aliases) + ")"
    return question["gold"]


def predicted_answer(graded_text, opts=None):
    o = _opts(opts)
    return graded_text[:WINDOW] if o["judge_window"] == "first300" else graded_text


def render_prompt(template, question, graded_text, opts=None):
    """C2. Literal, single-pass substitution of the three placeholders."""
    values = {"question": question["question"], "target": format_target(question),
              "predicted_answer": predicted_answer(graded_text, opts)}
    out, i = [], 0
    while i < len(template):
        hit = None
        for name, value in values.items():
            token = "{" + name + "}"
            if template.startswith(token, i):
                hit = (token, value)
                break
        if hit:
            out.append(hit[1])
            i += len(hit[0])
        else:
            out.append(template[i])
            i += 1
    return "".join(out)


def parse_grade(reply):
    """C4. The last capital A, B or C with no ASCII letter or digit directly before or after it."""
    grade = None
    for i, ch in enumerate(reply):
        if ch in "ABC":
            before = reply[i - 1] if i > 0 else ""
            after = reply[i + 1] if i + 1 < len(reply) else ""
            if before not in ASCII_ALNUM and after not in ASCII_ALNUM:
                grade = ch
    return grade


def call_judge(judge, prompt, opts=None):
    """C3. Call 1; call 2 only when call 1 has no grade."""
    o = _opts(opts)
    replies = []
    for call in range(1, MAX_CALLS + 1):
        try:
            reply = judge(prompt, call)
        except Exception:  # noqa: BLE001 - D-judge-exception
            if o["judge_exception"] == "raise":
                raise
            replies.append(None)
            continue
        replies.append(reply)
        grade = parse_grade(reply)
        if grade is not None:
            return grade, replies
    return None, replies


def grade_response(judge, template, question, response, opts=None):
    graded = extract_graded_text(response, opts)
    if graded is None:
        return {"label": "extraction_failure", "grade": None, "judge_calls": 0, "prompt_sha256": None}
    prompt = render_prompt(template, question, graded, opts)
    grade, replies = call_judge(judge, prompt, opts)
    label = LABEL_OF_GRADE[grade] if grade is not None else "judge_error"
    return {"label": label, "grade": grade, "judge_calls": len(replies), "prompt_sha256": prompt_sha256(prompt)}


def aggregate(rows, n_questions, per_response=False):
    """C6. Per model; denominators n_questions (D-missing-response proposal)."""
    table = {}
    for model in sorted({r["model"] for r in rows}):
        labels = [r["label"] for r in rows if r["model"] == model]
        c = Counter(labels)
        n = len(labels) if per_response else n_questions
        accuracy = c["correct"] / n
        attempted = c["correct"] + c["incorrect"]
        cga = c["correct"] / attempted if attempted else 0.0
        f = 2 * accuracy * cga / (accuracy + cga) if accuracy + cga else 0.0
        table[model] = {**{label: c[label] for label in LABELS},
                        "accuracy": round(100 * accuracy, 1),
                        "correct_given_attempted": round(100 * cga, 1),
                        "f_score": round(100 * f, 1),
                        "not_attempted_rate": round(100 * c["not_attempted"] / n, 1)}
    return table
