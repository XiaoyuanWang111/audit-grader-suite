"""Regression tests: every labeled fixture against the grader under audit and the replacement.

Run from the audit directory's parent (no pytest offline; plain unittest):

    python -I -m unittest discover -s audit/tests -p "test_*.py" -v

A fixture that the current grader gets wrong is marked with
unittest.expectedFailure, the standard-library counterpart of
pytest.mark.xfail(strict=True): an unexpected success makes the run fail, so
the change that fixes the grader must remove the mark. The reason for each
mark (a finding id or a decision entry) is in GRADER_WRONG.

The grader tests run verify.sh through Git Bash with WORKSPACE, TESTS_DIR and
PYTHON set as the harness sets them, on the pinned files of case/.
"""

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(AUDIT, "scripts"), os.path.join(AUDIT, "replacement")]

import common  # noqa: E402
import fixtures  # noqa: E402
import replacement_scoring as rs  # noqa: E402
import replacement_verifier as rv  # noqa: E402

# Fixture name -> why the current grader's verdict differs from the contract
# label (the proposed reading for decision fixtures).
GRADER_WRONG = {
    # F1: verify.sh ends with a bare `exit` after "no answer file", so it exits 0.
    "empty-workspace": "F1", "only-tmp-notes": "F1", "empty-out-dir": "F1",
    "answer-is-directory": "F1", "no-extension": "F1", "double-extension": "F1",
    "tmp-answer": "F1",
    # F2: verify.sh grades /workspace/answer.txt when out/answer.txt is not a regular file.
    "wrong-path-root-41": "F2", "answer-is-directory-root-41": "F2",
    # F3: str.strip() removes U+001C..U+001F, which are whitespace under neither reading.
    "info-sep-1c-after": "F3", "info-sep-1f-before": "F3", "info-sep-1e-1d": "F3",
    # Decisions: the grader takes the non-proposed reading.
    "plus-sign": "D-plus-sign",
    "plus-sign-and-leading-zero": "D-plus-sign (with D-leading-zeros proposed)",
    "nbsp-after": "D-whitespace-set", "ideographic-space-before": "D-whitespace-set",
    "line-separator-after": "D-whitespace-set", "nel-after": "D-whitespace-set",
    # F4 exception; the fail verdict is right only under D-leading-zeros = reject.
    "zeros-past-int-limit": "F4 + D-leading-zeros",
    # Scoring, F5: trial_reward() treats every falsy verifier_exit_code as a pass.
    "exit-null": "F5", "exit-absent": "F5", "exit-false": "F5", "denominator-with-null": "F5",
}

# The grader must not raise on these (F4): a traceback is a grading failure.
GRADER_RAISES = {"long-number": "F4", "zeros-past-int-limit": "F4"}


def setUpModule():
    common.require_pins("before tests")


def tearDownModule():
    common.require_pins("after tests")


def _tname(fx):
    return "test_" + fx["id"].replace(":", "_") + "_" + fx["name"].replace("-", "_")


_RUNS = {}


def _run_grader(fx):
    """verify.sh on the fixture's sandbox state, once per fixture per test run."""
    if fx["id"] not in _RUNS:
        with tempfile.TemporaryDirectory(prefix="fx_") as ws:
            common.materialize(ws, fx["files"])
            _RUNS[fx["id"]] = common.run_verify(ws)
    return _RUNS[fx["id"]]


def _grader_verifier_test(fx):
    def test(self):
        code, out, _err = _run_grader(fx)
        got = "pass" if code == 0 else "fail"
        self.assertEqual(got, fx["label"], f"{fx['id']} {fx['name']}: exit {code}, output {out[:60]!r}")
    return unittest.expectedFailure(test) if fx["name"] in GRADER_WRONG else test


def _grader_no_exception_test(fx):
    def test(self):
        _code, _out, err = _run_grader(fx)
        self.assertNotIn("Traceback", err, f"{fx['id']} {fx['name']}: the grader raised")
    return unittest.expectedFailure(test) if fx["name"] in GRADER_RAISES else test


def _replacement_verifier_test(fx):
    def test(self):
        with tempfile.TemporaryDirectory(prefix="fx_") as ws:
            common.materialize(ws, fx["files"])
            self.assertEqual(rv.grade(ws, fixtures.N)[0], fx["label"], f"{fx['id']} {fx['name']} proposed")
            if fx["decision"]:
                for sw, lab in fx["decision"]["readings"]:
                    self.assertEqual(rv.grade(ws, fixtures.N, sw)[0], lab, f"{fx['id']} {fx['name']} {sw}")
    return test


def _write_records(td, records):
    for r in records:
        os.makedirs(os.path.join(td, r["trial_id"]))
        with open(os.path.join(td, r["trial_id"], "result.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(r, f)


def _grader_scoring_test(fx):
    def test(self):
        with tempfile.TemporaryDirectory(prefix="sx_") as td:
            _write_records(td, fx["records"])
            rows, out, err, code = common.run_scoring(td)
        self.assertEqual(code, 0, err)
        # score_trials.py prints the mean reward as a percentage with one decimal.
        expected = {c: (t, p, round(100.0 * s, 1)) for c, (t, p, s) in fx["expected"].items()}
        self.assertEqual(rows, expected, f"{fx['id']} {fx['name']}")
    return unittest.expectedFailure(test) if fx["name"] in GRADER_WRONG else test


def _replacement_scoring_test(fx):
    def test(self):
        got = rs.scores(fx["records"])
        self.assertEqual({c: (t, p) for c, (t, p, _s) in got.items()},
                         {c: (t, p) for c, (t, p, _s) in fx["expected"].items()})
        for c, (_t, _p, s) in fx["expected"].items():
            self.assertAlmostEqual(got[c][2], s)
    return test


class TestGraderVerifierFixtures(unittest.TestCase):
    pass


class TestGraderVerifierExceptions(unittest.TestCase):
    pass


class TestReplacementVerifierFixtures(unittest.TestCase):
    def test_correct_count_from_logs(self):
        self.assertEqual(rv.count_server_errors(), fixtures.N)

    def test_expected_json_matches_count(self):
        with open(os.path.join(common.TESTS_DIR, "expected.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"server_error_count": fixtures.N})


class TestGraderScoringFixtures(unittest.TestCase):
    pass


class TestReplacementScoringFixtures(unittest.TestCase):
    pass


fixtures.all_ids()
for _fx in fixtures.VERIFIER_FIXTURES:
    setattr(TestGraderVerifierFixtures, _tname(_fx), _grader_verifier_test(_fx))
    setattr(TestReplacementVerifierFixtures, _tname(_fx), _replacement_verifier_test(_fx))
for _fx in fixtures.VERIFIER_FIXTURES:
    if _fx["kind"] in ("wrong-count", "decision", "control"):
        setattr(TestGraderVerifierExceptions, _tname(_fx), _grader_no_exception_test(_fx))
for _fx in fixtures.SCORING_FIXTURES:
    setattr(TestGraderScoringFixtures, _tname(_fx), _grader_scoring_test(_fx))
    setattr(TestReplacementScoringFixtures, _tname(_fx), _replacement_scoring_test(_fx))


if __name__ == "__main__":
    unittest.main()
