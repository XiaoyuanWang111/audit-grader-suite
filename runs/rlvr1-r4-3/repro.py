"""Reproduce one verdict of grader A (SkyRL reward, NVIDIA checkers), grader B (verifyit gate) and the replacement.

Usage, from <W>:
  .venv/Scripts/python.exe audit/repro.py --id <fixture id from audit/fixtures.jsonl>
  .venv/Scripts/python.exe audit/repro.py <instruction_id> '<kwargs as JSON>' '<response as a JSON string>' [--thinking true|false]

Without --thinking the response is the graded text, passed to the checkers as is. With --thinking,
the response is the raw model text: grader A applies final_answer_text, grader B applies its
_answer_text, and the replacement applies the contract's extraction (true: reasoning model).
"""
import json
import os
import sys

os.environ.setdefault("NLTK_DATA", "<W>/case/deps/nltk_data")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_lib as F  # noqa: E402


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    label = None
    if argv[0] == "--id":
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures.jsonl"), encoding="utf-8") as f:
            for line in f:
                fx = json.loads(line)
                if fx["id"] == argv[1]:
                    break
            else:
                sys.exit("no fixture " + argv[1])
        iid, kw, resp, thinking, label = fx["instruction_id"], fx["kwargs"], fx["response"], fx.get("thinking"), fx["label"]
    else:
        iid, kw, resp = argv[0], json.loads(argv[1]), json.loads(argv[2])
        thinking = None
        if "--thinking" in argv:
            thinking = argv[argv.index("--thinking") + 1] == "true"
    res = F.grade_all(iid, kw, resp, thinking)
    print("instruction_id:", iid)
    print("kwargs:", json.dumps(kw, ensure_ascii=False))
    print("response:", json.dumps(resp, ensure_ascii=False))
    if thinking is not None:
        print("raw model text; reasoning model:", thinking)
    if label is not None:
        print("contract label:", label)
    print("grader A (SkyRL reward, NVIDIA checker):", "pass" if res["A"] else "fail",
          f"(exception: {res['A_error']})" if res["A_error"] else "")
    b = res["B"]
    print("grader B (verifyit gate):", "no deterministic check (judged by the LLM)" if b is None else ("pass" if b else "fail"),
          f"[{res['B_detail']}]" if b is not None else "")
    print("replacement (proposed readings):", "pass" if res["R"] else "fail")


if __name__ == "__main__":
    main(sys.argv[1:])
