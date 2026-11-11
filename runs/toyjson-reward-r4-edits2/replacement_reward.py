"""Replacement ToyOrders reward, written from audit/CONTRACT.md (not from case/reward.py).

reward(response, reference, **switches) returns a float in [0, 1] for every string response.

One switch per decision entry of the contract. Each defaults to the proposed reading.

    whitespace        "unicode" (proposed, str.strip set) | "json" (space, tab, LF, CR only)   D-whitespace
    fence_tab         True (proposed, tab may follow the tag) | False                         D-fence-tab
    crlf              True (proposed, "\\r\\n" ends a line) | False                             D-crlf
    json_constants    True (proposed, NaN/Infinity parse) | False (answer invalid)            D-json-constants
    qty_decimal       False (proposed, 2.0 is not an integer) | True                          D-qty-decimal
    qty_bool          False (proposed, true is not an integer) | True                         D-qty-bool
    total_inclusive   True (proposed, distance 0.005 is within) | False                       D-total-boundary

MODES gives two named settings: "proposed" (every proposed reading) and "fixes_only" (every switch set to the reading
that case/reward.py implements, so that each difference from case/reward.py is a defect fix, not a decision).

Offline use, from the audit's working directory:
    python -B audit/replacement_reward.py [--mode proposed|fixes_only] [--responses FILE] [--out FILE]
"""

import argparse
import decimal
import json
import os
import re
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

FIELDS = ("customer", "date", "items", "total")
JSON_WS = " \t\n\r"
TOLERANCE = Decimal("0.005")

PROPOSED = dict(whitespace="unicode", fence_tab=True, crlf=True, json_constants=True,
                qty_decimal=False, qty_bool=False, total_inclusive=True)
# The grader's reading of each decision, as measured by the decision fixtures in audit/tests/fixtures.py.
FIXES_ONLY = dict(whitespace="unicode", fence_tab=True, crlf=False, json_constants=True,
                  qty_decimal=True, qty_bool=False, total_inclusive=True)
MODES = {"proposed": PROPOSED, "fixes_only": FIXES_ONLY}


def _strip(text, whitespace):
    return text.strip() if whitespace == "unicode" else text.strip(JSON_WS)


def _reject_constant(name):
    raise ValueError(f"non-standard JSON constant {name}")


def extract_answer(response, whitespace="unicode", fence_tab=True, crlf=True):
    """C1.1-C1.3: return the answer text."""
    text = _strip(response, whitespace)
    lines = text.split("\n")
    if crlf:
        lines = [l[:-1] if l.endswith("\r") else l for l in lines]
    if len(lines) >= 2:
        opening = re.compile(r"```(?:json)?[ \t]*" if fence_tab else r"```(?:json)? *")
        if opening.fullmatch(lines[0]) and lines[-1] == "```":
            return "\n".join(lines[1:-1])
    return text


def parse_answer(answer, whitespace="unicode", json_constants=True):
    """C1.4-C1.5: return the parsed object, or None when the reward is 0.0."""
    if whitespace == "unicode":
        answer = answer.strip()
    kwargs = {"parse_float": Decimal}
    if not json_constants:
        kwargs["parse_constant"] = _reject_constant
    try:
        # json.loads accepts JSON whitespace at both ends and rejects any other surrounding text ("Extra data").
        value = json.loads(answer, **kwargs)
    except (ValueError, RecursionError):  # JSONDecodeError is a ValueError; so is the int digit limit
        return None
    return value if isinstance(value, dict) else None


def customer_score(value, expected, whitespace="unicode"):
    if not isinstance(value, str):
        return 0
    return int(_strip(value, whitespace).casefold() == _strip(expected, whitespace).casefold())


def date_score(value, expected):
    return int(isinstance(value, str) and value == expected)


def _is_integer(qty, qty_decimal, qty_bool):
    if isinstance(qty, bool):
        return qty_bool
    if isinstance(qty, int):
        return True
    if qty_decimal and isinstance(qty, Decimal):
        return qty.is_finite() and qty == qty.to_integral_value()
    return False


def items_score(value, expected, qty_decimal=False, qty_bool=False):
    if not isinstance(value, list):
        return Fraction(0)
    unmatched = [(e["sku"], e["qty"]) for e in expected]
    matched = 0
    for item in value:
        if not isinstance(item, dict):
            continue
        sku, qty = item.get("sku"), item.get("qty")
        if not isinstance(sku, str) or not _is_integer(qty, qty_decimal, qty_bool):
            continue
        for k, (e_sku, e_qty) in enumerate(unmatched):
            # Matching is on equality, so greedy assignment finds the largest one-to-one matching.
            if sku == e_sku and qty == e_qty:
                del unmatched[k]
                matched += 1
                break
    return Fraction(matched, max(len(expected), len(value)))


def total_score(value, expected, total_inclusive=True):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        return 0
    v = Decimal(value)  # exact for int and Decimal
    if not v.is_finite():
        return 0
    ref = Decimal(expected)  # exact for Decimal, int and float
    with decimal.localcontext() as ctx:
        ctx.prec = 200
        ctx.traps[decimal.Inexact] = True  # the bounds below must be exact
        lo, hi = ref - TOLERANCE, ref + TOLERANCE
    # Decimal comparisons are exact and use no context, so huge or long values cannot overflow or round here.
    if total_inclusive:
        return int(lo <= v <= hi)
    return int(lo < v < hi)


def reward(response, reference, whitespace="unicode", fence_tab=True, crlf=True, json_constants=True,
           qty_decimal=False, qty_bool=False, total_inclusive=True):
    answer = extract_answer(response, whitespace=whitespace, fence_tab=fence_tab, crlf=crlf)
    obj = parse_answer(answer, whitespace=whitespace, json_constants=json_constants)
    if obj is None:
        return 0.0
    score = (Fraction(customer_score(obj.get("customer"), reference["customer"], whitespace))
             + date_score(obj.get("date"), reference["date"])
             + items_score(obj.get("items"), reference["items"], qty_decimal, qty_bool)
             + total_score(obj.get("total"), reference["total"], total_inclusive))
    extra = sum(1 for key in obj if key not in FIELDS)
    value = score / 4 - Fraction(extra, 10)
    return float(min(Fraction(1), max(Fraction(0), value)))


def breakdown(response, reference, mode="proposed"):
    """Per-check scores for reports: answer validity, the four fields, extra keys, reward."""
    s = MODES[mode]
    answer = extract_answer(response, whitespace=s["whitespace"], fence_tab=s["fence_tab"], crlf=s["crlf"])
    obj = parse_answer(answer, whitespace=s["whitespace"], json_constants=s["json_constants"])
    if obj is None:
        return {"answer": 0, "customer": 0, "date": 0, "items": "0", "total": 0, "extra_keys": 0, "reward": 0.0}
    items = items_score(obj.get("items"), reference["items"], s["qty_decimal"], s["qty_bool"])
    return {"answer": 1,
            "customer": customer_score(obj.get("customer"), reference["customer"], s["whitespace"]),
            "date": date_score(obj.get("date"), reference["date"]),
            "items": str(items),
            "total": total_score(obj.get("total"), reference["total"], s["total_inclusive"]),
            "extra_keys": sum(1 for key in obj if key not in FIELDS),
            "reward": reward(response, reference, **s)}


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line, parse_float=Decimal) for line in f if line.strip()]


def main(argv=None):
    w = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Score rollouts with the replacement ToyOrders reward.")
    ap.add_argument("--mode", choices=sorted(MODES), default="proposed")
    ap.add_argument("--orders", default=os.path.join(w, "case", "orders.jsonl"))
    ap.add_argument("--responses", default=os.path.join(w, "case", "responses.jsonl"))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    refs = {o["order_id"]: o["reference"] for o in load_jsonl(args.orders)}
    rows = [{"id": r["id"], "checkpoint": r["checkpoint"], "order_id": r["order_id"],
             "reward": round(reward(r["response"], refs[r["order_id"]], **MODES[args.mode]), 4)}
            for r in load_jsonl(args.responses)]
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
    by = defaultdict(list)
    for row in rows:
        by[row["checkpoint"]].append(row["reward"])
    print(f"{'checkpoint':<12}{'rollouts':>9}{'mean':>8}{'full':>6}")
    for ck in sorted(by):
        rs = by[ck]
        print(f"{ck:<12}{len(rs):>9}{sum(rs) / len(rs):>8.3f}{sum(x == 1.0 for x in rs):>6}")


if __name__ == "__main__":
    main()
