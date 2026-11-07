#!/usr/bin/env bash
# G2 reproduction: verify.sh runs "$PYTHON" (harness value python3) through PATH
# in the container the agent used. A python3 earlier on PATH decides the verdict.
# Sandbox state: /workspace/out/answer.txt = "37\n" (a wrong count) and an
# executable python3 that exits 0 in a directory ahead of the real one on PATH
# (in the image that would be, for example, /usr/local/bin/python3).
# Run from the audit run's root directory:  bash audit/scripts/repro_g2_path_shadow.sh
set -u
mkdir -p audit/tmp
d="$(mktemp -d -p audit/tmp)"
mkdir -p "$d/bin" "$d/ws/out"
printf '37\n' > "$d/ws/out/answer.txt"
printf '#!/bin/sh\nexit 0\n' > "$d/bin/python3"
chmod +x "$d/bin/python3"
echo "real interpreter, PYTHON=python (control):"
WORKSPACE="$d/ws" TESTS_DIR=case/task/tests PYTHON=python bash case/task/tests/verify.sh
echo "exit $?"
echo "python3 shadowed on PATH, PYTHON=python3 (harness value):"
PATH="$d/bin:$PATH" WORKSPACE="$d/ws" TESTS_DIR=case/task/tests PYTHON=python3 bash case/task/tests/verify.sh
echo "exit $?"
rm -rf "$d"
