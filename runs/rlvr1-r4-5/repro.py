"""Reproduce a grader verdict.

    repro.py FIXTURE_ID
        looks the id up in audit/fixtures.jsonl and prints the input and every grader's verdict
    repro.py INSTRUCTION_ID KWARGS_JSON RESPONSE_JSON
        grades one constraint, e.g.
        repro.py keywords:word_once '{"keyword": "fix"}' '"Fix it and fix it again."'
    repro.py --pipeline [--thinking] INSTRUCTION_ID KWARGS_JSON RAW_RESPONSE_JSON
        runs each pipeline's extraction first (final_answer_text / _answer_text / G1)

Graders: NV = SkyRL reward, default config (grade_instruction_following, NVIDIA checkers);
VS = SkyRL reward with verifyit_enabled (grade_nemotron_instructions, in-process);
VG = task-curation deterministic gate (verifyit checks via resolve_checks; "judge" for semantic ids);
R = replacement grader (contract, proposed readings). The global RNG is seeded with 20261112 first.
"""
import json
import os
import random
import sys

os.environ.setdefault("NLTK_DATA", "<W>/case/deps/nltk_data")
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import logging  # noqa: E402

logging.disable(logging.CRITICAL)
import harness as h  # noqa: E402

SEED = 20261112


def lab(v):
    return {True: "pass", False: "fail", None: "judge (no deterministic check)"}[v if v is None else bool(v)]


def one(iid, kw, resp):
    out = {}
    random.seed(SEED)
    v, e = h.nv_check(iid, kw, resp)
    out["NV"] = lab(v) + (f"  [error: {e}]" if e else "")
    random.seed(SEED)
    v, e = h.vs_check(iid, kw, resp)
    out["VS"] = lab(v) + (f"  [error: {e[:120]}]" if e else "")
    v, e = h.vg_check(iid, kw, resp)
    out["VG"] = lab(v) + (f"  [error: {e}]" if e else "")
    out["R"] = lab(h.R.check(iid, kw, resp))
    return out


def pipeline(iid, kw, raw, thinking):
    record = {"instruction_id_list": [iid], "kwargs": [kw]}
    random.seed(SEED)
    nv = h.nv_row(raw, record)
    random.seed(SEED)
    vs = h.vs_row(h.final_answer_text(raw), record)
    vg = h.vg_row(raw, record)
    r = h.r_row(raw, record, thinking)
    return {
        "graded text (SkyRL final_answer_text)": h.final_answer_text(raw)[:80],
        "NV": f"{lab(nv['results'][0])} outcome={nv['outcome']}" + (f" error={nv['errors'][0]}" if nv["errors"][0] else ""),
        "VS": lab(vs["status"] == "scored" and vs["detail"]["source_feedback"]["follow_instruction_list"][0]) + f" status={vs['status']}",
        "VG": lab(vg["results"][0]),
        "R": lab(r["results"][0]) + (" (extraction failure)" if r["extraction_failure"] else ""),
    }


def main(argv):
    if len(argv) == 1 and ":" in argv[0] and not argv[0].startswith("{"):
        fid = argv[0]
        for line in open(os.path.join(HERE, "fixtures.jsonl"), encoding="utf-8"):
            d = json.loads(line)
            if d["id"] == fid:
                print("instruction_id:", d["instruction_id"])
                print("kwargs:", json.dumps(d["kwargs"], ensure_ascii=False))
                print("response:", json.dumps(d["response"], ensure_ascii=False))
                print("label (contract):", d["label"])
                if d.get("source", "").startswith("hand-written") and d.get("thinking") is None and "pipeline" in d.get("kind", ""):
                    pass
                res = None
                for p in _pipeline_ids():
                    if p[0] == fid:
                        res = pipeline(d["instruction_id"], d["kwargs"], d["response"], p[1])
                if res is None:
                    res = one(d["instruction_id"], d["kwargs"], d["response"])
                for k, v in res.items():
                    print(f"{k}: {v}")
                return
        raise SystemExit(f"unknown fixture id {fid}")
    thinking = False
    if argv and argv[0] == "--pipeline":
        argv = argv[1:]
        if argv and argv[0] == "--thinking":
            thinking, argv = True, argv[1:]
        iid, kw, raw = argv[0], json.loads(argv[1]), json.loads(argv[2])
        for k, v in pipeline(iid, kw, raw, thinking).items():
            print(f"{k}: {v}")
        return
    iid, kw, resp = argv[0], json.loads(argv[1]), json.loads(argv[2])
    for k, v in one(iid, kw, resp).items():
        print(f"{k}: {v}")


def _pipeline_ids():
    sys.path.insert(0, os.path.join(HERE, "tests"))
    from fixture_defs import PIPELINE
    from run_ids import fid

    return [(fid(i, k, raw, "pipeline-thinking" if th else "pipeline"), th) for i, k, raw, th, *_ in PIPELINE]


if __name__ == "__main__":
    main(sys.argv[1:])
