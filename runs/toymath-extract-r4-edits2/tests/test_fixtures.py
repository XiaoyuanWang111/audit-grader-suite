"""Fixture regression tests (step 3).

Run from W:  python -B -m unittest discover -s audit/tests -v

pytest is not installed here, so a fixture the current grader fails is marked
with unittest.expectedFailure: an unexpected pass makes the run fail
(wasSuccessful() is False), the same effect as pytest.mark.xfail(strict=True).
The change that fixes the grader must remove the mark.

- TestGrader:      case/grade.py, full label (correct / incorrect / no_answer).
- TestReference:   case/reference/grade_ref.py, correct vs not correct (it has two labels).
- TestReplacement: audit/replacement/grade_contract.py at the proposed readings,
                   and at every alternative reading listed in a fixture's `alt`.
"""
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import fixtures  # noqa: E402
import harness  # noqa: E402

# Fixtures the grader under audit gets wrong, with the reason (finding or decision).
GRADER_FAILS = {
    "comma-2250": "F1", "comma-15000": "F1", "comma-15000-decimal": "F1",
    "comma-off-grid": "F1", "comma-with-reasoning": "F1",
    "rel-tol-15100": "F2", "rel-tol-485": "F2", "rel-tol-750": "F2", "rel-tol-3.52": "F2",
    "rel-tol-2240": "F2", "rel-tol-minus-7.05": "F2", "rel-tol-486.02": "F2",
    "rel-tol-15.1": "F2", "rel-tol-121": "F2", "rel-tol-72.5": "F2", "rel-tol-13.1": "F2",
    "rel-tol-29": "F2",
    "precision-zero": "F4", "precision-3.51": "F4 (and F2)",
    "fullwidth-digits": "D-digits reading B", "arabic-indic-digits": "D-digits reading B",
}

# Fixtures the reference gets wrong at the score level (correct vs not correct).
REFERENCE_FAILS = {
    "precision-zero": "F4", "precision-3.51": "F4", "double-comma": "R1",
    "fullwidth-digits": "D-digits reading B", "arabic-indic-digits": "D-digits reading B",
    "currency-sign": "D-surrounding-text reading B", "unit-after": "D-surrounding-text reading B",
    "final-period": "D-surrounding-text reading B", "bold-number": "D-surrounding-text reading B",
    "word-after": "D-surrounding-text reading B", "curly-quotes-number": "D-surrounding-text reading B",
    "multi-first-right": "D-surrounding-text reading B / D-multiple-numbers reading C",
}

_RESULTS = None


def results():
    global _RESULTS
    if _RESULTS is None:
        _RESULTS = harness.grade_all(fixtures.FIXTURES, "fixtures")
    return _RESULTS


def _parse_alt(key):
    opts = {}
    for part in key.split("&"):
        k, v = part.split("=")
        opts[k] = v
    return opts


class TestGrader(unittest.TestCase):
    pass


class TestReference(unittest.TestCase):
    pass


class TestReplacement(unittest.TestCase):
    pass


class TestBookkeeping(unittest.TestCase):
    def test_expectation_names_exist(self):
        for name in list(GRADER_FAILS) + list(REFERENCE_FAILS):
            self.assertIn(name, fixtures.BY_NAME)

    def test_decision_failures_match_an_alternative_reading(self):
        # A wrong verdict on a decision fixture must equal the label under a
        # non-proposed reading; otherwise it is a finding.
        res = results()
        for name, why in GRADER_FAILS.items():
            f = fixtures.BY_NAME[name]
            if f["kind"] == "decision":
                self.assertIn(res[f["id"]]["grader"], f["alt"].values(), name)
        for name, why in REFERENCE_FAILS.items():
            f = fixtures.BY_NAME[name]
            if f["kind"] == "decision":
                alts = {harness.binary(v) for v in f["alt"].values()}
                self.assertIn(harness.binary(res[f["id"]]["reference"]), alts, name)


def _safe(name):
    return "".join(c if c.isalnum() else "_" for c in name)


def _make(f):
    def t_grader(self):
        self.assertEqual(results()[f["id"]]["grader"], f["label"], f"{f['name']} {f['id']}")

    def t_reference(self):
        self.assertEqual(harness.binary(results()[f["id"]]["reference"]), harness.binary(f["label"]),
                         f"{f['name']} {f['id']}")

    def t_replacement(self):
        refs = {pid: p["answer"] for pid, p in fixtures.PROBLEMS.items()}
        lab, _ = harness.replacement.verdict(f["response"], refs[f["problem_id"]])
        self.assertEqual(lab, f["label"], f"{f['name']} {f['id']}")
        for key, alt_label in f["alt"].items():
            lab, _ = harness.replacement.verdict(f["response"], refs[f["problem_id"]], _parse_alt(key))
            self.assertEqual(lab, alt_label, f"{f['name']} under {key}")

    if f["name"] in GRADER_FAILS:
        t_grader = unittest.expectedFailure(t_grader)
    if f["name"] in REFERENCE_FAILS:
        t_reference = unittest.expectedFailure(t_reference)
    return t_grader, t_reference, t_replacement


for _f in fixtures.FIXTURES:
    _g, _r, _p = _make(_f)
    _n = "test_" + _safe(_f["name"])
    setattr(TestGrader, _n, _g)
    setattr(TestReference, _n, _r)
    setattr(TestReplacement, _n, _p)


if __name__ == "__main__":
    unittest.main()
