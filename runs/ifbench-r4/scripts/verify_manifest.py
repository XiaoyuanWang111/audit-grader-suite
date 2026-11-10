"""Check every file under case/ against case/MANIFEST.sha256, and list files not in it.

Usage: python audit/scripts/verify_manifest.py
Prints mismatches, missing files, unlisted files, and a final OK/FAIL line.
"""
import hashlib
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    listed = {}
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            digest, rel = line.split("  ", 1)
            listed[rel] = digest
    bad = 0
    for rel, digest in sorted(listed.items()):
        p = os.path.join(CASE, rel)
        if not os.path.exists(p):
            print("MISSING", rel)
            bad += 1
        elif sha(p) != digest:
            print("MISMATCH", rel)
            bad += 1
    seen = set()
    for root, dirs, files in os.walk(CASE):
        dirs[:] = [d for d in dirs if d != "__pycache__" or "reference" in root]
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), CASE).replace(os.sep, "/")
            seen.add(rel)
    unlisted = sorted(r for r in seen if r not in listed and r != "MANIFEST.sha256")
    for r in unlisted:
        print("UNLISTED", r)
    print(f"listed={len(listed)} bad={bad} unlisted={len(unlisted)}")
    print("OK" if bad == 0 else "FAIL")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
