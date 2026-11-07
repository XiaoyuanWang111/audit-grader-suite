"""Check that every pinned input still matches its hash; run before and after each audit run.

Checks every line of case/MANIFEST.sha256 and that case/ holds no file the manifest omits, then prints the sha256 of
the audit's own graders and fixtures so each run's log names the versions it used. Appends one line per call to
audit/results/pin_checks.log. Exit status 1 if any pinned file changed.

Usage: python -I audit/scripts/check_pins.py LABEL
"""

import datetime
import hashlib
import pathlib
import sys

AUDIT = pathlib.Path(__file__).resolve().parents[1]
CASE = AUDIT.parent / "case"
OWN = ["CONTRACT.md", "scripts/replacement_verifier.py", "scripts/grader_runner.py", "scripts/count_from_logs.py",
       "tests/fixtures.py"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(label):
    bad = []
    listed = set()
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        listed.add(name)
        p = CASE / name
        if not p.is_file() or sha(p) != digest:
            bad.append(name)
    extra = sorted(p.relative_to(CASE).as_posix() for p in CASE.rglob("*")
                   if p.is_file() and p.name != "MANIFEST.sha256" and p.relative_to(CASE).as_posix() not in listed)
    own = {name: sha(AUDIT / name)[:16] for name in OWN if (AUDIT / name).exists()}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "OK" if not bad and not extra else f"CHANGED {bad} EXTRA {extra}"
    line = f"{now} {label}: manifest {len(listed)} files {status}; own {own}"
    (AUDIT / "results").mkdir(exist_ok=True)
    with open(AUDIT / "results" / "pin_checks.log", "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
    print(line)
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
