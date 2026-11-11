#!/usr/bin/env bash
# Run the reference pipeline (run_eval.py) on 300 responses where only key 275 holds
# a CSV with one empty unquoted field. Usage (from W): bash audit/out/runeval_crash/run.sh
W="$(cd "$(dirname "$0")/../../.." && pwd)"
export NLTK_DATA="$W/case/deps/nltk_data"
cd "$W/audit/frozen/code/reference/IFBench" && "$W/.venv/Scripts/python.exe" -B run_eval.py \
  --input_data="$W/audit/out/runeval_crash/input.jsonl" \
  --input_response_data="$W/audit/out/runeval_crash/responses.jsonl" \
  --output_dir="$W/audit/out/runeval_crash/out" 2>&1 | tail -n 4
echo "exit=${PIPESTATUS[0]}"; ls "$W/audit/out/runeval_crash/out" 2>/dev/null | wc -l
