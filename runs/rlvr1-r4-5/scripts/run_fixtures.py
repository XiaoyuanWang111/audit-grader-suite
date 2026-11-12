"""Run every hand-written fixture against the graders, classify wrong verdicts, write records.

Outputs:
- audit/out/fixture_results.json : every fixture with each grader's verdict and classification
- audit/tests/expected_wrong.json : (fixture id, grader) pairs the current graders get wrong (xfail strict)
- appends the hand-written fixtures to audit/fixtures.jsonl (rewritten: hand-written part only;
  generated fixtures are appended by the step-4 scripts)
"""
import hashlib
import json
import random
import sys

sys.path.insert(0, "<W>/audit")
sys.path.insert(0, "<W>/audit/tests")

import harness as h  # noqa: E402
from fixture_defs import FIXTURES, PIPELINE  # noqa: E402
from replacement import Replacement  # noqa: E402

A = "<W>/audit"
SEED = 20261112  # same seed as tests/test_fixtures.py


def fid(iid, kwargs, response, extra=""):
    blob = json.dumps([iid, kwargs, response, extra], ensure_ascii=False, sort_keys=True).encode("utf-8")
    return iid.split(":")[1] + ":" + hashlib.sha256(blob).hexdigest()[:16]


def lab(b):
    return None if b is None else ("pass" if b else "fail")


def classify(verdict, label, deps, alt_label):
    if verdict is None:
        return "n/a"
    if verdict == label:
        return "ok"
    if deps and alt_label == verdict:
        return "decision"
    return "finding"


def main():
    out = []
    for iid, kw, resp, label, deps, note in FIXTURES:
        alt = Replacement(**{d: "alt" for d in deps}) if deps else None
        alt_label = lab(alt.check(iid, kw, resp)) if alt else None
        random.seed(SEED)
        nv, nv_err = h.nv_check(iid, kw, resp)
        random.seed(SEED)
        vs, vs_err = h.vs_check(iid, kw, resp)
        vg, vg_err = h.vg_check(iid, kw, resp)
        rec = {
            "id": fid(iid, kw, resp),
            "kind": "hand",
            "instruction_id": iid,
            "kwargs": kw,
            "response": resp,
            "label": label,
            "deps": deps,
            "note": note,
            "alt_label": alt_label,
            "R": lab(h.R.check(iid, kw, resp)),
            "RF": lab(h.RF.check(iid, kw, resp)),
            "NV": lab(nv),
            "NV_error": nv_err,
            "VS": lab(vs),
            "VS_error": vs_err,
            "VG": lab(vg),
            "VG_error": vg_err,
        }
        out.append(rec)
    for iid, kw, raw, thinking, label, deps, note in PIPELINE:
        record = {"instruction_id_list": [iid], "kwargs": [kw]}
        alt = Replacement(**{d: "alt" for d in deps}) if deps else None
        alt_label = lab(alt.check(iid, kw, alt.graded_text(raw, thinking))) if alt else None
        random.seed(SEED)
        nvr = h.nv_row(raw, record)
        vgr = h.vg_row(raw, record)
        action = h.final_answer_text(raw)
        random.seed(SEED)
        vsv = h.vs_row(action, record)
        vs = vsv["detail"]["source_feedback"]["follow_instruction_list"][0] if vsv["status"] == "scored" else False
        rec = {
            "id": fid(iid, kw, raw, "pipeline-thinking" if thinking else "pipeline"),
            "kind": "pipeline",
            "thinking": thinking,
            "instruction_id": iid,
            "kwargs": kw,
            "response": raw,
            "label": label,
            "deps": deps,
            "note": note,
            "alt_label": alt_label,
            "R": lab(h.r_row(raw, record, thinking)["results"][0]),
            "RF": lab(h.r_row(raw, record, thinking, h.RF)["results"][0]),
            "NV": lab(bool(nvr["results"][0]) and nvr["outcome"] == "graded"),
            "NV_error": nvr["errors"][0],
            "VS": lab(vs),
            "VS_error": None if vsv["status"] == "scored" else vsv["status"],
            "VG": lab(vgr["results"][0]) if vgr["results"][0] is not None else None,
            "VG_error": vgr["errors"][0],
        }
        out.append(rec)

    for rec in out:
        for g in ("NV", "VS", "VG", "R", "RF"):
            rec["cls_" + g] = classify(rec[g], rec["label"], rec["deps"], rec["alt_label"])
    ids = [r["id"] for r in out]
    assert len(ids) == len(set(ids)), "duplicate fixture ids"

    json.dump(out, open(f"{A}/out/fixture_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    wrong = sorted([r["id"], g] for r in out for g in ("NV", "VS", "VG") if r["cls_" + g] in ("finding", "decision"))
    json.dump(wrong, open(f"{A}/tests/expected_wrong.json", "w", encoding="utf-8"), indent=0)
    with open(f"{A}/fixtures_hand.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps({k: r[k] for k in ("id", "instruction_id", "kwargs", "response", "label")}, ensure_ascii=False) + "\n")

    # summary
    n = len(out)
    print("fixtures", n, "hand", sum(r["kind"] == "hand" for r in out), "pipeline", sum(r["kind"] == "pipeline" for r in out))
    for g in ("R", "RF", "NV", "VS", "VG"):
        c = {}
        for r in out:
            c[r["cls_" + g]] = c.get(r["cls_" + g], 0) + 1
        print(g, c)
    bad_r = [r for r in out if r["R"] != r["label"]]
    print("replacement disagrees with label:", len(bad_r))
    for r in bad_r:
        print("  R!", r["id"], r["instruction_id"], repr(r["response"][:60]), r["label"], r["R"])
    bad_dep = [r for r in out if r["deps"] and r["alt_label"] == r["label"]]
    print("deps that do not flip the label:", len(bad_dep))
    for r in bad_dep:
        print("  dep!", r["id"], r["instruction_id"], repr(r["response"][:60]), r["deps"])
    for g in ("NV", "VS", "VG"):
        print(f"\n== {g} wrong verdicts")
        for r in out:
            if r["cls_" + g] in ("finding", "decision"):
                err = r.get(g + "_error")
                print(f"  {r['cls_'+g]:8s} {r['id']:36s} {r['instruction_id']:45s} label={r['label']} got={r[g]} {repr(r['response'][:50])} {r['deps'] if r['cls_'+g]=='decision' else ''} {('ERR ' + err) if err else ''}")


if __name__ == "__main__":
    main()
