"""Property and metamorphic tests for the verifier under audit (step 4).

Content-level properties call check_answer.main() in-process with this host's Python 3.12: the same code and
interpreter that verify.sh runs, minus the bash wrapper, which never reads the content (the file is opened with an
explicit UTF-8 encoding, so the locale does not matter). State-level edits run the whole verify.sh.

A property must hold for every generated case. The seed is fixed, so failures reproduce.
Run: python -I audit/tests/test_properties.py -v
"""

import concurrent.futures
import contextlib
import importlib.util
import io
import os
import pathlib
import random
import shutil
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "scripts")]

import grader_runner as GR  # noqa: E402

sys.dont_write_bytecode = True  # importing check_answer.py must not write case/task/tests/__pycache__
SEED = 20261107
ASCII_WS = " \t\n\r\x0b\x0c"
_spec = importlib.util.spec_from_file_location("check_answer_under_audit", GR.TESTS_DIR / "check_answer.py")
CHECK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CHECK)


def grade_content(data, workdir):
    """The verdict check_answer.py gives a file holding `data`: 'pass', 'fail', or 'exception:<type>'."""
    p = workdir / "answer.txt"
    p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = CHECK.main(["check_answer.py", str(p), str(GR.TESTS_DIR / "expected.json")])
    except Exception as e:  # noqa: BLE001 - an exception is a grading failure, recorded as such
        return f"exception:{type(e).__name__}"
    return "pass" if code == 0 else "fail"


class ContentProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = GR.new_tmpdir("prop_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def _failures(self, cases, want):
        bad = []
        for data in cases:
            got = grade_content(data, self.dir)
            if got != want:
                bad.append((data[:20] if len(data) > 20 else data, got))
        return bad

    def test_ascii_whitespace_padding_keeps_pass(self):
        """Edits the contract ignores: ASCII whitespace added at either end of a passing answer."""
        rng = random.Random(SEED)
        cases = []
        for _ in range(300):
            pre = "".join(rng.choice(ASCII_WS) for _ in range(rng.randint(0, 4)))
            post = "".join(rng.choice(ASCII_WS) for _ in range(rng.randint(0, 4)))
            cases.append(pre + "41" + post)
        self.assertEqual(self._failures(cases, "pass"), [])

    def test_value_decides(self):
        """For an integer k written plainly, the answer passes if and only if k == 41."""
        rng = random.Random(SEED + 1)
        ks = [0, 1, 4, 14, 40, 42, 141, 410, 411, 1041, 4100] + [rng.randint(0, 10**6) for _ in range(300)]
        ks = [k for k in ks if k != 41]
        self.assertEqual(self._failures([f"{k}\n" for k in ks], "fail"), [])
        self.assertEqual(self._failures(["41\n"], "pass"), [])

    def test_inserted_printable_character_fails(self):
        """Edits the contract forbids: one printable ASCII character that is not a digit, '+' or whitespace,
        inserted anywhere in '41\\n'."""
        rng = random.Random(SEED + 2)
        alphabet = [chr(c) for c in range(0x21, 0x7f) if not chr(c).isdigit() and chr(c) != "+"]
        cases = []
        for _ in range(300):
            s = "41\n"
            i = rng.randint(0, len(s))
            cases.append(s[:i] + rng.choice(alphabet) + s[i:])
        self.assertEqual(self._failures(cases, "fail"), [])

    def test_inserted_inner_whitespace_fails(self):
        cases = ["4" + w + "1\n" for w in ASCII_WS]
        self.assertEqual(self._failures(cases, "fail"), [])

    @unittest.expectedFailure  # F4: str.strip() also removes U+001C..U+001F
    def test_control_character_at_either_end_fails(self):
        """Edits the contract forbids: a control character that is not whitespace (C0 controls other than
        TAB, LF, VT, FF, CR, and DEL) at the start or end of '41'. Both readings of D-whitespace fail these."""
        controls = [chr(c) for c in list(range(0x00, 0x09)) + list(range(0x0e, 0x20)) + [0x7f]]
        cases = [c + "41" for c in controls] + ["41" + c for c in controls]
        self.assertEqual(self._failures(cases, "fail"), [])

    def test_control_characters_other_than_1c_1f_fail(self):
        """The same edit without U+001C..U+001F: the grader fails every one (so F4 is exactly those four)."""
        controls = [chr(c) for c in list(range(0x00, 0x09)) + list(range(0x0e, 0x1c)) + [0x7f]]
        cases = [c + "41" for c in controls] + ["41" + c for c in controls]
        self.assertEqual(self._failures(cases, "fail"), [])

    @unittest.expectedFailure  # F5: int() raises ValueError above 4,300 digits
    def test_no_exception_on_long_numerals(self):
        """Any answer content gets a verdict without an exception (step 4: an exception is a grading failure)."""
        cases = ["1" * 4301, "0" * 4299 + "41", "9" * 10000]
        got = [grade_content(c, self.dir) for c in cases]
        self.assertTrue(all(not g.startswith("exception") for g in got), got)

    def test_numerals_up_to_4300_digits_get_a_verdict(self):
        """Below the limit there is no exception: 4,300 digits is the boundary."""
        got = [grade_content(c, self.dir) for c in ["1" * 4300, "0" * 4298 + "41"]]
        self.assertEqual(got, ["fail", "pass"])


class StateEdits(unittest.TestCase):
    """Metamorphic tests on the sandbox state, through the whole verify.sh. The base state passes; each edit is one
    the contract forbids, so the edited state must fail."""

    BASE = [{"path": "out", "kind": "dir"}, {"path": "out/answer.txt", "kind": "file", "hex": b"41\n".hex()}]
    EDITS = {
        "delete-answer": [{"path": "out", "kind": "dir"}],
        "move-to-workspace-root": [{"path": "out", "kind": "dir"},
                                   {"path": "answer.txt", "kind": "file", "hex": b"41\n".hex()}],
        "replace-with-directory": [{"path": "out", "kind": "dir"}, {"path": "out/answer.txt", "kind": "dir"}],
        "append-u001c": [{"path": "out", "kind": "dir"},
                         {"path": "out/answer.txt", "kind": "file", "hex": b"41\x1c".hex()}],
        "append-letter": [{"path": "out", "kind": "dir"},
                          {"path": "out/answer.txt", "kind": "file", "hex": b"41x\n".hex()}],
    }
    _res = {}

    @classmethod
    def setUpClass(cls):
        def run(state):
            root = GR.new_tmpdir("edit_")
            try:
                return GR.run_verify_sh(GR.build_workspace(state, root))[0]
            finally:
                shutil.rmtree(root, ignore_errors=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("AUDIT_WORKERS", "6"))) as ex:
            futs = {"base": ex.submit(run, cls.BASE)}
            futs.update({k: ex.submit(run, v) for k, v in cls.EDITS.items()})
            cls._res = {k: v.result() for k, v in futs.items()}

    def test_base_passes(self):
        self.assertEqual(self._res["base"], 0)

    @unittest.expectedFailure  # F1
    def test_delete_answer_fails(self):
        self.assertNotEqual(self._res["delete-answer"], 0)

    @unittest.expectedFailure  # F2
    def test_move_to_workspace_root_fails(self):
        self.assertNotEqual(self._res["move-to-workspace-root"], 0)

    @unittest.expectedFailure  # F1
    def test_replace_with_directory_fails(self):
        self.assertNotEqual(self._res["replace-with-directory"], 0)

    @unittest.expectedFailure  # F4
    def test_append_u001c_fails(self):
        self.assertNotEqual(self._res["append-u001c"], 0)

    def test_append_letter_fails(self):
        self.assertNotEqual(self._res["append-letter"], 0)


if __name__ == "__main__":
    unittest.main()
