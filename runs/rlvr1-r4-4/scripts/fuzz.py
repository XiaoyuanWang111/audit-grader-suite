"""Step 4 fuzzing: random token soups on random constraints of the real rows, graded by A, B and R.

Counts grader exceptions per id (grading failures, separate from model accuracy), counts verdict
disagreements with R that no allowed reading explains, and shrinks the shortest such response per
(grader, id) by greedy token deletion. Writes tests/fuzz_cases.json (label = R's verdict under the
proposed readings; each kept case was read by hand, see AUDIT.md) and work/fuzz.out.
Counts depend on this generator's distribution: report them as counts, not rates.
"""
import collections
import itertools
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "scripts"))
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
import harness as H  # noqa: E402
from grade_panel import RELEVANT  # noqa: E402

src = open(os.path.join(AUDIT, "scripts", "make_known_failures.py"), encoding="utf-8").read()
ns = {}
exec(src[src.index("FINDING = {"):src.index("known = {}")], ns)
FINDING = ns["FINDING"]

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
rng = random.Random(20261112)
WORDS = "the a and of to in is it you that for on with as are this be or your my we can not an at by cat dog sun big apple run day".split()
PUNCT = [",", ".", "!", "?", "-", ":", ";", "*", "**", "***", "******", "[", "]", "<<", ">>", '"', "“", "”", "'",
         "P.S.", "P.P.S", "#", "(", ")", "...", "。", "，", "--"]
UNI = ["привет", "你好", "λόγος", "café", "naïve", "مرحبا"]
LAYOUT = ["\n", "\n\n", "\n* ", "\n- ", "\nSECTION 1\n", "\nSection 2\n", "\n***\n", "\n\n\n"]
rows = list(H.load_rows().values())


def gen(kw):
    pool_kw = []
    for k, v in (kw or {}).items():
        if isinstance(v, str):
            pool_kw.append(v)
        elif isinstance(v, list):
            pool_kw += [x for x in v if isinstance(x, str)]
    toks = []
    for _ in range(rng.randint(0, 30)):
        x = rng.random()
        if x < 0.45:
            toks.append(rng.choice(WORDS))
        elif x < 0.6 and pool_kw:
            w = rng.choice(pool_kw)
            toks.append(rng.choice([w, w.upper(), w.capitalize(), w + "s"]))
        elif x < 0.78:
            toks.append(rng.choice(PUNCT))
        elif x < 0.86:
            toks.append(rng.choice(UNI))
        elif x < 0.93:
            toks.append(rng.choice(LAYOUT))
        else:
            toks.append(str(rng.randint(0, 99)))
    out = ""
    for t in toks:
        out += t if (not out or rng.random() < 0.25 or t.startswith("\n")) else " " + t
    return out


def verdicts(iid, kw, text):
    random.seed(0)
    a, a_err = H.a_check(iid, kw, text)
    if iid in H.SEMANTIC:
        b, b_err = None, None
    else:
        b, b_err = H.b_check(iid, kw, text)
    r = H.r_check(iid, kw, text)
    alts = []
    if a != r or (b is not None and b != r):
        rel = RELEVANT[iid]
        for k in range(1, len(rel) + 1):
            for sub in itertools.combinations(rel, k):
                alts.append(H.r_check(iid, kw, text, {d: "alt" for d in sub}))
    return a, a_err, b, b_err, r, alts


def unexplained(g, iid, kw, text):
    a, _, b, _, r, alts = verdicts(iid, kw, text)
    v = a if g == "A" else b
    return v is not None and v != r and v not in alts, v


errors = collections.Counter()
disagree = collections.Counter()
best = {}
for it in range(N):
    rec = rng.choice(rows)
    j = rng.randrange(len(rec["instruction_id_list"]))
    iid, kw = rec["instruction_id_list"][j], rec["kwargs"][j]
    text = gen(kw)
    a, a_err, b, b_err, r, alts = verdicts(iid, kw, text)
    if a_err:
        errors[("A", iid, a_err.split(":")[0])] += 1
    if b_err:
        errors[("B", iid, b_err.split(":")[0])] += 1
    for g, v in (("A", a), ("B", b)):
        if v is None or v == r:
            continue
        if v in alts:
            disagree[(g, iid, "decision")] += 1
            continue
        disagree[(g, iid, "unexplained")] += 1
        key = (g, iid, v)
        if key not in best or len(text) < len(best[key][1]):
            best[key] = (kw, text)

# shrink each kept case by greedy deletion of tokens, then of characters
cases = []
for (g, iid, v), (kw, text) in sorted(best.items()):
    cur = text
    for unit in ("token", "token", "char"):
        if unit == "char" and len(cur) > 60:
            break
        parts = cur.split(" ") if unit == "token" else list(cur)
        joiner = " " if unit == "token" else ""
        i = 0
        while i < len(parts):
            cand = joiner.join(parts[:i] + parts[i + 1:])
            ok, vv = unexplained(g, iid, kw, cand)
            if ok and vv == v:
                parts = parts[:i] + parts[i + 1:]
                cur = cand
            else:
                i += 1
    r = H.r_check(iid, kw, cur)
    cases.append({"id": f"fuzz:{g}:{iid.split(':')[1]}:{'pass' if v else 'fail'}", "grader": g, "instruction_id": iid,
                  "kwargs": kw, "response": cur, "label": "pass" if r else "fail",
                  "reason": FINDING.get((g, iid), "F-new"), "kind": "fuzz"})
with open(os.path.join(AUDIT, "tests", "fuzz_cases.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(cases, f, ensure_ascii=False, indent=1)
with open(os.path.join(AUDIT, "work", "fuzz.out"), "w", encoding="utf-8") as f:
    f.write(f"iterations {N}, seed 20261112\nexceptions: {dict(errors)}\n")
    for k, v in sorted(disagree.items()):
        f.write(f"{k[0]} {k[1]} {k[2]} {v}\n")
    for c in cases:
        f.write(f"{c['id']} label={c['label']} reason={c['reason']} kwargs={json.dumps(c['kwargs'], ensure_ascii=False)} response={json.dumps(c['response'], ensure_ascii=False)}\n")
print(open(os.path.join(AUDIT, "work", "fuzz.out"), encoding="utf-8").read())
