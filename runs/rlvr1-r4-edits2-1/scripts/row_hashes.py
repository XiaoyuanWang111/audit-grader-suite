"""Write one sha256 per data row (whole JSON line, and the grading-relevant fields), plus data facts."""
import hashlib
import json

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
OUT = "<W>/audit/frozen/row_hashes.tsv"
n_imp = 0
imp = []
with open(DATA, "rb") as f, open(OUT, "w", encoding="utf-8", newline="\n") as out:
    out.write("index\tuuid\tsha256_line\tsha256_grading_fields\n")
    for i, raw in enumerate(f):
        line = raw.rstrip(b"\n")
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        key = json.dumps(
            {"uuid": rec["uuid"], "prompt": row["prompt"], "instruction_id_list": rec["instruction_id_list"],
             "kwargs": rec["kwargs"]}, ensure_ascii=False, sort_keys=True)
        out.write(f"{i}\t{rec['uuid']}\t{hashlib.sha256(line).hexdigest()}\t{hashlib.sha256(key.encode()).hexdigest()}\n")
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]:
                n_imp += 1
                imp.append((rec["uuid"], kw))
        if rec.get("grading_mode") is not None:
            print("grading_mode set", rec["uuid"])
print("nth_paragraph > num_paragraphs rows:", n_imp)
for u, kw in imp[:5]:
    print(" ", u, kw)
