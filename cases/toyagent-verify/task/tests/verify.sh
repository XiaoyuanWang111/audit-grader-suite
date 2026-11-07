#!/usr/bin/env bash
# Verifier for the count-server-errors task. The harness runs it after the agent stops; exit status 0 passes.
WORKSPACE="${WORKSPACE:-/workspace}"
TESTS_DIR="${TESTS_DIR:-/tests}"
PYTHON="${PYTHON:-python3}"

ANSWER="$WORKSPACE/out/answer.txt"
if [ ! -f "$ANSWER" ] && [ -f "$WORKSPACE/answer.txt" ]; then
    ANSWER="$WORKSPACE/answer.txt"
fi

if [ ! -f "$ANSWER" ]; then
    echo "no answer file"
    exit
fi

"$PYTHON" "$TESTS_DIR/check_answer.py" "$ANSWER" "$TESTS_DIR/expected.json"
