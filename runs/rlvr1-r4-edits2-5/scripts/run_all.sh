#!/usr/bin/env bash
# Rebuild every audit artifact from case/ (Git Bash). Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
export NLTK_DATA="<W>/case/deps/nltk_data"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe
quiet() { grep -v "Unable to detect\|No features in text\|^ERROR:absl" || true; }
$PY scripts/survey_data.py | tail -2
$PY scripts/step4_properties.py
$PY scripts/step4_fuzz.py 300 20261112 2>&1 | quiet | tail -3
$PY scripts/filter_fuzz.py
$PY scripts/step4_content_free.py 2>&1 | quiet | tail -3
$PY scripts/build_fixtures.py work/property_fixtures.jsonl work/fuzz_fixtures.jsonl work/content_free_fixtures.jsonl 2>&1 | quiet
$PY -m pytest -q -p no:cacheprovider tests 2>&1 | tail -2
$PY scripts/panel_grade.py 2>&1 | quiet | tail -1
$PY scripts/panel_analyze.py > work/panel_analyze.out 2>&1
quiet < work/panel_analyze.out | tail -8
$PY scripts/panel_extra.py 2>&1 | quiet | tail -3
# The counterexamples of AUDIT.md: in-process, then as the literal Git Bash commands.
$PY scripts/report_cases.py verify 2>&1 | quiet | tail -1
$PY scripts/report_cases.py script
bash work/report_commands.sh | $PY scripts/check_commands.py
# The same commands, extracted from AUDIT.md's appendix as written.
$PY scripts/check_report_appendix.py > /dev/null
bash work/appendix_commands.sh | $PY scripts/check_commands.py
