"""Regression tests: the grader under audit against contract-labeled fixtures.

Fixtures the current grader gets wrong are marked xfail(strict=True) with the finding or decision id,
so the change that fixes the grader must remove the mark.
Run:  NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests/test_fixtures_grader.py -q
"""
import pytest

from fixture_runner import ALL, verdict


def _params():
    out = []
    for fid, f in ALL:
        marks = []
        if f["grader"]:
            marks.append(pytest.mark.xfail(strict=True, reason=f'{f["grader"]}: {f["note"]}'))
        out.append(pytest.param(f, id=fid, marks=marks))
    return out


@pytest.mark.parametrize("f", _params())
def test_grader_matches_contract(f):
    v = verdict("grader", f)
    assert v == f["label"], f'grader={v} contract={f["label"]} ({f["kind"]} {f["decisions"]}) {f["note"]}'
