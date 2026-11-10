"""Run the reference's unit tests (reference/IFBench/instructions_test.py, class InstructionsTest)
against a target implementation, recording every assertion instead of stopping at the first.

Targets: --target replacement  (audit/replacement/grader.py behind the reference class names)
         --target grader       (the grader under audit's instructions.py)
         --target reference    (the reference itself, as a control)
Writes audit/out/ref_tests_<target>.tsv: test, line, assertion, outcome, source line.
"""
import inspect
import linecache
import os
import sys
import types
import unittest

W = "<W>"
os.environ.setdefault("NLTK_DATA", f"{W}/case/deps/nltk_data")
target = sys.argv[sys.argv.index("--target") + 1] if "--target" in sys.argv else "replacement"
REF = f"{W}/audit/work/reference/IFBench"
sys.path.insert(0, REF)
sys.path.insert(0, f"{W}/audit/work/grader")
sys.path.insert(0, f"{W}/audit")

import ifbench  # noqa: E402  (the real reference package; replaced below for non-reference targets)
from ifbench import instructions_registry as RREG  # noqa: E402

if target != "reference":
    if target == "grader":
        from IFBench import instructions as impl_mod
    else:
        from replacement import grader as X
        name_to_iid = {cls.__name__: iid for iid, cls in RREG.INSTRUCTION_DICT.items() if ":" in iid
                       and not iid.split(":")[0] in ("keywords", "language", "length_constraints", "detectable_content",
                                                     "detectable_format", "combination", "startend", "change_case", "punctuation")}
        impl_mod = types.ModuleType("shim_instructions")

        def make(cname, iid):
            class Shim:
                def __init__(self, instruction_id=None):
                    self.iid = iid
                    self.kw = {}

                def build_description(self, **kw):
                    self.kw.update({k: v for k, v in kw.items() if v is not None})
                    return ""

                def get_instruction_args(self):
                    return dict(self.kw)

                def get_instruction_args_keys(self):
                    return list(self.kw)

                def check_following(self, value):
                    return X.grade(self.iid, value, self.kw, self.kw.get("prompt", ""))
            Shim.__name__ = cname
            return Shim
        for cname, iid in name_to_iid.items():
            setattr(impl_mod, cname, make(cname, iid))
    ifbench.instructions = impl_mod
    sys.modules["ifbench.instructions"] = impl_mod

RECORDS = []


def _rec(kind, ok):
    fr = inspect.stack()[2]
    test = next((f.function for f in inspect.stack() if f.function.startswith("test")), "?")
    RECORDS.append((test, fr.lineno, kind, "pass" if ok else "FAIL", linecache.getline(fr.filename, fr.lineno).strip()[:160]))


def patch(cls):
    def aT(self, x, msg=None):
        _rec("assertTrue", bool(x))

    def aF(self, x, msg=None):
        _rec("assertFalse", not bool(x))

    def aE(self, a, b, msg=None):
        _rec("assertEqual", a == b)
    cls.assertTrue, cls.assertFalse, cls.assertEqual = aT, aF, aE


import instructions_test as T  # noqa: E402

patch(T.InstructionsTest)
suite = unittest.TestLoader().loadTestsFromTestCase(T.InstructionsTest)
result = unittest.TestResult()
suite.run(result)
errors = [(str(t), "".join(e.splitlines(True)[-1:]).strip()) for t, e in result.errors + result.failures]
out = f"{W}/audit/out/ref_tests_{target}.tsv"
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("test\tline\tassertion\toutcome\tsource\n")
    for r in RECORDS:
        f.write("\t".join(str(x) for x in r) + "\n")
    for t, e in errors:
        f.write(f"{t}\t\terror\tERROR\t{e}\n")
fails = [r for r in RECORDS if r[3] == "FAIL"]
print(f"target={target}: {result.testsRun} tests, {len(RECORDS)} assertions, {len(fails)} failed assertions, {len(errors)} test errors")
for r in fails:
    print(f"  {r[0]}:{r[1]} {r[2]}  {r[4][:110]}")
for t, e in errors:
    print(f"  ERROR {t}: {e[:150]}")
