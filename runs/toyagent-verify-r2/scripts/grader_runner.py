"""Run the graders under audit the way the evaluation runs them, and build sandbox states for fixtures.

- run_verify_sh(): `bash verify.sh` with WORKSPACE, TESTS_DIR and PYTHON set, as TASK.md describes. Git Bash stands in
  for the image's bash; the interpreter is this host's Python 3.12 (`python`), with PYTHONUTF8=1 by default because
  Python 3.12 in a Debian image reads files as UTF-8.
- run_score_trials(): `python score_trials.py TRIALS_DIR`, parsed into rows.
- build_workspace(): writes a fixture's sandbox state (files, directories, symbolic links) under audit/tmp/.

Every temporary directory lives under audit/tmp/, inside the audit folder.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

AUDIT = pathlib.Path(__file__).resolve().parents[1]
ROOT = AUDIT.parent
CASE = ROOT / "case"
TESTS_DIR = CASE / "task" / "tests"
VERIFY_SH = TESTS_DIR / "verify.sh"
SCORE_TRIALS = CASE / "score_trials.py"
TMP = AUDIT / "tmp"
# An absolute path: on Windows a bare "bash" can resolve to System32\bash.exe (the WSL launcher) before PATH.
BASH = os.environ.get("AUDIT_BASH", r"C:\Program Files\Git\usr\bin\bash.exe" if os.name == "nt" else "/bin/bash")
PYTHON_NAME = os.environ.get("AUDIT_PYTHON_NAME", "python" if os.name == "nt" else "python3")


def _rel(path):
    """A path relative to case/, the working directory of every verifier run (avoids MSYS path rewriting)."""
    return os.path.relpath(os.path.abspath(path), CASE).replace(os.sep, "/")


def run_verify_sh(workspace, utf8=True, python=None, path_prepend=None, timeout=300):
    """Run the verifier under audit on a workspace directory. Returns (exit_status, output)."""
    env = dict(os.environ)
    env["WORKSPACE"] = _rel(workspace)
    env["TESTS_DIR"] = _rel(TESTS_DIR)
    env["PYTHON"] = python or PYTHON_NAME
    if utf8:
        env["PYTHONUTF8"] = "1"
    else:
        env.pop("PYTHONUTF8", None)
    if path_prepend:
        # bash on Windows reads PATH from the Windows environment; prepend in the platform's own form.
        env["PATH"] = str(path_prepend) + os.pathsep + env.get("PATH", "")
    p = subprocess.run([BASH, _rel(VERIFY_SH)], cwd=CASE, env=env, capture_output=True, timeout=timeout)
    out = (p.stdout + p.stderr).decode("utf-8", "replace").strip()
    return p.returncode, out


def run_score_trials(trials_dir, timeout=300):
    """Run score_trials.py on a directory of trial folders. Returns (exit_status, rows, raw_output)."""
    p = subprocess.run([sys.executable, str(SCORE_TRIALS), str(trials_dir)], capture_output=True, timeout=timeout)
    out = p.stdout.decode("utf-8", "replace")
    rows = {}
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 4:
            rows[parts[0]] = {"trials": int(parts[1]), "passed": int(parts[2]), "score": float(parts[3])}
    return p.returncode, rows, out + p.stderr.decode("utf-8", "replace")


def new_tmpdir(prefix):
    TMP.mkdir(parents=True, exist_ok=True)
    return pathlib.Path(tempfile.mkdtemp(prefix=prefix, dir=TMP))


class SymlinkUnavailable(Exception):
    pass


def build_workspace(state, root):
    """Create a sandbox state. `state` is a list of entries:
    {"path": "out/answer.txt", "kind": "file", "hex": "34310a"} | {"path": "out", "kind": "dir"} |
    {"path": "out/answer.txt", "kind": "symlink", "target": "../tmp/real.txt"}.
    Returns the workspace directory (root/workspace). Raises SymlinkUnavailable if the host cannot make links."""
    ws = pathlib.Path(root) / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    for entry in state:
        p = ws / entry["path"]
        if entry["kind"] == "dir":
            p.mkdir(parents=True, exist_ok=True)
        elif entry["kind"] == "file":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(bytes.fromhex(entry["hex"]))
        elif entry["kind"] == "symlink":
            p.parent.mkdir(parents=True, exist_ok=True)
            target = entry["target"].replace("{TESTS_DIR}", str(TESTS_DIR))
            try:
                os.symlink(target, p)
            except OSError as e:
                raise SymlinkUnavailable(str(e))
        else:
            raise ValueError(entry)
    return ws


def symlinks_available():
    d = new_tmpdir("symprobe_")
    try:
        os.symlink("nowhere", d / "link")
        return True
    except OSError:
        return False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def write_trials(records, root):
    """Write result.json files (one per record) as trials/<trial_id>/result.json under root. Returns the dir."""
    trials = pathlib.Path(root) / "trials"
    for r in records:
        d = trials / r["trial_id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "result.json").write_text(json.dumps(r), encoding="utf-8")
    return trials
