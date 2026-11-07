"""Step 4 stress probes of score_trials.py outside the contract's labels: what happens to scored coverage when a trial
folder has no result.json, and whether one malformed record stops the whole scoring run.

Usage: python -I audit/scripts/probe_scoring_robustness.py    Writes audit/results/probe_scoring_robustness.json.
"""

import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grader_runner as GR  # noqa: E402


def rec(i, code, config="agentx+probe"):
    return {"trial_id": f"p{i:02d}", "task": "count-server-errors", "config": config, "agent_status": "completed",
            "agent_error": None, "agent_steps": 3, "verifier_exit_code": code, "verifier_output": ""}


def main():
    out = {}
    root = GR.new_tmpdir("probe_")
    try:
        trials = GR.write_trials([rec(1, 0), rec(2, 1)], root / "a")
        (trials / "p03").mkdir()  # a trial folder whose record was never written
        code, rows, raw = GR.run_score_trials(trials)
        out["folder_without_result_json"] = {"trial_folders": 3, "exit": code, "rows": rows}

        trials = GR.write_trials([rec(1, 0), rec(2, 1)], root / "b")
        (trials / "p03").mkdir()
        (trials / "p03" / "result.json").write_text('{"trial_id": "p03", "config": ', encoding="utf-8")
        code, rows, raw = GR.run_score_trials(trials)
        out["one_truncated_result_json"] = {"exit": code, "rows": rows, "last_line": raw.strip().splitlines()[-1]}

        trials = GR.write_trials([rec(1, 0), dict(rec(2, 1), config=None)], root / "c")
        code, rows, raw = GR.run_score_trials(trials)
        out["one_record_with_null_config"] = {"exit": code, "rows": rows, "last_line": raw.strip().splitlines()[-1]}
    finally:
        shutil.rmtree(root, ignore_errors=True)
    (GR.AUDIT / "results" / "probe_scoring_robustness.json").write_text(json.dumps(out, indent=1) + "\n",
                                                                        encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
