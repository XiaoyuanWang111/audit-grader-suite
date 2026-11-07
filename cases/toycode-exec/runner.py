"""Child process for grade.py: load one candidate, call its function on the task's tests, print one result line.

Usage: python runner.py JOB_JSON
"""

import builtins
import copy
import io
import json
import sys

RESULT_PREFIX = "@@RESULT@@ "


def run(job):
    namespace = {"__name__": "candidate"}
    try:
        exec(compile(job["code"], "candidate.py", "exec"), namespace)
    except BaseException as exc:
        return {"loaded": False, "error": repr(exc)}

    fn = namespace.get(job["entry_point"])
    results = []
    errors = []
    for index, test in enumerate(job["tests"]):
        args = copy.deepcopy(test["args"])
        expected_exc = getattr(builtins, test["raises"]) if "raises" in test else None
        try:
            value = fn(*args)
        except Exception as exc:
            if expected_exc is not None:
                results.append({"test": index, "passed": isinstance(exc, expected_exc)})
            else:
                errors.append({"test": index, "error": repr(exc)})
            continue
        if expected_exc is not None:
            results.append({"test": index, "passed": False})
        else:
            results.append({"test": index, "value": json.dumps(value, default=repr)})
    return {"loaded": True, "results": results, "errors": errors}


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        job = json.load(f)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        outcome = run(job)
    finally:
        sys.stdout = real_stdout
    print(RESULT_PREFIX + json.dumps(outcome))


if __name__ == "__main__":
    main()
