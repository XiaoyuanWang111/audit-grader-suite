"""Run the reference's own pipeline (run_eval.py -> evaluation_lib strict then loose, with its
prompt lookup and aggregation) on stored runs, and compare with the per-check R / RL verdicts
in audit/frozen/panel_verdicts.

Usage: python audit/scripts/run_reference_pipeline.py [run name, default greedy]
Writes response files and eval outputs under audit/work/ref_runs/ and prints, per file,
the reference's printed prompt-level accuracy and the number of verdict mismatches.
"""
import json
import os
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = os.path.join(W, ".venv", "Scripts", "python.exe")
REF = os.path.join(W, "audit", "work", "reference")
OUT = os.path.join(W, "audit", "work", "ref_runs")


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "greedy"
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ, NLTK_DATA=os.path.join(W, "case", "deps", "nltk_data"), PYTHONPATH=REF)
    total_mis = 0
    for cfg in sorted(os.listdir(os.path.join(W, "case", "panel"))):
        src = os.path.join(W, "case", "panel", cfg, run + ".jsonl")
        if not os.path.exists(src):
            continue
        name = f"{cfg}__{run}"
        resp = os.path.join(OUT, name + "-responses.jsonl")
        with open(resp, "w", encoding="utf-8", newline="\n") as f:
            for line in open(src, encoding="utf-8"):
                r = json.loads(line)
                f.write(json.dumps({"prompt": r["prompt"], "response": r["response"]}, ensure_ascii=False) + "\n")
        p = subprocess.run([PY, "-X", "utf8", "-B", "run_eval.py", "--input_data=ifbench/data/IFBench_test.jsonl",
                            f"--input_response_data={resp}", f"--output_dir={OUT}"],
                           cwd=REF, env=env, capture_output=True, text=True, encoding="utf-8")
        acc = [l for l in p.stdout.splitlines() if l.startswith("prompt-level")]
        mine = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "panel_verdicts", cfg, run + ".jsonl"), encoding="utf-8")]
        mis = 0
        for kind, key in (("strict", "R"), ("loose", "RL")):
            outs = [json.loads(l) for l in open(os.path.join(OUT, f"{name}-eval_results_{kind}.jsonl"), encoding="utf-8")]
            for o, m in zip(outs, mine):
                mis += o["follow_instruction_list"] != [i[key] is True for i in m["inst"]]
        total_mis += mis
        print(f"{name}: {acc} mismatching prompts={mis} rc={p.returncode}")
    print("total mismatching prompts", total_mis)


if __name__ == "__main__":
    main()
