"""Print a few requirement texts for the instruction ids given on the command line.

Usage: python show_texts.py ID [ID ...] [--n N] [--raw]
--raw prints the end of the whole prompt instead of the parsed item.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from survey_data import DATA, split_requirements  # noqa: E402

args = sys.argv[1:]
n = 3
raw = False
if "--n" in args:
    i = args.index("--n")
    n = int(args[i + 1])
    del args[i:i + 2]
if "--raw" in args:
    raw = True
    args.remove("--raw")
want = set(args)
seen = {k: 0 for k in want}
for idx, line in enumerate(DATA.open(encoding="utf-8")):
    row = json.loads(line)
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    p = rec["prompt"]
    reqs = split_requirements(p, len(rec["instruction_id_list"]))
    for k, (iid, kw) in enumerate(zip(rec["instruction_id_list"], rec["kwargs"])):
        if iid in want and seen[iid] < n:
            if raw:
                text = p if len(p) < 700 else p[:300] + " [...] " + p[-400:]
            elif reqs is not None:
                text = reqs[k]
            else:
                continue
            seen[iid] += 1
            print(f"[{iid}] row {idx} kwargs={json.dumps(kw, ensure_ascii=False)}")
            print("   " + repr(text[:700]))
