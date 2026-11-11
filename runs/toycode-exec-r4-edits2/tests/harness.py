"""Run the three ToyCode graders on response rows, the way the evaluation runs them (CLI, same interpreter)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
TMP = os.path.join(AUDIT, "tmp")

GRADERS = {
    "grader": lambda resp, out, sw: [sys.executable, "-B", os.path.join(CASE, "grade.py"),
                                     "--responses", resp, "--out", out],
    "reference": lambda resp, out, sw: [sys.executable, "-B", os.path.join(CASE, "reference", "harness_ref.py"),
                                        os.path.join(CASE, "tasks.jsonl"), os.path.join(CASE, "tests.json"),
                                        resp, out],
    "replacement": lambda resp, out, sw: [sys.executable, "-B",
                                          os.path.join(AUDIT, "replacement", "grade_contract.py"),
                                          "--responses", resp, "--out", out, *sw],
}


def run(kind, rows, switches=(), env=None, timeout=600):
    """Grade rows with one grader. Returns dict(returncode, verdicts={id: verdict}, stdout, stderr, scores)."""
    os.makedirs(TMP, exist_ok=True)
    work = tempfile.mkdtemp(dir=TMP)
    try:
        resp = os.path.join(work, "responses.jsonl")
        out = os.path.join(work, "verdicts.jsonl")
        with open(resp, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        full_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        if env:
            full_env.update(env)
        proc = subprocess.run(GRADERS[kind](resp, out, list(switches)), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=full_env, timeout=timeout,
                              stdin=subprocess.DEVNULL)
        verdicts = {}
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        v = json.loads(line)
                        verdicts[v["id"]] = v["verdict"]
        scores = {}
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in ("model", "options:", "warning:"):
                try:
                    scores[parts[0]] = float(parts[-1])
                except ValueError:
                    pass
        return {"returncode": proc.returncode, "verdicts": verdicts, "stdout": proc.stdout,
                "stderr": proc.stderr, "scores": scores}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def row(fid, task_id, response, model=None):
    return {"id": fid, "model": model or fid, "task_id": task_id, "response": response}
