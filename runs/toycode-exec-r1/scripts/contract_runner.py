"""Child process of the replacement grader (contract_grader.py). Not a security sandbox.

Reads one job as JSON from stdin (so no file in the working directory holds the tests), loads the candidate code,
calls the entry point on each test, compares in this process with Python == on the returned object, and prints one
result line that starts with a per-run nonce. Everything the comparison needs is bound before the candidate code runs.
"""

import builtins
import copy
import io
import json
import sys
import time

_isinstance = builtins.isinstance
_type = builtins.type
_bool = builtins.bool
_len = builtins.len
_all = builtins.all
_repr = builtins.repr
_list, _tuple, _dict, _str, _int, _float = list, tuple, dict, str, int, float
_PLAIN_SCALARS = (type(None), bool, int, float, str)


def _plain(value, depth=0):
    """True when the value is built only from built-in types (exact types, so no user __eq__ can decide)."""
    if depth > 200:
        return False
    t = _type(value)
    if t in _PLAIN_SCALARS:
        return True
    if t is _list or t is _tuple:
        return _all(_plain(v, depth + 1) for v in value)
    if t is _dict:
        return _all(_plain(k, depth + 1) and _plain(v, depth + 1) for k, v in value.items())
    return False


def _same_types(a, b, depth=0):
    """D-numeric-type reading B: same exact type at every level."""
    if depth > 200 or _type(a) is not _type(b):
        return False
    if _type(a) in (_list, _tuple):
        return _len(a) == _len(b) and _all(_same_types(x, y, depth + 1) for x, y in zip(a, b))
    return True


def main():
    job = json.loads(sys.stdin.read())
    nonce = job.pop("nonce")
    decisions = job["decisions"]
    tests = job["tests"]
    exc_classes = {t["raises"]: getattr(builtins, t["raises"]) for t in tests if "raises" in t}
    real_stdout = sys.stdout
    write_result = real_stdout.write
    flush_result = real_stdout.flush
    sys.stdout = io.StringIO()
    results = []
    load_error = None
    started = time.perf_counter()  # D-time-start reading B measures from here: loading the code and the tests
    try:
        namespace = {"__name__": "__main__" if decisions["main_guard"] == "B" else "candidate"}
        try:
            exec(compile(job["code"], "candidate.py", "exec", dont_inherit=True), namespace)
        except BaseException as exc:  # noqa: BLE001 - any load failure is a verdict, not a crash
            load_error = _type(exc).__name__
        if load_error is not None and decisions["load_error"] == "A":
            results = [{"test": i, "passed": False, "why": "load error " + load_error} for i in range(_len(tests))]
        else:
            fn = namespace.get(job["entry_point"])
            for i, test in enumerate(tests):
                if fn is None:
                    results.append({"test": i, "passed": False, "why": "missing function"})
                    continue
                args = copy.deepcopy(test["args"])
                try:
                    value = fn(*args)
                except BaseException as exc:  # noqa: BLE001 - SystemExit and KeyboardInterrupt fail the test
                    cls = exc_classes.get(test.get("raises"))
                    ok = cls is not None and _isinstance(exc, cls)
                    results.append({"test": i, "passed": _bool(ok), "why": "raised " + _type(exc).__name__})
                    continue
                if "raises" in test:
                    results.append({"test": i, "passed": False, "why": "returned instead of raising"})
                    continue
                try:
                    expected = test["expected"]
                    if decisions["eq_object"] == "B" and not _plain(value):
                        ok, why = False, "returned a non-built-in value of type " + _type(value).__name__
                    elif decisions["numeric_type"] == "B" and not _same_types(value, expected):
                        ok, why = False, "returned a value of another type"
                    else:
                        ok = _bool(value == expected)
                        why = "equal" if ok else "not equal"
                except BaseException as exc:  # noqa: BLE001 - a comparison error fails the test
                    ok, why = False, "comparison raised " + _type(exc).__name__
                results.append({"test": i, "passed": ok, "why": why})
    finally:
        sys.stdout = real_stdout
    elapsed = time.perf_counter() - started
    write_result(nonce + " " + json.dumps({"results": results, "elapsed": elapsed}) + "\n")
    flush_result()


if __name__ == "__main__":
    main()
