"""Uniform access to the grader under audit, the reference, and the replacement.

All three are called through their own harness code where one exists:
- grader:    IFBench.grader.test_instruction_following_strict / _loose  (Marin's vendored copy)
- reference: evaluation_lib.test_instruction_following_strict / _loose  (allenai/IFBench @1c40f0c)
- replacement: audit/replacement/ifb_replacement.py (contracts, one switch per decision)

Import from verbatim copies under audit/work/pkgs (made by audit/scripts/s3_copy_pkgs.py).
"""
import copy
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
sys.dont_write_bytecode = True
for p in [os.path.join(W, "audit", "work", "pkgs", "grader"),
          os.path.join(W, "audit", "work", "pkgs", "reference"),
          os.path.join(W, "audit", "replacement")]:
    if p not in sys.path:
        sys.path.insert(0, p)

DOUBLE_FIELDS = {"N", "small_n", "percentage", "min_words", "max_words"}


def dataset_types(kwargs):
    """Give kwargs the types the parquet/datasets path delivers (double fields as float)."""
    out = {}
    for k, v in kwargs.items():
        if v is None:
            continue
        out[k] = float(v) if (k in DOUBLE_FIELDS and isinstance(v, (int, float))) else v
    return out


_G = None
_R = None


def grader_mod():
    global _G
    if _G is None:
        from IFBench import grader as g  # noqa
        _G = g
    return _G


def reference_mod():
    global _R
    if _R is None:
        import evaluation_lib as r  # noqa
        _R = r
    return _R


def _prompt_for(check, kwargs):
    return f"<fixture prompt for {check} {sorted(kwargs.items())!r}>"


def grade_grader(check, kwargs, response, prompt=None, loose=False):
    g = grader_mod()
    prompt = prompt if prompt is not None else _prompt_for(check, kwargs)
    inp = g.InputExample(key=0, instruction_id_list=[check], prompt=prompt,
                         kwargs=[dataset_types(kwargs)])
    fn = g.test_instruction_following_loose if loose else g.test_instruction_following_strict
    return fn(inp, {prompt: response}).follow_instruction_list[0]


def grade_reference(check, kwargs, response, prompt=None, loose=False):
    r = reference_mod()
    prompt = prompt if prompt is not None else _prompt_for(check, kwargs)
    inp = r.InputExample(key=0, instruction_id_list=[check], prompt=prompt,
                         kwargs=[copy.deepcopy(dataset_types(kwargs))])
    if loose:
        # run_eval.py runs strict first on the same InputExample objects; strict drops None
        # kwargs in place, loose then reuses them. dataset_types already dropped None.
        return r.test_instruction_following_loose(inp, {prompt: response}).follow_instruction_list[0]
    return r.test_instruction_following_strict(inp, {prompt: response}).follow_instruction_list[0]


def grade_replacement(check, kwargs, response, prompt=None, switches=None):
    import ifb_replacement as rep  # noqa
    return rep.check(check, dataset_types(kwargs), response, prompt=prompt, switches=switches)
