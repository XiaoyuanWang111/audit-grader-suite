"""Step 1: check every file in case/ against case/MANIFEST.sha256, and hash the
installed copies of verifyit and verifiable-instructions against case/ copies.

Usage: python audit/scripts/verify_manifest.py
Prints one line per mismatch and a summary line.
"""
import hashlib
import importlib.util
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    bad = 0
    n = 0
    listed = set()
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        listed.add(rel)
        n += 1
        p = CASE / rel
        if not p.exists():
            print("MISSING", rel)
            bad += 1
        elif sha(p) != digest:
            print("MISMATCH", rel)
            bad += 1
    # files present but not listed (MANIFEST itself is excluded by design)
    extra = []
    for p in CASE.rglob("*"):
        if p.is_file():
            rel = p.relative_to(CASE).as_posix()
            if rel != "MANIFEST.sha256" and rel not in listed:
                extra.append(rel)
    for rel in extra:
        print("UNLISTED", rel)
    print(f"manifest: {n} files listed, {bad} missing or mismatched, {len(extra)} unlisted")

    # installed packages vs case copies
    pairs = []
    spec = importlib.util.find_spec("verifyit")
    inst = pathlib.Path(spec.origin).parent
    for p in sorted((CASE / "grader" / "verifyit").rglob("*")):
        if p.is_file():
            rel = p.relative_to(CASE / "grader" / "verifyit")
            pairs.append(("verifyit", p, inst / rel))
    spec = importlib.util.find_spec("verifiable_instructions")
    inst2 = pathlib.Path(spec.origin).parent
    src2 = CASE / "reference" / "verifiable-instructions" / "verifiable_instructions"
    for p in sorted(src2.rglob("*")):
        if p.is_file():
            rel = p.relative_to(src2)
            pairs.append(("verifiable_instructions", p, inst2 / rel))
    diff = 0
    for pkg, a, b in pairs:
        if not b.exists() or sha(a) != sha(b):
            print("INSTALLED DIFFERS", pkg, a.relative_to(CASE).as_posix())
            diff += 1
    # files installed but absent from case copies (.py only)
    extra_inst = []
    for root, src in ((inst, CASE / "grader" / "verifyit"), (inst2, src2)):
        for p in root.rglob("*.py"):
            rel = p.relative_to(root)
            if not (src / rel).exists():
                extra_inst.append(str(p))
    for e in extra_inst:
        print("INSTALLED ONLY", e)
    print(f"installed copies: {len(pairs)} compared, {diff} differ, {len(extra_inst)} installed-only .py files")
    print(f"verifyit installed at {inst}")
    print(f"verifiable_instructions installed at {inst2}")
    return 1 if (bad or diff) else 0


if __name__ == "__main__":
    sys.exit(main())
