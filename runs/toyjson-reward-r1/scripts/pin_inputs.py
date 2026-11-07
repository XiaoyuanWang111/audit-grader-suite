"""Step 1: print the pinned inputs of the ToyOrders reward audit.

Usage, from the audit run directory:
    python -I audit/scripts/pin_inputs.py            # print the pins as Markdown
    python -I audit/scripts/pin_inputs.py --check    # exit 1 if any case file differs from its pin

The pins are the sha256 of each case file (as listed in case/MANIFEST.sha256), one sha256
per orders.jsonl row (the row's bytes without the trailing newline), and one sha256 per
rendered prompt (prompt_template.txt with "{email}" replaced by the row's email).
"""
import hashlib
import json
import pathlib
import platform
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "case"

# The pins recorded in audit/ISSUE.md (step 1). They equal case/MANIFEST.sha256.
PINNED = {
    "MANIFEST.sha256": "f190138bf83efd5887ebb7ec749bd86e93eae8916b207bbb8fc158b4e96c2142",
    "TASK.md": "ee70972e4cbaedcd05be184ee761d7a6f4432edd212acd24ff5ef2d94593bf34",
    "orders.jsonl": "f6a5d0a2a4d72fa8658b6160679d757bddda7105449b18757029e9e1e92e20bf",
    "prompt_template.txt": "11d2c94c0b96d8461b6106e6ad793f9e8822ef0b4c7797fef044581bba2fc02e",
    "responses.jsonl": "d343e478c3a61d5e1b0c57919e2ed30672fcae620e97c9dcf82383e0f77e5753",
    "reward.py": "e8cbb5566d04077449430f4bd3ef184f9f509afc34762fc89b8e46e0988f2362",
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def check():
    bad = []
    for name, want in PINNED.items():
        got = sha256_bytes((CASE / name).read_bytes())
        if got != want:
            bad.append((name, want, got))
    # The manifest itself must agree with the pins.
    manifest = {}
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split()
            manifest[name] = digest
    for name, digest in manifest.items():
        if PINNED.get(name) != digest:
            bad.append((name + " (manifest entry)", PINNED.get(name), digest))
    for name, want, got in bad:
        print("MISMATCH %s: pinned %s, found %s" % (name, want, got))
    if not bad:
        print("pins OK: %d case files match" % len(PINNED))
    return not bad


def main():
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    print("Python used by this audit: %s (%s)" % (platform.python_version(), sys.executable))
    print()
    print("| File | sha256 |")
    print("|---|---|")
    for name in PINNED:
        print("| `case/%s` | `%s` |" % (name, sha256_bytes((CASE / name).read_bytes())))
    print()
    template = (CASE / "prompt_template.txt").read_text(encoding="utf-8")
    print("| order_id | row sha256 | rendered prompt sha256 |")
    print("|---|---|---|")
    raw = (CASE / "orders.jsonl").read_bytes()
    for line in raw.split(b"\n"):
        if not line:
            continue
        row = json.loads(line.decode("utf-8"))
        prompt = template.replace("{email}", row["email"])
        print("| %s | `%s` | `%s` |" % (row["order_id"], sha256_bytes(line), sha256_bytes(prompt.encode("utf-8"))))


if __name__ == "__main__":
    main()
