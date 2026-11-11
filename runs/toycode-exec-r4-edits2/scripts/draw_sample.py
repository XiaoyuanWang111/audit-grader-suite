"""Step 6.1-6.3: draw, freeze and render the blinded-review sample from the stored panel.

Usage: python -B audit/scripts/draw_sample.py SEED
Strata: whether the replacement (proposed readings) and the grader under audit disagree. The population is 40
verdicts, so every case of both strata is drawn (census); the seed fixes the opaque ids and the two review orders.
Writes audit/frozen/: cases.jsonl (the frozen case list), keys.jsonl (source model and grader verdicts, never
shown to reviewers), responses/<case>.txt, batch_A.md, batch_B.md, show_case.py, reviewer_prompt_A.md,
reviewer_prompt_B.md, sample_meta.json.
"""

import hashlib
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AUDIT)
CASE = os.path.join(ROOT, "case")
FROZEN = os.path.join(AUDIT, "frozen")
PANEL = os.path.join(AUDIT, "panel")
NL = "\n"


def jl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def grading_rule():
    text = open(os.path.join(CASE, "TASK.md"), encoding="utf-8").read()
    start = text.index("## Grading rule")
    end = text.index("## How the grader is run")
    return text[start:end].split(NL, 1)[1].strip()


def main():
    seed = int(sys.argv[1])
    rng = random.Random(seed)
    responses = {r["id"]: r for r in jl(os.path.join(CASE, "responses.jsonl"))}
    tasks = {t["task_id"]: t for t in jl(os.path.join(CASE, "tasks.jsonl"))}
    tests = json.load(open(os.path.join(CASE, "tests.json"), encoding="utf-8"))
    template = open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8").read()
    v = {name: {r["id"]: r["verdict"] for r in jl(os.path.join(PANEL, name + ".jsonl"))}
         for name in ("grader", "reference", "replacement", "replacement_alt_palindrome_normalized")}

    ids = sorted(responses)
    strata = {"disagree": [i for i in ids if v["grader"][i] != v["replacement"][i]],
              "agree": [i for i in ids if v["grader"][i] == v["replacement"][i]]}
    drawn = {k: sorted(rng.sample(members, len(members))) for k, members in strata.items()}   # census
    sample = drawn["disagree"] + drawn["agree"]
    opaque = rng.sample(range(100, 1000), len(sample))
    case_of = {rid: f"TC{opaque[n]}" for n, rid in enumerate(sorted(sample, key=lambda _: rng.random()))}

    os.makedirs(os.path.join(FROZEN, "responses"), exist_ok=True)
    cases, keys = [], []
    for rid in sample:
        r = responses[rid]
        cid = case_of[rid]
        body = r["response"].encode("utf-8")
        with open(os.path.join(FROZEN, "responses", cid + ".txt"), "wb") as f:
            f.write(body)
        stratum = "disagree" if rid in strata["disagree"] else "agree"
        cases.append({"case_id": cid, "task_id": r["task_id"], "stratum": stratum,
                      "response_sha256": sha(body)})
        keys.append({"case_id": cid, "response_id": rid, "model": r["model"], "task_id": r["task_id"],
                     "stratum": stratum, "grader": v["grader"][rid], "reference": v["reference"][rid],
                     "replacement": v["replacement"][rid],
                     "replacement_stored_t02_test": v["replacement_alt_palindrome_normalized"][rid]})
    cases.sort(key=lambda c: c["case_id"])
    keys.sort(key=lambda c: c["case_id"])
    with open(os.path.join(FROZEN, "cases.jsonl"), "w", encoding="utf-8", newline=NL) as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True) + NL)
    with open(os.path.join(FROZEN, "keys.jsonl"), "w", encoding="utf-8", newline=NL) as f:
        for k in keys:
            f.write(json.dumps(k, sort_keys=True) + NL)

    rule = grading_rule()
    order_a = sorted(case_of.values())
    order_b = order_a[:]
    rng.shuffle(order_b)
    by_case = {c["case_id"]: c for c in cases}
    rid_of = {cid: rid for rid, cid in case_of.items()}
    for name, order in (("A", order_a), ("B", order_b)):
        out = [f"# ToyCode blinded review, batch {name}", "",
               "Each case below starts with a line `=== CASE <id> ===`. The REQUIREMENT TO JUDGE is the benchmark's "
               "grading rule followed by the task's stored tests, one JSON object per line. The PROMPT is the only "
               "message the model saw, between `<<<BEGIN PROMPT>>>` and `<<<END PROMPT>>>`. The RESPONSE is the "
               "model's complete reply, between `<<<BEGIN RESPONSE>>>` and `<<<END RESPONSE>>>`; the markers sit on "
               "their own lines, so any blank line or space just inside them belongs to the response. The exact "
               "response is also in responses/<id>.txt next to this file, and `python -B show_case.py <id>` prints "
               "it (add --repr to see every character escaped).", ""]
        for cid in order:
            r = responses[rid_of[cid]]
            t = tasks[r["task_id"]]
            out += [f"=== CASE {cid} ===", "", "REQUIREMENT TO JUDGE:", "", rule, "",
                    f"Stored tests for `{t['entry_point']}` (hidden from the model):", ""]
            out += [json.dumps(x) for x in tests[r["task_id"]]]
            out += ["", "PROMPT:", "<<<BEGIN PROMPT>>>", template.replace("{prompt}", t["prompt"]).rstrip(NL),
                    "<<<END PROMPT>>>", "", "RESPONSE:", "<<<BEGIN RESPONSE>>>", r["response"],
                    "<<<END RESPONSE>>>", ""]
        with open(os.path.join(FROZEN, f"batch_{name}.md"), "w", encoding="utf-8", newline=NL) as f:
            f.write(NL.join(out))

    with open(os.path.join(FROZEN, "show_case.py"), "w", encoding="utf-8", newline=NL) as f:
        f.write('"""Print the exact response of one case: python -B show_case.py <case_id> [--repr]."""\n'
                "import os\nimport sys\n\n"
                "path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'responses', sys.argv[1] + '.txt')\n"
                "text = open(path, 'rb').read().decode('utf-8')\n"
                "print(repr(text) if '--repr' in sys.argv[2:] else text)\n")

    prompt = open(os.path.join(AUDIT, "..", "skill", "references", "reviewer-prompt.md"), encoding="utf-8").read()
    body = prompt.split("```text", 1)[1].split("```", 1)[0].strip()
    for name in ("A", "B"):
        filled = (body.replace("<benchmark>", "ToyCode 1.0 (Python function completion graded by execution)")
                  .replace("<batch path>", f"audit/frozen/batch_{name}.md")
                  .replace("<output path>", f"audit/frozen/reviews_{name}.jsonl")
                  .replace("<helper command>", "python -B audit/frozen/show_case.py <case_id> [--repr]"))
        with open(os.path.join(FROZEN, f"reviewer_prompt_{name}.md"), "w", encoding="utf-8", newline=NL) as f:
            f.write(filled + NL)

    meta = {"seed": seed, "population": len(ids),
            "strata": {k: {"population": len(m), "drawn": len(drawn[k])} for k, m in strata.items()},
            "order_A": order_a, "order_B": order_b}
    with open(os.path.join(FROZEN, "sample_meta.json"), "w", encoding="utf-8", newline=NL) as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta["strata"]))


if __name__ == "__main__":
    main()
