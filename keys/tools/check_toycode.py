"""Private checks for cases/toycode-exec. Part of the keys; never give this to an auditor.

Oracle: the TASK.md grading rule with one switch per planted defect.
  C1  an exception raised by a call in a test without "raises" (or a missing function) does not fail the task
  C2  only blocks opened by exactly ```python are recognized as fenced blocks
  C3  return values are compared after a JSON round trip
One child run per response records every test outcome, so every switch combination is evaluated from it.
"""

import sys as _sys

_sys.dont_write_bytecode = True
import ast
import builtins
import copy
import io
import json
import os
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "cases", "toycode-exec"))
PY = sys.executable
ALLOWED = {"math", "itertools", "collections", "functools", "re", "heapq", "bisect", "string", "typing"}
ANY_FENCE = re.compile(r"^```[A-Za-z0-9_+-]*[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
PY_FENCE = re.compile(r"^```python[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
MARK = "##ORACLE## "
ALL_ON = {"C1": True, "C2": True, "C3": True}
ALL_OFF = {"C1": False, "C2": False, "C3": False}


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ------------------------------------------------------------------ child


def child(job_path):
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)
    real = sys.stdout
    sys.stdout = io.StringIO()
    rec = {"loaded": True, "tests": []}
    try:
        ns = {"__name__": "candidate"}
        try:
            exec(compile(job["code"], "candidate.py", "exec"), ns)
        except BaseException as exc:
            rec = {"loaded": False, "error": repr(exc)}
        else:
            fn = ns.get(job["entry_point"])
            for t in job["tests"]:
                out = {}
                try:
                    v = fn(*copy.deepcopy(t["args"]))
                except Exception as exc:
                    out["exc"] = type(exc).__name__
                    if "raises" in t:
                        out["exc_matches"] = isinstance(exc, getattr(builtins, t["raises"]))
                else:
                    out["exc"] = None
                    if "raises" not in t:
                        try:
                            out["eq"] = bool(v == t["expected"])
                        except Exception:
                            out["eq_error"] = True
                        try:
                            out["json_eq"] = json.loads(json.dumps(v, default=repr)) == t["expected"]
                        except Exception:
                            out["json_error"] = True
                rec["tests"].append(out)
    finally:
        sys.stdout = real
    print(MARK + json.dumps(rec))


# ------------------------------------------------------------------ parent


def extract(response, c2):
    m = (PY_FENCE if c2 else ANY_FENCE).search(response)
    return m.group(1) if m else response


def imports_ok(code):
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


_cache = {}


def run_child(code, entry, tests):
    key = (code, entry, json.dumps(tests))
    if key in _cache:
        return _cache[key]
    with tempfile.TemporaryDirectory() as td:
        job = os.path.join(td, "job.json")
        with open(job, "w", encoding="utf-8") as f:
            json.dump({"code": code, "entry_point": entry, "tests": tests}, f)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            p = subprocess.run(
                [PY, os.path.abspath(__file__), "--child", job],
                cwd=td,
                env=env,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=4.0,
            )
            marks = [l for l in p.stdout.splitlines() if l.startswith(MARK)]
            rec = json.loads(marks[-1][len(MARK) :]) if marks else {"no_result": True}
        except subprocess.TimeoutExpired:
            rec = {"timeout": True}
    _cache[key] = rec
    return rec


def verdict(response, task, tests, sw):
    code = extract(response, sw["C2"])
    if not imports_ok(code):
        return "fail"
    rec = run_child(code, task["entry_point"], tests)
    if rec.get("timeout") or rec.get("no_result") or not rec.get("loaded"):
        return "fail"
    for t, out in zip(tests, rec["tests"], strict=False):
        if "raises" in t:
            if out["exc"] is None or not out["exc_matches"]:
                return "fail"
            continue
        if out["exc"] is not None:
            if sw["C1"]:
                continue
            return "fail"
        if sw["C3"]:
            if out.get("json_error"):
                return "fail"
            if not out["json_eq"]:
                return "fail"
        else:
            if out.get("eq_error") or not out.get("eq"):
                return "fail"
    return "pass"


def run_grader(responses_path):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "v.jsonl")
        p = subprocess.run(
            [PY, os.path.join(CASE, "grade.py"), "--responses", responses_path, "--out", out],
            capture_output=True,
            text=True,
        )
        return load_jsonl(out), p.stdout


def run_reference(responses_path):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "v.jsonl")
        p = subprocess.run(
            [
                PY,
                os.path.join(CASE, "reference", "harness_ref.py"),
                os.path.join(CASE, "tasks.jsonl"),
                os.path.join(CASE, "tests.json"),
                responses_path,
                out,
            ],
            capture_output=True,
            text=True,
        )
        return load_jsonl(out), p.stdout


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def scores(rows, n_tasks=10):
    out = {}
    for m in sorted({r["model"] for r in rows}):
        out[m] = round(100.0 * sum(r["verdict"] == "pass" for r in rows if r["model"] == m) / n_tasks, 1)
    return out


def mutate(rng, response, task):
    """Variants that stress extraction, exceptions and comparison; none of them loops forever."""
    entry = task["entry_point"]
    kind = rng.choice(["tag", "tag", "tuple", "raise", "drop", "import", "syntax", "empty", "prose", "none"])
    text = response
    if kind == "tag":
        tag = rng.choice(["py", "", "Python", "python3", "python ", "python", "PY"])
        text = re.sub(r"^```python", "```" + tag, text, count=1, flags=re.M)
    elif kind == "tuple":
        text = text.replace("return ", "return tuple(", 1)
        text = re.sub(r"(return tuple\(.*)$", r"\1)", text, count=1, flags=re.M)
    elif kind == "raise":
        text = text.replace(
            f"def {entry}(",
            f"def {entry}(*args):\n    if not args[0]:\n        raise "
            "IndexError('empty')\n    return _orig(*args)\n\ndef _orig(",
            1,
        )
    elif kind == "drop":
        text = text.replace(f"def {entry}(", f"def {entry}_impl(", 1)
    elif kind == "import":
        text = text.replace(
            "```python\n",
            "```python\n"
            + rng.choice(["import os\n", "import math\n", "from typing import List\n", "import statistics\n"]),
            1,
        )
    elif kind == "syntax":
        text = text.replace("return", "retrun", 1)
    elif kind == "empty":
        text = rng.choice(["", " ", "```python\n```", "I cannot solve this."])
    elif kind == "prose":
        text = "Here is my answer.\n" + text + "\nThis should work."
    return text


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
        return 0
    tasks = {t["task_id"]: t for t in load_jsonl(os.path.join(CASE, "tasks.jsonl"))}
    with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as f:
        tests = json.load(f)
    responses = load_jsonl(os.path.join(CASE, "responses.jsonl"))
    ok = True

    g_rows, g_out = run_grader(os.path.join(CASE, "responses.jsonl"))
    r_rows, r_out = run_reference(os.path.join(CASE, "responses.jsonl"))

    def oracle(rows, sw):
        return [
            {
                "id": r["id"],
                "model": r["model"],
                "verdict": verdict(r["response"], tasks[r["task_id"]], tests[r["task_id"]], sw),
            }
            for r in rows
        ]

    o_on, o_off = oracle(responses, ALL_ON), oracle(responses, ALL_OFF)
    for g, o in zip(g_rows, o_on, strict=False):
        if g["verdict"] != o["verdict"]:
            ok = False
            print("MISMATCH grader/oracle", g, o)
    for r, o in zip(r_rows, o_off, strict=False):
        if r["verdict"] != o["verdict"]:
            ok = False
            print("MISMATCH reference/oracle", r, o)
    print("panel equality checks:", "OK" if ok else "FAILED")

    n = len(responses)
    gp = sum(o["verdict"] == "pass" for o in o_on)
    cp = sum(o["verdict"] == "pass" for o in o_off)
    print(
        f"\npanel: {n} responses; grader passes {gp} ({100.0 * gp / n:.1f}%), reference/contract passes {cp} "
        f"({100.0 * cp / n:.1f}%)"
    )
    print("per-model score: grader", scores(o_on), " contract/reference", scores(o_off))
    print("grader stdout:\n" + g_out)
    print("reference stdout:\n" + r_out)

    print("per-defect verdict changes (grader vs grader with only that defect removed):")
    for d in ["C1", "C2", "C3"]:
        fixed = oracle(responses, dict(ALL_ON, **{d: False}))
        ch = [a["id"] for a, b in zip(o_on, fixed, strict=False) if a["verdict"] != b["verdict"]]
        print(f"  {d}: {len(ch)}/{n} {ch}; scores with {d} fixed {scores(fixed)}")
    print("  panel fence tags:", sorted({m for r in responses for m in re.findall(r"^```(\S*)", r["response"], re.M)}))
    print("  responses without a fence:", [r["id"] for r in responses if "```" not in r["response"]])
    lit = [
        r["id"]
        for r in responses
        if r["task_id"] == "t02" and verdict(r["response"], tasks["t02"], tests["t02"], ALL_OFF) == "fail"
    ]
    print("  D-palindrome: t02 responses failing only on the normalized test:", lit)
    trap = [r["id"] for r in responses if not imports_ok(extract(r["response"], False))]
    print("  trap: responses failing the import check:", trap)

    # Counterexamples and content-free responses
    print("\ncounterexamples:")
    ce = [
        (
            "CE-C1",
            "t06",
            "```python\ndef run_length(s):\n    out = s[0]\n    n "
            "= 1\n    for c in s[1:]:\n        if c == out[-1]:\n    "
            "        n += 1\n        else:\n            out += str(n) "
            "+ c\n            n = 1\n    return out + str(n)\n```",
        ),
        (
            "CE-C2",
            "t07",
            "```py\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```",
        ),
        (
            "CE-C2b",
            "t07",
            "```\ndef fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```",
        ),
        (
            "CE-C3",
            "t09",
            "```python\ndef flatten(nested):\n    out = []\n    for x in nested:\n        "
            "out.extend(flatten(x) if isinstance(x, list) else [x])\n    return tuple(out)\n```",
        ),
        ("CE-T", "t05", "```python\nimport statistics\n\ndef median(nums):\n    return statistics.median(nums)\n```"),
        ("CE-D", "t02", "```python\ndef is_palindrome(s):\n    return s == s[::-1]\n```"),
    ]
    cf = []
    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8") as f:
        template = f.read()
    for tid in sorted(tasks):
        cf.append(("CF-empty", tid, ""))
        cf.append(("CF-restate", tid, template.replace("{prompt}", tasks[tid]["prompt"])))
        cf.append(("CF-repeat", tid, (tasks[tid]["prompt"].splitlines()[0] + "\n") * 3))
        cf.append(("CF-stub", tid, "```python\n" + tasks[tid]["prompt"] + "```"))
    rows = [
        {"id": f"x{i:03d}", "model": cid, "task_id": tid, "response": text} for i, (cid, tid, text) in enumerate(ce + cf)
    ]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "x.jsonl")
        write_jsonl(path, rows)
        g_x, _ = run_grader(path)
        r_x, _ = run_reference(path)
    for row, g, r in zip(rows, g_x, r_x, strict=False):
        o_on_v = verdict(row["response"], tasks[row["task_id"]], tests[row["task_id"]], ALL_ON)
        o_off_v = verdict(row["response"], tasks[row["task_id"]], tests[row["task_id"]], ALL_OFF)
        if g["verdict"] != o_on_v or r["verdict"] != o_off_v:
            ok = False
            print("  MISMATCH", row["model"], row["task_id"], g["verdict"], o_on_v, r["verdict"], o_off_v)
        if row["model"].startswith("CE"):
            print(
                f"  {row['model']:<8} {row['task_id']} grader={g['verdict']} "
                f"({g['detail']}) contract={o_off_v} reference={r['verdict']}"
            )
    for kind in ["CF-empty", "CF-restate", "CF-repeat", "CF-stub"]:
        passes = [
            row["task_id"] for row, g in zip(rows, g_x, strict=False) if row["model"] == kind and g["verdict"] == "pass"
        ]
        cpass = [
            row["task_id"] for row, r in zip(rows, r_x, strict=False) if row["model"] == kind and r["verdict"] == "pass"
        ]
        print(f"  {kind}: grader passes {len(passes)} tasks {passes}; contract passes {cpass}")

    # Fuzz
    rng = random.Random(20261106)
    fz = []
    for i in range(240):
        base = rng.choice(responses)
        fz.append(
            {
                "id": f"f{i:03d}",
                "model": "fz",
                "task_id": base["task_id"],
                "response": mutate(rng, base["response"], tasks[base["task_id"]]),
            }
        )
    fz = [
        f
        for f in fz
        if f["task_id"] not in ("t07",) or "fib(n - 1) + fib(n - 2)" not in f["response"] or "lru_cache" in f["response"]
    ]
    fz = [f for f in fz if "lo = mid\n" not in f["response"]]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "f.jsonl")
        write_jsonl(path, fz)
        g_f, _ = run_grader(path)
        r_f, _ = run_reference(path)
    o_f_on, o_f_off = oracle(fz, ALL_ON), oracle(fz, ALL_OFF)
    bad_g = [
        (a["id"], a["verdict"], b["verdict"]) for a, b in zip(g_f, o_f_on, strict=False) if a["verdict"] != b["verdict"]
    ]
    bad_r = [
        (a["id"], a["verdict"], b["verdict"]) for a, b in zip(r_f, o_f_off, strict=False) if a["verdict"] != b["verdict"]
    ]
    print(f"\nfuzz {len(fz)}: grader/oracle mismatches {bad_g}; reference/oracle mismatches {bad_r}")
    for d in ["C1", "C2", "C3"]:
        fixed = oracle(fz, dict(ALL_ON, **{d: False}))
        changed = sum(a["verdict"] != b["verdict"] for a, b in zip(o_f_on, fixed, strict=False))
        print(f"  fuzz verdicts changed by {d}: {changed}")
    if bad_g or bad_r:
        ok = False
    print("\nALL CHECKS", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
