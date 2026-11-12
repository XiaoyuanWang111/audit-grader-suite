"""Regression tests for the generated fixtures in audit/fixtures.jsonl: property and metamorphic
counterexamples, fuzz inputs and content-free responses, each labeled from the contracts.
Current wrong verdicts are xfail(strict=True) (tests/expected_wrong_generated.json)."""
import json
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import harness as h  # noqa: E402

SEED = 20261112
WRONG = {tuple(x) for x in json.load(open(os.path.join(HERE, "expected_wrong_generated.json"), encoding="utf-8"))}

CASES = []
for line in open(os.path.join(os.path.dirname(HERE), "fixtures.jsonl"), encoding="utf-8"):
    d = json.loads(line)
    if d["source"].startswith("hand-written"):
        continue
    for g in ("NV", "VS", "VG", "R"):
        marks = [pytest.mark.xfail(strict=True, reason="current grader wrong")] if (d["id"], g) in WRONG else []
        CASES.append(pytest.param(g, d["instruction_id"], d["kwargs"], d["response"], d["label"], id=f"{g}-{d['id']}", marks=marks))


@pytest.mark.parametrize("grader,iid,kw,resp,label", CASES)
def test_generated(grader, iid, kw, resp, label):
    random.seed(SEED)
    if grader == "NV":
        v = h.nv_check(iid, kw, resp)[0]
    elif grader == "VS":
        v = h.vs_check(iid, kw, resp)[0]
    elif grader == "VG":
        v = h.vg_check(iid, kw, resp)[0]
        if v is None:
            pytest.skip("semantic constraint: judged by the LLM")
    else:
        v = h.R.check(iid, kw, resp)
    assert ("pass" if v else "fail") == label
