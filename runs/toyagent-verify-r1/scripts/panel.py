"""Step 5: grade the 36 stored trials with every grader and measure score changes.

Graders: the stored verdicts (verifier_exit_code), a replay of verify.sh on each
stored workspace, the replacement verifier under the proposed readings and
under every combination of decision readings, score_trials.py, and the
replacement scoring.

    python -I audit/scripts/panel.py audit/panel/panel_results.json
"""

import itertools
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "replacement")]

import common  # noqa: E402
import replacement_scoring as rs  # noqa: E402
import replacement_verifier as rv  # noqa: E402

SEED = 20261107
BOOT = 10000


def workspace_files(tid):
    ws = os.path.join(common.TRIALS_DIR, tid, "workspace")
    out = {}
    for root, _d, files in os.walk(ws):
        for name in files:
            p = os.path.join(root, name)
            rel = os.path.relpath(p, ws).replace(os.sep, "/")
            with open(p, "rb") as f:
                out[rel] = f.read()
    return ws, out


def boot_ci(diffs, rng, reps=BOOT):
    """95% percentile interval of the mean of paired per-trial differences."""
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def main(argv):
    common.require_pins("before panel")
    n = rv.count_server_errors()
    assert n == 41
    switch_names = sorted(rv.CHOICES)
    combos = [dict(zip(switch_names, vals)) for vals in itertools.product(*(rv.CHOICES[k] for k in switch_names))]
    trials = []
    for tid in common.trial_ids():
        r = common.load_result(tid)
        ws, files = workspace_files(tid)
        code, out, err = common.run_verify(ws)
        rep, reason = rv.grade(ws, n)
        combo_verdicts = sorted({rv.grade(ws, n, c)[0] for c in combos})
        trials.append({
            "trial_id": tid, "config": r["config"], "agent_status": r["agent_status"],
            "agent_steps": r["agent_steps"],
            "stored_exit": r["verifier_exit_code"], "stored_output": r["verifier_output"],
            "replay_exit": code, "replay_output": out, "replay_traceback": "Traceback" in err,
            "grader": "pass" if r["verifier_exit_code"] == 0 else "fail",
            "replacement": rep, "replacement_reason": reason,
            "verdicts_over_all_readings": combo_verdicts,
            "files": {k: v.decode("utf-8", "backslashreplace") for k, v in files.items()},
            "has_out_answer": "out/answer.txt" in files,
            "has_root_answer": "answer.txt" in files,
        })
    fidelity = [t["trial_id"] for t in trials
                if t["replay_exit"] != t["stored_exit"] or t["replay_output"] != (t["stored_output"] or "").strip()]

    # Scoring: score_trials.py on the stored trials, and the replacement scoring.
    rows, sc_out, sc_err, sc_code = common.run_scoring(common.TRIALS_DIR)
    rep_scores = rs.scores(rs.load(common.TRIALS_DIR))

    rng = random.Random(SEED)
    configs = sorted({t["config"] for t in trials})
    per_config = {}
    for c in configs:
        ts = [t for t in trials if t["config"] == c]
        g = [1 if t["grader"] == "pass" else 0 for t in ts]
        p = [1 if t["replacement"] == "pass" else 0 for t in ts]
        d = [a - b for a, b in zip(g, p)]
        lo, hi = boot_ci(d, rng)
        per_config[c] = {
            "trials": len(ts), "grader_passes": sum(g), "replacement_passes": sum(p),
            "grader_score": sum(g) / len(ts), "replacement_score": sum(p) / len(ts),
            "change_grader_minus_replacement": sum(d) / len(ts), "change_ci95": [lo, hi],
            "score_trials_py": rows.get(c), "replacement_scoring": rep_scores.get(c),
            "disagreements": [t["trial_id"] for t in ts if t["grader"] != t["replacement"]],
        }
    combo_scores = []
    for cmb in combos:
        sc = {}
        for c in configs:
            ts = [t for t in trials if t["config"] == c]
            sc[c] = sum(1 for t in ts if rv.grade(os.path.join(common.TRIALS_DIR, t["trial_id"], "workspace"), n, cmb)[0] == "pass") / len(ts)
        combo_scores.append({"switches": cmb, "scores": sc})
    distinct_combo_scores = sorted({json.dumps(x["scores"], sort_keys=True) for x in combo_scores})

    gp = [t for t in trials if t["grader"] == "pass"]
    summary = {
        "n_trials": len(trials), "N": n,
        "scored_coverage_grader": sum(1 for t in trials if t["stored_exit"] is not None) / len(trials),
        "scored_coverage_replacement": 1.0,
        "fidelity_mismatches": fidelity,
        "grader_passes": len(gp), "replacement_passes": sum(1 for t in trials if t["replacement"] == "pass"),
        "false_passes": [t["trial_id"] for t in gp if t["replacement"] == "fail"],
        "false_fails": [t["trial_id"] for t in trials if t["grader"] == "fail" and t["replacement"] == "pass"],
        "trials_whose_verdict_depends_on_a_decision": [t["trial_id"] for t in trials if len(t["verdicts_over_all_readings"]) > 1],
        "distinct_score_vectors_over_all_reading_combinations": len(distinct_combo_scores),
        "score_trials_py_stdout": sc_out, "score_trials_py_exit": sc_code,
        "per_config": per_config,
        "agent_status_counts": {s: sum(1 for t in trials if t["agent_status"] == s) for s in ("completed", "error", "timeout")},
        "missing_out_answer": [t["trial_id"] for t in trials if not t["has_out_answer"]],
        "root_answer_only": [t["trial_id"] for t in trials if not t["has_out_answer"] and t["has_root_answer"]],
        "stored_null_exit": [t["trial_id"] for t in trials if t["stored_exit"] is None],
        "stored_no_answer_exit0": [t["trial_id"] for t in trials if t["stored_output"] == "no answer file" and t["stored_exit"] == 0],
        "seed": SEED, "bootstrap_reps": BOOT,
    }
    common.require_pins("after panel")
    with open(argv[0], "w", encoding="utf-8", newline="\n") as f:
        json.dump({"summary": summary, "trials": trials, "combo_scores": combo_scores}, f, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "per_config"}, indent=1))
    for c, v in per_config.items():
        print(c, json.dumps(v))


if __name__ == "__main__":
    main(sys.argv[1:])
