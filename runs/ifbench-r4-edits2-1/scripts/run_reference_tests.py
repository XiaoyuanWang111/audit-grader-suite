"""Step 4: run the reference's unit tests (instructions_test.py, IFBench OOD part) against a target checker set,
recording every assertion (soft asserts) instead of stopping at the first failure in a test method.

Usage: run_reference_tests.py {reference|grader|replacement} [--json out.json]
The target's classes are substituted for `ifbench.instructions` when the test module is imported.
"""
import importlib.util
import inspect
import json
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))
import harness as H  # noqa: E402

TEST_FILE = H.RUN / "reference" / "instructions_test.py"
RECORD = []


def _caller_line():
    for fr in inspect.stack()[2:8]:
        if fr.filename.endswith("instructions_test.py"):
            return fr.lineno, (fr.code_context or [""])[0].strip()
    return None, ""


def _soft(name, ok_fn):
    def method(self, *args, **kwargs):
        try:
            ok = ok_fn(*args)
            err = None
        except Exception as e:  # noqa: BLE001
            ok, err = False, f"{type(e).__name__}: {e}"
        line, code = _caller_line()
        RECORD.append({"test": self._testMethodName, "line": line, "assert": name, "ok": bool(ok), "error": err, "code": code[:200]})
    return method


def install_soft_asserts():
    tc = unittest.TestCase
    tc.assertTrue = _soft("assertTrue", lambda x, *a: bool(x))
    tc.assertFalse = _soft("assertFalse", lambda x, *a: not bool(x))
    tc.assertEqual = _soft("assertEqual", lambda a, b, *r: a == b)
    tc.assertNotEqual = _soft("assertNotEqual", lambda a, b, *r: a != b)
    tc.assertIn = _soft("assertIn", lambda a, b, *r: a in b)
    tc.assertIsNone = _soft("assertIsNone", lambda a, *r: a is None)
    tc.assertIsNotNone = _soft("assertIsNotNone", lambda a, *r: a is not None)


def make_replacement_module():
    from ifbench import instructions_registry as reg
    from replacement import contract_grader as R

    mod = types.ModuleType("replacement_instructions")
    cls_to_id = {}
    for iid, cls in reg.INSTRUCTION_DICT.items():
        if iid in R.CHECKS:
            cls_to_id[cls.__name__] = iid
    for name, iid in cls_to_id.items():
        def init(self, instruction_id=None, _iid=iid):
            self.id = instruction_id
            self._iid = _iid
            self._kw = {}

        def build_description(self, *args, **kwargs):
            self._kw.update({k: v for k, v in kwargs.items() if v is not None})
            return ""

        def get_instruction_args(self):
            return dict(self._kw)

        def check_following(self, value, _R=R):
            prompt = ""
            kw = dict(self._kw)
            if self._iid == "repeat:repeat_span" and "prompt_to_repeat" in kw:
                prompt = kw["prompt_to_repeat"] + " Copy the span of words that lies between"
            return _R.check(self._iid, kw, value, prompt)

        mod.__dict__[name] = type(name, (), {"__init__": init, "build_description": build_description,
                                             "get_instruction_args": get_instruction_args,
                                             "check_following": check_following})
    return mod


def main():
    target = sys.argv[1]
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    import ifbench  # the reference package (copy under audit/run/reference)
    from ifbench import instructions as ref_ins

    if target == "reference":
        sub = ref_ins
    elif target == "grader":
        sub = H.grader_modules()["instructions"]
    elif target == "replacement":
        sub = make_replacement_module()
    else:
        raise SystemExit("target must be reference, grader or replacement")
    sys.modules["ifbench.instructions"] = sub
    ifbench.instructions = sub
    install_soft_asserts()
    spec = importlib.util.spec_from_file_location("ref_instructions_test", TEST_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromTestCase(mod.InstructionsTest)
    result = unittest.TestResult()
    suite.run(result)
    errors = [(str(t), tb.splitlines()[-1]) for t, tb in result.errors]
    fails = [r for r in RECORD if not r["ok"]]
    print(f"target={target} tests={result.testsRun} assertions={len(RECORD)} failed_assertions={len(fails)} test_errors={len(errors)}")
    for r in fails:
        print(f"  FAIL line {r['line']} {r['test']}: {r['code']}" + (f"  [{r['error']}]" if r["error"] else ""))
    for t, e in errors:
        print(f"  ERROR {t}: {e}")
    if out_json:
        json.dump({"records": RECORD, "errors": errors}, open(out_json, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
