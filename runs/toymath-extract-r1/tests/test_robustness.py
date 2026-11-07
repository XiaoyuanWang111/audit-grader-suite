"""Robustness (contract S4.4): a response must never make the grader raise, and one bad response must not
stop the grading of the others. Each case runs in its own grader process, because an exception ends the run.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
import graders  # noqa: E402
from _xfail import xfail  # noqa: E402

BIG = fixtures.ISOLATED_FIXTURES[0]  # p02, "Answer: " + 1,000,000 nines; contract label: incorrect

with open(os.path.join(graders.CASE, "responses.jsonl"), encoding="utf-8") as _f:
    STORED = [json.loads(l) for l in _f if l.strip()]


class GradePyRobustness(unittest.TestCase):
    @xfail("F5: decimal.Overflow on an answer with 1,000,000 or more integer digits")
    def test_big_number_alone(self):
        v, out, rc = graders.run_grade_py(graders.as_rows([BIG]))
        self.assertEqual((rc, v and v[BIG["id"]][1]), (0, BIG["label"]), out[-300:])

    @xfail("F5: one such response ends the run before any verdict or score is written")
    def test_one_bad_response_does_not_stop_the_run(self):
        rows = STORED + graders.as_rows([BIG], model="fuzz")
        v, out, rc = graders.run_grade_py(rows)
        self.assertIsNotNone(v, "no verdict file; exit %d" % rc)
        self.assertEqual(len(v), len(rows))


class ReferenceRobustness(unittest.TestCase):
    @xfail("F5: decimal.Overflow in the reference as well")
    def test_big_number_alone(self):
        v, out, rc = graders.run_reference(graders.as_rows([BIG]))
        self.assertEqual((rc, v and v[BIG["id"]][1]), (0, BIG["label"]), out[-300:])


class ReplacementRobustness(unittest.TestCase):
    def test_big_number_alone(self):
        self.assertEqual(graders.run_replacement(graders.as_rows([BIG]))[BIG["id"]][1], BIG["label"])


if __name__ == "__main__":
    unittest.main()
