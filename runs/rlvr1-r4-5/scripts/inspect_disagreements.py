"""Print a few NV-vs-R defect disagreements for a check (development responses only, never held-out).

Usage: inspect_disagreements.py CHECK [N] [which]   which = nv_pass|nv_fail|any ; also VG via which=vg_pass|vg_fail
Prints only an excerpt of the graded text (after the last </think>), never reasoning text.
"""
import hashlib
import json
import sys

A = "<W>/audit"
W = "<W>"


def held_out(uuid):
    return int(hashlib.sha256(uuid.encode()).hexdigest(), 16) % 10 < 3


check = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
which = sys.argv[3] if len(sys.argv) > 3 else "any"
width = int(sys.argv[4]) if len(sys.argv) > 4 else 400
raws = {}
data = {}
for line in open(f"{W}/case/data/rlvr1_instruction_following.jsonl", encoding="utf-8"):
    row = json.loads(line)
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    data[rec["uuid"]] = rec
shown = 0
for p in ("panel_A.jsonl", "panel_B.jsonl"):
    for line in open(f"{A}/out/{p}", encoding="utf-8"):
        r = json.loads(line)
        if held_out(r["uuid"]) or check not in r["ids"]:
            continue
        j = r["ids"].index(check)
        nv = bool(r["nv"][j]) and not r["nv_err"][j]
        rr = r["r"][j]
        vg = r["vg"][j]
        if which.startswith("vg"):
            if vg is None or bool(vg) == rr:
                continue
            if which == "vg_pass" and not vg:
                continue
            if which == "vg_fail" and vg:
                continue
        else:
            if nv == rr or r["rf"][j] == nv:
                continue
            if which == "nv_pass" and not nv:
                continue
            if which == "nv_fail" and nv:
                continue
        if r["file"] not in raws:
            raws[r["file"]] = {}
            for l2 in open(f"{W}/case/panel/{r['file']}", encoding="utf-8"):
                d = json.loads(l2)
                raws[r["file"]][d["uuid"]] = d["raw_response"]
        raw = raws[r["file"]][r["uuid"]]
        text = raw[raw.rfind("</think>") + 8:] if "</think>" in raw else raw
        if r["thinking"] and "</think>" not in raw:
            text = "[reasoning never closed: not printed]"
        kw = data[r["uuid"]]["kwargs"][j]
        print(f"--- {r['file']} {r['uuid']} NV={nv} R={rr} RF={r['rf'][j]} VG={vg} kwargs={kw} len={len(text)}")
        print(repr(text[:width]))
        if len(text) > width:
            print("   ... tail:", repr(text[-150:]))
        shown += 1
        if shown >= n:
            sys.exit(0)
