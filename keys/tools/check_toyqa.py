"""Private checks for cases/toyqa-judge. Part of the keys; never give this to an auditor.

Oracle: the TASK.md pipeline with one switch per planted defect.
  J1  reply parsing takes the first capital A, B or C anywhere in the reply, also inside a word
  J2  rendering keeps only the first line of the graded text (an empty graded text raises IndexError)
  J3  a response whose reasoning never closed gets the label not_attempted instead of extraction_failure
"""

import sys as _sys

_sys.dont_write_bytecode = True
import json
import os
import random
import re
import string
import subprocess
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "cases", "toyqa-judge"))
sys.path.insert(0, CASE)
import judge_pipeline as jp
from judges import FakeJudge, RecordedJudge

PY = sys.executable
ALL_ON = {"J1": True, "J2": True, "J3": True}
ALL_OFF = {"J1": False, "J2": False, "J3": False}
STANDALONE = re.compile(r"(?<![A-Za-z0-9])([ABC])(?![A-Za-z0-9])")
GRADE_LABEL = {"A": "correct", "B": "incorrect", "C": "not_attempted"}


class Crash(Exception):
    pass


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def o_extract(response):
    if "</think>" in response:
        return response.rsplit("</think>", 1)[1].strip()
    if "<think>" in response:
        return None
    return response.strip()


def o_render(template, q, graded, sw):
    if sw["J2"]:
        lines = graded.splitlines()
        if not lines:
            raise Crash("IndexError in rendering")
        shown = lines[0][:300]
    else:
        shown = graded[:300]
    target = q["gold"] + (" (also accepted: " + ", ".join(q["aliases"]) + ")" if q["aliases"] else "")
    return template.format(question=q["question"], target=target, predicted_answer=shown)


def o_parse(reply, sw):
    if sw["J1"]:
        m = re.search(r"[ABC]", reply)
        return m.group(0) if m else None
    found = STANDALONE.findall(reply)
    return found[-1] if found else None


def o_label(judge, template, q, response, sw):
    graded = o_extract(response)
    if graded is None:
        return ("not_attempted" if sw["J3"] else "extraction_failure"), None
    prompt = o_render(template, q, graded, sw)
    for call in (1, 2):
        g = o_parse(judge(prompt, call), sw)
        if g:
            return GRADE_LABEL[g], prompt
    return "judge_error", prompt


def o_aggregate(labels_by_model, n):
    out = {}
    for m, labels in sorted(labels_by_model.items()):
        c = Counter(labels)
        acc = c["correct"] / n
        att = c["correct"] + c["incorrect"]
        cga = c["correct"] / att if att else 0.0
        f = 2 * acc * cga / (acc + cga) if acc + cga else 0.0
        out[m] = {
            "accuracy": round(100 * acc, 1),
            "cga": round(100 * cga, 1),
            "f": round(100 * f, 1),
            "na_rate": round(100 * c["not_attempted"] / n, 1),
            "counts": dict(c),
        }
    return out


def run_pipeline(responses_path, judge="recorded"):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "l.jsonl")
        p = subprocess.run(
            [PY, os.path.join(CASE, "judge_pipeline.py"), "--judge", judge, "--responses", responses_path, "--out", out],
            capture_output=True,
            text=True,
        )
        rows = load_jsonl(out) if os.path.exists(out) else None
        return rows, p.stdout, p.stderr, p.returncode


def run_reference(responses_path, judge="recorded"):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "l.jsonl")
        p = subprocess.run(
            [
                PY,
                os.path.join(CASE, "reference", "pipeline_ref.py"),
                os.path.join(CASE, "questions.jsonl"),
                responses_path,
                judge,
                out,
            ],
            capture_output=True,
            text=True,
        )
        rows = load_jsonl(out) if os.path.exists(out) else None
        return rows, p.stdout, p.stderr, p.returncode


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    questions = {q["question_id"]: q for q in load_jsonl(os.path.join(CASE, "questions.jsonl"))}
    responses = load_jsonl(os.path.join(CASE, "responses.jsonl"))
    with open(os.path.join(CASE, "judge_template.txt"), encoding="utf-8") as f:
        template = f.read()
    recorded, fake = RecordedJudge(), FakeJudge()
    n_q = len(questions)
    ok = True

    def oracle(rows, sw, judge):
        return [o_label(judge, template, questions[r["question_id"]], r["response"], sw)[0] for r in rows]

    g_rows, g_out, _g_err, _ = run_pipeline(os.path.join(CASE, "responses.jsonl"))
    r_rows, r_out, _r_err, _ = run_reference(os.path.join(CASE, "responses.jsonl"))
    o_on, o_off = oracle(responses, ALL_ON, recorded), oracle(responses, ALL_OFF, recorded)
    if [g["label"] for g in g_rows] != o_on:
        ok = False
        print("MISMATCH pipeline/oracle")
    if [r["label"] for r in r_rows] != o_off:
        ok = False
        print("MISMATCH reference/oracle")
    print("panel equality checks:", "OK" if ok else "FAILED")
    print(g_out)
    print(r_out)

    def by_model(labels):
        d = {}
        for r, l in zip(responses, labels, strict=False):
            d.setdefault(r["model"], []).append(l)
        return d

    print("aggregate, pipeline (oracle all on):", json.dumps(o_aggregate(by_model(o_on), n_q)))
    print("aggregate, contract (oracle all off):", json.dumps(o_aggregate(by_model(o_off), n_q)))
    n = len(responses)
    print(f"\nlabel shares, pipeline: {dict(Counter(o_on))}; contract: {dict(Counter(o_off))}")
    print("per-defect label changes (pipeline vs pipeline with only that defect removed):")
    for d in ["J1", "J2", "J3"]:
        fixed = oracle(responses, dict(ALL_ON, **{d: False}), recorded)
        ch = [(r["id"], a, b) for r, a, b in zip(responses, o_on, fixed, strict=False) if a != b]
        print(f"  {d}: {len(ch)}/{n} {ch}")
        print(f"      aggregate with {d} fixed: {json.dumps(o_aggregate(by_model(fixed), n_q))}")
    multi = [
        r["id"]
        for r in responses
        if o_extract(r["response"]) is not None and len(o_extract(r["response"]).splitlines()) != 1
    ]
    long_ = [
        (r["id"], len(o_extract(r["response"])))
        for r in responses
        if o_extract(r["response"]) and len(o_extract(r["response"])) > 300
    ]
    print(f"  panel graded texts that are empty or multi-line: {multi}; longer than 300 chars: {long_}")
    unclosed = [r["id"] for r in responses if o_extract(r["response"]) is None]
    print(f"  unclosed reasoning: {unclosed}")

    # flips between call 1 and call 2 (contract parser), per distinct prompt and per item
    reps = {}
    for line in load_jsonl(os.path.join(CASE, "judge_replies.jsonl")):
        reps.setdefault(line["prompt_sha256"], {})[line["call"]] = line["reply"]
    flips = [
        s[:12]
        for s, c in reps.items()
        if o_parse(c[1], ALL_OFF) and o_parse(c[2], ALL_OFF) and o_parse(c[1], ALL_OFF) != o_parse(c[2], ALL_OFF)
    ]
    no_grade = [s[:12] for s, c in reps.items() if not o_parse(c[1], ALL_OFF)]
    print(
        f"  distinct prompts {len(reps)}; call-1 vs call-2 flips {flips}; call 1 without a standalone grade {no_grade}"
    )
    j1_replies = sorted({c[1] for c in reps.values() if o_parse(c[1], ALL_ON) != o_parse(c[1], ALL_OFF)})
    print(f"  call-1 replies parsed differently by J1: {j1_replies}")

    # Counterexamples
    print("\ncounterexamples:")
    for reply in [
        "After review: B",
        "Comparing the answers: A",
        "Based on the gold target, A",
        "Cannot tell.",
        "A liver is not skin. B",
        "B",
        "Grade: A",
        "**C**",
    ]:
        print(
            f"  reply {reply!r:<32} pipeline parse={jp.parse_grade(reply)!s:<5} contract parse={o_parse(reply, ALL_OFF)}"
        )
    q01 = questions["q01"]
    for label, graded in [
        ("J2 two lines", "I am not sure.\nCanberra"),
        ("J2 correction", "Sydney.\nNo wait, Canberra."),
        ("trap 300 chars", "x" * 295 + " Canberra"),
        ("trap short", "Canberra"),
    ]:
        gp = jp.render_prompt(template, q01, graded)
        cp = o_render(template, q01, graded, ALL_OFF)
        print(
            f"  {label:<15} pipeline shows {gp.split('<<<' + chr(10))[1].split(chr(10) + '>>>')[0]!r:.60} "
            f"fake judge {fake(gp, 1)}; contract fake judge {fake(cp, 1)}"
        )
    try:
        jp.render_prompt(template, q01, "")
        print("  empty graded text: pipeline renders")
    except Exception as exc:
        print(f"  empty graded text: pipeline raises {exc.__class__.__name__}: {exc}")
    print(f"  empty graded text: contract renders, fake judge {fake(o_render(template, q01, '', ALL_OFF), 1)}")
    unc = "<think>The capital of Australia is Canberra, I am fairly sure, but let me check"
    print(
        f"  unclosed reasoning: pipeline {jp.grade_response(fake, template, q01, unc)['label']}, "
        f"contract {o_label(fake, template, q01, unc, ALL_OFF)[0]}"
    )
    for text in ["Either Canberra or Sydney.", "Canberra or maybe Sydney"]:
        print(f"  ambiguity {text!r}: fake judge (pipeline) {jp.grade_response(fake, template, q01, text)['label']}")

    # Content-free responses through the whole pipeline (fake judge), each run as its own file
    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8") as f:
        template_answer = f.read()
    cf = {
        "empty": "",
        "think-only": "<think>Let me think.</think>",
        "repeat": "Canberra\nCanberra\nCanberra",
        "restate": template_answer.replace("{question}", q01["question"]),
    }
    for name, text in cf.items():
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "cf.jsonl")
            write_jsonl(
                path,
                [
                    {"id": "cf1", "model": "cf", "question_id": "q01", "response": "Canberra"},
                    {"id": "cf2", "model": "cf", "question_id": "q01", "response": text},
                ],
            )
            g, _gout, gerr, gcode = run_pipeline(path, "fake")
            r, _, _, _ = run_reference(path, "fake")
        last_err = gerr.strip().splitlines()[-1] if gerr.strip() else ""
        print(
            f"  content-free {name:<10} pipeline exit {gcode} {last_err!r:.60} labels "
            f"{None if g is None else [x['label'] for x in g]}; reference labels {[x['label'] for x in r]}"
        )

    # Fuzz the parser, the renderer and the whole pipeline
    rng = random.Random(20261106)
    words = [
        "A",
        "B",
        "C",
        "a",
        "Answer",
        "Based",
        "Clearly",
        "grade",
        "is",
        "the",
        "After",
        "CORRECT",
        "B.",
        "(A)",
        "**B**",
        "C:",
        "AB",
        "A1",
        "1C",
        "Grade:",
        "not",
        "attempted",
        "\n",
        "Cannot",
        "OK",
    ]
    bad_parse = 0
    j1_parse = 0
    for _ in range(20000):
        reply = " ".join(rng.choice(words) for _ in range(rng.randint(0, 6)))
        if jp.parse_grade(reply) != o_parse(reply, ALL_ON):
            bad_parse += 1
        j1_parse += o_parse(reply, ALL_ON) != o_parse(reply, ALL_OFF)
    bad_render = 0
    j2_render = 0
    alphabet = string.ascii_letters + "  .,{}\n\té \r"
    for _ in range(5000):
        graded = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 400))).strip()
        if not graded:
            continue
        q = questions[rng.choice(sorted(questions))]
        try:
            a = jp.render_prompt(template, q, graded)
        except Exception as exc:
            a = "crash " + exc.__class__.__name__
        try:
            b = o_render(template, q, graded, ALL_ON)
        except Crash:
            b = "crash IndexError"
        bad_render += a != b
        j2_render += b != o_render(template, q, graded, ALL_OFF)
    fz = []
    for i in range(300):
        q = rng.choice(sorted(questions))
        base = rng.choice([r["response"] for r in responses if r["question_id"] == q])
        variant = rng.choice(
            [
                base,
                base.replace("</think>", ""),
                base + "\nMore text.",
                "I don't know.",
                "<think>x</think>" + rng.choice(["Canberra", "1648", "W", "Iron", "no idea"]),
                base.upper(),
                "Maybe " + base,
            ]
        )
        if o_extract(variant) == "":
            continue
        fz.append({"id": f"f{i:03d}", "model": f"fz{i % 2}", "question_id": q, "response": variant})
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "fz.jsonl")
        write_jsonl(path, fz)
        g, _gout, _, _ = run_pipeline(path, "fake")
        r, _, _, _ = run_reference(path, "fake")
    o1, o0 = oracle(fz, ALL_ON, fake), oracle(fz, ALL_OFF, fake)
    bad_g = sum(a["label"] != b for a, b in zip(g, o1, strict=False))
    bad_r = sum(a["label"] != b for a, b in zip(r, o0, strict=False))
    print(
        f"\nfuzz: parser mismatches {bad_parse}/20000 (J1 changes {j1_parse}); renderer mismatches "
        f"{bad_render}/5000 (J2 changes {j2_render}); pipeline (fake judge) mismatches {bad_g}/{len(fz)}, "
        f"reference mismatches {bad_r}/{len(fz)}"
    )
    for d in ["J1", "J2", "J3"]:
        fixed = oracle(fz, dict(ALL_ON, **{d: False}), fake)
        print(f"  fuzz labels changed by {d}: {sum(a != b for a, b in zip(o1, fixed, strict=False))}")
    if bad_parse or bad_render or bad_g or bad_r:
        ok = False
    print("\nALL CHECKS", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
