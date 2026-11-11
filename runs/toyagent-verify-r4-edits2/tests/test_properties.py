"""Property and metamorphic tests (skill step 4).

Edits that the contract ignores must keep a passing state passing; edits that the contract forbids must make it
fail. Each edit is applied to every passing base state. One test per edit and grader; the test collects every
base state where the verdict is wrong. Edits that the current grader gets wrong are expected failures (strict).
"""

import os
import shutil
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402

BASES = {
    "41 LF": {"out/answer.txt": b"41\n"},
    "41": {"out/answer.txt": b"41"},
    "41 CRLF": {"out/answer.txt": b"41\r\n"},
    "041 LF": {"out/answer.txt": b"041\n"},
}


def _content(state):
    return state["out/answer.txt"]


def _with_content(state, content):
    s = dict(state)
    s["out/answer.txt"] = content
    return s


def _core(state):
    return _content(state).strip(b" \t\r\n")


def _move(state, dest):
    s = dict(state)
    s[dest] = s.pop("out/answer.txt")
    return s


def _delete(state):
    s = dict(state)
    del s["out/answer.txt"]
    return s


def _wrap(prefix, suffix):
    return lambda st: _with_content(st, prefix.encode() + _core(st) + suffix.encode() + b"\n")


IGNORED = {
    "trailing newline": lambda st: _with_content(st, _content(st) + b"\n"),
    "CRLF newline": lambda st: _with_content(st, _core(st) + b"\r\n"),
    "leading spaces": lambda st: _with_content(st, b"   " + _content(st)),
    "trailing spaces and tab": lambda st: _with_content(st, _core(st) + b" \t \n"),
    "blank line before": lambda st: _with_content(st, b"\n" + _content(st)),
    "blank lines after": lambda st: _with_content(st, _core(st) + b"\n\n\n"),
    "unrelated files added": lambda st: dict(st, **{"answer.txt": b"37\n", "tmp/count.py": b"import gzip\n",
                                                   "out/count.sh": b"zcat -f /workspace/logs/* | wc -l\n"}),
}

FORBIDDEN = {
    "answer file deleted": _delete,
    "answer moved to /workspace/answer.txt": lambda st: _move(st, "answer.txt"),
    "answer moved to /workspace/tmp/answer.txt": lambda st: _move(st, "tmp/answer.txt"),
    "count minus one": lambda st: _with_content(st, b"40\n"),
    "count plus one": lambda st: _with_content(st, b"42\n"),
    "numbered label": _wrap("1. ", ""),
    "bullet": _wrap("- ", ""),
    "bold markup": _wrap("**", "**"),
    "italic markup": _wrap("_", "_"),
    "HTML tag": _wrap("<b>", "</b>"),
    "typographic double quotes": _wrap("“", "”"),
    "typographic single quotes": _wrap("‘", "’"),
    "typographic apostrophe inside a word": _wrap("", "’s"),
    "period after the number": _wrap("", "."),
    "comma after the number": _wrap("", ","),
    "word after the number": _wrap("", " requests"),
}

# Edits on which the current grader is expected to be wrong, with the finding that explains it.
CURRENT_WRONG = {
    "answer file deleted": "F1",
    "answer moved to /workspace/answer.txt": "F2",
    "answer moved to /workspace/tmp/answer.txt": "F1",
}


def _check(self, tests_dir, edit, want):
    wrong = []
    for base_name, base in BASES.items():
        state = edit(base)
        ws = harness.materialize(state)
        try:
            code, out = harness.run_verifier(ws, tests_dir)
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        if harness.verdict_of(code) != want:
            wrong.append(f"{base_name}: exit {code} ({out[-60:]!r})")
    self.assertEqual(wrong, [])


def _make(tests_dir, edit, want, name):
    def test(self):
        _check(self, tests_dir, edit, want)

    test.__doc__ = f"{want} after edit: {name}"
    return test


class PropertiesCurrent(unittest.TestCase):
    """Metamorphic tests on case/task/tests/verify.sh."""


class PropertiesReplacement(unittest.TestCase):
    """Metamorphic tests on audit/replacement/tests/verify.sh."""


def _slug(s):
    return "".join(c if c.isalnum() else "_" for c in s.lower())


for _name, _edit in IGNORED.items():
    setattr(PropertiesCurrent, "test_ignored_" + _slug(_name), _make(harness.ORIG_TESTS, _edit, "pass", _name))
    setattr(PropertiesReplacement, "test_ignored_" + _slug(_name), _make(harness.REPL_TESTS, _edit, "pass", _name))
for _name, _edit in FORBIDDEN.items():
    _t = _make(harness.ORIG_TESTS, _edit, "fail", _name)
    if _name in CURRENT_WRONG:
        _t = unittest.expectedFailure(_t)
    setattr(PropertiesCurrent, "test_forbidden_" + _slug(_name), _t)
    setattr(PropertiesReplacement, "test_forbidden_" + _slug(_name), _make(harness.REPL_TESTS, _edit, "fail", _name))


class ScorerIgnoresAgentStatus(unittest.TestCase):
    """The score depends only on verifier_exit_code: changing agent_status or agent_error changes nothing."""

    def _scores(self, scorer, status):
        recs = {}
        for i, code in enumerate([0, 1, 0, 2]):
            recs[f"t{i}"] = {"config": "c", "agent_status": status, "agent_error": None if status == "completed"
                             else "x", "agent_steps": 3, "verifier_exit_code": code, "verifier_output": ""}
        d = harness.write_trials(recs)
        try:
            return harness.run_scorer(d, scorer)[0]
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_current(self):
        base = self._scores(harness.ORIG_SCORER, "completed")
        self.assertEqual(base, {"c": (4, 2, 50.0)})
        for status in ("error", "timeout"):
            self.assertEqual(self._scores(harness.ORIG_SCORER, status), base)

    def test_replacement(self):
        base = self._scores(harness.REPL_SCORER, "completed")
        self.assertEqual(base, {"c": (4, 2, 50.0)})
        for status in ("error", "timeout"):
            self.assertEqual(self._scores(harness.REPL_SCORER, status), base)


if __name__ == "__main__":
    unittest.main()
