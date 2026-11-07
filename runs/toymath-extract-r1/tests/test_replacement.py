"""The replacement grader (audit/scripts/grade_contract.py) against every fixture label.

Under the proposed readings it must give each fixture's label. With one decision entry switched to reading
(b), it must give the fixture's label for that entry (fixture["alt"]), or its label when the entry does not
change it. These labels were written by hand from audit/CONTRACT.md, so this also checks the implementation.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
import graders  # noqa: E402

sys.path.insert(0, os.path.join(graders.ROOT, "audit", "scripts"))
import grade_contract  # noqa: E402

ROWS = graders.as_rows(fixtures.FIXTURES)


class ReplacementFixtures(unittest.TestCase):
    def test_proposed_readings(self):
        got = graders.run_replacement(ROWS)
        bad = [(f["id"], f["label"], got[f["id"]]) for f in fixtures.FIXTURES if got[f["id"]][1] != f["label"]]
        self.assertEqual(bad, [])

    def test_each_reading_b(self):
        for entry in grade_contract.ENTRY.values():
            got = graders.run_replacement(ROWS, grade_contract.switches_for([entry]))
            bad = [(f["id"], f["alt"].get(entry, f["label"]), got[f["id"]]) for f in fixtures.FIXTURES
                   if got[f["id"]][1] != f["alt"].get(entry, f["label"])]
            self.assertEqual(bad, [], entry)


if __name__ == "__main__":
    unittest.main()
