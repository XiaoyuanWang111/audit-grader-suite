"""Step 1: one sha256 per data row over its uuid, user prompt, instruction ids
and kwargs (as stored in record_json), in canonical JSON. Writes
audit/frozen/row_hashes.tsv (index, uuid, row hash) and prints the file's
sha256.
"""
import hashlib
import json
import pathlib

W = pathlib.Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT = W / "audit" / "frozen" / "row_hashes.tsv"


def row_hash(row):
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    payload = {
        "uuid": rec["uuid"],
        "prompt": row["prompt"],
        "instruction_id_list": rec["instruction_id_list"],
        "kwargs": rec["kwargs"],
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return rec["uuid"], hashlib.sha256(blob).hexdigest()


def main():
    lines = ["index\tuuid\trow_sha256"]
    with DATA.open(encoding="utf-8") as f:
        for i, l in enumerate(f):
            u, h = row_hash(json.loads(l))
            lines.append(f"{i}\t{u}\t{h}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(len(lines) - 1, "rows;", "file sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())
    print("row 0:", lines[1])


if __name__ == "__main__":
    main()
