#!/usr/bin/env bash
# Runs every command that audit/AUDIT.md gives, in the report's order, and prints each output under a header.
W=<W>

echo "### score table, current"
cd "$W/case" && python -B score_trials.py
echo "### score table, replacement"
cd "$W" && python -B audit/scripts/panel.py > /dev/null && python -B audit/scripts/regrade_trials.py && python -B audit/replacement/score_trials.py audit/panel/regraded_trials

cd "$W"
echo "### F1 minimal"
WORKSPACE=audit/repro/F1_no_answer TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
echo "### F1 t14"
cd "$W/case" && WORKSPACE=trials/t14/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"
echo "### F1 t21, t29 (named in the report)"
for t in t21 t29; do WORKSPACE=trials/$t/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"; done
cd "$W"
echo "### F2 minimal"
WORKSPACE=audit/repro/F2_root_answer TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
echo "### F2 t12"
cd "$W/case" && WORKSPACE=trials/t12/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"
echo "### F2 t35 (named in the report)"
WORKSPACE=trials/t35/workspace TESTS_DIR=task/tests PYTHON=python bash task/tests/verify.sh; echo "exit $?"
cd "$W"
echo "### F3 current"
python -B case/score_trials.py audit/repro/F3_null_trials
echo "### F3 replacement"
python -B audit/replacement/score_trials.py audit/repro/F3_null_trials
echo "### F3 record"
cat audit/repro/F3_null_trials/t1/result.json
echo "### O1"
WORKSPACE=audit/repro/O1_unit_separator TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
echo "### O2"
WORKSPACE=audit/repro/O2_nbsp TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh; echo "exit $?"
echo "### O3"
WORKSPACE=audit/repro/O3_leading_zeros TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh 2>&1 | tail -1; echo "exit ${PIPESTATUS[0]}"
echo "### repro bytes"
python -B -c "
import os
for p in ['audit/repro/F2_root_answer/answer.txt','audit/repro/O1_unit_separator/out/answer.txt','audit/repro/O2_nbsp/out/answer.txt']:
    print(p, open(p,'rb').read())
d=open('audit/repro/O3_leading_zeros/out/answer.txt','rb').read(); print('O3', len(d), d[:3], d[-4:], set(d[:-3]))
print('F1 files', [os.path.join(r,f) for r,_,fs in os.walk('audit/repro/F1_no_answer') for f in fs], os.listdir('audit/repro/F1_no_answer'))
"
echo "### manifest"
cd "$W/case" && sha256sum -c --quiet MANIFEST.sha256 && echo "manifest OK"
find "$W/case" -name __pycache__
