"""Step 3: run every fixture against the grader under audit (strict).

A fixture the grader gets wrong carries pytest.mark.xfail(strict=True) with the finding or
decision id as the reason, so the change that fixes the grader must remove the mark.
Run from W:  PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider audit/tests
"""
import pytest

import ifb
from fixtures_data import FIXTURES

ifb.verify_pins()


def params(attr):
    out = []
    for f in FIXTURES:
        status = getattr(f, attr)
        marks = [pytest.mark.xfail(strict=True, reason=status)] if status else []
        out.append(pytest.param(f, id=f.id, marks=marks))
    return out


@pytest.mark.parametrize("f", params("grader"))
def test_grader_strict(f):
    verdict, error = ifb.verdict("grader", f.check, f.kwargs, f.prompt, f.response)
    assert error is None, error
    assert verdict == (f.label == "pass")
