"""Step 6.5: join the two reviewers' labels with the frozen key and estimate error rates.

Inputs (frozen before the review): audit/frozen/review_round1/{cases,key}.jsonl, strata.json.
Reviews: audit/frozen/reviews/review_A.jsonl, review_B.jsonl.
Outputs: audit/work/review_summary.json and a printed report (used in AUDIT.md).
Run from W:  .venv/Scripts/python.exe -B audit/scripts/analyze_review.py [--boot 10000]
"""
import collections
import hashlib
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R1 = os.path.join(W, "audit", "frozen", "review_round1")
REV = sys.argv[sys.argv.index("--reviews") + 1] if "--reviews" in sys.argv else os.path.join(W, "audit", "frozen", "reviews")
BOOT = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 10000
GRADERS = {"grader": "grader strict", "grader_loose": "grader loose", "reference": "reference strict",
           "reference_loose": "reference loose", "replacement": "replacement"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    expected = {"cases.jsonl": "f360e3596f16f22c7c53fb117d6096b9784c4849f8406f4ef3a6292c8ad24f4d",
                "key.jsonl": "f39322475638d564e86a7b2bb63cb6bfccd621e59556c033a93168395634675f",
                "strata.json": "87f5ac13cd36f426916c6db4c4f543b07584dd771cd11719658562afbee274d0"}
    for f, h in expected.items():
        assert sha(os.path.join(R1, f)) == h, f"{f} changed since it was frozen"
    cases = {c["case_id"]: c for c in load(os.path.join(R1, "cases.jsonl"))}
    key = {k["case_id"]: k for k in load(os.path.join(R1, "key.jsonl"))}
    strata = json.load(open(os.path.join(R1, "strata.json"), encoding="utf-8"))["strata"]
    reviews = {}
    for who in ("A", "B"):
        rows = load(os.path.join(REV, f"review_{who}.jsonl"))
        ids = [r["case_id"] for r in rows]
        dup = [i for i, n in collections.Counter(ids).items() if n > 1]
        missing = sorted(set(cases) - set(ids))
        extra = sorted(set(ids) - set(cases))
        bad = [r for r in rows if r.get("verdict") not in ("pass", "fail", "ambiguous") or r.get("lean") not in ("pass", "fail")]
        print(f"reviewer {who}: {len(rows)} lines, duplicates {len(dup)}, missing {len(missing)}, unknown {len(extra)}, malformed {len(bad)}")
        assert not dup and not missing and not extra and not bad, (dup[:5], missing[:5], extra[:5], bad[:3])
        reviews[who] = {r["case_id"]: r for r in rows}
    A, B = reviews["A"], reviews["B"]
    ids = sorted(cases)
    # agreement
    both = [(A[i]["lean"], B[i]["lean"]) for i in ids]
    po = sum(a == b for a, b in both) / len(both)
    pa = sum(a == "pass" for a, _ in both) / len(both)
    pb = sum(b == "pass" for _, b in both) / len(both)
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    amb = {w: sum(r["verdict"] == "ambiguous" for r in reviews[w].values()) for w in reviews}
    amb_either = sum(1 for i in ids if A[i]["verdict"] == "ambiguous" or B[i]["verdict"] == "ambiguous")
    print(f"lean agreement {po:.3f}, Cohen's kappa {kappa:.3f}; ambiguous verdicts A {amb['A']}, B {amb['B']}, either {amb_either} of {len(ids)}")
    # consensus and errors
    cons = {i: A[i]["lean"] for i in ids if A[i]["lean"] == B[i]["lean"]}
    definite = {i: A[i]["verdict"] for i in ids if A[i]["verdict"] == B[i]["verdict"] and A[i]["verdict"] != "ambiguous"}
    by_stratum = collections.defaultdict(list)
    for i in ids:
        by_stratum[cases[i]["stratum"]].append(i)
    N = sum(v["population"] for v in strata.values())
    weights = {s: strata[s]["population"] / N for s in strata}

    def err(i, g, labels):
        v = key[i][g]
        return int(("pass" if v else "fail") != labels[i])

    def weighted(sample_ids_by_s, g, labels):
        tot = 0.0
        for s, w in weights.items():
            xs = [i for i in sample_ids_by_s.get(s, []) if i in labels]
            if xs:
                tot += w * sum(err(i, g, labels) for i in xs) / len(xs)
        return tot

    out = {"kappa_leans": kappa, "lean_agreement": po, "ambiguous": amb, "ambiguous_either": amb_either,
           "consensus_cases": len(cons), "definite_cases": len(definite), "weights": weights}
    rng = random.Random(20261110)
    est = {}
    for labels_name, labels in (("consensus", cons), ("definite", definite)):
        point = {g: weighted(by_stratum, g, labels) for g in GRADERS}
        boots = {g: [] for g in GRADERS}
        diffs = []
        for _ in range(BOOT):
            draw = {s: [rng.choice(xs) for _ in xs] for s, xs in by_stratum.items()}
            vals = {g: weighted(draw, g, labels) for g in GRADERS}
            for g in GRADERS:
                boots[g].append(vals[g])
            diffs.append(vals["grader"] - vals["replacement"])

        def ci(xs):
            xs = sorted(xs)
            return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

        est[labels_name] = {g: {"rate": point[g], "ci95": ci(boots[g])} for g in GRADERS}
        est[labels_name]["paired_grader_minus_replacement"] = {"diff": point["grader"] - point["replacement"], "ci95": ci(diffs)}
        print(f"\nweighted error rates against the {labels_name} labels ({len(labels)} cases):")
        for g, name in GRADERS.items():
            r = est[labels_name][g]
            print(f"  {name:18s} {r['rate']:.3%}  95% CI [{r['ci95'][0]:.3%}, {r['ci95'][1]:.3%}]")
        d = est[labels_name]["paired_grader_minus_replacement"]
        print(f"  grader - replacement {d['diff']:+.3%}  95% CI [{d['ci95'][0]:+.3%}, {d['ci95'][1]:+.3%}]")
    out["estimates"] = est
    # per stratum and per check
    per_s = {}
    for s, xs in by_stratum.items():
        c = [i for i in xs if i in cons]
        per_s[s] = {"sample": len(xs), "consensus": len(c),
                    **{g: (sum(err(i, g, cons) for i in c) / len(c) if c else None) for g in GRADERS}}
    out["per_stratum"] = per_s
    print("\nper stratum (error share among consensus cases):")
    for s, v in sorted(per_s.items()):
        print(f"  {s}: sample {v['sample']}, consensus {v['consensus']}, " +
              ", ".join(f"{g} {v[g]:.2f}" for g in ("grader", "reference", "replacement") if v[g] is not None))
    per_c = collections.defaultdict(lambda: collections.Counter())
    for i in cons:
        c = per_c[cases[i]["check"]]
        c["n"] += 1
        for g in ("grader", "replacement"):
            c[g] += err(i, g, cons)
    out["per_check"] = {k: dict(v) for k, v in sorted(per_c.items())}
    print("\nper check, consensus cases: errors grader / replacement")
    for k, v in sorted(per_c.items(), key=lambda kv: -kv[1]["grader"]):
        if v["grader"] or v["replacement"]:
            print(f"  {k:34s} n={v['n']:3d} grader {v['grader']:3d} replacement {v['replacement']:3d}")
    disputed = [{"case_id": i, "check": cases[i]["check"], "stratum": cases[i]["stratum"],
                 "A": {k: A[i][k] for k in ("verdict", "lean", "confidence", "reason")},
                 "B": {k: B[i][k] for k in ("verdict", "lean", "confidence", "reason")}} for i in ids if i not in cons]
    out["disputed"] = disputed
    print(f"\ndisputed cases (leans differ): {len(disputed)}")
    with open(os.path.join(W, "audit", "work", "review_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("wrote audit/work/review_summary.json")


if __name__ == "__main__":
    main()
