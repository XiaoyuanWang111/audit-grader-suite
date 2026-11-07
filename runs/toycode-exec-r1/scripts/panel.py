"""Step 5: grade the stored responses (the panel) with every grader and compare.

Usage (from the audit run directory): python audit/scripts/panel.py
Writes audit/work/panel_<name>.jsonl for each grader run and audit/work/panel_summary.json; prints the tables.
Runs: the grader twice (the second run measures rerun differences), the reference, the replacement in fixes-only and
proposed modes, and the replacement with each decision entry flipped from its proposed reading.
"""

import collections
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
WORK = os.path.join(ROOT, "audit", "work")
sys.path.insert(0, HERE)
import contract_grader  # noqa: E402

MODELS = ["kite-7b", "lark-13b", "wren-34b", "finch-8b"]


def manifest_ok():
    bad = []
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            h, name = line.split(None, 1)
            with open(os.path.join(CASE, name.strip()), "rb") as g:
                if hashlib.sha256(g.read()).hexdigest() != h:
                    bad.append(name.strip())
    return bad


def run(name, cmd, cwd):
    out = os.path.join(WORK, f"panel_{name}.jsonl")
    if os.path.exists(out):
        os.remove(out)
    before = manifest_ok()
    t0 = time.time()
    proc = subprocess.run(cmd + [out] if name.startswith("reference") else cmd + ["--out", out], cwd=cwd,
                          capture_output=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    seconds = time.time() - t0
    after = manifest_ok()
    with open(out, encoding="utf-8") as f:
        rows = {r["id"]: r for r in map(json.loads, filter(str.strip, f))}
    print(f"[{name}] exit {proc.returncode}, {len(rows)} verdicts, {seconds:.1f} s, manifest mismatches before/after:"
          f" {before}/{after}")
    print("   " + proc.stdout.strip().replace("\n", "\n   "))
    return {"rows": rows, "seconds": seconds, "exit": proc.returncode, "stdout": proc.stdout}


def scores(rows):
    passed = collections.defaultdict(set)
    for r in rows.values():
        if r["verdict"] == "pass":
            passed[r["model"]].add(r["task_id"])
    return {m: 10.0 * len(passed[m]) for m in MODELS}


def main():
    py = sys.executable
    grader = [py, "grade.py"]
    reference = [py, os.path.join("reference", "harness_ref.py"), "tasks.jsonl", "tests.json", "responses.jsonl"]
    repl = [py, os.path.join(HERE, "contract_grader.py")]
    runs = {}
    runs["grader"] = run("grader", grader, CASE)
    runs["grader_rerun"] = run("grader_rerun", grader, CASE)
    runs["reference"] = run("reference", reference, CASE)
    runs["fixes_only"] = run("fixes_only", repl + ["--mode", "fixes-only"], ROOT)
    runs["proposed"] = run("proposed", repl + ["--mode", "proposed"], ROOT)
    for key, reading in contract_grader.PROPOSED.items():
        other = "B" if reading == "A" else "A"
        runs[f"proposed_{key}_{other}"] = run(f"proposed_{key}_{other}",
                                              repl + ["--mode", "proposed", "--set", f"{key}={other}"], ROOT)

    with open(os.path.join(CASE, "responses.jsonl"), encoding="utf-8") as f:
        responses = [json.loads(l) for l in f if l.strip()]
    ids = [r["id"] for r in responses]
    expected_items = {(m, t) for m in MODELS for t in [f"t{i:02d}" for i in range(1, 11)]}

    summary = {"seconds": {k: round(v["seconds"], 1) for k, v in runs.items()},
               "coverage": {k: f"{len({(r['model'], r['task_id']) for r in v['rows'].values()} & expected_items)}/40"
                            for k, v in runs.items()},
               "scores": {k: scores(v["rows"]) for k, v in runs.items()},
               "timeouts": {k: sorted(i for i, r in v["rows"].items() if "timeout" in r.get("detail", ""))
                            for k, v in runs.items() if "grader" in k or k in ("fixes_only", "proposed")}}

    def diff(a, b):
        return sorted(i for i in ids if runs[a]["rows"][i]["verdict"] != runs[b]["rows"][i]["verdict"])

    summary["disagreements"] = {f"{a} vs {b}": diff(a, b) for a, b in [
        ("grader", "grader_rerun"), ("grader", "reference"), ("grader", "fixes_only"), ("grader", "proposed"),
        ("reference", "fixes_only"), ("fixes_only", "proposed")] + [("proposed", k) for k in runs if k.startswith("proposed_")]}
    per_task = {}
    for t in sorted({r["task_id"] for r in responses}):
        per_task[t] = {k: sum(runs[k]["rows"][r["id"]]["verdict"] == "pass" for r in responses if r["task_id"] == t)
                       for k in ("grader", "reference", "fixes_only", "proposed")}
    summary["passes_per_task"] = per_task
    summary["verdicts"] = {i: {k: runs[k]["rows"][i]["verdict"] for k in ("grader", "reference", "fixes_only", "proposed")}
                           | {"grader_detail": runs["grader"]["rows"][i]["detail"],
                              "fixes_only_detail": runs["fixes_only"]["rows"][i]["detail"],
                              "proposed_detail": runs["proposed"]["rows"][i]["detail"]} for i in ids}
    with open(os.path.join(WORK, "panel_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)

    print("\nScores (percent of 10 tasks):")
    print(f"{'run':<34}" + "".join(f"{m:>10}" for m in MODELS))
    for k, s in summary["scores"].items():
        print(f"{k:<34}" + "".join(f"{s[m]:>10.1f}" for m in MODELS))
    print("\nCoverage:", summary["coverage"])
    print("Timeouts:", summary["timeouts"])
    print("\nDisagreements:")
    for k, v in summary["disagreements"].items():
        print(f"  {k:<44} {len(v):>2}  {' '.join(v)}")
    print("\nPasses per task (of 4):", json.dumps(per_task))
    print("\nVerdicts where grader, reference, fixes-only and proposed are not all equal:")
    for i in ids:
        v = summary["verdicts"][i]
        if len({v[k] for k in ("grader", "reference", "fixes_only", "proposed")}) > 1:
            r = runs["grader"]["rows"][i]
            print(f"  {i} {r['model']:<9} {r['task_id']} grader={v['grader']:<5} ref={v['reference']:<5}"
                  f" fixes={v['fixes_only']:<5} proposed={v['proposed']:<5} | grader: {v['grader_detail']}"
                  f" | fixes: {v['fixes_only_detail']}")


if __name__ == "__main__":
    main()
