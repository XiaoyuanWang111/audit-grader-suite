"""Replacement grader for ToyCode 1.0: an implementation of audit/CONTRACT.md with one switch per decision entry.

Usage (from the audit run directory):
    python audit/scripts/contract_grader.py [--mode proposed|fixes-only] [--set D=R ...]
        [--tasks case/tasks.jsonl] [--tests case/tests.json] [--responses case/responses.jsonl] [--out FILE]

Modes: "proposed" uses the audit's proposed reading of every decision entry; "fixes-only" uses the reading that
case/grade.py follows, so every verdict that differs from case/grade.py is a defect fix. --set overrides one entry,
for example --set palindrome=B.

It is an audit instrument, not a sandbox: code that inspects the runner's frames or memory can still forge a result.
"""

import argparse
import ast
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "contract_runner.py")
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
TIME_LIMIT_SECONDS = 4.0
START_ALLOWANCE_SECONDS = 2.0  # only for D-time-start reading B
ALLOWED_MODULES = {"math", "itertools", "collections", "functools", "re", "heapq", "bisect", "string", "typing"}
FENCE_LINE = re.compile(r"```([A-Za-z0-9_+\-]*)[ \t]*\Z")

# Decision entries: reading A or B, as audit/CONTRACT.md defines them.
PROPOSED = {
    "palindrome": "A",       # D-palindrome-normalization: A literal s == s[::-1]; B stored test 4 (ignore case, spaces)
    "line_terminator": "A",  # D-line-terminator: A "\n" and "\r\n" end a line; B only "\n"
    "load_error": "A",       # D-load-error: A an exception while loading fails the task; B tests still run
    "main_guard": "A",       # D-main-guard: A __name__ is not "__main__"; B it is
    "dynamic_import": "A",   # D-dynamic-import: A only statements are checked; B __import__ of a module off the list fails
    "numeric_type": "A",     # D-numeric-type: A Python ==; B also the same exact type at every level
    "eq_object": "B",        # D-eq-object: A Python == on any object; B the value must be built from built-in types
    "time_start": "A",       # D-time-start: A budget from process start; B budget on loading + tests only
}
# The reading that case/grade.py follows for each entry (found in steps 3 and 4).
FIXES_ONLY = dict(PROPOSED, palindrome="B", line_terminator="B")

# D-palindrome-normalization reading A: the literal reading changes the expected value of t02 test 4.
LITERAL_OVERRIDES = {("t02", 3): False}


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def split_lines(text, line_terminator):
    parts = text.split("\n")
    if line_terminator == "A":  # "\r\n" ends a line too; a lone "\r" does not
        return [p[:-1] if i < len(parts) - 1 and p.endswith("\r") else p for i, p in enumerate(parts)]
    return parts


def extract_code(response, line_terminator="A"):
    """C-extract: (code, how), where how is "block", "no fence" or "unclosed"."""
    lines = split_lines(response, line_terminator)
    first = next((i for i, line in enumerate(lines) if FENCE_LINE.match(line)), None)
    if first is None:
        return response, "no fence"
    for j in range(first + 1, len(lines)):
        m = FENCE_LINE.match(lines[j])
        if m and m.group(1) == "":
            return "\n".join(lines[first + 1:j]), "block"
    return response, "unclosed"


def check_imports(code, dynamic_import="A"):
    """C-import: None if the code parses and imports only allowed modules, else the reason."""
    try:
        tree = ast.parse(code)
    except Exception as exc:  # SyntaxError, ValueError, and also MemoryError or RecursionError on deep nesting
        return f"does not parse: {type(exc).__name__}"
    allowed_calls = set()  # D-dynamic-import B: __import__("<allowed module>") is the only allowed use of the name
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__"
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
                and node.args[0].value.split(".")[0] in ALLOWED_MODULES):
            allowed_calls.add(id(node.func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES:
                    return f"imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                return "relative import"
            if (node.module or "").split(".")[0] not in ALLOWED_MODULES:
                return f"imports {node.module}"
        elif (dynamic_import == "B" and isinstance(node, ast.Name) and node.id == "__import__"
              and id(node) not in allowed_calls):
            return "dynamic import"
    return None


def tests_for(task_id, tests, decisions):
    tests = json.loads(json.dumps(tests))
    if decisions["palindrome"] == "A":
        for (tid, index), expected in LITERAL_OVERRIDES.items():
            if tid == task_id:
                tests[index]["expected"] = expected
    return tests


def run_candidate(code, entry_point, tests, decisions):
    nonce = secrets.token_hex(16)
    job = {"code": code, "entry_point": entry_point, "tests": tests, "nonce": nonce, "decisions": decisions}
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    for key in ("SYSTEMROOT", "WINDIR"):  # Windows needs these to start Python; not grading inputs
        if key in os.environ:
            env[key] = os.environ[key]
    limit = TIME_LIMIT_SECONDS if decisions["time_start"] == "A" else TIME_LIMIT_SECONDS + START_ALLOWANCE_SECONDS
    with tempfile.TemporaryDirectory() as workdir:  # empty working directory: the job arrives on stdin
        try:
            # -s -P instead of -I: -I implies -E, which would ignore the pinned PYTHONHASHSEED
            proc = subprocess.run([sys.executable, "-s", "-P", RUNNER], input=json.dumps(job), cwd=workdir, env=env,
                                  capture_output=True, encoding="utf-8", errors="replace", timeout=limit)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    lines = [line for line in proc.stdout.splitlines() if line.startswith(nonce + " ")]
    if len(lines) != 1 or proc.returncode != 0:
        return False, f"no single result line (exit code {proc.returncode}, {len(lines)} lines)"
    try:
        outcome = json.loads(lines[0][len(nonce) + 1:])
        results = outcome["results"]
    except (ValueError, KeyError, TypeError):
        return False, "unreadable result line"
    if decisions["time_start"] == "B" and outcome.get("elapsed", 0.0) >= TIME_LIMIT_SECONDS:
        return False, "timeout (loading and tests)"
    if sorted(r.get("test") for r in results) != list(range(len(tests))):
        return False, "result missing for some test"
    for r in results:
        if r.get("passed") is not True:
            return False, f"test {r['test']} failed: {r.get('why')}"
    return True, "all tests passed"


def grade_response(task, tests, response, decisions):
    try:
        code, _how = extract_code(response, decisions["line_terminator"])
        reason = check_imports(code, decisions["dynamic_import"])
        if reason is not None:
            return False, reason
        return run_candidate(code, task["entry_point"], tests_for(task["task_id"], tests, decisions), decisions)
    except Exception as exc:  # C-task 3: an error while grading one response fails that response only
        return False, f"grader error: {type(exc).__name__}"


def decisions_from(mode, overrides=()):
    decisions = dict(PROPOSED if mode == "proposed" else FIXES_ONLY)
    for item in overrides:
        key, value = item.split("=", 1)
        if key not in decisions or value not in ("A", "B"):
            raise SystemExit(f"bad --set {item!r}")
        decisions[key] = value
    return decisions


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("proposed", "fixes-only"), default="proposed")
    ap.add_argument("--set", action="append", default=[], metavar="ENTRY=READING")
    ap.add_argument("--tasks", default=os.path.join(CASE, "tasks.jsonl"))
    ap.add_argument("--tests", default=os.path.join(CASE, "tests.json"))
    ap.add_argument("--responses", default=os.path.join(CASE, "responses.jsonl"))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    decisions = decisions_from(args.mode, args.set)

    tasks = {t["task_id"]: t for t in load_jsonl(args.tasks)}
    with open(args.tests, encoding="utf-8") as f:
        all_tests = json.load(f)
    rows = []
    for r in load_jsonl(args.responses):
        passed, detail = grade_response(tasks[r["task_id"]], all_tests[r["task_id"]], r["response"], decisions)
        rows.append({"id": r["id"], "model": r["model"], "task_id": r["task_id"],
                     "verdict": "pass" if passed else "fail", "detail": detail})
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
    passed_tasks = defaultdict(set)  # C-task 2: a task counts once per model
    for row in rows:
        if row["verdict"] == "pass":
            passed_tasks[row["model"]].add(row["task_id"])
    print("decisions", json.dumps(decisions, sort_keys=True))
    print(f"{'model':<12}{'passed':>8}{'tasks':>7}{'score':>8}")
    for model in sorted({row["model"] for row in rows}):
        n = len(passed_tasks[model])
        print(f"{model:<12}{n:>8}{len(tasks):>7}{100.0 * n / len(tasks):>8.1f}")


if __name__ == "__main__":
    main()
