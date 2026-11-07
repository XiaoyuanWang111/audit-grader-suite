"""Private checks for cases/toymath-extract. Part of the keys; never give this to an auditor.

The oracle implements the TASK.md scoring rule with one switch per planted defect and one per reading of the
ambiguity. The script checks that
  * the grader equals the oracle with every defect on (reading 1), on the panel and on a fuzz corpus;
  * the reference equals the oracle with every defect off (reading 2), on the panel and on the fuzz corpus;
and prints the panel tables, the per-defect verdict changes and the counterexample verdicts used in the key.
"""

import sys as _sys

_sys.dont_write_bytecode = True
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import tempfile
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(HERE, "..", "..", "cases", "toymath-extract"))
PY = sys.executable

ANSWER_LINE = re.compile(r"^\s*Answer:(.*)$")
NUM = re.compile(r"-?\d+(?:\.\d+)?")
ALL_ON = {"M1": True, "M2": True, "M3": True}
ALL_OFF = {"M1": False, "M2": False, "M3": False}


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def oracle_answer(text, sw, reading):
    rest = None
    for line in text.splitlines():
        m = ANSWER_LINE.match(line)
        if m:
            rest = m.group(1)
    if rest is None:
        return None
    if not sw["M1"]:
        rest = rest.replace(",", "")
    if reading == 1:
        m = NUM.search(rest)
        return None if m is None else Decimal(m.group(0))
    s = rest.strip()
    return Decimal(s) if NUM.fullmatch(s) else None


def oracle_verdict(text, ref, sw, reading):
    a = oracle_answer(text, sw, reading)
    if a is None:
        return "no_answer", None
    tol = Decimal("0.01") * (max(Decimal(1), abs(ref)) if sw["M2"] else 1)
    return ("correct" if abs(a - ref) <= tol else "incorrect"), a


def oracle_scores(rows, n_problems, sw):
    out = {}
    for model in sorted({r["model"] for r in rows}):
        mine = [r for r in rows if r["model"] == model]
        correct = sum(r["verdict"] == "correct" for r in mine)
        denom = sum(r["verdict"] != "no_answer" for r in mine) if sw["M3"] else n_problems
        out[model] = round(100.0 * correct / denom, 1) if denom else 0.0
    return out


def run_oracle(problems, responses, sw, reading):
    refs = {p["problem_id"]: Decimal(p["answer"]) for p in problems}
    rows = []
    for r in responses:
        v, a = oracle_verdict(r["response"], refs[r["problem_id"]], sw, reading)
        rows.append({"id": r["id"], "model": r["model"], "verdict": v, "extracted": None if a is None else str(a)})
    return rows


def run_grader(problems_path, responses_path):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "v.jsonl")
        p = subprocess.run(
            [
                PY,
                os.path.join(CASE, "grade.py"),
                "--problems",
                problems_path,
                "--responses",
                responses_path,
                "--out",
                out,
            ],
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            return None, p.stdout + p.stderr
        return load_jsonl(out), p.stdout


def run_reference(problems_path, responses_path):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "v.jsonl")
        p = subprocess.run(
            [PY, os.path.join(CASE, "reference", "grade_ref.py"), problems_path, responses_path, out],
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            return None, p.stdout + p.stderr
        return load_jsonl(out), p.stdout


def grader_scores(stdout):
    scores = {}
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        scores[parts[0]] = float(parts[-1])
    return scores


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def fuzz_responses(problems, n, seed):
    rng = random.Random(seed)
    pieces = ["", " ", "$", "-", "- ", "+", "about ", "USD "]
    tails = ["", ".", " dollars", " km/h", "%", ",", " (rounded)", " or 12", ",000", "0"]
    rows = []
    for i in range(n):
        p = rng.choice(problems)
        ref = Decimal(p["answer"])
        choice = rng.random()
        if choice < 0.3:
            num = str(ref + Decimal(rng.choice([0, 0, 1, -1, "0.005", "0.01", "0.02", "-0.01", 5, 10, 20])))
        elif choice < 0.6:
            num = f"{rng.randint(0, 20000):,}"
        else:
            num = str(Decimal(rng.randint(-2000, 2000)) / rng.choice([1, 10, 100]))
        line = f"Answer: {rng.choice(pieces)}{num}{rng.choice(tails)}"
        body = rng.choice(["Work.\n", "", "Answer: 1\n", "Answer: 99,999\nmore\n", "  "])
        after = rng.choice(["", "\nThanks!", "\n\n(check)", "\nAnswer:", "\nanswer: 5"])
        if rng.random() < 0.1:
            line = rng.choice(["Answer:", "Answer: none", "The answer is 5", "  Answer:   7  ", "\tAnswer: 3,5"])
        rows.append(
            {"id": f"f{i:05d}", "model": f"fz{i % 3}", "problem_id": p["problem_id"], "response": body + line + after}
        )
    return rows


def main():
    problems_path = os.path.join(CASE, "problems.jsonl")
    responses_path = os.path.join(CASE, "responses.jsonl")
    problems = load_jsonl(problems_path)
    responses = load_jsonl(responses_path)
    n_problems = len(problems)
    ok = True

    g_rows, g_out = run_grader(problems_path, responses_path)
    r_rows, r_out = run_reference(problems_path, responses_path)
    o_grader = run_oracle(problems, responses, ALL_ON, 1)
    o_contract1 = run_oracle(problems, responses, ALL_OFF, 1)
    o_contract2 = run_oracle(problems, responses, ALL_OFF, 2)

    # 1. grader == oracle(all on, reading 1); reference == oracle(all off, reading 2)
    for g, o in zip(g_rows, o_grader, strict=False):
        if (g["verdict"], g["extracted"]) != (o["verdict"], o["extracted"]):
            ok = False
            print("MISMATCH grader/oracle", g, o)
    for r, o in zip(r_rows, o_contract2, strict=False):
        rv = "correct" if o["verdict"] == "correct" else "incorrect"
        if r["verdict"] != rv:
            ok = False
            print("MISMATCH reference/oracle", r, o)
    gs = grader_scores(g_out)
    if gs != oracle_scores(o_grader, n_problems, ALL_ON):
        ok = False
        print("MISMATCH grader scores", gs, oracle_scores(o_grader, n_problems, ALL_ON))
    print("panel equality checks:", "OK" if ok else "FAILED")

    # 2. panel tables
    def passes(rows):
        return sum(r["verdict"] == "correct" for r in rows)

    n = len(responses)
    print(f"\npanel: {n} responses")
    print(f"grader passes {passes(o_grader)}/{n} = {100.0 * passes(o_grader) / n:.1f}%")
    print(f"reference passes {passes(r_rows)}/{n} = {100.0 * passes(r_rows) / n:.1f}%")
    print(f"contract (reading 1) passes {passes(o_contract1)}/{n} = {100.0 * passes(o_contract1) / n:.1f}%")
    print(f"contract (reading 2) passes {passes(o_contract2)}/{n} = {100.0 * passes(o_contract2) / n:.1f}%")
    print("per-model score: grader", gs)
    print("per-model score: reference (printed)", {l.split()[0]: float(l.split()[-1]) for l in r_out.splitlines()[1:]})
    print("per-model score: contract reading 1", oracle_scores(o_contract1, n_problems, ALL_OFF))
    print("per-model score: contract reading 2", oracle_scores(o_contract2, n_problems, ALL_OFF))

    # 3. per-defect changes: grader vs grader with that one defect fixed
    print("\nper-defect verdict changes (grader vs grader with only that defect removed):")
    for d in ["M1", "M2", "M3"]:
        sw = dict(ALL_ON, **{d: False})
        fixed = run_oracle(problems, responses, sw, 1)
        changed = [
            g["id"]
            for g, f in zip(o_grader, fixed, strict=False)
            if (g["verdict"] == "correct") != (f["verdict"] == "correct")
        ]
        extr = [g["id"] for g, f in zip(o_grader, fixed, strict=False) if g["extracted"] != f["extracted"]]
        print(f"  {d}: verdicts changed {len(changed)}/{n} {changed}; extractions changed {extr}")
        print(f"      scores with {d} fixed: {oracle_scores(fixed, n_problems, sw)}")
    diff12 = [
        a["id"]
        for a, b in zip(o_contract1, o_contract2, strict=False)
        if (a["verdict"] == "correct") != (b["verdict"] == "correct")
    ]
    print(f"  D-units: verdicts that depend on the reading {len(diff12)}/{n} {diff12}")
    no_ans = [o["id"] for o in o_grader if o["verdict"] == "no_answer"]
    print(f"  responses without an answer: {no_ans}")
    multi = [r["id"] for r in responses if sum(1 for l in r["response"].splitlines() if ANSWER_LINE.match(l)) > 1]
    after = []
    for r in responses:
        lines = r["response"].splitlines()
        idx = [i for i, l in enumerate(lines) if ANSWER_LINE.match(l)]
        if idx and any(l.strip() for l in lines[idx[-1] + 1 :]):
            after.append(r["id"])
    print(f"  trap (text after the answer line): {after}; several answer lines: {multi}")
    m2_band = []
    refs = {p["problem_id"]: Decimal(p["answer"]) for p in problems}
    for r, o in zip(responses, o_contract1, strict=False):
        if o["extracted"] is not None:
            a, ref = Decimal(o["extracted"]), refs[r["problem_id"]]
            if Decimal("0.01") < abs(a - ref) <= Decimal("0.01") * max(Decimal(1), abs(ref)):
                m2_band.append(r["id"])
    print(f"  panel answers inside the M2 band: {m2_band}")

    # 4. counterexamples
    print("\ncounterexamples (grader verdict / contract verdict, reading 1):")
    ce = [
        ("CE-M1", "p03", "1800 + 450 = 2,250 liters.\nAnswer: 2,250"),
        ("CE-M2", "p02", "18 × 27 = 490\nAnswer: 490"),
        ("CE-M2b", "p11", "Answer: 757"),
        ("CE-D", "p01", "Answer: $3.50"),
        ("CE-T", "p04", "Answer: -7\nHope this helps!"),
        ("CE-T2", "p10", "Answer: 12\nNo, 13 days.\nAnswer: 13"),
        ("CF-empty", "p06", ""),
        (
            "CF-restate",
            "p06",
            pathlib.Path(CASE, "prompt_template.txt")
            .read_text(encoding="utf-8")
            .replace("{problem}", problems[5]["problem"]),
        ),
        ("CF-repeat", "p06", "Answer: 0\n" * 3),
    ]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "ce.jsonl")
        write_jsonl(path, [{"id": c, "model": "ce", "problem_id": pid, "response": t} for c, pid, t in ce])
        g_ce, _ = run_grader(problems_path, path)
        r_ce, _ = run_reference(problems_path, path)
    for (cid, pid, text), g, r in zip(ce, g_ce, r_ce, strict=False):
        o = oracle_verdict(text, refs[pid], ALL_OFF, 1)
        o2 = oracle_verdict(text, refs[pid], ALL_OFF, 2)
        print(
            f"  {cid:<10} {pid} grader={g['verdict']:<9} extracted={g['extracted']!s:<6} "
            f"contract1={o[0]:<9} contract2={o2[0]:<9} reference={r['verdict']}"
        )

    # M3 counterexample: one model, 11 correct responses and one without an answer line
    m3 = []
    for i, p in enumerate(problems):
        text = f"Answer: {p['answer']}" if i else "I could not finish."
        m3.append({"id": f"m3-{i}", "model": "ce-m3", "problem_id": p["problem_id"], "response": text})
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "m3.jsonl")
        write_jsonl(path, m3)
        _, out = run_grader(problems_path, path)
        _, rout = run_reference(problems_path, path)
    print(
        f"  CE-M3 grader score {grader_scores(out)}; reference {rout.splitlines()[1].split()[-1]}; contract "
        f"{oracle_scores(run_oracle(problems, m3, ALL_OFF, 1), n_problems, ALL_OFF)}"
    )

    # 5. fuzz: grader == oracle(all on, reading 1), reference == oracle(all off, reading 2)
    fz = fuzz_responses(problems, 4000, seed=20261106)
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "fz.jsonl")
        write_jsonl(path, fz)
        g_fz, g_fz_out = run_grader(problems_path, path)
        r_fz, _ = run_reference(problems_path, path)
    o_fz = run_oracle(problems, fz, ALL_ON, 1)
    o2_fz = run_oracle(problems, fz, ALL_OFF, 2)
    bad_g = sum(
        (g["verdict"], g["extracted"]) != (o["verdict"], o["extracted"]) for g, o in zip(g_fz, o_fz, strict=False)
    )
    bad_r = sum(
        r["verdict"] != ("correct" if o["verdict"] == "correct" else "incorrect")
        for r, o in zip(r_fz, o2_fz, strict=False)
    )
    gfs = grader_scores(g_fz_out)
    bad_s = gfs != oracle_scores(o_fz, n_problems, ALL_ON)
    print(
        f"\nfuzz {len(fz)}: grader/oracle mismatches {bad_g}, reference/oracle mismatches {bad_r}, "
        f"score mismatch {bad_s}"
    )
    for d in ["M1", "M2"]:
        fixed = run_oracle(problems, fz, dict(ALL_ON, **{d: False}), 1)
        changed = sum(
            (a["verdict"] == "correct") != (b["verdict"] == "correct") for a, b in zip(o_fz, fixed, strict=False)
        )
        print(f"  fuzz verdicts changed by {d}: {changed}")
    if bad_g or bad_r or bad_s:
        ok = False
    print("\nALL CHECKS", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
