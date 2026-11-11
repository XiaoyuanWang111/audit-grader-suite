"""List every fixture with its contract label and the verdicts of case/reward.py and the replacement.

    python -B audit/run_fixtures.py            # all fixtures
    python -B audit/run_fixtures.py --wrong    # only fixtures where case/reward.py differs from the proposed label
"""

import json
import os
import sys

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(W, "case"), os.path.join(W, "audit"), os.path.join(W, "audit", "tests")]

from decimal import Decimal  # noqa: E402

import replacement_reward as rr  # noqa: E402
import reward as grader  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

DECISION_SWITCH = {"D-whitespace": ("whitespace", "json"), "D-fence-tab": ("fence_tab", False),
                   "D-crlf": ("crlf", False), "D-json-constants": ("json_constants", False),
                   "D-qty-decimal": ("qty_decimal", True), "D-qty-bool": ("qty_bool", True),
                   "D-total-boundary": ("total_inclusive", False)}


def refs():
    with open(os.path.join(W, "case", "orders.jsonl"), encoding="utf-8") as f:
        return {o["order_id"]: o["reference"] for o in (json.loads(l, parse_float=Decimal) for l in f if l.strip())}


def call(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as e:  # noqa: BLE001 - every exception is a finding here
        return f"{type(e).__name__}"


def main():
    r = refs()
    wrong_only = "--wrong" in sys.argv
    for f in FIXTURES:
        ref = r[f["order_id"]]
        g = call(grader.reward, f["response"], ref)
        p = call(rr.reward, f["response"], ref, **rr.PROPOSED)
        x = call(rr.reward, f["response"], ref, **rr.FIXES_ONLY)
        dec = ""
        if f["decision"]:
            d, a, b = f["decision"]
            sw, bval = DECISION_SWITCH[d]
            rb = call(rr.reward, f["response"], ref, **{**rr.PROPOSED, sw: bval})
            dec = f" {d} A={a:.4f} B={b:.4f} repl(B)={rb if isinstance(rb, str) else round(rb, 4)}"
        ok = isinstance(g, float) and abs(g - f["expected"]) < 1e-9
        if wrong_only and ok:
            continue
        show = repr(f["response"][:70]) + ("..." if len(f["response"]) > 70 else "")
        fmt = lambda v: v if isinstance(v, str) else f"{v:.4f}"  # noqa: E731
        print(f"{f['id']} exp={f['expected']:.4f} grader={fmt(g)} repl={fmt(p)} fixes_only={fmt(x)}"
              f"{dec} {'' if ok else 'GRADER-DIFFERS'} {show}")


if __name__ == "__main__":
    main()
