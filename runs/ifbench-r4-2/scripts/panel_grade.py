"""Grade every stored panel response with the grader (strict, loose), the
reference (strict, loose) and the replacement (FIX and PROPOSED profiles, strict).

Writes audit/out/panel/<folder>.tsv, one line per (run, key, instruction).
Usage: python -B audit/scripts/panel_grade.py [folder ...]   (default: all, 4 processes)
"""
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

W = Path(__file__).resolve().parents[2]
PANEL = W / "case" / "panel"
OUT = W / "audit" / "out" / "panel"


def _v(x):
    if x is None:
        return "E"
    return "1" if x else "0"


def grade_folder(folder):
    sys.path.insert(0, str(W / "audit" / "scripts"))
    sys.path.insert(0, str(W / "audit" / "replacement"))
    import harness as H
    import ifbench_fixed as RF
    rows = H.row_by_key()
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{folder}.tsv"
    t0 = time.time()
    n = 0
    with open(out_path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write("folder\trun\tkey\tidx\tiid\tfinish\tntok\tthink_open\tthink_close\tresp_len\t"
                 "g_strict\tg_loose\tr_strict\tr_loose\tx_fix\tx_prop\terr\n")
        for run_file in sorted((PANEL / folder).glob("*.jsonl")):
            run = run_file.stem
            with open(run_file, encoding="utf-8") as rf:
                for line in rf:
                    rec = json.loads(line)
                    row = rows[str(rec["key"])]
                    resp = rec["response"]
                    raw = rec.get("raw_response") or ""
                    think_open = "<think>" in raw
                    think_close = "</think>" in raw
                    errs = []
                    gs, e1 = H.grade_row(row, resp, "grader", "strict")
                    gl, e2 = H.grade_row(row, resp, "grader", "loose")
                    rs, e3 = H.grade_row(row, resp, "reference", "strict")
                    rl, e4 = H.grade_row(row, resp, "reference", "loose")
                    for tag, e in (("gs", e1), ("gl", e2), ("rs", e3), ("rl", e4)):
                        if e:
                            errs.append(f"{tag}:{e[:80]}")
                    try:
                        xf = RF.grade_row(row, resp, RF.FIX)
                    except Exception as e:  # noqa: BLE001
                        xf = None
                        errs.append(f"xf:{type(e).__name__}:{str(e)[:60]}")
                    try:
                        xp = RF.grade_row(row, resp, RF.PROPOSED)
                    except Exception as e:  # noqa: BLE001
                        xp = None
                        errs.append(f"xp:{type(e).__name__}:{str(e)[:60]}")
                    for i, iid in enumerate(row["instruction_id_list"]):
                        vals = [(gs[i] if gs else None), (gl[i] if gl else None), (rs[i] if rs else None),
                                (rl[i] if rl else None), (xf[i] if xf else None), (xp[i] if xp else None)]
                        fh.write("\t".join([folder, run, str(rec["key"]), str(i), iid, str(rec.get("finish_reason")),
                                            str(rec.get("num_tokens")), str(int(think_open)), str(int(think_close)),
                                            str(len(resp or ""))] + [_v(v) for v in vals]
                                           + [";".join(errs).replace("\t", " ").replace("\n", " ")]) + "\n")
                    n += 1
    return folder, n, round(time.time() - t0, 1)


if __name__ == "__main__":
    folders = sys.argv[1:] or sorted(p.name for p in PANEL.iterdir() if p.is_dir())
    with Pool(4) as pool:
        for folder, n, secs in pool.imap_unordered(grade_folder, folders):
            print(f"{folder}\t{n}\t{secs}s", flush=True)
    print("DONE", flush=True)
