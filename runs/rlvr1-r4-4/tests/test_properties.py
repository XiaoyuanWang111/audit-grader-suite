"""Metamorphic and forbidden-edit cases (tests/property_cases.json, built from the fixtures by
scripts/make_property_cases.py). Each case is labeled from the contract: a metamorphic edit keeps
the source fixture's label; a forbidden edit of a passing fixture is labeled fail. Cases that a
grader gets wrong today are xfail(strict=True) (tests/known_failures_props.json); a fuzz-found
minimal case list is in tests/fuzz_cases.json.
"""
import json
import os
import random

import pytest

import harness as H

HERE = os.path.dirname(__file__)
CASES = json.load(open(os.path.join(HERE, "property_cases.json"), encoding="utf-8"))
KNOWN = json.load(open(os.path.join(HERE, "known_failures_props.json"), encoding="utf-8"))
FUZZ_PATH = os.path.join(HERE, "fuzz_cases.json")
FUZZ = json.load(open(FUZZ_PATH, encoding="utf-8")) if os.path.exists(FUZZ_PATH) else []


def _params(cases, known):
    for c in cases:
        for g in ("A", "B", "R"):
            if g == "B" and c["instruction_id"] in H.SEMANTIC:
                continue
            reason = known.get(f"{g}|{c['id']}")
            marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
            yield pytest.param(g, c, id=f"{g}-{c['id']}", marks=marks)


def _verdict(g, c):
    random.seed(0)
    if g == "A":
        return H.a_check(c["instruction_id"], c["kwargs"], c["response"])[0]
    if g == "B":
        return H.b_check(c["instruction_id"], c["kwargs"], c["response"])[0]
    return H.r_check(c["instruction_id"], c["kwargs"], c["response"])


@pytest.mark.parametrize("grader,case", list(_params(CASES, KNOWN)))
def test_property_case(grader, case):
    assert ("pass" if _verdict(grader, case) else "fail") == case["label"]


@pytest.mark.parametrize("grader,case", list(_params(FUZZ, {f"{c['grader']}|{c['id']}": c["reason"] for c in FUZZ})))
def test_fuzz_case(grader, case):
    if grader != case["grader"] and grader != "R":
        pytest.skip("fuzz case recorded for the other grader")
    assert ("pass" if _verdict(grader, case) else "fail") == case["label"]
