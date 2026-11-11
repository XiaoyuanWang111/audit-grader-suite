"""Every fixture against the replacement grader (audit/replacement/ifb_replacement.py) with
all switches at the contract's proposed readings. All must pass."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import graders as G  # noqa: E402
from fixtures import FIXTURES  # noqa: E402


@pytest.mark.parametrize("f", [pytest.param(f, id=f["id"]) for f in FIXTURES])
def test_replacement_matches_contract_label(f):
    got = G.grade_replacement(f["check"], f["kwargs"], f["response"])
    assert ("pass" if got else "fail") == f["label"]
