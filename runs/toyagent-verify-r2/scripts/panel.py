"""Step 5: grade the 36 stored trials (the panel) with every grader and measure each configuration's score change.

Graders:
- stored: verifier_exit_code from each result.json, scored by score_trials.py on case/trials (unchanged).
- rerun: verify.sh rerun on each stored workspace as the evaluation runs it (grader_runner.run_verify_sh).
- replacement: the contract (audit/scripts/replacement_verifier.py) under the proposed readings, under each single
  alternative reading, and under all alternatives at once. Its verdicts are written as result.json exit codes and
  scored with score_trials.py itself, so the scoring path is the evaluation's.
Each grader reads the state its own extraction picks: verify.sh may fall back to /workspace/answer.txt, the
replacement reads only /workspace/out/answer.txt.

Usage: python -I audit/scripts/panel.py      Writes audit/results/panel.json and audit/results/panel.md.
"""

import collections
import concurrent.futures
import json
import math
import os
import pathlib
import random
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grader_runner as GR  # noqa: E402
import replacement_verifier as RV  # noqa: E402

SEED = 20261107
TRIALS = GR.CASE / "trials"


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def paired_bootstrap(a, b, reps=10000, seed=SEED):
    """95% percentile interval of mean(b) - mean(a) in points, resampling trials (pairs) with replacement."""
    rng = random.Random(seed)
    n = len(a)
    diffs = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(100.0 * sum(b[i] - a[i] for i in idx) / n)
    diffs.sort()
    return round(diffs[int(0.025 * reps)], 1), round(diffs[int(0.975 * reps) - 1], 1)


def score_with_script(records, exit_of, label):
    root = GR.new_tmpdir(f"panel_{label}_")
    try:
        recs = [dict(r, verifier_exit_code=exit_of[r["trial_id"]]) for r in records]
        code, rows, raw = GR.run_score_trials(GR.write_trials(recs, root))
        assert code == 0, raw
        return rows
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    records = [json.loads((d / "result.json").read_text(encoding="utf-8")) for d in sorted(TRIALS.iterdir())]
    tid = [r["trial_id"] for r in records]

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("AUDIT_WORKERS", "6"))) as ex:
        reruns = dict(zip(tid, ex.map(lambda t: GR.run_verify_sh(TRIALS / t / "workspace"), tid)))

    readings = {"proposed": []}
    readings.update({f"alt {e}": [e] for e in RV.DECISIONS})
    readings["all alternatives"] = list(RV.DECISIONS)
    repl = {name: {t: RV.grade_workspace(str(TRIALS / t / "workspace"), sw=RV.switches_for(alts))
                   for t in tid} for name, alts in readings.items()}

    trials = []
    for r in records:
        t = r["trial_id"]
        ws = TRIALS / t / "workspace"
        files = sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*") if p.is_file()) if ws.exists() else []
        trials.append({
            "trial_id": t, "config": r["config"], "agent_status": r["agent_status"], "files": files,
            "stored_exit": r["verifier_exit_code"], "stored_output": r["verifier_output"],
            "rerun_exit": reruns[t][0], "rerun_output": reruns[t][1],
            "rerun_matches_stored": reruns[t][0] == r["verifier_exit_code"] and reruns[t][1] == r["verifier_output"],
            "grader": "pass" if r["verifier_exit_code"] == 0 else "fail",
            "replacement": repl["proposed"][t][0], "replacement_reason": repl["proposed"][t][1],
            "replacement_by_reading": {k: v[t][0] for k, v in repl.items()},
        })

    configs = sorted({r["config"] for r in records})
    stored_rows = GR.run_score_trials(TRIALS)[1]
    rerun_rows = score_with_script(records, {t: reruns[t][0] for t in tid}, "rerun")
    repl_rows = {name: score_with_script(records, {t: 0 if v[t][0] == "pass" else 1 for t in tid}, f"r{i}")
                 for i, (name, v) in enumerate(repl.items())}

    per_config = {}
    for c in configs:
        ts = [x for x in trials if x["config"] == c]
        g = [1 if x["grader"] == "pass" else 0 for x in ts]
        p = [1 if x["replacement"] == "pass" else 0 for x in ts]
        per_config[c] = {
            "trials": len(ts), "stored": stored_rows[c], "rerun": rerun_rows[c],
            "replacement": {name: rows[c] for name, rows in repl_rows.items()},
            "stored_wilson95": wilson(sum(g), len(g)), "replacement_wilson95": wilson(sum(p), len(p)),
            "change_points": round(100.0 * (sum(p) - sum(g)) / len(g), 1),
            "change_bootstrap95": paired_bootstrap(g, p),
            "grader_pass_replacement_fail": [x["trial_id"] for x in ts if x["grader"] == "pass" and
                                             x["replacement"] == "fail"],
            "grader_fail_replacement_pass": [x["trial_id"] for x in ts if x["grader"] == "fail" and
                                             x["replacement"] == "pass"],
        }

    status = collections.Counter(x["agent_status"] for x in trials)
    answer_at = collections.Counter(
        "out/answer.txt" if "out/answer.txt" in x["files"] else
        ("answer.txt only (wrong path)" if "answer.txt" in x["files"] else "no answer file") for x in trials)
    contents = collections.Counter()
    for x in trials:
        for name in ("out/answer.txt", "answer.txt"):
            if name in x["files"]:
                contents[(name, (TRIALS / x["trial_id"] / "workspace" / name).read_bytes().decode("utf-8"))] += 1
    summary = {
        "trials": len(trials),
        "rerun_matches_stored": sum(x["rerun_matches_stored"] for x in trials),
        "stored_null_exit": sum(x["stored_exit"] is None for x in trials),
        "agent_status": dict(status),
        "answer_location": dict(answer_at),
        "answer_contents": {f"{k[0]}={k[1]!r}": v for k, v in sorted(contents.items(), key=lambda kv: -kv[1])},
        "grader_passes": sum(x["grader"] == "pass" for x in trials),
        "replacement_passes": sum(x["replacement"] == "pass" for x in trials),
        "disagreements": [x["trial_id"] for x in trials if x["grader"] != x["replacement"]],
        "scored_coverage": {"stored": f"{sum(r['trials'] for r in stored_rows.values())}/{len(trials)}",
                            "rerun": f"{sum(r['trials'] for r in rerun_rows.values())}/{len(trials)}",
                            "replacement": f"{sum(r['trials'] for r in repl_rows['proposed'].values())}/{len(trials)}"},
        "readings_that_change_any_verdict": sorted(
            name for name in repl if any(repl[name][t][0] != repl["proposed"][t][0] for t in tid)),
    }
    result = {"summary": summary, "per_config": per_config, "trials": trials}
    out = GR.AUDIT / "results" / "panel.json"
    out.write_text(json.dumps(result, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")

    lines = ["| Configuration | Stored score (passes/9) | Replacement, proposed | Change, points [95% paired bootstrap] "
             "| Grader passes the contract fails | Replacement with D-surrounding-text B |", "|---|---|---|---|---|---|"]
    for c in configs:
        pc = per_config[c]
        alt = pc["replacement"]["alt D-surrounding-text"]
        lines.append(f"| `{c}` | {pc['stored']['score']} ({pc['stored']['passed']}/9) "
                     f"[{pc['stored_wilson95'][0]}, {pc['stored_wilson95'][1]}] | "
                     f"{pc['replacement']['proposed']['score']} ({pc['replacement']['proposed']['passed']}/9) "
                     f"[{pc['replacement_wilson95'][0]}, {pc['replacement_wilson95'][1]}] | "
                     f"{pc['change_points']:+.1f} [{pc['change_bootstrap95'][0]:+.1f}, {pc['change_bootstrap95'][1]:+.1f}]"
                     f" | {', '.join(pc['grader_pass_replacement_fail']) or 'none'} | {alt['score']} ({alt['passed']}/9) |")
    (GR.AUDIT / "results" / "panel.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1, ensure_ascii=True))
    print("\n".join(lines))
    for c in configs:
        print(c, {k: v["score"] for k, v in per_config[c]["replacement"].items()})


if __name__ == "__main__":
    main()
