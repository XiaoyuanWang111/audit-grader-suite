"""Shared helpers for the audit tests: paths, pinned hashes, sandbox materialization, verifier and scorer runs.

The verifier is run as the harness runs it: `bash verify.sh` with WORKSPACE, TESTS_DIR and PYTHON set. Offline
substitutes: Git Bash for the image's bash 5.2 and this machine's Python 3.12 (PYTHONUTF8=1, like the image's
UTF-8 locale) for the image's python3.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(TESTS)
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
ORIG_TESTS = os.path.join(CASE, "task", "tests")
REPL_TESTS = os.path.join(AUDIT, "replacement", "tests")
ORIG_SCORER = os.path.join(CASE, "score_trials.py")
REPL_SCORER = os.path.join(AUDIT, "replacement", "score_trials.py")
LOGS = os.path.join(CASE, "task", "environment", "logs")
TMP_ROOT = os.path.join(AUDIT, "tmp")

BASH = os.environ.get("AUDIT_BASH") or shutil.which("bash")
PYTHON = sys.executable

# sha256 of the files the grader loads, copied from case/MANIFEST.sha256 (pinned in audit/ISSUE.md, step 1).
PINNED = {
    "task/tests/verify.sh": "e741df570d2df0a6dc8e6cb103e67714fe8065caf4a015f1fbc53483c7991cae",
    "task/tests/check_answer.py": "add65682459117027d38997270d2f0e9ae972ee8fa24c76472800f2cd943a5e1",
    "task/tests/expected.json": "7eb936f0b49cce342f91c5d24d97f6cfc5b2a93e641e2cf508acedd5ed156926",
    "score_trials.py": "a8f72289bf4517f98070d765d8a26e0615ec6a626468a7d1ca7021fcfacdf6d7",
    "task/instruction.md": "95e87bff623fd7a0ca0cfc61cfa82fea88de20c9b34b254cce014873ba18f51d",
    "task/environment/logs/access.log": "8f3e0b36e66103dda03d7368f55792189977b94cce98031a544981ebd4525b04",
    "task/environment/logs/access.log.1": "b33a03646df72341678a79990c96aaa834b0b60feeaa3e269f2348459c6a03c1",
    "task/environment/logs/access.log.2.gz": "ec9beb05ec3f9292984f3287eeda6661ad922f5319888c0a5922e0b8fb7ae826",
}
MANIFEST_SHA256 = "16e509fd04426690b42ef5a8fe037e04100299363b360fafcac77b330d0aaee3"


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_manifest():
    """Return a list of (path, problem) for every case file that does not match MANIFEST.sha256."""
    problems = []
    manifest = os.path.join(CASE, "MANIFEST.sha256")
    if sha256_file(manifest) != MANIFEST_SHA256:
        problems.append(("MANIFEST.sha256", "hash changed"))
    with open(manifest, encoding="utf-8") as f:
        for line in f:
            digest, rel = line.rstrip("\n").split("  ", 1)
            p = os.path.join(CASE, rel)
            if not os.path.isfile(p):
                problems.append((rel, "missing"))
            elif sha256_file(p) != digest:
                problems.append((rel, "hash mismatch"))
    for rel, digest in PINNED.items():
        if sha256_file(os.path.join(CASE, rel)) != digest:
            problems.append((rel, "pinned hash mismatch"))
    return problems


def state_id(check, files):
    """Stable fixture id: the check name plus the first 16 hex digits of the sha256 of the canonical state."""
    canon = []
    for path in sorted(files):
        content = files[path]
        canon.append([path, None if content is None else content.hex()])
    digest = hashlib.sha256(json.dumps(canon, separators=(",", ":")).encode()).hexdigest()
    return f"{check}:{digest[:16]}"


def new_tmp(prefix):
    os.makedirs(TMP_ROOT, exist_ok=True)
    return tempfile.mkdtemp(prefix=prefix, dir=TMP_ROOT)


def materialize(files, base=None):
    """Write a sandbox state. Keys are paths under /workspace; a key ending in '/' with value None is a directory."""
    ws = base or new_tmp("ws_")
    for rel, content in files.items():
        p = os.path.join(ws, *rel.rstrip("/").split("/"))
        if rel.endswith("/"):
            os.makedirs(p, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(content)
    return ws


def posix(path):
    return os.path.abspath(path).replace(os.sep, "/")


def run_verifier(workspace, tests_dir=ORIG_TESTS, extra_env=None):
    """Run `bash verify.sh` as the harness does. Returns (exit_status, output)."""
    env = dict(os.environ)
    env.update({
        "WORKSPACE": posix(workspace),
        "TESTS_DIR": posix(tests_dir),
        "PYTHON": PYTHON,
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run([BASH, posix(os.path.join(tests_dir, "verify.sh"))], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()


def verdict_of(code):
    return "pass" if code == 0 else "fail"


def run_scorer(trials_dir, scorer=ORIG_SCORER):
    """Run a scorer on a trials directory. Returns ({config: (trials, passed, score)}, raw_output, returncode)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([PYTHON, "-B", scorer, posix(trials_dir)], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    out = proc.stdout.decode("utf-8", "replace")
    table = {}
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 4:
            table[" ".join(parts[:-3])] = (int(parts[-3]), int(parts[-2]), float(parts[-1]))
    return table, out + proc.stderr.decode("utf-8", "replace"), proc.returncode


def write_trials(records, base=None):
    """Write result.json records into a fresh trials directory. RECORDS maps trial name -> dict or raw bytes."""
    d = base or new_tmp("trials_")
    for name, rec in records.items():
        os.makedirs(os.path.join(d, name), exist_ok=True)
        with open(os.path.join(d, name, "result.json"), "wb") as f:
            f.write(rec if isinstance(rec, bytes) else json.dumps(rec).encode())
    return d


def load_original_checker():
    """Load case/task/tests/check_answer.py in process without writing bytecode. Returns its main()."""
    path = os.path.join(ORIG_TESTS, "check_answer.py")
    with open(path, encoding="utf-8") as f:
        code = compile(f.read(), path, "exec")
    ns = {"__name__": "check_answer_under_audit"}
    exec(code, ns)
    return ns["main"]


def load_replacement_checker():
    path = os.path.join(REPL_TESTS, "check_answer.py")
    with open(path, encoding="utf-8") as f:
        code = compile(f.read(), path, "exec")
    ns = {"__name__": "check_answer_replacement"}
    exec(code, ns)
    return ns


def count_server_errors():
    """Recompute the correct count from the logs per the contract (status = field after the quoted request)."""
    import gzip
    import re
    total = 0
    per_file = {}
    for name in ("access.log", "access.log.1", "access.log.2.gz"):
        p = os.path.join(LOGS, name)
        opener = gzip.open if name.endswith(".gz") else open
        with opener(p, "rb") as f:
            data = f.read()
        n = 0
        for line in data.split(b"\n"):
            if not line:
                continue
            m = re.match(rb'^\S+ \S+ \S+ \[[^\]]*\] "[^"]*" (\d{3}) \S+$', line)
            if m is None:
                raise ValueError(f"unparsed line in {name}: {line!r}")
            if 500 <= int(m.group(1)) <= 599:
                n += 1
        per_file[name] = n
        total += n
    return total, per_file
