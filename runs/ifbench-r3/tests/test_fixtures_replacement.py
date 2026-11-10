"""The replacement grader (audit/replacement/ifbench_contract.py) under the proposed readings must pass every fixture."""
import pytest

import ifbench_contract as rep
from fixtures_data import FIXTURES


@pytest.mark.parametrize("f", [pytest.param(f, id=f.id) for f in FIXTURES])
def test_replacement(f):
    assert rep.check(f.check, f.kwargs, f.prompt, f.response) == (f.label == "pass")
