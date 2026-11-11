"""Fixture regression tests (unittest; pytest is not installed in this run).

Run from anywhere:  python -B -m unittest discover -s audit/tests -p "test_*.py" -v
A test that the current grader (or the reference) fails is wrapped in unittest.expectedFailure, which is strict:
if the grader is fixed, the test reports an unexpected success and the run fails until the mark is removed.
"""

import functools
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402
from fixtures import AGGREGATION, FIB, FIXTURES, ROBUSTNESS, SET_ORDER_RLE, fenced  # noqa: E402

KINDS = ("grader", "reference", "replacement")


@functools.lru_cache(maxsize=None)
def _single_results():
    """Grade each fixture alone with each grader (and each decision switch on the replacement)."""
    jobs = []
    for fx in FIXTURES:
        for kind in KINDS:
            jobs.append((fx["id"], kind, ()))
        for dec, (sw, _alt) in fx["alt"].items():
            jobs.append((fx["id"], "replacement:" + dec, tuple(sw)))
    by_id = {fx["id"]: fx for fx in FIXTURES}

    def go(job):
        fid, kind, sw = job
        fx = by_id[fid]
        r = harness.run(kind.split(":")[0], [harness.row("x", fx["task"], fx["response"])], switches=sw)
        return job[:2], r["verdicts"].get("x")

    with ThreadPoolExecutor(max_workers=4) as ex:
        return dict(ex.map(go, jobs))


@functools.lru_cache(maxsize=None)
def _robust_results():
    out = {}
    for fx in ROBUSTNESS:
        rows = [harness.row("rob", fx["task"], fx["response"]), harness.row("ctl", "t07", fenced(FIB))]
        for kind in KINDS:
            out[(fx["id"], kind)] = harness.run(kind, rows)
    return out


class FixtureTests(unittest.TestCase):
    pass


def _make_single(fx, kind):
    def test(self):
        got = _single_results()[(fx["id"], kind)]
        self.assertEqual(got, fx["label"], f"{fx['id']} ({fx['note']}): {kind} gave {got}")
    ok = True if kind == "replacement" else fx[kind + "_ok"]
    return test if ok else unittest.expectedFailure(test)


def _make_alt(fx, dec, alt_label):
    def test(self):
        got = _single_results()[(fx["id"], "replacement:" + dec)]
        self.assertEqual(got, alt_label, f"{fx['id']} under the other reading of {dec}")
    return test


def _make_robust(fx, kind):
    def test(self):
        r = _robust_results()[(fx["id"], kind)]
        self.assertEqual(r["returncode"], 0, f"{kind} stopped: {r['stderr'][-300:]}")
        self.assertEqual(r["verdicts"].get("rob"), fx["label"])
        self.assertEqual(r["verdicts"].get("ctl"), "pass", "the control row after it must still be graded")
    ok = True if kind == "replacement" else fx[kind + "_ok"]
    return test if ok else unittest.expectedFailure(test)


def _make_agg(fid, rows, want, kind, ok):
    def test(self):
        r = harness.run(kind, [harness.row(i, t, resp, model="m") for i, t, resp in rows])
        self.assertEqual(r["returncode"], 0)
        self.assertEqual(r["scores"].get("m"), want, r["stdout"])
    return test if ok else unittest.expectedFailure(test)


def _make_seed(kind, ok):
    def test(self):
        rows = [harness.row("x", "t06", SET_ORDER_RLE)]
        v0 = harness.run(kind, rows, env={"PYTHONHASHSEED": "0"})["verdicts"]["x"]
        v1 = harness.run(kind, rows, env={"PYTHONHASHSEED": "1"})["verdicts"]["x"]
        self.assertEqual(v0, v1, "verdict depends on the grader's PYTHONHASHSEED")
    return test if ok else unittest.expectedFailure(test)


def _name(s):
    return "".join(ch if ch.isalnum() else "_" for ch in s)


for _fx in FIXTURES:
    for _kind in KINDS:
        setattr(FixtureTests, f"test_{_name(_fx['id'])}_{_kind}", _make_single(_fx, _kind))
    for _dec, (_sw, _alt) in _fx["alt"].items():
        setattr(FixtureTests, f"test_{_name(_fx['id'])}_replacement_{_name(_dec)}", _make_alt(_fx, _dec, _alt))
for _fx in ROBUSTNESS:
    for _kind in KINDS:
        setattr(FixtureTests, f"test_{_name(_fx['id'])}_{_kind}", _make_robust(_fx, _kind))
for _fid, _rows, _want, _gok, _rok, _note in AGGREGATION:
    for _kind, _ok in (("grader", _gok), ("reference", _rok), ("replacement", True)):
        setattr(FixtureTests, f"test_{_name(_fid)}_{_kind}", _make_agg(_fid, _rows, _want, _kind, _ok))
for _kind, _ok in (("grader", False), ("reference", False), ("replacement", True)):
    setattr(FixtureTests, f"test_seed_independence_t06_{_kind}", _make_seed(_kind, _ok))


if __name__ == "__main__":
    unittest.main()
