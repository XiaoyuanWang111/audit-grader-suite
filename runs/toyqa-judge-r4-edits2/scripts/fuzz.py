"""Step 4 fuzzing of the deterministic stages: the reply parser and the judge-prompt renderer.

Usage (from W):  python -B audit/scripts/fuzz.py [N]
Counts depend on this generator's input distribution; report them as counts, not rates.
"""
import random
import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import Scripted, grader, predicted_in, questions, reference, replacement, template  # noqa: E402

SEED = 1110
TPL, Q = template(), questions()["q05"]
REPLY_ATOMS = ["A", "B", "C", "a", "b", "c", "1", "_", " ", ".", ":", "*", "(", ")", "\n", "\u00e9", "\uff21",
               "Grade", "CORRECT", "INCORRECT", "NOT_ATTEMPTED", "Answer", "Based", "the grade is "]
TEXT_ATOMS = ["Canberra", " ", "\n", "\r\n", "\r", "\t", "\u2028", "\u2029", "\x85", "\x0c", "\u00a0", "{", "}",
              "{target}", "<think>", "</think>", "Garc\u00eda", "e\u0301", "\U0001F600", ">>>", "<<<", "x" * 50]


def render_with(which, response):
    j = Scripted("A")
    if which == "X_literal":
        lab = replacement.grade_response(j, TPL, Q, response, {"reopened_think": "literal"})["label"]
    elif which == "G":
        lab = grader.grade_response(j, TPL, Q, response)["label"]
    elif which == "R":
        lab = reference.ToyQAGrader(j, TPL).label(Q, response)
    else:
        lab = replacement.grade_response(j, TPL, Q, response)["label"]
    return lab, (j.calls[0][0] if j.calls else None)


def main(n):
    rnd = random.Random(SEED)
    parse_diff = Counter()
    for _ in range(n):
        reply = "".join(rnd.choice(REPLY_ATOMS) for _ in range(rnd.randint(0, 8)))
        want = replacement.parse_grade(reply)
        parse_diff["G"] += grader.parse_grade(reply) != want
        parse_diff["R"] += reference.ToyQAGrader.grade_of(reply) != want
    print(f"reply parser, {n} random replies (seed {SEED}): differs from the contract parser: "
          f"grader {parse_diff['G']}, reference {parse_diff['R']}")

    rnd = random.Random(SEED + 1)
    exc, prompt_diff, label_diff = Counter(), Counter(), Counter()
    for _ in range(n):
        resp = "".join(rnd.choice(TEXT_ATOMS) for _ in range(rnd.randint(0, 12)))
        want_label, want_prompt = render_with("X", resp)
        for which in ("G", "R"):
            try:
                lab, prompt = render_with(which, resp)
            except Exception as e:  # noqa: BLE001
                exc[(which, type(e).__name__)] += 1
                continue
            label_diff[which] += lab != want_label
            prompt_diff[which] += prompt != want_prompt
            if which == "R":
                lit_label, lit_prompt = render_with("X_literal", resp)
                prompt_diff["R_vs_literal"] += (lab, prompt) != (lit_label, lit_prompt)
    print(f"renderer, {n} random responses (seed {SEED + 1}):")
    for which, name in (("G", "grader"), ("R", "reference")):
        e = {k[1]: v for k, v in exc.items() if k[0] == which}
        print(f"  {name}: exceptions {sum(e.values())} {e or ''}; prompt differs from the replacement's "
              f"{prompt_diff[which]}; label differs (scripted judge) {label_diff[which]}")
    print(f"  reference vs the replacement with D-reopened-think reading (a): {prompt_diff['R_vs_literal']} differ")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
