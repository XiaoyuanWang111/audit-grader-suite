"""Step 1: per-row hashes of the data, and a summary of the stored panel records.

Writes audit/frozen/row_hashes.tsv (uuid, row index, sha256 over the canonical JSON of
uuid, prompt messages, instruction_id_list and kwargs) and prints panel counts.
"""
import collections
import hashlib
import json
import os

W = "<W>"
DATA = f"{W}/case/data/rlvr1_instruction_following.jsonl"
OUT = f"{W}/audit/frozen/row_hashes.tsv"


def row_hash(row):
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    key = {
        "uuid": rec["uuid"],
        "prompt": row["prompt"],
        "instruction_id_list": rec["instruction_id_list"],
        "kwargs": rec["kwargs"],
    }
    blob = json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return rec["uuid"], hashlib.sha256(blob).hexdigest()


def main():
    uuids = []
    with open(DATA, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8", newline="\n") as out:
        out.write("index\tuuid\trow_sha256\n")
        for i, line in enumerate(f):
            row = json.loads(line)
            u, h = row_hash(row)
            uuids.append(u)
            out.write(f"{i}\t{u}\t{h}\n")
    print("rows", len(uuids), "distinct uuids", len(set(uuids)))
    uuidset = set(uuids)
    panel = f"{W}/case/panel"
    for folder in sorted(os.listdir(panel)):
        p = os.path.join(panel, folder)
        if not os.path.isdir(p):
            continue
        for fn in sorted(os.listdir(p)):
            recs = [json.loads(l) for l in open(os.path.join(p, fn), encoding="utf-8")]
            fr = collections.Counter(r["finish_reason"] for r in recs)
            keys = collections.Counter(tuple(sorted(r.keys())) for r in recs)
            known = sum(r["uuid"] in uuidset for r in recs)
            dup = len(recs) - len({r["uuid"] for r in recs})
            think_open = sum("<think>" in r["raw_response"] for r in recs)
            think_close = sum("</think>" in r["raw_response"] for r in recs)
            empty = sum(not r["raw_response"].strip() for r in recs)
            models = collections.Counter((r["model"], r["revision"], r["run"]) for r in recs)
            mt = collections.Counter(r["max_tokens"] for r in recs)
            print(f"{folder}/{fn}: n={len(recs)} known_uuid={known} dup={dup} finish={dict(fr)} "
                  f"<think>={think_open} </think>={think_close} empty={empty} max_tokens={dict(mt.most_common(3))}")
            print("   models", dict(models))
            print("   keys", list(keys))


if __name__ == "__main__":
    main()
