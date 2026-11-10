"""Step 4: run the reference's unit tests (instructions_test.py) against the replacement grader.

A shim package named `ifbench` (audit/work/shim/ifbench) exposes the reference's class names; each
class forwards check_following to audit/replacement/ifbench_contract.py under the proposed
readings. assertTrue / assertFalse / assertEqual are patched to record every assertion instead of
stopping the test, together with the last text given to check_following. Classic IFEval tests
(classic_instructions) run against the reference's own classic code and are not recorded.

Output: audit/work/reftests_vs_replacement.json and a printed list of the assertions whose
expected value the replacement contradicts.
"""
import inspect
import json
import os
import shutil
import sys
import traceback

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
import ifb  # noqa: E402  (sets NLTK_DATA)

ifb.verify_pins()
SHIM = os.path.join(W, "audit", "work", "shim")
pkg = os.path.join(SHIM, "ifbench")
os.makedirs(pkg, exist_ok=True)
for f in ("classic_instructions.py", "instructions_util.py"):
    shutil.copy(os.path.join(ifb.PKG_R, "ifbench", f), os.path.join(pkg, f))
with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8") as fh:
    fh.write("")

# map reference class names to instruction ids, without importing the reference package under its own name
REG = os.path.join(ifb.PKG_R, "ifbench", "instructions_registry.py")
import re  # noqa: E402

pairs = re.findall(r'"([a-z_]+:[a-z_\-]+)"\s*:\s*instructions\.(\w+)', open(REG, encoding="utf-8").read())
with open(os.path.join(pkg, "instructions.py"), "w", encoding="utf-8") as fh:
    fh.write('"""Shim: reference class names backed by the replacement grader."""\n')
    fh.write("import ifbench_contract as _rep\n\nLAST = {}\n\n\n")
    fh.write("class Instruction:\n    def __init__(self, instruction_id):\n        self.id = instruction_id\n\n\n")
    fh.write("class _Base:\n    IID = None\n\n    def __init__(self, instruction_id):\n        self.id = instruction_id\n"
             "        self._kw = {}\n\n    def build_description(self, **kwargs):\n"
             "        self._kw = {k: v for k, v in kwargs.items() if v is not None}\n        return ''\n\n"
             "    def get_instruction_args(self):\n        return dict(self._kw)\n\n"
             "    def get_instruction_args_keys(self):\n        return list(self._kw)\n\n"
             "    def check_following(self, value):\n        LAST['iid'] = self.IID\n        LAST['kwargs'] = dict(self._kw)\n"
             "        LAST['value'] = value\n        return _rep.check(self.IID, self._kw, '', value)\n\n\n")
    for iid, cls in pairs:
        fh.write(f"class {cls}(_Base):\n    IID = {iid!r}\n\n\n")

sys.path.insert(0, os.path.join(W, "audit", "replacement"))
sys.path.insert(0, SHIM)
for m in [m for m in list(sys.modules) if m == "ifbench" or m.startswith("ifbench.")]:
    del sys.modules[m]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("ref_instructions_test", os.path.join(ifb.PKG_R, "instructions_test.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
shim = sys.modules["ifbench.instructions"]
assert shim.__file__.startswith(SHIM), shim.__file__

records = []
current = {"test": None}


def _rec(kind, expected, actual):
    frame = inspect.stack()[2]
    last = dict(shim.LAST)
    records.append({"test": current["test"], "line": frame.lineno, "kind": kind, "expected": expected,
                    "actual": bool(actual) if kind != "equal" else actual, "iid": last.get("iid"),
                    "kwargs": {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in last.get("kwargs", {}).items()},
                    "value": last.get("value")})
    shim.LAST.clear()


def assertTrue(self, x, msg=None):
    _rec("true", True, x)


def assertFalse(self, x, msg=None):
    _rec("false", False, x)


def assertEqual(self, a, b, msg=None):
    _rec("equal", b, a)


cls = T.InstructionsTest
cls.assertTrue, cls.assertFalse, cls.assertEqual = assertTrue, assertFalse, assertEqual
errors = []
names = [n for n in dir(cls) if n.startswith("test")]
for name in names:
    src = inspect.getsource(getattr(cls, name))
    if "instructions." not in src or "classic_instructions." in src:
        continue
    current["test"] = name
    inst = cls(name)
    try:
        getattr(inst, name)()
    except Exception as e:  # noqa: BLE001
        errors.append({"test": name, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-600:]})

out = os.path.join(W, "audit", "work", "reftests_vs_replacement.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"records": records, "errors": errors}, fh, ensure_ascii=False, indent=1)
mism = [r for r in records if r["kind"] != "equal" and r["iid"] and r["expected"] != r["actual"]]
print(f"tests run {len({r['test'] for r in records} | {e['test'] for e in errors})}, assertions {len(records)}, "
      f"replacement contradicts {len(mism)}, test errors {len(errors)}")
for r in mism:
    v = (r["value"] or "").replace("\n", "\\n")
    print(f"- {r['test']} line {r['line']} {r['iid']} {r['kwargs']} expected={r['expected']} contract={r['actual']} :: {v[:150]!r}")
for e in errors:
    print("ERROR", e["test"], e["error"])
