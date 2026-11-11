"""Print the instruction region of a few prompts that carry a given instruction id.

Usage: python show_instr.py <instruction_id> [n] [seed]
Reads only the data file (the text the model sees). Prints the header phrase and what follows it.
"""
import json
import random
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
HEADER = re.compile(
    r"(Please|Make sure|Your response should|When answering|While responding|Ensure|Follow|Your answer)[^:\n]{0,80}:"
)

iid = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
rows = []
for line in DATA.open(encoding="utf-8"):
    row = json.loads(line)
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    if iid in rec["instruction_id_list"]:
        rows.append((row, rec))
print("rows with", iid, ":", len(rows))
random.seed(seed)
for row, rec in random.sample(rows, min(n, len(rows))):
    c = row["prompt"][0]["content"]
    ms = list(HEADER.finditer(c))
    start = ms[-1].start() if ms else max(0, len(c) - 600)
    print("UUID", rec["uuid"], "IDS", list(zip(rec["instruction_id_list"], rec["kwargs"])))
    print(repr(c[start : start + 900]))
    print("-----")
