"""Grading harness for the audit.

Loads the grader under audit (package ``IFBench``) and the reference (package ``ifbench``) from
verified copies under ``audit/work/`` (importing either package creates a ``.nltk_data`` folder
next to its source, so the audit never imports from ``case/``).

Kwargs are given to the grader exactly as ``eval_instruct.load_questions`` produces them from the
HF parquet: every key present, unset keys ``None``, numbers as ``float``. ``int_cast=True`` casts
integral floats to ``int`` (what the reference's own JSONL gives it), to show the effect.
"""
import json
import os
import sys

W = "<W>"
os.environ.setdefault("NLTK_DATA", f"{W}/case/deps/nltk_data")
for p in (f"{W}/audit/work/grader", f"{W}/audit/work/reference/IFBench"):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402

from IFBench import grader as G  # noqa: E402
from IFBench import instructions_registry as GREG  # noqa: E402
import evaluation_lib as R  # noqa: E402  (reference/IFBench/evaluation_lib.py)
from ifbench import instructions_registry as RREG  # noqa: E402

_DF = None


def dataset():
    """Rows of the parquet as eval_instruct.load_questions builds them (key as str here)."""
    global _DF
    if _DF is None:
        df = pd.read_parquet(f"{W}/case/data/train-00000-of-00001.parquet")
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "key": r["key"],
                "prompt": r["prompt"],
                "instruction_id_list": list(r["instruction_id_list"]),
                "kwargs": [dict(kw) for kw in r["kwargs"]],
            })
        _DF = rows
    return _DF


def row(key):
    for r in dataset():
        if r["key"] == str(key):
            return r
    raise KeyError(key)


def _cast(kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        out[k] = v
    return out


def kwargs_for(key, iid, int_cast=False):
    r = row(key)
    kw = dict(r["kwargs"][r["instruction_id_list"].index(iid)])
    return _cast(kw) if int_cast else kw


def grade(iid, response, key=None, kwargs=None, prompt=None, impl="grader", mode="strict", int_cast=False):
    """Return True/False, or the string 'EXC:<ExceptionType>' when the checker raises.

    The grader's own ``grader.py`` (impl='grader') or the reference's ``evaluation_lib``
    (impl='reference') applies strict or loose grading to a one-instruction input.
    """
    if key is not None:
        r = row(key)
        prompt = r["prompt"] if prompt is None else prompt
        if kwargs is None:
            kwargs = kwargs_for(key, iid, int_cast=int_cast)
    kwargs = dict(kwargs or {})
    if impl == "reference":
        # the reference reads its JSONL: no null keys, ints for indices
        kwargs = {k: v for k, v in _cast(kwargs).items() if v is not None}
        inp = R.InputExample(key=0, instruction_id_list=[iid], prompt=prompt or "", kwargs=[kwargs])
        fn = R.test_instruction_following_strict if mode == "strict" else R.test_instruction_following_loose
    else:
        if int_cast:
            kwargs = _cast(kwargs)
        inp = G.InputExample(key=0, instruction_id_list=[iid], prompt=prompt or "", kwargs=[kwargs])
        fn = G.test_instruction_following_strict if mode == "strict" else G.test_instruction_following_loose
    try:
        out = fn(inp, {inp.prompt: response})
    except Exception as e:  # noqa: BLE001 - an exception is a grading failure, recorded as such
        return f"EXC:{type(e).__name__}"
    return bool(out.follow_instruction_list[0])


def grade_prompt(key, response, impl="grader", mode="strict", int_cast=False):
    """Per-instruction verdicts for one dataset row (list of True/False/'EXC:...')."""
    r = row(key)
    return [grade(iid, response, key=key, impl=impl, mode=mode, int_cast=int_cast)
            for iid in r["instruction_id_list"]]
