"""Step 4: run the reference's whole pipeline (run_eval.py: reading, strict, loose,
aggregation and report) on stored panel runs, and compare its prompt-level accuracies with
the per-response reference verdicts used in step 5.

For each chosen run file, writes a responses JSONL ({"prompt", "response"}) under
audit/work/ref_pipeline/, runs the verbatim copy of run_eval.py with the reference's own
data file, and parses the printed "prompt-level" accuracies.
Run from W: .venv/Scripts/python.exe audit/scripts/s4_reference_pipeline.py
"""
import json
import os
import re
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(W, "audit", "work", "pkgs", "reference")
OUT = os.path.join(W, "audit", "work", "ref_pipeline")
RUNS = [("marin-community__marin-8b-instruct", "greedy"), ("Qwen__Qwen3-8B__thinking", "greedy"),
        ("allenai__OLMo-2-1124-13B-Instruct", "sample0")]
os.makedirs(OUT, exist_ok=True)
stats = json.load(open(os.path.join(W, "audit", "work", "panel_stats_all.json")))
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", NLTK_DATA=os.path.join(W, "case", "deps", "nltk_data"),
           PYTHONPATH=REF, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")  # run_eval opens files with the locale encoding
ok = True
for cfg, run in RUNS:
    resp_path = os.path.join(OUT, f"{cfg}__{run}-responses.jsonl")
    with open(resp_path, "w", encoding="utf-8", newline="\n") as f:
        for line in open(os.path.join(W, "case", "panel", cfg, run + ".jsonl"), encoding="utf-8"):
            rec = json.loads(line)
            f.write(json.dumps({"prompt": rec["prompt"], "response": rec["response"]}, ensure_ascii=False) + "\n")
    p = subprocess.run([os.path.join(W, ".venv", "Scripts", "python.exe"), os.path.join(REF, "run_eval.py"),
                        "--input_data=" + os.path.join(REF, "ifbench", "data", "IFBench_test.jsonl"),
                        "--input_response_data=" + resp_path, "--output_dir=" + OUT],
                       cwd=REF, env=env, capture_output=True, text=True, encoding="utf-8")
    acc = re.findall(r"^prompt-level: ([0-9.]+)", p.stdout, re.M)
    inst = re.findall(r"^instruction-level: ([0-9.]+)", p.stdout, re.M)
    if len(acc) != 2:
        print("FAILED", cfg, run, p.stderr[-800:])
        ok = False
        continue
    mine = stats["runs"][f"{cfg}/{run}"]
    print(f"{cfg}/{run}: run_eval strict {float(acc[0]):.4f} loose {float(acc[1]):.4f} | step-5 reference strict "
          f"{mine['prompt_rs']:.4f} loose {mine['prompt_rl']:.4f} | instruction-level strict {float(inst[0]):.4f} vs {mine['inst_rs']:.4f}")
    ok &= abs(float(acc[0]) - mine["prompt_rs"]) < 1e-9 and abs(float(acc[1]) - mine["prompt_rl"]) < 1e-9
print("match" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
