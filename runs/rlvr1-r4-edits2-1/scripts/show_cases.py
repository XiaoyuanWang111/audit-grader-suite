"""Print short excerpts of panel cases for one check.

usage: show_cases.py CHECK [defect|decision|rp_pass|rp_fail|sk_pass|vi_pass] [sk|vi] [N] [--heldout] [--seed S]
Prints at most 160 characters from the start and 100 from the end of the graded text (repr), never a
reasoning block.
"""
import argparse
import glob
import gzip
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402

CASE = "<W>/case"
ap = argparse.ArgumentParser()
ap.add_argument("check")
ap.add_argument("kind", nargs="?", default="defect")
ap.add_argument("grader", nargs="?", default="sk")
ap.add_argument("n", nargs="?", type=int, default=6)
ap.add_argument("--heldout", action="store_true")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--head", type=int, default=160)
ap.add_argument("--tail", type=int, default=100)
a = ap.parse_args()

rows = P.load_rows()
cands = []
if a.kind in ("defect",):
    with gzip.open(os.path.join(HERE, "..", "results", "defect_cases.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["iid"] == a.check and d["grader"] == a.grader and (not a.heldout or d["held_out"]):
                cands.append((d["run"], d["uuid"], d["j"]))
else:
    with gzip.open(os.path.join(HERE, "..", "frozen", "panel_verdicts.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if a.heldout and not r["held_out"]:
                continue
            for j, iid in enumerate(r["ids"]):
                if iid != a.check:
                    continue
                g, v = r[a.grader][j], r["rp"][j]
                ok = {"decision": g is not None and g != v, "rp_pass": v, "rp_fail": not v,
                      "sk_pass": r["sk"][j], "vi_pass": r["vi"][j]}.get(a.kind)
                if ok:
                    cands.append((r["run"], r["uuid"], j))
random.Random(a.seed).shuffle(cands)
print(f"{len(cands)} cases; showing {min(a.n, len(cands))}")
raw = {}
for path in glob.glob(CASE + "/panel/*/*.jsonl"):
    folder = os.path.basename(os.path.dirname(path))
    run = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            raw[(f"{folder}/{run}", x["uuid"])] = x["raw_response"]
for run, uuid, j in cands[: a.n]:
    rec = rows[uuid]
    kw = {k: v for k, v in (rec["kwargs"][j] or {}).items() if v is not None}
    text = raw[(run, uuid)]
    g = C.graded_text(text, run.split("/")[0].endswith("__thinking"))
    sk_text = P.final_answer_text(text)
    nv = P.nvidia_check(a.check, kw, sk_text)[0]
    vi = P.verifyit_check(a.check, kw, P.verifyit_candidate(text))[0]
    rp = None if g is None else C.check(a.check, kw, g)
    shown = sk_text if g is None else g
    print(f"--- {run} {uuid} j={j} kw={kw} nvidia={nv} verifyit={vi} replacement={rp} len={len(shown)}"
          + (" [extraction failure: showing SkyRL's graded text]" if g is None else ""))
    print("HEAD:", repr(shown.strip()[: a.head]))
    if len(shown.strip()) > a.head:
        print("TAIL:", repr(shown.strip()[-a.tail:]))
