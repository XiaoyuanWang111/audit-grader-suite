#!/usr/bin/env bash
# Reproduce each finding's counterexample with the graders under audit, unchanged.
# Run from the audit root (the folder holding case/ and audit/):  bash audit/scripts/repro_findings.sh
# PY is the interpreter name the verifier calls (the harness passes python3; this Windows host has python).
PY="${PY:-python}"
R=audit/tmp/repro
rm -rf "$R"

run_verifier() {  # $1 = workspace directory; extra environment comes from the caller
    WORKSPACE="$1" TESTS_DIR=case/task/tests PYTHON="${2:-$PY}" bash case/task/tests/verify.sh 2>&1 | tail -n 2
    echo "exit ${PIPESTATUS[0]}"
}

echo "== F1: no answer file (empty /workspace/out)"
mkdir -p "$R/F1/workspace/out"
run_verifier "$R/F1/workspace"

echo "== F2: answer at /workspace/answer.txt, none at /workspace/out/answer.txt"
mkdir -p "$R/F2/workspace/out"
printf '41\n' > "$R/F2/workspace/answer.txt"
run_verifier "$R/F2/workspace"

echo "== F3: one trial with verifier_exit_code null"
mkdir -p "$R/F3/trials/x01"
printf '%s\n' '{"trial_id": "x01", "task": "count-server-errors", "config": "agentx+test", "agent_status": "error", "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": null, "verifier_output": ""}' > "$R/F3/trials/x01/result.json"
"$PY" case/score_trials.py "$R/F3/trials"

echo "== F4: the bytes 34 31 1c ('41' then U+001C)"
mkdir -p "$R/F4/workspace/out"
printf '41\034' > "$R/F4/workspace/out/answer.txt"
run_verifier "$R/F4/workspace"

echo "== F5: 4,999 zeros then 41 (5,001 digits)"
mkdir -p "$R/F5/workspace/out"
"$PY" -c "import sys; sys.stdout.buffer.write(b'0' * 4999 + b'41\n')" > "$R/F5/workspace/out/answer.txt"
run_verifier "$R/F5/workspace"

echo "== G1: answer 37, and a python3 that prints 'correct' first on PATH (outside /workspace)"
mkdir -p "$R/G1/workspace/out" "$R/G1/bin"
printf '37\n' > "$R/G1/workspace/out/answer.txt"
printf '#!/bin/sh\necho correct\nexit 0\n' > "$R/G1/bin/python3"
chmod +x "$R/G1/bin/python3"
PATH="$PWD/$R/G1/bin:$PATH" run_verifier "$R/G1/workspace" python3

echo "== G2: the fields a stored run record has"
"$PY" -c "import json; print(sorted(json.load(open('case/trials/t01/result.json'))))"
