"""Step 6.1-6.3: draw, freeze and render the blinded review round from the held-out responses.

Run from W:  python -B audit/scripts/draw_sample.py

Population: the 24 held-out responses (audit/frozen/holdout_ids.txt). Strata:
whether the grader under audit and the replacement give different labels
(audit/panel/all_table.jsonl). Every case of both strata is drawn, because the
population is small. The seed fixes the opaque case ids and the two reviewers'
orders.

Writes under audit/frozen/:
  round1_sample.txt     the case list (case id, response id, stratum): its sha256 freezes the round
  round1_keys.jsonl     per case: response id, source model, finish_reason, stratum, each grader's verdict
  round1_cases.jsonl    per case, blinded: case id, prompt, reference answer, response
  round1_batch_A.md     reviewer A's batch (case-id order)
  round1_batch_B.md     reviewer B's batch (shuffled order)
"""
import hashlib
import json
import pathlib
import random

W = pathlib.Path(__file__).resolve().parents[2]
FROZEN = W / "audit" / "frozen"
SEED = 61111
CHECK_NAME = "ToyMath final answer"
CHECK_TEXT = (
    "1. Only the final answer is graded. The answer line is the last line of the response that begins with "
    "`Answer:` (whitespace before it is allowed, and the match is case-sensitive; lines are split as Python's "
    "`str.splitlines` splits them). Lines after the answer line are ignored.\n"
    "2. The answer is the number given on the answer line. A number is an optional `-` (hyphen-minus), then "
    "digits, then optionally a decimal point and more digits. Commas in the number are ignored, so `12,500` and "
    "`12500` are the same number.\n"
    "3. A response with no answer line, or with no number on its answer line, is incorrect.\n"
    "4. A response is correct when its answer is within 0.01 of the reference answer.\n"
    "Labels: `correct`; `incorrect` (an answer line with a number that is not within 0.01); "
    "`no_answer` (no answer line, or no number on it). `incorrect` and `no_answer` both count as not correct."
)


def jl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    held = (FROZEN / "holdout_ids.txt").read_text(encoding="utf-8").split()
    table = {t["id"]: t for t in jl(W / "audit" / "panel" / "all_table.jsonl")}
    responses = {r["id"]: r for r in jl(W / "case" / "responses.jsonl")}
    problems = {p["problem_id"]: p for p in jl(W / "case" / "problems.jsonl")}
    template = (W / "case" / "prompt_template.txt").read_text(encoding="utf-8")

    strata = {"disagree": [], "agree": []}
    for rid in sorted(held):
        t = table[rid]
        strata["disagree" if t["grader"] != t["replacement"] else "agree"].append(rid)
    rng = random.Random(SEED)
    drawn = []
    for name in ("disagree", "agree"):
        drawn += [(rid, name) for rid in strata[name]]  # all of each stratum
    rng.shuffle(drawn)
    cases = [(f"C{i:02d}", rid, s) for i, (rid, s) in enumerate(drawn, start=1)]

    FROZEN.mkdir(parents=True, exist_ok=True)
    sample = "".join(f"{cid} {rid} {s}\n" for cid, rid, s in cases)
    (FROZEN / "round1_sample.txt").write_text(sample, encoding="utf-8", newline="\n")

    with open(FROZEN / "round1_keys.jsonl", "w", encoding="utf-8", newline="\n") as fk, \
            open(FROZEN / "round1_cases.jsonl", "w", encoding="utf-8", newline="\n") as fc:
        for cid, rid, s in cases:
            r, t = responses[rid], table[rid]
            fk.write(json.dumps({"case_id": cid, "response_id": rid, "model": r["model"],
                                 "problem_id": r["problem_id"], "finish_reason": r["finish_reason"],
                                 "stratum": s, "grader": t["grader"], "reference": t["reference"],
                                 "replacement": t["replacement"]}) + "\n")
            p = problems[r["problem_id"]]
            fc.write(json.dumps({"case_id": cid, "prompt": template.replace("{problem}", p["problem"]),
                                 "reference_answer": p["answer"], "response": r["response"]},
                                ensure_ascii=False) + "\n")

    blinded = {c["case_id"]: c for c in jl(FROZEN / "round1_cases.jsonl")}
    order_a = [cid for cid, _, _ in cases]
    order_b = list(order_a)
    random.Random(SEED + 1).shuffle(order_b)
    for name, order in (("A", order_a), ("B", order_b)):
        out = [f"# ToyMath blinded review, round 1, batch {name}\n",
               "Each case below starts with a `## CASE <id>` heading. `REQUIREMENT TO JUDGE` gives the check's name "
               "and its text. `PROMPT` is the exact text the model saw, and `REFERENCE ANSWER` is the answer to "
               "judge against. The response is everything between the line `<<<RESPONSE BEGIN>>>` and the line "
               "`<<<RESPONSE END>>>`, exactly as stored: the newline after the begin marker and the newline "
               "before the end marker are delimiters, not part of the response. Leading and trailing whitespace "
               "inside the markers belongs to the response. Some characters (other line breaks, unusual spaces) "
               "may not display: print the exact response with the helper "
               "`python -I audit/frozen/show_case.py <case id>`.\n"]
        for cid in order:
            c = blinded[cid]
            out.append(f"\n## CASE {cid}\n\nREQUIREMENT TO JUDGE: {CHECK_NAME}\n\n{CHECK_TEXT}\n\n"
                       f"PROMPT:\n\n````text\n{c['prompt']}\n````\n\nREFERENCE ANSWER: {c['reference_answer']}\n\n"
                       f"<<<RESPONSE BEGIN>>>\n{c['response']}\n<<<RESPONSE END>>>\n")
        (FROZEN / f"round1_batch_{name}.md").write_text("".join(out), encoding="utf-8", newline="\n")

    print(f"seed {SEED}; population {len(held)} held-out responses")
    for name in ("disagree", "agree"):
        print(f"  stratum {name}: population {len(strata[name])}, drawn {len(strata[name])}: {' '.join(strata[name])}")
    print("batch B order:", " ".join(order_b))
    for f in ("round1_sample.txt", "round1_keys.jsonl", "round1_cases.jsonl", "round1_batch_A.md", "round1_batch_B.md"):
        print(hashlib.sha256((FROZEN / f).read_bytes()).hexdigest(), f"audit/frozen/{f}")


if __name__ == "__main__":
    main()
