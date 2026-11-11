"""Metamorphic property tests and a robustness fuzz test for the ToyOrders reward.

Run from the audit's working directory:
    python -B -m unittest discover -s audit/tests -v

Each property applies one edit to 48 reference-correct responses (12 orders x 4 serializations) and compares the
reward with the contract's expected value. Properties that case/reward.py violates are strict expected failures.
"""

import os
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
for p in (os.path.join(W, "case"), os.path.join(W, "audit"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import classify  # noqa: E402
import replacement_reward as rr  # noqa: E402
import stress  # noqa: E402

# Properties case/reward.py violates, with the finding that explains each (from audit/stress.py's table).
GRADER_VIOLATES = {
    "numbered label before each line": "F3",  # the leading "1" parses as the answer, then AttributeError
    "full stop after the answer": "F1",
    "trailing sentence": "F1",
    "answer wrapped in a list": "F3",
    "last item duplicated": "F2",
    "extra shipping item": "F2",
}

_RESULTS = stress.run_properties()


class TestProperties(unittest.TestCase):
    def test_every_violation_is_listed(self):
        names = {n for n, *_ in stress.PROPERTIES}
        self.assertTrue(set(GRADER_VIOLATES) <= names)


def _make(name, who):
    def t(self):
        rec = _RESULTS[name]
        self.assertGreater(rec["cases"], 0)
        self.assertEqual(rec[who], [], f"{len(rec[who])} of {rec['cases']} cases violate '{name}'")
    return t


for _name in ["(base responses)"] + [n for n, *_ in stress.PROPERTIES]:
    _slug = "".join(c if c.isalnum() else "_" for c in _name).strip("_")
    _g = _make(_name, "grader")
    if _name in GRADER_VIOLATES:
        _g = unittest.expectedFailure(_g)
    setattr(TestProperties, f"test_grader_{_slug}", _g)
    setattr(TestProperties, f"test_replacement_{_slug}", _make(_name, "replacement"))


class TestRobustness(unittest.TestCase):
    def test_replacement_never_raises_on_fuzz(self):
        fuzz = stress.run_fuzz(n=500, seed=stress.FUZZ_SEED + 1)
        for gname, rec in fuzz.items():
            self.assertEqual(rec["replacement"], {}, gname)

    def test_grader_differences_on_fuzz_are_explained_by_findings(self):
        import random
        rng = random.Random(stress.FUZZ_SEED + 2)
        for _ in range(500):
            oid, resp = stress.gen_order_object(rng) if rng.random() < 0.5 else stress.gen_mutation(rng)
            self.assertIsNotNone(classify.explain(resp, stress.REFS[oid]), repr(resp[:120]))

    def test_replacement_float_in_range_on_panel(self):
        import json
        with open(os.path.join(W, "case", "responses.jsonl"), encoding="utf-8") as f:
            for r in map(json.loads, f):
                for mode in rr.MODES.values():
                    v = rr.reward(r["response"], stress.REFS[r["order_id"]], **mode)
                    self.assertIsInstance(v, float)
                    self.assertTrue(0.0 <= v <= 1.0)


if __name__ == "__main__":
    unittest.main()
