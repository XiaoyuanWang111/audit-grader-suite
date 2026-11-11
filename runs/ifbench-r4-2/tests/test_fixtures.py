"""Regression tests: contract-labeled fixtures against the grader, the reference
and the replacement. A fixture an implementation currently gets wrong is marked
xfail(strict=True), so the change that fixes it must remove the id from
known_wrong.py.

Run (Git Bash, from W):
  NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider audit/tests
"""
import sys
from pathlib import Path

import pytest

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "tests"))
sys.path.insert(0, str(W / "audit" / "replacement"))

import harness as H  # noqa: E402
import ifbench_fixed as RF  # noqa: E402
import known_wrong as KW  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402


def _params(known):
    out = []
    for f in FIXTURES:
        marks = [pytest.mark.xfail(strict=True, reason=f.get("finding") or ",".join(f["dec"]) or "known")] \
            if f["id"] in known else []
        out.append(pytest.param(f, id=f["id"], marks=marks))
    return out


@pytest.mark.parametrize("f", _params(set(KW.GRADER)))
def test_grader(f):
    assert H.check_one(f["check"], f["kwargs"], f["response"], which="grader", prompt=f["prompt"]) is f["label"]


@pytest.mark.parametrize("f", _params(set(KW.REFERENCE)))
def test_reference(f):
    assert H.check_one(f["check"], f["kwargs"], f["response"], which="reference", prompt=f["prompt"]) is f["label"]


@pytest.mark.parametrize("f", _params(set(KW.REPL_PROPOSED)))
def test_replacement_proposed(f):
    assert RF.check(f["check"], f["kwargs"], f["response"], prompt=f["prompt"] or "PROMPT", opts=RF.PROPOSED) is f["label"]


def test_fixture_ids_unique():
    ids = [f["id"] for f in FIXTURES]
    assert len(ids) == len(set(ids))


def test_every_check_has_pass_and_fail_fixture():
    checks = set(H.G_REG.INSTRUCTION_DICT)
    have = {}
    for f in FIXTURES:
        have.setdefault(f["check"], set()).add(f["label"])
    assert set(have) == checks
    assert all(v == {True, False} for v in have.values())
