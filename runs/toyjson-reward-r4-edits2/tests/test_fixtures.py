"""Fixture regression tests for the ToyOrders reward (stdlib unittest; pytest is not installed).

Run from the audit's working directory:
    python -B -m unittest discover -s audit/tests -v

Fixtures that case/reward.py gets wrong are marked unittest.expectedFailure. Since Python 3.4 an unexpected success
makes the run fail, so the mark is strict: the change that fixes the grader must remove it.
"""

import json
import os
import sys
import unittest
from decimal import Decimal

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
for p in (os.path.join(W, "case"), os.path.join(W, "audit"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import replacement_reward as rr  # noqa: E402
import reward as grader  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

DECISION_SWITCH = {"D-whitespace": ("whitespace", "json"), "D-fence-tab": ("fence_tab", False),
                   "D-crlf": ("crlf", False), "D-json-constants": ("json_constants", False),
                   "D-qty-decimal": ("qty_decimal", True), "D-qty-bool": ("qty_bool", True),
                   "D-total-boundary": ("total_inclusive", False)}

with open(os.path.join(W, "case", "orders.jsonl"), encoding="utf-8") as _f:
    REFS = {o["order_id"]: o["reference"] for o in (json.loads(l, parse_float=Decimal) for l in _f if l.strip())}


def _check(tc, value, expected):
    tc.assertIsInstance(value, float)
    tc.assertAlmostEqual(value, expected, places=9)


def _skip_reason(f):
    if f["needs_int_limit"]:
        limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if not 0 < limit < f["needs_int_limit"]:
            return f"label needs an integer-string limit below {f['needs_int_limit']} digits (limit: {limit})"
    return None


class TestGraderFixtures(unittest.TestCase):
    """case/reward.py against the contract's labels."""


class TestReplacementFixtures(unittest.TestCase):
    """audit/replacement_reward.py against the contract's labels, in both modes and under each reading."""


class TestFixtureTable(unittest.TestCase):
    def test_ids_unique(self):
        ids = [f["id"] for f in FIXTURES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_status_consistent(self):
        for f in FIXTURES:
            if f["decision"]:
                self.assertIn(f["grader"], ("reading-A", "reading-B"), f["id"])
            else:
                self.assertTrue(f["grader"] is None or f["grader"].startswith("F"), f["id"])


def _name(prefix, f):
    return f"test_{prefix}_{f['id'].replace(':', '_')}"


def _add(cls, name, fn, xfail=False, skip=None):
    if skip:
        fn = unittest.skip(skip)(fn)
    elif xfail:
        fn = unittest.expectedFailure(fn)
    setattr(cls, name, fn)


for _fx in FIXTURES:
    skip = _skip_reason(_fx)
    ref = REFS[_fx["order_id"]]
    if _fx["decision"] is None:
        def t(self, f=_fx, ref=ref):
            _check(self, grader.reward(f["response"], ref), f["expected"])
        _add(TestGraderFixtures, _name("grader", _fx), t, xfail=bool(_fx["grader"]), skip=skip)
    else:
        d, a_val, b_val = _fx["decision"]
        reading_val = a_val if _fx["grader"] == "reading-A" else b_val

        def t_reading(self, f=_fx, ref=ref, v=reading_val):
            _check(self, grader.reward(f["response"], ref), v)

        def t_proposed(self, f=_fx, ref=ref, v=a_val):
            _check(self, grader.reward(f["response"], ref), v)
        _add(TestGraderFixtures, _name("grader_recorded_reading", _fx), t_reading, skip=skip)
        _add(TestGraderFixtures, _name("grader_proposed", _fx), t_proposed,
             xfail=_fx["grader"] == "reading-B", skip=skip)

    def r_prop(self, f=_fx, ref=ref):
        _check(self, rr.reward(f["response"], ref, **rr.PROPOSED), f["expected"])
    _add(TestReplacementFixtures, _name("proposed", _fx), r_prop, skip=skip)

    fixes_expected = _fx["expected"]
    if _fx["decision"] and _fx["grader"] == "reading-B":
        fixes_expected = _fx["decision"][2]

    def r_fix(self, f=_fx, ref=ref, v=fixes_expected):
        _check(self, rr.reward(f["response"], ref, **rr.FIXES_ONLY), v)
    _add(TestReplacementFixtures, _name("fixes_only", _fx), r_fix, skip=skip)

    if _fx["decision"]:
        sw, bval = DECISION_SWITCH[_fx["decision"][0]]

        def r_b(self, f=_fx, ref=ref, sw=sw, bval=bval):
            _check(self, rr.reward(f["response"], ref, **{**rr.PROPOSED, sw: bval}), f["decision"][2])
        _add(TestReplacementFixtures, _name("reading_b", _fx), r_b, skip=skip)


if __name__ == "__main__":
    unittest.main()
