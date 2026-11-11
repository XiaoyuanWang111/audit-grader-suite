"""Write audit/frozen/row_hashes.tsv: one line per data row, in file order.

Columns: line number (1-based), uuid, sha256 of the exact JSON line (without the newline),
sha256 of json.dumps([uuid, prompt messages, instruction_id_list, kwargs], ensure_ascii=False, sort_keys=True).
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")
OUT = os.path.join(ROOT, "audit", "frozen", "row_hashes.tsv")
with open(DATA, "rb") as f, open(OUT, "w", encoding="utf-8", newline="\n") as out:
    out.write("line\tuuid\tsha256_line\tsha256_key\n")
    for i, raw in enumerate(f, 1):
        raw = raw.rstrip(b"\n")
        row = json.loads(raw)
        nu = row["extra_info"]["nemotron_ultra"]
        rec = json.loads(nu["record_json"])
        key = json.dumps([nu["uuid"], row["prompt"], rec["instruction_id_list"], rec["kwargs"]],
                         ensure_ascii=False, sort_keys=True)
        out.write(f"{i}\t{nu['uuid']}\t{hashlib.sha256(raw).hexdigest()}\t{hashlib.sha256(key.encode('utf-8')).hexdigest()}\n")
print("wrote", OUT)
