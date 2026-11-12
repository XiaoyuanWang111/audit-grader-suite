"""Step 4: content-free responses on every row, graded by SkyRL, the task-curation gate and the replacement.

Responses: empty text; whitespace; one word repeated; one sentence repeated; and a restatement
of the instructions (the row's own prompt echoed back). For each, per check: the share of the
check's constraints that pass; per grader: the share of rows that get reward 1.0 (SkyRL), pass
the gate (task curation; the judge then decides), or pass every contract (replacement).
Writes audit/content_free.json.
"""

import collections
import json
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)
logging.disable(logging.ERROR)

import harness as h  # noqa: E402

RESPONSES = {
    "empty": lambda row: "",
    "whitespace": lambda row: "  \n ",
    "repeated_word": lambda row: " ".join(["the"] * 300),
    "repeated_sentence": lambda row: " ".join(["This is a sentence."] * 40),
    "restated_prompt": lambda row: row["prompt"],
}


def main():
    rows = h.load_rows()
    out = {}
    for name, make in RESPONSES.items():
        per_check = collections.defaultdict(lambda: collections.Counter())
        row_pass = collections.Counter()
        exceptions = collections.Counter()
        for row in rows:
            resp = make(row)
            sky = h.skyrl_grade(resp, row["ids"], row["kwargs"])
            tc = h.tc_gate(resp, row["ids"], row["kwargs"])
            rep = h.contract_grade(resp, row["ids"], row["kwargs"], row["prompt"], False)
            row_pass["skyrl_reward_1"] += sky["reward"] == 1.0
            row_pass["skyrl_infra_error"] += sky["infra_error"]
            row_pass["tc_gate_pass"] += tc["gate_passed"]
            row_pass["rep_all_pass"] += rep["reward"] == 1.0
            for i, iid in enumerate(row["ids"]):
                c = per_check[iid]
                c["n"] += 1
                c["skyrl"] += bool(sky["results"][i]) and not sky["errors"][i]
                if sky["errors"][i]:
                    exceptions[(iid, sky["errors"][i][:80])] += 1
                if tc["results"][i] is not None:
                    c["tc_n"] += 1
                    c["tc"] += bool(tc["results"][i])
                c["rep"] += bool(rep["results"][i])
        out[name] = {
            "rows": len(rows),
            "row_level": dict(row_pass),
            "per_check": {k: dict(v) for k, v in sorted(per_check.items())},
            "skyrl_exceptions": {f"{k[0]} | {k[1]}": v for k, v in exceptions.items()},
        }
        print(f"== {name}: rows {len(rows)} {dict(row_pass)}")
        for iid, c in sorted(per_check.items()):
            flags = []
            if c["skyrl"]:
                flags.append(f"skyrl {c['skyrl']}/{c['n']}")
            if c["tc"]:
                flags.append(f"tc {c['tc']}/{c['tc_n']}")
            if c["rep"]:
                flags.append(f"contract {c['rep']}/{c['n']}")
            if flags:
                print(f"   {iid:45s} " + ", ".join(flags))
        for k, v in exceptions.items():
            print(f"   SKYRL EXCEPTION {k[0]}: {k[1]} x{v}")
    with open(os.path.join(AUDIT, "content_free.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
