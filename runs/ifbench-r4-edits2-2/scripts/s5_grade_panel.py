"""Step 5: grade every stored panel response with the grader (strict and loose), the reference
(strict and loose) and the replacement (strict, proposed readings), through each one's own
harness functions. One worker per run file.

Graded text:
- grader and reference: the stored `response` field (text after the last </think>, or the
  whole completion when there is none), which is what the panel records as the graded text.
- replacement: the contract's rule: text after the last </think>; a completion that opens
  <think> and never closes it is an extraction failure and fails every check.

Output: audit/work/panel_verdicts/<config>__<run>.jsonl, one line per instruction instance:
  {cfg, run, key, i, iid, gs, gl, rs, rl, ps, finish, xfail, empty}
  verdict values: 1 pass, 0 fail, -1 exception (no verdict)
Run from W: .venv/Scripts/python.exe audit/scripts/s5_grade_panel.py [--only CONFIG/RUN ...]
"""
import json
import os
import sys
import time
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(W, "audit", "work", "panel_verdicts")


def _init():
    sys.path.insert(0, os.path.join(W, "audit", "lib"))
    os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))


def grade_file(args):
    cfg, run = args
    import copy
    import pyarrow.parquet as pq
    sys.path.insert(0, os.path.join(W, "audit", "lib"))
    import graders as G
    g = G.grader_mod()
    r = G.reference_mod()
    import ifb_replacement as rep
    rows = {x["key"]: x for x in pq.read_table(os.path.join(W, "case", "data", "train-00000-of-00001.parquet")).to_pylist()}
    path = os.path.join(W, "case", "panel", cfg, run + ".jsonl")
    out_lines = []
    t0 = time.time()
    for line in open(path, encoding="utf-8"):
        rec = json.loads(line)
        row = rows[str(rec["key"])]
        ids = list(row["instruction_id_list"])
        kws = [{k: v for k, v in kw.items() if v is not None} for kw in row["kwargs"]]
        prompt = row["prompt"]
        resp = rec["response"]
        raw = rec["raw_response"]
        xfail = ("<think>" in raw) and ("</think>" not in raw)

        def harness(mod_inp_cls, fn, kwargs_list):
            try:
                inp = mod_inp_cls(key=int(row["key"]), instruction_id_list=ids, prompt=prompt,
                                  kwargs=copy.deepcopy(kwargs_list))
                return [1 if v else 0 for v in fn(inp, {prompt: resp}).follow_instruction_list]
            except Exception:  # noqa: BLE001
                return [-1] * len(ids)
        gs = harness(g.InputExample, g.test_instruction_following_strict, kws)
        gl = harness(g.InputExample, g.test_instruction_following_loose, kws)
        rs = harness(r.InputExample, r.test_instruction_following_strict, kws)
        rl = harness(r.InputExample, r.test_instruction_following_loose, kws)
        ps = []
        for iid, kw in zip(ids, kws):
            if xfail:
                ps.append(0)
                continue
            try:
                ps.append(1 if rep.check(iid, kw, resp, prompt=prompt) else 0)
            except Exception:  # noqa: BLE001
                ps.append(-1)
        for i, iid in enumerate(ids):
            out_lines.append(json.dumps({"cfg": cfg, "run": run, "key": int(row["key"]), "i": i, "iid": iid,
                                         "gs": gs[i], "gl": gl[i], "rs": rs[i], "rl": rl[i], "ps": ps[i],
                                         "finish": rec["finish_reason"], "xfail": xfail,
                                         "empty": not resp.strip()}))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{cfg}__{run}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out_lines) + "\n")
    return cfg, run, len(out_lines), round(time.time() - t0, 1)


def main():
    jobs = []
    panel = os.path.join(W, "case", "panel")
    for cfg in sorted(os.listdir(panel)):
        if os.path.isdir(os.path.join(panel, cfg)):
            for fn in sorted(os.listdir(os.path.join(panel, cfg))):
                if fn.endswith(".jsonl"):
                    jobs.append((cfg, fn[:-6]))
    if "--only" in sys.argv:
        want = set(sys.argv[sys.argv.index("--only") + 1:])
        jobs = [j for j in jobs if f"{j[0]}/{j[1]}" in want]
    t0 = time.time()
    with Pool(int(os.environ.get("WORKERS", "16")), initializer=_init) as pool:
        for cfg, run, n, sec in pool.imap_unordered(grade_file, jobs):
            print(f"{cfg}/{run}: {n} verdict rows in {sec}s  (elapsed {time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
