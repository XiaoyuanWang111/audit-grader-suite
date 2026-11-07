"""Regression tests: case/grade.py on every fixture in fixtures.py, run as the evaluation runs it.

One test per fixture asserts the verdict that audit/CONTRACT.md gives under the proposed readings. The fixtures
that grade.py gets wrong today are marked xfail(strict) with the finding or decision entry that explains
them, so the change that fixes grade.py must remove the mark.

Run from the run root:  python -m unittest discover -s audit/tests -p "test_*.py" -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
import graders  # noqa: E402
from _xfail import xfail  # noqa: E402

F1 = "F1: commas end the number"
F2 = "F2: tolerance is 1% of the reference, not 0.01"
F4 = "F4: Decimal subtraction rounds the distance to 28 significant digits"
D_COMMA = "decision D-comma-grouping: grade.py's verdict is reading (b)"
D_DIGITS = "decision D-digits: grade.py's verdict is reading (b)"

KNOWN = {
    "number:0e7d92f33bea1048": F1,   # p07 Answer: 15,000
    "number:a06dab316200a8be": F1,   # p07 Answer: $15,000
    "number:85c39589f1633e65": F1,   # p07 Answer: 15,000 dollars
    "number:da2b2f471d903579": F1,   # p07 Answer: 15,000.00
    "number:fe5fab5ed8839391": F1,   # p03 Answer: 2,250
    "number:ee919c5d8900a606": F1,   # p03 Answer: 2,250.
    "number:71c714f04005fff5": F1,   # p12 Answer: 15,000 (false correct)
    "compare:16617bfbc271b36f": F2,  # p01 Answer: 3.52
    "compare:89c9e1b58ec04932": F2,  # p01 Answer: 3.48
    "compare:5fd80e0c2a892e17": F2,  # p01 Answer: 3.51000000000000001
    "compare:c460abf743cbf65c": F2,  # p07 Answer: 15000.02
    "compare:6dad715a6cc98cca": F2,  # p02 Answer: 482
    "compare:9ab39be07a289612": F2,  # p03 Answer: 2240
    "compare:3e55c254c7ab471d": F2,  # p11 Answer: 754
    "compare:310aaa08a7b1e75f": F2,  # p09 Answer: 29
    "compare:82da74c0f140fa65": F2,  # p07 Answer: 14900
    "compare:4fe7d5cc032be73c": F2,  # p08 Answer: 121
    "compare:529d4c571da22d82": F2,  # p04 Answer: -7.05
    "compare:a7aad36b94926e93": F2,  # p05 Answer: 72.5
    "compare:79658af280b39c18": F2,  # p10 Answer: 13.1
    "compare:11063b6232742a39": F2,  # p12 Answer: 15.1
    "compare:c378f72df93df5de": F2,  # p01 Answer: 3.53
    "compare:03787696fdc3c2da": F2 + "; also " + F4,  # p01 Answer: 3.489999999999999999999999999999
    "compare:8001e423a0f0f867": F4,  # p06 Answer: 0.010000000000000000000000000001
    "decision:d174c93633b1230d": D_COMMA,   # p12 Answer: 1,5
    "decision:9b433c6d4f7c0929": D_COMMA,   # p03 Answer: 22,50
    "decision:de48efe47615d3ea": D_DIGITS,  # p02 fullwidth 486
    "decision:b52195406e23061b": D_DIGITS,  # p02 Arabic-Indic 486
    "decision:866c80c5727310f0": D_DIGITS,  # p02 Kawi 486
}

_VERDICTS = {}


def verdicts():
    if not _VERDICTS:
        v, out, rc = graders.run_grade_py(graders.as_rows(fixtures.FIXTURES))
        if v is None:
            raise RuntimeError("grade.py produced no verdict file (exit %d):\n%s" % (rc, out))
        _VERDICTS.update(v)
    return _VERDICTS


class GradePyFixtures(unittest.TestCase):
    pass


def _make(fx):
    def test(self):
        self.assertEqual(verdicts()[fx["id"]][1], fx["label"],
                         "%s %s %r (%s)" % (fx["id"], fx["problem_id"], fx["response"][:80], fx["note"]))
    test.__doc__ = "%s %s: %s" % (fx["problem_id"], fx["clause"], fx["note"])
    if fx["id"] in KNOWN:
        test = xfail(KNOWN[fx["id"]])(test)
    return test


for _fx in fixtures.FIXTURES:
    setattr(GradePyFixtures, "test_" + _fx["id"].replace(":", "_"), _make(_fx))

assert set(KNOWN) <= {f["id"] for f in fixtures.FIXTURES}, "a KNOWN id names no fixture"

if __name__ == "__main__":
    unittest.main()
