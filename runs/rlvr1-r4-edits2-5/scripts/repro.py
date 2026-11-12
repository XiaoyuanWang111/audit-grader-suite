"""Reproduce a verdict of both graders and of the contract (replacement, proposed readings).

Constraint:  python scripts/repro.py check INSTRUCTION_ID KWARGS_JSON RESPONSE [--reasoning] [--runs N]
Row:         python scripts/repro.py row UUID RESPONSE [--reasoning]

Run from audit/ with NLTK_DATA and PYTHONDONTWRITEBYTECODE set (see AUDIT.md). In Git Bash, write a
response with line breaks as $'line one\\nline two'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
import graders as g  # noqa: E402

args = sys.argv[1:]
reasoning = "--reasoning" in args
if reasoning:
    args.remove("--reasoning")
runs = 1
if "--runs" in args:
    i = args.index("--runs")
    runs = int(args[i + 1])
    del args[i:i + 2]


def word(v):
    return "pass" if v else "fail"


if args[0] == "check":
    iid, kw, resp = args[1], json.loads(args[2]), args[3]
    results = [fl.verdict_skyrl(iid, kw, resp) for _ in range(runs)]
    if runs == 1:
        v, e = results[0]
        print(f"A  SkyRL reward checker : {word(v)}" + (f"  (exception {e}: INFRA_ERROR, reward 0.0)" if e else ""))
    else:
        print(f"A  SkyRL reward checker : passes in {sum(bool(v) for v, _ in results)} of {runs} gradings")
    v, e = fl.verdict_curation(iid, kw, resp)
    print("B  curation gate check  : " + ("judged by the LLM (no deterministic check)" if v is None else word(v)))
    print(f"C  contract (proposed)  : {word(fl.verdict_replacement(iid, kw, resp, reasoning))}")
elif args[0] == "row":
    uuid, resp = args[1], args[2]
    for line in (W / "case/data/rlvr1_instruction_following.jsonl").open(encoding="utf-8"):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        if rec["uuid"] == uuid:
            break
    else:
        sys.exit("uuid not found")
    a = g.skyrl_row(resp, rec)
    b = g.curation_row(resp, rec)
    c = [fl.cg.grade_constraint(i, k, fl.cg.graded_text(resp, reasoning)) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
    print("constraints:", rec["instruction_id_list"])
    print(f"A  SkyRL row reward     : {a['reward']}  verdicts={a['verdicts']} errors={[e for e in a['errors'] if e]}")
    print(f"B  curation gate        : {'passed (the LLM judge decides)' if b['gate_passed'] else 'failed (reward 0.0)'}  verdicts={b['verdicts']}")
    print(f"C  contract (proposed)  : {float(all(c))}  verdicts={c}")
else:
    sys.exit(__doc__)
