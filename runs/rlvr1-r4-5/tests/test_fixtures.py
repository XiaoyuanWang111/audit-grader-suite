"""Regression tests: every fixture, labeled from the contracts, against every grader.

Graders: NV (SkyRL default reward, NVIDIA checkers), VS (SkyRL with verifyit_enabled),
VG (task-curation deterministic gate, verifyit checks), R (replacement grader, proposed readings).
A (fixture, grader) pair that the current grader gets wrong is marked xfail(strict=True), so the
change that fixes the grader must remove the mark (audit/tests/expected_wrong.json).

Run:  cd audit && ../.venv/Scripts/python.exe -m pytest -q tests
"""
import json
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import harness as h  # noqa: E402
from fixture_defs import FIXTURES, PIPELINE  # noqa: E402
from run_ids import fid  # noqa: E402

SEED = 20261112
WRONG = {tuple(x) for x in json.load(open(os.path.join(HERE, "expected_wrong.json"), encoding="utf-8"))}


def lab(b):
    return "pass" if b else "fail"


def _verdict(grader, iid, kw, resp):
    random.seed(SEED)  # NVIDIA's build_description can draw from the global RNG (finding F-NTH-RANDOM)
    if grader == "NV":
        return lab(h.nv_check(iid, kw, resp)[0])
    if grader == "VS":
        return lab(h.vs_check(iid, kw, resp)[0])
    if grader == "VG":
        v = h.vg_check(iid, kw, resp)[0]
        return None if v is None else lab(v)
    return lab(h.R.check(iid, kw, resp))


def _pipeline_verdict(grader, iid, kw, raw, thinking):
    random.seed(SEED)
    record = {"instruction_id_list": [iid], "kwargs": [kw]}
    if grader == "NV":
        r = h.nv_row(raw, record)
        return lab(r["results"][0] and r["outcome"] == "graded")
    if grader == "VS":
        v = h.vs_row(h.final_answer_text(raw), record)
        return lab(v["status"] == "scored" and v["detail"]["source_feedback"]["follow_instruction_list"][0])
    if grader == "VG":
        v = h.vg_row(raw, record)["results"][0]
        return None if v is None else lab(v)
    return lab(h.r_row(raw, record, thinking)["results"][0])


CASES = []
for iid, kw, resp, label, deps, note in FIXTURES:
    i = fid(iid, kw, resp)
    for g in ("NV", "VS", "VG", "R"):
        marks = [pytest.mark.xfail(strict=True, reason="current grader wrong")] if (i, g) in WRONG else []
        CASES.append(pytest.param(g, iid, kw, resp, label, id=f"{g}-{i}", marks=marks))

PCASES = []
for iid, kw, raw, thinking, label, deps, note in PIPELINE:
    i = fid(iid, kw, raw, "pipeline-thinking" if thinking else "pipeline")
    for g in ("NV", "VS", "VG", "R"):
        marks = [pytest.mark.xfail(strict=True, reason="current grader wrong")] if (i, g) in WRONG else []
        PCASES.append(pytest.param(g, iid, kw, raw, thinking, label, id=f"{g}-{i}", marks=marks))


@pytest.mark.parametrize("grader,iid,kw,resp,label", CASES)
def test_fixture(grader, iid, kw, resp, label):
    v = _verdict(grader, iid, kw, resp)
    if v is None:
        pytest.skip("semantic constraint: judged by the LLM, no deterministic check")
    assert v == label


@pytest.mark.parametrize("grader,iid,kw,raw,thinking,label", PCASES)
def test_pipeline_fixture(grader, iid, kw, raw, thinking, label):
    v = _pipeline_verdict(grader, iid, kw, raw, thinking)
    if v is None:
        pytest.skip("semantic constraint")
    assert v == label
