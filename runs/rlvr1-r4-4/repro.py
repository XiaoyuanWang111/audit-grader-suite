"""Reproduce a counterexample from AUDIT.md.

Usage (from <W>/case, with NLTK_DATA and PYTHONDONTWRITEBYTECODE set):
  ../.venv/Scripts/python.exe ../audit/repro.py <fixture-id>          a hand-written fixture
  ../.venv/Scripts/python.exe ../audit/repro.py <id> '<kwargs JSON>' '<response JSON string>'
  ../.venv/Scripts/python.exe ../audit/repro.py G1 | G2 | G3          pipeline findings

Prints the exact input (JSON), the contract label (fixtures only), and the verdicts of grader A
(NVIDIA checker as SkyRL runs it), grader B (verifyit check of the task-curation gate; "n/a" for the
four ids the gate leaves to the LLM judge) and R (the replacement, proposed readings).
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tests"))
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
import harness as H  # noqa: E402
from contract_grader import graded_text  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402


def verdicts(iid, kw, resp):
    random.seed(0)
    a, a_err = H.a_check(iid, kw, resp)
    if iid in H.SEMANTIC:
        b = "n/a (judged by the LLM)"
    else:
        b = "pass" if H.b_check(iid, kw, resp)[0] else "fail"
    r = "pass" if H.r_check(iid, kw, resp) else "fail"
    return ("pass" if a else "fail") + (f" (error: {a_err})" if a_err else ""), b, r


def main(argv):
    if argv[0] == "G1":
        raw = "Okay, the user wants a quote about teaching. Let me think about which quote fits best and"
        row = {"instruction_id_list": ["keywords:existence"], "kwargs": [{"keywords": ["quote", "teaching"]}]}
        print("raw response (Qwen3-Thinking, cut by the token limit, no </think>):", json.dumps(raw))
        print("row:", json.dumps(row))
        print("A reward:", H.a_row(raw, row)[0], "| B gate passes:", H.b_gate(raw, row)[0],
              "| contract: extraction failure, graded text =", graded_text(raw, reasoning_model=True))
        return
    if argv[0] == "G2":
        row = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
               "kwargs": [{"num_paragraphs": 3, "nth_paragraph": 4, "first_word": "crash"}]}
        resp = "A.\n\nB.\n\nCrash."
        out = []
        for seed in range(10):
            random.seed(seed)
            out.append(H.a_row(resp, row)[0])
        print("row:", json.dumps(row), "response:", json.dumps(resp))
        print("A reward for random.seed(0..9):", out, "| contract: fail (paragraph 4 of 3 cannot exist)")
        return
    if argv[0] == "G3":
        row = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "limit"}]}
        reward, detail = H.a_row("", row)
        print("row:", json.dumps(row), "response: \"\"")
        print("A reward:", reward, "| instruction_errors:", detail["instruction_errors"],
              "| NemotronTaskSession turns this into outcome INFRA_ERROR, reward 0.0")
        return
    if len(argv) == 1:
        fx = next((f for f in FIXTURES if f["id"] == argv[0]), None)
        if fx is None:
            sys.exit(f"unknown fixture id {argv[0]}")
        iid, kw, resp = fx["instruction_id"], fx["kwargs"], fx["response"]
        label = fx["label"] + (f" (proposed reading of {', '.join(fx['decisions'])})" if fx["decisions"] else "")
    else:
        iid, kw, resp = argv[0], json.loads(argv[1]), json.loads(argv[2])
        label = "(not a fixture)"
    a, b, r = verdicts(iid, kw, resp)
    print(f"instruction_id: {iid}\nkwargs: {json.dumps(kw, ensure_ascii=False)}\nresponse: {json.dumps(resp, ensure_ascii=False)}")
    print(f"contract label: {label}\nA (SkyRL/NVIDIA): {a}\nB (verifyit gate): {b}\nR (replacement): {r}")


if __name__ == "__main__":
    main(sys.argv[1:])
