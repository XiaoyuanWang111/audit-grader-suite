"""Metamorphic property tests (step 4): one test per (edit, grader), over all 12 problems.

Run from W:  python -B -m unittest discover -s audit/tests -v

Expected failures (unittest.expectedFailure, strict: an unexpected pass fails the run):
- grader: thousands-commas (F1), shift-plus-0.02 and shift-plus-1 (F2);
- reference: the D-surrounding-text edits (it follows reading B).
"""
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import fixtures  # noqa: E402
import harness  # noqa: E402
import properties  # noqa: E402

GRADER_FAILS = {"thousands-commas": "F1", "shift-plus-0.02": "F2", "shift-plus-1": "F2"}
REFERENCE_FAILS = {name: "D-surrounding-text reading B" for name, _, dep, _, _ in properties.EDITS
                   if dep == "D-surrounding-text"}

_RES = None


def res():
    global _RES
    if _RES is None:
        items = []
        for name, expect, depends, pid, resp in properties.cases(fixtures.PROBLEMS):
            items.append({"id": f"{name}|{pid}", "problem_id": pid, "response": resp,
                          "edit": name, "expect": expect})
        _RES = (items, harness.grade_all(items, "properties_test"))
    return _RES


class TestPropertiesGrader(unittest.TestCase):
    pass


class TestPropertiesReference(unittest.TestCase):
    pass


class TestPropertiesReplacement(unittest.TestCase):
    pass


def _make(edit, who):
    def t(self):
        items, r = res()
        bad = [it["problem_id"] for it in items
               if it["edit"] == edit and harness.binary(r[it["id"]][who]) != it["expect"]]
        self.assertEqual(bad, [], f"{who} breaks {edit} on {bad}")
    return t


for _name, _expect, _dep, _a, _b in properties.EDITS:
    _n = "test_" + "".join(c if c.isalnum() else "_" for c in _name)
    tg = _make(_name, "grader")
    tr = _make(_name, "reference")
    tp = _make(_name, "replacement")
    if _name in GRADER_FAILS:
        tg = unittest.expectedFailure(tg)
    if _name in REFERENCE_FAILS:
        tr = unittest.expectedFailure(tr)
    setattr(TestPropertiesGrader, _n, tg)
    setattr(TestPropertiesReference, _n, tr)
    setattr(TestPropertiesReplacement, _n, tp)


if __name__ == "__main__":
    unittest.main()
