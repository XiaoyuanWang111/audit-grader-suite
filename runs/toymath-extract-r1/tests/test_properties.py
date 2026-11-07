"""Property and metamorphic tests (skill step 4) on grade.py, the reference and the replacement.

Each property asserts that the grader gives every generated case its label, which is known by construction.
The properties that grade.py fails today are marked xfail(strict).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graders  # noqa: E402
import properties  # noqa: E402
from _xfail import xfail  # noqa: E402

CASES = properties.generate()
ROWS = graders.as_rows(CASES)
_CACHE = {}


def verdicts(name):
    if name not in _CACHE:
        if name == "grade_py":
            v, out, rc = graders.run_grade_py(ROWS)
        elif name == "reference":
            v, out, rc = graders.run_reference(ROWS)
        else:
            v = graders.run_replacement(ROWS)
        _CACHE[name] = v
    return _CACHE[name]


def violations(name, prop):
    v = verdicts(name)
    return [(c["id"], c["problem_id"], c["response"][-40:], c["label"], v[c["id"]][1])
            for c in CASES if c["prop"] == prop and v[c["id"]][1] != c["label"]]


KNOWN_GRADE_PY = {
    "P1": "F1: commas end the number",
    "P7": "F2: tolerance is 1% of the reference, not 0.01",
}


def _make(name, prop, known):
    def test(self):
        self.assertEqual(violations(name, prop)[:5], [])
    if prop in known:
        test = xfail(known[prop])(test)
    return test


class GradePyProperties(unittest.TestCase):
    pass


class ReferenceProperties(unittest.TestCase):
    pass


class ReplacementProperties(unittest.TestCase):
    pass


for _p in properties.PROPS:
    setattr(GradePyProperties, "test_" + _p, _make("grade_py", _p, KNOWN_GRADE_PY))
    setattr(ReferenceProperties, "test_" + _p, _make("reference", _p, {}))
    setattr(ReplacementProperties, "test_" + _p, _make("replacement", _p, {}))

if __name__ == "__main__":
    unittest.main()
