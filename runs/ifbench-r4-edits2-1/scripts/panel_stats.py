"""Count what the stored panel records show before grading: truncation, reasoning markers, empties, prompt matches.

Writes audit/frozen/panel_stats.json and prints a table per configuration.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import harness as H  # noqa: E402

rows = H.load_rows()
prompts = [r["prompt"] for r in rows]
keys = [str(r["key"]) for r in rows]

stats = {}
file_hashes = {}
problems = []
for folder in sorted(p for p in (H.CASE / "panel").iterdir() if p.is_dir()):
    for f in sorted(folder.glob("*.jsonl")):
        file_hashes[f"{folder.name}/{f.name}"] = H.sha256(f)
        c = Counter()
        lines = f.read_text(encoding="utf-8").splitlines()
        c["lines"] = len(lines)
        for i, line in enumerate(lines):
            d = json.loads(line)
            if i < len(rows):
                if str(d["key"]) != keys[i]:
                    c["key_mismatch"] += 1
                if d["prompt"] != prompts[i]:
                    c["prompt_mismatch"] += 1
            raw, resp = d["raw_response"], d["response"]
            c["finish_" + str(d["finish_reason"])] += 1
            if "</think>" in raw:
                c["has_close_think"] += 1
                exp = raw.rsplit("</think>", 1)[1].lstrip()
            else:
                exp = raw
            if exp != resp:
                c["extraction_rule_mismatch"] += 1
            if "<think>" in raw and "</think>" not in raw:
                c["unclosed_think"] += 1
                if d["finish_reason"] == "length":
                    c["unclosed_think_length"] += 1
            if not resp.strip():
                c["empty_response"] += 1
            if resp != resp.rstrip():
                c["trailing_ws"] += 1
            if resp.endswith("\n"):
                c["trailing_newline"] += 1
            if d["finish_reason"] == "length" and "</think>" in raw:
                c["length_after_close"] += 1
        stats[f"{folder.name}/{f.stem}"] = dict(c)

json.dump({"stats": stats, "file_sha256": file_hashes}, open(H.W / "audit/frozen/panel_stats.json", "w", encoding="utf-8", newline="\n"), indent=1)
agg = defaultdict(Counter)
for k, c in stats.items():
    agg[k.split("/")[0]].update(c)
cols = ["lines", "finish_length", "has_close_think", "unclosed_think", "unclosed_think_length", "empty_response", "trailing_ws", "extraction_rule_mismatch", "prompt_mismatch", "key_mismatch"]
print("config".ljust(46) + " ".join(c[:12].rjust(12) for c in cols))
tot = Counter()
for k in sorted(agg):
    tot.update(agg[k])
    print(k.ljust(46) + " ".join(str(agg[k].get(c, 0)).rjust(12) for c in cols))
print("TOTAL".ljust(46) + " ".join(str(tot.get(c, 0)).rjust(12) for c in cols))
print("files:", len(file_hashes))
