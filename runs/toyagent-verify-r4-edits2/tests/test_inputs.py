"""Pinned inputs: every case file matches MANIFEST.sha256, and expected.json holds the count the contract gives."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402


class PinnedInputs(unittest.TestCase):
    def test_manifest_matches(self):
        self.assertEqual(harness.check_manifest(), [])

    def test_expected_json_is_the_contract_count(self):
        total, per_file = harness.count_server_errors()
        self.assertEqual(per_file, {"access.log": 20, "access.log.1": 17, "access.log.2.gz": 4})
        self.assertEqual(total, 41)
        with open(os.path.join(harness.ORIG_TESTS, "expected.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"server_error_count": total})

    def test_replacement_uses_the_same_expected_json(self):
        self.assertEqual(harness.sha256_file(os.path.join(harness.REPL_TESTS, "expected.json")),
                         harness.PINNED["task/tests/expected.json"])


if __name__ == "__main__":
    unittest.main()
