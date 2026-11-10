"""Step 4: the same fixtures against the reference implementation (allenai/IFBench 1c40f0c)."""
import pytest

import ifb
from fixtures_data import FIXTURES
from test_fixtures_grader import params


@pytest.mark.parametrize("f", params("reference"))
def test_reference_strict(f):
    verdict, error = ifb.verdict("reference", f.check, f.kwargs, f.prompt, f.response)
    assert error is None, error
    assert verdict == (f.label == "pass")
