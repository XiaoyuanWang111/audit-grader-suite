"""Step 5: grade every stored panel response with SkyRL, the task-curation gate and the replacement.

Writes audit/panel/verdicts.jsonl, one line per response:
  folder, run, uuid, row, finish_reason, num_tokens, max_tokens, reasoning_model,
  raw_sha256, has_close_think, has_open_think,
  skyrl: {results, errors, reward, infra, action_empty},
  tc: {results (None = judged), gate},
  rep: {results, extraction_failure},
  flips: per constraint, the decision entries whose other reading flips the replacement verdict.
Run with NLTK_DATA set. Uses a process pool.
"""

import glob
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)

PANEL = os.path.join(os.path.dirname(AUDIT), "case", "panel")
OUT_DIR = os.path.join(AUDIT, "panel")
OUT = os.path.join(OUT_DIR, "verdicts.jsonl")

_rows = None


def _init():
    global _rows, h, cg
    import logging

    logging.disable(logging.ERROR)  # absl logs every LangDetectException at ERROR
    import harness as h_
    import contract_grader as cg_
    h, cg = h_, cg_
    _rows = {r["uuid"]: r for r in h.load_rows()}


def _flipped(cg, text, iid, kw, prompt, base):
    out = []
    for name, checks in cg.AFFECTS.items():
        if iid not in checks:
            continue
        field, value = cg.DECISIONS[name]
        r = cg.Readings(**{field: value})
        try:
            v = cg.check(text, iid, kw, prompt, r)
        except Exception as e:  # noqa: BLE001
            v = None
        if v != base:
            out.append(name)
    return out


def grade_one(item):
    folder, run, line = item
    rec = json.loads(line)
    row = _rows[rec["uuid"]]
    raw = rec["raw_response"]
    reasoning = folder.endswith("__thinking")
    sky = h.skyrl_grade(raw, row["ids"], row["kwargs"])
    tc = h.tc_gate(raw, row["ids"], row["kwargs"])
    rep = h.contract_grade(raw, row["ids"], row["kwargs"], row["prompt"], reasoning)
    flips = []
    alt = []
    all_other = cg.Readings(**{field: value for field, value in cg.DECISIONS.values()})
    if not rep["extraction_failure"]:
        for iid, kw, v in zip(row["ids"], row["kwargs"], rep["results"]):
            flips.append(_flipped(cg, rep["text"], iid, kw, row["prompt"], v))
            alt.append(cg.check(rep["text"], iid, kw, row["prompt"], all_other))
    else:
        flips = [[] for _ in row["ids"]]
        alt = [False for _ in row["ids"]]
    return {
        "folder": folder,
        "run": run,
        "uuid": rec["uuid"],
        "row": row["index"],
        "finish_reason": rec["finish_reason"],
        "num_tokens": rec["num_tokens"],
        "max_tokens": rec["max_tokens"],
        "reasoning_model": reasoning,
        "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "has_close_think": "</think>" in raw,
        "has_open_think": "<think>" in raw,
        "ids": row["ids"],
        "skyrl": {"results": [bool(x) for x in sky["results"]], "errors": sky["errors"], "reward": sky["reward"],
                  "infra": sky["infra_error"], "action_empty": not sky["action"]},
        "tc": {"results": tc["results"], "gate": tc["gate_passed"], "candidate_empty": not tc["candidate"]},
        "rep": {"results": rep["results"], "extraction_failure": rep["extraction_failure"], "all_other": alt},
        "flips": flips,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []
    for path in sorted(glob.glob(os.path.join(PANEL, "*", "*.jsonl"))):
        folder = os.path.basename(os.path.dirname(path))
        run = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append((folder, run, line))
    if os.environ.get("LIMIT"):
        items = items[:: max(1, len(items) // int(os.environ["LIMIT"]))]
    t0 = time.time()
    n = 0
    with mp.Pool(int(os.environ.get("WORKERS", "12")), initializer=_init) as pool, \
            open(OUT, "w", encoding="utf-8", newline="\n") as out:
        for res in pool.imap(grade_one, items, chunksize=20):
            out.write(json.dumps(res, ensure_ascii=False) + "\n")
            n += 1
            if n % 2000 == 0:
                print(f"{n}/{len(items)} {time.time() - t0:.0f}s", flush=True)
    print(f"done {n} responses in {time.time() - t0:.0f}s -> {OUT}", flush=True)


if __name__ == "__main__":
    import logging

    logging.disable(logging.ERROR)
    main()
