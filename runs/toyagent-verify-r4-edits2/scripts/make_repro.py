"""Create the minimal counterexample states that audit/AUDIT.md cites, under audit/repro/.

Usage: python -B audit/scripts/make_repro.py
"""

import json
import os
import shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repro")

STATES = {
    # F1: no answer file anywhere; only the empty out/ directory every sandbox starts with.
    "F1_no_answer": {"out/": None},
    # F2: the correct count written to /workspace/answer.txt instead of /workspace/out/answer.txt.
    "F2_root_answer": {"out/": None, "answer.txt": b"41\n"},
    # O1: U+001F (unit separator) after the count; Python's str.strip() removes it.
    "O1_unit_separator": {"out/answer.txt": b"41\x1f\n"},
    # O2: a no-break space after the count.
    "O2_nbsp": {"out/answer.txt": "41 \n".encode()},
    # O3: 5,000 leading zeros before the count.
    "O3_leading_zeros": {"out/answer.txt": b"0" * 5000 + b"41\n"},
}

F3_TRIALS = {
    "t1": {"trial_id": "t1", "task": "count-server-errors", "config": "agentx+test", "agent_status": "error",
           "agent_error": "container lost", "agent_steps": 3, "verifier_exit_code": None,
           "verifier_output": None},
}


def main():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    for name, files in STATES.items():
        base = os.path.join(ROOT, name)
        os.makedirs(base)
        for rel, content in files.items():
            p = os.path.join(base, *rel.rstrip("/").split("/"))
            if rel.endswith("/"):
                os.makedirs(p, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as f:
                    f.write(content)
    for trial, rec in F3_TRIALS.items():
        d = os.path.join(ROOT, "F3_null_trials", trial)
        os.makedirs(d)
        with open(os.path.join(d, "result.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f)
            f.write("\n")
    print("wrote", sorted(os.listdir(ROOT)))


if __name__ == "__main__":
    main()
