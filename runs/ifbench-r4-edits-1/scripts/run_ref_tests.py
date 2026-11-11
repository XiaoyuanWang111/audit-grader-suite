"""Run the reference's unit tests (case/reference/IFBench/instructions_test.py)
against a target checker implementation and list every failing assertion.

Usage: python audit/scripts/run_ref_tests.py {reference|grader|replacement}

The test module does `from ifbench import classic_instructions, instructions`.
For `grader` and `replacement`, a shim package `ifbench` placed first on
sys.path provides `instructions` (the grader's module, or wrapper classes that
call audit/replacement.py). Tests of the classic IFEval checkers are out of
scope (not among the 58) and are skipped for the shims.
Writes audit/work/ref_tests_<target>.json.
"""
import json
import os
import pathlib
import sys
import types
import unittest

W = pathlib.Path(__file__).resolve().parents[2]
os.environ.setdefault("NLTK_DATA", str(W / "case" / "deps" / "nltk_data"))
target = sys.argv[1]
REF = W / "case" / "reference" / "IFBench"
sys.path.insert(0, str(REF))
sys.path.insert(0, str(W / "audit"))
sys.path.insert(0, str(W / "case" / "grader"))

if target != "reference":
    import ifbench.instructions_registry as real_reg  # the real reference registry, for class -> id
    cls2id = {c.__name__: i for i, c in real_reg.INSTRUCTION_DICT.items() if ":" in i and not i.split(":")[0] in (
        "keywords", "language", "length_constraints", "detectable_content", "detectable_format", "combination",
        "startend", "change_case", "punctuation")}
    for m in [m for m in list(sys.modules) if m == "ifbench" or m.startswith("ifbench.")]:
        del sys.modules[m]
    pkg = types.ModuleType("ifbench")
    pkg.__path__ = []
    classic = types.ModuleType("ifbench.classic_instructions")

    def _skip_getattr(name):
        class _Skip:
            def __init__(self, *a, **k):
                raise unittest.SkipTest("classic IFEval checker: out of scope")
        return _Skip
    classic.__getattr__ = _skip_getattr
    if target == "grader":
        from IFBench import instructions as inst
    else:
        import replacement
        inst = types.ModuleType("ifbench.instructions")

        def make(name, check):
            class C:
                CHECK = check

                def __init__(self, instruction_id):
                    self.id = instruction_id
                    self._kw = {}

                def build_description(self, **kwargs):
                    self._kw = {k: v for k, v in kwargs.items() if v is not None}
                    return ""

                def get_instruction_args(self):
                    return dict(self._kw) or None

                def check_following(self, value):
                    return replacement.grade(self.CHECK, self._kw, self._kw.get("prompt", ""), value)
            C.__name__ = name
            return C
        for name, check in cls2id.items():
            setattr(inst, name, make(name, check))
    pkg.instructions = inst
    pkg.classic_instructions = classic
    sys.modules["ifbench"] = pkg
    sys.modules["ifbench.instructions"] = inst
    sys.modules["ifbench.classic_instructions"] = classic

import instructions_test  # noqa: E402


class Rec(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.rows = []

    def addSubTest(self, test, subtest, err):
        self.rows.append(dict(test=test.id().split(".")[-1], sub=subtest._subDescription(),
                              outcome="ok" if err is None else ("fail" if issubclass(err[0], AssertionError) else "error:" + err[0].__name__ + ":" + str(err[1])[:100])))
        super().addSubTest(test, subtest, err)

    def addSuccess(self, test):
        self.rows.append(dict(test=test.id().split(".")[-1], sub="", outcome="ok"))

    def addFailure(self, test, err):
        self.rows.append(dict(test=test.id().split(".")[-1], sub="", outcome="fail", detail=str(err[1])[:200]))

    def addError(self, test, err):
        self.rows.append(dict(test=test.id().split(".")[-1], sub="", outcome="error:" + err[0].__name__ + ":" + str(err[1])[:100]))

    def addSkip(self, test, reason):
        self.rows.append(dict(test=test.id().split(".")[-1], sub="", outcome="skip"))


suite = unittest.TestLoader().loadTestsFromModule(instructions_test)
res = Rec()
suite.run(res)
(W / "audit" / "work" / f"ref_tests_{target}.json").write_text(json.dumps(res.rows, indent=1), encoding="utf-8", newline="\n")
from collections import Counter  # noqa: E402
print(target, Counter(r["outcome"].split(":")[0] for r in res.rows))
for r in res.rows:
    if r["outcome"] not in ("ok", "skip"):
        print(" ", r["test"], "|", r["sub"], "|", r["outcome"])
