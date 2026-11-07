"""Property and metamorphic tests (step 4), seeded.

Content properties call check_answer.main in-process on an answer file (the
code path verify.sh takes whenever out/answer.txt is a regular file); sandbox
layout properties run verify.sh through Git Bash. Expected failures follow the
same rule as test_fixtures.py (unittest.expectedFailure = strict xfail).

    python -I -m unittest discover -s audit/tests -p "test_properties.py" -v
"""

import contextlib
import io
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(AUDIT, "scripts"), os.path.join(AUDIT, "replacement")]

import common  # noqa: E402
import replacement_scoring as rs  # noqa: E402
import replacement_verifier as rv  # noqa: E402

SEED = 20261107
N = 41
ASCII_WS = " \t\n\r\v\f"
EXPECTED = os.path.join(common.TESTS_DIR, "expected.json")
CHECK_MAIN = common.load_check_answer_main()


def setUpModule():
    common.require_pins("before property tests")


def tearDownModule():
    common.require_pins("after property tests")


def check_content(data):
    """The grader's verdict on answer bytes, in-process: 'pass', 'fail' or 'raise'."""
    with tempfile.TemporaryDirectory(prefix="pc_") as d:
        p = os.path.join(d, "answer.txt")
        with open(p, "wb") as f:
            f.write(data)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc = CHECK_MAIN(["check_answer.py", p, EXPECTED])
        except Exception:
            return "raise"
    return "pass" if rc == 0 else "fail"


def grader_state(files):
    with tempfile.TemporaryDirectory(prefix="ps_") as ws:
        common.materialize(ws, files)
        code, _out, _err = common.run_verify(ws)
    return "pass" if code == 0 else "fail"


def random_name(rng):
    return "".join(rng.choice("abcdefgh_") for _ in range(rng.randint(1, 6))) + rng.choice(["", ".txt", ".py", ".sh"])


def random_extra_files(rng, k, allow_root_answer):
    files = {}
    while len(files) < k:
        where = rng.choice(["tmp", "out", "", "work/sub"])
        name = random_name(rng)
        rel = f"{where}/{name}" if where else name
        if rel == "out/answer.txt" or (rel == "answer.txt" and not allow_root_answer):
            continue
        files[rel] = str(rng.randint(0, 99)).encode() + b"\n"
    return files


class TestContentProperties(unittest.TestCase):
    def test_p1_ascii_whitespace_padding_keeps_pass(self):
        rng = random.Random(SEED + 1)
        bad = []
        for _ in range(200):
            left = "".join(rng.choice(ASCII_WS) for _ in range(rng.randint(0, 5)))
            right = "".join(rng.choice(ASCII_WS) for _ in range(rng.randint(0, 5)))
            data = (left + "41" + right).encode()
            if check_content(data) != "pass":
                bad.append(data)
        self.assertEqual(bad, [])

    def test_p3_other_value_fails(self):
        rng = random.Random(SEED + 3)
        bad = []
        for _ in range(300):
            k = rng.choice([rng.randint(0, 100), rng.randint(0, 10 ** 6)])
            if k == N:
                continue
            data = f"{k}\n".encode()
            if check_content(data) != "fail":
                bad.append(data)
        self.assertEqual(bad, [])

    def test_p4_inserted_printable_character_fails(self):
        """Every printable ASCII non-digit at every position of '41' (exhaustive),
        except '+' in front, which D-plus-sign decides."""
        bad = []
        for code in range(33, 127):
            ch = chr(code)
            if ch.isdigit():
                continue
            for pos in range(3):
                if ch == "+" and pos == 0:
                    continue
                data = ("41"[:pos] + ch + "41"[pos:] + "\n").encode()
                if check_content(data) != "fail":
                    bad.append(data)
        self.assertEqual(bad, [])

    def test_p8_grader_and_replacement_agree_on_proposed_readings_for_ascii_only_input(self):
        """Random short strings over digits, ASCII whitespace and a few symbols."""
        rng = random.Random(SEED + 8)
        alphabet = "0123456789" + ASCII_WS + "-.,x"
        bad = []
        with tempfile.TemporaryDirectory(prefix="p8_") as ws:
            os.makedirs(os.path.join(ws, "out"))
            for _ in range(500):
                data = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6))).encode()
                with open(os.path.join(ws, "out", "answer.txt"), "wb") as f:
                    f.write(data)
                if check_content(data) != rv.grade(ws, N)[0]:
                    bad.append(data)
        self.assertEqual(bad, [])


class TestSandboxProperties(unittest.TestCase):
    """verify.sh through Git Bash; a few seeded samples each (each run takes seconds here)."""

    def test_p2_extra_files_do_not_change_verdict(self):
        rng = random.Random(SEED + 2)
        bad = []
        for base, label in ((b"41\n", "pass"), (b"37\n", "fail"), (b"", "fail")):
            for _ in range(2):
                files = {"out/answer.txt": base, **random_extra_files(rng, rng.randint(1, 3), True)}
                if grader_state(files) != label:
                    bad.append(sorted(files))
        self.assertEqual(bad, [])

    @unittest.expectedFailure  # F1 and F2
    def test_p5_states_without_out_answer_fail(self):
        rng = random.Random(SEED + 5)
        bad = []
        for i in range(6):
            files = random_extra_files(rng, rng.randint(0, 3), False)
            if i % 2 == 0:
                files["answer.txt"] = b"41\n"
            if grader_state(files) != "fail":
                bad.append(sorted(files))
        self.assertEqual(bad, [])

    @unittest.expectedFailure  # F1
    def test_p6_deleting_the_answer_file_fails(self):
        rng = random.Random(SEED + 6)
        bad = []
        for _ in range(3):
            extra = random_extra_files(rng, rng.randint(0, 2), False)
            self.assertEqual(grader_state({"out/answer.txt": b"41\n", **extra}), "pass")
            if grader_state(extra) != "fail":
                bad.append(sorted(extra))
        self.assertEqual(bad, [])

    @unittest.expectedFailure  # F2
    def test_p7_moving_the_answer_file_out_of_out_fails(self):
        self.assertEqual(grader_state({"out/answer.txt": b"41\n"}), "pass")
        self.assertEqual(grader_state({"answer.txt": b"41\n"}), "fail")


class TestScoringProperties(unittest.TestCase):
    def _records(self, rng, codes):
        recs = []
        for i in range(60):
            recs.append({"trial_id": f"r{i:02d}", "task": "count-server-errors",
                         "config": rng.choice(["cfg-a", "cfg-b", "cfg-c"]),
                         "agent_status": rng.choice(["completed", "error", "timeout"]),
                         "agent_error": None, "agent_steps": rng.randint(1, 40),
                         "verifier_exit_code": rng.choice(codes),
                         "verifier_output": rng.choice(["correct", "no answer file", "wrong count: 37", ""])})
        return recs

    def _score_trials(self, recs):
        with tempfile.TemporaryDirectory(prefix="sp_") as td:
            for r in recs:
                os.makedirs(os.path.join(td, r["trial_id"]))
                with open(os.path.join(td, r["trial_id"], "result.json"), "w", encoding="utf-8", newline="\n") as f:
                    json.dump(r, f)
            rows, _out, _err, _code = common.run_scoring(td)
        return rows

    def _contract(self, recs):
        return {c: (t, p, round(100.0 * s, 1)) for c, (t, p, s) in rs.scores(recs).items()}

    def test_p9_reward_ignores_status_and_output(self):
        recs = self._records(random.Random(SEED + 9), [0, 1, 2, 127, 137])
        self.assertEqual(self._score_trials(recs), self._contract(recs))

    @unittest.expectedFailure  # F5
    def test_p10_null_exit_codes_score_zero(self):
        recs = self._records(random.Random(SEED + 10), [0, 1, None])
        self.assertEqual(self._score_trials(recs), self._contract(recs))


if __name__ == "__main__":
    unittest.main()
