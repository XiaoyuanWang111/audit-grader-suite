"""Step 6.1 to 6.3: draw, freeze and render the round-1 review sample.

    python -I -B audit/scripts/draw_review_sample.py

Population: the 24 held-out rollouts (audit/frozen/heldout_split.json). A review case is one
rollout, and its label is the rollout's reward under the specification. Strata: whether the
grader under audit and the replacement (proposed readings) give different rewards, read from
audit/runs/panel_verdicts.jsonl. Every case of both strata is sampled (the population is
small). Case ids are opaque: drawn with random.Random(SEED), unrelated to rollout ids,
checkpoints or verdicts.

Writes, under audit/frozen/:
    review_r1_cases.jsonl      the case list (case id, order id, sha256 of the response); its
                               sha256 is the freeze recorded in audit/ISSUE.md
    review_r1_keys.jsonl       each case's rollout id, source checkpoint, stratum and verdicts
                               (never shown to reviewers)
    review_r1_material.jsonl   what the reviewers may read: prompt, reference, response
    review_r1_batch_A.md, review_r1_batch_B.md   the same cases in two different orders
    review_r1_strata.json      seed, population and sample size per stratum
"""
import hashlib
import json
import pathlib
import random
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
FROZEN = ROOT / "audit" / "frozen"
SEED = 20261108

SPEC = """The ToyOrders reward. The policy read the PROMPT and wrote the RESPONSE. Compute the reward that this
specification gives the RESPONSE against the REFERENCE:

1. Answer. Whitespace at both ends of the response is removed. If what remains is one fenced block, that is an
   opening line ```json or ``` (spaces may follow the tag), then the content, then a closing line ```,
   the answer is the block's content; otherwise the answer is all of what remains. The answer must be a single JSON
   object with nothing around it but whitespace; otherwise the reward is 0.0. JSON is parsed with Python's json
   module, which keeps the last value of a repeated key; numbers are read exactly (decimal fractions as
   decimal.Decimal).
2. Field scores, each from 0 to 1:
   - customer: 1 if it is a string equal to the reference name after removing whitespace at both ends and ignoring
     case (str.casefold), else 0.
   - date: 1 if it is a string exactly equal to the reference date, else 0.
   - items: 0 if it is not a list. Otherwise an answer item matches a reference item when it is an object whose
     sku is a string equal to the reference sku and whose qty is an integer equal to the reference quantity
     (other keys inside an item are ignored); each reference item can be matched by at most one answer item. The
     score is the number of matched reference items divided by the larger of the number of reference items and the
     number of answer items.
   - total: 1 if it is a number (not true or false) within 0.005 of the reference total, else 0.
3. Penalty: 0.1 for each top-level key other than the four above.
4. Reward = (sum of the four field scores) / 4 minus the penalty, clipped to [0, 1]."""

HEADER = """# Review batch {name}, round 1

Each case below starts with a line `=== CASE <id> ===` and has four parts. REQUIREMENT TO JUDGE is the
specification to apply; it is the same for every case. PROMPT is the exact text the policy received, between
the lines `<<<PROMPT BEGIN>>>` and `<<<PROMPT END>>>`. REFERENCE is the order's reference object as JSON,
between `<<<REFERENCE BEGIN>>>` and `<<<REFERENCE END>>>`. RESPONSE is the policy's exact response between the
lines `<<<RESPONSE BEGIN>>>` and `<<<RESPONSE END>>>`: the response starts right after the newline that ends the
begin line and stops right before the newline that precedes the end line, so leading and trailing whitespace stay
visible. The marker lines are not part of any text. To print a case's exact response (with escapes, so tabs,
carriage returns and other invisible characters show), run `python -I audit/frozen/review_r1_show.py <case id>`.
"""


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    orders = {}
    raw_refs = {}
    for line in open(ROOT / "case" / "orders.jsonl", encoding="utf-8"):
        if line.strip():
            row = json.loads(line, parse_float=Decimal)
            orders[row["order_id"]] = row
    # Show each reference as JSON with its total exactly as stored (two decimals).
    for oid, row in orders.items():
        ref = row["reference"]
        raw_refs[oid] = ('{"customer": %s, "date": %s, "items": [%s], "total": %s}' % (
            json.dumps(ref["customer"]), json.dumps(ref["date"]),
            ", ".join('{"sku": %s, "qty": %d}' % (json.dumps(i["sku"]), i["qty"]) for i in ref["items"]),
            format(ref["total"], "f")))
    template = (ROOT / "case" / "prompt_template.txt").read_text(encoding="utf-8")
    responses = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "case" / "responses.jsonl", encoding="utf-8") if l.strip()}
    verdicts = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "audit" / "runs" / "panel_verdicts.jsonl", encoding="utf-8")}
    heldout = json.load(open(FROZEN / "heldout_split.json"))["heldout"]

    strata = {"disagree": [], "agree": []}
    for rid in sorted(heldout):
        v = verdicts[rid]
        differs = isinstance(v["grader"], str) or abs(v["grader"] - v["proposed"]) > 1e-9
        strata["disagree" if differs else "agree"].append(rid)
    rng = random.Random(SEED)
    sample = {name: sorted(rng.sample(ids, len(ids))) for name, ids in strata.items()}  # all of each stratum
    chosen = sample["disagree"] + sample["agree"]
    numbers = rng.sample(range(100, 1000), len(chosen))
    case_of = {rid: "C%03d" % n for rid, n in zip(chosen, numbers)}

    cases, keys, material = [], [], []
    for rid in sorted(chosen, key=lambda r: case_of[r]):
        r, v = responses[rid], verdicts[rid]
        cid = case_of[rid]
        prompt = template.replace("{email}", orders[r["order_id"]]["email"])
        cases.append({"case_id": cid, "order_id": r["order_id"], "response_sha256": sha(r["response"])})
        keys.append({"case_id": cid, "rollout_id": rid, "checkpoint": r["checkpoint"], "order_id": r["order_id"],
                     "stratum": "disagree" if rid in strata["disagree"] else "agree",
                     "grader": v["grader"], "fixes_only": v["fixes_only"], "proposed": v["proposed"],
                     "findings": v["findings"], "decisions": v["decisions"]})
        material.append({"case_id": cid, "prompt": prompt, "reference": raw_refs[r["order_id"]], "response": r["response"]})

    def write_jsonl(name, rows):
        with open(FROZEN / name, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_jsonl("review_r1_cases.jsonl", cases)
    write_jsonl("review_r1_keys.jsonl", keys)
    write_jsonl("review_r1_material.jsonl", material)

    order_a = [m["case_id"] for m in material]
    order_b = order_a[:]
    random.Random(SEED + 1).shuffle(order_b)
    by_id = {m["case_id"]: m for m in material}
    for name, order in (("A", order_a), ("B", order_b)):
        parts = [HEADER.format(name=name)]
        for cid in order:
            m = by_id[cid]
            parts.append("=== CASE %s ===\n\nREQUIREMENT TO JUDGE:\n\n%s\n\nPROMPT:\n<<<PROMPT BEGIN>>>\n%s\n<<<PROMPT END>>>\n\n"
                         "REFERENCE:\n<<<REFERENCE BEGIN>>>\n%s\n<<<REFERENCE END>>>\n\nRESPONSE:\n<<<RESPONSE BEGIN>>>\n%s\n<<<RESPONSE END>>>\n"
                         % (cid, SPEC, m["prompt"], m["reference"], m["response"]))
        (FROZEN / ("review_r1_batch_%s.md" % name)).write_text("\n".join(parts), encoding="utf-8", newline="\n")

    info = {"seed": SEED, "population": "held-out rollouts, audit/frozen/heldout_split.json",
            "population_size": {k: len(v) for k, v in strata.items()},
            "sample_size": {k: len(v) for k, v in sample.items()},
            "stratum_rule": "disagree when case/reward.py and the replacement (proposed readings) give rewards more than 1e-9 apart, or the grader raises",
            "batch_A_order": order_a, "batch_B_order": order_b}
    (FROZEN / "review_r1_strata.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: info[k] for k in ("seed", "population_size", "sample_size")}))


if __name__ == "__main__":
    main()
