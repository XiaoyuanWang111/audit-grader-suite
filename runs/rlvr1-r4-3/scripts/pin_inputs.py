"""Step 1: pin the inputs.

Writes audit/frozen/row_hashes.tsv (one sha256 per data row) and prints the
hash comparison of the installed packages with the case copies. Reads no
grader code: it only hashes files.
"""
import hashlib
import json
import os
import sys

W = "<W>"
DATA = f"{W}/case/data/rlvr1_instruction_following.jsonl"
SITE = f"{W}/.venv/Lib/site-packages"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def row_hashes():
    out = f"{W}/audit/frozen/row_hashes.tsv"
    with open(DATA, "rb") as f, open(out, "w", encoding="utf-8", newline="\n") as o:
        o.write("index\tuuid\tline_sha256\tcontent_sha256\n")
        for i, line in enumerate(f):
            line = line.rstrip(b"\n")
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            content = json.dumps(
                {"uuid": rec["uuid"], "prompt": row["prompt"], "instruction_id_list": rec["instruction_id_list"],
                 "kwargs": rec["kwargs"], "request_json": row["extra_info"]["nemotron_ultra"]["request_json"]},
                ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            o.write(f"{i}\t{rec['uuid']}\t{sha(line)}\t{sha(content.encode('utf-8'))}\n")
    with open(out, "rb") as f:
        print("row_hashes.tsv", sha(f.read()))


def compare_tree(installed, case_dir):
    bad = []
    n = 0
    for root, _, files in os.walk(case_dir):
        for name in files:
            if "__pycache__" in root:
                continue
            p = os.path.join(root, name)
            rel = os.path.relpath(p, case_dir)
            q = os.path.join(installed, rel)
            n += 1
            if not os.path.exists(q):
                bad.append(("missing-installed", rel))
                continue
            with open(p, "rb") as a, open(q, "rb") as b:
                if sha(a.read()) != sha(b.read()):
                    bad.append(("differs", rel))
    extra = []
    for root, _, files in os.walk(installed):
        if "__pycache__" in root:
            continue
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), installed)
            if not os.path.exists(os.path.join(case_dir, rel)):
                extra.append(rel)
    print(installed, "files compared", n, "mismatches", bad, "installed-only", extra)


if __name__ == "__main__":
    row_hashes()
    compare_tree(f"{SITE}/verifyit", f"{W}/case/grader/verifyit")
    compare_tree(f"{SITE}/verifiable_instructions",
                 f"{W}/case/reference/verifiable-instructions/verifiable_instructions")
