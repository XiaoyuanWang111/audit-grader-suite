"""Verdict of each grader on one constraint of a raw (non-reasoning) response, as each pipeline computes it."""

import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AUDIT not in sys.path:
    sys.path.insert(0, AUDIT)

import harness  # noqa: E402
import replacement  # noqa: E402

GRADERS = ("nvidia", "verifyit", "replacement")


def verdict(grader: str, check: str, kwargs, response: str, reasoning: bool = False):
    """True/False, or None when the grader does not grade this check (verifyit's gate skips semantic checks).
    nvidia returns ("error", message) as False with the error kept separately by `nvidia_detail`."""
    harness.setup()
    if grader == "nvidia":
        return harness.skyrl_constraint(check, kwargs, harness.final_answer_text(response))[0]
    if grader == "verifyit":
        if check in harness.SEMANTIC:
            return None
        return bool(harness.verifyit_constraint(check, kwargs, harness.curation_answer_text(response))[0])
    if grader == "replacement":
        return replacement.check(check, kwargs, replacement.graded_text(response, reasoning))
    raise ValueError(grader)


def nvidia_error(check: str, kwargs, response: str):
    harness.setup()
    return harness.skyrl_constraint(check, kwargs, harness.final_answer_text(response))[1]
