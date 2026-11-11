"""Fixture regression tests for the ToyQA judge pipeline.

Run from W:  python -B -m unittest discover -s audit/tests -t audit/tests -v

Every fixture runs on three graders: the pipeline under audit (G, case/judge_pipeline.py), the reference
(R, case/reference/pipeline_ref.py) and the replacement (X, audit/replacement/toyqa_replacement.py, proposed
readings). Decision fixtures also run on X with the other reading's switch. A fixture that a grader currently gets
wrong is listed in G_KNOWN or R_KNOWN with its finding or decision; those tests carry unittest.expectedFailure,
which fails the run on an unexpected success (the strict xfail of the skill), so the change that fixes the grader
must remove the entry.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)

from common import Scripted, grader, predicted_in, questions, reference, replacement, template  # noqa: E402
from fixtures import FIXTURES, T1  # noqa: E402

TPL = template()
QS = questions()
QS[T1["question_id"]] = T1

# Fixtures the pipeline under audit gets wrong today (id -> finding or decision).
G_KNOWN = {
    "extract:b30c040723b01f7b": "F1",
    "extract:f787b4c6d5ac2b4e": "F1",
    "extract:234f9f119e45a58d": "D-reopened-think",
    "render:0dfaf661ec6b4719": "F2",
    "render:d76b116f9ff93eb7": "F2",
    "render:6b2cb89f80db48c9": "F2",
    "render:1dd1c32d4249e9fb": "F2",
    "render:52bd4ca35ca5ddb3": "F3",
    "render:f1eb08039cccaa06": "F3",
    "render:79f49042e5c7b0ee": "F3",
    "contentfree:6c7fc240cd574901": "F2",
    "parse:c6bb50c06df79d91": "F4",
    "parse:c9bec71961b8c88c": "F4",
    "parse:c8494ef8e993cc8b": "F4",
    "parse:a8ac45d542666a7c": "F4",
    "parse:7e55d4118f8aa4f9": "F4",
    "parse:e72f7bfdd46eba42": "F4",
    "parse:0ae8510f9f744220": "F4",
    "parse:f65b23b37c8a7483": "F4",
    "parse:55f3b3c1eb8d25b1": "F4",
    "parse:ecf283aa123e17b0": "F4",
    "parse:89eb50049d80c478": "F4",
    "parse:dd7a410ded6c426f": "F4",
    "judgecall:445735392a9f6218": "D-judge-exception",
    "judgecall:ef9b4efe7fea7a44": "D-judge-exception",
}
# Fixtures the reference gets wrong today.
R_KNOWN = {
    "extract:234f9f119e45a58d": "D-reopened-think",
    "judgecall:445735392a9f6218": "D-judge-exception",
    "judgecall:ef9b4efe7fea7a44": "D-judge-exception",
}
ALT_SWITCH = {"D-reopened-think": {"reopened_think": "literal"}, "D-whitespace": {"whitespace": "ascii"},
              "D-judge-window": {"judge_window": "full"}, "D-judge-exception": {"judge_exception": "raise"}}


def _judge(fx):
    replies = [LookupError("judge back end failed") if isinstance(r, dict) else r for r in fx["replies"]]
    return Scripted(*replies)


def run_pipeline(which, fx, opts=None):
    """Return (label, number of judge calls, first prompt or None)."""
    q, j = QS[fx["q"]], _judge(fx)
    if which == "G":
        label = grader.grade_response(j, TPL, q, fx["response"])["label"]
    elif which == "R":
        label = reference.ToyQAGrader(j, TPL).label(q, fx["response"])
    else:
        label = replacement.grade_response(j, TPL, q, fx["response"], opts)["label"]
    return label, len(j.calls), (j.calls[0][0] if j.calls else None)


def run_aggregate(which, fx, per_response=False):
    rows = [{"model": "m", "label": lab} for lab in fx["labels"]]
    if which == "G":
        return grader.aggregate(rows, 12)["m"]
    if which == "R":
        acc, cga, f, na = reference.metrics(list(fx["labels"]), 12)
        return {"accuracy": round(100 * acc, 1), "correct_given_attempted": round(100 * cga, 1),
                "f_score": round(100 * f, 1), "not_attempted_rate": round(100 * na, 1)}
    return replacement.aggregate(rows, 12, per_response=per_response)["m"]


def check(tc, which, fx, expect, opts=None, per_response=False):
    if fx["kind"] == "aggregate":
        got = run_aggregate(which, fx, per_response)
        for k, v in expect.items():
            if which == "R" and k in ("extraction_failure", "judge_error"):
                continue  # the reference's metrics() returns rates only; it prints the counts
            tc.assertEqual(got[k], v, k)
        return
    if "raises" in expect:
        with tc.assertRaises(LookupError):
            run_pipeline(which, fx, opts)
        return
    label, calls, prompt = run_pipeline(which, fx, opts)
    tc.assertEqual(label, expect["label"], "label")
    tc.assertEqual(calls, expect["calls"], "judge calls")
    if expect["predicted"] is None:
        tc.assertIsNone(prompt, "response must not reach the judge")
    else:
        tc.assertEqual(predicted_in(prompt), expect["predicted"], "predicted answer the judge sees")
    if "target" in expect:
        tc.assertIn("\nGold target: " + expect["target"] + "\n", prompt)


def _make(which, fx, expect, known=None, opts=None, per_response=False):
    def test(self):
        check(self, which, fx, expect, opts, per_response)
    if known:
        test = unittest.expectedFailure(test)
    test.__doc__ = f"{fx['id']} {which}" + (f" [known: {known}]" if known else "")
    return test


class TestGrader(unittest.TestCase):
    """The pipeline under audit, case/judge_pipeline.py."""


class TestReference(unittest.TestCase):
    """The reference, case/reference/pipeline_ref.py."""


class TestReplacement(unittest.TestCase):
    """The replacement with the proposed readings."""


class TestReplacementOtherReading(unittest.TestCase):
    """The replacement with the other reading of each decision entry."""


for _fx in FIXTURES:
    _name = "test_" + _fx["id"].replace(":", "_")
    setattr(TestGrader, _name, _make("G", _fx, _fx["expect"], G_KNOWN.get(_fx["id"])))
    setattr(TestReference, _name, _make("R", _fx, _fx["expect"], R_KNOWN.get(_fx["id"])))
    setattr(TestReplacement, _name, _make("X", _fx, _fx["expect"]))
    if "decision" in _fx:
        _d = _fx["decision"]
        setattr(TestReplacementOtherReading, _name,
                _make("X", _fx, _fx["alt"], opts=ALT_SWITCH.get(_d), per_response=(_d == "D-missing-response")))


class TestFixtureBookkeeping(unittest.TestCase):
    def test_known_lists_name_existing_fixtures(self):
        ids = {f["id"] for f in FIXTURES}
        self.assertEqual(set(G_KNOWN) - ids, set())
        self.assertEqual(set(R_KNOWN) - ids, set())

    def test_known_reason_matches_fixture_tag(self):
        by_id = {f["id"]: f for f in FIXTURES}
        for fid, why in G_KNOWN.items():
            self.assertIn(why, (by_id[fid].get("finding"), by_id[fid].get("decision")), fid)


if __name__ == "__main__":
    unittest.main()
