"""Run the reference's real CLI (case/reference/IFBench/run_eval.py) on one stored
run and compare its per-prompt outputs with the in-process replica in
ref_runner.run_file. Output files go to audit/work/ref_cli/.

Usage: python audit/scripts/check_ref_cli.py <folder> <run>
"""
import json
import os
import subprocess
import sys

import common
import ref_runner

folder, run = sys.argv[1], sys.argv[2]
out = common.W / "audit" / "work" / "ref_cli"
out.mkdir(parents=True, exist_ok=True)
lines = [json.loads(x) for x in (common.CASE / "panel" / folder / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
resp_file = out / f"{folder}__{run}-responses.jsonl"
resp_file.write_text("".join(json.dumps({"prompt": r["prompt"], "response": r["response"]}) + "\n" for r in lines),
                     encoding="utf-8", newline="\n")
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
cmd = [sys.executable, str(common.CASE / "reference" / "IFBench" / "run_eval.py"),
       "--input_data", str(common.CASE / "reference" / "IFBench" / "ifbench" / "data" / "IFBench_test.jsonl"),
       "--input_response_data", str(resp_file), "--output_dir", str(out)]
p = subprocess.run(cmd, cwd=str(common.CASE / "reference" / "IFBench"), env=env, capture_output=True, text=True, encoding="utf-8")
print("run_eval exit code", p.returncode)
if p.returncode:
    print(p.stderr[-1500:])
    sys.exit(1)
strict, loose = ref_runner.run_file({r["prompt"]: r["response"] for r in lines})
for name, mine in (("eval_results_strict", strict), ("eval_results_loose", loose)):
    cli = [json.loads(x) for x in (out / f"{folder}__{run}-{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    diff = sum(1 for a, b in zip(cli, mine) if a["follow_instruction_list"] != b.follow_instruction_list)
    print(name, "rows", len(cli), "rows differing from the in-process replica:", diff)
