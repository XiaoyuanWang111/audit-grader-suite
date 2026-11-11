"""Grade every stored panel response with the SkyRL reward, the verifyit gate and the replacement.

Output: audit/frozen/panel_verdicts.jsonl.gz, one line per response:
  run, uuid, idx, finish_reason, num_tokens, max_tokens, held_out,
  ext: {"skyrl_empty", "repl_failure", "has_close", "has_open"},
  ids, sk (SkyRL per-constraint verdicts), sk_err (indices with a checker exception), sk_reward,
  vi (verifyit verdicts, null for judged ids), vi_err, gate,
  rp (replacement verdicts, proposed readings).
Held-out responses (step 5): int(sha256("<folder>/<run>/<uuid>"), 16) % 5 == 0, fixed before any panel
result was looked at.
"""
import glob
import gzip
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
CASE = "<W>/case"
OUT = os.path.join(HERE, "..", "frozen", "panel_verdicts.jsonl.gz")

_rows = None


def held_out(folder, run, uuid):
    return int(hashlib.sha256(f"{folder}/{run}/{uuid}".encode()).hexdigest(), 16) % 5 == 0


def _init():
    global _rows, P, C
    import contracts_grader as C  # noqa: F401
    import pipelines as P  # noqa: F401
    globals()["P"] = P
    globals()["C"] = C
    _rows = P.load_rows()


def grade_one(item):
    folder, run, rec = item
    row = _rows[rec["uuid"]]
    raw = rec["raw_response"]
    ids, kws = row["instruction_id_list"], row["kwargs"]
    reward, sk, sk_err, sk_text = P.skyrl_grade(raw, row)
    gate, vi, vi_err, vi_text = P.verifyit_gate(raw, row)
    reasoning = folder.endswith("__thinking")
    g = C.graded_text(raw, reasoning)
    rp = C.grade_text(g, ids, kws)
    return {
        "run": f"{folder}/{run}", "uuid": rec["uuid"], "idx": row["_index"],
        "finish_reason": rec["finish_reason"], "num_tokens": rec["num_tokens"], "max_tokens": rec["max_tokens"],
        "held_out": held_out(folder, run, rec["uuid"]),
        "ext": {"skyrl_empty": sk_text == "", "vi_empty": vi_text.strip() == "", "repl_failure": g is None,
                "has_close": "</think>" in raw, "has_open": "<think>" in raw},
        "ids": ids, "sk": sk, "sk_err": [i for i, e in enumerate(sk_err) if e],
        "sk_err_msg": [e for e in sk_err if e][:3], "sk_reward": reward,
        "vi": vi, "vi_err": [i for i, e in enumerate(vi_err) if e], "gate": gate,
        "rp": rp,
    }


def items():
    for path in sorted(glob.glob(CASE + "/panel/*/*.jsonl")):
        folder = os.path.basename(os.path.dirname(path))
        run = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            for line in f:
                yield folder, run, json.loads(line)


if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    t0 = time.time()
    all_items = list(items())
    n = 0
    tmp = OUT + ".partial"
    with Pool(workers, initializer=_init) as pool, gzip.open(tmp, "wt", encoding="utf-8") as out:
        for result in pool.imap(grade_one, all_items, chunksize=32):
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            n += 1
            if n % 2000 == 0:
                print(f"{n}/{len(all_items)} {time.time() - t0:.0f}s", flush=True)
    os.replace(tmp, OUT)
    print(f"done {n} responses in {time.time() - t0:.0f}s -> {OUT}")
