"""Pin the ToyMath inputs: file hashes, one hash per data row, one hash per rendered prompt.

Usage (from the audit run root):
    python -I audit/scripts/pin_inputs.py            # writes audit/out/pins.json and prints a summary
    python -I audit/scripts/pin_inputs.py --check    # exit 1 if any case file differs from MANIFEST.sha256

The row hash is the sha256 of the row's canonical JSON: keys sorted, UTF-8, no ASCII escaping,
separators (",", ":"). The rendered-prompt hash is the sha256 of the UTF-8 prompt text that the model
sees: prompt_template.txt with "{problem}" replaced by the problem field (TASK.md, "What the model sees").
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(ROOT, "case")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def check_manifest():
    bad = []
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            digest, name = line.split(None, 1)
            actual = sha256_file(os.path.join(CASE, name))
            if actual != digest:
                bad.append((name, digest, actual))
    return bad


def main():
    bad = check_manifest()
    if "--check" in sys.argv:
        for name, want, got in bad:
            print("MISMATCH %s pinned %s actual %s" % (name, want, got))
        print("manifest check: %s" % ("FAIL" if bad else "OK (6 files)"))
        sys.exit(1 if bad else 0)

    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8", newline="") as f:
        template = f.read()
    problems = []
    with open(os.path.join(CASE, "problems.jsonl"), "rb") as f:
        for raw in f:
            if not raw.strip():
                continue
            row = json.loads(raw.decode("utf-8"))
            prompt = template.replace("{problem}", row["problem"])
            problems.append({
                "problem_id": row["problem_id"],
                "answer": row["answer"],
                "row_sha256": sha256_bytes(canonical(row)),
                "line_sha256": sha256_bytes(raw.rstrip(b"\r\n")),
                "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                "prompt_format_equal": prompt == template.format(problem=row["problem"]),
            })
    responses = []
    with open(os.path.join(CASE, "responses.jsonl"), "rb") as f:
        for raw in f:
            if not raw.strip():
                continue
            row = json.loads(raw.decode("utf-8"))
            responses.append({
                "id": row["id"],
                "model": row["model"],
                "problem_id": row["problem_id"],
                "finish_reason": row["finish_reason"],
                "row_sha256": sha256_bytes(canonical(row)),
            })
    files = {}
    for name in ("TASK.md", "grade.py", "problems.jsonl", "prompt_template.txt", "responses.jsonl",
                 "reference/grade_ref.py", "MANIFEST.sha256"):
        files[name] = sha256_file(os.path.join(CASE, name))
    out = {"manifest_mismatches": bad, "files": files, "problems": problems, "responses": responses,
           "python": sys.version.split()[0]}
    os.makedirs(os.path.join(ROOT, "audit", "out"), exist_ok=True)
    with open(os.path.join(ROOT, "audit", "out", "pins.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("manifest mismatches:", bad)
    for name, digest in files.items():
        print("%-24s %s" % (name, digest))
    print("problem_id answer row_sha256 prompt_sha256 format==replace")
    for p in problems:
        print(p["problem_id"], p["answer"], p["row_sha256"], p["prompt_sha256"], p["prompt_format_equal"])
    print("responses:", len(responses), "rows; row hashes in audit/out/pins.json")


if __name__ == "__main__":
    main()
