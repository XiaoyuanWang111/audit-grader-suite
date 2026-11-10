"""Step 6.5, analyses added after the review labels were read (not pre-registered).

audit/scripts/analyze_review.py (written before any label existed) gives the pre-registered
numbers. This script adds, from the same frozen inputs:
  1. error counts per stratum for every grader;
  2. the paired difference grader strict minus reference strict, and grader strict minus
     grader loose, bootstrapped within strata like the pre-registered difference;
  3. the grader's weighted error split into false passes and false fails;
  4. the held-out extraction failures that the review population excludes (contract G1);
  5. every case where grader, reference and replacement agree and the consensus differs (S3);
  6. for each replacement error, the decision switches whose reading gives the consensus
     verdict (the key's `replacement_alt`); for each grader error, the switches whose reading
     gives the grader's verdict.
Output: printed, and audit/work/review_post.json.
Run from W:  .venv/Scripts/python.exe -B audit/scripts/analyze_review_post.py [--boot 10000]
"""
import collections
import json
import os
import random
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R1 = os.path.join(W, "audit", "frozen", "review_round1")
REV = os.path.join(W, "audit", "frozen", "reviews")
BOOT = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 10000
GR = ("grader", "grader_loose", "reference", "reference_loose", "replacement")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def lab(v):
    return "pass" if v else "fail"


def main():
    cases = {c["case_id"]: c for c in load(os.path.join(R1, "cases.jsonl"))}
    key = {k["case_id"]: k for k in load(os.path.join(R1, "key.jsonl"))}
    strata = json.load(open(os.path.join(R1, "strata.json"), encoding="utf-8"))["strata"]
    A = {r["case_id"]: r for r in load(os.path.join(REV, "review_A.jsonl"))}
    B = {r["case_id"]: r for r in load(os.path.join(REV, "review_B.jsonl"))}
    ids = sorted(cases)
    cons = {i: A[i]["lean"] for i in ids if A[i]["lean"] == B[i]["lean"]}
    by_s = collections.defaultdict(list)
    for i in ids:
        by_s[cases[i]["stratum"]].append(i)
    N = sum(v["population"] for v in strata.values())
    wt = {s: strata[s]["population"] / N for s in strata}
    out = {}

    # 1. error counts per stratum
    print("1. errors among consensus cases, per stratum (errors / consensus cases):")
    per = {}
    for s in sorted(by_s):
        c = [i for i in by_s[s] if i in cons]
        per[s] = {"population": strata[s]["population"], "sample": len(by_s[s]), "consensus": len(c),
                  "consensus_pass": sum(cons[i] == "pass" for i in c)}
        for g in GR:
            per[s][g] = sum(lab(key[i][g]) != cons[i] for i in c)
        print(f"  {s}: population {per[s]['population']}, sample {per[s]['sample']}, consensus {len(c)} "
              f"(pass {per[s]['consensus_pass']}); " + ", ".join(f"{g} {per[s][g]}" for g in GR))
    out["per_stratum_counts"] = per

    # 2. paired differences
    def rate(draw, g, kind=None):
        tot = 0.0
        for s, w in wt.items():
            xs = [i for i in draw.get(s, []) if i in cons]
            if not xs:
                continue
            if kind is None:
                e = sum(lab(key[i][g]) != cons[i] for i in xs)
            elif kind == "false_pass":
                e = sum(key[i][g] and cons[i] == "fail" for i in xs)
            else:
                e = sum((not key[i][g]) and cons[i] == "pass" for i in xs)
            tot += w * e / len(xs)
        return tot

    rng = random.Random(20261111)
    pairs = [("grader", "reference"), ("grader", "grader_loose"), ("reference", "replacement")]
    boots = {p: [] for p in pairs}
    fp, ff = [], []
    for _ in range(BOOT):
        d = {s: [rng.choice(xs) for _ in xs] for s, xs in by_s.items()}
        for a, b in pairs:
            boots[(a, b)].append(rate(d, a) - rate(d, b))
        fp.append(rate(d, "grader", "false_pass"))
        ff.append(rate(d, "grader", "false_fail"))

    def ci(xs):
        xs = sorted(xs)
        return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

    print("\n2. paired differences of weighted error rates (consensus labels), 95% bootstrap within strata:")
    out["paired"] = {}
    for a, b in pairs:
        pt = rate(by_s, a) - rate(by_s, b)
        lo, hi = ci(boots[(a, b)])
        out["paired"][f"{a}-{b}"] = {"diff": pt, "ci95": [lo, hi]}
        print(f"  {a} - {b}: {pt:+.3%} [{lo:+.3%}, {hi:+.3%}]")

    # 3. false passes and false fails of the grader
    pfp, pff = rate(by_s, "grader", "false_pass"), rate(by_s, "grader", "false_fail")
    out["grader_false_pass"] = {"rate": pfp, "ci95": ci(fp)}
    out["grader_false_fail"] = {"rate": pff, "ci95": ci(ff)}
    print(f"\n3. grader strict, weighted: false pass {pfp:.3%} {ci(fp)}, false fail {pff:.3%} {ci(ff)}")

    # 4. extraction failures in the held-out runs
    ho = {}
    with open(os.path.join(W, "audit", "frozen", "heldout_runs.tsv"), encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                c, r = line.strip().split("\t")
                ho[c] = r
    n_ef = g_ef = gl_ef = n_pop = 0
    with open(os.path.join(W, "audit", "work", "panel_verdicts.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)
            if ho.get(v["cfg"]) != v["run"]:
                continue
            if v["extraction_failure"]:
                n_ef += 1
                g_ef += bool(v["g"])
                gl_ef += bool(v["gl"])
            else:
                n_pop += 1
    out["heldout_extraction_failures"] = {"verdicts": n_ef, "grader_pass": g_ef, "grader_loose_pass": gl_ef,
                                          "population_without_them": n_pop}
    print(f"\n4. held-out runs: {n_pop} verdicts in the review population; {n_ef} extraction-failure verdicts "
          f"excluded (grader strict passes {g_ef}, loose {gl_ef}; the contract fails all)")

    # 5. S3 cases where all three graders are wrong
    print("\n5. S3 consensus cases where grader, reference and replacement all differ from the consensus:")
    s3 = []
    for i in by_s["S3"]:
        if i in cons and lab(key[i]["grader"]) != cons[i]:
            row = {"case_id": i, "check": cases[i]["check"], "graders": lab(key[i]["grader"]), "consensus": cons[i],
                   "A": [A[i]["verdict"], A[i]["confidence"], A[i]["reason"]],
                   "B": [B[i]["verdict"], B[i]["confidence"], B[i]["reason"]]}
            s3.append(row)
            print(f"  {i} {row['check']}: graders {row['graders']}, consensus {cons[i]}")
            print(f"     A {row['A'][0]}/{row['A'][1]}: {row['A'][2]}")
            print(f"     B {row['B'][0]}/{row['B'][1]}: {row['B'][2]}")
    out["s3_all_wrong"] = s3

    # 6. decision switches behind replacement and grader errors
    print("\n6. replacement errors (consensus cases) by check, and the switches that give the consensus verdict:")
    rep_err = collections.defaultdict(list)
    for i in cons:
        k = key[i]
        if lab(k["replacement"]) != cons[i]:
            sw = sorted(d for d, v in k["replacement_alt"].items() if lab(v) == cons[i])
            rep_err[k["check"]].append({"case_id": i, "stratum": k["stratum"], "consensus": cons[i], "switches": sw,
                                        "definite": A[i]["verdict"] == B[i]["verdict"] != "ambiguous"})
    out["replacement_errors"] = rep_err
    for chk, rows in sorted(rep_err.items(), key=lambda kv: -len(kv[1])):
        sw = collections.Counter(s for r in rows for s in (r["switches"] or ["(none)"]))
        nd = sum(r["definite"] for r in rows)
        print(f"  {chk:32s} {len(rows):3d} errors ({nd} with both verdicts definite); switches: "
              + ", ".join(f"{s} {n}" for s, n in sw.most_common()))
    print("\n   grader errors (consensus cases) by check, and the switches that give the grader's verdict:")
    g_err = collections.defaultdict(list)
    for i in cons:
        k = key[i]
        if lab(k["grader"]) != cons[i]:
            sw = sorted(d for d, v in k["replacement_alt"].items() if v == k["grader"])
            g_err[k["check"]].append({"case_id": i, "stratum": k["stratum"], "grader": lab(k["grader"]),
                                      "consensus": cons[i], "switches": sw})
    out["grader_errors"] = g_err
    for chk, rows in sorted(g_err.items(), key=lambda kv: -len(kv[1])):
        sw = collections.Counter(s for r in rows for s in (r["switches"] or ["(none)"]))
        fpn = sum(r["grader"] == "pass" for r in rows)
        print(f"  {chk:32s} {len(rows):3d} errors (false pass {fpn}, false fail {len(rows) - fpn}); switches: "
              + ", ".join(f"{s} {n}" for s, n in sw.most_common()))
    with open(os.path.join(W, "audit", "work", "review_post.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\nwrote audit/work/review_post.json")


if __name__ == "__main__":
    main()
