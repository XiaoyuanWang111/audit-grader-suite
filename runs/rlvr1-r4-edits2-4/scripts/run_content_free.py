"""Step 4 content-free responses on every row: empty text, repeated text, and the prompt restated.

Per instruction id: how often each grader passes the constraint. Per row: how often the whole
row passes (SkyRL reward 1.0; gate passed). Writes audit/work/content_free.json.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

A = Path("<W>/audit")
sys.path.insert(0, str(A / "lib"))

import harness as h  # noqa: E402
from contract_grader import ContractGrader  # noqa: E402

cg = ContractGrader()
rows = h.load_rows()
KINDS = {
    "empty": lambda rec: "",
    "repeated": lambda rec: " ".join(["answer"] * 60),
    "restatement": lambda rec: rec["prompt"],
}
per_id = {k: defaultdict(Counter) for k in KINDS}
per_row = {k: Counter() for k in KINDS}
examples = {k: {} for k in KINDS}
for uuid, rec in rows.items():
    for kind, make in KINDS.items():
        raw = make(rec)
        random.seed(rec["_line"])
        s = h.skyrl_row(rec, raw)
        g = h.gate_row(rec, raw)
        r = [cg.check(i, k, cg.extract(raw, False)) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
        per_row[kind]["rows"] += 1
        per_row[kind]["skyrl_reward_1"] += s["reward"] == 1.0
        per_row[kind]["skyrl_infra_error"] += s["infra_error"]
        per_row[kind]["gate_pass"] += g["gate_pass"]
        per_row[kind]["gate_pass_empty_gate"] += g["gate_pass"] and g["n_deterministic"] == 0
        per_row[kind]["replacement_all_pass"] += all(r)
        for iid, kw, sp, se, gp, rp in zip(rec["instruction_id_list"], rec["kwargs"], s["results"], s["errors"], g["results"], r):
            c = per_id[kind][iid]
            c["n"] += 1
            c["skyrl_pass"] += bool(sp)
            c["skyrl_error"] += se is not None
            c["gate_pass"] += gp is True
            c["gate_judged"] += gp is None
            c["replacement_pass"] += rp
            if (sp or gp) and iid not in examples[kind]:
                examples[kind][iid] = {"uuid": uuid, "kwargs": kw, "skyrl": bool(sp), "gate": gp, "replacement": rp,
                                       "skyrl_error": se}
out = {"per_row": {k: dict(v) for k, v in per_row.items()},
       "per_id": {k: {i: dict(c) for i, c in sorted(v.items())} for k, v in per_id.items()},
       "examples": examples}
(A / "work" / "content_free.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for kind in KINDS:
    print("==", kind, dict(per_row[kind]))
    for iid, c in sorted(per_id[kind].items()):
        if c["skyrl_pass"] or c["gate_pass"] or c["skyrl_error"]:
            print(f"   {iid:<46} n={c['n']:<5} skyrl_pass={c['skyrl_pass']:<5} skyrl_err={c['skyrl_error']:<5} gate_pass={c['gate_pass']:<5} judged={c['gate_judged']:<5} repl_pass={c['replacement_pass']}")
