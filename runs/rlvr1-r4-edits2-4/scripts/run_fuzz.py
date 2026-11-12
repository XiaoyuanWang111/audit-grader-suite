"""Step 4 fuzzing: random token strings against every check, with kwargs drawn from the data.

Counts grader exceptions and verdict disagreements with the replacement grader, and shrinks
the first case of each exception type and of each disagreement direction to a minimal token
list. Counts depend on the fuzzer's distribution; they are not rates.
Writes audit/work/fuzz.json.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

A = Path("<W>/audit")
SEED = 20261112
N_PER_ID = 1000
TOKENS = [
    "the", "cat", "river", "art", "start", "Rain", "rain", "limit", "Zebras", "I", "a", "A", "NASA", "don't", "Don’t",
    "well-known", "1", "2.", "3.5", "café", "Мы", "你好", "。", "，", "！", ",", ".", "!", "?", ";", ":", "-", "—",
    "*", "**", "***", "******", "#", "##", "<<", ">>", "[", "]", "[]", "<b>", "</b>", '"', "“", "”", "'", "’", "`",
    "```", "P.S.", "p.s.", "SECTION", "Section", "\n", "\n\n", "\t", "...", "…", "(", ")", "{", "}", '{"a": 1}',
    "NaN", "Any other questions?", "My answer is yes.", "İ", "ß", "ǅ", "\u200b", "level", "noon",
]


def init():
    sys.path.insert(0, str(A / "lib"))
    global h, cg
    import harness as h  # noqa: F401
    from contract_grader import ContractGrader

    cg = ContractGrader()


def render(tokens, seps):
    return "".join(t + s for t, s in zip(tokens, seps))


def verdict_triplet(iid, kw, text):
    try:
        s_pass, s_err = h.skyrl_check(iid, kw, h.skyrl_text(text))
    except Exception as e:  # grade_instruction_following itself raising
        s_pass, s_err = False, f"OUTER {type(e).__name__}"
    g = h.gate_check_any(iid, kw, h.gate_text(text)) if True else None
    try:
        r = cg.check(iid, kw, cg.extract(text, False))
        r_err = None
    except Exception as e:
        r, r_err = False, f"{type(e).__name__}: {e}"
    return s_pass, (s_err.split(":")[0] if s_err else None), g, r, r_err


def shrink(iid, kw, tokens, seps, condition):
    tokens, seps = list(tokens), list(seps)
    changed = True
    while changed:
        changed = False
        for i in range(len(tokens)):
            t2, s2 = tokens[:i] + tokens[i + 1:], seps[:i] + seps[i + 1:]
            if condition(render(t2, s2)):
                tokens, seps, changed = t2, s2, True
                break
    return render(tokens, seps)


def fuzz_one(args):
    iid, kwargs_pool, seed = args
    rng = random.Random(seed)
    counts = Counter()
    first = {}
    for _ in range(N_PER_ID):
        kw = rng.choice(kwargs_pool)
        k = rng.randint(0, 25)
        extra = [str(v) for v in (kw or {}).values() if isinstance(v, str)]
        pool = TOKENS + extra * 3
        tokens = [rng.choice(pool) for _ in range(k)]
        seps = [rng.choice([" ", " ", "", "\n"]) for _ in range(k)]
        text = render(tokens, seps)
        random.seed(0)
        s, s_err, g, r, r_err = verdict_triplet(iid, kw, text)
        counts["n"] += 1
        keys = []
        if s_err:
            keys.append(("skyrl_exception", s_err))
        if r_err:
            keys.append(("replacement_exception", r_err.split(":")[0]))
        if s != r:
            keys.append(("skyrl_vs_replacement", "skyrl_pass" if s else "skyrl_fail"))
        if g != r:
            keys.append(("gate_vs_replacement", "gate_pass" if g else "gate_fail"))
        for key in keys:
            counts["|".join(key)] += 1
            if key not in first:
                def cond(t, key=key, kw=kw):
                    random.seed(0)
                    s2, se2, g2, r2, re2 = verdict_triplet(iid, kw, t)
                    if key[0] == "skyrl_exception":
                        return se2 == key[1]
                    if key[0] == "replacement_exception":
                        return bool(re2) and re2.split(":")[0] == key[1]
                    if key[0] == "skyrl_vs_replacement":
                        return s2 != r2 and (s2 if key[1] == "skyrl_pass" else not s2)
                    return g2 != r2 and (g2 if key[1] == "gate_pass" else not g2)
                minimal = shrink(iid, kw, tokens, seps, cond)
                random.seed(0)
                s3, se3, g3, r3, _ = verdict_triplet(iid, kw, minimal)
                first[key] = {"kwargs": kw, "response": minimal, "skyrl": s3, "skyrl_error": se3, "gate_check": g3,
                              "replacement": r3}
    return iid, dict(counts), {"|".join(k): v for k, v in first.items()}


if __name__ == "__main__":
    sys.path.insert(0, str(A / "lib"))
    import harness

    rows = harness.load_rows()
    pools = defaultdict(list)
    for rec in rows.values():
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            pools[iid].append(kw)
    jobs = [(iid, pools[iid], SEED + i) for i, iid in enumerate(sorted(pools))]
    result = {}
    with Pool(6, initializer=init) as pool:
        for iid, counts, first in pool.imap_unordered(fuzz_one, jobs):
            result[iid] = {"counts": counts, "minimal": first}
            print(iid, counts, flush=True)
    (A / "work" / "fuzz.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
