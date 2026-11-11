"""Replacement ToyCode grader written from audit/CONTRACT.md (clause ids in comments).

Usage (same as case/grade.py, plus one switch per decision entry):
    python -B audit/replacement/grade_contract.py [--tasks T] [--tests T] [--responses R] [--out V]
        [--crlf yes|no] [--palindrome literal|normalized] [--eq builtin|literal]
        [--dynamic-import statement|any] [--time-origin process|load] [--main-guard skip|run]

Defaults are the audit's proposed readings. The child process (child_contract.py) never receives the expected
values unless --eq literal is chosen, so code that forges the result channel can claim only values it could have
returned itself; the parent decodes typed values and compares them with Python ==.
"""

import argparse
import ast
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "case"))
CHILD = os.path.join(HERE, "child_contract.py")
TIME_LIMIT_SECONDS = 4.0
LOAD_MODE_STARTUP_ALLOWANCE = 2.0
ALLOWED_MODULES = frozenset(
    {"math", "itertools", "collections", "functools", "re", "heapq", "bisect", "string", "typing"})
OPEN_FENCE = re.compile(r"```[A-Za-z0-9_+-]*[ \t]*")   # C-EXT-1, matched against a whole line
CLOSE_FENCE = re.compile(r"```[ \t]*")

PROPOSED = {"crlf": "yes", "palindrome": "literal", "eq": "builtin", "dynamic_import": "statement",
            "time_origin": "process", "main_guard": "skip"}


# ------------------------------------------------------------------ C-EXT extraction

def extract_code(response, crlf="yes"):
    """Return (code, how). C-EXT-1..5; D-crlf decides whether a \\r before \\n belongs to the line ending."""
    lines = response.split("\n")
    if crlf == "yes":
        lines = [l[:-1] if l.endswith("\r") else l for l in lines]
    start = None
    for i, line in enumerate(lines):
        if OPEN_FENCE.fullmatch(line):
            start = i
            break
    if start is not None:
        for j in range(start + 1, len(lines)):
            if CLOSE_FENCE.fullmatch(lines[j]):
                return "\n".join(lines[start + 1:j]), "fenced"
    # No fenced block (an opening fence without a closing fence is not a block): the whole response.
    return response, "whole"


# ------------------------------------------------------------------ C-IMP import check

def check_imports(code):
    """Return None if the code parses and its import statements name only allowed modules, else a reason."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, MemoryError, RecursionError) as exc:   # C-IMP-1
        return f"does not parse: {exc.__class__.__name__}"
    for node in ast.walk(tree):                                              # C-IMP-2: anywhere in the tree
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES:
                    return f"imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.level:                                                   # C-IMP-3
                return "relative import"
            if (node.module or "").split(".")[0] not in ALLOWED_MODULES:     # C-IMP-4
                return f"imports {node.module}"
    return None


# ------------------------------------------------------------------ typed values (C-TST-3)

class _Opaque:
    """A value the child could not encode as plain data; equal to nothing."""

    def __init__(self, kind):
        self.kind = kind

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    __hash__ = object.__hash__


def decode(enc):
    tag = enc[0]
    if tag == "n":
        return None
    if tag == "b":
        return bool(enc[1])
    if tag == "i":
        return int(enc[1], 16)
    if tag == "f":
        return float(enc[1])
    if tag == "c":
        return complex(enc[1])
    if tag == "s":
        if not isinstance(enc[1], str):
            raise ValueError("bad str")
        return enc[1]
    if tag == "y":
        return bytes.fromhex(enc[1])
    if tag == "l":
        return [decode(e) for e in enc[1]]
    if tag == "t":
        return tuple(decode(e) for e in enc[1])
    if tag == "S":
        return {decode(e) for e in enc[1]}
    if tag == "F":
        return frozenset(decode(e) for e in enc[1])
    if tag == "d":
        return {decode(k): decode(v) for k, v in enc[1]}
    if tag == "o":
        return _Opaque(str(enc[1]))
    raise ValueError(f"unknown tag {tag!r}")


# ------------------------------------------------------------------ C-EXE / C-TST

def effective_tests(task_id, tests, palindrome):
    """D-palindrome-normalization: under the literal reading the mixed-case sentence is not a palindrome."""
    tests = json.loads(json.dumps(tests))
    if task_id == "t02" and palindrome == "literal":
        for t in tests:
            if "expected" in t and isinstance(t["args"][0], str):
                s = t["args"][0]
                t["expected"] = s == s[::-1]
    return tests


def child_env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
    env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONSAFEPATH="1",
               PYTHONIOENCODING="utf-8")
    return env


def run_candidate(code, entry_point, tests, opts):
    """Run the code in a fresh process; return (outcome dict or None, detail)."""
    job = {"code": code, "entry_point": entry_point, "args": [t["args"] for t in tests],
           "allowed": sorted(ALLOWED_MODULES), "dynamic_import": opts["dynamic_import"],
           "main_guard": opts["main_guard"]}
    if opts["eq"] == "literal":
        job["expected"] = [t.get("expected") for t in tests]
        job["has_expected"] = ["expected" in t for t in tests]
    with tempfile.TemporaryDirectory() as workdir:
        job_path = os.path.join(workdir, "job.json")
        result_path = os.path.join(workdir, "result.json")
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job, f)
        limit = TIME_LIMIT_SECONDS
        if opts["time_origin"] == "load":
            limit += LOAD_MODE_STARTUP_ALLOWANCE
        t0 = time.monotonic()
        try:
            subprocess.run([sys.executable, CHILD, job_path, result_path], cwd=workdir, env=child_env(),
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=limit)
        except subprocess.TimeoutExpired:
            return None, "timeout"
        wall = time.monotonic() - t0
        if opts["time_origin"] == "process" and wall >= TIME_LIMIT_SECONDS:
            return None, "timeout"
        try:
            with open(result_path, encoding="utf-8") as f:
                outcome = json.load(f)
        except (OSError, ValueError, RecursionError):
            return None, "no result"
    if not isinstance(outcome, dict):
        return None, "malformed result"
    if opts["time_origin"] == "load":
        elapsed = outcome.get("elapsed")
        if not isinstance(elapsed, (int, float)) or not elapsed < TIME_LIMIT_SECONDS:
            return None, "timeout"
    return outcome, None


def judge(outcome, tests, opts):
    """C-TST-1..5 and C-EXE-5: every test must have a recorded outcome that passes."""
    if opts["dynamic_import"] == "any" and outcome.get("import_violations"):
        return False, "dynamic import of " + str(outcome["import_violations"][0])
    if not outcome.get("loaded"):
        return False, "load error"
    if not outcome.get("callable"):
        return False, "missing function"
    results = outcome.get("results")
    if not isinstance(results, list) or len(results) != len(tests):
        return False, "incomplete results"
    for i, (test, res) in enumerate(zip(tests, results)):
        kind = res.get("kind") if isinstance(res, dict) else None
        if "raises" in test:
            if kind != "raise" or test["raises"] not in (res.get("builtin_mro") or []):
                return False, f"test {i} failed"
        else:
            if kind != "return":
                return False, f"test {i} failed ({kind})"
            if opts["eq"] == "literal":
                if res.get("eq") is not True:
                    return False, f"test {i} failed"
            else:
                try:
                    equal = decode(res["value"]) == test["expected"]
                except Exception:
                    return False, f"test {i} failed (undecodable)"
                if equal is not True:
                    return False, f"test {i} failed"
    return True, "all tests passed"


def grade_response(task, tests, response, opts):
    code, _how = extract_code(response, opts["crlf"])
    reason = check_imports(code)
    if reason is not None:
        return False, reason
    outcome, error = run_candidate(code, task["entry_point"], tests, opts)
    if outcome is None:
        return False, error
    return judge(outcome, tests, opts)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Replacement ToyCode grader (audit contract).")
    ap.add_argument("--tasks", default=os.path.join(CASE, "tasks.jsonl"))
    ap.add_argument("--tests", default=os.path.join(CASE, "tests.json"))
    ap.add_argument("--responses", default=os.path.join(CASE, "responses.jsonl"))
    ap.add_argument("--out")
    ap.add_argument("--crlf", choices=["yes", "no"], default=PROPOSED["crlf"])
    ap.add_argument("--palindrome", choices=["literal", "normalized"], default=PROPOSED["palindrome"])
    ap.add_argument("--eq", choices=["builtin", "literal"], default=PROPOSED["eq"])
    ap.add_argument("--dynamic-import", choices=["statement", "any"], default=PROPOSED["dynamic_import"])
    ap.add_argument("--time-origin", choices=["process", "load"], default=PROPOSED["time_origin"])
    ap.add_argument("--main-guard", choices=["skip", "run"], default=PROPOSED["main_guard"])
    args = ap.parse_args(argv)
    opts = {"crlf": args.crlf, "palindrome": args.palindrome, "eq": args.eq,
            "dynamic_import": args.dynamic_import, "time_origin": args.time_origin,
            "main_guard": args.main_guard}

    tasks = OrderedDict((t["task_id"], t) for t in load_jsonl(args.tasks))
    with open(args.tests, encoding="utf-8") as f:
        all_tests = json.load(f)

    rows, seen, warnings, grading_errors = [], set(), [], 0
    for r in load_jsonl(args.responses):
        key = (r.get("model"), r.get("task_id"))
        if r.get("task_id") not in tasks:
            warnings.append(f"skipped {r.get('id')}: unknown task {r.get('task_id')!r}")
            continue
        try:
            tests = effective_tests(r["task_id"], all_tests[r["task_id"]], opts["palindrome"])
            passed, detail = grade_response(tasks[r["task_id"]], tests, r.get("response") or "", opts)
        except Exception as exc:   # a grading failure, counted apart from model accuracy
            grading_errors += 1
            passed, detail = False, f"grading error: {exc.__class__.__name__}"
        duplicate = key in seen
        seen.add(key)
        if duplicate:
            warnings.append(f"duplicate {key}: row {r.get('id')} graded but not counted")
        rows.append({"id": r.get("id"), "model": r.get("model"), "task_id": r.get("task_id"),
                     "verdict": "pass" if passed else "fail", "detail": detail, "counted": not duplicate})

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    passed_by_model = Counter()
    for row in rows:
        if row["counted"] and row["verdict"] == "pass":
            passed_by_model[row["model"]] += 1
    models = sorted({str(row["model"]) for row in rows})
    print(f"{'model':<12}{'passed':>8}{'tasks':>7}{'score':>8}")
    for model in models:
        score = 100.0 * passed_by_model[model] / len(tasks)   # C-AGG-1: denominator is always the 10 tasks
        print(f"{model:<12}{passed_by_model[model]:>8}{len(tasks):>7}{score:>8.1f}")
    print(f"options: {json.dumps(opts, sort_keys=True)}; grading errors: {grading_errors}")
    for w in warnings:
        print("warning:", w)


if __name__ == "__main__":
    main()
