#!/usr/bin/env bash
# Rerun every command that audit/AUDIT.md gives and keep each output under audit/work/verify/.
# Run from anywhere:  bash <W>/audit/scripts/verify_all.sh
set -u
W=<W>
cd "$W" || exit 1
export NLTK_DATA="$W/case/deps/nltk_data"
export PYTHONDONTWRITEBYTECODE=1
PY=.venv/Scripts/python.exe
OUT=audit/work/verify
mkdir -p "$OUT"
run() {
  name=$1; shift
  "$@" > "$OUT/$name.log" 2>&1
  echo "$name exit $?" >> "$OUT/summary.txt"
}
: > "$OUT/summary.txt"
date -u +"start %Y-%m-%d %H:%M:%S UTC" >> "$OUT/summary.txt"
run pin_inputs $PY -B audit/scripts/pin_inputs.py
run pytest $PY -m pytest -p no:cacheprovider -q -rN audit/tests
run check_reviews $PY -B audit/scripts/check_reviews.py
run analyze_review $PY -B audit/scripts/analyze_review.py
run analyze_review_post $PY -B audit/scripts/analyze_review_post.py
run finding_bounds $PY -B audit/scripts/finding_bounds.py
run metamorphic_shares $PY -B audit/scripts/metamorphic_shares.py
run metamorphic_post $PY -B audit/scripts/metamorphic_post.py
run repro_all $PY -B audit/scripts/repro.py --all
run repro_one $PY -B audit/scripts/repro.py F-subbullets-none
run verify_report $PY -B audit/scripts/verify_report.py
run regrade_disagreements $PY -B audit/scripts/regrade_disagreements.py
date -u +"end %Y-%m-%d %H:%M:%S UTC" >> "$OUT/summary.txt"
