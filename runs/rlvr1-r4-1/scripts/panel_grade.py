"""Step 5: grade every stored panel response with SkyRL, the curation gate and the replacement.

Per response it records: run, uuid, finish_reason, extraction status, held-out flag, and for each
constraint the SkyRL verdict and checker error, the gate verdict (None = judged), the replacement
verdict on the contract's graded text (proposed readings), and the replacement verdict on the
graders' graded text (to separate extraction from checking).

Writes audit/out/panel_verdicts.jsonl. Usage: python audit/scripts/panel_grade.py
"""
import hashlib
import json
import pathlib
import random
import sys
import time

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402

PANEL = W / "case" / "panel"
OUT = W / "audit" / "out" / "panel_verdicts.jsonl"
RUNS = [
    ("Qwen__Qwen3-4B-Instruct-2507", "greedy"),
    ("Qwen__Qwen3-4B-Instruct-2507", "greedy_repeat"),
    ("Qwen__Qwen3-4B-Instruct-2507", "sample0"),
    ("Qwen__Qwen2.5-7B-Instruct", "sample0"),
    ("allenai__OLMo-2-1124-7B-Instruct", "sample0"),
    ("Qwen__Qwen3-4B-Thinking-2507__thinking", "sample0"),
]


def uhash(u: str) -> str:
    return hashlib.sha256(u.encode()).hexdigest()


def extraction_status(raw: str, reasoning: bool) -> str:
    if reasoning:
        return "closed" if "</think>" in raw else "unclosed"
    if any(m in raw for m in ("<think>", "<thinking>", "<|start_think|>", "</think>", "</thinking>", "<|end_think|>")):
        return "marker_in_answer"
    return "none"


def main():
    rows = {harness.record_of(r)["uuid"]: r for r in harness.load_rows()}
    n = 0
    t0 = time.time()
    with open(OUT, "w", encoding="utf-8", newline="\n") as out:
        for folder, run in RUNS:
            reasoning = folder.endswith("__thinking")
            for line in open(PANEL / folder / f"{run}.jsonl", encoding="utf-8"):
                r = json.loads(line)
                row = rows[r["uuid"]]
                rec = harness.record_of(row)
                prompt = row["prompt"][0]["content"]
                raw = r["raw_response"]
                h = uhash(r["uuid"])
                random.seed(int(h[:8], 16))
                reward, sk, errs, sk_text = harness.skyrl_grade(raw, rec)
                gate, gv, gate_text = harness.curation_gate(raw, rec)
                ct = rp.graded_text(raw, reasoning)
                rr, rv = rp.grade_row(ct, rec, prompt=prompt)
                rr_g, rv_g = rp.grade_row(sk_text, rec, prompt=prompt)
                off_sk = [rp.check_official("skyrl", i, k, ct, prompt=prompt)
                          for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
                off_vi = [None if i in harness.SEMANTIC else rp.check_official("verifyit", i, k, ct, prompt=prompt)
                          for i, k in zip(rec["instruction_id_list"], rec["kwargs"])]
                out.write(json.dumps({
                    "folder": folder, "run": run, "uuid": r["uuid"], "finish": r["finish_reason"],
                    "extraction": extraction_status(raw, reasoning), "heldout": int(h[0], 16) >= 8,
                    "ids": rec["instruction_id_list"], "kwargs": rec["kwargs"],
                    "skyrl": sk, "skyrl_err": errs, "skyrl_reward": reward,
                    "gate": gv, "gate_pass": gate,
                    "repl": rv, "repl_reward": rr, "repl_on_grader_text": rv_g,
                    "off_sk": off_sk, "off_sk_reward": float(all(off_sk)), "off_vi": off_vi,
                    "graded_empty": not sk_text.strip(), "texts_differ": (ct or "") != sk_text,
                }) + "\n")
                n += 1
                if n % 2000 == 0:
                    print(n, f"{time.time() - t0:.0f}s", flush=True)
    print("graded", n, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
