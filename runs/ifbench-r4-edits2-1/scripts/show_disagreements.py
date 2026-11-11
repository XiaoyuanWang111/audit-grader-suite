"""Print short excerpts of panel responses where the grader and the replacement disagree on one check.

Usage: show_disagreements.py <check> <fp|fn|gr> [n] [chars] [seed]
  fp: grader pass, replacement fail; fn: grader fail, replacement pass; gr: grader != reference.
Held-out files and responses whose reasoning never closed are skipped (no thinking text is printed).
"""
import csv
import gzip
import json
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
check, mode = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
chars = int(sys.argv[4]) if len(sys.argv) > 4 else 300
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
THINK = ("Qwen__Qwen3-8B__thinking", "Qwen__Qwen3-14B__thinking")

sel = []
for r in csv.DictReader(gzip.open(W / "audit/frozen/panel_verdicts.tsv.gz", "rt", encoding="utf-8"), delimiter="\t"):
    if r["iid"] != check or r["unclosed"] == "1":
        continue
    if r["run"] == ("greedy_repeat" if r["config"] in THINK else "sample0"):
        continue
    if mode == "fp" and r["g_strict"] == "1" and r["rep"] == "0" or mode == "fn" and r["g_strict"] == "0" and r["rep"] == "1" \
            or mode == "gr" and r["g_strict"] != r["r_strict"]:
        sel.append(r)
random.Random(seed).shuffle(sel)
print(f"{len(sel)} candidates (non-held-out); showing {min(n, len(sel))}")
cache = {}
for r in sel[:n]:
    f = W / "case/panel" / r["config"] / f"{r['run']}.jsonl"
    if f not in cache:
        cache[f] = {json.loads(l)["key"]: json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()}
    d = cache[f][r["key"]]
    print(f"--- {r['config']}/{r['run']} key={r['key']} g={r['g_strict']} r={r['r_strict']} rep={r['rep']}")
    print(repr(d["response"][:chars]))
