"""Step 3: run every labeled fixture against the grader under audit and the replacement.

    python -I -B -m unittest discover -s audit/tests -t audit/tests -v

A fixture whose `grader` field names a finding or decision is a strict expected failure for
case/reward.py: the change that fixes the grader (or adopts the proposed reading) must remove
the mark, because an unexpected success fails the run.
"""
import unittest

from fixtures import FIXTURES
from support import REFS, grader, replacement, run, verdict_ok, xfail_strict

SWITCH = {
    "D-fence-newline": "fence_newline",
    "D-inner-whitespace": "inner_whitespace",
    "D-qty-bool": "qty_bool",
    "D-qty-integral": "qty_integral",
    "D-total-boundary": "total_boundary",
}


def _official_label(f):
    """The fixture's label under the readings that case/reward.py implements."""
    if not f["readings"]:
        return f["expected"]
    (decision, labels), = f["readings"].items()
    return labels[replacement.OFFICIAL[SWITCH[decision]]]


class GraderFixtures(unittest.TestCase):
    """case/reward.py against each fixture's contract label (proposed readings)."""


class ReplacementFixtures(unittest.TestCase):
    """audit/replacement/reward_contract.py: proposed readings, each decision's readings,
    and the official readings ("fixes only")."""


def _grader_test(f):
    def test(self):
        outcome = run(grader.reward, f["response"], REFS[f["order_id"]])
        self.assertTrue(verdict_ok(outcome, f["expected"]),
                        "%s: grader %r, contract %r" % (f["id"], outcome, f["expected"]))
    if f["grader"]:
        test = xfail_strict(f["grader"])(test)
    return test


def _replacement_test(f):
    def test(self):
        ref = REFS[f["order_id"]]
        outcome = run(replacement.reward, f["response"], ref)
        self.assertTrue(verdict_ok(outcome, f["expected"]), "%s proposed: %r" % (f["id"], outcome))
        if f["readings"]:
            (decision, labels), = f["readings"].items()
            for reading, label in labels.items():
                got = run(replacement.reward, f["response"], ref, **{SWITCH[decision]: reading})
                self.assertTrue(verdict_ok(got, label), "%s %s=%s: %r" % (f["id"], decision, reading, got))
        got = run(replacement.reward, f["response"], ref, **replacement.OFFICIAL)
        self.assertTrue(verdict_ok(got, _official_label(f)), "%s official: %r" % (f["id"], got))
    return test


for _f in FIXTURES:
    _name = "test_" + _f["id"].replace(":", "_").replace("-", "_")
    setattr(GraderFixtures, _name, _grader_test(_f))
    setattr(ReplacementFixtures, _name, _replacement_test(_f))


if __name__ == "__main__":
    unittest.main()
