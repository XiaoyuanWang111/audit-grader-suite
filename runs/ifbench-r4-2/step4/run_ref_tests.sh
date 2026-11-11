#!/usr/bin/env bash
# Run the reference's unit tests (unmodified copy) against TARGET = reference | grader | replacement.
# Usage (from W): bash audit/step4/run_ref_tests.sh replacement
set -u
W="$(cd "$(dirname "$0")/../.." && pwd)"
export NLTK_DATA="$W/case/deps/nltk_data"
export IFB_TARGET="$1"
export PYTHONPATH="$W/audit/step4/shim"
cd "$W/audit/step4" && "$W/.venv/Scripts/python.exe" -B -m pytest -q -p no:cacheprovider instructions_test.py -k "not classic" 2>&1 | tail -n 60
