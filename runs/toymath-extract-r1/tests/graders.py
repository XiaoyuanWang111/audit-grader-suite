"""Run each ToyMath grader the way the evaluation runs it, on a list of responses.

grade.py and the reference run as subprocesses from case/, with the command lines in case/TASK.md and the
same interpreter as the tests. The replacement grader (audit/scripts/grade_contract.py) runs in-process.
Every function returns {response id: (extracted, verdict)} with three labels: the reference's `incorrect`
with `"answer": null` is mapped to `no_answer` (it has only two labels; see audit/ISSUE.md, step 1 addendum).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
TMP = os.path.join(ROOT, "audit", "out", "tmp")
sys.path.insert(0, os.path.join(ROOT, "audit", "scripts"))

import grade_contract  # noqa: E402


def _write(rows, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def as_rows(fixtures, model="fixture"):
    """Turn fixtures (dicts with id, problem_id, response) into response rows."""
    return [{"id": f["id"], "model": f.get("model", model), "problem_id": f["problem_id"],
             "response": f["response"]} for f in fixtures]


def run_grade_py(rows, problems=None):
    """Run `python grade.py --responses R --out V` from case/. Returns (verdicts, stdout, returncode)."""
    os.makedirs(TMP, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        rpath, vpath = os.path.join(d, "responses.jsonl"), os.path.join(d, "verdicts.jsonl")
        _write(rows, rpath)
        cmd = [sys.executable, "grade.py", "--responses", rpath, "--out", vpath]
        if problems:
            cmd += ["--problems", problems]
        p = subprocess.run(cmd, cwd=CASE, capture_output=True, text=True, encoding="utf-8")
        verdicts = {v["id"]: (v["extracted"], v["verdict"]) for v in _read(vpath)} if os.path.exists(vpath) else None
        return verdicts, p.stdout + p.stderr, p.returncode


def run_reference(rows):
    """Run `python reference/grade_ref.py problems.jsonl R V` from case/. Returns (verdicts, stdout, returncode)."""
    os.makedirs(TMP, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        rpath, vpath = os.path.join(d, "responses.jsonl"), os.path.join(d, "verdicts.jsonl")
        _write(rows, rpath)
        cmd = [sys.executable, os.path.join("reference", "grade_ref.py"), "problems.jsonl", rpath, vpath]
        p = subprocess.run(cmd, cwd=CASE, capture_output=True, text=True, encoding="utf-8")
        verdicts = None
        if os.path.exists(vpath):
            verdicts = {}
            for v in _read(vpath):
                label = v["verdict"]
                if v["answer"] is None:
                    label = "no_answer"
                verdicts[v["id"]] = (v["answer"], label)
        return verdicts, p.stdout + p.stderr, p.returncode


def scores_grade_py(stdout):
    """grade.py's table: model, correct, incorrect, no_answer, score. Returns {model: score}."""
    out = {}
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 5:
            out[parts[0]] = float(parts[4])
    return out


def scores_reference(stdout):
    """The reference's table: model, correct, number of problems, score. Returns {model: score}."""
    out = {}
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 4:
            out[parts[0]] = float(parts[3])
    return out


def run_replacement(rows, sw=None):
    """The contract implementation, in-process, with switches sw (default: every proposed reading)."""
    refs = {p["problem_id"]: p["answer"] for p in _read(os.path.join(CASE, "problems.jsonl"))}
    sw = sw or grade_contract.PROPOSED
    return {r["id"]: grade_contract.grade_response(r["response"], refs[r["problem_id"]], sw) for r in rows}
