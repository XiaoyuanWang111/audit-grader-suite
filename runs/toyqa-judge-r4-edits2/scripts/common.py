"""Shared loaders for the audit scripts and tests. Importing this never writes bytecode into case/."""
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"
AUDIT = W / "audit"

for p in (str(CASE), str(AUDIT / "replacement")):
    if p not in sys.path:
        sys.path.insert(0, p)

import judge_pipeline as grader  # noqa: E402  the pipeline under audit
import judges  # noqa: E402  judge back ends (not under audit)
import toyqa_replacement as replacement  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reference = _load("pipeline_ref", CASE / "reference" / "pipeline_ref.py")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def questions():
    return {q["question_id"]: q for q in load_jsonl(CASE / "questions.jsonl")}


def responses():
    return load_jsonl(CASE / "responses.jsonl")


def template():
    return (CASE / "judge_template.txt").read_text(encoding="utf-8")


class Scripted:
    """A fake judge that returns the given replies in order and records each (prompt, call)."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, call):
        self.calls.append((prompt, call))
        r = self.replies[min(len(self.calls), len(self.replies)) - 1]
        if isinstance(r, BaseException):
            raise r
        return r


def reference_grade(judge, q, response):
    """Run the reference grader; returns (label, judge_calls, first prompt or None)."""
    calls = []

    def wrapped(prompt, call):
        calls.append(prompt)
        return judge(prompt, call)

    g = reference.ToyQAGrader(wrapped, template())
    label = g.label(q, response)
    return label, len(calls), (calls[0] if calls else None)


def predicted_in(prompt):
    """The text between the template's markers in a rendered prompt."""
    return prompt.split("<<<\n", 1)[1].rsplit("\n>>>", 1)[0]
