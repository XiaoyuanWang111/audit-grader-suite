"""Step 5: grade every stored panel response with grader A, grader B's gate and the replacement.

Writes audit/results/panel_verdicts.jsonl, one line per response:
  run, model, uuid, finish, thinking, a_reward, a_errors, a_text_empty, r_extract_fail,
  c: list of [instruction_id, A, B, R, R_fixA, R_fixB] per constraint (B is null for judged ids).
R_fixA and R_fixB are the replacement with the readings each grader follows
(results/official_readings.json): their differences from the grader are defect fixes only.
Grader A is run row by row exactly as the session calls it (final_answer_text, then
grade_instruction_following), with random.seed(0) before each row so that its random redraws are
reproducible; panel_nondeterminism.py measures how much the seed matters.
"""
import glob
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graders as G  # noqa: E402

AUDIT = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(AUDIT, "..", "case")


def load_records():
    recs = {}
    with open(os.path.join(CASE, "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
        for line in f:
            rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
            recs[rec["uuid"]] = rec
    return recs


def main():
    recs = load_records()
    official = json.load(open(os.path.join(AUDIT, "results", "official_readings.json"), encoding="utf-8"))
    out_path = os.path.join(AUDIT, "results", "panel_verdicts.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    t0 = time.time()
    n = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as out:
        for path in sorted(glob.glob(os.path.join(CASE, "panel", "*", "*.jsonl"))):
            folder = os.path.basename(os.path.dirname(path))
            run = os.path.splitext(os.path.basename(path))[0]
            thinking = folder.endswith("__thinking")
            with open(path, encoding="utf-8") as f:
                for line in f:
                    p = json.loads(line)
                    rec = recs[p["uuid"]]
                    raw = p["raw_response"]
                    random.seed(0)
                    a_text = G.final_answer_text(raw)
                    a_reward, a_detail = G.grade_instruction_following(a_text, rec)
                    b_text = G.answer_text_b(raw)
                    r_text = G.R.extract(raw, thinking)
                    cons = []
                    for j, (iid, kw) in enumerate(zip(rec["instruction_id_list"], rec["kwargs"])):
                        b, _ = G.check_b(iid, kw, b_text)
                        if r_text is None:
                            r = ra = rb = False
                        else:
                            r = G.check_r(iid, kw, r_text)
                            ra = G.check_r(iid, kw, r_text, official["A"].get(iid, {}))
                            rb = G.check_r(iid, kw, r_text, official["B"].get(iid, {}))
                        cons.append([iid, a_detail["follow_instruction_list"][j], b, r, ra, rb])
                    out.write(json.dumps({
                        "folder": folder, "run": run, "uuid": p["uuid"], "finish": p["finish_reason"],
                        "thinking": thinking, "a_reward": a_reward,
                        "a_errors": [e for e in a_detail["instruction_errors"] if e],
                        "a_text_empty": not a_text.strip(), "b_text_empty": not b_text.strip(),
                        "r_extract_fail": r_text is None, "c": cons}, ensure_ascii=False) + "\n")
                    n += 1
                    if n % 2000 == 0:
                        print(n, round(time.time() - t0), "s", flush=True)
    print("done", n, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
