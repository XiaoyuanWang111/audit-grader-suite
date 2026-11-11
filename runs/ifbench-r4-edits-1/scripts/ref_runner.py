"""Run the benchmark authors' pipeline (case/reference/IFBench) in-process.

run_file() replicates run_eval.main: the same `inputs` list goes through
evaluation_lib.test_instruction_following_strict and then
test_instruction_following_loose, in that order (strict filters None kwargs in
place, and loose relies on that). audit/scripts/check_ref_cli.py runs the real
run_eval.py once to confirm the in-process replica gives the same outputs.
"""
import copy

import common  # noqa: F401  (paths)
import evaluation_lib as EL  # case/reference/IFBench/evaluation_lib.py


def _inputs(keys=None):
    rows = common.rows()
    keys = keys or common.row_list()
    return [EL.InputExample(key=r["key"], instruction_id_list=list(r["instruction_id_list"]),
                            prompt=r["prompt"], kwargs=copy.deepcopy(r["kwargs"]))
            for r in (rows[k] for k in keys)]


def run_file(prompt_to_response, keys=None):
    """Return (strict_outputs, loose_outputs) for all rows, as run_eval.main computes them."""
    inputs = _inputs(keys)
    strict = [EL.test_instruction_following_strict(inp, prompt_to_response) for inp in inputs]
    loose = [EL.test_instruction_following_loose(inp, prompt_to_response) for inp in inputs]
    return strict, loose


def grade_reference(check, kw, prompt, response):
    inp = EL.InputExample(key=0, instruction_id_list=[check], prompt=prompt, kwargs=[dict(kw)])
    return EL.test_instruction_following_strict(inp, {prompt: response}).follow_instruction_list[0]


def grade_reference_loose(check, kw, prompt, response):
    inp = EL.InputExample(key=0, instruction_id_list=[check], prompt=prompt, kwargs=[dict(kw)])
    EL.test_instruction_following_strict(inp, {prompt: response})  # filters None kwargs, as in run_eval
    return EL.test_instruction_following_loose(inp, {prompt: response}).follow_instruction_list[0]
