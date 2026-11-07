"""Step 4: the command line, run as TASK.md says ("from this directory": case/).

Contract section 6: the command grades every rollout against the reference with the same
order_id, prints each checkpoint's mean and full-reward count, and with --out writes one line
per rollout; one bad response must not stop the run.
"""
import json
import subprocess
import sys
import unittest

from support import REFS, ROOT, grader, xfail_strict

CASE = ROOT / "case"
WORK = ROOT / "audit" / "runs" / "cli"


def run_cli(*args):
    WORK.mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-I", "-B", "reward.py", *args], cwd=CASE, capture_output=True, text=True)


def write_rows(name, rows):
    path = WORK / name
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


GOOD = ('{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, '
        '{"sku": "CD-220", "qty": 1}], "total": 64.50}')


class CommandLine(unittest.TestCase):
    def test_default_run_matches_reward_function(self):
        res = run_cli()
        self.assertEqual(res.returncode, 0, res.stderr)
        printed = {}
        for line in res.stdout.splitlines()[1:]:
            ckpt, n, mean, full = line.split()
            printed[ckpt] = (int(n), float(mean), int(full))
        rows = [json.loads(l) for l in open(CASE / "responses.jsonl", encoding="utf-8") if l.strip()]
        by = {}
        for r in rows:
            by.setdefault(r["checkpoint"], []).append(grader.reward(r["response"], REFS[r["order_id"]]))
        for ckpt, rs in by.items():
            n, mean, full = printed[ckpt]
            self.assertEqual(n, len(rs))
            self.assertAlmostEqual(mean, sum(rs) / len(rs), places=3)
            self.assertEqual(full, sum(x == 1.0 for x in rs))

    def test_out_has_one_line_per_rollout_keyed_by_id(self):
        path = write_rows("two_rows.jsonl", [
            {"id": "a", "checkpoint": "c", "order_id": "o01", "response": GOOD},
            {"id": "b", "checkpoint": "c", "order_id": "o06", "response": GOOD},
        ])
        out = WORK / "two_rows_rewards.jsonl"
        res = run_cli("--responses", str(path), "--out", str(out))
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = [json.loads(l) for l in open(out, encoding="utf-8")]
        self.assertEqual([l["id"] for l in lines], ["a", "b"])
        self.assertEqual([l["reward"] for l in lines], [1.0, 0.0])

    @xfail_strict("F2: one response whose JSON value is not an object stops the whole run")
    def test_one_bad_response_does_not_stop_the_run(self):
        path = write_rows("one_bad_row.jsonl", [
            {"id": "a", "checkpoint": "c", "order_id": "o01", "response": GOOD},
            {"id": "b", "checkpoint": "c", "order_id": "o01", "response": "[]"},
        ])
        out = WORK / "one_bad_row_rewards.jsonl"
        if out.exists():
            out.unlink()
        res = run_cli("--responses", str(path), "--out", str(out))
        self.assertEqual(res.returncode, 0, res.stderr[-300:])
        self.assertEqual(len(open(out, encoding="utf-8").readlines()), 2)


if __name__ == "__main__":
    unittest.main()
