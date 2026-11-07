"""Reproduce each finding's counterexample on case/reward.py.

    python -I -B audit/scripts/repro.py            # every finding
    python -I -B audit/scripts/repro.py F3         # one finding
    python -I -B audit/scripts/repro.py --write    # also write audit/tests/counterexamples/<id>.jsonl

For each counterexample, prints the exact input as a Python string literal, the order whose
reference grades it, the grader's verdict (its reward, or the exception it raises) and the
contract's reward (the replacement, proposed readings). The --write files are response files
for the grader's own command line:

    cd case && python -I -B reward.py --responses ../audit/tests/counterexamples/F1.jsonl
"""
import decimal
import json
import pathlib
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "case"))
sys.path.insert(0, str(ROOT / "audit" / "replacement"))

import reward as G  # noqa: E402
import reward_contract as R  # noqa: E402

TAB = chr(9)
NL = chr(10)

COUNTEREXAMPLES = {
    "F1": ("o10", '{"total":24}x'),
    "F2": ("o01", "0"),
    "F3": ("o02", '{"items":[{"sku":"EF-310","qty":3},0]}'),
    "F4": ("o01", '{"total":1e1000000}'),
    "F5": ("o01", '{"a": ' + "[" * 2997 + "]" * 2997 + "}"),
    "F6": ("o01", '{"total":64.4949999999999999999999999999999}'),
    "F7": ("o10", "```json" + TAB + NL + '{"total":24}' + NL + "```"),
    "G2": ("o01", '{"total": ' + "1" * 4301 + "}"),
}
# G3: the caller's decimal context changes a verdict; run with a context change.
G3 = ("o01", '{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, '
             '{"sku": "CD-220", "qty": 1}], "total": 64.5051}')


def refs():
    out = {}
    for line in open(ROOT / "case" / "orders.jsonl", encoding="utf-8"):
        if line.strip():
            row = json.loads(line, parse_float=Decimal)
            out[row["order_id"]] = row["reference"]
    return out


def verdict(fn, *args):
    try:
        return repr(fn(*args))
    except Exception as exc:
        return "raises %s" % type(exc).__name__


def literal(text):
    s = ascii(text)
    return s if len(s) <= 160 else s[:70] + " ... " + s[-40:] + " (%d characters)" % len(text)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    ref = refs()
    for fid, (oid, text) in COUNTEREXAMPLES.items():
        if args and fid not in args:
            continue
        print("%s  order %s  input %s" % (fid, oid, literal(text)))
        print("    grader: %s   contract: %s" % (verdict(G.reward, text, ref[oid]), verdict(R.reward, text, ref[oid])))
        if write:
            d = ROOT / "audit" / "tests" / "counterexamples"
            d.mkdir(exist_ok=True)
            with open(d / (fid + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"id": fid, "checkpoint": "repro", "order_id": oid, "response": text}) + "\n")
    if not args or "G3" in args:
        oid, text = G3
        default = verdict(G.reward, text, ref[oid])
        with decimal.localcontext() as ctx:
            ctx.prec = 1
            low = verdict(G.reward, text, ref[oid])
        with decimal.localcontext() as ctx:
            ctx.traps[decimal.Overflow] = False
            no_trap = verdict(G.reward, COUNTEREXAMPLES["F4"][1], ref["o01"])
        print("G3  order %s  input %s" % (oid, literal(text)))
        print("    grader at the default context: %s; with decimal precision 1: %s; contract: %s"
              % (default, low, verdict(R.reward, text, ref[oid])))
        print("    F4's input with the Overflow trap off: %s (raises at the default context)" % no_trap)


if __name__ == "__main__":
    main()
