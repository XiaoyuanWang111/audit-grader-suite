"""Run the grader under audit, the reference and the replacement on a list of responses.

The grader and the reference run through their own command lines, as the
evaluation runs them (python -B, same interpreter), so the whole pipeline is
exercised: JSONL loading, extraction, comparison, verdict writing and the
score table. Scratch files go to audit/tests/_out/.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"
OUT = W / "audit" / "tests" / "_out"
GRADER = CASE / "grade.py"
REFERENCE = CASE / "reference" / "grade_ref.py"
PROBLEMS = CASE / "problems.jsonl"

_spec = importlib.util.spec_from_file_location("grade_contract", W / "audit" / "replacement" / "grade_contract.py")
replacement = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(replacement)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def run_grader(responses_path, out_path, problems_path=PROBLEMS):
    """Run case/grade.py. Returns (returncode, stdout, stderr, verdict rows or None)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    p = subprocess.run([sys.executable, "-B", str(GRADER), "--problems", str(problems_path),
                        "--responses", str(responses_path), "--out", str(out_path)],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(CASE))
    rows = read_jsonl(out_path) if out_path.exists() else None
    return p.returncode, p.stdout, p.stderr, rows


def run_reference(responses_path, out_path, problems_path=PROBLEMS):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    p = subprocess.run([sys.executable, "-B", str(REFERENCE), str(problems_path),
                        str(responses_path), str(out_path)],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(CASE))
    rows = read_jsonl(out_path) if out_path.exists() else None
    return p.returncode, p.stdout, p.stderr, rows


def as_response_rows(items, model="fixture"):
    """items: dicts with id, problem_id, response."""
    return [{"id": it["id"], "model": it.get("model", model), "problem_id": it["problem_id"],
             "response": it["response"]} for it in items]


def grade_all(items, tag):
    """Grade items with all three graders. Returns dict id -> {grader, reference, replacement}."""
    rows = as_response_rows(items)
    resp = OUT / f"{tag}_responses.jsonl"
    write_jsonl(resp, rows)
    rc, so, se, g = run_grader(resp, OUT / f"{tag}_grader.jsonl")
    if g is None:
        raise RuntimeError(f"grader failed rc={rc}: {se[-500:]}")
    rc2, so2, se2, r = run_reference(resp, OUT / f"{tag}_reference.jsonl")
    if r is None:
        raise RuntimeError(f"reference failed rc={rc2}: {se2[-500:]}")
    refs = {pid: p["answer"] for pid, p in ((x["problem_id"], x) for x in read_jsonl(PROBLEMS))}
    out = {}
    for it, gv, rv in zip(rows, g, r):
        assert gv["id"] == it["id"] and rv["id"] == it["id"]
        lab, num = replacement.verdict(it["response"], refs[it["problem_id"]])
        out[it["id"]] = {"grader": gv["verdict"], "grader_extracted": gv["extracted"],
                         "reference": rv["verdict"], "reference_answer": rv["answer"],
                         "replacement": lab, "replacement_extracted": num}
    return out


def binary(label):
    """Score-level view: correct vs not correct."""
    return "correct" if label == "correct" else "not_correct"
