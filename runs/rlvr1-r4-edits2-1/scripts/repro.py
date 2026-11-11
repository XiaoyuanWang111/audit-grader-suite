"""Reproduce a finding's verdicts.

From audit/ (Git Bash):
  export NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1
  ../.venv/Scripts/python.exe scripts/repro.py <fixture id>      # one fixture from tests/fixtures_data.py
  ../.venv/Scripts/python.exe scripts/repro.py F37|F38|F39|F44|G1 # pipeline findings

For a fixture it prints the exact input (Python repr), the contract label, and the verdict of the NVIDIA
checker as the SkyRL reward runs it, of the verifyit check as the task-curation gate runs it, and of the
replacement (proposed readings).
"""
import logging
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
logging.disable(logging.CRITICAL)
import absl.logging  # noqa: E402

absl.logging.set_verbosity(absl.logging.FATAL)
import contracts_grader as C  # noqa: E402
import pipelines as P  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402


def fixture(fid):
    fx = next((f for f in FIXTURES if f["id"] == fid), None)
    if fx is None:
        sys.exit(f"unknown fixture {fid}")
    print(f"check={fx['check']} kwargs={fx['kwargs']}")
    print(f"response={fx['response']!r}")
    print(f"contract label: {'pass' if fx['label'] else 'fail'} ({fx['kind']} {fx['ref']})")
    nv, err = P.nvidia_check(fx["check"], fx["kwargs"], fx["response"])
    print(f"NVIDIA/SkyRL: {'pass' if nv else 'fail'}" + (f" (exception {err})" if err else ""))
    if fx["check"] in P.SEMANTIC:
        print("verifyit gate: not run (the LLM judge grades this id)")
    else:
        vi, err = P.verifyit_check(fx["check"], fx["kwargs"], fx["response"])
        print(f"verifyit gate: {'pass' if vi else 'fail'}" + (f" (exception {err})" if err else ""))
    print(f"replacement: {'pass' if C.check(fx['check'], fx['kwargs'], fx['response']) else 'fail'}")


NEG = {"punctuation:no_comma", "punctuation:punctuation_dot", "punctuation:punctuation_exclamation",
       "keywords:forbidden_words"}


def negative_row():
    rows = P.load_rows()
    return next(r for r in rows.values() if set(r["instruction_id_list"]) <= NEG)


def main(arg):
    if arg == "F37":
        rec = negative_row()
        raw = "<think>\nThe user wants an answer without commas and dots so I will plan it"
        print(f"row uuid={rec['uuid']} ids={rec['instruction_id_list']}")
        print(f"response={raw!r}")
        r = P.skyrl_grade(raw, rec)
        g = P.verifyit_gate(raw, rec)
        print(f"SkyRL graded text={r[3]!r} reward={r[0]}; gate graded text={g[3]!r} gate passed={g[0]}")
        print("contract: extraction failure, every check fails (reward 0.0)")
    elif arg == "F38":
        raw = "The user wants an answer without commas and dots so I will plan it"
        print(f"Qwen3-4B-Thinking-2507 response cut inside its reasoning (template opened <think>): {raw!r}")
        print(f"SkyRL graded text={P.final_answer_text(raw)!r}; verifyit graded text={P.verifyit_candidate(raw)!r}")
        print(f"replacement graded text={C.graded_text(raw, reasoning_model=True)!r} (None = extraction failure)")
    elif arg == "F39":
        ok, err = P.nvidia_check("last_word:last_word_answer", {"last_word": "limit"}, "")
        print(f"last_word:last_word_answer on '': passed={ok} error={err} -> the session reports INFRA_ERROR")
    elif arg == "F44":
        rec = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
               "kwargs": [{"first_word": "hole", "nth_paragraph": 4, "num_paragraphs": 3}]}
        text = "Intro here.\n\nHole digging is fun.\n\nThird part."
        rewards = []
        for seed in range(20):
            random.seed(seed)
            rewards.append(P.grade_instruction_following(text, rec)[0])
        print(f"kwargs={rec['kwargs'][0]} response={text!r}")
        print(f"SkyRL rewards for random.seed(0..19): {rewards}")
        print("contract: paragraph 4 of a 3-paragraph answer cannot exist; every response fails")
    elif arg == "G1":
        rows = P.load_rows()
        bad = [r for r in rows.values() for iid, kw in zip(r["instruction_id_list"], r["kwargs"])
               if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]]
        print(f"{len(bad)} rows with nth_paragraph > num_paragraphs; first: uuid={bad[0]['uuid']}")
    else:
        fixture(arg)


if __name__ == "__main__":
    main(sys.argv[1])
