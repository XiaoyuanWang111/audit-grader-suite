"""Regression tests for the ToyCode grader audit.

Run from the audit run directory:  python -m unittest discover -s audit/tests -v

Each fixture in fixtures.py runs against case/grade.py (the grader under audit), case/reference/harness_ref.py (the
reference) and audit/scripts/contract_grader.py (the replacement, proposed readings). A test that the current code gets
wrong is marked with unittest.expectedFailure, which is strict in Python 3.4+: an unexpected success makes the run fail,
so the change that fixes a grader must remove the mark (the "grader" or "reference" field of the fixture).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
SCRIPTS = os.path.join(ROOT, "audit", "scripts")
for p in (CASE, os.path.join(CASE, "reference"), SCRIPTS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import contract_grader  # noqa: E402
import grade  # noqa: E402  (case/grade.py, the grader under audit)
import harness_ref  # noqa: E402  (case/reference/harness_ref.py)
from fixtures import CORRECT, FIXTURES  # noqa: E402

with open(os.path.join(CASE, "tasks.jsonl"), encoding="utf-8") as _f:
    TASKS = {t["task_id"]: t for t in map(json.loads, filter(str.strip, _f))}
with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as _f:
    TESTS = json.load(_f)

_CACHE = {}


def verdict(which, fixture, decisions=None):
    """'pass', 'fail' or 'crash' (an exception escaped the grader), cached per grader and fixture."""
    key = (which, fixture["id"], json.dumps(decisions, sort_keys=True))
    if key not in _CACHE:
        task, tests, response = TASKS[fixture["task_id"]], TESTS[fixture["task_id"]], fixture["response"]
        try:
            if which == "grader":
                ok, _ = grade.grade_response(task, tests, response)
            elif which == "reference":
                ok = harness_ref.passes(harness_ref.code_of(response), task["entry_point"], tests)
            else:
                ok, _ = contract_grader.grade_response(task, tests, response, decisions)
            _CACHE[key] = "pass" if ok else "fail"
        except Exception as exc:  # noqa: BLE001
            _CACHE[key] = "crash"
            _CACHE[key + ("exc",)] = type(exc).__name__
    return _CACHE[key]


def _make(which, fixture, expected, decisions=None, xfail=False):
    def test(self):
        self.assertEqual(verdict(which, fixture, decisions), expected, fixture["note"])
    test.__doc__ = f"{fixture['id']} [{fixture['shows']}] {fixture['note']}"
    return unittest.expectedFailure(test) if xfail else test


class GraderFixtures(unittest.TestCase):
    """case/grade.py against the contract labels."""


class ReferenceFixtures(unittest.TestCase):
    """case/reference/harness_ref.py against the contract labels."""


class ReplacementFixtures(unittest.TestCase):
    """audit/scripts/contract_grader.py, proposed readings, against the contract labels."""


class ReplacementReadings(unittest.TestCase):
    """Each decision fixture under each reading of its entry."""


class CurrentBehaviour(unittest.TestCase):
    """Snapshot of today's verdicts (pass, fail or crash), so the fixture metadata stays true."""


READING_KEYS = {
    "D-palindrome-normalization": "palindrome", "D-line-terminator": "line_terminator", "D-load-error": "load_error",
    "D-main-guard": "main_guard", "D-dynamic-import": "dynamic_import", "D-numeric-type": "numeric_type",
    "D-eq-object": "eq_object", "D-time-start": "time_start",
}

for _f in FIXTURES:
    _name = "test_" + _f["id"].replace(":", "_").replace("-", "_")
    setattr(GraderFixtures, _name, _make("grader", _f, _f["label"], xfail=_f["grader"] != _f["label"]))
    setattr(ReferenceFixtures, _name, _make("reference", _f, _f["label"], xfail=_f["reference"] != _f["label"]))
    setattr(ReplacementFixtures, _name, _make("replacement", _f, _f["label"], dict(contract_grader.PROPOSED)))
    setattr(CurrentBehaviour, _name + "_grader", _make("grader", _f, _f["grader"]))
    setattr(CurrentBehaviour, _name + "_reference", _make("reference", _f, _f["reference"]))
    if "readings" in _f:
        for _r, _label in _f["readings"].items():
            _d = dict(contract_grader.PROPOSED, **{READING_KEYS[_f["shows"]]: _r})
            setattr(ReplacementReadings, f"{_name}_reading_{_r}", _make("replacement", _f, _label, _d))


# ---------------------------------------------------------------- run level (C-task), through each command line

def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _row(i, task_id, response, model="m"):
    return {"id": f"x{i:02d}", "model": model, "task_id": task_id, "response": response}


def run_cli(which, rows):
    """Run one grader's command line on these rows; return (exit code, verdict rows or None, stdout)."""
    with tempfile.TemporaryDirectory() as tmp:
        responses, out = os.path.join(tmp, "responses.jsonl"), os.path.join(tmp, "verdicts.jsonl")
        _write_jsonl(responses, rows)
        if which == "grader":
            cmd = [sys.executable, os.path.join(CASE, "grade.py"), "--responses", responses, "--out", out]
        elif which == "reference":
            cmd = [sys.executable, os.path.join(CASE, "reference", "harness_ref.py"), os.path.join(CASE, "tasks.jsonl"),
                   os.path.join(CASE, "tests.json"), responses, out]
        else:
            cmd = [sys.executable, os.path.join(SCRIPTS, "contract_grader.py"), "--responses", responses, "--out", out]
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=300)
        verdicts = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                verdicts = [json.loads(l) for l in f if l.strip()]
        return proc.returncode, verdicts, proc.stdout


def score_of(stdout, model="m"):
    for line in stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == model:
            return float(parts[-1])
    return None


CRASH_ROWS = [_row(1, "t07", "```python\n" + CORRECT["t07"] + "```\n"), _row(2, "t07", "-" * 5965),
              _row(3, "t10", "```python\n" + CORRECT["t10"] + "```\n")]
DUPLICATE_ROWS = [_row(1, "t07", "```python\n" + CORRECT["t07"] + "```\n"),
                  _row(2, "t07", "```python\n" + CORRECT["t07"] + "```\n")]
SINGLE_ROW = [_row(1, "t07", "```python\n" + CORRECT["t07"] + "```\n")]


class RunLevel(unittest.TestCase):
    """C-task 2 and 3: one response cannot stop the run; a task counts once; the denominator is 10."""

    def _completes(self, which):
        code, verdicts, _ = run_cli(which, CRASH_ROWS)
        self.assertEqual(code, 0)
        self.assertEqual([v["verdict"] for v in verdicts], ["pass", "fail", "pass"])

    @unittest.expectedFailure
    def test_run_survives_unparsable_response_grader(self):
        self._completes("grader")  # F5: MemoryError from ast.parse ends the whole run, no verdict file

    @unittest.expectedFailure
    def test_run_survives_unparsable_response_reference(self):
        self._completes("reference")

    def test_run_survives_unparsable_response_replacement(self):
        self._completes("replacement")

    def _duplicate_counts_once(self, which):
        code, _, stdout = run_cli(which, DUPLICATE_ROWS)
        self.assertEqual(code, 0)
        self.assertEqual(score_of(stdout), 10.0)

    @unittest.expectedFailure
    def test_duplicate_rows_count_once_grader(self):
        self._duplicate_counts_once("grader")  # F7: prints 20.0

    @unittest.expectedFailure
    def test_duplicate_rows_count_once_reference(self):
        self._duplicate_counts_once("reference")

    def test_duplicate_rows_count_once_replacement(self):
        self._duplicate_counts_once("replacement")

    def test_denominator_is_ten(self):
        for which in ("grader", "reference", "replacement"):
            code, _, stdout = run_cli(which, SINGLE_ROW)
            self.assertEqual((code, score_of(stdout)), (0, 10.0), which)


# ---------------------------------------------------------------- reproducibility (G2): the hash seed is not pinned

ORDER_DEPENDENT = "```python\ndef run_length(s):\n    return \"\".join(f\"{c}{s.count(c)}\" for c in set(s))\n```\n"
SEEDS = range(16)


def verdicts_by_seed(which):
    task, tests = TASKS["t06"], TESTS["t06"]
    saved = os.environ.get("PYTHONHASHSEED")
    out = {}
    try:
        for seed in SEEDS:
            os.environ["PYTHONHASHSEED"] = str(seed)
            if which == "grader":
                out[seed] = grade.grade_response(task, tests, ORDER_DEPENDENT)[0]
            elif which == "reference":
                out[seed] = harness_ref.passes(harness_ref.code_of(ORDER_DEPENDENT), task["entry_point"], tests)
            else:
                out[seed] = contract_grader.grade_response(task, tests, ORDER_DEPENDENT, dict(contract_grader.PROPOSED))[0]
    finally:
        if saved is None:
            os.environ.pop("PYTHONHASHSEED", None)
        else:
            os.environ["PYTHONHASHSEED"] = saved
    return out


class Reproducibility(unittest.TestCase):
    """The same response must get the same verdict whatever the caller's PYTHONHASHSEED is."""

    @unittest.expectedFailure
    def test_hash_seed_grader(self):
        self.assertEqual(len(set(verdicts_by_seed("grader").values())), 1)

    @unittest.expectedFailure
    def test_hash_seed_reference(self):
        self.assertEqual(len(set(verdicts_by_seed("reference").values())), 1)

    def test_hash_seed_replacement(self):
        self.assertEqual(len(set(verdicts_by_seed("replacement").values())), 1)


if __name__ == "__main__":
    unittest.main()
