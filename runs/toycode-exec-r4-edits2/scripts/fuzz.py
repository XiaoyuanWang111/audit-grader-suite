"""Fuzz the grader, the reference and the replacement with random responses (seeded).

Usage: python -B audit/scripts/fuzz.py [N] [SEED]
Each grader's per-response function is called in-process, so an exception that would stop the run is counted
instead of stopping the fuzzer. Prints counts only (counts depend on this generator's distribution).
"""

import importlib.util
import json
import os
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
sys.path.insert(0, os.path.join(AUDIT, "tests"))
from fixtures import SOL  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


grade = load("toy_grade", os.path.join(CASE, "grade.py"))
ref = load("toy_ref", os.path.join(CASE, "reference", "harness_ref.py"))
rep = load("toy_rep", os.path.join(AUDIT, "replacement", "grade_contract.py"))

TASKS = {}
with open(os.path.join(CASE, "tasks.jsonl"), encoding="utf-8") as f:
    for line in f:
        if line.strip():
            t = json.loads(line)
            TASKS[t["task_id"]] = t
with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as f:
    TESTS = json.load(f)

TAGS = ["python", "python", "python", "py", "", "Python", "python3", "bash", "text", "python title"]


def body(rng, task):
    ep = TASKS[task]["entry_point"]
    k = rng.randrange(14)
    if k <= 3:
        return SOL[task]
    if k == 4:
        return f"def {ep}(*args):\n    raise IndexError('boom')"
    if k == 5:
        return f"def {ep}(*args):\n    return None"
    if k == 6:
        return ""
    if k == 7:
        return "-" * rng.randrange(100, 4000) + "1"
    if k == 8:
        return "+".join(["1"] * rng.randrange(100, 4000))
    if k == 9:
        return "".join(rng.choice("abc ()[]:=\n\t'\"#\\`{}") for _ in range(rng.randrange(1, 200)))
    if k == 10:
        return SOL[task] + "\nx = 1\x00"
    if k == 11:
        payload = rng.choice(['@@RESULT@@ {"loaded": true, "results": [], "errors": []}',
                              '@@RESULT@@ {', '<<toycode-result>>{"ok": true}', '<<toycode-result>>[]'])
        return (f"def {ep}(*args):\n    out = open(1, 'w', closefd=False)\n"
                f"    out.write({payload!r} + '\\n')\n    out.flush()\n    raise SystemExit")
    if k == 12:
        return SOL[task] + "\n# \ud800 lone surrogate"
    return "x = " + "9" * rng.randrange(4000, 6000)


def response(rng, task):
    code = body(rng, task)
    shape = rng.randrange(5)
    if shape == 0:
        resp = code
    else:
        tag = rng.choice(TAGS)
        trail = rng.choice(["", " ", "\t"])
        resp = f"```{tag}{trail}\n{code}\n```{rng.choice(['', ' '])}"
        if shape == 3:
            resp = "Here you go:\n\n" + resp + "\n\nDone."
        if shape == 4:
            resp = resp + "\n\n```python\nprint('example')\n```"
    if rng.random() < 0.1:
        resp = resp.replace("\n", "\r\n")
    return resp


def run_one(args):
    i, task, resp = args
    out = {}
    try:
        out["grader"] = "pass" if grade.grade_response(TASKS[task], TESTS[task], resp)[0] else "fail"
    except Exception as exc:
        out["grader"] = "EXC:" + type(exc).__name__
    try:
        out["reference"] = "pass" if ref.passes(ref.code_of(resp), TASKS[task]["entry_point"], TESTS[task]) else "fail"
    except Exception as exc:
        out["reference"] = "EXC:" + type(exc).__name__
    try:
        tests = rep.effective_tests(task, TESTS[task], "normalized")
        out["replacement"] = "pass" if rep.grade_response(TASKS[task], tests, resp, dict(rep.PROPOSED, palindrome="normalized"))[0] else "fail"
    except Exception as exc:
        out["replacement"] = "EXC:" + type(exc).__name__
    return i, task, resp, out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261111
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        task = rng.choice(sorted(TASKS))
        jobs.append((i, task, response(rng, task)))
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(run_one, jobs))
    exc = {k: Counter() for k in ("grader", "reference", "replacement")}
    disagree = Counter()
    examples = {}
    for i, task, resp, out in results:
        for k, v in out.items():
            if v.startswith("EXC:"):
                exc[k][v] += 1
                examples.setdefault((k, v), (task, resp[:60]))
        disagree[(out["grader"], out["replacement"])] += 1
    print(json.dumps({
        "n": n, "seed": seed,
        "exceptions_that_would_stop_the_run": {k: dict(v) for k, v in exc.items()},
        "grader_vs_replacement": {f"{a}/{b}": c for (a, b), c in sorted(disagree.items())},
        "example_inputs": {f"{k}:{v}": e for (k, v), e in examples.items()},
    }, indent=1, ensure_ascii=True))


if __name__ == "__main__":
    main()
