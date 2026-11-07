"""Score-level fixtures (contract S4): grade.py, the reference and the replacement on whole response files.

Labels come from audit/CONTRACT.md: a model's score is 100 x correct / 12, a no_answer or a missing problem
counts as not correct, and a problem never counts twice (rejecting such a file is allowed).
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graders  # noqa: E402
from _xfail import xfail  # noqa: E402

sys.path.insert(0, os.path.join(graders.ROOT, "audit", "scripts"))
import grade_contract  # noqa: E402

with open(os.path.join(graders.CASE, "problems.jsonl"), encoding="utf-8") as _f:
    PROBLEMS = [json.loads(l) for l in _f if l.strip()]
PIDS = [p["problem_id"] for p in PROBLEMS]
REF = {p["problem_id"]: p["answer"] for p in PROBLEMS}


def row(model, pid, response, n=[0]):
    n[0] += 1
    return {"id": "s%04d" % n[0], "model": model, "problem_id": pid, "response": response}


def right(model, pid):
    return row(model, pid, "Work.\nAnswer: %s" % REF[pid])


def wrong(model, pid):
    return row(model, pid, "Work.\nAnswer: 99999")


def empty(model, pid):
    return row(model, pid, "")


# Each case: rows, and the scores the contract gives (None = the file must be rejected or scored as given).
SC1 = [right("m", p) for p in PIDS[:6]] + [empty("m", p) for p in PIDS[6:]]               # 6 correct, 6 no_answer
SC2 = [right("m", p) for p in PIDS[:11]]                                                   # p12 missing
SC3 = [empty("m", p) for p in PIDS]                                                        # all no_answer
SC4 = ([right("a", p) for p in PIDS[:9]] + [wrong("a", p) for p in PIDS[9:]] +
       [right("b", p) for p in PIDS[:9]] + [empty("b", p) for p in PIDS[9:]])              # b abstains where a errs
SC5 = [right("m", p) for p in PIDS[:11]] + [right("m", "p01")]                             # p01 twice, p12 missing
SC6 = [right("m", p) for p in PIDS] + [right("m", "p01")]                                  # p01 twice
SC7 = [right("m", p) for p in PIDS] + [row("m", "p13", "Answer: 5")]                      # unknown problem


def gp(rows):
    _, out, rc = graders.run_grade_py(rows)
    return graders.scores_grade_py(out), rc


def ref(rows):
    _, out, rc = graders.run_reference(rows)
    return graders.scores_reference(out), rc


class GradePyScore(unittest.TestCase):
    @xfail("F3: grade.py drops no_answer from the denominator")
    def test_sc1_no_answer_counts_in_denominator(self):
        self.assertEqual(gp(SC1)[0]["m"], 50.0)

    @xfail("F3: grade.py's denominator is the graded responses, not the 12 problems")
    def test_sc2_missing_problem_counts_as_not_correct(self):
        self.assertEqual(gp(SC2)[0]["m"], 91.7)

    def test_sc3_all_no_answer_scores_zero(self):
        self.assertEqual(gp(SC3)[0]["m"], 0.0)

    @xfail("F3: replacing a wrong answer with an empty response raises grade.py's score from 75.0 to 100.0")
    def test_sc4_abstaining_does_not_raise_the_score(self):
        s = gp(SC4)[0]
        self.assertEqual((s["a"], s["b"]), (75.0, 75.0))

    @xfail("F6: grade.py counts a second response to p01, and F3 drops the missing p12")
    def test_sc5_duplicate_does_not_count_twice(self):
        s, rc = gp(SC5)
        self.assertTrue(rc != 0 or s["m"] <= 91.7, (rc, s))

    def test_sc6_duplicate_score_at_most_100(self):
        s, rc = gp(SC6)
        self.assertTrue(rc != 0 or s["m"] <= 100.0, (rc, s))

    def test_sc7_unknown_problem_rejected_or_not_counted(self):
        s, rc = gp(SC7)
        self.assertTrue(rc != 0 or s["m"] == 100.0, (rc, s))


class ReferenceScore(unittest.TestCase):
    def test_sc1(self):
        self.assertEqual(ref(SC1)[0]["m"], 50.0)

    def test_sc2(self):
        self.assertEqual(ref(SC2)[0]["m"], 91.7)

    def test_sc4(self):
        s = ref(SC4)[0]
        self.assertEqual((s["a"], s["b"]), (75.0, 75.0))

    @xfail("F6: the reference counts a second response to p01 and scores 12 of 12")
    def test_sc5_duplicate_does_not_count_twice(self):
        s, rc = ref(SC5)
        self.assertTrue(rc != 0 or s["m"] <= 91.7, (rc, s))

    @xfail("F6: the reference counts 13 correct of 12 problems and prints 108.3")
    def test_sc6_duplicate_score_at_most_100(self):
        s, rc = ref(SC6)
        self.assertTrue(rc != 0 or s["m"] <= 100.0, (rc, s))

    def test_sc7_unknown_problem_rejected_or_not_counted(self):
        s, rc = ref(SC7)
        self.assertTrue(rc != 0 or s["m"] == 100.0, (rc, s))


class ReplacementScore(unittest.TestCase):
    def score(self, rows):
        return grade_contract.summarize(grade_contract.grade(PROBLEMS, rows), len(PROBLEMS))

    def test_sc1_to_sc4(self):
        self.assertEqual(self.score(SC1)["m"]["score"], 50.0)
        self.assertAlmostEqual(self.score(SC2)["m"]["score"], 100.0 * 11 / 12)
        self.assertEqual(self.score(SC2)["m"]["missing"], 1)
        self.assertEqual(self.score(SC3)["m"]["score"], 0.0)
        s = self.score(SC4)
        self.assertEqual((s["a"]["score"], s["b"]["score"]), (75.0, 75.0))

    def test_sc5_to_sc7_rejected(self):
        for rows in (SC5, SC6, SC7):
            with self.assertRaises(ValueError):
                grade_contract.grade(PROBLEMS, rows)


if __name__ == "__main__":
    unittest.main()
