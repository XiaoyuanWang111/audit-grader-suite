"""Reproduce one verdict of each grader on one constraint.

Usage (Git Bash, from audit/):
  NLTK_DATA=../case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 ../.venv/Scripts/python.exe repro.py \
      <instruction_id> '<kwargs as JSON>' '<response as a JSON string>' [--reasoning] [--prompt '<JSON string>']

The response is passed through each pipeline's own extraction (SkyRL: final_answer_text;
task curation: grade_judge._answer_text with strip_reasoning=True; contract: text after the
last </think> for a reasoning model, else the whole response). Prints one line:
  skyrl=<pass|fail|EXCEPTION ...> task_curation=<pass|fail|judged> contract=<pass|fail>
"""

import json
import logging
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
logging.disable(logging.ERROR)

import harness as h  # noqa: E402


def main(argv):
    iid, kw, resp = argv[1], json.loads(argv[2]), json.loads(argv[3])
    reasoning = "--reasoning" in argv
    prompt = json.loads(argv[argv.index("--prompt") + 1]) if "--prompt" in argv else ""
    sky = h.skyrl_grade(resp, [iid], [kw])
    if sky["errors"][0]:
        s = "EXCEPTION " + sky["errors"][0] + " (row reward 0.0, INFRA_ERROR)"
    else:
        s = "pass" if sky["results"][0] else "fail"
    tc = h.tc_gate(resp, [iid], [kw])["results"][0]
    t = "judged" if tc is None else ("pass" if tc else "fail")
    c = h.contract_grade(resp, [iid], [kw], prompt, reasoning)
    k = "pass" if c["results"][0] else "fail"
    print(f"skyrl={s} task_curation={t} contract={k}")


if __name__ == "__main__":
    main(sys.argv)
