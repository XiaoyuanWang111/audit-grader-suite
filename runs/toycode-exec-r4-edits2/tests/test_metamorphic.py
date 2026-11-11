"""Metamorphic, property and content-free tests: 33 edits x 10 tasks, graded by all three graders.

Each (grader, edit, task) is one test. KNOWN_MISSES lists the current grader's wrong verdicts (recorded
2026-11-11); those tests are strict expected failures. The reference and the replacement have none.
"""

import functools
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metamorphic  # noqa: E402

_ALL = ["t01", "t02", "t03", "t04", "t05", "t06", "t07", "t08", "t09", "t10"]
_NO_RAISES_TESTS = ["t01", "t02", "t05", "t06", "t07", "t08", "t09", "t10"]
KNOWN_MISSES = {
    "grader": {
        "I05-tag-py": _ALL, "I06-tag-empty": _ALL, "I07-tag-python3": _ALL, "I08-tag-Python": _ALL,   # F3
        "X05-non-python-first-block": _ALL,                                                           # F3
        "X03-rename-function": _NO_RAISES_TESTS, "X04-raise-first": _NO_RAISES_TESTS,                 # F1
        "X10-empty-block": _NO_RAISES_TESTS, "X11-empty-response": _NO_RAISES_TESTS,                  # F1
        "X07-tuple-results": ["t04", "t08", "t09"], "X08-repr-proxy": ["t06"],                         # F2
    },
    "reference": {},
    "replacement": {},
}


@functools.lru_cache(maxsize=None)
def _results():
    return metamorphic.grade_all()


class MetamorphicTests(unittest.TestCase):
    def test_runs_complete(self):
        for kind, r in _results().items():
            self.assertEqual(r["returncode"], 0, kind)
            self.assertEqual(len(r["verdicts"]), len(metamorphic.cases()), kind)


def _make(kind, case):
    def test(self):
        got = _results()[kind]["verdicts"].get(case["id"])
        self.assertEqual(got, case["label"], f"{kind}: {case['id']}")
    known = case["task"] in KNOWN_MISSES[kind].get(case["edit"], [])
    return unittest.expectedFailure(test) if known else test


for _case in metamorphic.cases():
    for _kind in ("grader", "reference", "replacement"):
        _n = "".join(ch if ch.isalnum() else "_" for ch in f"{_kind}_{_case['edit']}_{_case['task']}")
        setattr(MetamorphicTests, "test_" + _n, _make(_kind, _case))


if __name__ == "__main__":
    unittest.main()
