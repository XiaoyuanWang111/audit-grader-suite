"""Labeled fixtures for the ToyQA judge pipeline, one list per deterministic stage (step 3 of the audit).

Every expected value is written out from audit/CONTRACT.md alone; the clause it rests on is named. Each fixture runs
against the grader under audit, the reference and the replacement. A fixture that an implementation fails carries
`xfail={"<impl>": "<finding id>"}`, applied as a strict expected failure, so the change that fixes the
implementation must also remove the mark.

Run from the audit run's root:  python -I -m unittest discover -s audit/tests -v
"""

import unittest

from toyqa_audit_lib import (IMPLS, QUESTIONS, ScriptedJudge, CountingJudge, expected_prompt, fixture_id, judges,
                             xfail_strict)

Q01 = QUESTIONS["q01"]
TWO_ALIASES = {"question_id": "x2", "question": "Which letter?", "gold": "X", "aliases": ["Y", "Z"]}

# (stage, clause, kind, inputs, expected, xfail)
FIXTURES = [
    # --- E: graded text -------------------------------------------------------------------------------------------
    ("extract", "E3", "pass", {"response": "Canberra"}, "Canberra", {}),
    ("extract", "E3", "pass", {"response": "  Canberra.\n"}, "Canberra.", {}),
    ("extract", "E1", "pass",
     {"response": "<think>Sydney is the largest city; the capital is Canberra.</think>\n\nCanberra"}, "Canberra", {}),
    ("extract", "E1", "pass", {"response": "The user asks for the capital.</think>Canberra"}, "Canberra", {}),
    ("extract", "E1", "near-miss", {"response": "<think>one</think>Sydney<think>two</think> Canberra"}, "Canberra", {}),
    ("extract", "E1", "near-miss", {"response": "<think>x</think>Canberra<think>y"}, "Canberra<think>y", {}),
    ("extract", "E2", "fail", {"response": "<think>The capital of Australia is"}, None, {}),
    ("extract", "E2", "fail", {"response": "Canberra <think>"}, None, {}),
    ("extract", "E4", "near-miss", {"response": "<THINK>Canberra"}, "<THINK>Canberra", {}),
    ("extract", "E5", "near-miss", {"response": "<think>x</think>"}, "", {}),
    ("extract", "E5", "near-miss", {"response": ""}, "", {}),
    ("extract", "E5", "near-miss", {"response": " \n\t "}, "", {}),

    # --- E, J, P, L end to end for one row: (label, judge calls) ------------------------------------------------------
    ("label", "E2 L1 J3", "fail",
     {"question_id": "q01", "response": "<think>The capital of Australia is", "judge": {"scripted": []}},
     {"label": "extraction_failure", "judge_calls": 0}, {"grader": "F1"}),
    ("label", "E5 R1", "near-miss",
     {"question_id": "q01", "response": "<think>I am not sure what to say.</think>", "judge": "fake"},
     {"label": "not_attempted", "judge_calls": 1}, {"grader": "F3"}),
    ("label", "E5 R1", "near-miss", {"question_id": "q01", "response": "", "judge": "fake"},
     {"label": "not_attempted", "judge_calls": 1}, {"grader": "F3"}),
    ("label", "L1", "pass", {"question_id": "q01", "response": "Canberra", "judge": {"scripted": ["A"]}},
     {"label": "correct", "judge_calls": 1, "call_numbers": [1]}, {}),
    ("label", "L1", "pass", {"question_id": "q01", "response": "Sydney", "judge": {"scripted": ["B"]}},
     {"label": "incorrect", "judge_calls": 1, "call_numbers": [1]}, {}),
    ("label", "L1", "pass", {"question_id": "q01", "response": "I don't know.", "judge": {"scripted": ["C"]}},
     {"label": "not_attempted", "judge_calls": 1, "call_numbers": [1]}, {}),
    ("label", "P3 L1", "fail", {"question_id": "q01", "response": "Canberra", "judge": {"scripted": ["", ""]}},
     {"label": "judge_error", "judge_calls": 2, "call_numbers": [1, 2]}, {}),
    ("label", "J2 P3", "pass",
     {"question_id": "q01", "response": "Canberra", "judge": {"scripted": ["Sorry, I cannot grade this.", "B"]}},
     {"label": "incorrect", "judge_calls": 2, "call_numbers": [1, 2]}, {}),
    ("label", "J2 P1 P3", "near-miss",
     {"question_id": "q01", "response": "Canberra", "judge": {"scripted": ["CORRECT", "A"]}},
     {"label": "correct", "judge_calls": 2, "call_numbers": [1, 2]}, {"grader": "F4"}),
    ("label", "J2 P1 P3", "near-miss",
     {"question_id": "q01", "response": "Sydney", "judge": {"scripted": ["INCORRECT", "B"]}},
     {"label": "incorrect", "judge_calls": 2, "call_numbers": [1, 2]}, {"grader": "F4"}),
    ("label", "J2 P1 P3", "near-miss",
     {"question_id": "q01", "response": "I don't know.", "judge": {"scripted": ["NOT_ATTEMPTED", "C"]}},
     {"label": "not_attempted", "judge_calls": 2, "call_numbers": [1, 2]}, {"grader": "F4"}),
    ("label", "P1 L1", "near-miss",
     {"question_id": "q01", "response": "Sydney", "judge": {"scripted": ["Answer: B"]}},
     {"label": "incorrect", "judge_calls": 1, "call_numbers": [1]}, {"grader": "F4"}),

    # --- R: judge prompt; expected {target, predicted} fill the template as R4 says ----------------------------------
    ("render", "R1 R2", "pass", {"question": Q01, "graded_text": "Canberra"},
     {"target": "Canberra", "predicted": "Canberra"}, {}),
    ("render", "R2", "pass", {"question": QUESTIONS["q05"], "graded_text": "García Márquez"},
     {"target": "Gabriel García Márquez (also accepted: García Márquez)", "predicted": "García Márquez"}, {}),
    ("render", "R2", "pass", {"question": TWO_ALIASES, "graded_text": "Y"},
     {"target": "X (also accepted: Y, Z)", "predicted": "Y"}, {}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "Let me check the list of capitals.\nCanberra"},
     {"target": "Canberra", "predicted": "Let me check the list of capitals.\nCanberra"}, {"grader": "F2"}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "Final answer:\n\nCanberra"},
     {"target": "Canberra", "predicted": "Final answer:\n\nCanberra"}, {"grader": "F2"}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "Canberra is the capital."},
     {"target": "Canberra", "predicted": "Canberra is the capital."}, {"grader": "F2"}),
    ("render", "R1", "pass", {"question": Q01, "graded_text": "Canberra " * 39 + "Canberra"},
     {"target": "Canberra", "predicted": "Canberra " * 33 + "Can"}, {}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "a" * 200 + "\n" + "b" * 200},
     {"target": "Canberra", "predicted": "a" * 200 + "\n" + "b" * 99}, {"grader": "F2"}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "\U0001F600" * 301},
     {"target": "Canberra", "predicted": "\U0001F600" * 300}, {}),
    ("render", "R1", "near-miss", {"question": Q01, "graded_text": "a" * 299 + " b"},
     {"target": "Canberra", "predicted": "a" * 299 + " "}, {}),
    ("render", "R4", "near-miss", {"question": Q01, "graded_text": "{target} or {question}"},
     {"target": "Canberra", "predicted": "{target} or {question}"}, {}),
    ("render", "R1 E5", "near-miss", {"question": Q01, "graded_text": ""},
     {"target": "Canberra", "predicted": ""}, {"grader": "F3"}),

    # --- P: reply parsing -------------------------------------------------------------------------------------------
    ("parse", "P1", "pass", {"reply": "A"}, "A", {}),
    ("parse", "P1", "pass", {"reply": "B."}, "B", {}),
    ("parse", "P1", "pass", {"reply": "**C**"}, "C", {}),
    ("parse", "P1", "pass", {"reply": "Grade: B"}, "B", {}),
    ("parse", "P1", "pass", {"reply": "A: CORRECT"}, "A", {}),
    ("parse", "P1", "pass", {"reply": "B (INCORRECT)"}, "B", {}),
    ("parse", "P1", "pass", {"reply": "C. NOT_ATTEMPTED"}, "C", {}),
    ("parse", "P1", "pass", {"reply": "The answer is A."}, "A", {}),
    ("parse", "P1", "pass", {"reply": "éA"}, "A", {}),
    ("parse", "P1", "pass", {"reply": "A_"}, "A", {}),
    ("parse", "P1", "near-miss", {"reply": "A or B"}, "B", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "B\nA"}, "A", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "Answer: B"}, "B", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "Based on the rubric: C"}, "C", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "CORRECT (A)"}, "A", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "NOT_ATTEMPTED (C)"}, "C", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "INCORRECT. B"}, "B", {"grader": "F4"}),
    ("parse", "P1", "near-miss", {"reply": "A, not B"}, "B", {"grader": "F4"}),
    ("parse", "P2", "fail", {"reply": "CORRECT"}, None, {"grader": "F4"}),
    ("parse", "P2", "fail", {"reply": "INCORRECT"}, None, {"grader": "F4"}),
    ("parse", "P2", "fail", {"reply": "NOT_ATTEMPTED"}, None, {"grader": "F4"}),
    ("parse", "P2", "fail", {"reply": ""}, None, {}),
    ("parse", "P2", "fail", {"reply": "a"}, None, {}),
    ("parse", "P2", "fail", {"reply": "I cannot decide."}, None, {}),
    ("parse", "P2", "near-miss", {"reply": "A1"}, None, {"grader": "F4"}),
    ("parse", "P2", "near-miss", {"reply": "1A"}, None, {"grader": "F4"}),
    ("parse", "P2", "near-miss", {"reply": "AB"}, None, {"grader": "F4"}),

    # --- G: aggregation over one model's 12 labels; percentages rounded to 0.1 ---------------------------------------
    ("aggregate", "G1-G5", "pass",
     {"labels": ["correct"] * 6 + ["incorrect"] * 2 + ["not_attempted"] * 2 + ["extraction_failure", "judge_error"]},
     {"accuracy": 50.0, "cga": 75.0, "f_score": 60.0, "not_attempted_rate": 16.7, "correct": 6, "incorrect": 2,
      "not_attempted": 2, "extraction_failure": 1, "judge_error": 1}, {}),
    ("aggregate", "G2 G3 G4", "near-miss", {"labels": ["not_attempted"] * 10 + ["extraction_failure"] * 2},
     {"accuracy": 0.0, "cga": 0.0, "f_score": 0.0, "not_attempted_rate": 83.3, "correct": 0, "incorrect": 0,
      "not_attempted": 10, "extraction_failure": 2, "judge_error": 0}, {}),
    ("aggregate", "G1", "near-miss", {"labels": ["correct"] * 11},
     {"accuracy": 91.7, "cga": 100.0, "f_score": 95.7, "not_attempted_rate": 0.0, "correct": 11, "incorrect": 0,
      "not_attempted": 0, "extraction_failure": 0, "judge_error": 0}, {}),
    ("aggregate", "G3", "fail", {"labels": ["incorrect"] * 12},
     {"accuracy": 0.0, "cga": 0.0, "f_score": 0.0, "not_attempted_rate": 0.0, "correct": 0, "incorrect": 12,
      "not_attempted": 0, "extraction_failure": 0, "judge_error": 0}, {}),
    ("aggregate", "G1 G5", "near-miss", {"labels": ["correct"] + ["judge_error"] * 11},
     {"accuracy": 8.3, "cga": 100.0, "f_score": 15.4, "not_attempted_rate": 0.0, "correct": 1, "incorrect": 0,
      "not_attempted": 0, "extraction_failure": 0, "judge_error": 11}, {}),
]


def _make_judge(spec):
    if spec == "fake":
        return CountingJudge(judges.FakeJudge())
    return ScriptedJudge(spec["scripted"])


def _check(test, impl, stage, inputs, expected):
    if stage == "extract":
        test.assertEqual(impl.extract(inputs["response"]), expected)
    elif stage == "label":
        judge = _make_judge(inputs["judge"])
        label, calls = impl.label(judge, QUESTIONS[inputs["question_id"]], inputs["response"])
        test.assertEqual({"label": label, "judge_calls": calls},
                         {"label": expected["label"], "judge_calls": expected["judge_calls"]})
        if "call_numbers" in expected:
            test.assertEqual([c for c, _ in judge.calls], expected["call_numbers"])
            test.assertEqual(len({p for _, p in judge.calls}), 1, "a retry must resend the same prompt")
    elif stage == "render":
        q = inputs["question"]
        test.assertEqual(impl.render(q, inputs["graded_text"]),
                         expected_prompt(q, expected["target"], expected["predicted"]))
    elif stage == "parse":
        test.assertEqual(impl.parse(inputs["reply"]), expected)
    elif stage == "aggregate":
        test.assertEqual(impl.scores(inputs["labels"]), expected)
    else:
        raise ValueError(stage)


class Fixtures(unittest.TestCase):
    pass


def _attach():
    seen = set()
    for stage, clause, kind, inputs, expected, xfail in FIXTURES:
        fid = fixture_id(stage, inputs)
        assert fid not in seen, f"duplicate fixture {fid}"
        seen.add(fid)
        for impl in IMPLS:
            def test(self, impl=impl, stage=stage, inputs=inputs, expected=expected):
                _check(self, impl, stage, inputs, expected)
            test.__doc__ = f"{fid} [{clause}, {kind}] on {impl.name}"
            if impl.name in xfail:
                test = xfail_strict(f"{xfail[impl.name]}: {fid}")(test)
            setattr(Fixtures, f"test_{impl.name}_{fid.replace(':', '_')}", test)


_attach()

if __name__ == "__main__":
    unittest.main()
