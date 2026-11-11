"""Shared harness: load the grader under audit, the reference, and the replacement; grade one response.

The grader and the reference create a `.nltk_data` directory next to their source at import time,
so they are imported from byte-identical copies under audit/run/ (hashes checked against
case/MANIFEST.sha256 by `verify_copies()`), never from case/.
nltk.download is replaced by a function that raises, so a missing resource can never reach the network.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
CASE = W / "case"
RUN = W / "audit" / "run"
os.environ["NLTK_DATA"] = str(CASE / "deps" / "nltk_data")

import nltk  # noqa: E402


def _no_download(*args, **kwargs):
    raise RuntimeError(f"nltk.download blocked in the audit (args={args})")


nltk.download = _no_download

for p in (str(RUN / "grader"), str(RUN / "reference"), str(W / "audit")):
    if p not in sys.path:
        sys.path.insert(0, p)

COPY_MAP = {
    "grader/IFBench/__init__.py": RUN / "grader/IFBench/__init__.py",
    "grader/IFBench/eval_instruct.py": RUN / "grader/IFBench/eval_instruct.py",
    "grader/IFBench/grader.py": RUN / "grader/IFBench/grader.py",
    "grader/IFBench/instructions.py": RUN / "grader/IFBench/instructions.py",
    "grader/IFBench/instructions_registry.py": RUN / "grader/IFBench/instructions_registry.py",
    "grader/IFBench/instructions_util.py": RUN / "grader/IFBench/instructions_util.py",
    "reference/IFBench/ifbench/__init__.py": RUN / "reference/ifbench/__init__.py",
    "reference/IFBench/ifbench/classic_instructions.py": RUN / "reference/ifbench/classic_instructions.py",
    "reference/IFBench/ifbench/instructions.py": RUN / "reference/ifbench/instructions.py",
    "reference/IFBench/ifbench/instructions_registry.py": RUN / "reference/ifbench/instructions_registry.py",
    "reference/IFBench/ifbench/instructions_util.py": RUN / "reference/ifbench/instructions_util.py",
    "reference/IFBench/evaluation_lib.py": RUN / "reference/evaluation_lib.py",
    "reference/IFBench/run_eval.py": RUN / "reference/run_eval.py",
    "reference/IFBench/instructions_test.py": RUN / "reference/instructions_test.py",
    "reference/IFBench/data/IFBench_test.jsonl": RUN / "reference/data/IFBench_test.jsonl",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest() -> dict:
    out = {}
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, name = line.split(None, 1)
        out[name.lstrip("*")] = h
    return out


def verify_copies() -> list[str]:
    """Return a list of mismatches between the run copies and the manifest (empty = all good)."""
    man = manifest()
    bad = []
    for rel, copy in COPY_MAP.items():
        if man.get(rel) != sha256(copy):
            bad.append(rel)
    return bad


def load_rows() -> list[dict]:
    """Dataset rows with the value types that HF `datasets` returns (int64 -> int, double -> float)."""
    import pyarrow.parquet as pq

    return pq.read_table(CASE / "data/train-00000-of-00001.parquet").to_pylist()


_G = {}


def grader_modules():
    if not _G:
        from IFBench import grader as g, instructions_registry as reg, instructions as ins, instructions_util as util

        _G.update(grader=g, registry=reg, instructions=ins, util=util)
    return _G


_R = {}


def reference_modules():
    if not _R:
        import evaluation_lib as ev
        from ifbench import instructions_registry as reg, instructions as ins

        _R.update(evaluation_lib=ev, registry=reg, instructions=ins)
    return _R


def _input(module, row):
    return module.InputExample(
        key=row["key"],
        instruction_id_list=list(row["instruction_id_list"]),
        prompt=row["prompt"],
        kwargs=[dict(k) for k in row["kwargs"]],
    )


def grade_grader(row: dict, response: str, mode: str = "strict") -> list:
    """Grade with the grader under audit through its own harness (grader.py). Returns per-instruction bools."""
    g = grader_modules()["grader"]
    fn = g.test_instruction_following_strict if mode == "strict" else g.test_instruction_following_loose
    out = fn(_input(g, row), {row["prompt"]: response})
    return list(out.follow_instruction_list)


def grade_reference(row: dict, response: str, mode: str = "strict") -> list:
    """Grade with the reference pipeline (evaluation_lib). Loose runs after strict in run_eval.py, on the
    kwargs that strict has already filtered; this function filters them the same way."""
    ev = reference_modules()["evaluation_lib"]
    inp = _input(ev, row)
    if mode == "strict":
        out = ev.test_instruction_following_strict(inp, {row["prompt"]: response})
    else:
        inp.kwargs = [{k: v for k, v in kw.items() if v is not None} for kw in inp.kwargs]
        out = ev.test_instruction_following_loose(inp, {row["prompt"]: response})
    return list(out.follow_instruction_list)


def build_grader_checker(instruction_id: str, kwargs: dict, prompt: str = ""):
    g = grader_modules()["grader"]
    return g._build_instruction(instruction_id, kwargs, prompt)


def check_grader(instruction_id: str, kwargs: dict, response: str, prompt: str = "") -> bool:
    """Strict verdict of the grader for one instruction (same guard as grader.py)."""
    inst = build_grader_checker(instruction_id, kwargs, prompt)
    return bool(response and response.strip() and inst.check_following(response))


def check_reference(instruction_id: str, kwargs: dict, response: str, prompt: str = "") -> bool:
    reg = reference_modules()["registry"]
    inst = reg.INSTRUCTION_DICT[instruction_id](instruction_id)
    kw = {k: v for k, v in kwargs.items() if v is not None}
    inst.build_description(**kw)
    args = inst.get_instruction_args()
    if args and "prompt" in args:
        inst.build_description(prompt=prompt)
    return bool(response and response.strip() and inst.check_following(response))


def row_by_key(rows, key) -> dict:
    for r in rows:
        if str(r["key"]) == str(key):
            return r
    raise KeyError(key)
