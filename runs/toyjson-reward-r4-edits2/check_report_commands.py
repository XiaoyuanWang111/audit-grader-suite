"""Run every command that audit/AUDIT.md gives and check that it prints what the report says.

    python -B audit/check_report_commands.py

Run from the audit's working directory W. Exits 1 if any check fails.
"""

import os
import re
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = [sys.executable, "-B"]
G = PY + ["case/reward.py", "--responses"]
R = PY + ["audit/replacement_reward.py", "--responses"]
CX = "audit/counterexamples/"

# (label, argv, expected exit code or None, substrings that must appear, substrings that must not appear)
CHECKS = [
    ("tests", PY + ["-m", "unittest", "discover", "-s", "audit/tests"], 0,
     ["Ran 390 tests", "OK (expected failures=32)"], []),
    ("pins", PY + ["audit/pin_inputs.py"], 0, ['"all_match_manifest": true'], []),
    ("grader on stored rollouts", PY + ["case/reward.py"], 0,
     ["step-0000          12   0.756     5", "step-0200          12   0.971    10",
      "step-0400          12   0.979    11", "step-0600          12   1.000    12"], []),
    ("replacement proposed on stored rollouts", PY + ["audit/replacement_reward.py"], 0,
     ["step-0000          12   0.584     2", "step-0200          12   0.929     7",
      "step-0400          12   0.896    10", "step-0600          12   0.726     6"], []),
    ("replacement fixes_only on stored rollouts", PY + ["audit/replacement_reward.py", "--mode", "fixes_only"], 0,
     ["step-0200          12   0.960     9", "step-0600          12   0.726     6"], []),
    ("panel", PY + ["audit/panel.py"], 0,
     ["all          48   0.926   0.791   0.784   38/27/25", "+0.135 [+0.050, +0.237]", "+0.143 [+0.058, +0.245]",
      "step-0600    12   1.000   0.726   0.726   12/6/6     +0.274 [+0.045, +0.521]",
      '"rollouts_rewarded_above_contract": 11', '"rollouts_rewarded_above_contract": 13',
      '"share_of_grader_reward_mass_contradicted": 0.1457', '"share_of_grader_reward_mass_contradicted": 0.1541'],
     []),
    ("classify", PY + ["audit/classify.py"], 0, ["cases 8150, unexplained 0"], []),
    ("stress", PY + ["audit/stress.py"], 0,
     ["random text                grader={'AttributeError': 370} replacement={}",
      "random order object        grader={'RecursionError': 399, 'Overflow': 117, 'ValueError': 258} replacement={}",
      "numbered label before each line                           forbidden    48/48        0/48"], []),
    ("F1 grader", G + [CX + "F1.jsonl"], 0, ["F1                  1   1.000     1"], []),
    ("F1 contract", R + [CX + "F1.jsonl"], 0, ["F1                  1   0.000     0"], []),
    ("F2 grader", G + [CX + "F2.jsonl"], 0, ["F2                  1   1.000     1"], []),
    ("F2 contract", R + [CX + "F2.jsonl"], 0, ["F2                  1   0.875     0"], []),
    ("F3 grader", G + [CX + "F3.jsonl"], 1, ["AttributeError: 'list' object has no attribute 'get'"], ["checkpoint"]),
    ("F3 contract", R + [CX + "F3.jsonl"], 0, ["F3                  1   0.000     0"], []),
    ("F4a grader", G + [CX + "F4a.jsonl"], 1,
     ["ValueError: Exceeds the limit (4300 digits) for integer string conversion"], ["checkpoint"]),
    ("F4a contract", R + [CX + "F4a.jsonl"], 0, ["F4a                 1   0.000     0"], []),
    ("F4b grader", G + [CX + "F4b.jsonl"], 1,
     ["RecursionError: maximum recursion depth exceeded while decoding a JSON array"], ["checkpoint"]),
    ("F4b contract", R + [CX + "F4b.jsonl"], 0, ["F4b                 1   0.000     0"], []),
    ("F5 grader", G + [CX + "F5.jsonl"], 1, ["decimal.Overflow: [<class 'decimal.Overflow'>]"], ["checkpoint"]),
    ("F5 contract", R + [CX + "F5.jsonl"], 0, ["F5                  1   0.750     0"], []),
    ("F6 grader", G + [CX + "F6.jsonl"], 0, ["F6                  1   1.000     1"], []),
    ("F6 contract", R + [CX + "F6.jsonl"], 0, ["F6                  1   0.750     0"], []),
    ("G1 grader, limit off", PY + ["-X", "int_max_str_digits=0", "case/reward.py", "--responses", CX + "F4a.jsonl"],
     0, ["F4a                 1   0.900     0"], []),
    ("G2", PY + ["audit/g2_decimal_context.py"], 0,
     ["default context (prec 28): 0.75", "caller set prec 9:         1.0"], []),
    ("G3 grader", G + [CX + "G3.jsonl"], 1, ["AttributeError: 'list' object has no attribute 'get'"], ["checkpoint"]),
    ("G3 contract", R + [CX + "G3.jsonl"], 0, ["G3                  3   0.667     2"], []),
    ("D-qty-decimal grader", G + [CX + "D-qty-decimal.jsonl"], 0, ["D-qty-decimal        1   1.000     1"], []),
    ("D-qty-decimal proposed", R + [CX + "D-qty-decimal.jsonl"], 0, ["D-qty-decimal        1   0.750     0"], []),
    ("D-crlf grader", G + [CX + "D-crlf.jsonl"], 0, ["D-crlf              1   0.000     0"], []),
    ("D-crlf proposed", R + [CX + "D-crlf.jsonl"], 0, ["D-crlf              1   1.000     1"], []),
]


def main():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONINTMAXSTRDIGITS"}
    failed = 0
    for label, argv, code, must, must_not in CHECKS:
        p = subprocess.run(argv, cwd=W, capture_output=True, text=True, env=env)
        out = p.stdout + p.stderr
        problems = []
        if code is not None and p.returncode != code:
            problems.append(f"exit {p.returncode} != {code}")
        problems += [f"missing: {s!r}" for s in must if s not in out]
        problems += [f"unexpected: {s!r}" for s in must_not if re.search(re.escape(s), p.stdout)]
        print(("FAIL " if problems else "ok   ") + label + ("" if not problems else "  " + "; ".join(problems)))
        failed += bool(problems)
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
