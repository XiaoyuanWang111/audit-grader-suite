"""Fuzz the reply parser, the judge-prompt renderer and the whole per-row path of each ToyQA pipeline.

Counts depend on the generators below, so they are reported as counts, not rates. An exception is counted as a
grading failure, apart from verdict mismatches.

    python -I audit/scripts/fuzz.py            # writes audit/work/fuzz_summary.json
"""

import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import (GRADER, QUESTIONS, REFERENCE, WORK, contract_grade, contract_parse,  # noqa: E402
                             contract_prompt)

SEED = 1106
N = 20000
LINE_BREAKS = ["\n", "\r\n", "\r", " ", " ", "\x0b", "\x0c", "\x1c", "\x85"]
TOKENS = ["A", "B", "C", "CORRECT", "INCORRECT", "NOT_ATTEMPTED", "Answer:", "Grade:", "The", "grade", "is", "**",
          "(", ")", ".", ":", " ", "\n", "é", "1", "x", "Based", "on", "A1", "_", "a", "Ｂ", "٣"]
BROAD = [chr(c) for c in list(range(32, 127)) + [0xE9, 0xC9, 0x2028, 0xFF21, 0x0663, 0x4E2D, 0x1F600, 0x0301]]


def reply_tokens(rng):
    return "".join(rng.choice(TOKENS) for _ in range(rng.randint(0, 10)))


def reply_chars(rng):
    return "".join(rng.choice(BROAD) for _ in range(rng.randint(0, 24)))


def graded_text(rng):
    if rng.random() < 0.05:
        return ""
    parts = []
    for _ in range(rng.randint(1, 60)):
        r = rng.random()
        parts.append(rng.choice(LINE_BREAKS) if r < 0.04 else rng.choice(BROAD) if r < 0.3 else
                     rng.choice(["Canberra", "the", "answer", "is", " ", "{target}", "{", "}", "I don't know"]))
    return "".join(parts).strip()


def response(rng):
    parts = []
    for _ in range(rng.randint(0, 8)):
        parts.append(rng.choice(["<think>", "</think>", " ", "\n", "Canberra", "maybe", "Sydney", " ",
                                 "I am not sure", "Final answer:\n", "{question}"]))
    return "".join(parts)


class StubJudge:
    def __call__(self, prompt, call):
        return "A"


def fuzz_parser(impl, rng, gen):
    mismatch, kinds, exceptions, example = 0, Counter(), Counter(), {}
    for _ in range(N):
        reply = gen(rng)
        want = contract_parse(reply)
        try:
            got = impl.parse(reply)
        except Exception as e:  # noqa: BLE001
            exceptions[type(e).__name__] += 1
            continue
        if got != want:
            mismatch += 1
            kind = ("grade where the contract has none" if want is None else
                    "no grade where the contract has one" if got is None else "a different letter")
            kinds[kind] += 1
            if kind not in example or len(reply) < len(example[kind][0]):
                example[kind] = (reply, got, want)
    return {"cases": N, "mismatches": mismatch, "kinds": dict(kinds), "exceptions": dict(exceptions),
            "shortest": {k: {"reply": v[0], "impl": v[1], "contract": v[2]} for k, v in example.items()}}


def fuzz_renderer(impl, rng):
    mismatch, exceptions, example, n_empty = 0, Counter(), {}, 0
    q_ids = sorted(QUESTIONS)
    for _ in range(N):
        q = QUESTIONS[rng.choice(q_ids)]
        text = graded_text(rng)
        n_empty += text == ""
        try:
            got = impl.render(q, text)
        except Exception as e:  # noqa: BLE001
            exceptions[type(e).__name__] += 1
            if "exception" not in example or len(text) < len(example["exception"]):
                example["exception"] = text
            continue
        if got != contract_prompt(q, text):
            mismatch += 1
            if "mismatch" not in example or len(text) < len(example["mismatch"]):
                example["mismatch"] = text
    return {"cases": N, "empty_texts": n_empty, "mismatches": mismatch, "exceptions": dict(exceptions),
            "shortest": example}


def fuzz_rows(impl, rng):
    mismatch, exceptions, labels, example = 0, Counter(), Counter(), {}
    q_ids = sorted(QUESTIONS)
    for _ in range(N):
        q = QUESTIONS[rng.choice(q_ids)]
        text = response(rng)
        want = contract_grade(StubJudge(), q, text)
        try:
            label, calls = impl.label(StubJudge(), q, text)
        except Exception as e:  # noqa: BLE001
            exceptions[type(e).__name__] += 1
            if "exception" not in example or len(text) < len(example["exception"]):
                example["exception"] = text
            continue
        if (label, calls) != (want["label"], want["judge_calls"]):
            mismatch += 1
            labels[f"{want['label']} -> {label}"] += 1
            key = f"{want['label']} -> {label}"
            if key not in example or len(text) < len(example[key]):
                example[key] = text
    return {"cases": N, "label_mismatches": mismatch, "by_kind": dict(labels), "exceptions": dict(exceptions),
            "shortest": example}


def main():
    summary = {}
    for impl in (GRADER, REFERENCE):
        summary[impl.name] = {
            "parser_tokens": fuzz_parser(impl, random.Random(f"{SEED}:p1"), reply_tokens),
            "parser_chars": fuzz_parser(impl, random.Random(f"{SEED}:p2"), reply_chars),
            "renderer": fuzz_renderer(impl, random.Random(f"{SEED}:r")),
            "rows_stub_judge_A": fuzz_rows(impl, random.Random(f"{SEED}:rows")),
        }
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "fuzz_summary.json"
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    for name, s in summary.items():
        print(f"== {name}")
        for part, r in s.items():
            core = {k: v for k, v in r.items() if k != "shortest"}
            print(f"  {part}: {json.dumps(core, ensure_ascii=True)}")
            for k, v in r.get("shortest", {}).items():
                print(f"    shortest [{k}]: {json.dumps(v, ensure_ascii=True)[:160]}")
    print(f"wrote {out.relative_to(WORK.parents[1])}")


if __name__ == "__main__":
    main()
