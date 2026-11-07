"""Regression tests for score_trials.py (contract C2, trial verdict from the exit status, and C3, reward and score).

Each fixture is a set of result.json records written to a temporary trials folder under audit/tmp/; the test runs
`python score_trials.py TRIALS_DIR` and compares each configuration's trials, passes and score with the contract:
reward 1 only for verifier_exit_code 0, every trial in the denominator. The script prints the mean reward times 100;
the tests use that unit.

Run: python -I audit/tests/test_scoring.py -v
"""

import concurrent.futures
import hashlib
import json
import os
import pathlib
import shutil
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "scripts")]

import grader_runner as GR  # noqa: E402

MISSING = object()


def rec(i, exit_code, status="completed", config="agentx+test-model"):
    r = {"trial_id": f"x{i:02d}", "task": "count-server-errors", "config": config, "agent_status": status,
         "agent_error": None if status == "completed" else f"{status} in fixture", "agent_steps": 5,
         "verifier_exit_code": exit_code, "verifier_output": ""}
    if exit_code is MISSING:
        del r["verifier_exit_code"]
    return r


def expected_rows(records):
    rows = {}
    for r in records:
        row = rows.setdefault(r["config"], {"trials": 0, "passed": 0})
        row["trials"] += 1
        code = r.get("verifier_exit_code")
        row["passed"] += 1 if (type(code) is int and code == 0) else 0  # C2: only exit status 0 passes
    for row in rows.values():
        row["score"] = round(100.0 * row["passed"] / row["trials"], 1)
    return rows


SCORING_FIXTURES = [
    dict(name="null-exit", records=[rec(1, None, "error")], finding="F3",
         note="the container was lost before the verifier ran (README rule 2: fails)"),
    dict(name="missing-exit-field", records=[rec(1, MISSING, "error")], finding="F3",
         note="no verifier_exit_code at all; the verifier did not report a status"),
    dict(name="exit0-completed", records=[rec(1, 0)]),
    dict(name="exit0-agent-error", records=[rec(1, 0, "error")], note="README rule 2: agent status does not matter"),
    dict(name="exit0-agent-timeout", records=[rec(1, 0, "timeout")]),
    dict(name="exit1", records=[rec(1, 1)]),
    dict(name="exit2-127-137", records=[rec(1, 2), rec(2, 127), rec(3, 137)]),
    dict(name="nine-trials-no-null", records=[rec(i, c, s) for i, (c, s) in enumerate(
        [(0, "completed"), (0, "timeout"), (0, "error"), (1, "completed"), (1, "completed"), (1, "error"),
         (1, "timeout"), (2, "completed"), (1, "completed")])], note="3 of 9 pass; every trial in the denominator"),
    dict(name="nine-trials-one-null", records=[rec(i, c, s) for i, (c, s) in enumerate(
        [(0, "completed"), (0, "completed"), (0, "completed"), (1, "completed"), (1, "completed"),
         (1, "completed"), (None, "error"), (1, "completed"), (1, "completed")])], finding="F3",
         note="3 of 9 pass; the null trial must count as a fail"),
    dict(name="two-configs", records=[rec(1, 0, config="agentx+a"), rec(2, 1, config="agentx+a"),
                                      rec(3, 1, config="agentx+b"), rec(4, 1, config="agentx+b"),
                                      rec(5, 0, config="agentx+b")]),
]
for _fx in SCORING_FIXTURES:
    _fx.setdefault("finding", None)
    _fx.setdefault("note", "")
    _canon = json.dumps([{k: v for k, v in r.items()} for r in _fx["records"]], sort_keys=True)
    _fx["id"] = f"score:{hashlib.sha256(_canon.encode()).hexdigest()[:16]}"

_CACHE = {}


def _run(fx):
    root = GR.new_tmpdir("score_")
    try:
        trials = GR.write_trials(fx["records"], root)
        code, rows, raw = GR.run_score_trials(trials)
        return {"exit": code, "rows": rows, "raw": raw}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def results():
    if not _CACHE:
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("AUDIT_WORKERS", "6"))) as ex:
            futs = {fx["id"]: ex.submit(_run, fx) for fx in SCORING_FIXTURES}
            _CACHE.update({k: v.result() for k, v in futs.items()})
    return _CACHE


class ScoringFixtures(unittest.TestCase):
    pass


def _make(fx):
    def test(self):
        r = results()[fx["id"]]
        self.assertEqual(r["exit"], 0, r["raw"])
        self.assertEqual(r["rows"], expected_rows(fx["records"]), f"{fx['id']}: {r['raw']}")
    if fx["finding"]:
        test = unittest.expectedFailure(test)
    test.__doc__ = f"{fx['id']} {fx['name']} {fx['note']}"
    return test


for _fx in SCORING_FIXTURES:
    setattr(ScoringFixtures, "test_" + _fx["name"].replace("-", "_"), _make(_fx))


if __name__ == "__main__":
    if "--table" in sys.argv:
        for fx in SCORING_FIXTURES:
            r = results()[fx["id"]]
            print(fx["id"], fx["name"], "script:", r["rows"], "contract:", expected_rows(fx["records"]))
    else:
        unittest.main()
