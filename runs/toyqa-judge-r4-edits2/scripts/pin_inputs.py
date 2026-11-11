"""Pin the audit inputs: verify case/MANIFEST.sha256 and write per-row hashes.

Usage (from W):  python -B audit/scripts/pin_inputs.py
Writes audit/pins.json and prints a summary. Reads only files under case/.
A row hash is the sha256 of the row's raw UTF-8 line bytes without the newline.
"""
import hashlib
import json
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
CASE = W / "case"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ok = True
    manifest = {}
    for line in (CASE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, name = line.split(None, 1)
        name = name.lstrip("*")
        actual = sha((CASE / name).read_bytes())
        manifest[name] = {"pinned": h, "actual": actual, "ok": h == actual}
        ok &= h == actual
    rows = {}
    for fn in ("questions.jsonl", "responses.jsonl"):
        out = []
        for raw in (CASE / fn).read_bytes().split(b"\n"):
            if not raw.strip():
                continue
            obj = json.loads(raw.decode("utf-8"))
            key = obj.get("question_id") if fn == "questions.jsonl" else obj.get("id")
            out.append({"key": key, "sha256": sha(raw)})
        rows[fn] = out
    pins = {
        "manifest_sha256": sha((CASE / "MANIFEST.sha256").read_bytes()),
        "files": manifest,
        "rows": rows,
    }
    (W / "audit" / "pins.json").write_text(json.dumps(pins, indent=1) + "\n", encoding="utf-8", newline="\n")
    for name, v in manifest.items():
        print(f"{'OK ' if v['ok'] else 'BAD'} {v['actual']}  {name}")
    print("MANIFEST.sha256 itself:", pins["manifest_sha256"])
    for fn, out in rows.items():
        print(fn, len(out), "rows; first", out[0]["key"], out[0]["sha256"][:16])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
