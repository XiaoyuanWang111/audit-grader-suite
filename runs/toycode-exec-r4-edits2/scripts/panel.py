"""Step 5 on the stored panel: grade case/responses.jsonl with every grader and every decision switch.

Usage: python -B audit/scripts/panel.py
Writes audit/panel/<config>.jsonl (verdicts) and audit/panel/summary.json; prints the summary.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
OUT = os.path.join(AUDIT, "panel")
RESP = os.path.join(CASE, "responses.jsonl")
REP = os.path.join(AUDIT, "replacement", "grade_contract.py")

CONFIGS = {
    "grader": [sys.executable, "-B", os.path.join(CASE, "grade.py"), "--responses", RESP],
    "grader_rerun": [sys.executable, "-B", os.path.join(CASE, "grade.py"), "--responses", RESP],
    "reference": [sys.executable, "-B", os.path.join(CASE, "reference", "harness_ref.py"),
                  os.path.join(CASE, "tasks.jsonl"), os.path.join(CASE, "tests.json"), RESP],
    "replacement": [sys.executable, "-B", REP, "--responses", RESP],
    "replacement_rerun": [sys.executable, "-B", REP, "--responses", RESP],
    "replacement_alt_palindrome_normalized": [sys.executable, "-B", REP, "--responses", RESP,
                                              "--palindrome", "normalized"],
    "replacement_alt_crlf_no": [sys.executable, "-B", REP, "--responses", RESP, "--crlf", "no"],
    "replacement_alt_eq_literal": [sys.executable, "-B", REP, "--responses", RESP, "--eq", "literal"],
    "replacement_alt_dynamic_import_any": [sys.executable, "-B", REP, "--responses", RESP,
                                           "--dynamic-import", "any"],
    "replacement_alt_time_origin_load": [sys.executable, "-B", REP, "--responses", RESP, "--time-origin", "load"],
    "replacement_alt_main_guard_run": [sys.executable, "-B", REP, "--responses", RESP, "--main-guard", "run"],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open(RESP, encoding="utf-8") if l.strip()]
    expected_items = {(r["model"], t) for r in rows for t in [f"t{i:02d}" for i in range(1, 11)]}
    verdicts, seconds = {}, {}
    for name, cmd in CONFIGS.items():
        out = os.path.join(OUT, name + ".jsonl")
        if name == "reference":
            cmd = cmd + [out]
        else:
            cmd = cmd + ["--out", out]
        t0 = time.monotonic()
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), stdin=subprocess.DEVNULL)
        seconds[name] = round(time.monotonic() - t0, 1)
        if proc.returncode != 0:
            raise SystemExit(f"{name} failed: {proc.stderr[-2000:]}")
        verdicts[name] = {json.loads(l)["id"]: json.loads(l) for l in open(out, encoding="utf-8") if l.strip()}

    meta = {r["id"]: r for r in rows}
    models = sorted({r["model"] for r in rows})
    summary = {"seconds": seconds, "n_responses": len(rows),
               "finish_reason": dict(Counter(r.get("finish_reason") for r in rows)),
               "settings": sorted({(r.get("temperature"), r.get("max_tokens")) for r in rows}),
               "fence_tags": dict(Counter(
                   (r["response"].split("```", 1)[1].split("\n", 1)[0] if "```" in r["response"] else "<none>")
                   for r in rows)),
               "responses_with_think_marker": sum("</think>" in r["response"] for r in rows),
               "responses_with_cr": sum("\r" in r["response"] for r in rows)}
    scores, coverage, per_task = {}, {}, {}
    for name, v in verdicts.items():
        by_model = defaultdict(int)
        for vid, row in v.items():
            if row["verdict"] == "pass" and row.get("counted", True):
                by_model[row["model"]] += 1
        scores[name] = {m: 10.0 * by_model[m] for m in models}
        coverage[name] = f"{len({(row['model'], row['task_id']) for row in v.values()})}/{len(expected_items)}"
        pt = defaultdict(int)
        for row in v.values():
            pt[row["task_id"]] += row["verdict"] == "pass"
        per_task[name] = dict(sorted(pt.items()))
    summary["scores_percent"] = scores
    summary["scored_coverage"] = coverage
    summary["passes_per_task_of_4"] = per_task

    def diff(a, b):
        return sorted(i for i in verdicts[a] if verdicts[a][i]["verdict"] != verdicts[b][i]["verdict"])

    pairs = [("grader", "grader_rerun"), ("replacement", "replacement_rerun"), ("grader", "reference"),
             ("grader", "replacement"), ("reference", "replacement"),
             ("grader", "replacement_alt_palindrome_normalized"),
             ("reference", "replacement_alt_palindrome_normalized")]
    pairs += [("replacement", n) for n in CONFIGS if n.startswith("replacement_alt")]
    summary["disagreements"] = {}
    for a, b in pairs:
        d = diff(a, b)
        summary["disagreements"][f"{a} vs {b}"] = [
            f"{i} {meta[i]['model']} {meta[i]['task_id']} {a}={verdicts[a][i]['verdict']} "
            f"{b}={verdicts[b][i]['verdict']} ({verdicts[a][i].get('detail', '')})" for i in d]
    summary["grader_details"] = {i: v["detail"] for i, v in verdicts["grader"].items()}
    summary["replacement_details"] = {i: v["detail"] for i, v in verdicts["replacement"].items()}
    summary["verdict_file_sha256"] = {
        n: hashlib.sha256(open(os.path.join(OUT, n + ".jsonl"), "rb").read()).hexdigest() for n in CONFIGS}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, default=list)
    print(json.dumps({k: summary[k] for k in summary if k not in ("grader_details", "replacement_details")},
                     indent=1, default=list))


if __name__ == "__main__":
    main()
