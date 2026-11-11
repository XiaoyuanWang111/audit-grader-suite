"""Step 1: pin the inputs of the ToyOrders reward audit.

Usage (from the audit's working directory W):
    python -B audit/pin_inputs.py            # print the pins and check them against MANIFEST.sha256
    python -B audit/pin_inputs.py --write    # also write audit/pins.json

Exits with status 1 if any case file differs from MANIFEST.sha256.
"""

import hashlib
import json
import os
import platform
import sys
from collections import Counter

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(W, "case")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def row_hashes(path, key):
    """One sha256 per JSON line, over the line's bytes without its newline."""
    out = []
    with open(path, "rb") as f:
        for raw in f.read().split(b"\n"):
            if not raw.strip():
                continue
            out.append((json.loads(raw)[key], sha256_bytes(raw)))
    return out


def main():
    manifest = {}
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="ascii") as f:
        for line in f:
            if line.strip():
                digest, name = line.split()
                manifest[name] = digest
    files = {}
    ok = True
    for name in sorted(os.listdir(CASE)):
        path = os.path.join(CASE, name)
        if not os.path.isfile(path):
            continue
        digest = sha256_file(path)
        with open(path, "rb") as f:
            data = f.read()
        files[name] = {"sha256": digest, "bytes": len(data), "cr_bytes": data.count(b"\r"),
                       "manifest": manifest.get(name),
                       "matches_manifest": (manifest.get(name) == digest) if name in manifest else None}
        if name in manifest and manifest[name] != digest:
            ok = False
    missing = sorted(set(manifest) - set(files))
    if missing:
        ok = False

    responses = [json.loads(l) for l in open(os.path.join(CASE, "responses.jsonl"), encoding="utf-8") if l.strip()]
    gen = Counter((r.get("temperature"), r.get("max_tokens")) for r in responses)
    pins = {
        "case_files": files,
        "manifest_missing_files": missing,
        "all_match_manifest": ok,
        "orders_row_sha256": row_hashes(os.path.join(CASE, "orders.jsonl"), "order_id"),
        "responses_row_sha256": row_hashes(os.path.join(CASE, "responses.jsonl"), "id"),
        "responses_per_checkpoint": dict(sorted(Counter(r["checkpoint"] for r in responses).items())),
        "responses_fields": sorted({k for r in responses for k in r}),
        "generation_settings_in_records": {f"temperature={t}, max_tokens={m}": n for (t, m), n in gen.items()},
        "audit_interpreter": {"version": sys.version, "implementation": platform.python_implementation(),
                              "platform": platform.platform(),
                              "int_max_str_digits": getattr(sys, "get_int_max_str_digits", lambda: None)(),
                              "recursion_limit": sys.getrecursionlimit()},
    }
    print(json.dumps(pins, indent=1))
    if "--write" in sys.argv:
        with open(os.path.join(W, "audit", "pins.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(pins, f, indent=1)
            f.write("\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
