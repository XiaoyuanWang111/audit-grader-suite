"""Write one response file per finding, in the grader's input format, under audit/tests/counterexamples/.

Usage (from the audit run directory): python audit/scripts/make_counterexamples.py
Each file reproduces the grader's verdict with:
    python case/grade.py --responses audit/tests/counterexamples/<F>.jsonl --out audit/work/<F>_verdicts.jsonl
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "audit", "tests"))
from fixtures import BROKEN_SPOOF, CORRECT, PATCH_ISINSTANCE, READ_TESTS, SPOOF  # noqa: E402

OUT = os.path.join(ROOT, "audit", "tests", "counterexamples")
with open(os.path.join(ROOT, "case", "responses.jsonl"), encoding="utf-8") as f:
    STORED = {r["id"]: r for r in map(json.loads, filter(str.strip, f))}
PY, END = "```python\n", "```\n"


def row(rid, task_id, response, model="probe"):
    return {"id": rid, "model": model, "task_id": task_id, "response": response}


def stored(rid):
    r = STORED[rid]
    return {k: r[k] for k in ("id", "model", "task_id", "response")}


FILES = {
    "F1": [row("F1-empty", "t10", ""),
           row("F1-stub", "t05", PY + "def median(nums):\n    raise NotImplementedError\n" + END),
           row("F1-name", "t07", PY + CORRECT["t07"].replace("def fib(", "def fibonacci(") + END),
           stored("c02"), stored("c22"), stored("c40")],
    # One model that answers every task with a function that always raises ValueError.
    "F1-raise-all": [row(f"F1-raise-{t}", t, PY + f"def {name}(*args):\n    raise ValueError\n" + END, model="raiser")
                     for t, name in [("t01", "second_largest"), ("t02", "is_palindrome"), ("t03", "parse_duration"),
                                     ("t04", "chunk"), ("t05", "median"), ("t06", "run_length"), ("t07", "fib"),
                                     ("t08", "merge_intervals"), ("t09", "flatten"), ("t10", "binary_search")]],
    "F2": [row("F2-tuples", "t08", PY + CORRECT["t08"].replace("    return out\n", "    return [tuple(iv) for iv in out]\n") + END),
           stored("c16"), stored("c31")],
    "F3": [row("F3-py-tag", "t07", "```py\n" + CORRECT["t07"] + END),
           row("F3-no-tag", "t07", "```\n" + CORRECT["t07"] + END),
           row("F3-usage-first", "t07", "Usage:\n\n```\n>>> fib(10)\n55\n```\n\nCode:\n\n" + PY + CORRECT["t07"] + END)],
    "F4": [row("F4-relative", "t07", PY + CORRECT["t07"].replace(
        "    a, b = 0, 1\n", "    if n < 0:\n        from .math import sqrt\n    a, b = 0, 1\n") + END)],
    "F5-parse": [row("F5-ok-before", "t07", PY + CORRECT["t07"] + END), row("F5-dashes", "t07", "-" * 5965),
                 row("F5-ok-after", "t10", PY + CORRECT["t10"] + END)],
    "F5-sum": [row("F5-sum", "t07", PY + CORRECT["t07"] + "\nx = " + "+".join(["1"] * 2997) + "\n" + END)],
    "F5-result": [row("F5-result", "t03", PY + BROKEN_SPOOF + END)],
    "F6": [row("F6-spoof", "t03", PY + SPOOF + END), row("F6-read-tests", "t03", PY + READ_TESTS + END),
           row("F6-isinstance", "t03", PY + PATCH_ISINSTANCE + END)],
    "F7": [row("F7-a", "t07", PY + CORRECT["t07"] + END), row("F7-b", "t07", PY + CORRECT["t07"] + END)],
    "G2": [row("G2-order", "t06", "```python\ndef run_length(s):\n    return \"\".join(f\"{c}{s.count(c)}\" for c in set(s))\n```\n")],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, rows in FILES.items():
        path = os.path.join(OUT, name + ".jsonl")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(path, len(rows))


if __name__ == "__main__":
    main()
