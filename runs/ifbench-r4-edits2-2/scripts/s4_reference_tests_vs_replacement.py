"""Step 4: run the reference's unit tests (instructions_test.py) against the replacement.

A shim package named `ifbench` exposes adapter classes with the reference's class names;
each adapter records build_description(**kwargs) and answers check_following(value) with
the replacement grader (all switches at the proposed readings). Tests of the classic IFEval
checkers are skipped (not part of the 58 IFBench checks). Every failing assertion is
printed with its line number and the subTest label, and written to
audit/work/reference_tests_vs_replacement.json.

Run from W: .venv/Scripts/python.exe audit/scripts/s4_reference_tests_vs_replacement.py
"""
import importlib.util
import json
import os
import re
import sys
import traceback
import types
import unittest

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(W, "audit", "replacement"))
import ifb_replacement as rep  # noqa: E402

reg = open(os.path.join(W, "case", "reference", "IFBench", "ifbench", "instructions_registry.py"), encoding="utf-8").read()
CLASS_TO_ID = {cls: iid for iid, cls in re.findall(r'"([a-z]+:[\w\-]+)"\s*:\s*instructions\.(\w+)', reg)}
assert len(CLASS_TO_ID) == 58


def make_adapter(cls_name, iid):
    class Adapter:
        def __init__(self, instruction_id=None):
            self.kwargs = {}

        def build_description(self, **kwargs):
            self.kwargs = {k: v for k, v in kwargs.items() if v is not None}
            return ""

        def get_instruction_args(self):
            return self.kwargs

        def check_following(self, value):
            return rep.check(iid, self.kwargs, value)
    Adapter.__name__ = cls_name
    return Adapter


pkg = types.ModuleType("ifbench")
pkg.__path__ = []
instr = types.ModuleType("ifbench.instructions")
for c, i in CLASS_TO_ID.items():
    setattr(instr, c, make_adapter(c, i))
classic = types.ModuleType("ifbench.classic_instructions")


def _classic_getattr(name):
    class Skip:
        def __init__(self, *a, **k):
            raise unittest.SkipTest("classic IFEval checker, not audited")
    return Skip


classic.__getattr__ = _classic_getattr
pkg.instructions = instr
pkg.classic_instructions = classic
sys.modules["ifbench"] = pkg
sys.modules["ifbench.instructions"] = instr
sys.modules["ifbench.classic_instructions"] = classic

test_path = os.path.join(W, "audit", "work", "pkgs", "reference", "instructions_test.py")
spec = importlib.util.spec_from_file_location("ref_instructions_test", test_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

src_lines = open(test_path, encoding="utf-8").read().split("\n")


class Rec(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.rows = []

    def _row(self, test, err, sub=None):
        tb = traceback.extract_tb(err[2])
        line = next((fr.lineno for fr in reversed(tb) if fr.filename == test_path), None)
        self.rows.append({"test": test._testMethodName if hasattr(test, "_testMethodName") else str(test),
                          "subtest": getattr(sub, "_message", None) if sub is not None else None,
                          "line": line, "assertion": src_lines[line - 1].strip() if line else None,
                          "error": err[0].__name__})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._row(test, err)

    def addError(self, test, err):
        super().addError(test, err)
        self._row(test, err)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._row(test, err, subtest)


suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
res = Rec()
suite.run(res)
ran = res.testsRun
print(f"tests run {ran}, skipped {len(res.skipped)}, failing assertions {len(res.rows)}")
for r in res.rows:
    print(f"  line {r['line']:4d} {r['test']} [{r['subtest']}] {r['error']}: {r['assertion']}")
json.dump(res.rows, open(os.path.join(W, "audit", "work", "reference_tests_vs_replacement.json"), "w"), indent=1)
