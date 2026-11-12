"""Step 1: one sha256 per data row, over its uuid, user message, instruction ids and kwargs.

Writes audit/frozen/row_hashes.tsv (row index, uuid, sha256) and prints the
sha256 of that file. The hash input is
json.dumps([uuid, message, instruction_id_list, kwargs], ensure_ascii=False, sort_keys=True)
encoded as UTF-8.
"""
import hashlib
import json

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"
OUT = "<W>/audit/frozen/row_hashes.tsv"

lines = []
with open(PATH, encoding="utf-8") as f:
    for i, line in enumerate(f):
        row = json.loads(line)
        nu = row["extra_info"]["nemotron_ultra"]
        rec = json.loads(nu["record_json"])
        payload = json.dumps(
            [nu["uuid"], row["prompt"][0]["content"], rec["instruction_id_list"], rec["kwargs"]],
            ensure_ascii=False,
            sort_keys=True,
        )
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        lines.append(f"{i}\t{nu['uuid']}\t{h}\n")
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("row\tuuid\tsha256\n")
    f.writelines(lines)
print("rows", len(lines))
print("first row", lines[0].strip())
with open(OUT, "rb") as f:
    print("row_hashes.tsv sha256", hashlib.sha256(f.read()).hexdigest())
uuids = [l.split("\t")[1] for l in lines]
print("unique uuids", len(set(uuids)))
