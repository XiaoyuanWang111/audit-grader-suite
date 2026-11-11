"""Run-level tests: the pipelines as the evaluation runs them, through their command lines.

Run from W:  python -B -m unittest discover -s audit/tests -t audit/tests -v
Needs the files from `python -B audit/tests/make_data.py` (kept in audit/tests/data/).
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

from common import CASE, W, judges, questions, replacement, responses, template  # noqa: E402

DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "_out")
os.makedirs(OUT, exist_ok=True)


def run(args):
    return subprocess.run([sys.executable, "-B", *args], cwd=W, capture_output=True, text=True, encoding="utf-8")


def read_labels(path):
    with open(path, encoding="utf-8") as f:
        return {json.loads(l)["id"]: json.loads(l)["label"] for l in f if l.strip()}


def contract_labels():
    rec, tpl, qs = judges.RecordedJudge(CASE / "judge_replies.jsonl"), template(), questions()
    return {r["id"]: replacement.grade_response(rec, tpl, qs[r["question_id"]], r["response"])["label"]
            for r in responses()}


class TestGraderCLI(unittest.TestCase):
    @unittest.expectedFailure  # F3: IndexError on an empty graded text stops the whole run
    def test_empty_response_does_not_stop_run(self):
        out = os.path.join(OUT, "grader_empty_in_batch.jsonl")
        p = run(["case/judge_pipeline.py", "--judge", "fake", "--responses",
                 os.path.join(DATA, "empty_in_batch.jsonl"), "--out", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(len(read_labels(out)), 3)

    @unittest.expectedFailure  # F1: unclosed reasoning is labeled not_attempted
    def test_unclosed_reasoning_is_extraction_failure(self):
        out = os.path.join(OUT, "grader_f1.jsonl")
        p = run(["case/judge_pipeline.py", "--judge", "fake", "--responses",
                 os.path.join(DATA, "f1_unclosed_think.jsonl"), "--out", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(read_labels(out), {"f1": "extraction_failure"})

    @unittest.expectedFailure  # F1 and F4: 10 of 48 stored verdicts differ from the contract pipeline
    def test_stored_panel_matches_contract_pipeline(self):
        out = os.path.join(OUT, "grader_panel.jsonl")
        p = run(["case/judge_pipeline.py", "--out", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(read_labels(out), contract_labels())


class TestReferenceCLI(unittest.TestCase):
    def test_empty_response_does_not_stop_run(self):
        out = os.path.join(OUT, "ref_empty_in_batch.jsonl")
        p = run(["case/reference/pipeline_ref.py", "case/questions.jsonl",
                 os.path.join(DATA, "empty_in_batch.jsonl"), "fake", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(len(read_labels(out)), 3)

    def test_unclosed_reasoning_is_extraction_failure(self):
        out = os.path.join(OUT, "ref_f1.jsonl")
        p = run(["case/reference/pipeline_ref.py", "case/questions.jsonl",
                 os.path.join(DATA, "f1_unclosed_think.jsonl"), "fake", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(read_labels(out), {"f1": "extraction_failure"})

    def test_stored_panel_matches_contract_pipeline(self):
        out = os.path.join(OUT, "ref_panel.jsonl")
        p = run(["case/reference/pipeline_ref.py", "case/questions.jsonl", "case/responses.jsonl", "recorded", out])
        self.assertEqual(p.returncode, 0, p.stderr[-300:])
        self.assertEqual(read_labels(out), contract_labels())


if __name__ == "__main__":
    unittest.main()
