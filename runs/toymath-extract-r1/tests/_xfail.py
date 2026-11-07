"""Strict expected-failure marker that works with or without pytest.

With pytest installed, xfail(reason) is pytest.mark.xfail(strict=True, reason=reason). Without it (this
offline run has no pytest), it is unittest.expectedFailure, which also fails the run on an unexpected success
(TestResult.wasSuccessful() is False when unexpectedSuccesses is non-empty). Either way, the change that fixes
the grader must remove the mark.
"""
import unittest

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None


def xfail(reason):
    if pytest is not None:
        return pytest.mark.xfail(strict=True, reason=reason)

    def deco(fn):
        fn = unittest.expectedFailure(fn)
        fn.__doc__ = "xfail(strict): " + reason
        return fn
    return deco
