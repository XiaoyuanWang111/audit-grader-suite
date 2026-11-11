"""Write one sha256 per data row: over the row's whole JSON line, and over (uuid, prompt, ids, kwargs).

Output: audit/frozen/row_hashes.tsv with columns line_no, uuid, sha256_line, sha256_content.
sha256_content hashes json.dumps([uuid, prompt messages, instruction_id_list, kwargs], sort_keys=True, ensure_ascii=False).
"""
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
OUT = W / "audit" / "frozen" / "row_hashes.tsv"

with DATA.open("rb") as f, OUT.open("w", encoding="utf-8", newline="\n") as out:
    out.write("line_no\tuuid\tsha256_line\tsha256_content\n")
    for i, raw in enumerate(f, 1):
        line = raw.rstrip(b"\n")
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        content = json.dumps([rec["uuid"], row["prompt"], rec["instruction_id_list"], rec["kwargs"]],
                             sort_keys=True, ensure_ascii=False)
        out.write("%d\t%s\t%s\t%s\n" % (i, rec["uuid"], hashlib.sha256(line).hexdigest(),
                                        hashlib.sha256(content.encode("utf-8")).hexdigest()))
print("wrote", OUT)
