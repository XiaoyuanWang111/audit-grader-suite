"""Shared helpers for the ToyQA judge-pipeline audit.

- Paths, the pinned judge template and questions.
- The three implementations under test, behind one adapter interface:
  `GRADER` (case/judge_pipeline.py, under audit), `REFERENCE` (case/reference/pipeline_ref.py) and
  `REPLACEMENT` (audit/replacement/toyqa_replacement.py, the contract in audit/CONTRACT.md).
- The contract oracle for property tests and fuzzing: the replacement's functions, which were written from the
  contract and not from either pipeline. Fixtures never use the oracle; their labels are written out literally.
- Judge stand-ins: `ScriptedJudge` (fixed replies per call, records every call) and `CountingJudge` (wraps a judge).
"""

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "case"
WORK = ROOT / "audit" / "work"
if str(CASE) not in sys.path:
    sys.path.insert(0, str(CASE))

import judge_pipeline as grader_module  # noqa: E402  the grader under audit
import judges  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference_module = _load("pipeline_ref", CASE / "reference" / "pipeline_ref.py")
replacement_module = _load("toyqa_replacement", ROOT / "audit" / "replacement" / "toyqa_replacement.py")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


TEMPLATE = (CASE / "judge_template.txt").read_text(encoding="utf-8")
QUESTIONS = {q["question_id"]: q for q in load_jsonl(CASE / "questions.jsonl")}
N_QUESTIONS = 12
LABELS = ("correct", "incorrect", "not_attempted", "extraction_failure", "judge_error")

assert TEMPLATE.count("{") == 3 and TEMPLATE.count("}") == 3, "template has braces besides the 3 placeholders"

# The contract oracle (see the module docstring).
contract_graded_text = replacement_module.extract_graded_text
contract_target = replacement_module.format_target
contract_parse = replacement_module.parse_grade
fill = replacement_module.fill


def contract_prompt(question, graded_text):
    return replacement_module.render_prompt(TEMPLATE, question, graded_text)


def contract_grade(judge, question, response):
    return replacement_module.grade_response(judge, TEMPLATE, question, response)


def contract_scores(labels, n=N_QUESTIONS):
    """G1-G5 for one model's labels, as unrounded fractions plus the label counts."""
    c = Counter(labels)
    accuracy = c["correct"] / n
    attempted = c["correct"] + c["incorrect"]
    cga = c["correct"] / attempted if attempted else 0.0
    f = 2 * accuracy * cga / (accuracy + cga) if accuracy + cga else 0.0
    return {"accuracy": accuracy, "cga": cga, "f_score": f, "not_attempted_rate": c["not_attempted"] / n,
            **{label: c[label] for label in LABELS}}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fixture_id(stage, inputs):
    """Stage name plus the first 16 hex digits of the sha256 of the fixture's inputs."""
    blob = json.dumps({"stage": stage, "inputs": inputs}, sort_keys=True, ensure_ascii=False)
    return f"{stage}:{hashlib.sha256(blob.encode('utf-8')).hexdigest()[:16]}"


def expected_prompt(question, target, predicted):
    """The prompt R1-R4 call for, from the values a fixture states."""
    return fill(TEMPLATE, question["question"], target, predicted)


# ---------------------------------------------------------------------------------------------------------------
# Judge stand-ins.

class ScriptedJudge:
    """Replies with replies[call - 1]; records (call, prompt) for every call; a call past the script fails."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, call):
        self.calls.append((call, prompt))
        if not 1 <= call <= len(self.replies):
            raise AssertionError(f"unexpected judge call {call}")
        return self.replies[call - 1]


class CountingJudge:
    """Wraps a judge and records (call, prompt) for every call."""

    def __init__(self, judge):
        self.judge = judge
        self.calls = []

    def __call__(self, prompt, call):
        self.calls.append((call, prompt))
        return self.judge(prompt, call)


# ---------------------------------------------------------------------------------------------------------------
# One adapter per implementation. label() returns (label, number of judge calls); scores() a percent row.

class _PipelineImpl:
    """Adapter for a module with judge_pipeline.py's interface (the grader and the replacement)."""

    def __init__(self, name, module):
        self.name = name
        self.module = module

    def extract(self, response):
        return self.module.extract_graded_text(response)

    def render(self, question, graded_text):
        return self.module.render_prompt(TEMPLATE, question, graded_text)

    def parse(self, reply):
        return self.module.parse_grade(reply)

    def label(self, judge, question, response):
        r = self.module.grade_response(judge, TEMPLATE, question, response)
        return r["label"], r["judge_calls"]

    def scores(self, labels):
        rows = [{"model": "m", "label": label} for label in labels]
        t = self.module.aggregate(rows, N_QUESTIONS)["m"]
        return {"accuracy": t["accuracy"], "cga": t["correct_given_attempted"], "f_score": t["f_score"],
                "not_attempted_rate": t["not_attempted_rate"], **{label: t[label] for label in LABELS}}


class _ReferenceImpl:
    name = "reference"

    def extract(self, response):
        return reference_module.ToyQAGrader.answer_text(response)

    def render(self, question, graded_text):
        return reference_module.ToyQAGrader(None, TEMPLATE).prompt(question, graded_text)

    def parse(self, reply):
        return reference_module.ToyQAGrader.grade_of(reply)

    def label(self, judge, question, response):
        counting = CountingJudge(judge)
        label = reference_module.ToyQAGrader(counting, TEMPLATE).label(question, response)
        return label, len(counting.calls)

    def scores(self, labels):
        acc, cga, f, na = reference_module.metrics(list(labels), N_QUESTIONS)
        c = Counter(labels)
        return {"accuracy": round(100 * acc, 1), "cga": round(100 * cga, 1), "f_score": round(100 * f, 1),
                "not_attempted_rate": round(100 * na, 1), **{label: c[label] for label in LABELS}}


GRADER = _PipelineImpl("grader", grader_module)
REFERENCE = _ReferenceImpl()
REPLACEMENT = _PipelineImpl("replacement", replacement_module)
IMPLS = (GRADER, REFERENCE, REPLACEMENT)


def xfail_strict(reason):
    """pytest.mark.xfail(strict=True) when pytest is installed, else unittest.expectedFailure, which is also strict:
    an unexpected success makes the run fail."""
    try:
        import pytest
    except ImportError:
        import unittest
        return unittest.expectedFailure
    return pytest.mark.xfail(strict=True, reason=reason)
