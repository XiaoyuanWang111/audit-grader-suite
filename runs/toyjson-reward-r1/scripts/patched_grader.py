"""case/reward.py's logic with each defect fix behind a flag, to attribute verdict changes.

    reward(response, reference, fixes=frozenset()) -> float (may raise, like the grader)

With no fixes it must equal case/reward.py on every input, and with ALL_FIXES it must equal
the replacement under its OFFICIAL readings; audit/scripts/fuzz.py and audit/scripts/panel.py
check both on every case they grade. The fixes:

    F1  decode the whole answer (json.JSONDecoder.decode) instead of raw_decode, so text after
        the first JSON value fails the gate
    F2  a top-level value that is not an object gives 0.0 instead of an AttributeError
    F3  items score divides by max(reference items, answer items)
    F4  the total comparison never raises on extreme exponents (exact bounds, no subtraction)
    F5  a parse that raises RecursionError or ValueError fails the gate
    F6  the total comparison is exact instead of rounded to the context's 28 digits
    F7  only spaces (U+0020) may follow the fence tag, not tabs
F4 and F6 share one change, the replacement's exact total comparison; either flag selects it.
"""
import json
import pathlib
import re
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
for sub in ("case", "audit/replacement"):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

import reward as G  # noqa: E402
import reward_contract as R  # noqa: E402

ALL_FIXES = frozenset({"F1", "F2", "F3", "F4", "F5", "F6", "F7"})
FENCE_TAB = G.FENCE
FENCE_SPACE = re.compile(r"```(?:json)?[ ]*\n(.*)\n```", re.DOTALL)
_DECODER = json.JSONDecoder(parse_float=Decimal)


def parse_answer(response, fixes):
    text = response.strip()
    m = (FENCE_SPACE if "F7" in fixes else FENCE_TAB).fullmatch(text)
    if m:
        text = m.group(1).strip()
    caught = (ValueError, RecursionError) if "F5" in fixes else json.JSONDecodeError
    try:
        if "F1" in fixes:
            return _DECODER.decode(text)
        answer, _ = _DECODER.raw_decode(text)
        return answer
    except caught:
        return None


def items_score(value, expected, fixes):
    if not isinstance(value, list):
        return 0.0
    remaining = [(e["sku"], e["qty"]) for e in expected]
    matched = 0
    for item in value:
        if not isinstance(item, dict):
            continue
        sku, qty = item.get("sku"), item.get("qty")
        if not isinstance(sku, str) or not G._is_number(qty):
            continue
        for k, (e_sku, e_qty) in enumerate(remaining):
            if sku == e_sku and qty == e_qty:
                del remaining[k]
                matched += 1
                break
    return matched / (max(len(expected), len(value)) if "F3" in fixes else len(expected))


def total_score(value, expected, fixes):
    if "F4" in fixes or "F6" in fixes:
        if not G._is_number(value):
            return 0.0
        return R.total_score(value, expected, "inclusive")
    return G.total_score(value, expected)


def reward(response, reference, fixes=frozenset()):
    answer = parse_answer(response, fixes)
    if answer is None:
        return 0.0
    if "F2" in fixes and not isinstance(answer, dict):
        return 0.0
    scores = [
        G.customer_score(answer.get("customer"), reference["customer"]),
        G.date_score(answer.get("date"), reference["date"]),
        items_score(answer.get("items"), reference["items"], fixes),
        total_score(answer.get("total"), reference["total"], fixes),
    ]
    extra = sum(1 for key in answer if key not in G.FIELDS)
    value = sum(scores) / len(G.FIELDS) - G.EXTRA_KEY_PENALTY * extra
    return min(1.0, max(0.0, value))


def outcome(fn, *args, **kw):
    try:
        return ("ok", fn(*args, **kw))
    except Exception as exc:
        return ("raises", type(exc).__name__)


def same(a, b, tol=1e-9):
    if a[0] != b[0]:
        return False
    if a[0] == "raises":
        return a[1] == b[1]
    return abs(a[1] - b[1]) <= tol


def attribute(response, reference):
    """Findings whose fix alone changes the grader's verdict on this response.

    F4 and F6 share one fix: a change counts as F4 when the grader raised, else as F6."""
    base = outcome(G.reward, response, reference)
    found = {k for k in sorted(ALL_FIXES - {"F6"})
             if not same(base, outcome(reward, response, reference, fixes=frozenset({k})))}
    if "F4" in found and base[0] == "ok":
        found = (found - {"F4"}) | {"F6"}
    return sorted(found)
