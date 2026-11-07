"""Shared helpers for the ToyOrders reward tests.

Imports the grader under audit (case/reward.py) and the replacement
(audit/replacement/reward_contract.py) without writing bytecode into case/, and loads the
references the way the trainer does: json.loads(line, parse_float=Decimal).
"""
import json
import pathlib
import sys
import unittest
from decimal import Decimal

sys.dont_write_bytecode = True  # keep case/ free of __pycache__

ROOT = pathlib.Path(__file__).resolve().parents[2]
for sub in ("case", "audit/replacement"):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

import reward as grader  # noqa: E402  the grader under audit
import reward_contract as replacement  # noqa: E402

TOL = 1e-9


def load_references():
    refs = {}
    with open(ROOT / "case" / "orders.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line, parse_float=Decimal)
                refs[row["order_id"]] = row["reference"]
    return refs


REFS = load_references()


def run(fn, response, reference, **kw):
    """Return ("ok", value) or ("raises", exception type name)."""
    try:
        return "ok", fn(response, reference, **kw)
    except Exception as exc:  # the contract forbids every exception
        return "raises", type(exc).__name__


def verdict_ok(outcome, expected):
    status, value = outcome
    return status == "ok" and type(value) is float and abs(value - expected) <= TOL


def xfail_strict(reason):
    """pytest.mark.xfail(strict=True) when pytest is installed; unittest.expectedFailure
    otherwise, which also fails the run on an unexpected success."""
    try:
        import pytest
    except ImportError:
        return unittest.expectedFailure
    return pytest.mark.xfail(strict=True, reason=reason)


# --- building answers -----------------------------------------------------------------

class Raw(str):
    """A JSON fragment emitted verbatim, such as the number 64.50 or 6.45e1."""


class Pairs(list):
    """An object given as (key, value) pairs, so that a key can repeat."""


def dump(value, indent=None, level=0):
    if isinstance(value, Raw):
        return str(value)
    if isinstance(value, (dict, Pairs)):
        items = list(value.items()) if isinstance(value, dict) else list(value)
        parts = [json.dumps(k, ensure_ascii=False) + ": " + dump(v, indent, level + 1) for k, v in items]
        if indent is None:
            return "{" + ", ".join(parts) + "}"
        pad, pad_in = " " * (indent * level), " " * (indent * (level + 1))
        return "{\n" + ",\n".join(pad_in + p for p in parts) + "\n" + pad + "}"
    if isinstance(value, list):
        parts = [dump(v, indent, level + 1) for v in value]
        if indent is None:
            return "[" + ", ".join(parts) + "]"
        pad, pad_in = " " * (indent * level), " " * (indent * (level + 1))
        return "[\n" + ",\n".join(pad_in + p for p in parts) + "\n" + pad + "]"
    return json.dumps(value, ensure_ascii=False)


def correct(order_id):
    """The correct answer for an order as an ordered dict, total written as in orders.jsonl."""
    ref = REFS[order_id]
    return {
        "customer": ref["customer"],
        "date": ref["date"],
        "items": [{"sku": i["sku"], "qty": i["qty"]} for i in ref["items"]],
        "total": Raw(format(ref["total"], "f")),
    }


def correct_text(order_id, **changes):
    obj = correct(order_id)
    for key, value in changes.items():
        if value is DELETE:
            obj.pop(key)
        else:
            obj[key] = value
    return dump(obj)


DELETE = object()
