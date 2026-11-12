"""Check that every file a run loads matches its pin.

- case/ files against case/MANIFEST.sha256
- installed verifyit and verifiable_instructions packages against the case copies (byte-identical)
- the NLTK punkt_tab files (part of the manifest)
- audit/frozen files against the sha256 recorded in audit/frozen/SHA256SUMS
Exit code 1 on any mismatch.
"""
import hashlib
import os
import sys

W = "<W>"
SITE = f"{W}/.venv/Lib/site-packages"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    bad = []
    n = 0
    with open(f"{W}/case/MANIFEST.sha256", encoding="utf-8") as f:
        for line in f:
            digest, name = line.rstrip("\n").split("  ", 1)
            n += 1
            if sha(f"{W}/case/{name}") != digest:
                bad.append(("manifest", name))
    print(f"case manifest: {n} files checked")

    pairs = [(f"{W}/case/grader/verifyit", f"{SITE}/verifyit"),
             (f"{W}/case/reference/verifiable-instructions/verifiable_instructions", f"{SITE}/verifiable_instructions")]
    for src, inst in pairs:
        m = 0
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                a = os.path.join(root, fn)
                rel = os.path.relpath(a, src)
                b = os.path.join(inst, rel)
                m += 1
                if not os.path.exists(b) or sha(a) != sha(b):
                    bad.append(("installed", rel))
        # installed files that the case does not have (other than bytecode)
        for root, dirs, files in os.walk(inst):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                b = os.path.join(root, fn)
                rel = os.path.relpath(b, inst)
                if not os.path.exists(os.path.join(src, rel)):
                    bad.append(("installed-extra", rel))
        print(f"installed {os.path.basename(inst)}: {m} files compared with the case copy")

    sums = f"{W}/audit/frozen/SHA256SUMS"
    if os.path.exists(sums):
        k = 0
        for line in open(sums, encoding="utf-8"):
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            name = name.strip().lstrip("*")
            k += 1
            if sha(f"{W}/audit/frozen/{name}") != digest:
                bad.append(("frozen", name))
        print(f"audit/frozen: {k} files checked")
    pyc = [os.path.join(r, d) for r, ds, _ in os.walk(f"{W}/case") for d in ds if d == "__pycache__"]
    if pyc:
        bad.append(("pycache-in-case", pyc))
    if bad:
        print("MISMATCH", bad)
        sys.exit(1)
    print("all pins match")


if __name__ == "__main__":
    main()
