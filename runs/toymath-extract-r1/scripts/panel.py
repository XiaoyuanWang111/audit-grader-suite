"""Step 5: grade the 48 stored responses (the panel) with every grader, and with each decision reading.

Usage: python -I audit/scripts/panel.py   (writes audit/out/panel_verdicts.jsonl and audit/out/panel_summary.json)

grade.py and the reference run as the evaluation runs them (case/TASK.md), twice each, to check that their
verdicts repeat. The replacement runs through its command line with the proposed readings, then with each
decision entry's reading (b) alone, then with the readings that grade.py and the reference use.
"""
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(ROOT, "case")
OUT = os.path.join(ROOT, "audit", "out")
sys.path.insert(0, os.path.join(ROOT, "audit", "scripts"))
import grade_contract  # noqa: E402

RESP = os.path.join(CASE, "responses.jsonl")


def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode:
        raise SystemExit("failed: %s\n%s" % (" ".join(cmd), p.stdout + p.stderr))
    return p.stdout


def main():
    rows = read(RESP)
    pids = [p["problem_id"] for p in read(os.path.join(CASE, "problems.jsonl"))]
    runs = {}
    tables = {}
    for k in (1, 2):
        v = os.path.join(OUT, "panel_grade_py_run%d.jsonl" % k)
        tables["grade_py_run%d" % k] = run([sys.executable, "grade.py", "--out", v], CASE)
        runs["grade_py_run%d" % k] = {r["id"]: (r["extracted"], r["verdict"]) for r in read(v)}
        v = os.path.join(OUT, "panel_reference_run%d.jsonl" % k)
        tables["reference_run%d" % k] = run([sys.executable, os.path.join("reference", "grade_ref.py"),
                                             "problems.jsonl", "responses.jsonl", v], CASE)
        runs["reference_run%d" % k] = {r["id"]: (r["answer"], "no_answer" if r["answer"] is None else r["verdict"])
                                       for r in read(v)}
    configs = [("replacement", [])] + [("rep_b:" + e, [e]) for e in grade_contract.ENTRY.values()] + [
        ("rep_as_grade_py_readings", ["D-digits"]),
        ("rep_as_reference_readings", ["D-answer-line-form", "D-digits"])]
    for name, entries in configs:
        sw = grade_contract.switches_for(entries)
        v = os.path.join(OUT, "panel_%s.jsonl" % name.replace(":", "_"))
        args = [sys.executable, "-I", os.path.join(ROOT, "audit", "scripts", "grade_contract.py"), "--responses", RESP,
                "--out", v] + sum([["--" + k.replace("_", "-"), sw[k]] for k in sw], [])
        tables[name] = run(args, ROOT)
        runs[name] = {r["id"]: (r["extracted"], r["verdict"]) for r in read(v)}
    repeat = {g: runs[g + "_run1"] == runs[g + "_run2"] and tables[g + "_run1"] == tables[g + "_run2"]
              for g in ("grade_py", "reference")}
    runs["grade_py"] = runs.pop("grade_py_run1")
    runs["reference"] = runs.pop("reference_run1")
    runs.pop("grade_py_run2")
    runs.pop("reference_run2")
    models = sorted({r["model"] for r in rows})

    def score(name, model, denominator="12"):
        mine = [r for r in rows if r["model"] == model]
        c = collections.Counter(runs[name][r["id"]][1] for r in mine)
        if denominator == "graded":  # grade.py's own score: correct / (correct + incorrect)
            graded = c["correct"] + c["incorrect"]
            return round(100.0 * c["correct"] / graded, 1) if graded else 0.0
        return round(100.0 * c["correct"] / len(pids), 1)

    summary = {"repeat_identical": repeat, "scores": {}, "label_counts": {}, "disagreements": {},
               "truncated": [], "no_answer": {}, "coverage": {}}
    for name in runs:
        summary["scores"][name] = {m: score(name, m, "graded" if name == "grade_py" else "12") for m in models}
        summary["label_counts"][name] = dict(collections.Counter(v[1] for v in runs[name].values()))
        summary["no_answer"][name] = sorted(i for i, v in runs[name].items() if v[1] == "no_answer")
        summary["coverage"][name] = "%d of %d responses have a verdict" % (len(runs[name]), len(pids) * len(models))
    summary["scores"]["grade_py_if_denominator_12"] = {m: score("grade_py", m, "12") for m in models}
    for name in runs:
        if name == "replacement":
            continue
        d = []
        for r in rows:
            a, b = runs["replacement"][r["id"]], runs[name][r["id"]]
            if a[1] != b[1]:
                d.append({"id": r["id"], "model": r["model"], "problem_id": r["problem_id"],
                          "replacement": a, name: b, "answer_line": [l for l in r["response"].splitlines()
                                                                     if l.lstrip().startswith("Answer:")][-1:]})
        summary["disagreements"][name] = d
    for r in rows:
        if r["finish_reason"] != "stop":
            summary["truncated"].append({"id": r["id"], "model": r["model"], "problem_id": r["problem_id"],
                                         "chars": len(r["response"]),
                                         "has_answer_line": any(l.lstrip().startswith("Answer:")
                                                                for l in r["response"].splitlines()),
                                         "verdicts": {n: runs[n][r["id"]][1] for n in ("grade_py", "reference",
                                                                                       "replacement")}})
    summary["reasoning_markers"] = sum(1 for r in rows if any(t in r["response"] for t in
                                                              ("<think>", "</think>", "<reasoning>")))
    with open(os.path.join(OUT, "panel_verdicts.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "model": r["model"], "problem_id": r["problem_id"],
                                "finish_reason": r["finish_reason"],
                                "verdicts": {n: runs[n][r["id"]] for n in runs}}) + "\n")
    with open(os.path.join(OUT, "panel_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("repeat identical:", repeat)
    print("grade.py table as printed:\n" + tables["grade_py_run1"])
    print("reference table as printed:\n" + tables["reference_run1"])
    print("replacement table as printed:\n" + tables["replacement"])
    print("%-34s" % "scores" + "".join("%11s" % m for m in models))
    for name, s in summary["scores"].items():
        print("%-34s" % name + "".join("%11.1f" % s[m] for m in models))
    for name, d in summary["disagreements"].items():
        print("disagreements with replacement, %s: %d" % (name, len(d)))
        for x in d:
            print("   ", x["id"], x["model"], x["problem_id"], "rep", x["replacement"], name, x[name], ascii(x["answer_line"]))
    print("truncated:", json.dumps(summary["truncated"]))
    print("no_answer:", json.dumps(summary["no_answer"]["replacement"]), "| reasoning markers:",
          summary["reasoning_markers"])
    print("label counts:", json.dumps(summary["label_counts"]))


if __name__ == "__main__":
    main()
