"""Regression tests: every labeled fixture against the current grader and the replacement.

Run from the audit directory's parent:  python -B -m unittest discover -s audit/tests -v

Fixtures that the current grader gets wrong are unittest.expectedFailure, which is strict: an unexpected success
makes the run fail (pytest reports it the same way for unittest-style tests), so the change that fixes the grader
must remove the mark. pytest is not installed in this offline environment, hence unittest.
"""

import os
import shutil
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
import harness  # noqa: E402

FLIP = {
    "D-surrounding-text": ("D_SURROUNDING_TEXT", "embedded"),
    "D-whitespace": ("D_WHITESPACE", "unicode"),
    "D-leading-zeros": ("D_LEADING_ZEROS", "forbid"),
    "D-plus-sign": ("D_PLUS_SIGN", "allow"),
    "D-nonascii-digits": ("D_NONASCII_DIGITS", "allow"),
}


def _method_name(prefix, fid, suffix=""):
    return f"test_{prefix}_{fid.replace(':', '_')}{suffix}"


def _verifier_test(fx, tests_dir, extra_env=None, want=None):
    want = want or fx["label"]

    def test(self):
        ws = harness.materialize(fx["files"])
        try:
            code, out = harness.run_verifier(ws, tests_dir, extra_env)
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        self.assertEqual(harness.verdict_of(code), want, f"{fx['name']}: exit {code}, output {out[-200:]!r}")

    test.__doc__ = fx["name"]
    return test


def _scorer_test(fx, scorer):
    def test(self):
        d = harness.write_trials(fx["trials"])
        try:
            table, out, rc = harness.run_scorer(d, scorer)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(rc, 0, out)
        self.assertEqual(table, fx["label"], f"{fx['name']}: {out!r}")

    test.__doc__ = fx["name"]
    return test


class VerifierCurrent(unittest.TestCase):
    """case/task/tests/verify.sh on every verifier fixture."""


class VerifierReplacement(unittest.TestCase):
    """audit/replacement/tests/verify.sh on every verifier fixture, proposed readings and each flipped reading."""


class ScorerCurrent(unittest.TestCase):
    """case/score_trials.py on every scorer fixture."""


class ScorerReplacement(unittest.TestCase):
    """audit/replacement/score_trials.py on every scorer fixture."""


for _fx in fixtures.VERIFIER:
    _fid = harness.state_id("verifier", _fx["files"])
    _t = _verifier_test(_fx, harness.ORIG_TESTS)
    if _fx.get("current"):
        _t = unittest.expectedFailure(_t)
    setattr(VerifierCurrent, _method_name("current", _fid), _t)
    setattr(VerifierReplacement, _method_name("replacement", _fid), _verifier_test(_fx, harness.REPL_TESTS))
    for _dec, _alt in _fx.get("alt", {}).items():
        _var, _val = FLIP[_dec]
        setattr(VerifierReplacement, _method_name("replacement", _fid, "_" + _var.lower() + "_" + _val),
                _verifier_test(_fx, harness.REPL_TESTS, {_var: _val}, _alt))

for _fx in fixtures.SCORER:
    _fid = harness.state_id("score", {k: repr(v).encode() for k, v in _fx["trials"].items()})
    _t = _scorer_test(_fx, harness.ORIG_SCORER)
    if _fx.get("current"):
        _t = unittest.expectedFailure(_t)
    setattr(ScorerCurrent, _method_name("current", _fid), _t)
    setattr(ScorerReplacement, _method_name("replacement", _fid), _scorer_test(_fx, harness.REPL_SCORER))


if __name__ == "__main__":
    unittest.main()
