"""Replacement ToyOrders reward, an implementation of audit/CONTRACT.md.

    score(response, reference, **readings) -> dict with the gate, each field score,
                                               the extra-key count and the reward
    reward(response, reference, **readings) -> float in [0, 1]

It never raises for a str response and a reference loaded from case/orders.jsonl with
parse_float=Decimal.

One switch per decision entry. PROPOSED holds the readings the audit proposes, and OFFICIAL
the readings that case/reward.py implements, so that OFFICIAL differs from case/reward.py
only by the defect fixes ("fixes only").

    fence_newline    D-fence-newline     "lf": lines end at "\\n" only (reading A)
                                         "universal": LF, CR or CRLF end a line (reading B)
    inner_whitespace D-inner-whitespace  "strip": str.strip() the answer, then parse (A)
                                         "json": parse the answer as it is (B)
    qty_bool         D-qty-bool          "reject": true/false are not integers (A)
                                         "accept": true == 1, false == 0 (B)
    qty_integral     D-qty-integral      "type": only a JSON integer (int) is an integer (A)
                                         "value": any number with an integral value (B)
    total_boundary   D-total-boundary    "inclusive": |total - reference| <= 0.005 (A)
                                         "exclusive": |total - reference| < 0.005 (B)
"""
import decimal
import json
import re
from decimal import Decimal

FIELDS = ("customer", "date", "items", "total")
EXTRA_KEY_PENALTY = 0.1
TOLERANCE = Decimal("0.005")

PROPOSED = dict(fence_newline="universal", inner_whitespace="strip", qty_bool="reject",
                qty_integral="type", total_boundary="inclusive")
OFFICIAL = dict(fence_newline="lf", inner_whitespace="strip", qty_bool="reject",
                qty_integral="value", total_boundary="inclusive")

_LINE_END = {"lf": re.compile(r"\n"), "universal": re.compile(r"\r\n|\r|\n")}
_OPENING = re.compile(r"```(?:json)? *")  # contract 1.2: spaces (U+0020) only
_DECODER = json.JSONDecoder(parse_float=Decimal)


def _readings(overrides):
    readings = dict(PROPOSED)
    for key, value in overrides.items():
        if key not in readings:
            raise TypeError("unknown reading %r" % key)
        readings[key] = value
    return readings


def extract_answer(response, fence_newline="universal"):
    """Contract 1.1-1.2: return (answer text, whether it came from a fenced block)."""
    s = response.strip()
    ends = list(_LINE_END[fence_newline].finditer(s))
    if ends:
        first_end, last_end = ends[0], ends[-1]
        first_line = s[:first_end.start()]
        last_line = s[last_end.end():]
        if _OPENING.fullmatch(first_line) and last_line == "```":
            if first_end is last_end:
                return "", True
            return s[first_end.end():last_end.start()], True
    return s, False


def parse_answer(response, fence_newline="universal", inner_whitespace="strip"):
    """Contract 1.3: the parsed object, or None when the gate fails."""
    answer, _ = extract_answer(response, fence_newline)
    if inner_whitespace == "strip":
        answer = answer.strip()
    try:
        value = _DECODER.decode(answer)  # whole string: one value, JSON whitespace around it
    except (ValueError, RecursionError):  # JSONDecodeError is a ValueError; so is the int-digit limit
        return None
    return value if isinstance(value, dict) else None


def customer_score(value, expected):
    return 1.0 if isinstance(value, str) and value.strip().casefold() == expected.strip().casefold() else 0.0


def date_score(value, expected):
    return 1.0 if isinstance(value, str) and value == expected else 0.0


def _is_integer(value, qty_bool, qty_integral):
    if isinstance(value, bool):
        return qty_bool == "accept"
    if isinstance(value, int):
        return True
    if qty_integral == "value" and isinstance(value, Decimal) and value.is_finite():
        return value == value.to_integral_value()
    return False


def items_score(value, expected, qty_bool="reject", qty_integral="type"):
    if not isinstance(value, list):
        return 0.0
    remaining = [(e["sku"], e["qty"]) for e in expected]
    matched = 0
    for item in value:
        if not isinstance(item, dict):
            continue
        sku, qty = item.get("sku"), item.get("qty")
        if not isinstance(sku, str) or not _is_integer(qty, qty_bool, qty_integral):
            continue
        for k, (e_sku, e_qty) in enumerate(remaining):
            if sku == e_sku and qty == e_qty:  # exact comparisons, no rounding
                del remaining[k]
                matched += 1
                break
    return matched / max(len(expected), len(value))


def _bounds(expected):
    """expected -/+ 0.005, computed exactly whatever the caller's decimal context."""
    digits = len(expected.as_tuple().digits) + 10
    ctx = decimal.Context(prec=max(28, digits), Emax=decimal.MAX_EMAX, Emin=decimal.MIN_EMIN,
                          traps=[])
    lo, hi = ctx.subtract(expected, TOLERANCE), ctx.add(expected, TOLERANCE)
    if ctx.flags[decimal.Inexact]:
        raise ValueError("reference total %s has too many digits" % expected)
    return lo, hi


def total_score(value, expected, total_boundary="inclusive"):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, float)):
        return 0.0
    if isinstance(value, float):  # only NaN and the infinities come from the parse
        if value != value or value in (float("inf"), float("-inf")):
            return 0.0
        value = Decimal(value)  # exact conversion
    if isinstance(value, Decimal) and not value.is_finite():
        return 0.0
    lo, hi = _bounds(Decimal(expected))
    # Decimal comparisons are exact and do not depend on the context's precision.
    if total_boundary == "inclusive":
        return 1.0 if lo <= value <= hi else 0.0
    return 1.0 if lo < value < hi else 0.0


def score(response, reference, **overrides):
    r = _readings(overrides)
    answer = parse_answer(response, r["fence_newline"], r["inner_whitespace"])
    if answer is None:
        return {"gate": False, "customer": 0.0, "date": 0.0, "items": 0.0, "total": 0.0,
                "extra_keys": 0, "reward": 0.0}
    fields = {
        "customer": customer_score(answer.get("customer"), reference["customer"]),
        "date": date_score(answer.get("date"), reference["date"]),
        "items": items_score(answer.get("items"), reference["items"], r["qty_bool"], r["qty_integral"]),
        "total": total_score(answer.get("total"), reference["total"], r["total_boundary"]),
    }
    extra = sum(1 for key in answer if key not in FIELDS)
    value = sum(fields.values()) / 4 - EXTRA_KEY_PENALTY * extra
    out = {"gate": True}
    out.update(fields)
    out["extra_keys"] = extra
    out["reward"] = float(min(1.0, max(0.0, value)))
    return out


def reward(response, reference, **overrides):
    return score(response, reference, **overrides)["reward"]
