"""Write MANIFEST.sha256 in every case directory and report sizes. Private: part of the keys."""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.normpath(os.path.join(HERE, "..", "..", "cases"))


def main():
    ok = True
    for case in sorted(os.listdir(CASES)):
        root = os.path.join(CASES, case)
        entries = []
        total = 0
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                if rel == "MANIFEST.sha256":
                    continue
                with open(path, "rb") as f:
                    data = f.read()
                total += len(data)
                if b"\r\n" in data:
                    print(f"  CRLF in {case}/{rel}")
                    ok = False
                entries.append(f"{hashlib.sha256(data).hexdigest()}  {rel}")
        text = "\n".join(entries) + "\n"
        with open(os.path.join(root, "MANIFEST.sha256"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        total += len(text.encode("utf-8"))
        flag = "" if total < 60 * 1024 else "  OVER 60 KB"
        ok = ok and not flag
        print(f"{case:<18} {len(entries):>3} files {total:>7} bytes{flag}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
