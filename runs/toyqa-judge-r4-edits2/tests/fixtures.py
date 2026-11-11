"""Labeled fixtures for the ToyQA judge pipeline, labeled from audit/CONTRACT.md alone.

Kinds:
  pipeline   one response, one question, scripted judge replies -> expected label, number of judge calls, the
             predicted answer the judge sees (None = not sent), and optionally the target line.
  aggregate  one model's labels over 12 questions -> expected metrics (rounded to 0.1 point).

A fixture with "decision" depends on that decision entry: "expect" is the proposed reading, "alt" the other one.
Each fixture's id is its stage plus the first 16 hex digits of the sha256 of its canonical JSON (without the id).
"""
import hashlib
import json

Q01 = "q01"  # Canberra, no aliases
Q05 = "q05"  # Gabriel García Márquez (also accepted: García Márquez)
Q08 = "q08"  # the Amazon River (also accepted: the Amazon)
T1 = {"question_id": "t1", "question": "Name a primary color of light.", "gold": "red", "aliases": ["green", "blue"]}

INSTR = "Answer the question below with a short answer. If you do not know the answer, say so."
PROMPT_Q01 = INSTR + "\n\nQuestion: What is the capital city of Australia?"


def P(stage, response, expect, replies=("A",), q=Q01, **kw):
    return dict(kind="pipeline", stage=stage, q=q, response=response, replies=list(replies), expect=expect, **kw)


def E(label, calls, predicted, target=None):
    e = {"label": label, "calls": calls, "predicted": predicted}
    if target is not None:
        e["target"] = target
    return e


RAISE = {"raise": "LookupError"}

_RAW = [
    # ---- C1 extraction -------------------------------------------------------------------------------------------
    P("extract", "Canberra", E("correct", 1, "Canberra")),
    P("extract", "<think>Sydney is larger.</think>\n\nCanberra", E("correct", 1, "Canberra")),
    P("extract", "<think>a</think>Sydney<think>b</think>Canberra", E("correct", 1, "Canberra")),
    P("extract", "The user wants a capital.</think>Canberra", E("correct", 1, "Canberra")),
    P("extract", "  \n Canberra \n\n", E("correct", 1, "Canberra")),
    P("extract", "<think>Australia's capital is", E("extraction_failure", 0, None), finding="F1"),
    P("extract", "<think>", E("extraction_failure", 0, None), finding="F1"),
    P("extract", "<think>a</think>Canberra<think>but wait", E("extraction_failure", 0, None),
      decision="D-reopened-think", alt=E("correct", 1, "Canberra<think>but wait")),
    P("extract", "\u00a0Canberra\u3000", E("correct", 1, "Canberra"),
      decision="D-whitespace", alt=E("correct", 1, "\u00a0Canberra\u3000")),
    # ---- C2 rendering --------------------------------------------------------------------------------------------
    P("render", "Let me answer.\nCanberra", E("correct", 1, "Let me answer.\nCanberra"), finding="F2"),
    P("render", "The capital of Australia\nis Canberra.", E("correct", 1, "The capital of Australia\nis Canberra."),
      finding="F2"),
    P("render", "Canberra\u2028is the capital.", E("correct", 1, "Canberra\u2028is the capital."), finding="F2"),
    P("render", "Sydney?\r\nNo: Canberra.", E("correct", 1, "Sydney?\r\nNo: Canberra."), finding="F2"),
    P("render", "", E("not_attempted", 1, ""), replies=("C",), finding="F3"),
    P("render", "<think>Thinking done.</think>", E("not_attempted", 1, ""), replies=("C",), finding="F3"),
    P("render", "   \n\t ", E("not_attempted", 1, ""), replies=("C",), finding="F3"),
    P("render", "Canberra " * 40, E("correct", 1, ("Canberra " * 40).strip()[:300])),
    P("render", "y" * 300, E("incorrect", 1, "y" * 300), replies=("B",)),
    P("render", "\U0001F600" * 301, E("incorrect", 1, "\U0001F600" * 300), replies=("B",)),
    P("render", "{target} or {question} or {0} or {}", E("incorrect", 1, "{target} or {question} or {0} or {}"),
      replies=("B",)),
    P("render", "x" * 290 + " so the answer is Canberra", E("not_attempted", 1, ("x" * 290 + " so the answer is Canberra")[:300]),
      replies=("C",), decision="D-judge-window",
      alt=E("not_attempted", 1, "x" * 290 + " so the answer is Canberra")),
    P("render", "Garc\u00eda M\u00e1rquez", E("correct", 1, "Garc\u00eda M\u00e1rquez",
                                    target="Gabriel Garc\u00eda M\u00e1rquez (also accepted: Garc\u00eda M\u00e1rquez)"), q=Q05),
    P("render", "Amazon", E("correct", 1, "Amazon", target="the Amazon River (also accepted: the Amazon)"), q=Q08),
    P("render", "green", E("correct", 1, "green", target="red (also accepted: green, blue)"), q=T1["question_id"]),
    P("render", "Canberra", E("correct", 1, "Canberra", target="Canberra")),
    # ---- content-free responses (step 4): they must reach the judge unchanged ------------------------------------
    P("contentfree", INSTR, E("not_attempted", 1, INSTR), replies=("C",)),
    P("contentfree", PROMPT_Q01, E("not_attempted", 1, PROMPT_Q01), replies=("C",), finding="F2"),
    P("contentfree", "What is the capital city of Australia? " * 10,
      E("not_attempted", 1, ("What is the capital city of Australia? " * 10).strip()[:300]), replies=("C",)),
    # ---- C4 parsing and C5 label mapping (scripted judge replies) ------------------------------------------------
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("A",)),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("B",)),
    P("parse", "Canberra", E("not_attempted", 1, "Canberra"), replies=("C",)),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("A.",)),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("**A**",)),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("Grade: B",)),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("B: INCORRECT",)),
    P("parse", "Canberra", E("not_attempted", 1, "Canberra"), replies=("C: NOT_ATTEMPTED",)),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("B\n",)),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("(B)",)),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("\u00e9A",)),
    P("parse", "Canberra", E("not_attempted", 1, "Canberra"), replies=("_C_",)),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("Answer matches the gold target. A",)),
    P("parse", "Canberra", E("incorrect", 2, "Canberra"), replies=("\uff21", "B")),
    P("parse", "Canberra", E("judge_error", 2, "Canberra"), replies=("no grade here", "still none")),
    P("parse", "Canberra", E("judge_error", 2, "Canberra"), replies=("", "")),
    P("parse", "Canberra", E("judge_error", 2, "Canberra"), replies=("a", "b")),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("Based on the gold target, the grade is A.",),
      finding="F4"),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("Clearly wrong: B",), finding="F4"),
    P("parse", "Canberra", E("correct", 1, "Canberra"), replies=("Comparing it with the gold target: A",),
      finding="F4"),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("After checking the symbol, the grade is B",),
      finding="F4"),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("A liver is not skin. B",), finding="F4"),
    P("parse", "Canberra", E("incorrect", 1, "Canberra"), replies=("The grade is A, not B",), finding="F4"),
    P("parse", "Canberra", E("correct", 2, "Canberra"), replies=("CORRECT", "A"), finding="F4"),
    P("parse", "Canberra", E("incorrect", 2, "Canberra"), replies=("INCORRECT", "B"), finding="F4"),
    P("parse", "Canberra", E("not_attempted", 2, "Canberra"), replies=("NOT_ATTEMPTED", "C"), finding="F4"),
    P("parse", "Canberra", E("incorrect", 2, "Canberra"), replies=("A1", "B"), finding="F4"),
    P("parse", "Canberra", E("incorrect", 2, "Canberra"), replies=("Cannot be the Amazon, so this is wrong.", "B"),
      finding="F4"),
    P("parse", "Canberra", E("judge_error", 2, "Canberra"), replies=("CORRECT", "CORRECT"), finding="F4"),
    # ---- C3 judge call: a back end that raises (D-judge-exception) -----------------------------------------------
    P("judgecall", "Canberra", E("correct", 2, "Canberra"), replies=(RAISE, "A"), decision="D-judge-exception",
      alt={"raises": "LookupError"}),
    P("judgecall", "Canberra", E("judge_error", 2, "Canberra"), replies=(RAISE, RAISE), decision="D-judge-exception",
      alt={"raises": "LookupError"}),
    # ---- C6 aggregation ------------------------------------------------------------------------------------------
    dict(kind="aggregate", stage="aggregate",
         labels=["correct"] * 6 + ["incorrect"] * 2 + ["not_attempted"] * 2 + ["extraction_failure", "judge_error"],
         expect={"accuracy": 50.0, "correct_given_attempted": 75.0, "f_score": 60.0, "not_attempted_rate": 16.7,
                 "extraction_failure": 1, "judge_error": 1}),
    dict(kind="aggregate", stage="aggregate", labels=["not_attempted"] * 12,
         expect={"accuracy": 0.0, "correct_given_attempted": 0.0, "f_score": 0.0, "not_attempted_rate": 100.0}),
    dict(kind="aggregate", stage="aggregate", labels=["extraction_failure"] * 12,
         expect={"accuracy": 0.0, "correct_given_attempted": 0.0, "f_score": 0.0, "not_attempted_rate": 0.0,
                 "extraction_failure": 12}),
    dict(kind="aggregate", stage="aggregate", labels=["correct"] * 11, decision="D-missing-response",
         expect={"accuracy": 91.7, "correct_given_attempted": 100.0, "f_score": 95.7, "not_attempted_rate": 0.0},
         alt={"accuracy": 100.0, "correct_given_attempted": 100.0, "f_score": 100.0, "not_attempted_rate": 0.0}),
    dict(kind="aggregate", stage="aggregate", labels=["correct"] + ["incorrect"] * 11,
         expect={"accuracy": 8.3, "correct_given_attempted": 8.3, "f_score": 8.3, "not_attempted_rate": 0.0}),
]


def _fid(fx):
    body = json.dumps({k: v for k, v in fx.items() if k != "id"}, sort_keys=True, ensure_ascii=True)
    return fx["stage"] + ":" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


FIXTURES = []
for _fx in _RAW:
    _fx = dict(_fx)
    _fx["id"] = _fid(_fx)
    FIXTURES.append(_fx)

assert len({f["id"] for f in FIXTURES}) == len(FIXTURES), "duplicate fixture ids"
