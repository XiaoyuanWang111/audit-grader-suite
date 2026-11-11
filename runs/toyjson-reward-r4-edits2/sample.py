"""Step 6.1-6.3: draw, freeze and render the blinded review sample (round 1).

    python -B audit/sample.py

Population: the 48 stored rollouts. Strata: whether case/reward.py and the replacement (proposed mode) give different
rewards (from audit/panel/verdicts.jsonl). The population is small, so every rollout of both strata is sampled.
Writes audit/frozen/round1/:
    cases.jsonl        the frozen case list: case_id, prompt, reference, response (no source model, no verdicts)
    keys.jsonl         case_id -> rollout id, checkpoint (source model), stratum, grader and replacement rewards
    batch_A.md         every case, in case-id order, for reviewer A
    batch_B.md         every case, in a different seeded order, for reviewer B
    show_case.py       helper that prints a case's exact response
    reviewer_prompt.md the reviewer prompt from skill/references/reviewer-prompt.md, filled in
    sample_meta.json   seed, strata population sizes and sample sizes
"""

import json
import os
import random

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W, "audit", "frozen", "round1")
SEED = 20261111


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f if l.strip()]


def spec_text():
    text = open(os.path.join(W, "case", "TASK.md"), encoding="utf-8").read()
    start = text.index("## Reward specification")
    end = text.index("## How the reward is run")
    return text[start:end].strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    template = open(os.path.join(W, "case", "prompt_template.txt"), encoding="utf-8").read()
    order_lines = {json.loads(l)["order_id"]: l for l in read_lines(os.path.join(W, "case", "orders.jsonl"))}
    orders = {k: json.loads(v) for k, v in order_lines.items()}
    responses = [json.loads(l) for l in read_lines(os.path.join(W, "case", "responses.jsonl"))]
    verdicts = {v["id"]: v for v in map(json.loads, read_lines(os.path.join(W, "audit", "panel", "verdicts.jsonl")))}

    strata = {"disagree": [], "agree": []}
    for r in responses:
        v = verdicts[r["id"]]
        strata["disagree" if abs(v["grader"] - v["proposed"]) > 1e-9 else "agree"].append(r["id"])
    rng = random.Random(SEED)
    sample = []
    for name in ("disagree", "agree"):
        sample += strata[name]  # census: every rollout of the stratum
    rng.shuffle(sample)
    case_of = {rid: f"C{k:02d}" for k, rid in enumerate(sample, 1)}
    by_id = {r["id"]: r for r in responses}

    cases, keys = [], []
    for rid in sample:
        r = by_id[rid]
        o = orders[r["order_id"]]
        raw_ref = order_lines[r["order_id"]]
        raw_ref = raw_ref[raw_ref.index('"reference": ') + len('"reference": '):-1]  # exact text from orders.jsonl
        cases.append({"case_id": case_of[rid], "prompt": template.replace("{email}", o["email"]),
                      "reference": raw_ref, "response": r["response"]})
        v = verdicts[rid]
        keys.append({"case_id": case_of[rid], "rollout_id": rid, "checkpoint": r["checkpoint"],
                     "order_id": r["order_id"],
                     "stratum": "disagree" if abs(v["grader"] - v["proposed"]) > 1e-9 else "agree",
                     "grader": v["grader"], "fixes_only": v["fixes_only"], "proposed": v["proposed"],
                     "findings": v["findings"], "decisions": v["decisions"]})
    cases.sort(key=lambda c: c["case_id"])
    keys.sort(key=lambda k: k["case_id"])

    with open(os.path.join(OUT, "cases.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "keys.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for k in keys:
            f.write(json.dumps(k) + "\n")

    order_b = [c["case_id"] for c in cases]
    random.Random(SEED + 1).shuffle(order_b)
    spec = spec_text()
    for reviewer, order in (("A", [c["case_id"] for c in cases]), ("B", order_b)):
        by_case = {c["case_id"]: c for c in cases}
        parts = [
            f"# ToyOrders reward review, round 1, batch {reviewer}",
            "",
            "Each case below shows a case id, the prompt the policy saw, the order's reference values, and the "
            "policy's response. The response is the exact text between the line `<<<BEGIN RESPONSE Cnn>>>` and the "
            "line `<<<END RESPONSE Cnn>>>`, excluding the newline right after the BEGIN line and the newline right "
            "before the END line; leading and trailing whitespace inside the markers is part of the response. "
            "Print the exact response, with escapes, with `python -B audit/frozen/round1/show_case.py Cnn`.",
            "",
            "## REQUIREMENT TO JUDGE (the same for every case)",
            "",
            "Give the reward that the following specification assigns to the response, against the case's "
            "reference. The specification is quoted from the task's design document.",
            "",
            spec,
            "",
        ]
        for cid in order:
            c = by_case[cid]
            parts += [f"## Case {cid}", "", "PROMPT:", "", "```text", c["prompt"].rstrip("\n"), "```", "",
                      "REFERENCE (JSON):", "", "```text", c["reference"], "```", "",
                      f"<<<BEGIN RESPONSE {cid}>>>", c["response"], f"<<<END RESPONSE {cid}>>>", ""]
        with open(os.path.join(OUT, f"batch_{reviewer}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(parts))

    with open(os.path.join(OUT, "show_case.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write('''"""Print a review case's exact response (repr first, then the raw text) and its reference.

    python -B audit/frozen/round1/show_case.py C07
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8") as f:
    cases = {c["case_id"]: c for c in map(json.loads, f)}
c = cases[sys.argv[1]]
print("repr:", repr(c["response"]))
print("length:", len(c["response"]))
print("reference:", c["reference"])
print("----- raw response -----")
print(c["response"])
''')

    prompt = open(os.path.join(W, "skill", "references", "reviewer-prompt.md"), encoding="utf-8").read()
    body = prompt[prompt.index("```text\n") + len("```text\n"):prompt.index("\n```\n\nRule 5")]
    body = (body.replace("<benchmark>", "the ToyOrders RL reward")
                .replace("<helper command>", "python -B audit/frozen/round1/show_case.py <case id>"))
    body = body.replace(
        'whether the RESPONSE satisfies the single REQUIREMENT TO JUDGE',
        'which reward the single REQUIREMENT TO JUDGE assigns to the RESPONSE')
    body = body.replace(
        "unless the requirement is about that.",
        "unless the requirement is about that. Judge against the reference answer as given. Do not use your own "
        "knowledge of the facts. If the reference answer looks wrong, set verdict ambiguous and say why.")
    body = body.replace(
        '"verdict" ("pass", "fail" or "ambiguous"), "lean" ("pass" or "fail")',
        '"verdict" (the reward as a number with 4 decimals, such as 0.8750, or "ambiguous"), "lean" (the reward '
        'under the reading you find most natural, a number with 4 decimals)')
    for reviewer in ("A", "B"):
        filled = (body.replace("<batch path>", f"audit/frozen/round1/batch_{reviewer}.md")
                      .replace("<output path>", f"audit/frozen/round1/review_{reviewer}.jsonl"))
        with open(os.path.join(OUT, f"reviewer_prompt_{reviewer}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(filled + "\n")

    meta = {"seed": SEED, "population": len(responses),
            "strata": {k: {"population": len(v), "sampled": len(v)} for k, v in strata.items()},
            "reviewer_B_order_seed": SEED + 1,
            "stratum_definition": "case/reward.py reward differs from replacement_reward.py proposed mode by > 1e-9"}
    with open(os.path.join(OUT, "sample_meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=1)
        f.write("\n")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
