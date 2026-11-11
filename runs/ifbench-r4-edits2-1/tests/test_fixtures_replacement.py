"""The replacement grader (audit/replacement/contract_grader.py) must pass every fixture under the proposed readings.

Run:  NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -m pytest audit/tests/test_fixtures_replacement.py -q
"""
import pytest

from fixture_runner import ALL, verdict


@pytest.mark.parametrize("f", [pytest.param(f, id=fid) for fid, f in ALL])
def test_replacement_matches_contract(f):
    v = verdict("replacement", f)
    assert v == f["label"], f'replacement={v} contract={f["label"]} {f["note"]}'
