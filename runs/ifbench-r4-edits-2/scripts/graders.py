"""Uniform entry points to the graders compared in this audit.

- grader:   Marin's vendored copy (case/grader/IFBench), run through its own harness
            grader.test_instruction_following_strict / _loose.
- reference: allenai/IFBench@1c40f0c (case/reference/IFBench), run through its own
            harness evaluation_lib.test_instruction_following_strict / _loose.
- replacement: audit/scripts/replacement.py (built from audit/CONTRACTS.md).

All three are called on byte-identical copies under audit/run/ (see setup_run_copies.py).
Each (prompt, instruction) pair is graded with a single-instruction InputExample so that one
checker exception is recorded for that pair only; both harnesses build every instruction
independently, so the verdicts equal those of the multi-instruction call.
"""
import copy
import hashlib
import os
import random
import sys

W = "<W>"
os.environ["NLTK_DATA"] = W + "/case/deps/nltk_data"

import nltk  # noqa: E402


def _blocked_download(*args, **kwargs):
    raise RuntimeError(f"nltk.download blocked (offline audit): {args!r}")


nltk.download = _blocked_download

RUN = W + "/audit/run"
for p in (RUN + "/grader", RUN + "/reference", W + "/audit/scripts"):
    if p not in sys.path:
        sys.path.insert(0, p)

from IFBench import grader as _g  # noqa: E402
from IFBench import instructions_registry as _g_reg  # noqa: E402
import evaluation_lib as _r  # noqa: E402
from ifbench import instructions_registry as _r_reg  # noqa: E402

for _d in (RUN + "/grader/IFBench/.nltk_data", RUN + "/reference/ifbench/.nltk_data"):
    assert not os.listdir(_d), f"{_d} must stay empty: it precedes NLTK_DATA on nltk.data.path"

ERR = "ERR"


def _call(fn, mod, iid, kwargs, prompt, response):
    random.seed(0)
    inp = mod.InputExample(key=0, instruction_id_list=[iid], prompt=prompt, kwargs=[copy.deepcopy(kwargs)])
    try:
        out = fn(inp, {prompt: response})
        return bool(out.follow_instruction_list[0])
    except Exception as e:  # a grading failure, recorded separately from model accuracy
        return f"{ERR}:{type(e).__name__}:{str(e)[:80]}"


def grader_strict(iid, kwargs, prompt, response):
    return _call(_g.test_instruction_following_strict, _g, iid, kwargs, prompt, response)


def grader_loose(iid, kwargs, prompt, response):
    return _call(_g.test_instruction_following_loose, _g, iid, kwargs, prompt, response)


def reference_strict(iid, kwargs, prompt, response):
    return _call(_r.test_instruction_following_strict, _r, iid, kwargs, prompt, response)


def reference_loose(iid, kwargs, prompt, response):
    # run_eval.py runs strict first, and strict drops None kwargs in place; mirror that.
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    return _call(_r.test_instruction_following_loose, _r, iid, kwargs, prompt, response)


def replacement(iid, kwargs, prompt, response, **switches):
    import replacement as _rep
    try:
        return bool(_rep.check(iid, kwargs, response, prompt=prompt, **switches))
    except Exception as e:
        return f"{ERR}:{type(e).__name__}:{str(e)[:80]}"


GRADERS = {
    "grader_strict": grader_strict,
    "grader_loose": grader_loose,
    "reference_strict": reference_strict,
    "reference_loose": reference_loose,
}

ALL_IDS = sorted(_g_reg.INSTRUCTION_DICT)
assert set(ALL_IDS) <= set(_r_reg.INSTRUCTION_DICT)
