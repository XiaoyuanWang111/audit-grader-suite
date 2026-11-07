#!/usr/bin/env bash
# Reproduce each finding's counterexample with the grader under audit.
# Run from the audit run's root directory (the folder that holds case/ and audit/):
#     bash audit/scripts/repro_findings.sh
# Uses PYTHON=python as case/TASK.md allows where python3 is not the interpreter's name.
set -u
PY="${PY:-python}"
T=case/task/tests
run() {  # run <label> <workspace>
    printf '%s: ' "$1"
    out="$(WORKSPACE="$2" TESTS_DIR="$T" PYTHON="$PY" bash "$T/verify.sh" 2>&1)"; code=$?
    printf 'exit %s, output %s\n' "$code" "$(printf '%s' "$out" | tail -n 1 | cut -c1-70)"
}
mkdir -p audit/tmp
d="$(mktemp -d -p audit/tmp)"

echo "== F1: no answer file passes (stored trial t14: only tmp/notes.txt)"
run "t14" case/trials/t14/workspace
mkdir -p "$d/f1"
run "empty workspace" "$d/f1"

echo "== F2: /workspace/answer.txt is graded when out/answer.txt is missing (stored trial t12)"
run "t12" case/trials/t12/workspace

echo "== F3: U+001C..U+001F count as whitespace"
mkdir -p "$d/f3/out"; printf '41\x1c' > "$d/f3/out/answer.txt"
od -An -c "$d/f3/out/answer.txt" | tr -s ' '
run "41 + U+001C" "$d/f3"

echo "== F4: more than 4,300 digits raise ValueError in check_answer.py"
mkdir -p "$d/f4a/out" "$d/f4b/out"
printf '%04301d\n' 1 > "$d/f4a/out/answer.txt"
printf '%04301d\n' 41 > "$d/f4b/out/answer.txt"
printf '4,301 chars ending in 1: '; WORKSPACE="$d/f4a" TESTS_DIR="$T" PYTHON="$PY" bash "$T/verify.sh" 2>&1 | tail -n 1 | cut -c1-90
printf '4,301 chars, 4,299 zeros then 41: '; WORKSPACE="$d/f4b" TESTS_DIR="$T" PYTHON="$PY" bash "$T/verify.sh" >/dev/null 2>&1; echo "exit $?"

echo "== F5: verifier_exit_code null scores as a pass"
mkdir -p "$d/f5/x1" "$d/f5/x2"
printf '%s' '{"trial_id": "x1", "task": "count-server-errors", "config": "c", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": null}' > "$d/f5/x1/result.json"
printf '%s' '{"trial_id": "x2", "task": "count-server-errors", "config": "c", "agent_status": "completed", "agent_error": null, "agent_steps": 5, "verifier_exit_code": 1, "verifier_output": "wrong count: 37"}' > "$d/f5/x2/result.json"
"$PY" case/score_trials.py "$d/f5"

rm -rf "$d"
