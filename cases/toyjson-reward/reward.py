"""Reward function for the ToyOrders structured-extraction task.

reward(response, reference) returns a float in [0, 1]. The trainer calls it once per rollout.

Offline use:
    python reward.py [--orders orders.jsonl] [--responses responses.jsonl] [--out rewards.jsonl]
prints the mean reward per checkpoint.
"""

import argparse
import json
import os
import re
from collections import defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("customer", "date", "items", "total")
EXTRA_KEY_PENALTY = 0.1
TOTAL_TOLERANCE = Decimal("0.005")
FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*)\n```", re.DOTALL)
_DECODER = json.JSONDecoder(parse_float=Decimal)


def _is_number(value):
    return isinstance(value, (int, Decimal)) and not isinstance(value, bool)


def parse_answer(response):
    text = response.strip()
    m = FENCE.fullmatch(text)
    if m:
        text = m.group(1).strip()
    try:
        answer, _ = _DECODER.raw_decode(text)
    except json.JSONDecodeError:
        return None
    return answer


def customer_score(value, expected):
    if not isinstance(value, str):
        return 0.0
    return float(value.strip().casefold() == expected.strip().casefold())


def date_score(value, expected):
    return float(isinstance(value, str) and value == expected)


def items_score(value, expected):
    if not isinstance(value, list):
        return 0.0
    remaining = [(e["sku"], e["qty"]) for e in expected]
    matched = 0
    for item in value:
        if not isinstance(item, dict):
            continue
        sku, qty = item.get("sku"), item.get("qty")
        if not isinstance(sku, str) or not _is_number(qty):
            continue
        for k, (e_sku, e_qty) in enumerate(remaining):
            if sku == e_sku and qty == e_qty:
                del remaining[k]
                matched += 1
                break
    return matched / len(expected)


def total_score(value, expected):
    if not _is_number(value):
        return 0.0
    return float(abs(Decimal(value) - Decimal(expected)) <= TOTAL_TOLERANCE)


def reward(response, reference):
    answer = parse_answer(response)
    if answer is None:
        return 0.0
    scores = [
        customer_score(answer.get("customer"), reference["customer"]),
        date_score(answer.get("date"), reference["date"]),
        items_score(answer.get("items"), reference["items"]),
        total_score(answer.get("total"), reference["total"]),
    ]
    extra = sum(1 for key in answer if key not in FIELDS)
    value = sum(scores) / len(FIELDS) - EXTRA_KEY_PENALTY * extra
    return min(1.0, max(0.0, value))


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line, parse_float=Decimal) for line in f if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score stored rollouts with the ToyOrders reward.")
    ap.add_argument("--orders", default=os.path.join(HERE, "orders.jsonl"))
    ap.add_argument("--responses", default=os.path.join(HERE, "responses.jsonl"))
    ap.add_argument("--out", help="write one JSON line per rollout with its reward")
    args = ap.parse_args(argv)

    references = {o["order_id"]: o["reference"] for o in load_jsonl(args.orders)}
    rows = []
    for r in load_jsonl(args.responses):
        rows.append({"id": r["id"], "checkpoint": r["checkpoint"], "order_id": r["order_id"],
                     "reward": round(reward(r["response"], references[r["order_id"]]), 4)})

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    by_ckpt = defaultdict(list)
    for row in rows:
        by_ckpt[row["checkpoint"]].append(row["reward"])
    print(f"{'checkpoint':<12}{'rollouts':>9}{'mean':>8}{'full':>6}")
    for ckpt in sorted(by_ckpt):
        rs = by_ckpt[ckpt]
        print(f"{ckpt:<12}{len(rs):>9}{sum(rs) / len(rs):>8.3f}{sum(x == 1.0 for x in rs):>6}")


if __name__ == "__main__":
    main()
