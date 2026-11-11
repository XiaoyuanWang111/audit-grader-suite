"""Step 4: run the reference's unit tests (instructions_test.py, InstructionsTest) against
(a) the reference itself, (b) the vendored grader, (c) the replacement.

Each assertTrue/assertFalse/assertEqual is recorded instead of raising, so every assertion
is evaluated. Prints the assertions each target fails, with the test line number.
Usage: python run_reference_tests.py [reference|grader|replacement]
"""
import inspect
import sys
import types

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402  (sets NLTK_DATA, blocks downloads, puts audit/run on sys.path)

target = sys.argv[1] if len(sys.argv) > 1 else "replacement"

import ifbench  # noqa: E402
from ifbench import instructions as ref_instructions  # noqa: E402
from ifbench import instructions_registry as ref_registry  # noqa: E402

if target != "reference":
    class_to_id = {cls.__name__: iid for iid, cls in ref_registry.INSTRUCTION_DICT.items()
                   if cls.__module__.endswith(".instructions")}
    fake = types.ModuleType("ifbench.instructions")
    if target == "grader":
        from IFBench import instructions as g_instructions
        for name in class_to_id:
            setattr(fake, name, getattr(g_instructions, name))
    else:
        import replacement

        def make(iid):
            class Adapter:
                def __init__(self, instruction_id):
                    self.id = instruction_id
                    self.kw = {}

                def build_description(self, **kw):
                    self.kw = {k: v for k, v in kw.items() if v is not None}
                    return ""

                def get_instruction_args(self):
                    return self.kw

                def check_following(self, value):
                    return replacement.check(iid, self.kw, value)
            Adapter.__name__ = "Adapter_" + iid
            return Adapter
        for name, iid in class_to_id.items():
            setattr(fake, name, make(iid))
    sys.modules["ifbench.instructions"] = fake
    ifbench.instructions = fake

sys.path.insert(0, "<W>/audit/run/reference")
import instructions_test as T  # noqa: E402

failures = []
total = [0]


def rec(kind):
    def f(self, *args, **kwargs):
        total[0] += 1
        frame = inspect.stack()[1]
        if kind == "true":
            ok = bool(args[0])
        elif kind == "false":
            ok = not bool(args[0])
        else:
            ok = args[0] == args[1]
        if not ok:
            failures.append((self._testMethodName, frame.lineno, kind, repr(args[:2])[:120]))
    return f


cls = T.InstructionsTest
cls.assertTrue = rec("true")
cls.assertFalse = rec("false")
cls.assertEqual = rec("equal")
errors = []
for name in sorted(n for n in dir(cls) if n.startswith("test")):
    t = cls(name)
    try:
        getattr(t, name)()
    except Exception as e:
        errors.append((name, f"{type(e).__name__}: {str(e)[:100]}"))
print(f"target={target}: {total[0]} assertions evaluated, {len(failures)} fail, {len(errors)} tests raised")
for f in failures:
    print("  FAIL", f)
for e in errors:
    print("  RAISE", e)
