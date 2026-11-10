"""Step 4 stress tests: content-free responses, fuzzing, metamorphic edits on stored responses, loose transform.

Run from W:  .venv/Scripts/python.exe -B audit/scripts/step4_stress.py
Writes audit/work/step4_stress.json and prints a summary.
"""
import collections
import json
import os
import random
import sys
import time
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
sys.path.insert(0, os.path.join(W, "audit", "replacement"))
import ifb  # noqa: E402

FUZZ_PER_CHECK = 400
SEED = 20261109


def rep_verdict(iid, kw, prompt, resp, sw=None):
    import ifbench_contract as rep
    try:
        return rep.check(iid, kw, prompt, resp, sw), None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


# ------------------------------------------------------------------ A. content-free responses
def content_free(rows):
    variants = {
        "empty": lambda r: "",
        "space": lambda r: " ",
        "period": lambda r: ".",
        "repeat_word": lambda r: " ".join(["word"] * 100),
        "repeat_sentence": lambda r: " ".join(["This is a sentence."] * 30),
        "restate_prompt": lambda r: r["prompt"],
    }
    out = {}
    for name, fn in variants.items():
        per = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # n, grader, reference, replacement, grader errors
        for r in rows:
            resp = fn(r)
            for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
                g, ge = ifb.verdict("grader", iid, kw, r["prompt"], resp)
                f, _ = ifb.verdict("reference", iid, kw, r["prompt"], resp)
                p, _ = rep_verdict(iid, kw, r["prompt"], resp)
                c = per[iid]
                c[0] += 1
                c[1] += bool(g)
                c[2] += bool(f)
                c[3] += bool(p)
                c[4] += ge is not None
        out[name] = {iid: v for iid, v in sorted(per.items()) if v[1] or v[2] or v[3] or v[4]}
    return out


# ------------------------------------------------------------------ B. fuzzing
POOL_WORDS = ("the a an and but or so yet for nor I you it they we he she this that is are was be "
              "alpha beta gamma level radar civic kayak eagle bald Emma Liam Noah river door blue "
              "Question Zimbabwe Zambia My Answer: Conclusion: Future Outlook: despite verb strong "
              "don't isn't it's can't won't O'Neil well-known self-driving 3.14 10,000 2024 1st 9-11 "
              "日本 東京 です ".split())
POOL_PUNCT = list(".,;:!?'\"-—–()[]{}…/*#_`~|<>@$%^&+=\\") + ["?!", "!?", "“", "”", "‘", "’",
                                                              "**", "<i>", "</i>", "<em>", "</em>", "```"]
POOL_SPACE = [" ", " ", " ", "\n", "\n\n", "\t", "  ", " ", "\r\n"]
POOL_EMOJI = ["😊", "🚀", "❤️", "👍🏽", "🇺🇸", "🎉"]


def fuzz_text(rng):
    n = rng.randint(0, 60)
    parts = []
    for _ in range(n):
        x = rng.random()
        if x < 0.55:
            parts.append(rng.choice(POOL_WORDS))
        elif x < 0.80:
            parts.append(rng.choice(POOL_PUNCT))
        elif x < 0.95:
            parts.append(rng.choice(POOL_SPACE))
        else:
            parts.append(rng.choice(POOL_EMOJI))
        if rng.random() < 0.6:
            parts.append(" ")
    s = "".join(parts)
    if rng.random() < 0.15:  # line-structured text
        s = "\n".join(rng.choice(["* ", "- ", "  - ", "1. ", "", "\t", '"', "# "]) + w
                      for w in s.split(" ") if w)
    return s


def fuzz_job(args):
    iid, kw, prompt, seed = args
    rng = random.Random(seed)
    errs = collections.Counter()
    examples = {}
    n = 0
    for _ in range(FUZZ_PER_CHECK):
        t = fuzz_text(rng)
        if not t.strip():
            continue
        n += 1
        for which in ("grader", "reference"):
            v, e = ifb.verdict(which, iid, kw, prompt, t)
            if e:
                k = (which, e.split(":")[0] + ":" + e.split(":", 1)[1][:60])
                errs[k] += 1
                examples.setdefault(k, t)
        v, e = rep_verdict(iid, kw, prompt, t)
        if e:
            k = ("replacement", e[:80])
            errs[k] += 1
            examples.setdefault(k, t)
    return iid, n, {f"{a}|{b}": c for (a, b), c in errs.items()}, {f"{a}|{b}": ex for (a, b), ex in examples.items()}


# ------------------------------------------------------------------ C. metamorphic edits on stored responses
def curly(t):
    out, open_d = [], True
    for ch in t:
        if ch == '"':
            out.append("“" if open_d else "”")
            open_d = not open_d
        else:
            out.append(ch)
    return "".join(out)


EDITS = {"trailing_newline": lambda t: t + "\n", "curly_double_quotes": curly}


def meta_job(args):
    iid, kw, prompt, resp = args
    res = {}
    g0, _ = ifb.verdict("grader", iid, kw, prompt, resp)
    p0, _ = rep_verdict(iid, kw, prompt, resp)
    for name, fn in EDITS.items():
        t2 = fn(resp)
        if t2 == resp:
            continue
        g1, _ = ifb.verdict("grader", iid, kw, prompt, t2)
        p1, _ = rep_verdict(iid, kw, prompt, t2)
        res[name] = (g0 != g1, p0 != p1)
    return iid, res


def main():
    t0 = time.time()
    ifb.verify_pins()
    rows = ifb.load_rows()
    out = {}
    print("A. content-free responses ...", flush=True)
    out["content_free"] = content_free(rows)
    for name, per in out["content_free"].items():
        gl = [f"{iid}({v[1]}/{v[0]})" for iid, v in per.items() if v[1]]
        print(f"  {name}: grader passes {sum(v[1] for v in per.values())} instruction instances in {len(gl)} checks; "
              f"replacement passes {sum(v[3] for v in per.values())}; grader errors {sum(v[4] for v in per.values())}")
        print("    grader:", ", ".join(gl))
    print("B. fuzzing ...", flush=True)
    first = {}
    for r in rows:
        for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
            first.setdefault(iid, (iid, kw, r["prompt"]))
    jobs = [(iid, kw, p, SEED + i) for i, (iid, kw, p) in enumerate(sorted(first.values()))]
    with Pool(12) as pool:
        fz = pool.map(fuzz_job, jobs)
    out["fuzz"] = {iid: {"n": n, "errors": errs, "examples": ex} for iid, n, errs, ex in fz}
    tot = collections.Counter()
    for iid, n, errs, ex in fz:
        for k, c in errs.items():
            tot[k.split("|")[0]] += c
            print(f"  {iid}: {c}/{n} {k}")
    print("  total exceptions by grader:", dict(tot), "texts per check", FUZZ_PER_CHECK)
    print("C. metamorphic edits on the greedy runs ...", flush=True)
    recs = list(ifb.iter_panel(runs=["greedy"]))
    mjobs = []
    for cfg, run, i, rec in recs:
        if ifb.extraction_failure(rec):
            continue
        row = rows[i]
        for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
            mjobs.append((iid, kw, row["prompt"], rec["response"]))
    with Pool(12) as pool:
        mres = pool.map(meta_job, mjobs, chunksize=50)
    agg = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
    for iid, res in mres:
        for name, (gf, pf) in res.items():
            a = agg[name][iid]
            a[0] += 1
            a[1] += gf
            a[2] += pf
    out["metamorphic"] = {name: {iid: v for iid, v in sorted(d.items()) if v[1] or v[2]} for name, d in agg.items()}
    for name, d in out["metamorphic"].items():
        print(f"  {name}: grader flips {sum(v[1] for v in d.values())}, replacement flips {sum(v[2] for v in d.values())}")
        for iid, v in d.items():
            print(f"    {iid}: n={v[0]} grader flips={v[1]} replacement flips={v[2]}")
    with open(os.path.join(W, "audit", "work", "step4_stress.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("done in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
