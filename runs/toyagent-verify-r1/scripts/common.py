"""Shared helpers for the count-server-errors audit (offline).

Paths, pin checks against case/MANIFEST.sha256, and runners for the grader
under audit (verify.sh through bash, score_trials.py through python).
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
TESTS_DIR = os.path.join(CASE, "task", "tests")
LOGS_DIR = os.path.join(CASE, "task", "environment", "logs")
TRIALS_DIR = os.path.join(CASE, "trials")
REPLACEMENT_DIR = os.path.join(AUDIT, "replacement")

# Git Bash, by absolute path: a bare "bash" from a Windows process can resolve
# to WSL's bash.exe in System32.
BASH = r"C:\Program Files\Git\usr\bin\bash.exe"
PYTHON = sys.executable

# Temporary sandboxes stay inside the audit run's directory.
TMP_ROOT = os.path.join(AUDIT, "tmp")
os.makedirs(TMP_ROOT, exist_ok=True)
tempfile.tempdir = TMP_ROOT

MANIFEST_SHA256 = "16e509fd04426690b42ef5a8fe037e04100299363b360fafcac77b330d0aaee3"
CONTRACT_V1_SHA256 = "eaa1e8e70a8d25f94dcfccbdfe2758a91c8e3647ffc97e84193121789f1cfe3f"


def fwd(path):
    """Windows path with forward slashes, which Git Bash and Python both accept."""
    return os.path.abspath(path).replace("\\", "/")


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def check_pins():
    """Return a list of problems; empty when every pinned case file matches."""
    problems = []
    manifest = os.path.join(CASE, "MANIFEST.sha256")
    if sha256_file(manifest) != MANIFEST_SHA256:
        problems.append("MANIFEST.sha256 changed")
    listed = set()
    with open(manifest, encoding="ascii") as f:
        for line in f:
            digest, rel = line.rstrip("\n").split("  ", 1)
            listed.add(rel)
            path = os.path.join(CASE, *rel.split("/"))
            if not os.path.isfile(path):
                problems.append(f"missing {rel}")
            elif sha256_file(path) != digest:
                problems.append(f"hash mismatch {rel}")
    for root, _dirs, files in os.walk(CASE):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), CASE).replace(os.sep, "/")
            if rel != "MANIFEST.sha256" and rel not in listed:
                problems.append(f"unlisted file {rel}")
    return problems


def require_pins(stage):
    problems = check_pins()
    if problems:
        raise SystemExit(f"pin check failed {stage}: {problems}")


def run_verify(workspace, tests_dir=TESTS_DIR, timeout=60):
    """Run verify.sh as the harness does: bash, WORKSPACE, TESTS_DIR, PYTHON.

    Returns (exit_status, stripped_stdout, stderr).
    """
    env = {k: v for k, v in os.environ.items() if k not in ("BASH_ENV", "ENV")}
    env.update(WORKSPACE=fwd(workspace), TESTS_DIR=fwd(tests_dir), PYTHON=fwd(PYTHON))
    with tempfile.TemporaryDirectory(prefix="vcwd_") as cwd:
        p = subprocess.run(
            [BASH, fwd(os.path.join(tests_dir, "verify.sh"))],
            env=env, cwd=cwd, capture_output=True, timeout=timeout,
        )
    return p.returncode, p.stdout.decode("utf-8", "replace").strip(), p.stderr.decode("utf-8", "replace")


def run_scoring(trials_dir, script=os.path.join(CASE, "score_trials.py")):
    """Run score_trials.py on a trials directory and parse its table.

    Returns (rows, stdout, stderr, exit) with rows = {config: (trials, passed, score)}.
    """
    with tempfile.TemporaryDirectory(prefix="scwd_") as cwd:
        p = subprocess.run([PYTHON, "-I", fwd(script), fwd(trials_dir)], cwd=cwd,
                           capture_output=True, timeout=60)
    out = p.stdout.decode("utf-8", "replace")
    rows = {}
    for line in out.splitlines()[1:]:
        m = re.fullmatch(r"(\S+)\s+(\d+)\s+(\d+)\s+(-?[\d.]+|nan)", line.strip())
        if m:
            rows[m.group(1)] = (int(m.group(2)), int(m.group(3)), float(m.group(4)))
    return rows, out, p.stderr.decode("utf-8", "replace"), p.returncode


def materialize(root, files):
    """Write a sandbox state. files maps a path under /workspace to bytes,
    or to None for an empty directory."""
    for rel, content in files.items():
        path = os.path.join(root, *rel.split("/"))
        if content is None:
            os.makedirs(path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(content)


def load_check_answer_main():
    """Load check_answer.main from its source without writing bytecode into case/."""
    src_path = os.path.join(TESTS_DIR, "check_answer.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    ns = {"__name__": "check_answer_audit", "__file__": src_path}
    exec(compile(src, src_path, "exec"), ns)
    return ns["main"]


def trial_ids():
    return sorted(d for d in os.listdir(TRIALS_DIR) if os.path.isdir(os.path.join(TRIALS_DIR, d)))


def load_result(tid):
    with open(os.path.join(TRIALS_DIR, tid, "result.json"), encoding="utf-8") as f:
        return json.load(f)
