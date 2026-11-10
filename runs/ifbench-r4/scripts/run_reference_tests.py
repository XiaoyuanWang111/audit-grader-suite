"""Run the reference's unit tests (instructions_test.py, IFBench OOD class only) against a target.

Usage: python audit/scripts/run_reference_tests.py R|G|X|XP
Writes audit/frozen/reftests_<target>.txt (pytest -rf summary) and prints the counts.
"""
import os
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = os.path.join(W, ".venv", "Scripts", "python.exe")


def main():
    target = sys.argv[1]
    env = dict(os.environ, IFB_TARGET=target, NLTK_DATA=os.path.join(W, "case", "deps", "nltk_data"))
    test = os.path.join(W, "audit", "work", "reference", "instructions_test.py")
    cmd = [PY, "-X", "utf8", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "reftest_plugin",
           "-rf", "--tb=line", test + "::InstructionsTest"]
    env["PYTHONPATH"] = os.pathsep.join([os.path.join(W, "audit", "scripts"), os.path.join(W, "audit", "work", "reference")])
    r = subprocess.run(cmd, cwd=os.path.join(W, "audit", "work", "reference"), env=env, capture_output=True,
                       text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    path = os.path.join(W, "audit", "frozen", f"reftests_{target}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(out.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
