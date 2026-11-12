"""Verdicts of the three graders on one fixture: SkyRL reward, task-curation gate, replacement."""
from __future__ import annotations

import hashlib
import json
import random

import harness as h
from contract_grader import ContractGrader

_CG = ContractGrader()


def fixture_id(iid: str, kwargs: dict, response: str, thinking: bool = False) -> str:
    payload = json.dumps([iid, kwargs, response, thinking], ensure_ascii=False, sort_keys=True)
    return f"{iid}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def verdicts(iid: str, kwargs: dict, response: str, thinking: bool = False, seed: int = 0) -> dict:
    random.seed(seed)  # only nth_paragraph_first_word rows with nth > num draw from it
    s_text = h.skyrl_text(response)
    s_pass, s_err = h.skyrl_check(iid, kwargs, s_text)
    g_text = h.gate_text(response)
    g_pass = h.gate_check(iid, kwargs, g_text)
    r_text = _CG.extract(response, thinking)
    r_pass = _CG.check(iid, kwargs, r_text)
    return {
        "skyrl": "pass" if s_pass else "fail",
        "skyrl_error": s_err,
        "gate": None if g_pass is None else ("pass" if g_pass else "fail"),
        "gate_check_unused": "pass" if h.gate_check_any(iid, kwargs, g_text) else "fail",
        "replacement": "pass" if r_pass else "fail",
    }


def replacement_with(iid, kwargs, response, readings, thinking=False):
    cg = ContractGrader(readings)
    return "pass" if cg.check(iid, kwargs, cg.extract(response, thinking)) else "fail"
