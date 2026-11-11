"""Child process for grade_contract.py: load one candidate, call it on each test's arguments, write typed outcomes.

Usage: python child_contract.py JOB_JSON RESULT_JSON

The parent passes stdout/stderr as DEVNULL and reads only RESULT_JSON. Expected values are absent unless the
parent runs --eq literal.
"""

import builtins
import copy
import json
import sys
import time

_MAX_NODES = 1_000_000


class _Unencodable(Exception):
    pass


def encode(value, path_ids=None, budget=None):
    """Encode plain data with exact types (C-TST-3); anything else becomes an opaque marker."""
    if path_ids is None:
        path_ids, budget = set(), [_MAX_NODES]
    budget[0] -= 1
    if budget[0] < 0:
        raise _Unencodable("too large")
    t = type(value)
    if value is None:
        return ["n"]
    if t is bool:
        return ["b", value]
    if t is int:
        return ["i", format(value, "x") if value >= 0 else "-" + format(-value, "x")]
    if t is float:
        return ["f", repr(value)]
    if t is complex:
        return ["c", repr(value)]
    if t is str:
        return ["s", value]
    if t is bytes:
        return ["y", value.hex()]
    if t in (list, tuple, set, frozenset, dict):
        if id(value) in path_ids:
            raise _Unencodable("cycle")
        path_ids.add(id(value))
        try:
            if t is dict:
                body = [[encode(k, path_ids, budget), encode(v, path_ids, budget)] for k, v in value.items()]
            else:
                body = [encode(v, path_ids, budget) for v in value]
        finally:
            path_ids.discard(id(value))
        return [{list: "l", tuple: "t", set: "S", frozenset: "F", dict: "d"}[t], body]
    return ["o", t.__name__ if isinstance(t.__name__, str) else "?"]


def builtin_mro(exc):
    names = []
    for cls in type(exc).__mro__:
        name = getattr(cls, "__name__", None)
        if isinstance(name, str) and getattr(builtins, name, None) is cls:
            names.append(name)
    return names


def main():
    job_path, result_path = sys.argv[1], sys.argv[2]
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)
    out = open(result_path, "w", encoding="utf-8")
    dump, perf = json.dump, time.perf_counter
    allowed = frozenset(job["allowed"])
    namespace = {"__name__": "__main__" if job.get("main_guard") == "run" else "candidate"}
    violations = []

    if job.get("dynamic_import") == "any":   # D-dynamic-import reading B (best effort)
        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if globals is None or globals is namespace:
                if level or str(name).split(".")[0] not in allowed:
                    violations.append(str(name))
                    raise ImportError(f"import of {name!r} is not allowed")
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

    outcome = {"loaded": False, "callable": False, "results": [], "import_violations": violations}
    t0 = perf()
    try:
        exec(compile(job["code"], "candidate.py", "exec"), namespace)
        outcome["loaded"] = True
    except BaseException as exc:   # C-EXE-3
        outcome["load_error"] = type(exc).__name__
    fn = namespace.get(job["entry_point"]) if outcome["loaded"] else None
    if callable(fn):
        outcome["callable"] = True
        literal = "expected" in job
        for i, args in enumerate(job["args"]):
            try:
                value = fn(*copy.deepcopy(args))   # C-TST-2
            except BaseException as exc:            # C-TST-4, C-TST-5
                outcome["results"].append({"kind": "raise", "builtin_mro": builtin_mro(exc)})
                continue
            if literal:
                if not job["has_expected"][i]:
                    outcome["results"].append({"kind": "return", "eq": False})
                    continue
                try:
                    eq = bool(value == job["expected"][i])
                except BaseException:
                    eq = False
                outcome["results"].append({"kind": "return", "eq": eq})
            else:
                try:
                    outcome["results"].append({"kind": "return", "value": encode(value)})
                except (_Unencodable, RecursionError, MemoryError, ValueError):
                    outcome["results"].append({"kind": "unencodable"})
    outcome["elapsed"] = perf() - t0
    dump(outcome, out)
    out.close()


if __name__ == "__main__":
    main()
