"""Score-level and run-level tests (contract C4) over the inputs in audit/repro/.

Run from W:  python -B -m unittest discover -s audit/tests -v
(Regenerate the inputs with python -B audit/scripts/make_repro.py; their sha256
are recorded in audit/ISSUE.md.)

Each test states the contract's expectation. unittest.expectedFailure marks the
ones the grader or the reference fails (strict: an unexpected pass fails the run).
"""
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import harness  # noqa: E402

REPRO = harness.W / "audit" / "repro"
OUT = harness.OUT / "scores"


def grader_table(name):
    rc, so, se, rows = harness.run_grader(REPRO / name, OUT / f"{name}.grader")
    table = {}
    for line in so.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 5:
            table[parts[0]] = {"correct": int(parts[1]), "incorrect": int(parts[2]),
                               "no_answer": int(parts[3]), "score": float(parts[4])}
    return rc, table, se


def reference_table(name):
    rc, so, se, rows = harness.run_reference(REPRO / name, OUT / f"{name}.reference")
    table = {}
    for line in so.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 4:
            table[parts[0]] = {"correct": int(parts[1]), "of": int(parts[2]), "score": float(parts[3])}
    return rc, table, se


def replacement_table(name):
    m = harness.replacement
    problems = m.load_jsonl(str(harness.PROBLEMS))
    rows, notes = m.grade(problems, m.load_jsonl(str(REPRO / name)))
    return m.summarize(problems, rows), notes


class TestF3Denominator(unittest.TestCase):
    """Score = correct / 12. `abstainer`: 1 correct + 11 without an answer line -> 8.3.
    `partial`: 11 correct, p12 missing -> 91.7."""

    @unittest.expectedFailure
    def test_grader_abstainer(self):
        rc, t, _ = grader_table("F3_denominator.jsonl")
        self.assertEqual(t["abstainer"]["score"], 8.3)

    @unittest.expectedFailure
    def test_grader_partial(self):
        rc, t, _ = grader_table("F3_denominator.jsonl")
        self.assertEqual(t["partial"]["score"], 91.7)

    def test_grader_observed(self):
        # The observed grader behaviour, pinned so that a silent change is noticed.
        rc, t, _ = grader_table("F3_denominator.jsonl")
        self.assertEqual((t["abstainer"]["score"], t["partial"]["score"]), (100.0, 100.0))

    def test_reference(self):
        rc, t, _ = reference_table("F3_denominator.jsonl")
        self.assertEqual((t["abstainer"]["score"], t["partial"]["score"]), (8.3, 91.7))

    def test_replacement(self):
        t, _ = replacement_table("F3_denominator.jsonl")
        self.assertEqual((t["abstainer"]["score"], t["partial"]["score"]), (8.3, 91.7))


class TestF5OneBadRowStopsTheRun(unittest.TestCase):
    """A row the grader cannot grade must not stop the run: the valid row is still scored."""

    @unittest.expectedFailure
    def test_grader_unknown_problem(self):
        rc, t, se = grader_table("F5_unknown_problem.jsonl")
        self.assertEqual(rc, 0, se[-300:])

    @unittest.expectedFailure
    def test_grader_null_response(self):
        rc, t, se = grader_table("F5_null_response.jsonl")
        self.assertEqual(rc, 0, se[-300:])

    @unittest.expectedFailure
    def test_reference_unknown_problem(self):
        rc, t, se = reference_table("F5_unknown_problem.jsonl")
        self.assertEqual(rc, 0, se[-300:])

    @unittest.expectedFailure
    def test_reference_null_response(self):
        rc, t, se = reference_table("F5_null_response.jsonl")
        self.assertEqual(rc, 0, se[-300:])

    def test_replacement(self):
        t, notes = replacement_table("F5_unknown_problem.jsonl")
        self.assertEqual(t["m1"]["correct"], 1)
        t, notes = replacement_table("F5_null_response.jsonl")
        self.assertEqual((t["m1"]["correct"], t["m1"]["grading_error"]), (1, 1))


class TestF6Duplicate(unittest.TestCase):
    """12 correct responses plus a second response to p01: the problem counts once."""

    @unittest.expectedFailure
    def test_grader(self):
        rc, t, _ = grader_table("F6_duplicate.jsonl")
        self.assertEqual(t["dup"]["correct"], 12)

    @unittest.expectedFailure
    def test_reference(self):
        rc, t, _ = reference_table("F6_duplicate.jsonl")
        self.assertLessEqual(t["dup"]["score"], 100.0)

    def test_replacement(self):
        t, notes = replacement_table("F6_duplicate.jsonl")
        self.assertEqual((t["dup"]["correct"], t["dup"]["score"]), (12, 100.0))
        self.assertTrue(any("second response" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
