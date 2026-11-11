"""Attribute each difference between case/reward.py and the replacement (fixes_only mode) to findings.

emulate(response, reference, bugs) runs the replacement's fixes_only logic with the named defects put back:
    F1  the answer is the first JSON value of the extracted text; the rest is ignored (raw_decode)
    F2  the items score divides by the number of reference items only
    F3  a top-level value that is not an object raises AttributeError
    F4  json errors other than JSONDecodeError propagate (RecursionError, ValueError)
    F5  the total's distance is computed in the default decimal context, and Overflow propagates
    F6  the total's distance is rounded to the default context's 28 significant digits
explain(response, reference) returns the smallest set of defects whose emulation reproduces the grader's verdict,
or None if no set does (an unexplained difference, to be investigated).

    python -B audit/classify.py   # check that emulating all six defects reproduces the grader on fixtures, panel, fuzz
"""

import decimal
import itertools
import json
import os
import sys
from decimal import Decimal
from fractions import Fraction

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(W, "case"), os.path.join(W, "audit"), os.path.join(W, "audit", "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import replacement_reward as rr  # noqa: E402
import reward as grader  # noqa: E402

S = rr.FIXES_ONLY
BUGS = ("F1", "F2", "F3", "F4", "F5", "F6")
_RAW = json.JSONDecoder(parse_float=Decimal)


def _parse(answer, bugs):
    answer = answer.strip()
    try:
        if "F1" in bugs:
            value, _ = _RAW.raw_decode(answer)
        else:
            value = json.loads(answer, parse_float=Decimal)
    except json.JSONDecodeError:
        return None
    except (ValueError, RecursionError):
        if "F4" in bugs:
            raise
        return None
    if value is None:
        return None
    if not isinstance(value, dict):
        if "F3" in bugs:
            raise AttributeError(f"'{type(value).__name__}' object has no attribute 'get'")
        return None
    return value


def _total(value, expected, bugs):
    exact = rr.total_score(value, expected, S["total_inclusive"])
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)) or not ({"F5", "F6"} & bugs):
        return exact
    try:
        rounded = int(abs(Decimal(value) - Decimal(expected)) <= Decimal("0.005"))
    except decimal.Overflow:
        if "F5" in bugs:
            raise
        return exact
    return rounded if "F6" in bugs else exact


def emulate(response, reference, bugs=frozenset()):
    bugs = frozenset(bugs)
    answer = rr.extract_answer(response, whitespace=S["whitespace"], fence_tab=S["fence_tab"], crlf=S["crlf"])
    obj = _parse(answer, bugs)
    if obj is None:
        return 0.0
    items = obj.get("items")
    i_score = rr.items_score(items, reference["items"], S["qty_decimal"], S["qty_bool"])
    if "F2" in bugs and isinstance(items, list):
        i_score = i_score * max(len(reference["items"]), len(items)) / len(reference["items"])
    score = (Fraction(rr.customer_score(obj.get("customer"), reference["customer"], S["whitespace"]))
             + rr.date_score(obj.get("date"), reference["date"]) + i_score
             + _total(obj.get("total"), reference["total"], bugs))
    extra = sum(1 for k in obj if k not in rr.FIELDS)
    return float(min(Fraction(1), max(Fraction(0), score / 4 - Fraction(extra, 10))))


def _verdict(fn, *a):
    try:
        return fn(*a)
    except BaseException as e:  # noqa: BLE001
        return type(e).__name__


def _same(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return abs(a - b) < 1e-9


def explain(response, reference):
    g = _verdict(grader.reward, response, reference)
    for k in range(len(BUGS) + 1):
        for subset in itertools.combinations(BUGS, k):
            if _same(_verdict(emulate, response, reference, frozenset(subset)), g):
                return subset
    return None


def main():
    import stress  # noqa: E402
    from fixtures import FIXTURES  # noqa: E402
    import random
    refs = stress.REFS
    cases = [(f["order_id"], f["response"]) for f in FIXTURES]
    with open(os.path.join(W, "case", "responses.jsonl"), encoding="utf-8") as f:
        cases += [(r["order_id"], r["response"]) for r in map(json.loads, f)]
    rng = random.Random(stress.FUZZ_SEED)
    gens = [lambda: (rng.choice(list(refs)), stress.gen_text(rng)), lambda: stress.gen_mutation(rng),
            lambda: (rng.choice(list(refs)), stress.gen_json_value(rng)), lambda: stress.gen_order_object(rng)]
    for gen in gens:
        cases += [gen() for _ in range(2000)]
    unexplained = 0
    counts = {}
    for oid, resp in cases:
        sub = explain(resp, refs[oid])
        if sub is None:
            unexplained += 1
            print("UNEXPLAINED", oid, repr(resp[:120]))
        elif sub:
            counts[sub] = counts.get(sub, 0) + 1
    print(f"cases {len(cases)}, unexplained {unexplained}")
    for sub, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {'+'.join(sub)}: {n}")


if __name__ == "__main__":
    main()
