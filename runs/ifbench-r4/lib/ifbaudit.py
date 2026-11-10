"""Shared helpers for the IFBench grader audit.

Imports the grader under audit (package `IFBench`, from the byte-identical copy in
audit/work/grader) and the reference (package `ifbench` plus `evaluation_lib`, from
audit/work/reference), with NLTK_DATA pinned to case/deps/nltk_data.

    G: grader under audit (Marin's vendored Evalchemy copy), harness grader.py
    R: reference implementation (allenai/IFBench 1c40f0c), harness evaluation_lib.py
    X: replacement grader (audit/lib/replacement.py)
"""
import copy
import json
import os
import sys

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["NLTK_DATA"] = os.path.join(W, "case", "deps", "nltk_data")
WORK = os.path.join(W, "audit", "work")
for p in (os.path.join(WORK, "grader"), os.path.join(WORK, "reference"), os.path.join(W, "audit", "lib")):
    if p not in sys.path:
        sys.path.insert(0, p)

import nltk  # noqa: E402

nltk.data.path[:] = [os.environ["NLTK_DATA"]]  # no fallback to user-level NLTK data

from IFBench import grader as G_harness  # noqa: E402
from IFBench import instructions_registry as G_registry  # noqa: E402
import evaluation_lib as R_harness  # noqa: E402
from ifbench import instructions_registry as R_registry  # noqa: E402

# grader import inserts its own .nltk_data dir in front; keep only the pinned data
nltk.data.path[:] = [os.environ["NLTK_DATA"]]

ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]
ROW_BY_KEY = {r["key"]: r for r in ROWS}


def nonnull(kw):
    return {k: v for k, v in kw.items() if v is not None}


def row_kwargs(row_index, iid):
    r = ROWS[row_index]
    return nonnull(r["kwargs"][r["instruction_id_list"].index(iid)])


# ---- single-check graders (same logic as each harness's strict path) ----

def check_G(iid, kwargs, response, prompt=""):
    """Strict verdict of the grader under audit for one instruction."""
    inst = G_harness._build_instruction(iid, dict(kwargs), prompt)
    return bool(response and response.strip() and inst.check_following(response))


def check_R(iid, kwargs, response, prompt=""):
    """Strict verdict of the reference for one instruction (evaluation_lib strict path)."""
    cls = R_registry.INSTRUCTION_DICT[iid]
    inst = cls(iid)
    inst.build_description(**nonnull(dict(kwargs)))
    args = inst.get_instruction_args()
    if args and "prompt" in args:
        inst.build_description(prompt=prompt)
    fn = getattr(cls, "_orig_check_following", cls.check_following)  # unpatched (see reftest_plugin.py)
    return bool(response and response.strip() and fn(inst, response))


# ---- per-prompt graders through the real harness functions ----

def grade_G(row, response, loose=False):
    inp = G_harness.InputExample(key=row["key"], instruction_id_list=list(row["instruction_id_list"]),
                                 prompt=row["prompt"], kwargs=copy.deepcopy(row["kwargs"]))
    fn = G_harness.test_instruction_following_loose if loose else G_harness.test_instruction_following_strict
    return fn(inp, {row["prompt"]: response}).follow_instruction_list


def grade_R(row, response, loose=False):
    """Reference harness. Strict filters None kwargs in place; loose relies on that
    (run_eval runs strict first), so loose here is given filtered kwargs as run_eval does."""
    kw = [nonnull(k) for k in row["kwargs"]] if loose else copy.deepcopy(row["kwargs"])
    inp = R_harness.InputExample(key=row["key"], instruction_id_list=list(row["instruction_id_list"]),
                                 prompt=row["prompt"], kwargs=kw)
    fn = R_harness.test_instruction_following_loose if loose else R_harness.test_instruction_following_strict
    return fn(inp, {row["prompt"]: response}).follow_instruction_list


def loose_variants(response):
    """The eight candidate texts both harnesses' loose paths try, in order."""
    lines = response.split("\n")
    rf = "\n".join(lines[1:]).strip()
    rl = "\n".join(lines[:-1]).strip()
    rb = "\n".join(lines[1:-1]).strip()
    return [response, response.replace("*", ""), rf, rl, rb, rf.replace("*", ""), rl.replace("*", ""), rb.replace("*", "")]
