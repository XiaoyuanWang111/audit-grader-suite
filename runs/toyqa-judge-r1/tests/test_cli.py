"""End-to-end fixtures: each pipeline run as the evaluation runs it, as a subprocess, with the fake judge.

Expected labels come from the contract and FakeJudge's documented behaviour (case/judges.py docstring): A when the
predicted answer contains the gold or an alias after normalization, C when it is empty or a refusal, else B.

Run from the audit run's root:  python -I -m unittest discover -s audit/tests -v
"""

import json
import subprocess
import sys
import unittest

from toyqa_audit_lib import CASE, ROOT, WORK, fixture_id, xfail_strict

TMP = WORK / "tests"

# Model "m", one row per question. Contract labels with FakeJudge in the comment.
SCORES_ROWS = [
    ("c01", "q01", "Canberra"),                                                    # correct
    ("c02", "q02", "<think>The treaty ended the Thirty Years' War.</think>1648"),  # correct
    ("c03", "q03", "<think>Tungsten's symbol comes from Wolfram, so it is"),       # extraction_failure (E2)
    ("c04", "q04", "I don't know."),                                               # not_attempted
    ("c05", "q05", "Gabriel Garcia Marquez"),                                      # correct
    ("c06", "q06", "The answer is:\nthe skin"),                                    # correct (R1: both lines)
    ("c07", "q07", "205"),                                                         # incorrect
    ("c08", "q08", "Amazon"),                                                      # correct (alias)
    ("c09", "q09", "Fe"),                                                          # correct (alias)
    ("c10", "q10", "Berlin"),                                                      # correct
    ("c11", "q11", "two"),                                                         # correct (alias)
    ("c12", "q12", "The Pacific Ocean"),                                           # incorrect
]
SCORES_LABELS = {"c01": "correct", "c02": "correct", "c03": "extraction_failure", "c04": "not_attempted",
                 "c05": "correct", "c06": "correct", "c07": "incorrect", "c08": "correct", "c09": "correct",
                 "c10": "correct", "c11": "correct", "c12": "incorrect"}
SCORES_ROW = {"accuracy": 66.7, "cga": 80.0, "f_score": 72.7, "not_att_%": 8.3, "extr_fail": 1, "judge_err": 0}

EMPTY_ROWS = [
    ("e01", "q01", "Canberra"),                                    # correct
    ("e02", "q02", "<think>I could not recall the year.</think>"),  # E5: empty graded text, judge says C
]
EMPTY_LABELS = {"e01": "correct", "e02": "not_attempted"}
EMPTY_ROW = {"accuracy": 8.3, "cga": 100.0, "f_score": 15.4, "not_att_%": 8.3, "extr_fail": 0, "judge_err": 0}

COMMANDS = {
    "grader": lambda responses, out: [sys.executable, "-I", str(CASE / "judge_pipeline.py"), "--judge", "fake",
                                      "--responses", str(responses), "--out", str(out)],
    "replacement": lambda responses, out: [sys.executable, "-I", str(ROOT / "audit" / "replacement" /
                                                                     "toyqa_replacement.py"),
                                           "--judge", "fake", "--responses", str(responses), "--out", str(out)],
    "reference": lambda responses, out: [sys.executable, "-I", str(CASE / "reference" / "pipeline_ref.py"),
                                         str(CASE / "questions.jsonl"), str(responses), "fake", str(out)],
}


def write_responses(name, rows):
    TMP.mkdir(parents=True, exist_ok=True)
    path = TMP / f"{name}.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for rid, qid, text in rows:
            f.write(json.dumps({"id": rid, "model": "m", "question_id": qid, "response": text}) + "\n")
    return path


def run(impl, name, rows):
    """Run one pipeline; return (exit code, printed row for model m as a dict, labels by id)."""
    responses = write_responses(name, rows)
    out = TMP / f"{name}.{impl}.labels.jsonl"
    out.unlink(missing_ok=True)
    proc = subprocess.run(COMMANDS[impl](responses, out), capture_output=True, text=True, encoding="utf-8",
                          cwd=str(ROOT))
    lines = [l.split() for l in proc.stdout.splitlines() if l.strip()]
    row = {}
    if len(lines) >= 2:
        header, values = lines[0][1:], lines[1][1:]
        for key, value in zip(header, values):
            row[key] = float(value) if "." in value else int(value)
    labels = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                labels[d["id"]] = d["label"]
    return proc.returncode, row, labels


def _subset(row, keys):
    return {k: row.get(k) for k in keys}


class Cli(unittest.TestCase):
    pass


CLI_FIXTURES = [
    # (name, rows, expected labels, expected printed values, xfail by implementation)
    ("scores", SCORES_ROWS, SCORES_LABELS, SCORES_ROW, {"grader": "F1 F2"}),
    ("empty", EMPTY_ROWS, EMPTY_LABELS, EMPTY_ROW, {"grader": "F3"}),
]


def _attach():
    for name, rows, labels, printed, xfail in CLI_FIXTURES:
        fid = fixture_id("cli", {"rows": rows})
        for impl in COMMANDS:
            def test(self, impl=impl, name=name, rows=rows, labels=labels, printed=printed):
                code, row, got = run(impl, name, rows)
                self.assertEqual(code, 0, "the run must finish")
                self.assertEqual(got, labels)
                self.assertEqual(_subset(row, printed), printed)
            test.__doc__ = f"{fid} [cli {name}] on {impl}"
            if impl in xfail:
                test = xfail_strict(f"{xfail[impl]}: {fid}")(test)
            setattr(Cli, f"test_{impl}_{fid.replace(':', '_')}", test)


_attach()

if __name__ == "__main__":
    unittest.main()
