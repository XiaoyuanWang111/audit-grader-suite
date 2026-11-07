"""ToyCode reference harness, as released by the benchmark authors (toycode 1.0).

Usage:
    python harness_ref.py TASKS_JSONL TESTS_JSON RESPONSES_JSONL [VERDICTS_OUT_JSONL]

The same file runs as the child process (python harness_ref.py --child JOB_JSON) that executes one candidate.
"""

import ast
import builtins
import copy
import io
import json
import os
import re
import subprocess
import sys
import tempfile

ALLOWED = ("math", "itertools", "collections", "functools", "re", "heapq", "bisect", "string", "typing")
LIMIT = 4.0
MARK = "<<toycode-result>>"
BLOCK = re.compile(r"^```[A-Za-z0-9_+-]*[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


# ---------------------------------------------------------------- child side

def child(job_path):
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)
    saved = sys.stdout
    sys.stdout = io.StringIO()
    ok = True
    try:
        env = {"__name__": "candidate"}
        try:
            exec(compile(job["code"], "candidate.py", "exec"), env)
            fn = env.get(job["entry_point"])
        except BaseException:
            fn = None
        if not callable(fn):
            ok = False
        else:
            for test in job["tests"]:
                try:
                    out = fn(*copy.deepcopy(test["args"]))
                except Exception as exc:
                    passed = "raises" in test and isinstance(exc, getattr(builtins, test["raises"]))
                else:
                    passed = "raises" not in test and out == test["expected"]
                if not passed:
                    ok = False
                    break
    finally:
        sys.stdout = saved
    print(MARK + json.dumps({"ok": bool(ok)}))


# ---------------------------------------------------------------- parent side

def code_of(response):
    m = BLOCK.search(response)
    return response if m is None else m.group(1)


def allowed(code):
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        if any(n.split(".")[0] not in ALLOWED for n in names):
            return False
    return True


def passes(code, entry_point, tests):
    if not allowed(code):
        return False
    with tempfile.TemporaryDirectory() as tmp:
        job = os.path.join(tmp, "job.json")
        with open(job, "w", encoding="utf-8") as f:
            json.dump({"code": code, "entry_point": entry_point, "tests": tests}, f)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child", job], cwd=tmp, env=env,
                               capture_output=True, encoding="utf-8", errors="replace", timeout=LIMIT)
        except subprocess.TimeoutExpired:
            return False
    marks = [l for l in p.stdout.splitlines() if l.startswith(MARK)]
    return bool(marks) and json.loads(marks[-1][len(MARK):])["ok"]


def main(argv):
    if len(argv) >= 2 and argv[0] == "--child":
        child(argv[1])
        return
    if len(argv) < 3:
        sys.exit(__doc__)
    with open(argv[0], encoding="utf-8") as f:
        tasks = {t["task_id"]: t for t in map(json.loads, filter(str.strip, f))}
    with open(argv[1], encoding="utf-8") as f:
        tests = json.load(f)
    with open(argv[2], encoding="utf-8") as f:
        responses = [json.loads(l) for l in f if l.strip()]

    verdicts = []
    for r in responses:
        task = tasks[r["task_id"]]
        ok = passes(code_of(r["response"]), task["entry_point"], tests[r["task_id"]])
        verdicts.append({"id": r["id"], "model": r["model"], "task_id": r["task_id"],
                         "verdict": "pass" if ok else "fail"})

    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8", newline="\n") as f:
            for v in verdicts:
                f.write(json.dumps(v) + "\n")

    print("model        pass@1")
    for m in sorted({v["model"] for v in verdicts}):
        n = sum(v["verdict"] == "pass" for v in verdicts if v["model"] == m)
        print(f"{m:<12} {100.0 * n / len(tasks):6.1f}")


if __name__ == "__main__":
    main(sys.argv[1:])
