"""Check that every pinned input of the ToyQA audit matches its recorded sha256.

Run from the audit run's root directory (the folder that holds case/ and audit/):

    python -I audit/scripts/check_pins.py

Checks, in order:
1. every file listed in case/MANIFEST.sha256, and the manifest itself;
2. the per-row hashes in audit/pins/rows.sha256 (questions and responses);
3. every file listed in audit/pins/audit_files.sha256, if that list exists
   (the contract, the frozen sample and the other audit artifacts whose hashes
   are recorded in audit/ISSUE.md).
Exits 1 on the first mismatch class, after printing every mismatch.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "case"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_list(list_path: Path, base: Path) -> list[str]:
    bad = []
    for line in list_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.lstrip("*").strip()
        target = base / name
        if not target.is_file():
            bad.append(f"missing: {target}")
        elif sha256_file(target) != digest:
            bad.append(f"hash mismatch: {target}")
    return bad


def check_rows(rows_path: Path) -> list[str]:
    bad = []
    expected = {}
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        digest, ref = line.split(None, 1)
        expected[ref] = digest
    seen = set()
    for fn in ("questions.jsonl", "responses.jsonl"):
        raw = (CASE / fn).read_bytes().split(b"\n")
        if raw and raw[-1] == b"":
            raw = raw[:-1]
        for i, row in enumerate(raw):
            d = json.loads(row.decode("utf-8"))
            key = d.get("question_id") if fn == "questions.jsonl" else d.get("id")
            ref = f"{fn}:{i + 1}:{key}"
            seen.add(ref)
            if expected.get(ref) != hashlib.sha256(row).hexdigest():
                bad.append(f"row hash mismatch: {ref}")
    for ref in set(expected) - seen:
        bad.append(f"row missing: {ref}")
    return bad


def main() -> int:
    problems = check_list(CASE / "MANIFEST.sha256", CASE)
    manifest_digest = sha256_file(CASE / "MANIFEST.sha256")
    pinned_manifest = (ROOT / "audit" / "pins" / "manifest.sha256").read_text(encoding="utf-8").split()[0]
    if manifest_digest != pinned_manifest:
        problems.append("MANIFEST.sha256 itself changed")
    problems += check_rows(ROOT / "audit" / "pins" / "rows.sha256")
    audit_list = ROOT / "audit" / "pins" / "audit_files.sha256"
    if audit_list.is_file():
        problems += check_list(audit_list, ROOT)
    for p in problems:
        print(p)
    n_audit = 0
    if audit_list.is_file():
        n_audit = sum(1 for l in audit_list.read_text(encoding="utf-8").splitlines() if l.strip())
    print(f"pins: {'FAIL' if problems else 'OK'} (9 case files, manifest, 60 rows, {n_audit} audit files)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
