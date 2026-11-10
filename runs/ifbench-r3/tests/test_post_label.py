"""Post-label fixtures (fixtures_post_label.py) against the grader, the reference and the replacement.

A wrong verdict carries pytest.mark.xfail(strict=True) with the finding or replacement-error id, so a
fix must remove the mark. These fixtures were written after the review labels were read and are not
part of the 277 step 3 fixtures that the pre-registered rule refers to.
"""
import pytest

import ifb
import ifbench_contract as rep
from fixtures_post_label import POST


def params(attr):
    return [pytest.param(f, id=f.id, marks=[pytest.mark.xfail(strict=True, reason=getattr(f, attr))] if getattr(f, attr) else [])
            for f in POST]


@pytest.mark.parametrize("f", params("grader"))
def test_post_label_grader(f):
    v, err = ifb.verdict("grader", f.check, f.kwargs, f.prompt, f.response)
    assert err is None, err
    assert v == (f.label == "pass")


@pytest.mark.parametrize("f", params("reference"))
def test_post_label_reference(f):
    v, err = ifb.verdict("reference", f.check, f.kwargs, f.prompt, f.response)
    assert err is None, err
    assert v == (f.label == "pass")


@pytest.mark.parametrize("f", params("replacement"))
def test_post_label_replacement(f):
    assert rep.check(f.check, f.kwargs, f.prompt, f.response) == (f.label == "pass")
