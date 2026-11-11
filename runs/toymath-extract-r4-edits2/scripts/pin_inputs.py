"""Pin the audit inputs: check every case file against MANIFEST.sha256 and
print one sha256 per data row.

Run from W:  python -B audit/scripts/pin_inputs.py
Exit status 1 if any file differs from the manifest.
"""
import hashlib
import json
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_hash(obj, keys):
    # Canonical JSON over the named fields, sorted keys, UTF-8, no spaces.
    sub = {k: obj[k] for k in keys}
    blob = json.dumps(sub, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def main():
    ok = True
    manifest = {}
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            manifest[name.strip()] = h
    print("file checks against case/MANIFEST.sha256:")
    for name, h in sorted(manifest.items()):
        got = sha(CASE / name)
        status = "OK" if got == h else "MISMATCH"
        ok &= got == h
        print(f"  {status}  {got}  case/{name}")
    listed = set(manifest) | {"MANIFEST.sha256"}
    for p in sorted(CASE.rglob("*")):
        if p.is_file():
            rel = p.relative_to(CASE).as_posix()
            if rel not in listed:
                ok = False
                print(f"  UNLISTED  case/{rel}")
    print(f"  manifest itself: {sha(CASE / 'MANIFEST.sha256')}")
    if "--rows" in sys.argv:
        print("problems.jsonl rows (sha256 over problem_id, problem, answer):")
        for line in (CASE / "problems.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            print(f"  {r['problem_id']}  {row_hash(r, ['problem_id', 'problem', 'answer'])}")
        print("responses.jsonl rows (sha256 over all seven fields):")
        for line in (CASE / "responses.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            print(f"  {r['id']}  {row_hash(r, sorted(r))}")
    print("ALL OK" if ok else "CHANGED INPUTS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
