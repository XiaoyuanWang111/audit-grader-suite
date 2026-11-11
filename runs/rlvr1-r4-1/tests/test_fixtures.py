"""Regression tests: every fixture against the replacement, the SkyRL checker and the verifyit check.

A test asserts the contract label. Tests that the current grader fails are marked
``xfail(strict=True)``, so a grader fix must remove the mark. The marks come from the frozen
audit/tests/fixture_expectations.json (sha256 in audit/ISSUE.md).

Run from W:
  NLTK_DATA=case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider audit/tests
"""
import json
import pathlib
import random
import sys

import pytest

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
sys.path.insert(0, str(W / "audit" / "tests"))

import harness  # noqa: E402
import replacement as rp  # noqa: E402
from fixtures import all_fixtures  # noqa: E402

EXPECT = json.loads((W / "audit" / "tests" / "fixture_expectations.json").read_text(encoding="utf-8"))
BY_ID = {e["id"]: e for e in EXPECT["fixtures"]}
FIXTURES = all_fixtures()


def test_expectations_cover_fixtures():
    assert {f["id"] for f in FIXTURES} == set(BY_ID)


def _param(fx, grader):
    e = BY_ID[fx["id"]]
    marks = []
    if e[grader] is not None and e[grader] != fx["label"]:
        why = e[grader + "_class"] + (": " + ", ".join(e[grader + "_decisions"]) if e[grader + "_decisions"] else "")
        marks.append(pytest.mark.xfail(strict=True, reason=f"{grader} contradicts the contract ({why})"))
    return pytest.param(fx, id=fx["id"], marks=marks)


@pytest.mark.parametrize("fx", [pytest.param(f, id=f["id"]) for f in FIXTURES])
def test_replacement(fx):
    assert rp.check_constraint(fx["check"], fx["kwargs"], fx["text"]) == fx["label"]


@pytest.mark.parametrize("fx", [_param(f, "skyrl") for f in FIXTURES])
def test_skyrl_checker(fx):
    assert harness.skyrl_check(fx["check"], fx["kwargs"], fx["text"]) == fx["label"]


@pytest.mark.parametrize("fx", [_param(f, "verifyit") for f in FIXTURES if f["check"] not in harness.SEMANTIC])
def test_verifyit_check(fx):
    assert harness.curation_check(fx["check"], fx["kwargs"], fx["text"]) == fx["label"]


# ---- graded-text extraction (both pipelines use the same algorithm) ------------------------------

EXT = {e["id"]: e for e in EXPECT["extraction"]}


@pytest.mark.parametrize("eid", sorted(EXT))
def test_extraction_replacement(eid):
    e = EXT[eid]
    assert rp.grade_row(rp.graded_text(e["raw"], e["reasoning_model"]), e["record"])[0] == e["label"]


@pytest.mark.parametrize(
    "eid",
    [pytest.param(k, marks=[pytest.mark.xfail(strict=True, reason="extraction grades text the contract excludes")]
                  if EXT[k]["skyrl_reward"] != EXT[k]["label"] else []) for k in sorted(EXT)],
)
def test_extraction_skyrl(eid):
    e = EXT[eid]
    assert harness.skyrl_grade(e["raw"], e["record"])[0] == e["label"]


@pytest.mark.parametrize(
    "eid",
    [pytest.param(k, marks=[pytest.mark.xfail(strict=True, reason="extraction grades text the contract excludes")]
                  if EXT[k]["gate_passed"] != bool(EXT[k]["label"]) else []) for k in sorted(EXT)],
)
def test_extraction_curation_gate(eid):
    e = EXT[eid]
    assert harness.curation_gate(e["raw"], e["record"])[0] == bool(e["label"])


# ---- the 77 rows whose text asks for paragraph N+1 of N paragraphs -------------------------------

NTH = {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}
NTH_TEXT = "Intro text.\n\nHistory matters."


def test_nth_paragraph_impossible_replacement():
    assert rp.check_constraint("length_constraints:nth_paragraph_first_word", NTH, NTH_TEXT) is False


@pytest.mark.xfail(strict=True, reason="SkyRL draws the checked paragraph at random when nth > num")
def test_nth_paragraph_impossible_skyrl_deterministic_fail():
    verdicts = set()
    for seed in range(20):
        random.seed(seed)
        verdicts.add(harness.skyrl_check("length_constraints:nth_paragraph_first_word", NTH, NTH_TEXT))
    assert verdicts == {False}


def test_nth_paragraph_impossible_verifyit():
    assert harness.curation_check("length_constraints:nth_paragraph_first_word", NTH, NTH_TEXT) is False


# ---- exceptions ----------------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason="an empty answer raises IndexError, which the session reports as INFRA_ERROR")
def test_last_word_answer_empty_has_no_checker_error():
    record = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "limit"}]}
    _, _, errors, _ = harness.skyrl_grade("", record)
    assert errors == [None]


def test_semantic_set_matches_graders_py():
    src = (W / "case" / "grader" / "experiments" / "post_training" / "task_curation" / "datasets" / "nemotron_ultra"
           / "graders.py").read_text(encoding="utf-8")
    block = src[src.index("SEMANTIC_INSTRUCTION_CONSTRAINTS = frozenset("):].split(")", 1)[0]
    assert {s for s in harness.SEMANTIC if f'"{s}"' in block} == set(harness.SEMANTIC)
