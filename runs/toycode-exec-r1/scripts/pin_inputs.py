"""Step 1: pin the inputs. Prints file hashes, per-row hashes and run-record settings.

Usage (from the audit run directory): python -I audit/scripts/pin_inputs.py
Reads only files under case/. Writes nothing.
"""
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "case"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    print("python", sys.version.split()[0], sys.implementation.name)
    # Manifest check
    bad = 0
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, name = line.split(None, 1)
        got = sha((CASE / name.strip()).read_bytes())
        ok = got == h
        bad += not ok
        print(f"manifest {'OK ' if ok else 'BAD'} {h[:16]} {name.strip()}")
    print("manifest_mismatches", bad)
    print("MANIFEST.sha256", sha((CASE / "MANIFEST.sha256").read_bytes()))

    # Per-row hashes: tasks (raw line bytes), tests (canonical JSON per task), responses (raw line bytes)
    for raw in (CASE / "tasks.jsonl").read_bytes().split(b"\n"):
        if raw:
            r = json.loads(raw)
            print("task_row", r["task_id"], r["entry_point"], sha(raw)[:16])
    tests = json.loads((CASE / "tests.json").read_text(encoding="utf-8"))
    for tid, lst in tests.items():
        canon = json.dumps(lst, sort_keys=True, separators=(",", ":")).encode()
        print("tests_row", tid, len(lst), sha(canon)[:16])
    settings = collections.Counter()
    nonascii = cr = 0
    for raw in (CASE / "responses.jsonl").read_bytes().split(b"\n"):
        if raw:
            r = json.loads(raw)
            settings[(r["finish_reason"], r["max_tokens"], r["temperature"])] += 1
            nonascii += any(ord(c) > 127 for c in r["response"])
            cr += "\r" in r["response"]
            print("response_row", r["id"], r["model"], r["task_id"], sha(raw)[:16])
    print("response_settings (finish_reason, max_tokens, temperature):", dict(settings))
    print("responses_with_nonascii_chars", nonascii, "responses_with_CR", cr)
    tmpl = (CASE / "prompt_template.txt").read_bytes()
    print("prompt_template", sha(tmpl)[:16], "placeholder_count", tmpl.count(b"{prompt}"))


if __name__ == "__main__":
    main()
