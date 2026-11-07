"""Step 6.1: draw the blinded-review sample (round 1) with a recorded seed, and write the frozen files.

Usage: python -I audit/scripts/draw_sample.py     (needs audit/out/panel_verdicts.jsonl from panel.py)

Population: the 48 stored-response verdicts. Strata:
  disagree  grade.py, the reference and the replacement (proposed readings) do not all give the same label
  agree     all three give the same label
Both strata are sampled in full, because the population is small. A third stratum of 12 calibration fixtures
(labels that need no reading) checks the reviewers and stays out of the error rate: 4 drawn from the
fixtures that grade.py fails, 8 from those it passes, families line, number, compare and free only.

Writes to audit/frozen/:
  round1_cases.jsonl  what a reviewer sees: case_id, check name and text, prompt, reference answer, response
  round1_keys.jsonl   case_id, stratum, source id, model, problem_id, each grader's verdict, fixture label
  round1_orders.json  reviewer A's and reviewer B's case orders
  round1_manifest.json  seed, stratum sizes, file hashes
No case file shows a source model, a grader verdict or a stratum.
"""
import hashlib
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(ROOT, "case")
FROZEN = os.path.join(ROOT, "audit", "frozen")
sys.path.insert(0, os.path.join(ROOT, "audit", "tests"))
import fixtures  # noqa: E402

SEED = 61106


def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def scoring_rule_text():
    """Rules 1 to 4 of the benchmark card, verbatim from case/TASK.md."""
    with open(os.path.join(CASE, "TASK.md"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    start = lines.index("## Scoring rule (from the ToyMath benchmark card)")
    out = []
    for line in lines[start + 1:]:
        if line.startswith("5.") or line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


def main():
    rng = random.Random(SEED)
    problems = {p["problem_id"]: p for p in read(os.path.join(CASE, "problems.jsonl"))}
    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8", newline="") as f:
        template = f.read()
    responses = {r["id"]: r for r in read(os.path.join(CASE, "responses.jsonl"))}
    panel = read(os.path.join(ROOT, "audit", "out", "panel_verdicts.jsonl"))
    rule = scoring_rule_text()
    labels = ("Labels: `correct` (rule 4 holds), `incorrect` (the answer line has a number that is not within "
              "0.01 of the reference answer), `no_answer` (rule 3: no answer line, or no number on it).")

    items = []
    for p in panel:
        v = {k: p["verdicts"][k][1] for k in ("grade_py", "reference", "replacement")}
        stratum = "agree" if len(set(v.values())) == 1 else "disagree"
        items.append({"stratum": stratum, "source": p["id"], "model": p["model"], "problem_id": p["problem_id"],
                      "response": responses[p["id"]]["response"], "verdicts": v, "fixture_label": None})
    population = {s: sum(1 for i in items if i["stratum"] == s) for s in ("disagree", "agree")}

    matrix = {e["id"]: e for e in read_matrix()}
    pool = [f for f in fixtures.FIXTURES if not f["alt"] and f["family"] in ("line", "number", "compare", "free")]
    failing = sorted((f for f in pool if matrix[f["id"]]["grade_py"]["class"] != "pass"), key=lambda f: f["id"])
    passing = sorted((f for f in pool if matrix[f["id"]]["grade_py"]["class"] == "pass"), key=lambda f: f["id"])
    calib = rng.sample(failing, 4) + rng.sample(passing, 8)
    for f in calib:
        m = matrix[f["id"]]
        items.append({"stratum": "fixture", "source": f["id"], "model": None, "problem_id": f["problem_id"],
                      "response": f["response"], "fixture_label": f["label"],
                      "verdicts": {k: m[k]["verdict"] for k in ("grade_py", "reference", "replacement")}})

    rng.shuffle(items)
    cases, keys = [], []
    for n, it in enumerate(items, 1):
        cid = "T%03d" % n
        pr = problems[it["problem_id"]]
        cases.append({
            "case_id": cid,
            "check": "answer",
            "requirement": rule + "\n\nReference answer: " + pr["answer"] + "\n\n" + labels,
            "prompt": template.replace("{problem}", pr["problem"]),
            "reference_answer": pr["answer"],
            "response": it["response"],
        })
        keys.append({"case_id": cid, "stratum": it["stratum"], "source": it["source"], "model": it["model"],
                     "problem_id": it["problem_id"], "verdicts": it["verdicts"],
                     "fixture_label": it["fixture_label"]})
    ids = [c["case_id"] for c in cases]
    order_b = ids[:]
    rng.shuffle(order_b)
    orders = {"reviewer_A": ids, "reviewer_B": order_b}

    os.makedirs(FROZEN, exist_ok=True)
    paths = {}
    for name, data in (("round1_cases.jsonl", cases), ("round1_keys.jsonl", keys)):
        path = os.path.join(FROZEN, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for row in data:
                f.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
        paths[name] = path
    path = os.path.join(FROZEN, "round1_orders.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(orders, f, indent=1)
        f.write("\n")
    paths["round1_orders.json"] = path
    hashes = {}
    for name, path in paths.items():
        with open(path, "rb") as f:
            hashes[name] = hashlib.sha256(f.read()).hexdigest()
    manifest = {"round": 1, "seed": SEED, "population": population,
                "sample": {s: sum(1 for k in keys if k["stratum"] == s) for s in ("disagree", "agree", "fixture")},
                "strata": "disagree: grade.py, reference and replacement (proposed readings) not all equal; "
                          "agree: all equal; fixture: calibration, outside the error rate",
                "sha256": hashes}
    with open(os.path.join(FROZEN, "round1_manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print(json.dumps(manifest, indent=1))
    print("disagree cases:", sorted((k["case_id"], k["source"]) for k in keys if k["stratum"] == "disagree"))
    print("fixture cases:", sorted((k["case_id"], k["source"], k["fixture_label"]) for k in keys
                                   if k["stratum"] == "fixture"))


def read_matrix():
    with open(os.path.join(ROOT, "audit", "out", "fixture_matrix.json"), encoding="utf-8") as f:
        return json.load(f)["matrix"]


if __name__ == "__main__":
    main()
