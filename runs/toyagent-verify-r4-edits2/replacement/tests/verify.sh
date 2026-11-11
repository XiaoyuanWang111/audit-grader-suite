#!/usr/bin/env bash
# Replacement verifier for count-server-errors, written from audit/CONTRACT.md (check V).
# Same interface as task/tests/verify.sh: WORKSPACE, TESTS_DIR, PYTHON; exit status 0 passes, anything else fails.
# Only $WORKSPACE/out/answer.txt is graded; a missing file fails with exit 1.
# Decision switches (D_SURROUNDING_TEXT, D_WHITESPACE, D_LEADING_ZEROS, D_PLUS_SIGN, D_NONASCII_DIGITS) pass
# through the environment to check_answer.py; unset means the proposed reading.
WORKSPACE="${WORKSPACE:-/workspace}"
TESTS_DIR="${TESTS_DIR:-/tests}"
PYTHON="${PYTHON:-python3}"

ANSWER="$WORKSPACE/out/answer.txt"
if [ ! -f "$ANSWER" ]; then
    echo "no answer file"
    exit 1
fi

# -I: isolated mode, so no PYTHON* variable, user site directory or current directory can inject code.
exec "$PYTHON" -I "$TESTS_DIR/check_answer.py" "$ANSWER" "$TESTS_DIR/expected.json"
