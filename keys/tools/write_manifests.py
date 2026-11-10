"""Write MANIFEST.sha256 in each of the five small case directories and report sizes. Private: part of the keys."""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.normpath(os.path.join(HERE, "..", "..", "cases"))
# cases/ifbench is left out: its MANIFEST.sha256 is the run's own, copied unchanged, and covers the rebuilt case.
SMALL_CASES = ("toyagent-verify", "toycode-exec", "toyjson-reward", "toymath-extract", "toyqa-judge")


def main():
    ok = True
    for case in SMALL_CASES:
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
