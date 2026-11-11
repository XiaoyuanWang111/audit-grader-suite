"""Load the grader under audit and the reference from frozen copies and grade.

The copies in audit/frozen/code are byte-identical to case/ (hashes in
audit/ISSUE.md). Importing from case/ directly would write __pycache__ and an
empty .nltk_data folder into case/, so this module never does that.

Network is blocked: nltk.download raises.
"""
import copy
import os
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
os.environ.setdefault("NLTK_DATA", str(W / "case" / "deps" / "nltk_data"))
sys.dont_write_bytecode = True

import nltk  # noqa: E402


def _no_download(*args, **kwargs):
    raise RuntimeError("nltk.download blocked (offline audit)")


nltk.download = _no_download

for p in (W / "audit" / "frozen" / "code" / "grader", W / "audit" / "frozen" / "code" / "reference" / "IFBench"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from IFBench import grader as G  # noqa: E402
from IFBench import instructions_registry as G_REG  # noqa: E402
import evaluation_lib as R  # noqa: E402
from ifbench import instructions_registry as R_REG  # noqa: E402

import pyarrow.parquet as pq  # noqa: E402


def load_rows():
    """Dataset rows with the Python types that `datasets` produces (to_pylist)."""
    rows = pq.read_table(W / "case" / "data" / "train-00000-of-00001.parquet").to_pylist()
    return rows


def row_by_key():
    return {r["key"]: r for r in load_rows()}


def _g_input(row):
    return G.InputExample(key=int(row["key"]), instruction_id_list=list(row["instruction_id_list"]),
                          prompt=row["prompt"], kwargs=copy.deepcopy([dict(k) for k in row["kwargs"]]))


def _r_input(row):
    return R.InputExample(key=int(row["key"]), instruction_id_list=list(row["instruction_id_list"]),
                          prompt=row["prompt"], kwargs=copy.deepcopy([dict(k) for k in row["kwargs"]]))


def _safe(fn, inp, resp_map):
    try:
        return fn(inp, resp_map).follow_instruction_list, None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def grade_row(row, response, which="grader", mode="strict"):
    """Return (list_of_bools or None, error or None) for one dataset row."""
    if which == "grader":
        inp = _g_input(row)
        fn = G.test_instruction_following_strict if mode == "strict" else G.test_instruction_following_loose
    else:
        inp = _r_input(row)
        if mode == "loose":
            # run_eval.py runs strict first, which drops None kwargs in place;
            # loose then reuses the mutated kwargs.
            inp.kwargs = [{k: v for k, v in kw.items() if v is not None} for kw in inp.kwargs]
        fn = R.test_instruction_following_strict if mode == "strict" else R.test_instruction_following_loose
    return _safe(fn, inp, {row["prompt"]: response})


def check_one(iid, kwargs, response, which="grader", prompt="", mode="strict"):
    """Grade one instruction as the strict path does (one-instruction row)."""
    row = {"key": "0", "prompt": prompt or "PROMPT", "instruction_id_list": [iid], "kwargs": [dict(kwargs)]}
    res, err = grade_row(row, response, which=which, mode=mode)
    if err is not None:
        return "EXC:" + err
    return res[0]
