"""Shared helpers: import paths, dataset rows, grading wrappers.

The grader is imported as package `IFBench` (case/grader on sys.path), the
reference as package `ifbench` (case/reference/IFBench on sys.path), as
case/TASK.md describes.
"""
import os
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"
os.environ.setdefault("NLTK_DATA", str(CASE / "deps" / "nltk_data"))
for p in (str(CASE / "grader"), str(CASE / "reference" / "IFBench"), str(W / "audit")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402


def _conv(v):
    try:
        return v.tolist()
    except AttributeError:
        return v


_ROWS = None


def rows():
    """Dataset rows keyed by `key` (str), as Hugging Face `datasets` yields them.

    Arrow `to_pylist()` keeps int64 kwargs (n, m, n_start, n_end) as Python
    ints; pandas would turn them into floats. Checked identical to
    `datasets.Dataset.from_parquet` on 2026-11-10 (see audit/ISSUE.md).
    """
    global _ROWS
    if _ROWS is None:
        import pyarrow.parquet as pq
        t = pq.read_table(CASE / "data" / "train-00000-of-00001.parquet").to_pylist()
        _ROWS = {}
        for r in t:
            _ROWS[str(r["key"])] = dict(
                key=str(r["key"]),
                prompt=r["prompt"],
                instruction_id_list=list(r["instruction_id_list"]),
                kwargs=[dict(kw) for kw in r["kwargs"]],
            )
    return _ROWS


def row_list():
    """Rows in dataset order."""
    import pyarrow.parquet as pq
    return [r["key"] for r in pq.read_table(CASE / "data" / "train-00000-of-00001.parquet", columns=["key"]).to_pylist()]


def kwargs_for(key, check, override=None):
    r = rows()[str(key)]
    i = r["instruction_id_list"].index(check)
    kw = dict(r["kwargs"][i])
    if override:
        kw.update(override)
    return kw, r["prompt"]


def grade_grader(check, kw, prompt, response):
    """Strict verdict of the grader under audit, as grader.test_instruction_following_strict computes it."""
    from IFBench import grader as G
    inst = G._build_instruction(check, kw, prompt)
    return bool(response and response.strip() and inst.check_following(response))


def grade_grader_loose(check, kw, prompt, response):
    from IFBench import grader as G
    inp = G.InputExample(key=0, instruction_id_list=[check], prompt=prompt, kwargs=[kw])
    return G.test_instruction_following_loose(inp, {prompt: response}).follow_instruction_list[0]
