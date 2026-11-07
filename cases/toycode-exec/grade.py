"""Grade ToyCode responses by running each candidate function on the task's stored tests.

Usage:
    python grade.py [--tasks tasks.jsonl] [--tests tests.json] [--responses responses.jsonl] [--out verdicts.jsonl]

Each response runs in its own Python process (runner.py). Prints one row per model; with --out, also writes one
JSON verdict per response.
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "runner.py")
RESULT_PREFIX = "@@RESULT@@ "
TIME_LIMIT_SECONDS = 4.0
ALLOWED_MODULES = {"math", "itertools", "collections", "functools", "re", "heapq", "bisect", "string", "typing"}
FENCE = re.compile(r"^```python[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def extract_code(response):
    m = FENCE.search(response)
    return m.group(1) if m else response


def check_imports(code):
    """Return None if the code parses and imports only allowed modules, else a reason."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError) as exc:
        return f"does not parse: {exc.__class__.__name__}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        else:
            continue
        for module in modules:
            if module.split(".")[0] not in ALLOWED_MODULES:
                return f"imports {module or '(relative)'}"
    return None


def run_candidate(code, entry_point, tests):
    with tempfile.TemporaryDirectory() as workdir:
        job_path = os.path.join(workdir, "job.json")
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump({"code": code, "entry_point": entry_point, "tests": tests}, f)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            proc = subprocess.run([sys.executable, RUNNER, job_path], cwd=workdir, env=env,
                                  capture_output=True, encoding="utf-8", errors="replace",
                                  timeout=TIME_LIMIT_SECONDS)
        except subprocess.TimeoutExpired:
            return None, "timeout"
    lines = [l for l in proc.stdout.splitlines() if l.startswith(RESULT_PREFIX)]
    if not lines:
        return None, f"no result (exit code {proc.returncode})"
    return json.loads(lines[-1][len(RESULT_PREFIX):]), None


def judge(outcome, tests):
    if not outcome["loaded"]:
        return False, "load error: " + outcome["error"]
    for r in outcome["results"]:
        test = tests[r["test"]]
        if "passed" in r:
            if not r["passed"]:
                return False, f"test {r['test']} failed"
        elif json.loads(r["value"]) != test["expected"]:
            return False, f"test {r['test']} failed"
    return True, "all tests passed"


def grade_response(task, tests, response):
    code = extract_code(response)
    reason = check_imports(code)
    if reason is not None:
        return False, reason
    outcome, error = run_candidate(code, task["entry_point"], tests)
    if outcome is None:
        return False, error
    return judge(outcome, tests)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade ToyCode responses.")
    ap.add_argument("--tasks", default=os.path.join(HERE, "tasks.jsonl"))
    ap.add_argument("--tests", default=os.path.join(HERE, "tests.json"))
    ap.add_argument("--responses", default=os.path.join(HERE, "responses.jsonl"))
    ap.add_argument("--out", help="write one JSON verdict per response to this file")
    args = ap.parse_args(argv)

    tasks = {t["task_id"]: t for t in load_jsonl(args.tasks)}
    with open(args.tests, encoding="utf-8") as f:
        all_tests = json.load(f)

    rows = []
    for r in load_jsonl(args.responses):
        passed, detail = grade_response(tasks[r["task_id"]], all_tests[r["task_id"]], r["response"])
        rows.append({"id": r["id"], "model": r["model"], "task_id": r["task_id"],
                     "verdict": "pass" if passed else "fail", "detail": detail})

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    passed_by_model = defaultdict(int)
    for row in rows:
        passed_by_model[row["model"]] += row["verdict"] == "pass"
    models = sorted({row["model"] for row in rows})
    print(f"{'model':<12}{'passed':>8}{'tasks':>7}{'score':>8}")
    for model in models:
        score = 100.0 * passed_by_model[model] / len(tasks)
        print(f"{model:<12}{passed_by_model[model]:>8}{len(tasks):>7}{score:>8.1f}")


if __name__ == "__main__":
    main()
