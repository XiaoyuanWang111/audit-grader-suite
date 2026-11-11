"""Write the exact counterexample inputs that AUDIT.md cites, one JSONL response file per finding.

Usage: python -B audit/scripts/make_repro.py
Each row's `model` names the counterexample, so the grader's per-model table shows each verdict on its own row.
"""

import json
import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(os.path.dirname(AUDIT), "case")
sys.path.insert(0, os.path.join(AUDIT, "tests"))
from fixtures import (FIB, FORGE_FD1, FORGE_PRINT, MALFORMED_FD1, REPR_PROXY, SET_ORDER_RLE,  # noqa: E402
                      SOL, fenced)

stored = {}
with open(os.path.join(CASE, "responses.jsonl"), encoding="utf-8") as f:
    for line in f:
        if line.strip():
            r = json.loads(line)
            stored[r["id"]] = r


ENTRY = {}
with open(os.path.join(CASE, "tasks.jsonl"), encoding="utf-8") as f:
    for line in f:
        if line.strip():
            t = json.loads(line)
            ENTRY[t["task_id"]] = t["entry_point"]


def copy(rid):
    r = stored[rid]
    return {"id": rid, "model": f"stored-{rid}", "task_id": r["task_id"], "response": r["response"]}


def row(name, task, response):
    return {"id": name, "model": name, "task_id": task, "response": response}


FILES = {
    "F1_ignored_exceptions": [
        row("F1-empty-response", "t07", ""),
        row("F1-raise-ValueError", "t07", fenced("def fib(n):\n    raise ValueError")),
        row("F1-t03-raise-ValueError", "t03", fenced("def parse_duration(text):\n    raise ValueError(text)")),
        copy("c02"), copy("c22"), copy("c40"),
    ],
    "F2_json_round_trip": [
        copy("c16"), copy("c31"),
        row("F2-repr-proxy", "t06", fenced(REPR_PROXY)),
    ],
    "F3_python_tag_only": [
        row("F3-tag-py", "t07", fenced(FIB, "py")),
        row("F3-no-tag", "t07", fenced(FIB, "")),
        row("F3-bash-block-first", "t07", "```bash\npip install toycode\n```\n\n" + fenced(FIB)),
    ],
    "F4_forged_result": [
        row("F4-fd1-systemexit", "t07", fenced(FORGE_FD1)),
        row("F4-builtins-print", "t07", fenced(FORGE_PRINT)),
    ],
    "F5_parse_recursion": [
        row("F5-control", "t07", fenced(FIB)),
        row("F5-deep-unary", "t07", "-" * 2996 + "1"),
    ],
    "F5_malformed_forge": [
        row("F5-control", "t07", fenced(FIB)),
        row("F5-malformed-line", "t07", fenced(MALFORMED_FD1)),
    ],
    "F6_duplicate_rows": [
        {"id": "d1", "model": "F6-dup", "task_id": "t07", "response": fenced(FIB)},
        {"id": "d2", "model": "F6-dup", "task_id": "t07", "response": fenced(FIB)},
    ],
    "F1_whole_benchmark": (
        [{"id": f"v{t}", "model": "F1-always-ValueError", "task_id": t,
          "response": fenced(f"def {ep}(*args):\n    raise ValueError")} for t, ep in ENTRY.items()]
        + [{"id": f"e{t}", "model": "F1-empty-response", "task_id": t, "response": ""} for t in ENTRY]),
    "G2_hash_seed": [row("G2-set-order", "t06", SET_ORDER_RLE)],
    "D_palindrome": [copy("c05"), copy("c06"), copy("c07"), copy("c08")],
    "D_crlf": [row("D-crlf", "t07", fenced(FIB).replace("\n", "\r\n"))],
}

os.makedirs(os.path.join(AUDIT, "repro"), exist_ok=True)
for name, rows in FILES.items():
    with open(os.path.join(AUDIT, "repro", name + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
print("wrote", len(FILES), "files")
