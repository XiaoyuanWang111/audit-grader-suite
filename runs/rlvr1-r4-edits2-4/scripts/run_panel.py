"""Step 5: grade every stored panel response with the SkyRL reward, the task-curation gate and
the frozen replacement grader. Writes audit/work/panel_verdicts.jsonl (one line per response).

SkyRL draws nth_paragraph_first_word's index from `random` for 77 rows; each response is graded
with random.seed(<row line>) so the run is reproducible, and those rows are graded a second time
with random.seed(<row line> + 10**6) to measure the nondeterminism.
"""
import json
import random
import sys
from multiprocessing import Pool
from pathlib import Path

A = Path("<W>/audit")
CASE = A.parent / "case"
FILES = sorted((CASE / "panel").glob("*/*.jsonl"))


def init():
    sys.path.insert(0, str(A / "lib"))
    global h, cg, rows
    import harness as h  # noqa: F401
    from contract_grader import ContractGrader

    cg = ContractGrader()
    rows = h.load_rows()


def grade(args):
    folder, run, line_no, line = args
    obj = json.loads(line)
    rec = rows[obj["uuid"]]
    raw = obj["raw_response"]
    thinking = folder.endswith("__thinking")
    random.seed(rec["_line"])
    s = h.skyrl_row(rec, raw)
    g = h.gate_row(rec, raw)
    rtext = cg.extract(raw, thinking)
    r = [cg.check(i, k, rtext) for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
    out = {
        "folder": folder, "run": run, "i": line_no, "uuid": obj["uuid"], "line": rec["_line"],
        "finish_reason": obj["finish_reason"], "num_tokens": obj["num_tokens"], "max_tokens": obj["max_tokens"],
        "thinking": thinking, "has_close": "</think>" in raw, "has_open": "<think>" in raw,
        "extraction_failure": rtext is None,
        "skyrl_text_empty": not h.skyrl_text(raw).strip(),
        "same_text": (rtext or "") == h.skyrl_text(raw),
        "ids": rec["instruction_id_list"],
        "skyrl": s["results"], "skyrl_err": s["errors"], "skyrl_reward": s["reward"], "skyrl_infra": s["infra_error"],
        "gate": g["results"], "gate_pass": g["gate_pass"],
        "repl": r,
    }
    if "length_constraints:nth_paragraph_first_word" in rec["instruction_id_list"]:
        k = rec["kwargs"][rec["instruction_id_list"].index("length_constraints:nth_paragraph_first_word")]
        if k["nth_paragraph"] > k["num_paragraphs"]:
            random.seed(rec["_line"] + 10**6)
            s2 = h.skyrl_row(rec, raw)
            out["nth_gt_num"] = True
            out["skyrl_reward_seed2"] = s2["reward"]
            out["skyrl_seed2"] = s2["results"]
    return out


def tasks():
    for path in FILES:
        folder, run = path.parent.name, path.stem
        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f):
                yield folder, run, line_no, line


if __name__ == "__main__":
    out_path = A / "work" / "panel_verdicts.jsonl"
    n = 0
    with Pool(8, initializer=init) as pool, open(out_path, "w", encoding="utf-8", newline="\n") as out:
        for result in pool.imap(grade, tasks(), chunksize=32):
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            n += 1
            if n % 2000 == 0:
                print("graded", n, flush=True)
    print("done", n)
